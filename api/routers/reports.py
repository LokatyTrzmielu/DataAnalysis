"""Reports router: ZIP and PDF download for an analysis run."""

import tempfile
from pathlib import Path
from typing import Any

import polars as pl
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
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


def _rebuild_capacity_result(data: dict[str, Any]):
    """Rebuild CapacityAnalysisResult from JSONB dict."""
    from src.analytics.capacity import CapacityAnalysisResult, CarrierStats

    carrier_stats = {
        cid: CarrierStats(**cs) for cid, cs in data.get("carrier_stats", {}).items()
    }
    df = pl.DataFrame(data.get("rows", []))
    return CapacityAnalysisResult(
        df=df,
        total_sku=data["total_sku"],
        fit_count=data["fit_count"],
        borderline_count=data["borderline_count"],
        not_fit_count=data["not_fit_count"],
        fit_percentage=data["fit_percentage"],
        carriers_analyzed=data["carriers_analyzed"],
        carrier_stats=carrier_stats,
    )


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

    if not rows:
        # Return empty CSV with just headers (from first element or minimal)
        csv_bytes = "\uFEFF".encode("utf-8")
    else:
        df = pl.DataFrame(rows)
        csv_bytes = b"\xef\xbb\xbf" + df.write_csv().encode("utf-8")

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
) -> FileResponse:
    """Generate and return the ZIP report package for a run."""
    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.owner_id != current_user.id and not run.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    capacity_result = None
    if run.capacity_result:
        capacity_result = _rebuild_capacity_result(run.capacity_result)

    from src.reporting.zip_export import ZipExporter

    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = ZipExporter()
        zip_path = exporter.export(
            output_dir=Path(tmpdir),
            client_name=run.client_name or run.id,
            capacity_result=capacity_result,
            run_id=run.id,
        )
        # Copy to a stable path that won't be cleaned up before response is sent
        stable = Path(tempfile.mktemp(suffix=".zip"))
        stable.write_bytes(zip_path.read_bytes())

    return FileResponse(
        path=str(stable),
        media_type="application/zip",
        filename=f"{run.client_name or run.id}_report.zip",
        background=None,
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
