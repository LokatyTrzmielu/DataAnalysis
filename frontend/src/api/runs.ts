import client from './client'

export interface RunListItem {
  id: string
  client_name: string
  status: string
  is_public: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

export interface RunPatch {
  client_name?: string
  is_public?: boolean
  notes?: string
}

export interface RunShareItem {
  user_id: string
  email: string
  name: string
  shared_at: string
}

export interface DateGap {
  from: string
  to: string
  days: number
}

export interface OrdersValidationResult {
  // Summary KPIs
  total_rows: number
  date_from: string | null
  date_to: string | null
  unique_days: number
  has_hourly_data: boolean
  // Missing SKUs
  missing_sku_count: number
  missing_sku_pct: number
  // Date gaps
  date_coverage_pct: number
  total_calendar_days: number
  gap_count: number
  max_gap_days: number
  gap_list: DateGap[]
  // Quantity anomalies
  qty_null_count: number
  qty_zero_count: number
  qty_negative_count: number
  qty_outlier_count: number
  qty_outlier_threshold: number
  // SKU cross-validation
  sku_xval_available: boolean
  orders_skus_not_in_masterdata_count: number
  orders_skus_not_in_masterdata: string[]
  masterdata_skus_not_in_orders_count: number
  masterdata_skus_not_in_orders: string[]
  // Weekday distribution
  weekday_distribution: Record<string, number>
  most_active_weekday: number | null
  least_active_weekday: number | null
}

export interface RunDetail extends RunListItem {
  owner_id: string
  masterdata_path: string | null
  orders_path: string | null
  masterdata_mapping: Record<string, unknown> | null
  orders_mapping: Record<string, unknown> | null
  quality_result: Record<string, unknown> | null
  capacity_result: CapacityResult | null
  performance_result: PerformanceResult | null
  analysis_config: Record<string, unknown> | null
  orders_validation_result: OrdersValidationResult | null
}

export interface CapacityResult {
  total_sku: number
  fit_count: number
  borderline_count: number
  not_fit_count: number
  fit_percentage: number
  avg_length_mm: number
  avg_width_mm: number
  avg_height_mm: number
  avg_weight_kg: number
  carriers_analyzed: string[]
  carrier_stats: Record<string, CarrierStats>
  rows: CapacityRow[]
}

export interface CarrierStats {
  carrier_id: string
  carrier_name: string
  fit_count: number
  borderline_count: number
  not_fit_count: number
  fit_percentage: number
  total_volume_m3: number
  stock_volume_m3: number
  total_locations_required: number
  avg_filling_rate: number
}

export interface CapacityRow {
  sku: string
  carrier_id: string
  fit_status: 'FIT' | 'BORDERLINE' | 'NOT_FIT'
  units_per_carrier: number
  volume_m3: number
  stock_volume_m3: number
  limiting_factor: string
  margin_mm: number | null
  locations_required: number
  filling_rate: number
  stored_volume_L: number
  carrier_volume_L: number
  length_mm: number
  width_mm: number
  height_mm: number
  weight_kg: number
}

export interface RunListResponse {
  items: RunListItem[]
  total: number
}

export interface ColumnSuggestion {
  source_column: string
  suggested_target: string | null
  confidence: number
}

export interface MappingInspectResponse {
  run_id: string
  file_columns: string[]
  suggestions: ColumnSuggestion[]
  missing_required: string[]
  preview_rows: Record<string, unknown>[]
  schema_fields: { name: string; required: boolean; description: string }[]
}

export interface PerformanceKPI {
  total_lines: number
  total_orders: number
  total_units: number
  unique_sku: number
  avg_lines_per_hour: number
  avg_orders_per_hour: number
  avg_units_per_hour: number
  avg_lines_per_order: number
  peak_lines_per_hour: number
  p90_lines_per_hour: number
  p95_lines_per_hour: number
  p99_lines_per_hour: number
}

export interface PerformanceDailyMetric {
  date: string
  lines: number
  orders: number
  units: number
}

export interface PerformanceDateHourMetric {
  date: string
  hour: number
  lines: number
}

export interface PerformanceSKUPareto {
  sku: string
  total_lines: number
  total_units: number
  total_orders: number
  frequency_rank: number
  cumulative_pct: number
  abc_class: string
}

export interface PerformanceHourlyMetric {
  hour: number
  lines: number
}

export interface PerformanceWeeklyTrend {
  year: number
  week: number
  lines: number
  avg_lines_per_hour: number
}

export interface PerformanceWeekdayPoint {
  day: string
  avg_lines: number
}

export interface PerformanceLinesPerOrderBin {
  bin: string
  count: number
}

export interface PerformanceResult {
  kpi: PerformanceKPI
  daily_metrics: PerformanceDailyMetric[]
  datehour_metrics: PerformanceDateHourMetric[]
  hourly_metrics: PerformanceHourlyMetric[]
  weekly_trends: PerformanceWeeklyTrend[]
  weekday_profile: PerformanceWeekdayPoint[]
  lines_per_order_dist: PerformanceLinesPerOrderBin[]
  sku_pareto: PerformanceSKUPareto[]
  date_from: string
  date_to: string
  has_hourly_data: boolean
}

export const runsApi = {
  list: (params?: { my_only?: boolean; page?: number; page_size?: number; search?: string; status_filter?: string; sort?: string }) =>
    client.get<RunListResponse>('/runs', { params }),

  get: (id: string) => client.get<RunDetail>(`/runs/${id}`),

  create: (client_name: string) =>
    client.post<RunDetail>('/runs', { client_name }),

  delete: (id: string) =>
    client.delete<void>(`/runs/${id}`),

  patch: (id: string, data: RunPatch) =>
    client.patch<RunDetail>(`/runs/${id}`, data),

  duplicate: (id: string) =>
    client.post<RunDetail>(`/runs/${id}/duplicate`),

  getShares: (id: string) =>
    client.get<RunShareItem[]>(`/runs/${id}/shares`),

  addShare: (id: string, email: string) =>
    client.post<RunShareItem>(`/runs/${id}/shares`, { email }),

  removeShare: (id: string, userId: string) =>
    client.delete<void>(`/runs/${id}/shares/${userId}`),

  runCapacity: (id: string, file: File | null, opts?: { prioritization_mode?: boolean; best_fit_mode?: boolean; borderline_threshold?: number; carrier_ids?: string[] }) => {
    const fd = new FormData()
    if (file) fd.append('file', file)
    if (opts?.prioritization_mode) fd.append('prioritization_mode', 'true')
    if (opts?.best_fit_mode) fd.append('best_fit_mode', 'true')
    if (opts?.borderline_threshold != null) fd.append('borderline_threshold', String(opts.borderline_threshold))
    if (opts?.carrier_ids?.length) fd.append('carrier_ids', opts.carrier_ids.join(','))
    return client.post<RunDetail>(`/runs/${id}/capacity`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  runQuality: (id: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return client.post<RunDetail>(`/runs/${id}/quality`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  inspectMasterdata: (id: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return client.post<MappingInspectResponse>(`/runs/${id}/masterdata/inspect`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  runQualityWithMapping: (id: string, file: File | null, mapping: Record<string, string>) => {
    const fd = new FormData()
    if (file) fd.append('file', file)
    fd.append('mapping_json', JSON.stringify(mapping))
    return client.post<RunDetail>(`/runs/${id}/quality`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  inspectOrders: (id: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return client.post<MappingInspectResponse>(`/runs/${id}/orders/inspect`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  ingestOrders: (id: string, mapping: Record<string, string>) => {
    const fd = new FormData()
    fd.append('mapping_json', JSON.stringify(mapping))
    return client.post<RunDetail>(`/runs/${id}/orders/ingest`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  runPerformance: (id: string, productiveHours: number) => {
    const fd = new FormData()
    fd.append('productive_hours', String(productiveHours))
    return client.post<RunDetail>(`/runs/${id}/performance`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  downloadZip: (id: string) =>
    client.get(`/runs/${id}/reports/zip`, { responseType: 'blob' }),

  downloadPdf: (id: string) =>
    client.get(`/runs/${id}/reports/pdf`, { responseType: 'blob' }),

  downloadCsvReport: (id: string, reportName: string) =>
    client.get(`/runs/${id}/reports/csv/${reportName}`, { responseType: 'blob' }),
}
