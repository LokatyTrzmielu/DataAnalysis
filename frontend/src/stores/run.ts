import { defineStore } from 'pinia'
import { ref } from 'vue'
import { runsApi, type RunDetail, type RunListItem, type RunPatch } from '@/api/runs'

export const useRunStore = defineStore('run', () => {
  const runs = ref<RunListItem[]>([])
  const currentRun = ref<RunDetail | null>(null)
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchRuns(params?: { my_only?: boolean; search?: string; status_filter?: string; sort?: string }) {
    loading.value = true
    error.value = null
    try {
      const { data } = await runsApi.list({ my_only: true, ...params })
      runs.value = data.items
      total.value = data.total
    } catch (e: unknown) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function fetchRun(id: string) {
    loading.value = true
    error.value = null
    try {
      const { data } = await runsApi.get(id)
      currentRun.value = data
    } catch (e: unknown) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function createRun(clientName: string): Promise<RunDetail> {
    const { data } = await runsApi.create(clientName)
    runs.value.unshift(data)
    return data
  }

  async function deleteRun(id: string): Promise<void> {
    await runsApi.delete(id)
    runs.value = runs.value.filter(r => r.id !== id)
    if (currentRun.value?.id === id) currentRun.value = null
  }

  async function patchRun(id: string, patch: RunPatch): Promise<RunDetail> {
    const { data } = await runsApi.patch(id, patch)
    const idx = runs.value.findIndex(r => r.id === id)
    if (idx !== -1) runs.value[idx] = { ...runs.value[idx], ...data }
    if (currentRun.value?.id === id) currentRun.value = data
    return data
  }

  async function duplicateRun(id: string): Promise<RunDetail> {
    const { data } = await runsApi.duplicate(id)
    runs.value.unshift(data)
    return data
  }

  return { runs, currentRun, total, loading, error, fetchRuns, fetchRun, createRun, deleteRun, patchRun, duplicateRun }
})
