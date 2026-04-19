<template>
  <div>
    <div class="mb-6">
      <h2 class="text-lg font-semibold text-gray-800">Welcome, {{ auth.user?.name }}</h2>
      <p class="text-sm text-gray-500 mt-1">Warehouse capacity & performance analytics</p>
    </div>

    <!-- Quick actions -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      <button
        @click="newAnalysis"
        class="bg-blue-600 hover:bg-blue-700 text-white rounded-lg p-4 text-left transition-colors"
      >
        <div class="font-medium text-sm">New Analysis</div>
        <div class="text-xs opacity-80 mt-1">Start capacity / quality run</div>
      </button>
      <RouterLink
        to="/runs"
        class="bg-white border border-gray-200 hover:border-blue-400 rounded-lg p-4 text-left transition-colors block"
      >
        <div class="font-medium text-sm text-gray-800">History</div>
        <div class="text-xs text-gray-500 mt-1">Browse past analyses</div>
      </RouterLink>
      <RouterLink
        to="/carriers"
        class="bg-white border border-gray-200 hover:border-blue-400 rounded-lg p-4 text-left transition-colors block"
      >
        <div class="font-medium text-sm text-gray-800">Carriers</div>
        <div class="text-xs text-gray-500 mt-1">Manage carrier configs</div>
      </RouterLink>
    </div>

    <!-- Latest run summary -->
    <div v-if="latestRun" class="mb-8">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">
        Latest analysis: <span class="text-blue-600">{{ latestRun.client_name }}</span>
        <RouterLink :to="`/runs/${latestRun.id}`" class="ml-2 text-xs font-normal text-blue-400 hover:text-blue-600">Open →</RouterLink>
      </h3>

      <!-- Pipeline status steps -->
      <div class="bg-white border border-gray-200 rounded-lg p-4 mb-4">
        <div class="flex items-center gap-0">
          <div
            v-for="(step, i) in pipelineSteps"
            :key="step.id"
            class="flex items-center"
          >
            <div class="flex flex-col items-center">
              <div :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                step.done ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-400',
              ]">
                {{ step.done ? '✓' : i + 1 }}
              </div>
              <span :class="['text-xs mt-1 text-center w-16', step.done ? 'text-blue-600 font-medium' : 'text-gray-400']">
                {{ step.label }}
              </span>
            </div>
            <div v-if="i < pipelineSteps.length - 1" :class="['w-8 h-0.5 mb-5', step.done ? 'bg-blue-300' : 'bg-gray-200']"></div>
          </div>
        </div>
      </div>

      <!-- KPI summary -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="bg-white border border-gray-200 rounded-lg p-3">
          <p class="text-xs text-gray-500">Total SKUs</p>
          <p v-if="latestRun.quality_result" class="text-lg font-semibold text-gray-800">{{ (latestRun.quality_result as any).total_records?.toLocaleString() ?? '—' }}</p>
          <p v-else class="text-xs text-gray-400 mt-1">Quality not run</p>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-3">
          <p class="text-xs text-gray-500">Quality Score</p>
          <p v-if="latestRun.quality_result" class="text-lg font-semibold text-gray-800">{{ (latestRun.quality_result as any).overall_score?.toFixed(1) ?? '—' }}%</p>
          <p v-else class="text-xs text-gray-400 mt-1">Quality not run</p>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-3">
          <p class="text-xs text-gray-500">Fit %</p>
          <p v-if="latestRun.capacity_result" class="text-lg font-semibold text-green-600">{{ (latestRun.capacity_result as any).fit_percentage?.toFixed(1) ?? '—' }}%</p>
          <p v-else class="text-xs text-gray-400 mt-1">Capacity not run</p>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-3">
          <p class="text-xs text-gray-500">Total Lines</p>
          <p v-if="latestRun.performance_result" class="text-lg font-semibold text-gray-800">{{ (latestRun.performance_result as any).kpi?.total_lines?.toLocaleString() ?? '—' }}</p>
          <p v-else class="text-xs text-gray-400 mt-1">Performance not run</p>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-3">
          <p class="text-xs text-gray-500">Avg Lines/Hour</p>
          <p v-if="latestRun.performance_result" class="text-lg font-semibold text-gray-800">{{ (latestRun.performance_result as any).kpi?.avg_lines_per_hour?.toFixed(1) ?? '—' }}</p>
          <p v-else class="text-xs text-gray-400 mt-1">Performance not run</p>
        </div>
      </div>
    </div>

    <!-- Recent runs list -->
    <div>
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Recent analyses</h3>
      <div v-if="runStore.loading" class="text-sm text-gray-400">Loading…</div>
      <div v-else-if="runStore.runs.length === 0" class="text-sm text-gray-400">
        No analyses yet. Create one above.
      </div>
      <div v-else class="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
        <div v-for="run in runStore.runs.slice(0, 5)" :key="run.id">
          <div
            :class="['flex items-center justify-between px-4 py-3 transition-colors cursor-pointer', selectedRunId === run.id ? 'bg-blue-50' : 'hover:bg-gray-50']"
            @dblclick="router.push(`/runs/${run.id}`)"
          >
            <button @click="selectRun(run.id)" class="flex-1 min-w-0 text-left">
              <span class="text-sm font-medium text-gray-800">{{ run.client_name }}</span>
              <span class="ml-2 text-xs text-gray-400">{{ formatDate(run.created_at) }}</span>
            </button>
            <div class="flex items-center gap-1 shrink-0 ml-3">
              <StatusBadge :status="run.status" />
              <button
                @click="toggleNotes(run.id)"
                :class="['p-1.5 rounded transition-colors', openNotesId === run.id || run.notes ? 'text-blue-500 hover:bg-blue-50' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100']"
                title="Notes"
              >
                <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
                </svg>
              </button>
            </div>
          </div>
          <div v-if="openNotesId === run.id" class="px-4 pb-3">
            <textarea
              :value="run.notes ?? ''"
              @input="onDashboardNotesInput(run.id, ($event.target as HTMLTextAreaElement).value)"
              placeholder="Add notes about this analysis…"
              rows="2"
              class="w-full text-sm text-gray-700 border border-gray-200 rounded p-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- New run modal -->
    <NewRunModal v-if="showModal" @close="showModal = false" @created="onCreated" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRunStore } from '@/stores/run'
