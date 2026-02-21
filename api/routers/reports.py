"""Reports router: ZIP download for an analysis run."""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db
from api.models.analysis_run import AnalysisRun
from api.models.user import User
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/runs", tags=["reports"])


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
