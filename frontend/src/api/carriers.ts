import client from './client'

export interface Carrier {
  id: string
  carrier_id: string
  name: string
  inner_length_mm: number
  inner_width_mm: number
  inner_height_mm: number
  max_weight_kg: number
  is_predefined: boolean
  is_active: boolean
  priority: number | null
}

export interface CarrierCreate {
  carrier_id: string
  name: string
  inner_length_mm: number
  inner_width_mm: number
  inner_height_mm: number
  max_weight_kg: number
  is_active?: boolean
  priority?: number | null
}

export const carriersApi = {
  list: () => client.get<Carrier[]>('/carriers'),
  create: (data: CarrierCreate) => client.post<Carrier>('/carriers', data),
  update: (carrierId: string, data: Partial<Carrier>) =>
    client.patch<Carrier>(`/carriers/${carrierId}`, data),
  delete: (carrierId: string) => client.delete(`/carriers/${carrierId}`),
}
