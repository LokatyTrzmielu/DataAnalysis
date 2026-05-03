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
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/runs", tags=["reports"])

CSV_REPORTS = {
    "DQ_Summary",
    "DQ_MissingCritical",
    "DQ_SuspectOutliers",
    "DQ_HighRiskBorderline",
    "DQ_Duplicates",
    "DQ_Conflicts",
    "Capacity_Results",
    "SKU_Pareto",
    "SolDimTool_DashboardInput",
}

# Known column headers per report type (used to write empty CSVs with headers)
REPORT_COLUMNS: dict[str, list[str]] = {
    "DQ_Summary": [
        "total_records", "overall_score", "dimensions_coverage_pct",
        "weight_coverage_pct", "stock_coverage_pct", "missing_critical_count",
        "suspect_outliers_count", "high_risk_borderline_count",
        "duplicates_count", "conflicts_count",
        "imputed_dimensions_count", "imputed_weight_count",
    ],
    "DQ_MissingCritical": ["sku", "field", "details"],
    "DQ_SuspectOutliers": ["sku", "field", "details"],
    "DQ_HighRiskBorderline": ["sku", "field", "details"],
    "DQ_Duplicates": ["sku", "field", "details"],
    "DQ_Conflicts": ["sku", "field", "details"],
    "Capacity_Results": [],  # dynamic — derived from stored rows schema
    "SKU_Pareto": [
        "sku", "total_lines", "total_units", "total_orders",
        "frequency_rank", "cumulative_pct", "abc_class",
    ],
    "SolDimTool_DashboardInput": ["Section", "Cell", "Metric", "Value", "Note"],
}


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

    rows: list[dict] = []

    if report_name == "DQ_Summary":
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
    elif report_name == "DQ_MissingCritical":
        if not qr:
            raise HTTPException(status_code=422, detail="No quality results available.")
        rows = qr.get("missing_critical", [])
    elif report_name == "DQ_SuspectOutliers":
        if not qr:
            raise HTTPException(status_code=422, detail="No quality results available.")
        rows = qr.get("suspect_outliers", [])
    elif report_name == "DQ_HighRiskBorderline":
        if not qr:
            raise HTTPException(status_code=422, detail="No quality results available.")
        rows = qr.get("high_risk_borderline", [])
    elif report_name == "DQ_Duplicates":
        if not qr:
            raise HTTPException(status_code=422, detail="No quality results available.")
        rows = qr.get("duplicates", [])
    elif report_name == "DQ_Conflicts":
        if not qr:
            raise HTTPException(status_code=422, detail="No quality results available.")
        rows = qr.get("conflicts", [])
    elif report_name == "Capacity_Results":
        if not cr:
            raise HTTPException(status_code=422, detail="No capacity results available.")
        rows = cr.get("rows", [])
    elif report_name == "SKU_Pareto":
        if not pr:
            raise HTTPException(status_code=422, detail="No performance results available.")
        rows = [
            {**r, "cumulative_pct": f"{r['cumulative_pct']:.2f}%"}
            for r in pr.get("sku_pareto", [])
        ]
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

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # --- Capacity Results ---
        if cr:
            rows = cr.get("rows", [])
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

        # --- SolDimTool Dashboard Input ---
        if pr:
            zf.writestr(
                f"{client}_SolDimTool_DashboardInput.csv",
                _rows_to_csv_bytes(_generate_soldimtool_rows(pr), REPORT_COLUMNS.get("SolDimTool_DashboardInput")),
            )

    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{client}_report.zip"'},
    )


@router.get("/{run_id}/reports/pdf")
async def download_pdf(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate and return a PDF capacity analysis report for a run."""
    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.owner_id != current_user.id and not run.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    if not run.capacity_result:
        raise HTTPException(
            status_code=422,
            detail="No capacity results available. Run capacity analysis first.",
        )

    from api.pdf_generator import generate_capacity_pdf

    pdf_bytes = generate_capacity_pdf(
        client_name=run.client_name or run.id,
        capacity_data=run.capacity_result,
        run_id=run.id,
        performance_data=run.performance_result,
    )

    filename = f"{run.client_name or run.id}_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
