<template>
  <div>
    <div class="mb-6">
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:var(--app-text);line-height:1.14;letter-spacing:-0.28px">
        Welcome, {{ auth.user?.name }}
      </h2>
      <p class="mt-1" style="font-size:17px;color:var(--app-text-sec);letter-spacing:-0.374px">
        Warehouse capacity &amp; performance analytics
      </p>
    </div>

    <!-- Quick actions -->
    <div class="grid grid-cols-1 sm:grid-cols-3" style="gap:20px;margin-bottom:40px">
      <button
        @click="newAnalysis"
        class="btn-apple-primary text-left"
        style="border-radius:8px;height:auto;flex-direction:column;align-items:flex-start;gap:4px;padding:20px;width:100%"
      >
        <div style="font-size:14px;font-weight:600">New Analysis</div>
        <div style="font-size:12px;opacity:0.8">Start capacity / quality run</div>
      </button>
      <RouterLink
        to="/runs"
        class="card-apple block"
        style="text-decoration:none"
      >
        <div style="font-size:14px;font-weight:600;color:var(--app-text)">History</div>
        <div class="mt-1" style="font-size:12px;color:var(--app-text-sec)">Browse past analyses</div>
      </RouterLink>
      <RouterLink
        to="/carriers"
        class="card-apple block"
        style="text-decoration:none"
      >
        <div style="font-size:14px;font-weight:600;color:var(--app-text)">Carriers</div>
        <div class="mt-1" style="font-size:12px;color:var(--app-text-sec)">Manage carrier configs</div>
      </RouterLink>
    </div>

    <!-- Two-column layout: KPIs left, list right -->
    <div style="display:flex;gap:28px;align-items:flex-start">

    <!-- Left: selected analysis details -->
    <div style="flex:1;min-width:0">
    <div v-if="latestRun">
      <div class="flex items-center gap-3 mb-3">
        <RouterLink :to="openLink" class="btn-apple-primary" style="font-size:13px;padding:5px 14px;line-height:1">
          Open
        </RouterLink>
        <span style="font-size:17px;font-weight:500;color:#0071e3;letter-spacing:-0.374px">{{ latestRun.client_name }}</span>
      </div>

      <!-- Pipeline status steps -->
      <div class="card-apple" style="margin-bottom:24px">
        <div class="flex items-center gap-0">
          <div
            v-for="(step, i) in pipelineSteps"
            :key="step.id"
            class="flex items-center"
          >
            <div class="flex flex-col items-center">
              <div :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
              ]" :style="step.done ? 'background:#0071e3;color:#fff' : 'background:var(--app-border);color:var(--app-placeholder)'">
                {{ step.done ? '✓' : i + 1 }}
              </div>
              <span class="text-xs mt-1 text-center w-16" :style="step.done ? 'color:#0071e3;font-weight:600' : 'color:var(--app-placeholder)'">
                {{ step.label }}
              </span>
            </div>
            <div v-if="i < pipelineSteps.length - 1" class="w-8 h-0.5 mb-5" :style="step.done ? 'background:rgba(0,113,227,0.4)' : 'background:var(--app-border)'"></div>
          </div>
        </div>
      </div>

      <!-- KPI summary -->
      <div style="display:flex;flex-direction:column;gap:16px">

        <!-- Masterdata -->
        <div>
          <p style="font-size:11px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.4px;text-transform:uppercase;margin-bottom:8px">Masterdata</p>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Total SKU</p>
              <p v-if="quality" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ quality.total_records?.toLocaleString() ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Quality not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Quality Score</p>
              <p v-if="quality" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ quality.overall_score?.toFixed(1) ?? '—' }}%</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Quality not run</p>
            </div>
          </div>
        </div>

        <!-- Capacity -->
        <div>
          <p style="font-size:11px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.4px;text-transform:uppercase;margin-bottom:8px">Capacity</p>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Fit %</p>
              <p v-if="capacity" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ capacity.fit_percentage?.toFixed(1) ?? '—' }}%</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Capacity not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Fit</p>
              <p v-if="capacity" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ capacity.fit_count?.toLocaleString() ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Capacity not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Not Fit</p>
              <p v-if="capacity" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ capacity.not_fit_count?.toLocaleString() ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Capacity not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Avg Dimensions</p>
              <p v-if="avgDimensions" style="font-size:15px;font-weight:600;color:var(--app-text);line-height:1.3;overflow-wrap:break-word">{{ avgDimensions }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Capacity not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Avg Weight</p>
              <p v-if="capacity" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ capacity.avg_weight_kg?.toFixed(2) ?? '—' }} kg</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Capacity not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Carriers selected</p>
              <p v-if="capacity" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ capacity.carriers_analyzed?.length ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Capacity not run</p>
            </div>
          </div>
        </div>

        <!-- Cross-validation -->
        <div>
          <p style="font-size:11px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.4px;text-transform:uppercase;margin-bottom:8px">SKU Cross-validation</p>
          <div class="card-apple" style="max-width:340px">
            <template v-if="ovr?.sku_xval_available">
              <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px">
                <span style="font-size:12px;color:var(--app-text-sec)">Orders → MD</span>
                <span style="font-size:17px;font-weight:600;color:var(--app-text)">
                  {{ ovr.orders_skus_not_in_masterdata_count.toLocaleString() }}
                  <span v-if="xvalOrdersPct" style="font-size:13px;font-weight:400;color:var(--app-text-sec)"> ({{ xvalOrdersPct }}%)</span>
                </span>
              </div>
              <div style="display:flex;justify-content:space-between;align-items:baseline">
                <span style="font-size:12px;color:var(--app-text-sec)">MD → Orders</span>
                <span style="font-size:17px;font-weight:600;color:var(--app-text)">
                  {{ ovr.masterdata_skus_not_in_orders_count.toLocaleString() }}
                  <span v-if="xvalMDPct" style="font-size:13px;font-weight:400;color:var(--app-text-sec)"> ({{ xvalMDPct }}%)</span>
                </span>
              </div>
            </template>
            <p v-else-if="ovr && !ovr.sku_xval_available" style="font-size:12px;color:var(--app-placeholder)">Masterdata not available for cross-val</p>
            <p v-else style="font-size:12px;color:var(--app-placeholder)">Orders not ingested</p>
          </div>
        </div>

        <!-- Orders -->
        <div>
          <p style="font-size:11px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.4px;text-transform:uppercase;margin-bottom:8px">Orders</p>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Total rows</p>
              <p v-if="ovr" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ ovr.total_rows?.toLocaleString() ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Orders not ingested</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Unique days</p>
              <p v-if="ovr" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ ovr.unique_days?.toLocaleString() ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Orders not ingested</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Unique SKU</p>
              <p v-if="perf" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ perf.kpi?.unique_sku?.toLocaleString() ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Performance not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Hourly data</p>
              <p v-if="ovr" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ ovr.has_hourly_data ? 'Yes' : 'No' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Orders not ingested</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Total Orders</p>
              <p v-if="perf" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ perf.kpi?.total_orders?.toLocaleString() ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Performance not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Total Lines</p>
              <p v-if="perf" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ perf.kpi?.total_lines?.toLocaleString() ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Performance not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Avg Orders/Hour</p>
              <p v-if="perf" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ perf.kpi?.avg_orders_per_hour?.toFixed(1) ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Performance not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Avg Lines/Order</p>
              <p v-if="perf" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ perf.kpi?.avg_lines_per_order?.toFixed(2) ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Performance not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Avg Pieces/Order</p>
              <p v-if="perf" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ perf.kpi?.avg_units_per_order?.toFixed(2) ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Performance not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Avg Lines/Hour</p>
              <p v-if="perf" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ perf.kpi?.avg_lines_per_hour?.toFixed(1) ?? '—' }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Performance not run</p>
            </div>
            <div class="card-apple">
              <p style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:4px">Avg Pieces/Line</p>
              <p v-if="avgPiecesPerLine" style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19">{{ avgPiecesPerLine }}</p>
              <p v-else style="font-size:12px;color:var(--app-placeholder);margin-top:4px">Performance not run</p>
            </div>
          </div>
        </div>

      </div>
    </div>
    <div v-else style="font-size:14px;color:var(--app-text-sec);padding-top:8px">
      Select an analysis from the list.
    </div>
    </div><!-- /left col -->

    <!-- Right: Recent analyses list -->
    <div style="width:270px;flex-shrink:0;position:sticky;top:20px">
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Recent analyses</h3>
      <div v-if="runStore.loading" style="font-size:14px;color:var(--app-text-sec)">Loading…</div>
      <div v-else-if="runStore.runs.length === 0" style="font-size:14px;color:var(--app-text-sec)">
        No analyses yet. Create one above.
      </div>
      <div v-else class="card-apple-list" style="max-height:calc(100vh - 180px);overflow-y:auto">
        <div v-for="run in runStore.runs.slice(0, 20)" :key="run.id">
          <div
            :class="['flex items-center justify-between px-4 py-3 transition-colors cursor-pointer', selectedRunId === run.id ? 'bg-[rgba(0,113,227,0.06)]' : 'hover:bg-black/[.02]']"
            @click="selectRun(run.id)"
            @dblclick="router.push({ path: `/runs/${run.id}`, query: { tab: tabFromStatus(run.status) } })"
          >
            <div class="flex-1 min-w-0 text-left">
              <div style="font-size:14px;color:var(--app-text);letter-spacing:-0.224px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ run.client_name }}</div>
              <div class="flex items-center gap-2 mt-0.5">
                <StatusBadge :status="run.status" />
                <span style="font-size:11px;color:var(--app-text-sec)">{{ formatDate(run.created_at) }}</span>
              </div>
            </div>
            <button
              @click.stop="toggleNotes(run.id)"
              :class="['p-1.5 rounded transition-colors ml-2 flex-shrink-0']"
              :style="openNotesId === run.id || run.notes ? 'color:#0071e3' : 'color:var(--app-placeholder)'"
              title="Notes"
            >
              <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
              </svg>
            </button>
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
    </div><!-- /right col -->

    </div><!-- /two-column layout -->

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

