import client from './client'

export interface RunListItem {
  id: string
  client_name: string
  status: string
  is_public: boolean
  created_at: string
  updated_at: string
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
}

export interface CapacityResult {
  total_sku: number
  fit_count: number
  borderline_count: number
  not_fit_count: number
  fit_percentage: number
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

export interface PerformanceResult {
  kpi: PerformanceKPI
  daily_metrics: PerformanceDailyMetric[]
  datehour_metrics: PerformanceDateHourMetric[]
  sku_pareto: PerformanceSKUPareto[]
  date_from: string
  date_to: string
  has_hourly_data: boolean
}

export const runsApi = {
  list: (params?: { my_only?: boolean; page?: number; page_size?: number }) =>
    client.get<RunListResponse>('/runs', { params }),

  get: (id: string) => client.get<RunDetail>(`/runs/${id}`),

  create: (client_name: string) =>
    client.post<RunDetail>('/runs', { client_name }),

  runCapacity: (id: string, file: File | null, opts?: { prioritization_mode?: boolean; best_fit_mode?: boolean; borderline_threshold?: number }) => {
    const fd = new FormData()
    if (file) fd.append('file', file)
    if (opts?.prioritization_mode) fd.append('prioritization_mode', 'true')
    if (opts?.best_fit_mode) fd.append('best_fit_mode', 'true')
    if (opts?.borderline_threshold != null) fd.append('borderline_threshold', String(opts.borderline_threshold))
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
