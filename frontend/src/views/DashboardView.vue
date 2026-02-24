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
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Latest analysis: <span class="text-blue-600">{{ latestRun.client_name }}</span></h3>

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
        <template v-if="latestRun.quality_result">
          <div class="bg-white border border-gray-200 rounded-lg p-3">
            <p class="text-xs text-gray-500">Total SKUs</p>
            <p class="text-lg font-semibold text-gray-800">{{ (latestRun.quality_result as any).total_records?.toLocaleString() ?? '—' }}</p>
          </div>
          <div class="bg-white border border-gray-200 rounded-lg p-3">
            <p class="text-xs text-gray-500">Quality Score</p>
            <p class="text-lg font-semibold text-gray-800">{{ (latestRun.quality_result as any).overall_score?.toFixed(1) ?? '—' }}%</p>
          </div>
        </template>
        <template v-if="latestRun.capacity_result">
          <div class="bg-white border border-gray-200 rounded-lg p-3">
            <p class="text-xs text-gray-500">Fit %</p>
            <p class="text-lg font-semibold text-green-600">{{ (latestRun.capacity_result as any).fit_percentage?.toFixed(1) ?? '—' }}%</p>
          </div>
        </template>
        <template v-if="latestRun.performance_result">
          <div class="bg-white border border-gray-200 rounded-lg p-3">
            <p class="text-xs text-gray-500">Total Lines</p>
            <p class="text-lg font-semibold text-gray-800">{{ (latestRun.performance_result as any).kpi?.total_lines?.toLocaleString() ?? '—' }}</p>
          </div>
          <div class="bg-white border border-gray-200 rounded-lg p-3">
            <p class="text-xs text-gray-500">Avg Lines/Hour</p>
            <p class="text-lg font-semibold text-gray-800">{{ (latestRun.performance_result as any).kpi?.avg_lines_per_hour?.toFixed(1) ?? '—' }}</p>
          </div>
        </template>
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
        <RouterLink
          v-for="run in runStore.runs.slice(0, 5)"
          :key="run.id"
          :to="`/runs/${run.id}`"
          class="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
        >
          <div>
            <span class="text-sm font-medium text-gray-800">{{ run.client_name }}</span>
            <span class="ml-2 text-xs text-gray-400">{{ formatDate(run.created_at) }}</span>
          </div>
          <StatusBadge :status="run.status" />
        </RouterLink>
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

onMounted(async () => {
  await runStore.fetchRuns()
  // Fetch full detail of latest run for KPIs
  if (runStore.runs.length > 0) {
    try {
      const { data } = await runsApi.get(runStore.runs[0].id)
      latestRun.value = data
    } catch {
      // ignore
    }
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
