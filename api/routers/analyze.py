"""Stateless analysis endpoints (Phase 1 PoC)."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.analytics.capacity import CapacityAnalyzer
from src.core.carriers import CarrierService
from src.ingest.pipeline import MasterdataIngestPipeline
from api.schemas.analysis import CapacityResponse

router = APIRouter(prefix="/api/v1/analyze", tags=["analyze"])


@router.post("/capacity", response_model=CapacityResponse)
async def analyze_capacity(
    file: UploadFile = File(..., description="Masterdata file (XLSX or CSV)"),
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
    """Run capacity analysis on an uploaded masterdata file.

    Phase 1 PoC — stateless, no auth, no DB.

    Returns the full CapacityAnalysisResult serialized as JSON.
    """
    # Validate file extension
    if file.filename:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in {".xlsx", ".xls", ".csv"}:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type '{suffix}'. Use XLSX or CSV.",
            )

    # Save upload to a temp file so the pipeline can read it via file path
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(file.filename or "data.xlsx").suffix
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # 1. Ingest masterdata
        pipeline = MasterdataIngestPipeline()
        ingest_result = pipeline.run(tmp_path)

        if not ingest_result.mapping_result.is_complete:
            missing = ", ".join(ingest_result.mapping_result.missing_required)
            raise HTTPException(
                status_code=422,
                detail=f"Column mapping incomplete. Missing required fields: {missing}",
            )

        # 2. Load carriers
        service = CarrierService()
        all_carriers = service.load_all_carriers()
        active_carriers = [c for c in all_carriers if c.is_active]

        if carrier_ids:
            requested = {cid.strip() for cid in carrier_ids.split(",") if cid.strip()}
            active_carriers = [c for c in active_carriers if c.carrier_id in requested]

        if not active_carriers:
            raise HTTPException(
                status_code=422,
                detail="No active carriers available for analysis.",
            )

        # 3. Run capacity analysis
        analyzer = CapacityAnalyzer(active_carriers)
        result = analyzer.analyze_dataframe(
            ingest_result.df,
            prioritization_mode=prioritization_mode,
            best_fit_mode=best_fit_mode,
        )

        return CapacityResponse.from_result(result)

    finally:
        # Always clean up temp file
        tmp_path.unlink(missing_ok=True)
