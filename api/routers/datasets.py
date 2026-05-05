"""Dataset persistence endpoints — import Excel once, reuse via dataset_id."""

import json
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.models.dataset import Dataset
from api.schemas.dataset import (
    DatasetColumnSuggestion,
    DatasetDetailResponse,
    DatasetInspectResponse,
    DatasetListResponse,
    DatasetResponse,
)
from src.ingest.mapping import MASTERDATA_SCHEMA, ORDERS_SCHEMA, ColumnMapping, MappingResult, MappingWizard
from src.ingest.pipeline import MasterdataIngestPipeline, OrdersIngestPipeline
from src.ingest.readers import FileReader
from src.storage.data_store import DataStore, hash_bytes

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])

STORE = DataStore()


@router.post("/inspect", response_model=DatasetInspectResponse)
async def inspect_dataset(
    file: UploadFile = File(..., description="XLSX or CSV file to inspect"),
    file_type: str = Form(..., description="'masterdata' or 'orders'"),
) -> DatasetInspectResponse:
    """Read file columns and return mapping suggestions + preview. File is NOT persisted."""
    if file_type not in {"masterdata", "orders"}:
        raise HTTPException(status_code=422, detail="file_type must be 'masterdata' or 'orders'")
    if file.filename:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in {".xlsx", ".xls", ".csv"}:
            raise HTTPException(status_code=422, detail=f"Unsupported file type '{suffix}'")

    content = await file.read()
    suffix_str = Path(file.filename or "data.xlsx").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix_str) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        reader = FileReader(tmp_path)
        preview_df = reader.read(n_rows=5)
        columns = list(preview_df.columns)

        schema = MASTERDATA_SCHEMA if file_type == "masterdata" else ORDERS_SCHEMA
        wizard = MappingWizard(schema, file_type)
        mapping_result = wizard.auto_map(columns)

        suggestions = []
        for col in columns:
            col_suggestions = wizard.get_suggestions(col)
            best = col_suggestions[0] if col_suggestions else None
            suggestions.append(DatasetColumnSuggestion(
                source_column=col,
                suggested_target=best[0] if best else None,
                confidence=best[1] if best else 0.0,
            ))

        schema_fields = [
            {"name": name, "required": cfg["required"], "description": cfg["description"]}
            for name, cfg in schema.items()
        ]
        preview_rows = preview_df.to_dicts()
    finally:
        tmp_path.unlink(missing_ok=True)

    return DatasetInspectResponse(
        file_columns=columns,
        suggestions=suggestions,
        missing_required=mapping_result.missing_required,
        preview_rows=preview_rows,
        schema_fields=schema_fields,
    )


@router.post("/import", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def import_dataset(
    file: UploadFile = File(..., description="XLSX or CSV file to import"),
    file_type: str = Form(..., description="'masterdata' or 'orders'"),
    mapping_json: str | None = Form(default=None, description="JSON mapping: target_field -> source_column"),
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Import an Excel/CSV file, persist it as a DuckDB dataset, and return a dataset_id.

    Each upload always creates a new independent dataset — the same file can be imported
    multiple times for use across different analysis sessions.
    """
    if file_type not in {"masterdata", "orders"}:
        raise HTTPException(status_code=422, detail="file_type must be 'masterdata' or 'orders'")

    if file.filename:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in {".xlsx", ".xls", ".csv"}:
            raise HTTPException(status_code=422, detail=f"Unsupported file type '{suffix}'")

    content = await file.read()
    file_hash = hash_bytes(content)

    # Save to temp file so the pipeline can read by path
    suffix_str = Path(file.filename or "data.xlsx").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix_str) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        parsed_mapping: MappingResult | None = None
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
            parsed_mapping = mr

        if file_type == "masterdata":
            pipeline = MasterdataIngestPipeline()
        else:
            pipeline = OrdersIngestPipeline()

        result = pipeline.run(tmp_path, mapping=parsed_mapping)
    finally:
        tmp_path.unlink(missing_ok=True)

    # Persist DataFrame to DuckDB file
    dataset_id = str(uuid.uuid4())
    duckdb_path = STORE.save(dataset_id, result.df, file_type)

    # Store metadata in SQLite
    dataset = Dataset(
        id=dataset_id,
        name=file.filename or "unnamed",
        file_type=file_type,
        row_count=result.rows_imported,
        duckdb_path=str(duckdb_path),
        file_hash=file_hash,
        column_names=result.df.columns,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

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


@router.get("", response_model=DatasetListResponse)
async def list_datasets(db: AsyncSession = Depends(get_db)) -> DatasetListResponse:
    """List all imported datasets."""
    rows = (await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))).scalars().all()
    items = []
    for row in rows:
        size_mb = STORE.get_info(row.id)["size_mb"] if STORE.exists(row.id) else 0.0
        items.append(DatasetResponse(
            id=row.id,
            name=row.name,
            file_type=row.file_type,
            row_count=row.row_count,
            column_names=row.column_names,
            notes=row.notes,
            size_mb=size_mb,
            created_at=row.created_at,
        ))
    return DatasetListResponse(datasets=items, total=len(items))


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> DatasetDetailResponse:
    """Get dataset info and a preview of the first 10 rows."""
    row = (await db.execute(select(Dataset).where(Dataset.id == dataset_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not STORE.exists(dataset_id):
        raise HTTPException(status_code=404, detail="Dataset file missing from disk")

    size_mb = STORE.get_info(dataset_id)["size_mb"]
    preview = STORE.preview(dataset_id, row.file_type)
    return DatasetDetailResponse(
        id=row.id,
        name=row.name,
        file_type=row.file_type,
        row_count=row.row_count,
        column_names=row.column_names,
        notes=row.notes,
        size_mb=size_mb,
        created_at=row.created_at,
        preview=preview,
    )


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def patch_dataset(
    dataset_id: str,
    notes: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Update mutable fields on a dataset (currently: notes)."""
    row = (await db.execute(select(Dataset).where(Dataset.id == dataset_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    row.notes = notes
    await db.commit()
    await db.refresh(row)
    size_mb = STORE.get_info(dataset_id)["size_mb"] if STORE.exists(dataset_id) else 0.0
    return DatasetResponse(
        id=row.id,
        name=row.name,
        file_type=row.file_type,
        row_count=row.row_count,
        column_names=row.column_names,
        notes=row.notes,
        size_mb=size_mb,
        created_at=row.created_at,
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a dataset and its DuckDB file from disk."""
    row = (await db.execute(select(Dataset).where(Dataset.id == dataset_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    STORE.delete(dataset_id)
    await db.delete(row)
    await db.commit()
