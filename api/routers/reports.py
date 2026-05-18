"""Reports router: ZIP and PDF download for an analysis run."""

import io
import math
import zipfile
from datetime import datetime

import polars as pl
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db
from api.models.analysis_run import AnalysisRun
from api.models.user import User
from api.services.time_saving import record_event as record_time_saving_event
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/runs", tags=["reports"])

CSV_REPORTS = {
    "DQ_Summary",
    "DQ_MissingCritical",
    "DQ_SuspectOutliers",
    "DQ_HighRiskBorderline",
    "DQ_Duplicates",
    "DQ_Conflicts",
    "Orders_DateGaps",
    "Orders_QtyNull",
    "Orders_QtyZero",
    "Orders_QtyNegative",
    "Orders_QtyOutliers",
    "Capacity_Results",
    "SKU_Pareto",
    "Pareto_Bands",
    "SolDimTool_DashboardInput",
}

_DQ_COLUMNS = ["sku", "field", "value", "details"]
_QTY_ROW_COLUMNS = ["order_id", "sku", "order_date", "order_hour", "quantity"]

# Known column headers per report type (used to write empty CSVs with headers)
REPORT_COLUMNS: dict[str, list[str]] = {
    "DQ_Summary": [
        "total_records", "overall_score", "dimensions_coverage_pct",
        "weight_coverage_pct", "stock_coverage_pct", "missing_critical_count",
        "suspect_outliers_count", "high_risk_borderline_count",
        "duplicates_count", "conflicts_count",
        "imputed_dimensions_count", "imputed_weight_count",
    ],
    "DQ_MissingCritical": _DQ_COLUMNS,
    "DQ_SuspectOutliers": _DQ_COLUMNS,
    "DQ_HighRiskBorderline": _DQ_COLUMNS,
    "DQ_Duplicates": _DQ_COLUMNS,
    "DQ_Conflicts": _DQ_COLUMNS,
    "Orders_DateGaps": ["from", "to", "days"],
    "Orders_QtyNull": _QTY_ROW_COLUMNS,
    "Orders_QtyZero": _QTY_ROW_COLUMNS,
    "Orders_QtyNegative": _QTY_ROW_COLUMNS,
    "Orders_QtyOutliers": _QTY_ROW_COLUMNS,
    "Capacity_Results": [],  # dynamic — derived from stored rows schema
    "SKU_Pareto": [
        "sku", "total_lines", "total_units", "total_orders",
        "frequency_rank", "cumulative_pct", "abc_class", "recommendation", "fit_status",
    ],
    "Pareto_Bands": [
        "moved_sku", "cumulated_sku_pct", "lines_day", "lines_day_pct",
        "cumulated_lines_pct", "pieces_day", "pieces_day_pct", "cumulated_pieces_pct",
    ],
    "SolDimTool_DashboardInput": ["Section", "Cell", "Metric", "Value", "Note"],
}

_ORDERS_REPORT_TO_FIELD = {
    "Orders_DateGaps": "gap_list",
    "Orders_QtyNull": "qty_null_rows",
    "Orders_QtyZero": "qty_zero_rows",
    "Orders_QtyNegative": "qty_negative_rows",
    "Orders_QtyOutliers": "qty_outlier_rows",
}

# Orders qty CSV reports re-run the filter against the orders dataframe with
# no row cap. ``qty_*_rows`` in the JSON column is only a sampled preview.
_ORDERS_QTY_REPORT_TO_KIND: dict[str, str] = {
    "Orders_QtyNull": "null",
    "Orders_QtyZero": "zero",
    "Orders_QtyNegative": "negative",
    "Orders_QtyOutliers": "outlier",
}


_QUALITY_DETAIL_KEYS = (
    "missing_critical",
    "suspect_outliers",
    "high_risk_borderline",
    "duplicates",
    "conflicts",
)


def _quality_result_needs_value_backfill(qr: dict | None) -> bool:
    """True when stored DQ items predate the ``value`` field on quality_result."""
    if not qr:
        return False
    for key in _QUALITY_DETAIL_KEYS:
        items = qr.get(key) or []
        for item in items:
            if "value" not in item:
                return True
            break
    return False


