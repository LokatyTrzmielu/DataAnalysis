import client from './client'

export interface Dataset {
  id: string
  name: string
  file_type: 'masterdata' | 'orders'
  row_count: number
  column_names: string[] | null
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

export const datasetsApi = {
  import: (file: File, file_type: 'masterdata' | 'orders') => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('file_type', file_type)
    return client.post<Dataset>('/datasets/import', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  list: () => client.get<DatasetListResponse>('/datasets'),

  get: (id: string) => client.get<DatasetDetail>(`/datasets/${id}`),

  delete: (id: string) => client.delete<void>(`/datasets/${id}`),
}
