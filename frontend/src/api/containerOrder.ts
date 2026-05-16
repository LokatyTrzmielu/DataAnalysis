import client from './client'

export interface EligibleAnalysis {
  run_id: string
  client_name: string
  status: string
  created_at: string
  sku_count: number
  fit_count: number
  fit_pct: number
  has_performance: boolean
  abc_distribution: Record<string, number>
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
  bins_required: number
  avg_fill_pct: number
}

export interface ContainerPlan {
  run_id: string
  client_name: string
  total_bins: number
  total_sku_planned: number
  total_sku_covered: number
  coverage_pct: number
  avg_fill_pct: number
  selected_variant_codes: string[]
  summaries: VariantSummaryRow[]
  assignments: AssignmentRow[]
  orphans: AssignmentRow[]
  params_echo: Record<string, unknown>
}

export interface CatalogResponse {
  auto_codes: string[]
  full: VariantInfo[]
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
}

export function defaultParams(): PlanParams {
  return {
    abc_classes: ['A', 'B'],
    only_machine: true,
    include_borderline: true,
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
