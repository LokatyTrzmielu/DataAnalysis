"""Pydantic schemas for dataset API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    file_type: str
    row_count: int
    column_names: list[str] | None
    size_mb: float
    created_at: datetime
    is_duplicate: bool = False


class DatasetListResponse(BaseModel):
    datasets: list[DatasetResponse]
    total: int


class DatasetDetailResponse(DatasetResponse):
    preview: list[dict[str, Any]]
