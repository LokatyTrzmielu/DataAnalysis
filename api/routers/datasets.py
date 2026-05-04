"""Dataset persistence endpoints — import Excel once, reuse via dataset_id."""

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.models.dataset import Dataset
from api.schemas.dataset import DatasetDetailResponse, DatasetListResponse, DatasetResponse
from src.ingest.pipeline import MasterdataIngestPipeline, OrdersIngestPipeline
from src.storage.data_store import DataStore, hash_bytes

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])

STORE = DataStore()


@router.post("/import", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def import_dataset(
    file: UploadFile = File(..., description="XLSX or CSV file to import"),
    file_type: str = Form(..., description="'masterdata' or 'orders'"),
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
        if file_type == "masterdata":
            pipeline = MasterdataIngestPipeline()
        else:
            pipeline = OrdersIngestPipeline()

        result = pipeline.run(tmp_path)
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
        size_mb=size_mb,
        created_at=row.created_at,
        preview=preview,
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
