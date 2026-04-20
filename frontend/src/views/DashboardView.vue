<template>
  <div>
    <div class="mb-6">
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:#1d1d1f;line-height:1.14;letter-spacing:-0.28px">
        Welcome, {{ auth.user?.name }}
      </h2>
      <p class="mt-1" style="font-size:17px;color:rgba(0,0,0,0.48);letter-spacing:-0.374px">
        Warehouse capacity &amp; performance analytics
      </p>
    </div>

    <!-- Quick actions -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      <button
        @click="newAnalysis"
        class="btn-apple-primary rounded-lg p-4 text-left"
        style="border-radius:8px;height:auto;flex-direction:column;align-items:flex-start;gap:4px"
      >
        <div style="font-size:14px;font-weight:600">New Analysis</div>
        <div style="font-size:12px;opacity:0.8">Start capacity / quality run</div>
      </button>
      <RouterLink
        to="/runs"
        class="card-apple block hover:shadow-sm transition-shadow"
        style="text-decoration:none"
      >
        <div style="font-size:14px;font-weight:600;color:#1d1d1f">History</div>
        <div class="mt-1" style="font-size:12px;color:rgba(0,0,0,0.48)">Browse past analyses</div>
      </RouterLink>
      <RouterLink
        to="/carriers"
        class="card-apple block hover:shadow-sm transition-shadow"
        style="text-decoration:none"
      >
        <div style="font-size:14px;font-weight:600;color:#1d1d1f">Carriers</div>
        <div class="mt-1" style="font-size:12px;color:rgba(0,0,0,0.48)">Manage carrier configs</div>
      </RouterLink>
    </div>

    <!-- Latest run summary -->
    <div v-if="latestRun" class="mb-8">
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:#1d1d1f;letter-spacing:-0.224px">
        Latest analysis:
        <span style="color:#0071e3">{{ latestRun.client_name }}</span>
        <RouterLink :to="`/runs/${latestRun.id}`" class="ml-2" style="font-size:12px;font-weight:400;color:#0066cc;text-decoration:none" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">
          Open →
        </RouterLink>
      </h3>

      <!-- Pipeline status steps -->
      <div class="card-apple mb-4">
        <div class="flex items-center gap-0">
          <div
            v-for="(step, i) in pipelineSteps"
            :key="step.id"
            class="flex items-center"
          >
            <div class="flex flex-col items-center">
              <div :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                step.done ? 'text-white' : 'text-[rgba(0,0,0,0.32)]',
              ]" :style="step.done ? 'background:#0071e3' : 'background:rgba(0,0,0,0.06)'">
                {{ step.done ? '✓' : i + 1 }}
              </div>
              <span class="text-xs mt-1 text-center w-16" :style="step.done ? 'color:#0071e3;font-weight:600' : 'color:rgba(0,0,0,0.32)'">
                {{ step.label }}
              </span>
            </div>
            <div v-if="i < pipelineSteps.length - 1" class="w-8 h-0.5 mb-5" :style="step.done ? 'background:rgba(0,113,227,0.4)' : 'background:rgba(0,0,0,0.1)'"></div>
          </div>
        </div>
      </div>

      <!-- KPI summary -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="card-apple">
          <p style="font-size:12px;color:rgba(0,0,0,0.48);letter-spacing:-0.12px;margin-bottom:4px">Total SKUs</p>
          <p v-if="latestRun.quality_result" style="font-size:21px;font-weight:600;color:#1d1d1f;line-height:1.19">{{ (latestRun.quality_result as any).total_records?.toLocaleString() ?? '—' }}</p>
          <p v-else style="font-size:12px;color:rgba(0,0,0,0.32);margin-top:4px">Quality not run</p>
        </div>
        <div class="card-apple">
          <p style="font-size:12px;color:rgba(0,0,0,0.48);letter-spacing:-0.12px;margin-bottom:4px">Quality Score</p>
          <p v-if="latestRun.quality_result" style="font-size:21px;font-weight:600;color:#1d1d1f;line-height:1.19">{{ (latestRun.quality_result as any).overall_score?.toFixed(1) ?? '—' }}%</p>
          <p v-else style="font-size:12px;color:rgba(0,0,0,0.32);margin-top:4px">Quality not run</p>
        </div>
        <div class="card-apple">
          <p style="font-size:12px;color:rgba(0,0,0,0.48);letter-spacing:-0.12px;margin-bottom:4px">Fit %</p>
          <p v-if="latestRun.capacity_result" style="font-size:21px;font-weight:600;color:#1d1d1f;line-height:1.19">{{ (latestRun.capacity_result as any).fit_percentage?.toFixed(1) ?? '—' }}%</p>
          <p v-else style="font-size:12px;color:rgba(0,0,0,0.32);margin-top:4px">Capacity not run</p>
        </div>
        <div class="card-apple">
          <p style="font-size:12px;color:rgba(0,0,0,0.48);letter-spacing:-0.12px;margin-bottom:4px">Total Lines</p>
          <p v-if="latestRun.performance_result" style="font-size:21px;font-weight:600;color:#1d1d1f;line-height:1.19">{{ (latestRun.performance_result as any).kpi?.total_lines?.toLocaleString() ?? '—' }}</p>
          <p v-else style="font-size:12px;color:rgba(0,0,0,0.32);margin-top:4px">Performance not run</p>
        </div>
        <div class="card-apple">
          <p style="font-size:12px;color:rgba(0,0,0,0.48);letter-spacing:-0.12px;margin-bottom:4px">Avg Lines/Hour</p>
          <p v-if="latestRun.performance_result" style="font-size:21px;font-weight:600;color:#1d1d1f;line-height:1.19">{{ (latestRun.performance_result as any).kpi?.avg_lines_per_hour?.toFixed(1) ?? '—' }}</p>
          <p v-else style="font-size:12px;color:rgba(0,0,0,0.32);margin-top:4px">Performance not run</p>
        </div>
      </div>
    </div>

    <!-- Recent runs list -->
    <div>
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:#1d1d1f;letter-spacing:-0.224px">Recent analyses</h3>
      <div v-if="runStore.loading" style="font-size:14px;color:rgba(0,0,0,0.48)">Loading…</div>
      <div v-else-if="runStore.runs.length === 0" style="font-size:14px;color:rgba(0,0,0,0.48)">
        No analyses yet. Create one above.
      </div>
      <div v-else class="card-apple-list">
        <div v-for="run in runStore.runs.slice(0, 5)" :key="run.id">
          <div
            :class="['flex items-center justify-between px-4 py-3 transition-colors cursor-pointer', selectedRunId === run.id ? 'bg-[rgba(0,113,227,0.06)]' : 'hover:bg-black/[.02]']"
            @dblclick="router.push(`/runs/${run.id}`)"
          >
            <button @click="selectRun(run.id)" class="flex-1 min-w-0 text-left">
              <span style="font-size:17px;color:#1d1d1f;letter-spacing:-0.374px">{{ run.client_name }}</span>
              <span class="ml-2" style="font-size:12px;color:rgba(0,0,0,0.48)">{{ formatDate(run.created_at) }}</span>
            </button>
            <div class="flex items-center gap-1 shrink-0 ml-3">
              <StatusBadge :status="run.status" />
              <button
                @click="toggleNotes(run.id)"
                :class="['p-1.5 rounded transition-colors']"
                :style="openNotesId === run.id || run.notes ? 'color:#0071e3' : 'color:rgba(0,0,0,0.32)'"
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
              class="input-apple-sm resize-none"
              style="font-size:14px"
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
    await selectRun(runStore.runs[0]!.id)
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
