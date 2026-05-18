"""Tools router — data preparation utilities."""

import json
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

import polars as pl
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db
from api.models.dataset import Dataset
from api.models.user import User
from api.schemas.dataset import DatasetResponse
from api.schemas.runs import ColumnSuggestion, MappingInspectResponse
from api.services.time_saving import record_event as record_time_saving_event
from src.storage.data_store import DataStore, hash_bytes

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])

STORE = DataStore()


@router.post("/data-preparation/inspect", response_model=MappingInspectResponse)
async def inspect_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    current_user: User = Depends(get_current_user),
) -> MappingInspectResponse:
    """Inspect a single file and return column suggestions for column mapping."""
    if file_type not in {"masterdata", "orders"}:
        raise HTTPException(status_code=422, detail="file_type must be 'masterdata' or 'orders'")

    suffix = Path(file.filename or "data.xlsx").suffix
    content = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        from src.ingest.readers import FileReader
        from src.ingest.mapping import MappingWizard, MASTERDATA_SCHEMA, ORDERS_SCHEMA

        schema = MASTERDATA_SCHEMA if file_type == "masterdata" else ORDERS_SCHEMA
        schema_type = file_type

        reader = FileReader(tmp_path)
        try:
            preview_df = reader.read(n_rows=5)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Cannot read file: {exc}. Make sure the file is a valid CSV or Excel.",
            ) from exc
        columns = preview_df.columns

        wizard = MappingWizard(schema, schema_type)
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
            {"name": field_name, "required": field_cfg["required"], "description": field_cfg["description"]}
            for field_name, field_cfg in schema.items()
        ]

        return MappingInspectResponse(
            run_id="",
            file_columns=columns,
            suggestions=suggestions,
            missing_required=mapping_result.missing_required,
            preview_rows=preview_df.to_dicts(),
            schema_fields=schema_fields,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/data-preparation/merge", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def merge_files(
    files: List[UploadFile] = File(...),
    file_type: str = Form(...),
    mapping_json: str = Form(...),
    name: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetResponse:
    """Merge multiple files using a shared column mapping and save as a Dataset."""
    if file_type not in {"masterdata", "orders"}:
        raise HTTPException(status_code=422, detail="file_type must be 'masterdata' or 'orders'")
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required")

    from src.ingest.pipeline import MasterdataIngestPipeline, OrdersIngestPipeline
    from src.ingest.mapping import MappingResult, ColumnMapping, MASTERDATA_SCHEMA, ORDERS_SCHEMA

    schema = MASTERDATA_SCHEMA if file_type == "masterdata" else ORDERS_SCHEMA
    pipeline = MasterdataIngestPipeline() if file_type == "masterdata" else OrdersIngestPipeline()

    raw_mapping = json.loads(mapping_json)
    mr = MappingResult()
    for target_field, source_col in raw_mapping.items():
        if source_col:
            mr.mappings[target_field] = ColumnMapping(
                target_field=target_field,
                source_column=source_col,
                confidence=1.0,
                is_auto=False,
            )
    required_fields = [f for f, cfg in schema.items() if cfg["required"]]
    mr.missing_required = [f for f in required_fields if f not in mr.mappings]

    dfs: list[pl.DataFrame] = []
    tmp_paths: list[Path] = []

    try:
        for i, upload in enumerate(files):
            suffix = Path(upload.filename or "data.xlsx").suffix
            content = await upload.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            tmp_paths.append(tmp_path)

            try:
                result = pipeline.run(tmp_path, mapping=mr)
                dfs.append(result.df)
            except Exception as exc:
                raise HTTPException(
                    status_code=422,
                    detail=f"Failed to process file '{upload.filename}': {exc}",
                )

        merged = pl.concat(dfs, how="diagonal_relaxed")

        if file_type == "masterdata" and "sku" in merged.columns:
            merged = merged.unique(subset=["sku"], keep="last", maintain_order=True)

        dataset_id = str(uuid.uuid4())
        first_filename = files[0].filename or "merged"
        dataset_name = name or f"merged_{first_filename}"
        file_hash = hash_bytes(dataset_name.encode())

        duckdb_path = STORE.save(dataset_id, merged, file_type)

        dataset = Dataset(
            id=dataset_id,
            name=dataset_name,
            file_type=file_type,
            row_count=merged.height,
            duckdb_path=str(duckdb_path),
            file_hash=file_hash,
            column_names=merged.columns,
        )
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)

        await record_time_saving_event(
            db,
            current_user.id,
            "data_preparation_merge",
            file_count=len(files),
            row_count=merged.height,
        )

        size_mb = round(duckdb_path.stat().st_size / 1_048_576, 2)
        return DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            file_type=dataset.file_type,
            row_count=dataset.row_count,
            column_names=dataset.column_names,
            notes=dataset.notes,
            size_mb=size_mb,
            created_at=dataset.created_at,
        )
    finally:
        for p in tmp_paths:
            p.unlink(missing_ok=True)
