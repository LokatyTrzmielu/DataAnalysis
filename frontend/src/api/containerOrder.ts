import client from './client'

export interface EligibleAnalysis {
  run_id: string
  client_name: string
  status: string
  created_at: string
  sku_count: number          // total unique SKUs in dataset
  fit_count: number          // global FIT (best across analyzed carriers)
  fit_pct: number            // global FIT+BORDERLINE %
  has_performance: boolean
  abc_distribution: Record<string, number>
  // MiB-specific — what the planner actually uses
  mib_fit_count: number
  mib_borderline_count: number
  mib_not_fit_count: number
  mib_fit_pct: number
  mib_planned_sku: number    // FIT + BORDERLINE for MiB
  carriers_analyzed: string[]
}

export interface VariantInfo {
  code: string
  footprint_key: string
  footprint_label: string
  cell_length_mm: number
  cell_width_mm: number
  cell_height_mm: number
  bin_height_mm: number
  locations_per_bin: number
  max_weight_kg_per_cell: number
  cell_volume_L: number
  in_auto_catalog: boolean
}

export interface PlanParams {
  abc_classes: string[]
  only_machine: boolean
  include_borderline: boolean
  impute_missing_dimensions: boolean
  stock_multiplier: number
  location_fill_rate: number
  min_locations_per_sku: number
  max_locations_per_sku: number
  mode: 'auto' | 'guided' | 'manual'
  auto_max_variants: number
  auto_goal: 'min_waste' | 'min_bins' | 'max_coverage'
  guided_preset: 'simple' | 'standard' | 'full_coverage'
  manual_variant_codes: string[]
}

export interface AssignmentRow {
  sku: string
  variant_code: string | null
  locations: number
  bins: number
  cell_fill_pct: number
  abc_class: string | null
  recommendation: string | null
  length_mm: number
  width_mm: number
  height_mm: number
  weight_kg: number
  stock_volume_L: number
  pcs_per_location: number   // pieces of this SKU planned per allocated location
  fit_status: string | null
  dimensions_imputed: boolean
  orphan_reason: string | null
}

export interface VariantSummaryRow {
  code: string
  footprint_key: string
  footprint_label: string
  bin_height_mm: number
  cell_length_mm: number
  cell_width_mm: number
  cell_height_mm: number
  locations_per_bin: number
  sku_count: number
  total_locations: number
  bins_required: number       // also = bases (1 base per bin)
  avg_fill_pct: number
  frames_per_bin: number
  total_frames_required: number
  dividers_required: number     // bins × locations_per_bin
  total_weight_kg: number       // Σ stocked weight assigned to this variant (stock only)
  bin_gross_weight_kg: number   // avg full bin weight = stock per bin + empty-bin tare
}

export interface ContainerPlan {
  run_id: string
  client_name: string
  total_bins: number           // also = total bases
  total_sku_planned: number
  total_sku_covered: number
  coverage_pct: number
  avg_fill_pct: number
  selected_variant_codes: string[]
  summaries: VariantSummaryRow[]
  assignments: AssignmentRow[]
  orphans: AssignmentRow[]
  params_echo: Record<string, unknown>
  total_frames: number
}

export interface CatalogResponse {
  auto_codes: string[]
  full: VariantInfo[]
}

// ── Saved plans (history) ────────────────────────────────────────────────

export interface SavedPlanResponse {
  id: string
  label: string
  client_name: string
  source_run_id: string | null
  source_run_available: boolean
  created_at: string
  updated_at: string
  total_bins: number
  total_frames: number
  total_sku_covered: number
  coverage_pct: number
  mode: string
  notes: string | null
}

export interface SavedPlanDetail extends SavedPlanResponse {
  params: PlanParams
  plan: ContainerPlan
}

export interface SavedPlanListResponse {
  items: SavedPlanResponse[]
  total: number
}

export interface SavedPlanPatch {
  label?: string | null
  notes?: string | null
}

export const containerOrderApi = {
  getCatalog: () => client.get<CatalogResponse>('/tools/container-order/catalog'),

  listEligibleAnalyses: () =>
    client.get<EligibleAnalysis[]>('/tools/container-order/eligible-analyses'),

  calculate: (runId: string, params: PlanParams) =>
    client.post<ContainerPlan>(`/tools/container-order/calculate/${runId}`, params),

  exportFile: (runId: string, params: PlanParams, plan: ContainerPlan,
               format: 'xlsx' | 'pdf' | 'csv') =>
    client.post(
      `/tools/container-order/export/${runId}`,
      { run_id: runId, params, plan, format },
      { responseType: 'blob' },
    ),

  // history
  listSavedPlans: (page = 1, pageSize = 20) =>
    client.get<SavedPlanListResponse>('/tools/container-order/plans', {
      params: { page, page_size: pageSize },
    }),

  savePlan: (
    runId: string,
    params: PlanParams,
    plan: ContainerPlan,
    label?: string,
    notes?: string,
  ) =>
    client.post<SavedPlanResponse>('/tools/container-order/plans', {
      run_id: runId,
      params,
      plan,
      label: label || null,
      notes: notes || null,
    }),

  getSavedPlan: (planId: string) =>
    client.get<SavedPlanDetail>(`/tools/container-order/plans/${planId}`),

  patchSavedPlan: (planId: string, patch: SavedPlanPatch) =>
    client.patch<SavedPlanResponse>(`/tools/container-order/plans/${planId}`, patch),

  deleteSavedPlan: (planId: string) =>
    client.delete(`/tools/container-order/plans/${planId}`),
}

export function defaultParams(): PlanParams {
  return {
    abc_classes: ['A', 'B'],
    only_machine: true,
    include_borderline: true,
    impute_missing_dimensions: true,
    stock_multiplier: 1.0,
    location_fill_rate: 0.9,
    min_locations_per_sku: 1,
    max_locations_per_sku: 50000,
    mode: 'auto',
    auto_max_variants: 6,
    auto_goal: 'min_waste',
    guided_preset: 'standard',
    manual_variant_codes: [],
  }
}
