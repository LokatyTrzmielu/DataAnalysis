"""Stateless analysis endpoints (Phase 1 PoC)."""

import tempfile
from pathlib import Path
from typing import Optional

import polars as pl
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.analytics.capacity import CapacityAnalyzer
from src.core.carriers import CarrierService
from src.ingest.pipeline import MasterdataIngestPipeline
from src.storage.data_store import DataStore
from api.schemas.analysis import CapacityResponse

router = APIRouter(prefix="/api/v1/analyze", tags=["analyze"])


def _load_masterdata_from_file(file_content: bytes, filename: str) -> pl.DataFrame:
    suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_content)
        tmp_path = Path(tmp.name)
    try:
        pipeline = MasterdataIngestPipeline()
        ingest_result = pipeline.run(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    if not ingest_result.mapping_result.is_complete:
        missing = ", ".join(ingest_result.mapping_result.missing_required)
        raise HTTPException(
            status_code=422,
            detail=f"Column mapping incomplete. Missing required fields: {missing}",
        )
    return ingest_result.df


@router.post("/capacity", response_model=CapacityResponse)
async def analyze_capacity(
    file: Optional[UploadFile] = File(None, description="Masterdata file (XLSX or CSV)"),
    dataset_id: Optional[str] = Form(None, description="ID of a previously imported dataset"),
    carrier_ids: str = Form(
        default="",
        description="Comma-separated carrier IDs to include (empty = all active)",
    ),
    prioritization_mode: bool = Form(
        default=False,
        description="Assign each SKU to the smallest fitting carrier by priority",
    ),
    best_fit_mode: bool = Form(
        default=False,
        description="Assign each SKU to carrier with best filling rate",
    ),
) -> CapacityResponse:
    """Run capacity analysis.

    Provide either 'file' (Excel/CSV upload) or 'dataset_id' (previously imported dataset).
    Using dataset_id skips Excel parsing entirely — much faster for large files.
    """
    if dataset_id:
        store = DataStore()
        if not store.exists(dataset_id):
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
        df = store.load(dataset_id, "masterdata")
    elif file is not None:
        if file.filename:
            suffix = Path(file.filename).suffix.lower()
            if suffix not in {".xlsx", ".xls", ".csv"}:
                raise HTTPException(
                    status_code=422,
                    detail=f"Unsupported file type '{suffix}'. Use XLSX or CSV.",
                )
        content = await file.read()
        df = _load_masterdata_from_file(content, file.filename or "data.xlsx")
    else:
        raise HTTPException(
            status_code=422,
            detail="Provide either 'file' (file upload) or 'dataset_id' (saved dataset).",
        )

    # Load carriers
    service = CarrierService()
    all_carriers = service.load_all_carriers()
    active_carriers = [c for c in all_carriers if c.is_active]

    if carrier_ids:
        requested = {cid.strip() for cid in carrier_ids.split(",") if cid.strip()}
        active_carriers = [c for c in active_carriers if c.carrier_id in requested]

    if not active_carriers:
        raise HTTPException(status_code=422, detail="No active carriers available for analysis.")

    analyzer = CapacityAnalyzer(active_carriers)
    result = analyzer.analyze_dataframe(
        df,
        prioritization_mode=prioritization_mode,
        best_fit_mode=best_fit_mode,
    )
    return CapacityResponse.from_result(result)