async def _maybe_backfill_quality_result(db: AsyncSession, run: AnalysisRun) -> dict | None:
    """Re-run the QualityPipeline so ``quality_result`` picks up the ``value`` column.

    Triggered when older runs are exported — those rows lack the ``value``
    field on each DQ item. We reload masterdata, re-run the pipeline, and
    overwrite ``quality_result`` so the cached JSON matches today's schema.
    """
    from api.routers.runs import _load_masterdata_df

    try:
        df = _load_masterdata_df(run)
    except Exception:
        return None
    if df is None:
        return None

    try:
        from src.quality.pipeline import QualityPipeline

        result = QualityPipeline().run(df)
        dq = result.dq_lists
        metrics = result.metrics_after
        imputation = result.imputation

        imputed_dims = sum(
            s.imputed_count for s in (imputation.stats if imputation else [])
            if s.field_name in ("length_mm", "width_mm", "height_mm")
        )
        imputed_weight = sum(
            s.imputed_count for s in (imputation.stats if imputation else [])
            if s.field_name == "weight_kg"
        )

        run.quality_result = {
            "total_records": metrics.total_records,
            "dimensions_coverage_pct": metrics.dimensions_coverage_pct,
            "weight_coverage_pct": metrics.weight_coverage_pct,
            "stock_coverage_pct": metrics.stock_coverage_pct,
            "missing_critical_count": len(dq.missing_critical),
            "suspect_outliers_count": len(dq.suspect_outliers),
            "high_risk_borderline_count": len(dq.high_risk_borderline),
            "duplicates_count": len(dq.duplicates),
            "conflicts_count": len(dq.conflicts),
            "collisions_count": len(dq.collisions),
            "imputed_dimensions_count": imputed_dims,
            "imputed_weight_count": imputed_weight,
            "overall_score": result.quality_score,
            "missing_critical": [
                {"sku": i.sku, "field": i.field, "value": i.value or "", "details": i.details or ""}
                for i in dq.missing_critical
            ],
            "suspect_outliers": [
                {"sku": i.sku, "field": i.field, "value": i.value or "", "details": i.details or ""}
                for i in dq.suspect_outliers
            ],
            "high_risk_borderline": [
                {"sku": i.sku, "field": i.field, "value": i.value or "", "details": i.details or ""}
                for i in dq.high_risk_borderline
            ],
            "duplicates": [
                {"sku": i.sku, "field": i.field, "value": i.value or "", "details": i.details or ""}
                for i in dq.duplicates
            ],
            "conflicts": [
                {"sku": i.sku, "field": i.field, "value": i.value or "", "details": i.details or ""}
                for i in dq.conflicts
            ],
        }
        await db.commit()
        await db.refresh(run)
        return run.quality_result
    except Exception:
        return None


# ---------------------------------------------------------------------------
# SolDimTool Dashboard Input — JSON-based calculator
# ---------------------------------------------------------------------------

def _pct(sorted_vals: list, p: float) -> float:
    """Linear-interpolation percentile from a pre-sorted list."""
    n = len(sorted_vals)
    if n == 0:
        return 0.0
    if n == 1:
        return float(sorted_vals[0])
    idx = (p / 100) * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    return sorted_vals[lo] * (1 - (idx - lo)) + sorted_vals[hi] * (idx - lo)


def _suggest_batch_sizes(max_batch: int) -> list[int]:
    raw = [
        1,
        max(2, round(max_batch * 0.10)),
        max(3, round(max_batch * 0.25)),
        max(4, round(max_batch * 0.50)),
        max_batch,
    ]
    seen: list[int] = []
    for v in raw:
        if v not in seen:
            seen.append(v)
    while len(seen) < 5:
        gaps = [(seen[i + 1] - seen[i], i) for i in range(len(seen) - 1)]
        _, idx = max(gaps)
        seen.insert(idx + 1, (seen[idx] + seen[idx + 1]) // 2)
    return sorted(seen[:5])


def _approx_percentiles_from_hist(lpo_dist: list[dict]) -> tuple[float, float]:
    """Approximate median and P90 from the bucketed lines-per-order histogram."""
    bin_midpoints = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
                     "6–10": 8, "11–20": 15, "21+": 25}
    values: list[int] = []
    for b in lpo_dist:
        val = bin_midpoints.get(b.get("bin", ""), 1)
        values.extend([val] * max(0, b.get("count", 0)))
    if not values:
        return 1.0, 2.0
    values.sort()
    return round(_pct(values, 50), 2), round(_pct(values, 90), 2)


