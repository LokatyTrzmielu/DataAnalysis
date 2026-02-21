"""Analysis runs CRUD router."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db
from api.models.analysis_run import AnalysisRun
from api.models.user import User
from api.schemas.runs import RunCreate, RunListItem, RunListResponse, RunResponse
from api.schemas.analysis import CapacityResponse

import tempfile

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

UPLOAD_DIR = Path("uploads")


def _run_to_response(run: AnalysisRun) -> RunResponse:
    return RunResponse(
        id=run.id,
        owner_id=run.owner_id,
        client_name=run.client_name,
        status=run.status,
        masterdata_mapping=run.masterdata_mapping,
        orders_mapping=run.orders_mapping,
        quality_result=run.quality_result,
        capacity_result=run.capacity_result,
        performance_result=run.performance_result,
        analysis_config=run.analysis_config,
        is_public=run.is_public,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    body: RunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunResponse:
    run = AnalysisRun(owner_id=current_user.id, client_name=body.client_name)
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return _run_to_response(run)


@router.get("", response_model=RunListResponse)
async def list_runs(
    my_only: bool = True,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunListResponse:
    query = select(AnalysisRun)
    if my_only:
        query = query.where(AnalysisRun.owner_id == current_user.id)
    else:
        query = query.where(
            (AnalysisRun.owner_id == current_user.id) | (AnalysisRun.is_public.is_(True))
        )
    query = query.order_by(AnalysisRun.created_at.desc())

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    runs = (await db.execute(query)).scalars().all()

    return RunListResponse(
        items=[
            RunListItem(
                id=r.id,
                client_name=r.client_name,
                status=r.status,
                is_public=r.is_public,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in runs
        ],
        total=total,
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunResponse:
    run = await _get_run_or_404(run_id, db, current_user)
    return _run_to_response(run)


@router.post("/{run_id}/capacity", response_model=RunResponse)
async def run_capacity(
    run_id: str,
    file: Optional[UploadFile] = File(default=None),
    prioritization_mode: bool = Form(default=False),
    best_fit_mode: bool = Form(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunResponse:
    """Upload masterdata and run capacity analysis, saving result to the run."""
    run = await _get_run_or_404(run_id, db, current_user)

    # Determine file path: either from upload or from persisted path
    tmp_path: Optional[Path] = None
    source_path: Optional[Path] = None

    if file is not None:
        suffix = Path(file.filename or "data.xlsx").suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = Path(tmp.name)
        source_path = tmp_path

        # Persist the file for future re-runs
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        persistent = UPLOAD_DIR / f"{run_id}_masterdata{suffix}"
        persistent.write_bytes(tmp_path.read_bytes())
        run.masterdata_path = str(persistent)

    elif run.masterdata_path:
        source_path = Path(run.masterdata_path)
    else:
        raise HTTPException(
            status_code=422,
            detail="No masterdata file. Upload a file or ensure one was already uploaded.",
        )

    try:
        from src.ingest.pipeline import MasterdataIngestPipeline
        from src.analytics.capacity import CapacityAnalyzer
        from src.core.carriers import CarrierService
        from dataclasses import asdict

        pipeline = MasterdataIngestPipeline()
        ingest_result = pipeline.run(source_path)

        if not ingest_result.mapping_result.is_complete:
            missing = ", ".join(ingest_result.mapping_result.missing_required)
            raise HTTPException(status_code=422, detail=f"Missing columns: {missing}")

        carriers = [c for c in CarrierService().load_all_carriers() if c.is_active]
        analyzer = CapacityAnalyzer(carriers)
        result = analyzer.analyze_dataframe(
            ingest_result.df,
            prioritization_mode=prioritization_mode,
            best_fit_mode=best_fit_mode,
        )

        # Serialize result for JSONB storage
        run.capacity_result = {
            "total_sku": result.total_sku,
            "fit_count": result.fit_count,
            "borderline_count": result.borderline_count,
            "not_fit_count": result.not_fit_count,
            "fit_percentage": result.fit_percentage,
            "carriers_analyzed": result.carriers_analyzed,
            "carrier_stats": {
                cid: asdict(cs) for cid, cs in result.carrier_stats.items()
            },
            "rows": result.df.to_dicts(),
        }
        run.status = "capacity_done"
        run.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(run)
        return _run_to_response(run)

    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


@router.post("/{run_id}/quality", response_model=RunResponse)
async def run_quality(
    run_id: str,
    file: Optional[UploadFile] = File(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunResponse:
    """Upload masterdata and run quality pipeline, saving result to the run."""
    run = await _get_run_or_404(run_id, db, current_user)

    tmp_path: Optional[Path] = None
    source_path: Optional[Path] = None

    if file is not None:
        suffix = Path(file.filename or "data.xlsx").suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = Path(tmp.name)
        source_path = tmp_path

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        persistent = UPLOAD_DIR / f"{run_id}_masterdata{suffix}"
        persistent.write_bytes(tmp_path.read_bytes())
        run.masterdata_path = str(persistent)

    elif run.masterdata_path:
        source_path = Path(run.masterdata_path)
    else:
        raise HTTPException(status_code=422, detail="No masterdata file.")

    try:
        from src.ingest.pipeline import MasterdataIngestPipeline
        from src.quality.pipeline import QualityPipeline
        from src.core.types import MasterdataRow

        ingest = MasterdataIngestPipeline()
        ingest_result = ingest.run(source_path)

        quality_pipeline = QualityPipeline()
        quality_result = quality_pipeline.run(ingest_result.df)

        scorecard = quality_result.metrics_after
        run.quality_result = {
            "total_records": scorecard.total_records,
            "dimensions_coverage_pct": scorecard.dimensions_coverage_pct,
            "weight_coverage_pct": scorecard.weight_coverage_pct,
            "stock_coverage_pct": scorecard.stock_coverage_pct,
            "missing_critical_count": scorecard.missing_critical_count,
            "suspect_outliers_count": scorecard.suspect_outliers_count,
            "high_risk_borderline_count": scorecard.high_risk_borderline_count,
            "duplicates_count": scorecard.duplicates_count,
            "conflicts_count": scorecard.conflicts_count,
            "collisions_count": scorecard.collisions_count,
            "imputed_dimensions_count": scorecard.imputed_dimensions_count,
            "imputed_weight_count": scorecard.imputed_weight_count,
            "overall_score": scorecard.overall_score,
        }
        run.status = "quality_done"
        run.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(run)
        return _run_to_response(run)

    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


async def _get_run_or_404(
    run_id: str, db: AsyncSession, current_user: User
) -> AnalysisRun:
    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.owner_id != current_user.id and not run.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    return run
