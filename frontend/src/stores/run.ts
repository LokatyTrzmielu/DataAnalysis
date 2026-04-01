import { defineStore } from 'pinia'
import { ref } from 'vue'
import { runsApi, type RunDetail, type RunListItem } from '@/api/runs'

export const useRunStore = defineStore('run', () => {
  const runs = ref<RunListItem[]>([])
  const currentRun = ref<RunDetail | null>(null)
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchRuns(myOnly = true) {
    loading.value = true
    error.value = null
    try {
      const { data } = await runsApi.list({ my_only: myOnly })
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

  return { runs, currentRun, total, loading, error, fetchRuns, fetchRun, createRun }
})