def _generate_soldimtool_rows(pr: dict) -> list[dict]:
    """Calculate SolDimTool Dashboard inputs from stored performance_result JSON."""
    warnings: list[str] = []

    # 1. Orders/Day
    daily_orders = sorted([d["orders"] for d in pr.get("daily_metrics", [])])
    if daily_orders:
        n = len(daily_orders)
        mean_ord = round(sum(daily_orders) / n, 1)
        med_ord = round(_pct(daily_orders, 50), 1)
        p90_ord = round(_pct(daily_orders, 90), 1)
        if med_ord < 10:
            warnings.append("Very low daily order count — verify the date range of the data.")
        if med_ord > 0 and p90_ord / med_ord > 2.0:
            warnings.append("Strong seasonality (P90/median > 2×) — consider using P90 instead of median for C16.")
        if med_ord > 0 and p90_ord / med_ord > 1.5:
            rec_ord, ord_basis = int(p90_ord), "P90 (strong seasonality)"
        else:
            rec_ord, ord_basis = int(med_ord), "median"
    else:
        mean_ord = med_ord = p90_ord = 0.0
        rec_ord = 0
        ord_basis = "no data"
        warnings.append("No daily data — cannot calculate Orders/Day.")

    # 2. Orderlines/Order
    kpi = pr.get("kpi", {})
    avg_ol = round(kpi.get("avg_lines_per_order") or 1.0, 2)
    med_ol, p90_ol = _approx_percentiles_from_hist(pr.get("lines_per_order_dist", []))
    if avg_ol > 50:
        warnings.append("High lines/order count — verify data is not at line level instead of order level.")
    if avg_ol < 1:
        warnings.append("Lines/order < 1 — aggregation error or incomplete data.")

    # 3. Hours/Day
    datehour = pr.get("datehour_metrics", [])
    has_hourly = pr.get("has_hourly_data", False)
    if has_hourly and datehour:
        by_date: dict[str, list[int]] = {}
        for dh in datehour:
            by_date.setdefault(dh["date"], []).append(dh["hour"])
        windows = sorted([max(h) - min(h) for h in by_date.values()])
        win_med = _pct(windows, 50)
        hours_per_day = min(24, max(1, math.ceil(win_med + 0.5)))
        all_hours = [h for hs in by_date.values() for h in hs]
        win_min, win_max = min(all_hours), max(all_hours)
        time_detected = True
        if hours_per_day > 16:
            warnings.append("Detected operational window > 16h — possible multi-shift data or timestamp error.")
    else:
        hours_per_day, win_med, win_min, win_max = 8, None, None, None
        time_detected = False
        warnings.append("No time data — Hours/Day set to default value of 8h.")

    adj_view = "hourly view" if hours_per_day <= 8 else "daily view"

    # 4. Batch sizes
    max_batch = max(5, min(math.floor(rec_ord / 4) if rec_ord > 0 else 5, 100))
    if max_batch <= 5 and rec_ord < 20:
        warnings.append("Very low daily order count — batch size range may not be representative.")
    batch_sizes = _suggest_batch_sizes(max_batch)

    # 5. Commonality — raw SKU data not available in stored JSON
    commonality_values = [0.00, 0.05, 0.10, 0.15, 0.20]
    warnings.append("No row-level SKU data available — Commonality based on default values.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows: list[dict] = [
        {"Section": "Info", "Cell": "", "Metric": "Generated", "Value": now, "Note": ""},
        # Orders/Day
        {"Section": "Order Information", "Cell": "C16", "Metric": "Orders/Day - Mean", "Value": str(mean_ord), "Note": ""},
        {"Section": "Order Information", "Cell": "C16", "Metric": "Orders/Day - Median", "Value": str(med_ord), "Note": ""},
        {"Section": "Order Information", "Cell": "C16", "Metric": "Orders/Day - P90", "Value": str(p90_ord), "Note": ""},
        {"Section": "Order Information", "Cell": "C16", "Metric": "Orders/Day - Recommended", "Value": str(rec_ord), "Note": f"Basis: {ord_basis} — enter in C16"},
        # Orderlines/Order
        {"Section": "Order Information", "Cell": "C17", "Metric": "Orderlines/Order - Mean", "Value": str(avg_ol), "Note": ""},
        {"Section": "Order Information", "Cell": "C17", "Metric": "Orderlines/Order - Median (approx)", "Value": str(med_ol), "Note": ""},
        {"Section": "Order Information", "Cell": "C17", "Metric": "Orderlines/Order - P90 (approx)", "Value": str(p90_ol), "Note": ""},
        {"Section": "Order Information", "Cell": "C17", "Metric": "Orderlines/Order - Recommended", "Value": str(avg_ol), "Note": "enter in C17"},
        # Batch sizes
        {"Section": "Station Based", "Cell": "", "Metric": "max_batch", "Value": str(max_batch), "Note": f"floor({rec_ord} / 4), clamped [5, 100]"},
    ]
    for i, bs in enumerate(batch_sizes, start=1):
        cell = f"B{20 + i}"
        rows.append({"Section": "Station Based", "Cell": cell, "Metric": f"Orders/Batch {i}.", "Value": str(bs), "Note": f"enter in {cell}"})

    # Commonality
    rows.append({"Section": "Station Based", "Cell": "", "Metric": "Commonality - note", "Value": "default range",
                 "Note": "No SKU data — default range 0–20% applied. Adjust based on product knowledge."})
    for i, cv in enumerate(commonality_values, start=1):
        cell = f"C{20 + i}"
        rows.append({"Section": "Station Based", "Cell": cell, "Metric": f"Commonality {i}.", "Value": str(cv), "Note": f"enter in {cell}"})

    # Hours/Day
    rows.append({"Section": "Picking", "Cell": "A29", "Metric": "time_detected", "Value": "YES" if time_detected else "NO", "Note": ""})
    if win_min is not None:
        rows += [
            {"Section": "Picking", "Cell": "A29", "Metric": "Operational window min hour", "Value": str(int(win_min)), "Note": ""},
            {"Section": "Picking", "Cell": "A29", "Metric": "Operational window max hour", "Value": str(int(win_max)), "Note": ""},
            {"Section": "Picking", "Cell": "A29", "Metric": "Operational window median (h)", "Value": str(round(win_med, 2)), "Note": ""},
        ]
    else:
        rows.append({"Section": "Picking", "Cell": "A29", "Metric": "Hours/Day fallback",
                     "Value": "No time data — default value of 8h applied. Verify manually.", "Note": ""})
    rows.append({"Section": "Picking", "Cell": "A29", "Metric": "Hours/Day - Recommended", "Value": str(hours_per_day), "Note": "enter in A29"})

    adj_reason = "hours/day <= 8" if adj_view == "hourly view" else "hours/day > 8"
    rows.append({"Section": "Picking", "Cell": "A31", "Metric": "Adjusting View - Recommended",
                 "Value": adj_view, "Note": f"Reason: {adj_reason} — enter in A31"})
    rows.append({"Section": "Picking", "Cell": "C29", "Metric": "System Factor - Recommended",
                 "Value": "0.1", "Note": "Default value 10%. Adjust manually based on machine service data. — enter in C29"})

    # Warnings
    for w in warnings:
        rows.append({"Section": "Warnings", "Cell": "", "Metric": "", "Value": w, "Note": ""})
    if not warnings:
        rows.append({"Section": "Warnings", "Cell": "", "Metric": "", "Value": "none", "Note": ""})

    return rows


