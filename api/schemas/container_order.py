"""Pydantic schemas for the Container Order Calculator tool."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class EligibleAnalysis(BaseModel):
    """One completed analysis suitable for container ordering (uses MiB carrier).

    Holds both global stats (whole dataset, may include other carriers) and
    MiB-specific stats. The tool only plans SKUs that fit MiB, so the
    ``mib_*`` numbers are what the user should look at.
    """

    run_id: str
    client_name: str
    status: str
    created_at: datetime
    sku_count: int            # total unique SKUs in dataset
    fit_count: int            # global FIT (best status across analyzed carriers)
    fit_pct: float            # global FIT+BORDERLINE share
    has_performance: bool
    abc_distribution: dict[str, int] = Field(default_factory=dict)  # {"A": n, "B": n, "C": n}
    # MiB-specific (the SKUs actually planned by this tool)
    mib_fit_count: int = 0
    mib_borderline_count: int = 0
    mib_not_fit_count: int = 0
    mib_fit_pct: float = 0.0
    mib_planned_sku: int = 0          # FIT + BORDERLINE for MiB
    carriers_analyzed: list[str] = Field(default_factory=list)


class PlanParamsRequest(BaseModel):
    """User-controlled planning parameters submitted from frontend."""

    abc_classes: list[str] = ["A", "B"]
    only_machine: bool = True
    include_borderline: bool = True
    impute_missing_dimensions: bool = True

    stock_multiplier: float = 1.0
    location_fill_rate: float = 0.9
    min_locations_per_sku: int = 1
    max_locations_per_sku: int = 50000

    mode: Literal["auto", "guided", "manual"] = "guided"
    auto_max_variants: int = 6
    auto_goal: Literal["min_waste", "min_bins", "max_coverage"] = "min_waste"
    guided_preset: Literal["simple", "standard", "full_coverage"] = "full_coverage"
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
    # Pieces of this SKU planned per allocated location — derived from
    # masterdata stock and unit volume. Zero for orphans / unknown dimensions.
    pcs_per_location: int = 0
    fit_status: Optional[str] = None
    dimensions_imputed: bool = False
    orphan_reason: Optional[str] = None


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
    # Procurement breakdown — EasyClick frame count needed to build N bins of
    # this variant. Each bin = 1 base (138 mm) + frames_per_bin frames (50 mm each).
    frames_per_bin: int = 0
    total_frames_required: int = 0
    # Total divider walls to order = bins_required × dividers_per_bin,
    # where dividers_per_bin = (n_L − 1) + (n_W − 1). 0 for full-bin and 0
    # unconditionally for tiers above 288 mm (no dividers sold for 338/388).
    dividers_required: int = 0
    # Σ stocked weight assigned to this variant (kg) — *stock only*, no tare.
    # By construction (per-cell net-weight cap), this divided by bins_required
    # plus the 2.35-kg empty-bin tare is ≤ 35 kg.
    total_weight_kg: float = 0.0
    # Avg total bin weight = stock weight per bin + empty-bin tare (~2.35 kg).
    # Surfaces the 35-kg gross cap in exports so the warehouse can verify.
    bin_gross_weight_kg: float = 0.0


class ContainerPlanResponse(BaseModel):
    run_id: str
    client_name: str
    total_bins: int             # also equals total bases (one base per physical bin)
    total_sku_planned: int
    total_sku_covered: int
    coverage_pct: float
    avg_fill_pct: float
    selected_variant_codes: list[str]
    summaries: list[VariantSummaryRow]
    assignments: list[AssignmentRow]
    orphans: list[AssignmentRow]
    params_echo: dict[str, Any]
    total_frames: int = 0       # aggregate EasyClick frame count across all variants


class CatalogResponse(BaseModel):
    auto_codes: list[str]
    full: list[VariantInfo]


class ExportRequest(BaseModel):
    run_id: str
    params: PlanParamsRequest
    plan: ContainerPlanResponse
    format: Literal["xlsx", "pdf", "csv"]


# ── Saved plans (history) ──────────────────────────────────────────────────


class SavedPlanCreate(BaseModel):
    """Body for POST /plans — frontend ships the params + plan it currently
    holds in the Pinia store; server snapshots them under the user's account."""

    run_id: str
    label: Optional[str] = None
    notes: Optional[str] = None
    params: PlanParamsRequest
    plan: ContainerPlanResponse


class SavedPlanPatch(BaseModel):
    """PATCH body for renaming / annotating a saved plan."""

    label: Optional[str] = None
    notes: Optional[str] = None


class SavedPlanResponse(BaseModel):
    """List-view of a saved plan — lightweight (no full plan/params blobs).
    Used by GET /plans and POST /plans."""

    id: str
    label: str
    client_name: str
    source_run_id: Optional[str] = None
    source_run_available: bool
    created_at: datetime
    updated_at: datetime
    # Headline KPIs lifted from the plan snapshot:
    total_bins: int
    total_frames: int
    total_sku_covered: int
    coverage_pct: float
    mode: str
    notes: Optional[str] = None


class SavedPlanDetail(SavedPlanResponse):
    """Full detail — includes the original params and the full plan snapshot,
    enough to restore the Calculation tab UI state from history."""

    params: PlanParamsRequest
    plan: ContainerPlanResponse


class SavedPlanListResponse(BaseModel):
    items: list[SavedPlanResponse]
    total: int
