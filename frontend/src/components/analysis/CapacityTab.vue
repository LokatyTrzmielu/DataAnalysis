<template>
  <div class="space-y-6">
    <!-- Upload + run capacity -->
    <div class="bg-white border border-gray-200 rounded-lg p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Run capacity analysis</h3>
      <div class="flex flex-col gap-3">
        <!-- Analysis mode (radio) -->
        <div>
          <label class="block text-xs text-gray-600 mb-1">Analysis mode</label>
          <div class="flex gap-3 text-xs">
            <label class="flex items-center gap-1 text-gray-700">
              <input v-model="analysisMode" type="radio" value="independent" /> Independent
            </label>
            <label class="flex items-center gap-1 text-gray-700">
              <input v-model="analysisMode" type="radio" value="prioritized" /> Prioritized
            </label>
            <label class="flex items-center gap-1 text-gray-700">
              <input v-model="analysisMode" type="radio" value="bestfit" /> Best Fit
            </label>
          </div>
        </div>

        <!-- Borderline threshold slider -->
        <div class="max-w-64">
          <label class="block text-xs text-gray-600 mb-1">Borderline threshold: <strong>{{ borderlineThreshold }}mm</strong></label>
          <input
            v-model.number="borderlineThreshold"
            type="range" min="0.5" max="10" step="0.5"
            class="w-full accent-blue-600"
          />
        </div>

        <div>
          <button
            @click="runCapacity"
            :disabled="running || !run.masterdata_path"
            class="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
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
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
        <KpiCard label="Total SKU" :value="cr.total_sku" />
        <KpiCard label="Fit %" :value="`${cr.fit_percentage.toFixed(1)}%`" />
        <KpiCard label="FIT" :value="cr.fit_count" />
        <KpiCard label="NOT FIT" :value="cr.not_fit_count" />
      </div>

      <!-- Plotly Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <!-- Carrier Fit Chart -->
        <div class="bg-white border border-gray-200 rounded-lg p-4">
          <h4 class="text-xs font-semibold text-gray-700 mb-2">Carrier Fit</h4>
          <div ref="carrierChartEl" style="height:200px"></div>
        </div>
        <!-- Volume Distribution -->
        <div class="bg-white border border-gray-200 rounded-lg p-4">
          <h4 class="text-xs font-semibold text-gray-700 mb-2">Volume Distribution (m³)</h4>
          <div ref="dimsChartEl" style="height:200px"></div>
        </div>
        <!-- Margin Distribution -->
        <div class="bg-white border border-gray-200 rounded-lg p-4">
          <h4 class="text-xs font-semibold text-gray-700 mb-2">Margin Distribution (mm, FIT + BORDERLINE)</h4>
          <div ref="weightChartEl" style="height:200px"></div>
        </div>
        <!-- Dimensions Distribution -->
        <div class="bg-white border border-gray-200 rounded-lg p-4">
          <h4 class="text-xs font-semibold text-gray-700 mb-2">Dimensions Distribution (mm)</h4>
          <div ref="dimsDistChartEl" style="height:200px"></div>
        </div>
        <!-- Weight Distribution -->
        <div class="bg-white border border-gray-200 rounded-lg p-4">
          <h4 class="text-xs font-semibold text-gray-700 mb-2">Weight Distribution (kg)</h4>
          <div ref="weightDistChartEl" style="height:200px"></div>
        </div>
      </div>

      <!-- Per-carrier table -->
      <div class="bg-white border border-gray-200 rounded-lg overflow-hidden mb-4">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-600">Carrier</th>
              <th class="px-4 py-2 text-right text-xs font-medium text-gray-600">Fit %</th>
              <th class="px-4 py-2 text-right text-xs font-medium text-gray-600">FIT</th>
              <th class="px-4 py-2 text-right text-xs font-medium text-gray-600">BORDERLINE</th>
              <th class="px-4 py-2 text-right text-xs font-medium text-gray-600">NOT FIT</th>
              <th class="px-4 py-2 text-right text-xs font-medium text-gray-600">Locations</th>
              <th class="px-4 py-2 text-right text-xs font-medium text-gray-600">Avg fill</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="(stats, cid) in cr.carrier_stats" :key="cid" class="hover:bg-gray-50">
              <td class="px-4 py-2 font-medium text-gray-800">{{ stats.carrier_name }}</td>
              <td class="px-4 py-2 text-right text-gray-700">{{ stats.fit_percentage.toFixed(1) }}%</td>
              <td class="px-4 py-2 text-right text-green-700">{{ stats.fit_count }}</td>
              <td class="px-4 py-2 text-right text-yellow-600">{{ stats.borderline_count }}</td>
              <td class="px-4 py-2 text-right text-red-600">{{ stats.not_fit_count }}</td>
              <td class="px-4 py-2 text-right text-gray-700">{{ stats.total_locations_required }}</td>
              <td class="px-4 py-2 text-right text-gray-700">{{ (stats.avg_filling_rate * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ABC Cross-stats (visible only when Performance data is available) -->
      <div v-if="hasPerformanceData" class="bg-white border border-gray-200 rounded-lg overflow-hidden mb-4">
        <div class="px-4 py-3 border-b border-gray-200">
          <h4 class="text-xs font-semibold text-gray-700">Capacity × ABC Class (unique SKU)</h4>
          <p class="text-xs text-gray-400 mt-0.5">Click a row to filter the table below</p>
        </div>
        <table class="w-full text-xs">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-2 text-left font-medium text-gray-600">ABC Class</th>
              <th class="px-4 py-2 text-right font-medium text-gray-600">SKU count</th>
              <th class="px-4 py-2 text-right font-medium text-gray-600">FIT</th>
              <th class="px-4 py-2 text-right font-medium text-gray-600">BORDERLINE</th>
              <th class="px-4 py-2 text-right font-medium text-gray-600">NOT FIT</th>
              <th class="px-4 py-2 text-right font-medium text-gray-600">Fit %</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="[cls, s] in abcCrossStats"
              :key="cls"
              class="hover:bg-blue-50 cursor-pointer transition-colors"
              :class="{ 'bg-blue-50': abcFilter === cls }"
              @click="abcFilter = (abcFilter === cls ? 'ALL' : cls as typeof abcFilter)"
            >
              <td class="px-4 py-2">
                <span :class="['px-1.5 py-0.5 rounded text-xs font-medium', abcClassBadge(cls)]">{{ cls }}</span>
              </td>
              <td class="px-4 py-2 text-right text-gray-700">{{ s.total }}</td>
              <td class="px-4 py-2 text-right text-green-700">{{ s.fit }}</td>
              <td class="px-4 py-2 text-right text-yellow-600">{{ s.borderline }}</td>
              <td class="px-4 py-2 text-right text-red-600">{{ s.not_fit }}</td>
              <td class="px-4 py-2 text-right text-gray-700">{{ s.total ? ((s.fit / s.total) * 100).toFixed(1) + '%' : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- SKU-level table with filters -->
      <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-200 flex flex-wrap gap-3 items-center justify-between">
          <h4 class="text-xs font-semibold text-gray-700">Individual SKU results</h4>
          <div class="flex gap-2 flex-wrap items-center">
            <!-- Status filter -->
            <select v-model="statusFilter" class="text-xs border border-gray-300 rounded px-2 py-1">
              <option value="ALL">All statuses</option>
              <option value="FIT">FIT only</option>
              <option value="BORDERLINE">BORDERLINE only</option>
              <option value="NOT_FIT">NOT FIT only</option>
            </select>
            <!-- Carrier filter -->
            <select v-model="carrierFilter" class="text-xs border border-gray-300 rounded px-2 py-1">
              <option value="ALL">All carriers</option>
              <option v-for="(stats, cid) in cr.carrier_stats" :key="cid" :value="cid">{{ stats.carrier_name }}</option>
            </select>
            <!-- ABC Class filter (only when Performance data is available) -->
            <select v-if="hasPerformanceData" v-model="abcFilter" class="text-xs border border-gray-300 rounded px-2 py-1">
              <option value="ALL">All ABC classes</option>
              <option value="A">Class A (top 80%)</option>
              <option value="B">Class B (80–95%)</option>
              <option value="C">Class C (95–100%)</option>
              <option value="NOT_IN_PARETO">Not in Performance</option>
            </select>
            <!-- CSV export -->
            <button @click="exportCsv" class="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded transition-colors">
              Export CSV
            </button>
          </div>
        </div>
        <div class="overflow-x-auto max-h-80">
          <table class="w-full text-xs">
            <thead class="bg-gray-50 border-b border-gray-200 sticky top-0">
              <tr>
                <th class="px-3 py-2 text-left font-medium text-gray-600">SKU</th>
                <th class="px-3 py-2 text-left font-medium text-gray-600">Carrier</th>
                <th class="px-3 py-2 text-center font-medium text-gray-600">Status</th>
                <th v-if="hasPerformanceData" class="px-3 py-2 text-center font-medium text-gray-600">ABC</th>
                <th class="px-3 py-2 text-right font-medium text-gray-600">Units</th>
                <th class="px-3 py-2 text-left font-medium text-gray-600">Limiting factor</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="row in filteredRows" :key="`${row.sku}-${row.carrier_id}`" class="hover:bg-gray-50">
                <td class="px-3 py-1.5 font-medium text-gray-800">{{ row.sku }}</td>
                <td class="px-3 py-1.5 text-gray-600">{{ carrierName(row.carrier_id) }}</td>
                <td class="px-3 py-1.5 text-center">
                  <span :class="['px-1.5 py-0.5 rounded text-xs font-medium', statusClass(row.fit_status)]">
                    {{ row.fit_status }}
                  </span>
                </td>
                <td v-if="hasPerformanceData" class="px-3 py-1.5 text-center">
                  <span v-if="skuAbcMap.get(row.sku)" :class="['px-1.5 py-0.5 rounded text-xs font-medium', abcClassBadge(skuAbcMap.get(row.sku)!)]">
                    {{ skuAbcMap.get(row.sku) }}
                  </span>
                  <span v-else class="text-gray-300">—</span>
                </td>
                <td class="px-3 py-1.5 text-right text-gray-700">{{ row.units_per_carrier }}</td>
                <td class="px-3 py-1.5 text-gray-500">{{ row.limiting_factor }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="text-xs text-gray-400 px-4 py-2">Showing {{ filteredRows.length }} of {{ cr.rows.length }} rows</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import type { RunDetail, CapacityResult } from '@/api/runs'
import { runsApi } from '@/api/runs'
import KpiCard from '@/components/shared/KpiCard.vue'
import Plotly from 'plotly.js-dist-min'
import { useNotificationsStore } from '@/stores/notifications'

const notify = useNotificationsStore()

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{ (e: 'refreshed'): void }>()

const running = ref(false)
const error = ref('')
const analysisMode = ref<'independent' | 'prioritized' | 'bestfit'>('independent')
const borderlineThreshold = ref(2.0)
const statusFilter = ref<'ALL' | 'FIT' | 'BORDERLINE' | 'NOT_FIT'>('ALL')
const carrierFilter = ref('ALL')
const abcFilter = ref<'ALL' | 'A' | 'B' | 'C' | 'NOT_IN_PARETO'>('ALL')

const carrierChartEl = ref<HTMLElement>()
const dimsChartEl = ref<HTMLElement>()
const weightChartEl = ref<HTMLElement>()
const dimsDistChartEl = ref<HTMLElement>()
const weightDistChartEl = ref<HTMLElement>()

const cr = computed(() => props.run.capacity_result as CapacityResult | null)

// ABC class map from Performance pareto data
const skuAbcMap = computed(() => {
  const pareto = props.run.performance_result?.sku_pareto
  if (!pareto) return new Map<string, string>()
  return new Map(pareto.map(s => [s.sku, s.abc_class]))
})

const hasPerformanceData = computed(() => skuAbcMap.value.size > 0)

// Cross-stats: unique SKU count per ABC class with fit breakdown
const abcCrossStats = computed((): [string, { fit: number; borderline: number; not_fit: number; total: number }][] => {
  if (!cr.value || !hasPerformanceData.value) return []
  // Deduplicate by unique SKU per class (Independent mode produces multiple rows per SKU)
  const skuBestStatus = new Map<string, string>()
  for (const row of cr.value.rows) {
    const existing = skuBestStatus.get(row.sku)
    // Priority: FIT > BORDERLINE > NOT_FIT
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
  // Sort: A, B, C, NOT_IN_PARETO
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

function carrierName(cid: string): string {
  return cr.value?.carrier_stats[cid]?.carrier_name ?? cid
}

function statusClass(status: string) {
  if (status === 'FIT') return 'bg-green-100 text-green-800'
  if (status === 'BORDERLINE') return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

function abcClassBadge(cls: string | undefined): string {
  if (cls === 'A') return 'bg-green-100 text-green-800'
  if (cls === 'B') return 'bg-yellow-100 text-yellow-800'
  if (cls === 'C') return 'bg-gray-100 text-gray-600'
  return 'bg-gray-100 text-gray-400'
}

// Reset ABC filter when performance data disappears
watch(() => props.run.performance_result, (val) => {
  if (!val) abcFilter.value = 'ALL'
})

watch(cr, (val) => {
  if (val) nextTick(() => renderCharts(val))
})

onMounted(() => {
  if (cr.value) nextTick(() => renderCharts(cr.value!))
})

function renderCharts(data: CapacityResult) {
  // Carrier Fit stacked bar
  if (carrierChartEl.value) {
    const carriers = Object.values(data.carrier_stats)
    const fitTrace = { x: carriers.map(c => c.carrier_name), y: carriers.map(c => c.fit_count), name: 'FIT', type: 'bar' as const, marker: { color: '#22c55e' } }
    const borderTrace = { x: carriers.map(c => c.carrier_name), y: carriers.map(c => c.borderline_count), name: 'BORDERLINE', type: 'bar' as const, marker: { color: '#eab308' } }
    const notFitTrace = { x: carriers.map(c => c.carrier_name), y: carriers.map(c => c.not_fit_count), name: 'NOT FIT', type: 'bar' as const, marker: { color: '#ef4444' } }
    Plotly.newPlot(carrierChartEl.value, [fitTrace, borderTrace, notFitTrace], {
      barmode: 'stack',
      margin: { t: 10, b: 55, l: 80, r: 10 },
      legend: { x: 1, xanchor: 'right', y: 1, yanchor: 'top' },
      xaxis: { title: { text: 'Carrier' } },
      yaxis: { title: { text: 'SKU count', standoff: 12 } },
    }, { responsive: true, displayModeBar: false })
  }

  // Volume distribution histogram
  if (dimsChartEl.value && data.rows.length > 0) {
    const volumes = data.rows.map(r => r.volume_m3).filter(v => v != null && v > 0)
    Plotly.newPlot(dimsChartEl.value, [{
      x: volumes, type: 'histogram' as const, marker: { color: '#3b82f6' }, name: 'Volume'
    }], {
      margin: { t: 10, b: 55, l: 80, r: 10 },
      xaxis: { title: { text: 'm³' } },
      yaxis: { title: { text: 'SKU count', standoff: 12 } },
    }, { responsive: true, displayModeBar: false })
  }

  // Margin distribution (FIT + BORDERLINE only)
  if (weightChartEl.value && data.rows.length > 0) {
    const margins = data.rows
      .filter(r => r.fit_status !== 'NOT_FIT' && r.margin_mm != null)
      .map(r => r.margin_mm as number)
    Plotly.newPlot(weightChartEl.value, [{
      x: margins, type: 'histogram' as const, marker: { color: '#8b5cf6' }, name: 'Margin'
    }], {
      margin: { t: 10, b: 55, l: 80, r: 10 },
      xaxis: { title: { text: 'mm' } },
      yaxis: { title: { text: 'SKU count', standoff: 12 } },
    }, { responsive: true, displayModeBar: false })
  }

  // Dimensions distribution (length / width / height overlay)
  if (dimsDistChartEl.value && data.rows.length > 0) {
    Plotly.newPlot(dimsDistChartEl.value, [
      { x: data.rows.map(r => r.length_mm), type: 'histogram' as const, name: 'Length', opacity: 0.6, marker: { color: '#3b82f6' } },
      { x: data.rows.map(r => r.width_mm),  type: 'histogram' as const, name: 'Width',  opacity: 0.6, marker: { color: '#f59e0b' } },
      { x: data.rows.map(r => r.height_mm), type: 'histogram' as const, name: 'Height', opacity: 0.6, marker: { color: '#10b981' } },
    ], {
      barmode: 'overlay',
      margin: { t: 10, b: 55, l: 80, r: 10 },
      legend: { x: 1, xanchor: 'right', y: 1, yanchor: 'top' },
      xaxis: { title: { text: 'mm' } },
      yaxis: { title: { text: 'SKU count', standoff: 12 } },
    }, { responsive: true, displayModeBar: false })
  }

  // Weight distribution
  if (weightDistChartEl.value && data.rows.length > 0) {
    Plotly.newPlot(weightDistChartEl.value, [{
      x: data.rows.map(r => r.weight_kg), type: 'histogram' as const, marker: { color: '#ec4899' }, name: 'Weight'
    }], {
      margin: { t: 10, b: 55, l: 80, r: 10 },
      xaxis: { title: { text: 'kg' } },
      yaxis: { title: { text: 'SKU count', standoff: 12 } },
    }, { responsive: true, displayModeBar: false })
  }
}

async function runCapacity() {
  running.value = true
  error.value = ''
  try {
    await runsApi.runCapacity(props.run.id, null, {
      prioritization_mode: analysisMode.value === 'prioritized',
      best_fit_mode: analysisMode.value === 'bestfit',
      borderline_threshold: borderlineThreshold.value,
    })
    emit('refreshed')
    notify.push({ type: 'success', title: 'Analysis complete' })
  } catch (e: unknown) {
    error.value = (e as Error).message || 'Analysis failed.'
  } finally {
    running.value = false
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
  const csv = '\uFEFF' + [headers, ...rows].map(r => r.map(v => `"${v}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'capacity_results.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>