def _capacity_rows_with_carrier_name(cr: dict) -> list[dict]:
    """Return capacity rows with ``carrier_id`` swapped for ``carrier_name``.

    Looks up the human-readable name via ``carrier_settings`` (with a fallback
    to ``carrier_stats``) so the exported CSV shows the carrier name in place
    of the internal ID. Column position is preserved.
    """
    rows = cr.get("rows", []) or []
    if not rows:
        return rows

    settings = cr.get("carrier_settings") or {}
    stats = cr.get("carrier_stats") or {}

    def _name_for(cid: str | None) -> str:
        if not cid:
            return ""
        if cid == "NONE":
            return "Does not fit any carrier"
        info = settings.get(cid) or {}
        name = info.get("name")
        if name:
            return name
        stat = stats.get(cid) or {}
        return stat.get("carrier_name") or cid

    enriched: list[dict] = []
    for r in rows:
        new_row: dict = {}
        for k, v in r.items():
            if k == "carrier_id":
                new_row["carrier_name"] = _name_for(v)
            else:
                new_row[k] = v
        enriched.append(new_row)
    return enriched


def _rows_to_csv_bytes(rows: list[dict], columns: list[str] | None = None) -> bytes:
    """Convert a list of dicts to UTF-8 BOM CSV bytes (separator ';').

    Always writes column headers. If rows is empty and columns is provided,
    returns a header-only CSV.
    """
    if rows:
        df = pl.DataFrame(rows, infer_schema_length=None)
    elif columns:
        df = pl.DataFrame({c: [] for c in columns})
    else:
        return b"\xef\xbb\xbf"
    return b"\xef\xbb\xbf" + df.write_csv(separator=";").encode("utf-8")


