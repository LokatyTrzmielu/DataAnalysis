"""Analysis run request/response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class RunCreate(BaseModel):
    client_name: str


class ColumnSuggestion(BaseModel):
    source_column: str
    suggested_target: Optional[str] = None
    confidence: float


class MappingInspectResponse(BaseModel):
    run_id: str
    file_columns: list[str]
    suggestions: list[ColumnSuggestion]
    missing_required: list[str]
    preview_rows: list[dict]
    schema_fields: list[dict]


class RunResponse(BaseModel):
    id: str
    owner_id: str
    client_name: str
    status: str
    masterdata_path: Optional[str] = None
    orders_path: Optional[str] = None
    masterdata_mapping: Optional[dict[str, Any]] = None
    orders_mapping: Optional[dict[str, Any]] = None
    quality_result: Optional[dict[str, Any]] = None
    capacity_result: Optional[dict[str, Any]] = None
    performance_result: Optional[dict[str, Any]] = None
    analysis_config: Optional[dict[str, Any]] = None
    is_public: bool
    created_at: datetime
    updated_at: datetime


class RunListItem(BaseModel):
    id: str
    client_name: str
    status: str
    is_public: bool
    created_at: datetime
    updated_at: datetime


class RunListResponse(BaseModel):
    items: list[RunListItem]
    total: int
