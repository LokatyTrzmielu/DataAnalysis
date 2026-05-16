<template>
  <div class="space-y-6">
    <!-- Upload + run capacity -->
    <div class="card-apple">
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Run capacity analysis</h3>
      <div class="flex flex-col gap-3">
        <!-- Analysis mode (radio) -->
        <div>
          <label class="block text-xs mb-1" style="color:var(--app-text-sec)">Analysis mode</label>
          <div class="flex gap-3 text-xs">
            <label class="flex items-center gap-1" style="color:var(--app-text-sec)">
              <input v-model="analysisMode" type="radio" value="independent" /> Independent
            </label>
            <label class="flex items-center gap-1" style="color:var(--app-text-sec)">
              <input v-model="analysisMode" type="radio" value="prioritized" /> Prioritized
            </label>
            <label class="flex items-center gap-1" style="color:var(--app-text-sec)">
              <input v-model="analysisMode" type="radio" value="bestfit" /> Best Fit
            </label>
          </div>
        </div>

        <!-- Borderline threshold slider -->
        <div class="max-w-64">
          <label class="block text-xs mb-1" style="color:var(--app-text-sec)">Borderline threshold: <strong>{{ borderlineThreshold }}mm</strong></label>
          <input
            v-model.number="borderlineThreshold"
            type="range" min="0.5" max="10" step="0.5"
            class="w-full accent-[#0071e3]"
          />
        </div>

        <!-- Carrier selection -->
        <div v-if="availableCarriers.length">
          <label class="block text-xs mb-1" style="color:var(--app-text-sec)">Carriers</label>
          <CarrierMultiSelect
            :carriers="availableCarriers"
            v-model:modelValue="selectedCarrierIds"
            :showError="ranOnce && selectedCarrierIds.size === 0"
          />
          <!-- Priority drag & drop — only in Prioritized mode -->
          <div v-if="analysisMode === 'prioritized' && prioritizedOrder.length" class="mt-2">
            <label class="block text-xs mb-1" style="color:var(--app-text-sec)">Priority order — drag to reorder</label>
            <ul class="flex flex-col gap-1">
              <li
                v-for="(cid, idx) in prioritizedOrder"
                :key="cid"
                draggable="true"
                @dragstart="onDragStart(idx)"
                @dragover="onDragOver"
                @drop="onDrop(idx)"
                @dragend="dragIndex = null"
                :class="['priority-row', dragIndex === idx ? 'is-dragging' : '']"
              >
                <span class="priority-num">{{ idx + 1 }}</span>
                <span class="drag-handle">⠿</span>
                <span class="priority-name">{{ carrierLabel(cid) }}</span>
                <span class="priority-dims">{{ carrierDims(cid) }}</span>
              </li>
            </ul>
          </div>
          <p v-else-if="analysisMode === 'prioritized'" class="text-xs mt-1.5" style="color:var(--app-placeholder)">
            Select carriers above to set priority order
          </p>
        </div>

        <div>
          <button
            @click="runCapacity"
            :disabled="running || !canRun"
            class="btn-apple-primary"
          >
            {{ running ? 'Analyzing…' : 'Run analysis' }}
          </button>
        </div>
      </div>
      <p v-if="error" class="text-red-600 text-sm mt-3">{{ error }}</p>
    </div>

    <!-- Results -->
    <div v-if="cr">
      <!-- Summary KPIs -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6" style="gap:16px;margin-bottom:24px">
        <KpiCard label="Total SKU" :value="cr.total_sku" />
        <KpiCard label="Fit %" :value="`${cr.fit_percentage.toFixed(1)}%`" />
        <KpiCard label="FIT" :value="cr.fit_count" />
        <KpiCard label="NOT FIT" :value="cr.not_fit_count" />
        <KpiCard label="Avg Dimensions" :value="avgStats?.dims" />
        <KpiCard label="Avg Weight" :value="avgStats?.weight" />
      </div>

      <!-- Plotly Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2" style="gap:16px;margin-bottom:24px">
        <!-- Carrier Fit Chart -->
        <div class="card-apple">
          <div class="flex items-center justify-between mb-2">
            <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Carrier Fit</h4>
            <button @click="openZoom('carrier', 'Carrier Fit')" class="chart-zoom-btn" title="Expand chart">
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
          <div ref="carrierChartEl" style="height:280px"></div>
        </div>
        <!-- Volume Distribution -->
        <div class="card-apple">
          <div class="flex items-center justify-between mb-2">
            <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Volume Distribution (m³)</h4>
            <button @click="openZoom('volume', 'Volume Distribution (m³)')" class="chart-zoom-btn" title="Expand chart">
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
          <div ref="dimsChartEl" style="height:280px"></div>
        </div>
        <!-- Margin Distribution -->
        <div class="card-apple">
          <div class="flex items-center justify-between mb-2">
            <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Margin Distribution (mm, FIT + BORDERLINE)</h4>
            <button @click="openZoom('margin', 'Margin Distribution (mm)')" class="chart-zoom-btn" title="Expand chart">
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
          <div ref="weightChartEl" style="height:280px"></div>
        </div>
        <!-- Dimensions Distribution -->
        <div class="card-apple">
          <div class="flex items-center justify-between mb-2">
            <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Dimensions Distribution (mm)</h4>
            <button @click="openZoom('dims', 'Dimensions Distribution (mm)')" class="chart-zoom-btn" title="Expand chart">
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
          <div ref="dimsDistChartEl" style="height:280px"></div>
        </div>
        <!-- Weight Distribution -->
        <div class="card-apple">
          <div class="flex items-center justify-between mb-2">
            <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Weight Distribution (kg)</h4>
            <button @click="openZoom('weight', 'Weight Distribution (kg)')" class="chart-zoom-btn" title="Expand chart">
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
          <div ref="weightDistChartEl" style="height:280px"></div>
        </div>
      </div>

      <!-- Per-carrier table -->
      <div class="card-apple-list" style="margin-bottom:24px">
        <table class="w-full text-sm">
          <thead class="cap-thead">
            <tr>
              <th class="px-4 py-2 text-left text-xs font-medium" style="color:var(--app-text-sec)">Carrier</th>
              <th class="px-4 py-2 text-right text-xs font-medium" style="color:var(--app-text-sec)">Fit %</th>
              <th class="px-4 py-2 text-right text-xs font-medium" style="color:var(--app-text-sec)">FIT</th>
              <th class="px-4 py-2 text-right text-xs font-medium" style="color:var(--app-text-sec)">BORDERLINE</th>
              <th class="px-4 py-2 text-right text-xs font-medium" style="color:var(--app-text-sec)">NOT FIT</th>
              <th class="px-4 py-2 text-right text-xs font-medium" style="color:var(--app-text-sec)">Locations</th>
              <th class="px-4 py-2 text-right text-xs font-medium" style="color:var(--app-text-sec)">Volume (m³)</th>
              <th class="px-4 py-2 text-right text-xs font-medium" style="color:var(--app-text-sec)">Stock vol. (m³)</th>
              <th class="px-4 py-2 text-right text-xs font-medium" style="color:var(--app-text-sec)">Filling rate</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(stats, cid) in cr.carrier_stats" :key="cid" class="cap-row">
              <td class="px-4 py-2 font-medium" style="color:var(--app-text)">{{ stats.carrier_name }}</td>
              <td class="px-4 py-2 text-right" style="color:var(--app-text-sec)">{{ stats.fit_percentage.toFixed(1) }}%</td>
              <td class="px-4 py-2 text-right badge-fit-text">{{ stats.fit_count }}</td>
              <td class="px-4 py-2 text-right badge-bl-text">{{ stats.borderline_count }}</td>
              <td class="px-4 py-2 text-right badge-nf-text">{{ stats.not_fit_count }}</td>
              <td class="px-4 py-2 text-right" style="color:var(--app-text-sec)">{{ stats.total_locations_required }}</td>
              <td class="px-4 py-2 text-right" style="color:var(--app-text-sec)">{{ stats.total_volume_m3.toFixed(3) }}</td>
              <td class="px-4 py-2 text-right" style="color:var(--app-text-sec)">{{ stats.stock_volume_m3.toFixed(3) }}</td>
              <td class="px-4 py-2 text-right" style="color:var(--app-text-sec)">{{ (stats.avg_filling_rate * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ABC Cross-stats (visible only when Performance data is available) -->
      <div v-if="hasPerformanceData" class="card-apple-list overflow-hidden" style="margin-bottom:24px">
        <div class="px-4 py-3 cap-section-header">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Capacity × ABC Class (unique SKU)</h4>
          <p class="mt-0.5" style="font-size:12px;color:var(--app-placeholder)">Click a row to filter the table below</p>
        </div>
        <table class="w-full text-xs">
          <thead class="cap-thead">
            <tr>
              <th class="px-4 py-2 text-left font-medium" style="color:var(--app-text-sec)">ABC Class</th>
              <th class="px-4 py-2 text-right font-medium" style="color:var(--app-text-sec)">SKU count</th>
              <th class="px-4 py-2 text-right font-medium" style="color:var(--app-text-sec)">FIT</th>
              <th class="px-4 py-2 text-right font-medium" style="color:var(--app-text-sec)">BORDERLINE</th>
              <th class="px-4 py-2 text-right font-medium" style="color:var(--app-text-sec)">NOT FIT</th>
              <th class="px-4 py-2 text-right font-medium" style="color:var(--app-text-sec)">Fit %</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="[cls, s] in abcCrossStats"
              :key="cls"
              class="cap-row cursor-pointer transition-colors"
              :class="abcFilter === cls ? 'cap-row-selected' : ''"
              @click="abcFilter = (abcFilter === cls ? 'ALL' : cls as typeof abcFilter)"
            >
              <td class="px-4 py-2">
                <span :class="['px-1.5 py-0.5 rounded text-xs font-medium', abcClassBadge(cls)]">{{ cls }}</span>
              </td>
              <td class="px-4 py-2 text-right" style="color:var(--app-text-sec)">{{ s.total }}</td>
              <td class="px-4 py-2 text-right badge-fit-text">{{ s.fit }}</td>
              <td class="px-4 py-2 text-right badge-bl-text">{{ s.borderline }}</td>
              <td class="px-4 py-2 text-right badge-nf-text">{{ s.not_fit }}</td>
              <td class="px-4 py-2 text-right" style="color:var(--app-text-sec)">{{ s.total ? ((s.fit / s.total) * 100).toFixed(1) + '%' : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- SKU-level table with filters -->
      <div class="card-apple-list">
        <div class="px-4 py-3 flex flex-wrap gap-3 items-center justify-between cap-section-header">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Individual SKU results</h4>
          <div class="flex gap-2 flex-wrap items-center">
            <select v-model="statusFilter" class="input-apple-sm" style="width:auto">
              <option value="ALL">All statuses</option>
              <option value="FIT">FIT only</option>
              <option value="BORDERLINE">BORDERLINE only</option>
              <option value="NOT_FIT">NOT FIT only</option>
            </select>
            <select v-model="carrierFilter" class="input-apple-sm" style="width:auto">
              <option value="ALL">All carriers</option>
              <option v-for="(stats, cid) in cr.carrier_stats" :key="cid" :value="cid">{{ stats.carrier_name }}</option>
            </select>
            <select v-if="hasPerformanceData" v-model="abcFilter" class="input-apple-sm" style="width:auto">
              <option value="ALL">All ABC classes</option>
              <option value="A">Class A (top 80%)</option>
              <option value="B">Class B (80–95%)</option>
              <option value="C">Class C (95–100%)</option>
              <option value="NOT_IN_PARETO">Not in Performance</option>
            </select>
            <button @click="exportCsv" class="btn-apple-pill" style="font-size:12px;padding:5px 10px">
              Export CSV
            </button>
          </div>
        </div>
        <div class="overflow-x-auto max-h-80">
          <table class="w-full text-xs">
            <thead class="cap-thead sticky top-0">
              <tr>
                <th class="px-3 py-2 text-left font-medium" style="color:var(--app-text-sec)">SKU</th>
                <th class="px-3 py-2 text-left font-medium" style="color:var(--app-text-sec)">Carrier</th>
                <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">Status</th>
                <th v-if="hasPerformanceData" class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">ABC</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Locations</th>
                <th class="px-3 py-2 text-left font-medium" style="color:var(--app-text-sec)">Limiting factor</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in visibleSkuRows" :key="`${row.sku}-${row.carrier_id}`" class="cap-row">
                <td class="px-3 py-1.5 font-medium" style="color:var(--app-text)">{{ row.sku }}</td>
                <td class="px-3 py-1.5" style="color:var(--app-text-sec)">{{ carrierName(row.carrier_id) }}</td>
                <td class="px-3 py-1.5 text-center">
                  <span :class="['px-1.5 py-0.5 rounded text-xs font-medium', statusClass(row.fit_status)]">
                    {{ row.fit_status }}
                  </span>
                </td>
                <td v-if="hasPerformanceData" class="px-3 py-1.5 text-center">
                  <span v-if="skuAbcMap.get(row.sku)" :class="['px-1.5 py-0.5 rounded text-xs font-medium', abcClassBadge(skuAbcMap.get(row.sku)!)]">
                    {{ skuAbcMap.get(row.sku) }}
                  </span>
                  <span v-else style="color:var(--app-placeholder)">—</span>
                </td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.units_per_carrier }}</td>
                <td class="px-3 py-1.5" style="color:var(--app-placeholder)">{{ row.limiting_factor }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="px-4 py-2 flex items-center justify-between">
          <p class="text-xs" style="color:var(--app-placeholder)">Showing {{ visibleSkuRows.length }} of {{ filteredRows.length }} rows</p>
          <button
            v-if="visibleSkuRows.length < filteredRows.length"
            @click="skuVisibleCount = filteredRows.length"
            class="text-xs text-[#0071e3] hover:underline"
          >Load more ({{ filteredRows.length - visibleSkuRows.length }} remaining)</button>
        </div>
      </div>
    </div>
  </div>

  <ChartZoomModal
    v-if="zoomChart"
    :title="zoomChart.title"
    :traces="zoomChart.traces"
    :layout="zoomChart.layout"
    @close="zoomChart = null"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import type { RunDetail, CapacityResult } from '@/api/runs'
import { runsApi } from '@/api/runs'
import { carriersApi, type Carrier } from '@/api/carriers'
import KpiCard from '@/components/shared/KpiCard.vue'
import ChartZoomModal from '@/components/shared/ChartZoomModal.vue'
import CarrierMultiSelect from '@/components/shared/CarrierMultiSelect.vue'
import Plotly from 'plotly.js-dist-min'
import { useNotificationsStore } from '@/stores/notifications'
import { useThemeStore } from '@/stores/theme'
import { useAnalysisStore } from '@/stores/analysis'

const notify = useNotificationsStore()
const theme = useThemeStore()
const analysis = useAnalysisStore()

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{ (e: 'refreshed'): void }>()

const running = ref(false)
const ranOnce = ref(false)
const error = ref('')
const analysisMode = ref<'independent' | 'prioritized' | 'bestfit'>('independent')
const borderlineThreshold = ref(2.0)
const availableCarriers = ref<Carrier[]>([])
const selectedCarrierIds = ref(new Set<string>())
const prioritizedOrder = ref<string[]>([])
const dragIndex = ref<number | null>(null)
const statusFilter = ref<'ALL' | 'FIT' | 'BORDERLINE' | 'NOT_FIT'>('ALL')
const carrierFilter = ref('ALL')
const abcFilter = ref<'ALL' | 'A' | 'B' | 'C' | 'NOT_IN_PARETO'>('ALL')

const carrierChartEl = ref<HTMLElement>()
const dimsChartEl = ref<HTMLElement>()
const weightChartEl = ref<HTMLElement>()
const dimsDistChartEl = ref<HTMLElement>()
const weightDistChartEl = ref<HTMLElement>()

const zoomChart = ref<{ title: string; traces: any[]; layout: any } | null>(null)
const chartStore: Record<string, { traces: any[]; layout: any }> = {}
function openZoom(key: string, title: string) {
  const d = chartStore[key]
  if (d) zoomChart.value = { title, ...d }
}

const cr = computed(() => props.run.capacity_result as CapacityResult | null)

const avgStats = computed(() => {
  const rows = cr.value?.rows
  if (!rows?.length) return null
  const seen = new Set<string>()
  let sumL = 0, sumW = 0, sumH = 0, sumWt = 0, count = 0
  for (const row of rows) {
    if (seen.has(row.sku)) continue
    seen.add(row.sku)
    sumL += row.length_mm
    sumW += row.width_mm
    sumH += row.height_mm
    sumWt += row.weight_kg
    count++
  }
  if (!count) return null
  return {
    dims: `${(sumL / count).toFixed(1)} × ${(sumW / count).toFixed(1)} × ${(sumH / count).toFixed(1)} mm`,
    weight: `${(sumWt / count).toFixed(2)} kg`,
  }
})

const skuAbcMap = computed(() => {
  const pareto = props.run.performance_result?.sku_pareto
  if (!pareto) return new Map<string, string>()
  return new Map(pareto.map(s => [s.sku, s.abc_class]))
})

const hasPerformanceData = computed(() => skuAbcMap.value.size > 0)

const abcCrossStats = computed((): [string, { fit: number; borderline: number; not_fit: number; total: number }][] => {
  if (!cr.value || !hasPerformanceData.value) return []
  const skuBestStatus = new Map<string, string>()
  for (const row of cr.value.rows) {
    const existing = skuBestStatus.get(row.sku)
    if (!existing || fitPriority(row.fit_status) > fitPriority(existing)) {
      skuBestStatus.set(row.sku, row.fit_status)
    }
  }
  const stats: Record<string, { fit: number; borderline: number; not_fit: number; total: number }> = {}
  for (const [sku, status] of skuBestStatus) {
    const cls = skuAbcMap.value.get(sku) ?? 'NOT_IN_PARETO'
    if (!stats[cls]) stats[cls] = { fit: 0, borderline: 0, not_fit: 0, total: 0 }
    stats[cls].total++
    if (status === 'FIT') stats[cls].fit++
    else if (status === 'BORDERLINE') stats[cls].borderline++
    else stats[cls].not_fit++
  }
  const order = ['A', 'B', 'C', 'NOT_IN_PARETO']
  return Object.entries(stats).sort(([a], [b]) => {
    const ia = order.indexOf(a), ib = order.indexOf(b)
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
  })
})

function fitPriority(status: string): number {
  if (status === 'FIT') return 2
  if (status === 'BORDERLINE') return 1
  return 0
}

const filteredRows = computed(() => {
  if (!cr.value) return []
  return cr.value.rows.filter(row => {
    if (statusFilter.value !== 'ALL' && row.fit_status !== statusFilter.value) return false
    if (carrierFilter.value !== 'ALL' && row.carrier_id !== carrierFilter.value) return false
    if (abcFilter.value !== 'ALL') {
      const cls = skuAbcMap.value.get(row.sku)
      if (abcFilter.value === 'NOT_IN_PARETO') {
        if (cls !== undefined) return false
      } else {
        if (cls !== abcFilter.value) return false
      }
    }
    return true
  })
})

const skuVisibleCount = ref(50)
const visibleSkuRows = computed(() => filteredRows.value.slice(0, skuVisibleCount.value))

watch([statusFilter, carrierFilter, abcFilter], () => { skuVisibleCount.value = 50 })

function carrierName(cid: string): string {
  return cr.value?.carrier_stats[cid]?.carrier_name ?? cid
}

function statusClass(status: string) {
  if (status === 'FIT') return 'badge-fit'
  if (status === 'BORDERLINE') return 'badge-bl'
  return 'badge-nf'
}

function abcClassBadge(cls: string | undefined): string {
  if (cls === 'A') return 'badge-fit'
  if (cls === 'B') return 'badge-bl'
  return 'badge-abc-c'
}

watch(() => props.run.performance_result, (val) => {
  if (!val) abcFilter.value = 'ALL'
})

watch(cr, (val) => {
  if (val) nextTick(() => renderCharts(val))
})

watch(() => theme.dark, () => {
  if (cr.value) nextTick(() => renderCharts(cr.value!))
})

watch(selectedCarrierIds, (newSet) => {
  for (const id of newSet) {
    if (!prioritizedOrder.value.includes(id)) prioritizedOrder.value.push(id)
  }
  prioritizedOrder.value = prioritizedOrder.value.filter(id => newSet.has(id))
}, { deep: true })

watch(analysisMode, (mode) => {
  if (mode === 'prioritized' && prioritizedOrder.value.length === 0) {
    prioritizedOrder.value = [...selectedCarrierIds.value]
      .filter(id => availableCarriers.value.some(c => c.carrier_id === id))
  }
})

function onDragStart(index: number) { dragIndex.value = index }
function onDragOver(e: DragEvent) { e.preventDefault() }
function onDrop(targetIndex: number) {
  if (dragIndex.value === null || dragIndex.value === targetIndex) return
  const arr = [...prioritizedOrder.value]
  const removed = arr.splice(dragIndex.value, 1)
  if (!removed[0]) return
  arr.splice(targetIndex, 0, removed[0])
  prioritizedOrder.value = arr
  dragIndex.value = null
}

function carrierLabel(id: string) {
  const c = availableCarriers.value.find(x => x.carrier_id === id)
  return c?.name || id
}
function carrierDims(id: string) {
  const c = availableCarriers.value.find(x => x.carrier_id === id)
  if (!c) return ''
  return `${c.inner_length_mm}×${c.inner_width_mm}×${c.inner_height_mm} mm · max ${c.max_weight_kg} kg`
}

onMounted(async () => {
  const { data } = await carriersApi.list()
  availableCarriers.value = data.filter(c => c.is_active)
  if (cr.value) {
    selectedCarrierIds.value = new Set(cr.value.carriers_analyzed.filter(id => id !== 'NONE'))
    nextTick(() => renderCharts(cr.value!))
  } else {
    selectedCarrierIds.value = new Set(availableCarriers.value.map(c => c.carrier_id))
  }
})

const canRun = computed(() => !!props.run.masterdata_path && selectedCarrierIds.value.size > 0)

function renderCharts(data: CapacityResult) {
  const isDark = theme.dark
  const fontColor = isDark ? 'rgba(255,255,255,0.60)' : 'rgba(0,0,0,0.48)'
  const gridColor = isDark ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.08)'
  const zeroColor = isDark ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.12)'

  const base = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif', size: 11, color: fontColor },
  }
  const ax = { gridcolor: gridColor, zerolinecolor: zeroColor }

  if (carrierChartEl.value) {
    const carriers = Object.values(data.carrier_stats)
    const fitTrace = { x: carriers.map(c => c.carrier_name), y: carriers.map(c => c.fit_count), name: 'FIT', type: 'bar' as const, marker: { color: '#34c759' } }
    const borderTrace = { x: carriers.map(c => c.carrier_name), y: carriers.map(c => c.borderline_count), name: 'BORDERLINE', type: 'bar' as const, marker: { color: '#ff9500' } }
    const notFitTrace = { x: carriers.map(c => c.carrier_name), y: carriers.map(c => c.not_fit_count), name: 'NOT FIT', type: 'bar' as const, marker: { color: '#ff3b30' } }
    const carrierLayout = { ...base, barmode: 'stack', margin: { t: 10, b: 55, l: 80, r: 10 }, legend: { x: 1, xanchor: 'right', y: 1, yanchor: 'top' }, xaxis: { ...ax, title: { text: 'Carrier' } }, yaxis: { ...ax, title: { text: 'SKU count', standoff: 12 } } }
    Plotly.newPlot(carrierChartEl.value, [fitTrace, borderTrace, notFitTrace], carrierLayout, { responsive: true, displayModeBar: false })
    chartStore.carrier = { traces: [fitTrace, borderTrace, notFitTrace], layout: carrierLayout }
  }

  if (dimsChartEl.value && data.rows.length > 0) {
    const volumes = data.rows.map(r => r.volume_m3).filter(v => v != null && v > 0)
    const volumeTraces = [{ x: volumes, type: 'histogram' as const, marker: { color: '#0071e3' }, name: 'Volume' }]
    const volumeLayout = { ...base, margin: { t: 10, b: 55, l: 80, r: 10 }, xaxis: { ...ax, title: { text: 'm³' } }, yaxis: { ...ax, title: { text: 'SKU count', standoff: 12 } } }
    Plotly.newPlot(dimsChartEl.value, volumeTraces, volumeLayout, { responsive: true, displayModeBar: false })
    chartStore.volume = { traces: volumeTraces, layout: volumeLayout }
  }

  if (weightChartEl.value && data.rows.length > 0) {
    const margins = data.rows
      .filter(r => r.fit_status !== 'NOT_FIT' && r.margin_mm != null)
      .map(r => r.margin_mm as number)
    const marginTraces = [{ x: margins, type: 'histogram' as const, marker: { color: '#8b5cf6' }, name: 'Margin' }]
    const marginLayout = { ...base, margin: { t: 10, b: 55, l: 80, r: 10 }, xaxis: { ...ax, title: { text: 'mm' } }, yaxis: { ...ax, title: { text: 'SKU count', standoff: 12 } } }
    Plotly.newPlot(weightChartEl.value, marginTraces, marginLayout, { responsive: true, displayModeBar: false })
    chartStore.margin = { traces: marginTraces, layout: marginLayout }
  }

  if (dimsDistChartEl.value && data.rows.length > 0) {
    const dimsTraces = [
      { x: data.rows.map(r => r.length_mm), type: 'histogram' as const, name: 'Length', opacity: 0.6, marker: { color: '#0071e3' } },
      { x: data.rows.map(r => r.width_mm),  type: 'histogram' as const, name: 'Width',  opacity: 0.6, marker: { color: '#f59e0b' } },
      { x: data.rows.map(r => r.height_mm), type: 'histogram' as const, name: 'Height', opacity: 0.6, marker: { color: '#10b981' } },
    ]
    const dimsLayout = { ...base, barmode: 'overlay', margin: { t: 10, b: 55, l: 80, r: 10 }, legend: { x: 1, xanchor: 'right', y: 1, yanchor: 'top' }, xaxis: { ...ax, title: { text: 'mm' } }, yaxis: { ...ax, title: { text: 'SKU count', standoff: 12 } } }
    Plotly.newPlot(dimsDistChartEl.value, dimsTraces, dimsLayout, { responsive: true, displayModeBar: false })
    chartStore.dims = { traces: dimsTraces, layout: dimsLayout }
  }

  if (weightDistChartEl.value && data.rows.length > 0) {
    const weightTraces = [{ x: data.rows.map(r => r.weight_kg), type: 'histogram' as const, marker: { color: '#0071e3' }, name: 'Weight' }]
    const weightLayout = { ...base, margin: { t: 10, b: 55, l: 80, r: 10 }, xaxis: { ...ax, title: { text: 'kg' } }, yaxis: { ...ax, title: { text: 'SKU count', standoff: 12 } } }
    Plotly.newPlot(weightDistChartEl.value, weightTraces, weightLayout, { responsive: true, displayModeBar: false })
    chartStore.weight = { traces: weightTraces, layout: weightLayout }
  }
}

async function runCapacity() {
  ranOnce.value = true
  running.value = true
  analysis.start()
  error.value = ''
  try {
    await runsApi.runCapacity(props.run.id, null, {
      prioritization_mode: analysisMode.value === 'prioritized',
      best_fit_mode: analysisMode.value === 'bestfit',
      borderline_threshold: borderlineThreshold.value,
      carrier_ids: analysisMode.value === 'prioritized'
        ? [...prioritizedOrder.value]
        : [...selectedCarrierIds.value],
    })
    emit('refreshed')
    notify.push({ type: 'success', title: 'Analysis complete' })
  } catch (e: unknown) {
    error.value = (e as Error).message || 'Analysis failed.'
  } finally {
    running.value = false
    analysis.stop()
  }
}

function exportCsv() {
  if (!filteredRows.value.length) return
  const headers = ['sku', 'carrier_id', 'carrier_name', 'fit_status', ...(hasPerformanceData.value ? ['abc_class'] : []), 'units_per_carrier', 'limiting_factor', 'margin_mm', 'locations_required', 'filling_rate']
  const rows = filteredRows.value.map(row => [
    row.sku,
    row.carrier_id,
    carrierName(row.carrier_id),
    row.fit_status,
    ...(hasPerformanceData.value ? [skuAbcMap.value.get(row.sku) ?? ''] : []),
    row.units_per_carrier,
    row.limiting_factor,
    row.margin_mm ?? '',
    row.locations_required,
    (row.filling_rate * 100).toFixed(1) + '%',
  ])
  const csv = '﻿' + [headers, ...rows].map(r => r.map(v => typeof v === 'string' && /^\d{10,}$/.test(v) ? `"=""${v}"""` : `"${v}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'capacity_results.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.cap-thead {
  background: var(--table-header-bg);
  border-bottom: 1px solid var(--table-divider);
}

.cap-section-header {
  border-bottom: 1px solid var(--table-divider);
}

.cap-row {
  border-top: 1px solid var(--table-divider);
}
.cap-row:hover { background: var(--table-row-hover); }

.cap-row-selected { background: rgba(0, 113, 227, 0.06); }

/* Fit status badge classes (used by statusClass() and abcClassBadge()) */
.badge-fit    { background: var(--badge-fit-bg);  color: var(--badge-fit-color); }
.badge-bl     { background: var(--badge-bl-bg);   color: var(--badge-bl-color); }
.badge-nf     { background: var(--badge-nf-bg);   color: var(--badge-nf-color); }
.badge-abc-c  { background: var(--table-header-bg); color: var(--app-text-sec); }

/* Colored text for FIT/BORDERLINE/NOT FIT counts in table cells */
.badge-fit-text { color: var(--badge-fit-color); }
.badge-bl-text  { color: var(--badge-bl-color); }
.badge-nf-text  { color: var(--badge-nf-color); }

/* Priority drag & drop list */
.priority-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: grab;
  background: var(--app-input-bg);
  border: 1px solid var(--table-divider);
  font-size: 12px;
  color: var(--app-text);
  user-select: none;
  transition: background 0.1s, opacity 0.1s;
}
.priority-row:hover { background: var(--table-row-hover); }
.priority-row.is-dragging { opacity: 0.4; cursor: grabbing; }
.priority-num { width: 14px; font-weight: 600; color: var(--app-text-sec); flex-shrink: 0; text-align: right; }
.drag-handle { color: var(--app-placeholder); font-size: 14px; flex-shrink: 0; }
.priority-name { font-weight: 500; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.priority-dims { color: var(--app-placeholder); font-size: 10px; flex-shrink: 0; }

/* Expand chart button */
.chart-zoom-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--app-text-sec);
  transition: background 0.15s;
}
.chart-zoom-btn:hover { background: var(--table-row-hover); }
</style>