@router.get("/{run_id}/reports/csv/{report_name}")
async def download_csv_report(
    run_id: str,
    report_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Download an individual CSV report for a run."""
    if report_name not in CSV_REPORTS:
        raise HTTPException(status_code=404, detail=f"Unknown report: {report_name}. Available: {sorted(CSV_REPORTS)}")

    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.owner_id != current_user.id and not run.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    qr = run.quality_result or {}
    cr = run.capacity_result or {}
    pr = run.performance_result or {}
    ovr = run.orders_validation_result or {}

    rows: list[dict] = []

    if report_name in _ORDERS_REPORT_TO_FIELD:
        if not ovr:
            raise HTTPException(status_code=422, detail="No orders validation results available.")
        # Qty CSV exports re-run the filter against the live orders df so the
        # output isn't truncated by the 100-row sampling cap.
        if report_name in _ORDERS_QTY_REPORT_TO_KIND:
            rows = []
            try:
                from api.routers.runs import _load_orders_df
                from src.analytics.orders_validation import compute_qty_issue_rows

                orders_df = _load_orders_df(run)
                if orders_df is not None:
                    rows = compute_qty_issue_rows(
                        orders_df,
                        _ORDERS_QTY_REPORT_TO_KIND[report_name],
                    )
            except Exception:
                rows = []
            # Fallback to the cached (sampled) preview if reloading the
            # source dataframe fails — better partial than nothing.
            if not rows:
                if not ovr.get(_ORDERS_REPORT_TO_FIELD[report_name]):
                    ovr = await _maybe_backfill_orders_validation(db, run) or ovr
                rows = ovr.get(_ORDERS_REPORT_TO_FIELD[report_name], []) or []
        else:
            # Orders_DateGaps — full list lives in the JSON.
            rows = ovr.get(_ORDERS_REPORT_TO_FIELD[report_name], []) or []
    elif report_name == "DQ_Summary":
        if not qr:
            raise HTTPException(status_code=422, detail="No quality results available.")
        rows = [{
            "total_records": qr.get("total_records"),
            "overall_score": qr.get("overall_score"),
            "dimensions_coverage_pct": qr.get("dimensions_coverage_pct"),
            "weight_coverage_pct": qr.get("weight_coverage_pct"),
            "stock_coverage_pct": qr.get("stock_coverage_pct"),
            "missing_critical_count": qr.get("missing_critical_count"),
            "suspect_outliers_count": qr.get("suspect_outliers_count"),
            "high_risk_borderline_count": qr.get("high_risk_borderline_count"),
            "duplicates_count": qr.get("duplicates_count"),
            "conflicts_count": qr.get("conflicts_count"),
            "imputed_dimensions_count": qr.get("imputed_dimensions_count"),
            "imputed_weight_count": qr.get("imputed_weight_count"),
        }]
    elif report_name in ("DQ_MissingCritical", "DQ_SuspectOutliers", "DQ_HighRiskBorderline", "DQ_Duplicates", "DQ_Conflicts"):
        if not qr:
            raise HTTPException(status_code=422, detail="No quality results available.")
        if _quality_result_needs_value_backfill(qr):
            qr = await _maybe_backfill_quality_result(db, run) or qr
        key_map = {
            "DQ_MissingCritical": "missing_critical",
            "DQ_SuspectOutliers": "suspect_outliers",
            "DQ_HighRiskBorderline": "high_risk_borderline",
            "DQ_Duplicates": "duplicates",
            "DQ_Conflicts": "conflicts",
        }
        rows = qr.get(key_map[report_name], [])
    elif report_name == "Capacity_Results":
        if not cr:
            raise HTTPException(status_code=422, detail="No capacity results available.")
        rows = _capacity_rows_with_carrier_name(cr)
    elif report_name == "SKU_Pareto":
        if not pr:
            raise HTTPException(status_code=422, detail="No performance results available.")
        rows = [
            {**r, "cumulative_pct": f"{r['cumulative_pct']:.2f}%"}
            for r in pr.get("sku_pareto", [])
        ]
    elif report_name == "Pareto_Bands":
        if not pr:
            raise HTTPException(status_code=422, detail="No performance results available.")
        rows = pr.get("pareto_bands", [])
    elif report_name == "SolDimTool_DashboardInput":
        if not pr:
            raise HTTPException(status_code=422, detail="No performance results available.")
        rows = _generate_soldimtool_rows(pr)

    csv_bytes = _rows_to_csv_bytes(rows, REPORT_COLUMNS.get(report_name))

    filename = f"{run.client_name or run_id}_{report_name}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{run_id}/reports/zip")
async def download_zip(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate and return the ZIP report package for a run."""
    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.owner_id != current_user.id and not run.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    qr = run.quality_result or {}
    cr = run.capacity_result or {}
    pr = run.performance_result or {}
    client = run.client_name or run.id

    csv_count = 0
    if cr:
        csv_count += 1  # Capacity_Results
    if qr:
        csv_count += 6  # Summary + 5 DQ lists
    if pr:
        csv_count += 3  # SKU_Pareto + Pareto_Bands + SolDimTool

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # --- Capacity Results ---
        if cr:
            rows = _capacity_rows_with_carrier_name(cr)
            zf.writestr(
                f"{client}_Capacity_Results.csv",
                _rows_to_csv_bytes(rows, REPORT_COLUMNS.get("Capacity_Results")),
            )

        # --- DQ reports ---
        if qr:
            dq_map = {
                "DQ_Summary": [{
                    "total_records": qr.get("total_records"),
                    "overall_score": qr.get("overall_score"),
                    "dimensions_coverage_pct": qr.get("dimensions_coverage_pct"),
                    "weight_coverage_pct": qr.get("weight_coverage_pct"),
                    "stock_coverage_pct": qr.get("stock_coverage_pct"),
                    "missing_critical_count": qr.get("missing_critical_count"),
                    "suspect_outliers_count": qr.get("suspect_outliers_count"),
                    "high_risk_borderline_count": qr.get("high_risk_borderline_count"),
                    "duplicates_count": qr.get("duplicates_count"),
                    "conflicts_count": qr.get("conflicts_count"),
                    "imputed_dimensions_count": qr.get("imputed_dimensions_count"),
                    "imputed_weight_count": qr.get("imputed_weight_count"),
                }],
                "DQ_MissingCritical": qr.get("missing_critical", []),
                "DQ_SuspectOutliers": qr.get("suspect_outliers", []),
                "DQ_HighRiskBorderline": qr.get("high_risk_borderline", []),
                "DQ_Duplicates": qr.get("duplicates", []),
                "DQ_Conflicts": qr.get("conflicts", []),
            }
            for name, rows in dq_map.items():
                zf.writestr(
                    f"{client}_{name}.csv",
                    _rows_to_csv_bytes(rows, REPORT_COLUMNS.get(name)),
                )

        # --- SKU Pareto ---
        if pr:
            pareto_rows = [
                {**r, "cumulative_pct": f"{r['cumulative_pct']:.2f}%"}
                for r in pr.get("sku_pareto", [])
            ]
            zf.writestr(
                f"{client}_SKU_Pareto.csv",
                _rows_to_csv_bytes(pareto_rows, REPORT_COLUMNS.get("SKU_Pareto")),
            )

        # --- Pareto Bands ---
        if pr:
            zf.writestr(
                f"{client}_Pareto_Bands.csv",
                _rows_to_csv_bytes(pr.get("pareto_bands", []), REPORT_COLUMNS.get("Pareto_Bands")),
            )

        # --- SolDimTool Dashboard Input ---
        if pr:
            zf.writestr(
                f"{client}_SolDimTool_DashboardInput.csv",
                _rows_to_csv_bytes(_generate_soldimtool_rows(pr), REPORT_COLUMNS.get("SolDimTool_DashboardInput")),
            )

    await record_time_saving_event(
        db,
        current_user.id,
        "report_exported_zip",
        run_id=run.id,
        csv_count=csv_count,
    )

    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{client}_report.zip"'},
    )