function tabFromDetail(run: RunDetail): string {
  if (run.performance_result) return 'performance'
  if (run.capacity_result) return 'capacity'
  if (run.quality_result || run.orders_validation_result) return 'quality'
  return 'import'
}

function tabFromStatus(status: string): string {
  if (status === 'performance_done' || status === 'orders_ingested') return 'performance'
  if (status === 'capacity_done') return 'capacity'
  if (status === 'quality_done') return 'quality'
  return 'import'
}
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

const openLink = computed(() => {
  if (!latestRun.value) return '/'
  return { path: `/runs/${latestRun.value.id}`, query: { tab: tabFromDetail(latestRun.value) } }
})

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
    await runStore.fetchRun(id)
    latestRun.value = runStore.currentRun
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

const capacity = computed(() => latestRun.value?.capacity_result ?? null)
const quality  = computed(() => latestRun.value?.quality_result as any ?? null)
const perf     = computed(() => latestRun.value?.performance_result ?? null)
const ovr      = computed(() => latestRun.value?.orders_validation_result ?? null)

const avgDimensions = computed(() => {
  if (!capacity.value) return null
  const { avg_length_mm: l, avg_width_mm: w, avg_height_mm: h } = capacity.value
  if (l == null || w == null || h == null) return null
  return `${l.toFixed(0)}×${w.toFixed(0)}×${h.toFixed(0)} mm`
})

