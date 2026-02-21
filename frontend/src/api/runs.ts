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
  performance_result: Record<string, unknown> | null
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

export const runsApi = {
  list: (params?: { my_only?: boolean; page?: number; page_size?: number }) =>
    client.get<RunListResponse>('/runs', { params }),

  get: (id: string) => client.get<RunDetail>(`/runs/${id}`),

  create: (client_name: string) =>
    client.post<RunDetail>('/runs', { client_name }),

  runCapacity: (id: string, file: File, opts?: { prioritization_mode?: boolean; best_fit_mode?: boolean }) => {
    const fd = new FormData()
    fd.append('file', file)
    if (opts?.prioritization_mode) fd.append('prioritization_mode', 'true')
    if (opts?.best_fit_mode) fd.append('best_fit_mode', 'true')
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

  downloadZip: (id: string) =>
    client.get(`/runs/${id}/reports/zip`, { responseType: 'blob' }),
}