async def _maybe_backfill_orders_validation(db: AsyncSession, run: AnalysisRun) -> dict | None:
    """Re-run OrdersValidator for runs created before per-issue row collection landed.

    Triggered when ``orders_validation_result`` exists but lacks the new
    row-level fields (e.g. ``qty_outlier_rows``). Returns the refreshed
    dict (also persisted on ``run``) or ``None`` when the orders dataframe
    can't be reloaded.
    """
    from api.routers.runs import _load_orders_df
    from src.analytics.orders_validation import OrdersValidator
    from src.storage.data_store import DataStore
    from pathlib import Path

    try:
        orders_df = _load_orders_df(run)
    except Exception:
        return None
    if orders_df is None:
        return None

    masterdata_df = None
    masterdata_path = None
    masterdata_mapping = None
    if run.masterdata_path:
        if run.masterdata_path.endswith(".duckdb"):
            try:
                md_dataset_id = Path(run.masterdata_path).stem
                store = DataStore()
                if store.exists(md_dataset_id):
                    masterdata_df = store.load(md_dataset_id, "masterdata")
            except Exception:
                masterdata_df = None
        elif run.quality_result and run.masterdata_mapping:
            masterdata_path = Path(run.masterdata_path)
            masterdata_mapping = run.masterdata_mapping

    try:
        result = OrdersValidator().validate(
            orders_df,
            masterdata_path=masterdata_path,
            masterdata_mapping=masterdata_mapping,
            masterdata_df=masterdata_df,
        )
        run.orders_validation_result = result
        await db.commit()
        await db.refresh(run)
        return result
    except Exception:
        return None


