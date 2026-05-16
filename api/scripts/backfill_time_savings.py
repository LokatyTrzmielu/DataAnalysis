"""One-shot CLI: backfill TimeSavingEvent rows from existing AnalysisRun data.

Idempotent — running twice never duplicates events (UNIQUE on (run_id, event_type)
enforced in code via a pre-check, since SQLite/Postgres unique-with-NULLs differs).

Usage:
    python -m api.scripts.backfill_time_savings
"""

import asyncio

from sqlalchemy import select

from api.database import SessionLocal, engine, Base
from api.models import *  # noqa: F401, F403 — register all models
from api.models.analysis_run import AnalysisRun
from api.models.time_saving_event import TimeSavingEvent
from api.services.time_saving import calculate_manual_seconds, _pick_scale_value


async def _event_exists(db, run_id: str, event_type: str) -> bool:
    result = await db.execute(
        select(TimeSavingEvent.id).where(
            TimeSavingEvent.run_id == run_id,
            TimeSavingEvent.event_type == event_type,
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


def _quality_context(qr: dict) -> dict:
    return {"row_count": int(qr.get("total_records") or 0)}


def _capacity_context(cr: dict) -> dict:
    carriers = cr.get("carriers_analyzed")
    if isinstance(carriers, list):
        carrier_count = len(carriers)
    elif isinstance(carriers, (int, float)):
        carrier_count = int(carriers)
    else:
        carrier_count = len(cr.get("carrier_stats") or {})
    return {
        "sku_count": int(cr.get("total_sku") or 0),
        "carrier_count": carrier_count,
    }


def _performance_context(pr: dict) -> dict:
    kpi = pr.get("kpi") or {}
    return {
        "lines_count": int(kpi.get("total_lines") or 0),
        "includes_pareto": True,
    }


_RESULT_MAP = [
    ("quality_run", "quality_result", _quality_context),
    ("capacity_run", "capacity_result", _capacity_context),
    ("performance_run", "performance_result", _performance_context),
]


async def backfill() -> None:
    # Make sure the new table exists in older DBs.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    inserted = 0
    skipped = 0

    async with SessionLocal() as db:
        runs = (await db.execute(select(AnalysisRun))).scalars().all()
        for run in runs:
            for event_type, attr, ctx_fn in _RESULT_MAP:
                payload = getattr(run, attr)
                if not payload:
                    continue
                if await _event_exists(db, run.id, event_type):
                    skipped += 1
                    continue
                context = ctx_fn(payload)
                seconds = calculate_manual_seconds(event_type, **context)
                event = TimeSavingEvent(
                    user_id=run.owner_id,
                    event_type=event_type,
                    manual_seconds=seconds,
                    scale_value=_pick_scale_value(context),
                    run_id=run.id,
                    context=context,
                    created_at=run.updated_at or run.created_at,
                )
                db.add(event)
                inserted += 1
        await db.commit()

    print(f"Backfill complete. inserted={inserted} skipped_existing={skipped}")


if __name__ == "__main__":
    asyncio.run(backfill())
