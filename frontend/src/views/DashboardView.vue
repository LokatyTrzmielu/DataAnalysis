<template>
  <div>
    <DashboardSidebar
      :selected-id="selectedId"
      @select="onSelect"
      @created="onCreated"
      @open="onOpen"
    />

    <div class="mb-6">
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:var(--app-text);line-height:1.14;letter-spacing:-0.28px">
        Welcome, {{ auth.user?.name }}
      </h2>
      <p class="mt-1" style="font-size:17px;color:var(--app-text-sec);letter-spacing:-0.374px">
        Warehouse capacity &amp; performance analytics
      </p>
    </div>

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
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
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

          <!-- Carrier breakdown table -->
          <div v-if="carrierRows.length" class="card-apple" style="margin-top:12px;padding:0;overflow:hidden">
            <div style="overflow-x:auto">
              <table style="width:100%;border-collapse:collapse;font-size:12px">
                <thead>
                  <tr style="border-bottom:1px solid var(--app-border)">
                    <th style="text-align:left;padding:8px 12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.2px;white-space:nowrap">Carrier</th>
                    <th style="text-align:right;padding:8px 12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.2px;white-space:nowrap">Fit %</th>
                    <th style="text-align:right;padding:8px 12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.2px;white-space:nowrap">FIT</th>
                    <th style="text-align:right;padding:8px 12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.2px;white-space:nowrap">BORDERLINE</th>
                    <th style="text-align:right;padding:8px 12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.2px;white-space:nowrap">NOT FIT</th>
                    <th style="text-align:right;padding:8px 12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.2px;white-space:nowrap">Locations</th>
                    <th style="text-align:right;padding:8px 12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.2px;white-space:nowrap">Volume (m³)</th>
                    <th style="text-align:right;padding:8px 12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.2px;white-space:nowrap">Stock vol. (m³)</th>
                    <th style="text-align:right;padding:8px 12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.2px;white-space:nowrap">Filling rate</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(cs, i) in carrierRows"
                    :key="cs.carrier_id"
                    :style="i % 2 === 1 ? 'background:var(--app-surface-alt, rgba(0,0,0,0.02))' : ''"
                  >
                    <td style="padding:7px 12px;color:var(--app-text);font-weight:500;white-space:nowrap">{{ cs.carrier_name }}</td>
                    <td style="padding:7px 12px;text-align:right;color:var(--app-text);font-variant-numeric:tabular-nums">{{ cs.fit_percentage.toFixed(1) }}%</td>
                    <td style="padding:7px 12px;text-align:right;color:#1a9e5c;font-weight:600;font-variant-numeric:tabular-nums">{{ cs.fit_count.toLocaleString() }}</td>
                    <td style="padding:7px 12px;text-align:right;color:#e07b00;font-variant-numeric:tabular-nums">{{ cs.borderline_count.toLocaleString() }}</td>
                    <td style="padding:7px 12px;text-align:right;color:#d93025;font-variant-numeric:tabular-nums">{{ cs.not_fit_count.toLocaleString() }}</td>
                    <td style="padding:7px 12px;text-align:right;color:var(--app-text);font-variant-numeric:tabular-nums">{{ cs.total_locations_required.toLocaleString() }}</td>
                    <td style="padding:7px 12px;text-align:right;color:var(--app-text);font-variant-numeric:tabular-nums">{{ cs.total_volume_m3.toFixed(2) }}</td>
                    <td style="padding:7px 12px;text-align:right;color:var(--app-text);font-variant-numeric:tabular-nums">{{ cs.stock_volume_m3.toFixed(2) }}</td>
                    <td style="padding:7px 12px;text-align:right;color:var(--app-text);font-variant-numeric:tabular-nums">{{ (cs.avg_filling_rate * 100).toFixed(1) }}%</td>
                  </tr>
                </tbody>
              </table>
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
          <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
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
      Select an analysis from the sidebar.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRunStore } from '@/stores/run'
import type { RunDetail } from '@/api/runs'
import DashboardSidebar from '@/components/layout/DashboardSidebar.vue'

function tabFromDetail(run: RunDetail): string {
  if (run.performance_result) return 'performance'
  if (run.capacity_result) return 'capacity'
  if (run.quality_result || run.orders_validation_result) return 'quality'
  return 'import'
}

const auth = useAuthStore()
const runStore = useRunStore()
const router = useRouter()

const latestRun = computed<RunDetail | null>(() => runStore.currentRun)
const selectedId = computed<string | null>(() => runStore.currentRun?.id ?? null)

const openLink = computed(() => {
  if (!latestRun.value) return '/'
  return { path: `/runs/${latestRun.value.id}`, query: { tab: tabFromDetail(latestRun.value) } }
})

async function onSelect(id: string) {
  try { await runStore.fetchRun(id) } catch { /* ignore */ }
}

function onCreated(id: string) {
  router.push(`/runs/${id}`)
}

function onOpen(id: string, tab: string) {
  router.push({ path: `/runs/${id}`, query: { tab } })
}

onMounted(async () => {
  await runStore.fetchRuns()
  if (runStore.runs.length > 0) {
    await onSelect(runStore.runs[0]!.id)
  }
})

const capacity = computed(() => latestRun.value?.capacity_result ?? null)
const quality  = computed(() => latestRun.value?.quality_result as any ?? null)
const perf     = computed(() => latestRun.value?.performance_result ?? null)
const ovr      = computed(() => latestRun.value?.orders_validation_result ?? null)

const carrierRows = computed(() => {
  const stats = capacity.value?.carrier_stats
  if (!stats) return []
  return Object.values(stats).filter(cs => cs.carrier_id !== 'NONE')
})

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

</script>
