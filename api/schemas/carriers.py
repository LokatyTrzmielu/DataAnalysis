"""Carrier request/response schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class CarrierCreate(BaseModel):
    carrier_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    inner_length_mm: float = Field(..., gt=0)
    inner_width_mm: float = Field(..., gt=0)
    inner_height_mm: float = Field(..., gt=0)
    max_weight_kg: float = Field(..., gt=0)
    is_active: bool = True
    priority: Optional[int] = Field(default=None, ge=1)


class CarrierUpdate(BaseModel):
    name: Optional[str] = None
    inner_length_mm: Optional[float] = Field(default=None, gt=0)
    inner_width_mm: Optional[float] = Field(default=None, gt=0)
    inner_height_mm: Optional[float] = Field(default=None, gt=0)
    max_weight_kg: Optional[float] = Field(default=None, gt=0)
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=1)


class CarrierResponse(BaseModel):
    id: str
    carrier_id: str
    name: str
    inner_length_mm: float
    inner_width_mm: float
    inner_height_mm: float
    max_weight_kg: float
    is_predefined: bool
    is_active: bool
    priority: Optional[int]
