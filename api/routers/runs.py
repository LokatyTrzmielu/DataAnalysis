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
from api.schemas.runs import (
    RunCreate, RunListItem, RunListResponse, RunResponse,
    MappingInspectResponse, ColumnSuggestion,
)
from api.schemas.analysis import CapacityResponse
import json

import tempfile

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

UPLOAD_DIR = Path("uploads")


def _run_to_response(run: AnalysisRun) -> RunResponse:
    return RunResponse(
        id=run.id,
        owner_id=run.owner_id,
        client_name=run.client_name,
        status=run.status,
        masterdata_path=run.masterdata_path,
        orders_path=run.orders_path,
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


@router.post("/{run_id}/masterdata/inspect", response_model=MappingInspectResponse)
async def inspect_masterdata(
    run_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MappingInspectResponse:
    """Upload masterdata file, save it and return column suggestions + preview rows."""
    run = await _get_run_or_404(run_id, db, current_user)

    suffix = Path(file.filename or "data.xlsx").suffix
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    persistent = UPLOAD_DIR / f"{run_id}_masterdata{suffix}"
    content = await file.read()
    persistent.write_bytes(content)
    run.masterdata_path = str(persistent)
    run.updated_at = datetime.now(timezone.utc)
    await db.commit()

    from src.ingest.readers import FileReader
    from src.ingest.mapping import MappingWizard, MASTERDATA_SCHEMA

    reader = FileReader(persistent)
    preview_df = reader.read(n_rows=5)
    columns = preview_df.columns

    wizard = MappingWizard(MASTERDATA_SCHEMA, "masterdata")
    mapping_result = wizard.auto_map(columns)

    suggestions = []
    for col in columns:
        col_suggestions = wizard.get_suggestions(col)
        best = col_suggestions[0] if col_suggestions else None
        suggestions.append(ColumnSuggestion(
            source_column=col,
            suggested_target=best[0] if best else None,
            confidence=best[1] if best else 0.0,
        ))

    schema_fields = [
        {
            "name": field_name,
            "required": field_cfg["required"],
            "description": field_cfg["description"],
        }
        for field_name, field_cfg in MASTERDATA_SCHEMA.items()
    ]

    preview_rows = preview_df.to_dicts()

    return MappingInspectResponse(
        run_id=run_id,
        file_columns=columns,
        suggestions=suggestions,
        missing_required=mapping_result.missing_required,
        preview_rows=preview_rows,
        schema_fields=schema_fields,
    )


@router.post("/{run_id}/capacity", response_model=RunResponse)
async def run_capacity(
    run_id: str,
    file: Optional[UploadFile] = File(default=None),
    prioritization_mode: bool = Form(default=False),
    best_fit_mode: bool = Form(default=False),
    borderline_threshold: float = Form(default=2.0),
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
        from src.ingest.mapping import MappingResult, ColumnMapping, MASTERDATA_SCHEMA
        from src.analytics.capacity import CapacityAnalyzer
        from src.core.carriers import CarrierService
        from dataclasses import asdict

        # Reconstruct saved column mapping (set during quality check)
        parsed_mapping: Optional[MappingResult] = None
        if run.masterdata_mapping:
            mr = MappingResult()
            for target_field, source_col in run.masterdata_mapping.items():
                if source_col:
                    mr.mappings[target_field] = ColumnMapping(
                        target_field=target_field,
                        source_column=source_col,
                        confidence=1.0,
                        is_auto=False,
                    )
            required_fields = [f for f, cfg in MASTERDATA_SCHEMA.items() if cfg["required"]]
            mr.missing_required = [f for f in required_fields if f not in mr.mappings]
            parsed_mapping = mr

        pipeline = MasterdataIngestPipeline()
        ingest_result = pipeline.run(source_path, mapping=parsed_mapping)

        if not ingest_result.mapping_result.is_complete:
            missing = ", ".join(ingest_result.mapping_result.missing_required)
            raise HTTPException(status_code=422, detail=f"Missing columns: {missing}")

        carriers = [c for c in CarrierService().load_all_carriers() if c.is_active]
        analyzer = CapacityAnalyzer(carriers, borderline_threshold_mm=borderline_threshold)
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
    mapping_json: Optional[str] = Form(default=None),
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
        from src.ingest.mapping import MappingWizard, MappingResult, ColumnMapping, MASTERDATA_SCHEMA
        from src.quality.pipeline import QualityPipeline

        ingest = MasterdataIngestPipeline()

        # Parse user-supplied mapping if provided
        parsed_mapping: Optional[MappingResult] = None
        if mapping_json:
            raw = json.loads(mapping_json)  # dict: target_field -> source_column
            mr = MappingResult()
            for target_field, source_col in raw.items():
                if source_col:
                    mr.mappings[target_field] = ColumnMapping(
                        target_field=target_field,
                        source_column=source_col,
                        confidence=1.0,
                        is_auto=False,
                    )
            required_fields = [f for f, cfg in MASTERDATA_SCHEMA.items() if cfg["required"]]
            mr.missing_required = [f for f in required_fields if f not in mr.mappings]
            parsed_mapping = mr
            run.masterdata_mapping = raw
            run.updated_at = datetime.now(timezone.utc)

        ingest_result = ingest.run(source_path, mapping=parsed_mapping)

        quality_pipeline = QualityPipeline()
        quality_result = quality_pipeline.run(ingest_result.df)

        metrics = quality_result.metrics_after
        dq = quality_result.dq_lists
        imputation = quality_result.imputation

        imputed_dims = sum(
            s.imputed_count
            for s in (imputation.stats if imputation else [])
            if s.field_name in ("length_mm", "width_mm", "height_mm")
        )
        imputed_weight = sum(
            s.imputed_count
            for s in (imputation.stats if imputation else [])
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
            "overall_score": quality_result.quality_score,
            # Detailed DQ lists for CSV download
            "missing_critical": [
                {"sku": i.sku, "field": i.field, "details": i.details or ""}
                for i in dq.missing_critical
            ],
            "suspect_outliers": [
                {"sku": i.sku, "field": i.field, "details": i.details or ""}
                for i in dq.suspect_outliers
            ],
            "high_risk_borderline": [
                {"sku": i.sku, "field": i.field, "details": i.details or ""}
                for i in dq.high_risk_borderline
            ],
            "duplicates": [
                {"sku": i.sku, "field": i.field, "details": i.details or ""}
                for i in dq.duplicates
            ],
            "conflicts": [
                {"sku": i.sku, "field": i.field, "details": i.details or ""}
                for i in dq.conflicts
            ],
        }
        run.capacity_result = None
        run.status = "quality_done"
        run.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(run)
        return _run_to_response(run)

    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


@router.post("/{run_id}/orders/inspect", response_model=MappingInspectResponse)
async def inspect_orders(
    run_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MappingInspectResponse:
    """Upload orders file, save it and return column suggestions + preview rows."""
    run = await _get_run_or_404(run_id, db, current_user)

    suffix = Path(file.filename or "data.xlsx").suffix
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    persistent = UPLOAD_DIR / f"{run_id}_orders{suffix}"
    content = await file.read()
    persistent.write_bytes(content)
    run.orders_path = str(persistent)
    run.updated_at = datetime.now(timezone.utc)
    await db.commit()

    from src.ingest.readers import FileReader
    from src.ingest.mapping import MappingWizard, ORDERS_SCHEMA

    reader = FileReader(persistent)
    preview_df = reader.read(n_rows=5)
    columns = preview_df.columns

    wizard = MappingWizard(ORDERS_SCHEMA, "orders")
    mapping_result = wizard.auto_map(columns)

    suggestions = []
    for col in columns:
        col_suggestions = wizard.get_suggestions(col)
        best = col_suggestions[0] if col_suggestions else None
        suggestions.append(ColumnSuggestion(
            source_column=col,
            suggested_target=best[0] if best else None,
            confidence=best[1] if best else 0.0,
        ))

    schema_fields = [
        {
            "name": field_name,
            "required": field_cfg["required"],
            "description": field_cfg["description"],
        }
        for field_name, field_cfg in ORDERS_SCHEMA.items()
    ]

    return MappingInspectResponse(
        run_id=run_id,
        file_columns=columns,
        suggestions=suggestions,
        missing_required=mapping_result.missing_required,
        preview_rows=preview_df.to_dicts(),
        schema_fields=schema_fields,
    )


@router.post("/{run_id}/orders/ingest", response_model=RunResponse)
async def ingest_orders(
    run_id: str,
    mapping_json: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunResponse:
    """Ingest orders with the given column mapping."""
    run = await _get_run_or_404(run_id, db, current_user)
    if not run.orders_path:
        raise HTTPException(status_code=422, detail="No orders file. Upload via /orders/inspect first.")

    from src.ingest.pipeline import OrdersIngestPipeline
    from src.ingest.mapping import MappingResult, ColumnMapping, ORDERS_SCHEMA

    parsed_mapping: Optional[MappingResult] = None
    if mapping_json:
        raw = json.loads(mapping_json)
        mr = MappingResult()
        for target_field, source_col in raw.items():
            if source_col:
                mr.mappings[target_field] = ColumnMapping(
                    target_field=target_field,
                    source_column=source_col,
                    confidence=1.0,
                    is_auto=False,
                )
        required_fields = [f for f, cfg in ORDERS_SCHEMA.items() if cfg["required"]]
        mr.missing_required = [f for f in required_fields if f not in mr.mappings]
        parsed_mapping = mr
        run.orders_mapping = raw

    pipeline = OrdersIngestPipeline()
    result = pipeline.run(Path(run.orders_path), mapping=parsed_mapping)

    date_from = None
    date_to = None
    if "order_date" in result.df.columns and result.df.height > 0:
        dates = result.df["order_date"].drop_nulls()
        if dates.len() > 0:
            date_from = str(dates.min())
            date_to = str(dates.max())

    run.analysis_config = {
        **(run.analysis_config or {}),
        "orders_rows": result.rows_imported,
        "orders_has_hourly_data": result.has_hourly_data,
        "orders_date_from": date_from,
        "orders_date_to": date_to,
    }
    run.status = "orders_ingested"
    run.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(run)
    return _run_to_response(run)


@router.post("/{run_id}/performance", response_model=RunResponse)
async def run_performance(
    run_id: str,
    productive_hours: float = Form(default=7.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunResponse:
    """Run performance analysis using saved orders file and mapping."""
    run = await _get_run_or_404(run_id, db, current_user)
    if not run.orders_path:
        raise HTTPException(status_code=422, detail="No orders file. Use /orders/inspect first.")

    from src.ingest.pipeline import OrdersIngestPipeline
    from src.ingest.mapping import MappingResult, ColumnMapping, ORDERS_SCHEMA
    from src.analytics.performance import PerformanceAnalyzer
    from dataclasses import asdict

    # Rebuild mapping from stored orders_mapping
    parsed_mapping: Optional[MappingResult] = None
    if run.orders_mapping:
        mr = MappingResult()
        for target_field, source_col in run.orders_mapping.items():
            if source_col:
                mr.mappings[target_field] = ColumnMapping(
                    target_field=target_field,
                    source_column=source_col,
                    confidence=1.0,
                    is_auto=False,
                )
        required_fields = [f for f, cfg in ORDERS_SCHEMA.items() if cfg["required"]]
        mr.missing_required = [f for f in required_fields if f not in mr.mappings]
        parsed_mapping = mr

    pipeline = OrdersIngestPipeline()
    ingest_result = pipeline.run(Path(run.orders_path), mapping=parsed_mapping)

    analyzer = PerformanceAnalyzer(productive_hours_per_shift=productive_hours)
    perf = analyzer.analyze(ingest_result.df)

    run.performance_result = {
        "kpi": {
            "total_lines": perf.kpi.total_lines,
            "total_orders": perf.kpi.total_orders,
            "total_units": perf.kpi.total_units,
            "unique_sku": perf.kpi.unique_sku,
            "avg_lines_per_hour": perf.kpi.avg_lines_per_hour,
            "avg_orders_per_hour": perf.kpi.avg_orders_per_hour,
            "avg_units_per_hour": perf.kpi.avg_units_per_hour,
            "avg_lines_per_order": perf.kpi.avg_lines_per_order,
            "peak_lines_per_hour": perf.kpi.peak_lines_per_hour,
            "p90_lines_per_hour": perf.kpi.p90_lines_per_hour,
            "p95_lines_per_hour": perf.kpi.p95_lines_per_hour,
            "p99_lines_per_hour": perf.kpi.p99_lines_per_hour,
        },
        "daily_metrics": [
            {"date": str(d.date), "lines": d.lines, "orders": d.orders, "units": d.units}
            for d in perf.daily_metrics
        ],
        "datehour_metrics": [
            {"date": str(dh.date), "hour": dh.hour, "lines": dh.lines}
            for dh in perf.datehour_metrics
        ],
        "sku_pareto": [
            {
                "sku": s.sku,
                "total_lines": s.total_lines,
                "total_units": s.total_units,
                "total_orders": s.total_orders,
                "frequency_rank": s.frequency_rank,
                "cumulative_pct": s.cumulative_pct,
                "abc_class": s.abc_class,
            }
            for s in perf.sku_pareto
        ],
        "date_from": str(perf.date_from),
        "date_to": str(perf.date_to),
        "has_hourly_data": perf.has_hourly_data,
    }
    run.status = "performance_done"
    run.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(run)
    return _run_to_response(run)


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
