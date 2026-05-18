"""Time-saving accounting service.

Estimates how much manual work in Excel/SQL each automated operation
replaces, and persists per-user events that drive the Settings counter.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.time_saving_event import TimeSavingEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Estimation rules — manual-work seconds per automated operation.
# Values reflect a realistic analyst workflow: opening files, mapping
# columns, building VLOOKUPs / pivot tables, waiting for Excel macros or
# SQL queries to finish, formatting tables for reports.
# Tune here if the office team has different baselines.
# ---------------------------------------------------------------------------

TIME_SAVING_RULES: dict[str, dict[str, int]] = {
    "dataset_imported_masterdata": {
        "base_seconds": 15 * 60,           # opening file, finding template
        "per_1000_rows": 5 * 60,           # cleaning numeric columns, normalising SKU
    },
    "dataset_imported_orders": {
        "base_seconds": 20 * 60,
        "per_1000_rows": 4 * 60,
    },
    "quality_run": {
        "base_seconds": 30 * 60,           # writing SQL / pivots for DQ checks
        "per_1000_rows": 3 * 60,           # waiting for queries, eyeballing results
    },
    "capacity_run": {
        "base_seconds": 45 * 60,           # VLOOKUP setup, 6 orientations per carrier
        "per_1000_skus": 10 * 60,
        "per_carrier": 5 * 60,
    },
    "performance_run": {
        "base_seconds": 40 * 60,           # pivot tables, hourly buckets
        "per_1000_lines": 1 * 60,          # SQL aggregations scale sub-linearly with row count
        "pareto_bonus": 25 * 60,           # ABC classification + ranking
        "max_seconds": 6 * 3600,           # ceiling — a realistic upper bound per event (6h)
    },
    "report_exported_zip": {
        "base_seconds": 25 * 60,           # collecting files, formatting CSVs
        "per_csv": 2 * 60,
    },
    "report_exported_pdf": {
        "base_seconds": 45 * 60,           # rebuilding charts in PowerPoint/Word
        "per_chart": 5 * 60,
    },
    "report_exported_xlsx": {
        "base_seconds": 25 * 60,           # collecting DQ lists, formatting sheets
    },
}

# Mapping for grouping events in the Settings UI.
# Backend is the source of truth for labels.
EVENT_LABELS: dict[str, str] = {
    "dataset_imported_masterdata": "Masterdata import",
    "dataset_imported_orders": "Orders import",
    "quality_run": "Quality (DQ) analysis",
    "capacity_run": "Capacity analysis",
    "performance_run": "Performance + SKU Pareto",
    "report_exported_zip": "Report ZIP export",
    "report_exported_pdf": "Report PDF export",
    "report_exported_xlsx": "Data quality Excel export",
}


@dataclass
class TimeSavingBreakdownItem:
    event_type: str
    label: str
    count: int
    seconds: int


@dataclass
class TimeSavingSummary:
    total_seconds: int
    total_events: int
    breakdown: list[TimeSavingBreakdownItem]


# ---------------------------------------------------------------------------
# Pure calculation — testable in isolation.
# ---------------------------------------------------------------------------

def calculate_manual_seconds(event_type: str, **context: Any) -> int:
    """Estimate how many seconds the manual equivalent of this operation would take.

    Unknown event_types return 0 so the caller never crashes on a typo.
    """
    rule = TIME_SAVING_RULES.get(event_type)
    if rule is None:
        logger.warning("Unknown time-saving event_type %r — recording 0 seconds", event_type)
        return 0

    seconds = rule.get("base_seconds", 0)

    row_count = int(context.get("row_count") or 0)
    if row_count and "per_1000_rows" in rule:
        seconds += rule["per_1000_rows"] * row_count // 1000

    sku_count = int(context.get("sku_count") or 0)
    if sku_count and "per_1000_skus" in rule:
        seconds += rule["per_1000_skus"] * sku_count // 1000

    lines_count = int(context.get("lines_count") or 0)
    if lines_count and "per_1000_lines" in rule:
        seconds += rule["per_1000_lines"] * lines_count // 1000

    carrier_count = int(context.get("carrier_count") or 0)
    if carrier_count and "per_carrier" in rule:
        seconds += rule["per_carrier"] * carrier_count

    csv_count = int(context.get("csv_count") or 0)
    if csv_count and "per_csv" in rule:
        seconds += rule["per_csv"] * csv_count

    chart_count = int(context.get("chart_count") or 0)
    if chart_count and "per_chart" in rule:
        seconds += rule["per_chart"] * chart_count

    if context.get("includes_pareto") and "pareto_bonus" in rule:
        seconds += rule["pareto_bonus"]

    # Optional per-rule ceiling — prevents extreme datasets from producing
    # implausible single-event durations.
    max_seconds = rule.get("max_seconds")
    if max_seconds and seconds > max_seconds:
        seconds = max_seconds

    return int(seconds)


def _pick_scale_value(context: dict[str, Any]) -> int | None:
    """Pick the most representative scale number to persist for later inspection."""
    for key in ("sku_count", "lines_count", "row_count", "carrier_count", "csv_count", "chart_count"):
        v = context.get(key)
        if v:
            return int(v)
    return None


# ---------------------------------------------------------------------------
# Persistence helpers — safe to call from request handlers.
# Failures are logged but never raised — telemetry must not break the
# analysis itself.
# ---------------------------------------------------------------------------

async def record_event(
    db: AsyncSession,
    user_id: str,
    event_type: str,
    *,
    run_id: str | None = None,
    **context: Any,
) -> TimeSavingEvent | None:
    """Persist one time-saving event. Returns the event or None on failure."""
    try:
        manual_seconds = calculate_manual_seconds(event_type, **context)
        event = TimeSavingEvent(
            user_id=user_id,
            event_type=event_type,
            manual_seconds=manual_seconds,
            scale_value=_pick_scale_value(context),
            run_id=run_id,
            context=context or None,
        )
        db.add(event)
        await db.commit()
        return event
    except Exception:
        logger.exception(
            "Failed to record time-saving event user_id=%s type=%s", user_id, event_type
        )
        try:
            await db.rollback()
        except Exception:
            pass
        return None


async def get_summary_for_user(db: AsyncSession, user_id: str) -> TimeSavingSummary:
    """Aggregate per-user totals + per-type breakdown for the Settings view."""
    total_row = await db.execute(
        select(
            func.coalesce(func.sum(TimeSavingEvent.manual_seconds), 0),
            func.count(TimeSavingEvent.id),
        ).where(TimeSavingEvent.user_id == user_id)
    )
    total_seconds, total_events = total_row.one()

    breakdown_rows = await db.execute(
        select(
            TimeSavingEvent.event_type,
            func.count(TimeSavingEvent.id).label("count"),
            func.coalesce(func.sum(TimeSavingEvent.manual_seconds), 0).label("seconds"),
        )
        .where(TimeSavingEvent.user_id == user_id)
        .group_by(TimeSavingEvent.event_type)
        .order_by(func.sum(TimeSavingEvent.manual_seconds).desc())
    )

    breakdown = [
        TimeSavingBreakdownItem(
            event_type=row.event_type,
            label=EVENT_LABELS.get(row.event_type, row.event_type),
            count=int(row.count),
            seconds=int(row.seconds),
        )
        for row in breakdown_rows
    ]

    return TimeSavingSummary(
        total_seconds=int(total_seconds),
        total_events=int(total_events),
        breakdown=breakdown,
    )
