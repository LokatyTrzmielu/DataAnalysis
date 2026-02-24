<template>
  <div class="space-y-6">
    <!-- Upload + run capacity -->
    <div class="bg-white border border-gray-200 rounded-lg p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Run capacity analysis</h3>
      <div class="flex gap-4 flex-wrap items-end">
        <div>
          <label class="block text-xs text-gray-600 mb-1">Masterdata file</label>
          <input
            ref="fileInput"
            type="file"
            accept=".xlsx,.xls,.csv"
            class="block text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-600 hover:file:bg-blue-100"
            @change="onFileChange"
          />
        </div>

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
        <div class="min-w-40">
          <label class="block text-xs text-gray-600 mb-1">Borderline threshold: <strong>{{ borderlineThreshold }}mm</strong></label>
          <input
            v-model.number="borderlineThreshold"
            type="range" min="0.5" max="10" step="0.5"
            class="w-full accent-blue-600"
          />
        </div>

        <button
          @click="runCapacity"
          :disabled="running || (!selectedFile && !run.masterdata_path)"
          class="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition-colors self-end"
        >
          {{ running ? 'Analyzing…' : 'Run analysis' }}
        </button>
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

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{ (e: 'refreshed'): void }>()

const fileInput = ref<HTMLInputElement>()
const selectedFile = ref<File | null>(null)
const running = ref(false)
const error = ref('')
const analysisMode = ref<'independent' | 'prioritized' | 'bestfit'>('independent')
const borderlineThreshold = ref(2.0)
const statusFilter = ref<'ALL' | 'FIT' | 'BORDERLINE' | 'NOT_FIT'>('ALL')
const carrierFilter = ref('ALL')

const carrierChartEl = ref<HTMLElement>()
const dimsChartEl = ref<HTMLElement>()
const weightChartEl = ref<HTMLElement>()

const cr = computed(() => props.run.capacity_result as CapacityResult | null)

const filteredRows = computed(() => {
  if (!cr.value) return []
  return cr.value.rows.filter(row => {
    if (statusFilter.value !== 'ALL' && row.fit_status !== statusFilter.value) return false
    if (carrierFilter.value !== 'ALL' && row.carrier_id !== carrierFilter.value) return false
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
      margin: { t: 10, b: 60, l: 50, r: 10 },
      legend: { orientation: 'h', y: -0.3 },
    }, { responsive: true, displayModeBar: false })
  }

  // Volume distribution histogram
  if (dimsChartEl.value && data.rows.length > 0) {
    const volumes = data.rows.map(r => r.volume_m3).filter(v => v != null && v > 0)
    Plotly.newPlot(dimsChartEl.value, [{
      x: volumes, type: 'histogram' as const, marker: { color: '#3b82f6' }, name: 'Volume'
    }], {
      margin: { t: 10, b: 40, l: 50, r: 10 },
      xaxis: { title: 'm³' },
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
      margin: { t: 10, b: 40, l: 50, r: 10 },
      xaxis: { title: 'mm' },
    }, { responsive: true, displayModeBar: false })
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  error.value = ''
}

async function runCapacity() {
  running.value = true
  error.value = ''
  try {
    await runsApi.runCapacity(props.run.id, selectedFile.value, {
      prioritization_mode: analysisMode.value === 'prioritized',
      best_fit_mode: analysisMode.value === 'bestfit',
      borderline_threshold: borderlineThreshold.value,
    })
    emit('refreshed')
  } catch (e: unknown) {
    error.value = (e as Error).message || 'Analysis failed.'
  } finally {
    running.value = false
  }
}

function exportCsv() {
  if (!filteredRows.value.length) return
  const headers = ['sku', 'carrier_id', 'carrier_name', 'fit_status', 'units_per_carrier', 'limiting_factor', 'margin_mm', 'locations_required', 'filling_rate']
  const rows = filteredRows.value.map(row => [
    row.sku,
    row.carrier_id,
    carrierName(row.carrier_id),
    row.fit_status,
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
