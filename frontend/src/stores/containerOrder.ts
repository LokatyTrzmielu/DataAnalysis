import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  containerOrderApi,
  defaultParams,
  type ContainerPlan,
  type EligibleAnalysis,
  type PlanParams,
  type SavedPlanResponse,
  type VariantInfo,
} from '@/api/containerOrder'

export const useContainerOrderStore = defineStore('containerOrder', () => {
  const eligible = ref<EligibleAnalysis[]>([])
  const catalogFull = ref<VariantInfo[]>([])
  const catalogAutoCodes = ref<string[]>([])

  const currentRun = ref<EligibleAnalysis | null>(null)
  const params = ref<PlanParams>(defaultParams())
  const plan = ref<ContainerPlan | null>(null)

  // History (saved plans)
  const savedPlans = ref<SavedPlanResponse[]>([])
  const savedPlansTotal = ref(0)
  const savedPlansLoading = ref(false)
  const savedPlansError = ref('')

  // When this is non-null, the currently visible `plan` was loaded from (or
  // saved to) this history entry — used to flip the "Save plan" button to
  // "Saved ✓" so the user can't double-save in one session.
  const currentSavedId = ref<string | null>(null)

  // True when the loaded plan's source AnalysisRun is no longer in DB
  // (e.g. someone deleted the analysis). UI surfaces this as a banner and
  // disables the "Calculate plan" button.
  const sourceMissing = ref(false)

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
    currentSavedId.value = null
    sourceMissing.value = false
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
      // Fresh calculation — this isn't tied to any saved entry anymore.
      currentSavedId.value = null
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
    currentSavedId.value = null
    sourceMissing.value = false
  }

  // ── History ─────────────────────────────────────────────────────────────

  async function listSavedPlans(page = 1, pageSize = 20) {
    savedPlansLoading.value = true
    savedPlansError.value = ''
    try {
      const { data } = await containerOrderApi.listSavedPlans(page, pageSize)
      savedPlans.value = data.items
      savedPlansTotal.value = data.total
    } catch (e) {
      savedPlansError.value = (e as Error).message || 'Failed to load saved plans.'
    } finally {
      savedPlansLoading.value = false
    }
  }

  async function savePlan(label?: string, notes?: string): Promise<SavedPlanResponse | null> {
    if (!currentRun.value || !plan.value) return null
    const { data } = await containerOrderApi.savePlan(
      currentRun.value.run_id, params.value, plan.value, label, notes,
    )
    currentSavedId.value = data.id
    // Prepend to the list if it's already loaded.
    savedPlans.value = [data, ...savedPlans.value]
    savedPlansTotal.value += 1
    return data
  }

  async function loadSavedPlan(planId: string): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await containerOrderApi.getSavedPlan(planId)
      // Restore params + plan from the snapshot.
      params.value = { ...defaultParams(), ...data.params }
      plan.value = data.plan
      currentSavedId.value = data.id
      sourceMissing.value = !data.source_run_available
      // Try to reattach to the source run when it's still around so the user
      // can re-calculate with adjusted params.
      if (data.source_run_available && data.source_run_id) {
        const match = eligible.value.find(e => e.run_id === data.source_run_id)
        if (match) {
          currentRun.value = match
        } else {
          // Eligible list might not be loaded yet — fetch and retry.
          try {
            await loadEligible()
            const retry = eligible.value.find(e => e.run_id === data.source_run_id)
            currentRun.value = retry ?? null
            if (!retry) sourceMissing.value = true
          } catch {
            sourceMissing.value = true
          }
        }
      } else {
        currentRun.value = null
      }
      return true
    } catch (e) {
      error.value = (e as Error).message || 'Failed to load saved plan.'
      return false
    } finally {
      loading.value = false
    }
  }

  async function renameSavedPlan(planId: string, label: string) {
    const { data } = await containerOrderApi.patchSavedPlan(planId, { label })
    const i = savedPlans.value.findIndex(p => p.id === planId)
    if (i !== -1) savedPlans.value[i] = data
    return data
  }

  async function deleteSavedPlan(planId: string) {
    await containerOrderApi.deleteSavedPlan(planId)
    savedPlans.value = savedPlans.value.filter(p => p.id !== planId)
    savedPlansTotal.value = Math.max(0, savedPlansTotal.value - 1)
    if (currentSavedId.value === planId) currentSavedId.value = null
  }

  return {
    eligible, catalogFull, catalogAutoCodes, currentRun, params, plan,
    loading, error,
    loadEligible, loadCatalog, selectRun, updateParams, resetParams,
    calculate, exportFile, reset,
    // history
    savedPlans, savedPlansTotal, savedPlansLoading, savedPlansError,
    currentSavedId, sourceMissing,
    listSavedPlans, savePlan, loadSavedPlan, renameSavedPlan, deleteSavedPlan,
  }
})
