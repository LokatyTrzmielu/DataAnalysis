import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  containerOrderApi,
  defaultParams,
  type ContainerPlan,
  type EligibleAnalysis,
  type PlanParams,
  type VariantInfo,
} from '@/api/containerOrder'

export const useContainerOrderStore = defineStore('containerOrder', () => {
  const eligible = ref<EligibleAnalysis[]>([])
  const catalogFull = ref<VariantInfo[]>([])
  const catalogAutoCodes = ref<string[]>([])

  const currentRun = ref<EligibleAnalysis | null>(null)
  const params = ref<PlanParams>(defaultParams())
  const plan = ref<ContainerPlan | null>(null)

  const loading = ref(false)
  const error = ref('')

  async function loadEligible() {
    loading.value = true
    error.value = ''
    try {
      const { data } = await containerOrderApi.listEligibleAnalyses()
      eligible.value = data
    } catch (e) {
      error.value = (e as Error).message || 'Failed to load analyses.'
    } finally {
      loading.value = false
    }
  }

  async function loadCatalog() {
    if (catalogFull.value.length) return
    const { data } = await containerOrderApi.getCatalog()
    catalogFull.value = data.full
    catalogAutoCodes.value = data.auto_codes
  }

  function selectRun(run: EligibleAnalysis | null) {
    currentRun.value = run
    plan.value = null
  }

  function updateParams(patch: Partial<PlanParams>) {
    params.value = { ...params.value, ...patch }
  }

  function resetParams() {
    params.value = defaultParams()
  }

  async function calculate(): Promise<ContainerPlan | null> {
    if (!currentRun.value) return null
    loading.value = true
    error.value = ''
    try {
      const { data } = await containerOrderApi.calculate(currentRun.value.run_id, params.value)
      plan.value = data
      return data
    } catch (e) {
      error.value = (e as Error).message || 'Calculation failed.'
      plan.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  async function exportFile(format: 'xlsx' | 'pdf' | 'csv'): Promise<Blob | null> {
    if (!currentRun.value || !plan.value) return null
    const { data } = await containerOrderApi.exportFile(
      currentRun.value.run_id, params.value, plan.value, format,
    )
    return data as Blob
  }

  function reset() {
    currentRun.value = null
    plan.value = null
    params.value = defaultParams()
    error.value = ''
  }

  return {
    eligible, catalogFull, catalogAutoCodes, currentRun, params, plan,
    loading, error,
    loadEligible, loadCatalog, selectRun, updateParams, resetParams,
    calculate, exportFile, reset,
  }
})
