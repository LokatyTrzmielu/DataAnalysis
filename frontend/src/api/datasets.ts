import client from './client'

export interface Dataset {
  id: string
  name: string
  file_type: 'masterdata' | 'orders'
  row_count: number
  column_names: string[] | null
  notes: string | null
  size_mb: number
  created_at: string
}

export interface DatasetDetail extends Dataset {
  preview: Record<string, unknown>[]
}

export interface DatasetListResponse {
  datasets: Dataset[]
  total: number
}

export interface DatasetColumnSuggestion {
  source_column: string
  suggested_target: string | null
  confidence: number
}

export interface DatasetInspectResponse {
  file_columns: string[]
  suggestions: DatasetColumnSuggestion[]
  missing_required: string[]
  preview_rows: Record<string, unknown>[]
  schema_fields: { name: string; required: boolean; description: string }[]
}

export const datasetsApi = {
  inspect: (file: File, file_type: 'masterdata' | 'orders') => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('file_type', file_type)
    return client.post<DatasetInspectResponse>('/datasets/inspect', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  import: (file: File, file_type: 'masterdata' | 'orders', mapping?: Record<string, string>) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('file_type', file_type)
    if (mapping) fd.append('mapping_json', JSON.stringify(mapping))
    return client.post<Dataset>('/datasets/import', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  list: () => client.get<DatasetListResponse>('/datasets'),

  patch: (id: string, notes: string | null) => {
    const fd = new FormData()
    if (notes !== null) fd.append('notes', notes)
    return client.patch<Dataset>(`/datasets/${id}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  get: (id: string) => client.get<DatasetDetail>(`/datasets/${id}`),

  delete: (id: string) => client.delete<void>(`/datasets/${id}`),
}
