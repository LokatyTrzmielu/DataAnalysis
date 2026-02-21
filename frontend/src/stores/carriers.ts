import { defineStore } from 'pinia'
import { ref } from 'vue'
import { carriersApi, type Carrier, type CarrierCreate } from '@/api/carriers'

export const useCarriersStore = defineStore('carriers', () => {
  const carriers = ref<Carrier[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchCarriers() {
    loading.value = true
    error.value = null
    try {
      const { data } = await carriersApi.list()
      carriers.value = data
    } catch (e: unknown) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function createCarrier(data: CarrierCreate) {
    const { data: carrier } = await carriersApi.create(data)
    carriers.value.push(carrier)
    return carrier
  }

  async function deleteCarrier(carrierId: string) {
    await carriersApi.delete(carrierId)
    carriers.value = carriers.value.filter((c) => c.carrier_id !== carrierId)
  }

  return { carriers, loading, error, fetchCarriers, createCarrier, deleteCarrier }
})
