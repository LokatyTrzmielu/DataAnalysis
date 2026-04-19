"""Reports router: ZIP and PDF download for an analysis run."""

import io
import zipfile

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
}


def _rows_to_csv_bytes(rows: list[dict], columns: list[str] | None = None) -> bytes:
    """Convert a list of dicts to UTF-8 BOM CSV bytes (separator ';').

    Always writes column headers. If rows is empty and columns is provided,
    returns a header-only CSV.
    """
    if rows:
        df = pl.DataFrame(rows)
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
    )

    filename = f"{run.client_name or run.id}_capacity_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