def _orders_validation_needs_backfill(ovr: dict) -> bool:
    if not ovr:
        return False
    expected_keys = ("qty_null_rows", "qty_zero_rows", "qty_negative_rows", "qty_outlier_rows", "total_gap_days")
    return any(k not in ovr for k in expected_keys)


@router.get("/{run_id}/reports/xlsx")
async def download_dq_xlsx(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate and return a multi-sheet Data Quality xlsx workbook for a run."""
    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.owner_id != current_user.id and not run.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    if not (run.quality_result or run.orders_validation_result):
        raise HTTPException(
            status_code=422,
            detail="No data quality results available. Run quality check first.",
        )

    # Self-heal pre-existing runs that lack per-issue row collections or
    # whose quality_result DQ items predate the `value` column.
    if _orders_validation_needs_backfill(run.orders_validation_result or {}):
        await _maybe_backfill_orders_validation(db, run)
    if _quality_result_needs_value_backfill(run.quality_result):
        await _maybe_backfill_quality_result(db, run)

    from api.dq_excel_generator import generate_dq_xlsx

    xlsx_bytes = generate_dq_xlsx(run, user=current_user)

    await record_time_saving_event(
        db,
        current_user.id,
        "report_exported_xlsx",
        run_id=run.id,
    )

    filename = f"{run.client_name or run.id}_data_quality.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{run_id}/reports/pdf")
async def download_pdf(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate and return a PDF report for a run.

    Accepts runs that have capacity results, performance results, or both.
    Capacity-only and performance-only exports skip the missing section.
    """
    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.owner_id != current_user.id and not run.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    if not run.capacity_result and not run.performance_result:
        raise HTTPException(
            status_code=422,
            detail="No capacity or performance results available. Run an analysis first.",
        )

    from api.pdf_generator import generate_capacity_pdf

    pdf_bytes = generate_capacity_pdf(
        client_name=run.client_name or run.id,
        capacity_data=run.capacity_result,
        run_id=run.id,
        performance_data=run.performance_result,
        user=current_user,
    )

    if run.capacity_result and run.performance_result:
        chart_count = 5
    elif run.capacity_result:
        chart_count = 2
    else:
        chart_count = 3

    await record_time_saving_event(
        db,
        current_user.id,
        "report_exported_pdf",
        run_id=run.id,
        chart_count=chart_count,
    )

    filename = f"{run.client_name or run.id}_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