const avgPiecesPerLine = computed(() => {
  const k = perf.value?.kpi
  if (!k || !k.total_lines) return null
  return (k.total_units / k.total_lines).toFixed(2)
})

const xvalOrdersPct = computed(() => {
  const xv = ovr.value
  const uniqueSku = perf.value?.kpi?.unique_sku
  if (!xv || !uniqueSku) return null
  return ((xv.orders_skus_not_in_masterdata_count / uniqueSku) * 100).toFixed(1)
})

const xvalMDPct = computed(() => {
  const xv = ovr.value
  const total = quality.value?.total_records
  if (!xv || !total) return null
  return ((xv.masterdata_skus_not_in_orders_count / total) * 100).toFixed(1)
})

const pipelineSteps = computed(() => {
  const status = latestRun.value?.status ?? ''
  const hasQuality = !!latestRun.value?.quality_result
  const hasCapacity = !!latestRun.value?.capacity_result
  const hasPerformance = !!latestRun.value?.performance_result
  const hasOrders = status === 'orders_ingested' || status === 'performance_done'

  return [
    { id: 'created', label: 'Created', done: !!latestRun.value },
    { id: 'masterdata', label: 'Import', done: !!latestRun.value?.masterdata_path || hasOrders },
    { id: 'quality', label: 'Validation', done: hasQuality || hasOrders },
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
