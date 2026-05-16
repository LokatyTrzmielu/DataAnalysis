"""Pydantic schemas for the Container Order Calculator tool."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class EligibleAnalysis(BaseModel):
    """One completed analysis suitable for container ordering (uses MiB carrier)."""

    run_id: str
    client_name: str
    status: str
    created_at: datetime
    sku_count: int
    fit_count: int
    fit_pct: float
    has_performance: bool
    abc_distribution: dict[str, int] = Field(default_factory=dict)  # {"A": n, "B": n, "C": n}


class PlanParamsRequest(BaseModel):
    """User-controlled planning parameters submitted from frontend."""

    abc_classes: list[str] = ["A", "B"]
    only_machine: bool = True
    include_borderline: bool = True

    stock_multiplier: float = 1.0
    location_fill_rate: float = 0.9
    min_locations_per_sku: int = 1
    max_locations_per_sku: int = 50000

    mode: Literal["auto", "guided", "manual"] = "auto"
    auto_max_variants: int = 6
    auto_goal: Literal["min_waste", "min_bins", "max_coverage"] = "min_waste"
    guided_preset: Literal["simple", "standard", "full_coverage"] = "standard"
    manual_variant_codes: list[str] = []


class VariantInfo(BaseModel):
    """Catalog entry — sent to frontend so it can render cards / 3D preview."""

    code: str
    footprint_key: str
    footprint_label: str
    cell_length_mm: int
    cell_width_mm: int
    cell_height_mm: int
    bin_height_mm: int
    locations_per_bin: int
    max_weight_kg_per_cell: float
    cell_volume_L: float
    in_auto_catalog: bool


class AssignmentRow(BaseModel):
    sku: str
    variant_code: Optional[str] = None
    locations: int
    bins: int
    cell_fill_pct: float
    abc_class: Optional[str] = None
    recommendation: Optional[str] = None
    length_mm: float
    width_mm: float
    height_mm: float
    weight_kg: float
    stock_volume_L: float


class VariantSummaryRow(BaseModel):
    code: str
    footprint_key: str
    footprint_label: str
    bin_height_mm: int
    cell_length_mm: int
    cell_width_mm: int
    cell_height_mm: int
    locations_per_bin: int
    sku_count: int
    total_locations: int
    bins_required: int
    avg_fill_pct: float


class ContainerPlanResponse(BaseModel):
    run_id: str
    client_name: str
    total_bins: int
    total_sku_planned: int
    total_sku_covered: int
    coverage_pct: float
    avg_fill_pct: float
    selected_variant_codes: list[str]
    summaries: list[VariantSummaryRow]
    assignments: list[AssignmentRow]
    orphans: list[AssignmentRow]
    params_echo: dict[str, Any]


class CatalogResponse(BaseModel):
    auto_codes: list[str]
    full: list[VariantInfo]


class ExportRequest(BaseModel):
    run_id: str
    params: PlanParamsRequest
    plan: ContainerPlanResponse
    format: Literal["xlsx", "pdf", "csv"]