import type { RunDetail } from '@/api/runs'
import { runsApi } from '@/api/runs'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import NewRunModal from '@/components/analysis/NewRunModal.vue'

const auth = useAuthStore()
const runStore = useRunStore()
const router = useRouter()
const showModal = ref(false)
const latestRun = ref<RunDetail | null>(null)
const selectedRunId = ref<string | null>(null)
const openNotesId = ref<string | null>(null)
let dashboardNotesTimer: ReturnType<typeof setTimeout> | null = null

function toggleNotes(id: string) {
  openNotesId.value = openNotesId.value === id ? null : id
}

function onDashboardNotesInput(id: string, value: string) {
  if (dashboardNotesTimer) clearTimeout(dashboardNotesTimer)
  dashboardNotesTimer = setTimeout(async () => {
    await runStore.patchRun(id, { notes: value })
  }, 500)
}

async function selectRun(id: string) {
  selectedRunId.value = id
  try {
    const { data } = await runsApi.get(id)
    latestRun.value = data
  } catch {
    // ignore
  }
}

onMounted(async () => {
  await runStore.fetchRuns()
  if (runStore.runs.length > 0) {
    await selectRun(runStore.runs[0].id)
  }
})

const pipelineSteps = computed(() => {
  const status = latestRun.value?.status ?? ''
  const hasQuality = !!latestRun.value?.quality_result
  const hasCapacity = !!latestRun.value?.capacity_result
  const hasPerformance = !!latestRun.value?.performance_result
  const hasOrders = status === 'orders_ingested' || status === 'performance_done'

  return [
    { id: 'created', label: 'Created', done: !!latestRun.value },
    { id: 'masterdata', label: 'Masterdata', done: !!latestRun.value?.masterdata_path },
    { id: 'quality', label: 'Quality', done: hasQuality },
    { id: 'capacity', label: 'Capacity', done: hasCapacity },
    { id: 'performance', label: 'Performance', done: hasPerformance },
  ]
})

function newAnalysis() {
  showModal.value = true
}

function onCreated(id: string) {
  showModal.value = false
  router.push(`/runs/${id}`)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
