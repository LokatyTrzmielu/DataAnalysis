<template>
  <div class="space-y-6">

    <!-- Section 1: Orders Upload Wizard -->
    <div class="bg-white border border-gray-200 rounded-lg p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Step 1 — Upload orders file</h3>

      <!-- Step: upload -->
      <div v-if="ordersStep === 'upload'">
        <p class="text-xs text-gray-500 mb-3">Upload an Excel or CSV file with order lines (order_id, sku, quantity, date).</p>
        <input
          ref="fileInput"
          type="file"
          accept=".xlsx,.xls,.csv"
          class="block text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-600 hover:file:bg-blue-100"
          @change="onFileChange"
        />
        <p v-if="uploadError" class="text-red-600 text-sm mt-2">{{ uploadError }}</p>
        <button
          v-if="selectedFile"
          @click="doInspect"
          :disabled="inspecting"
          class="mt-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
        >
          {{ inspecting ? 'Reading file…' : 'Inspect columns →' }}
        </button>
        <p v-if="run.orders_path && !selectedFile" class="text-xs text-gray-400 mt-3">
          Previously uploaded orders file on server.
        </p>
      </div>

      <!-- Step: mapping -->
      <div v-else-if="ordersStep === 'mapping' && inspectResult">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs font-medium text-gray-600">Map columns</p>
          <button @click="ordersStep = 'upload'" class="text-xs text-gray-400 hover:text-gray-600">← Back</button>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
          <div v-for="field in requiredFields" :key="field.name" class="flex items-center gap-2">
            <label class="text-xs text-gray-600 w-24 shrink-0">
              {{ field.name }}
              <span v-if="!ordersMapping[field.name]" class="text-red-500 ml-1">*</span>
            </label>
            <select
              v-model="ordersMapping[field.name]"
              :class="['flex-1 text-xs border rounded px-2 py-1', !ordersMapping[field.name] ? 'border-red-300 bg-red-50' : 'border-gray-300']"
            >
              <option value="">— not mapped —</option>
              <option v-for="col in inspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
            </select>
          </div>
        </div>
        <details class="mb-3">
          <summary class="text-xs font-medium text-gray-500 cursor-pointer">Optional fields</summary>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
            <div v-for="field in optionalFields" :key="field.name" class="flex items-center gap-2">
              <label class="text-xs text-gray-600 w-24 shrink-0">{{ field.name }}</label>
              <select v-model="ordersMapping[field.name]" class="flex-1 text-xs border border-gray-300 rounded px-2 py-1">
                <option value="">— not mapped —</option>
                <option v-for="col in inspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
          </div>
        </details>
        <!-- Preview -->
        <div class="overflow-x-auto mb-3">
          <table class="text-xs border border-gray-200 rounded w-full">
            <thead class="bg-gray-50">
              <tr>
                <th v-for="col in inspectResult.file_columns" :key="col" class="px-2 py-1 text-left text-gray-600 whitespace-nowrap">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in inspectResult.preview_rows" :key="i" class="border-b border-gray-100">
                <td v-for="col in inspectResult.file_columns" :key="col" class="px-2 py-1 text-gray-700 whitespace-nowrap">{{ row[col] ?? '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="missingRequired.length > 0" class="text-xs text-red-600 mb-2">Missing required: {{ missingRequired.join(', ') }}</p>
        <p v-if="uploadError" class="text-red-600 text-sm mb-2">{{ uploadError }}</p>
        <button
          @click="doIngest"
          :disabled="ingesting || missingRequired.length > 0"
          class="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
        >
          {{ ingesting ? 'Ingesting…' : 'Confirm mapping →' }}
        </button>
      </div>

      <!-- Step: ingested -->
      <div v-else-if="ordersStep === 'ingested'">
        <p class="text-green-600 text-sm mb-3">Orders file ingested.</p>
        <div v-if="run.analysis_config" class="grid grid-cols-3 gap-3 text-xs text-gray-600 mb-3">
          <div><span class="font-medium block">{{ run.analysis_config['orders_rows'] }}</span> rows</div>
          <div><span class="font-medium block">{{ run.analysis_config['orders_date_from'] }} — {{ run.analysis_config['orders_date_to'] }}</span> date range</div>
          <div><span class="font-medium block">{{ run.analysis_config['orders_has_hourly_data'] ? 'Yes' : 'No' }}</span> hourly data</div>
        </div>
        <button @click="ordersStep = 'upload'" class="text-xs text-gray-400 hover:text-gray-600 underline">Re-upload</button>
      </div>
    </div>

    <!-- Section 2: Settings (after ingested) -->
    <div
      v-if="ordersStep === 'ingested' || run.status === 'orders_ingested' || run.status === 'performance_done'"
      class="bg-white border border-gray-200 rounded-lg p-5"
    >
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Step 2 — Analysis settings</h3>
      <div class="flex items-center gap-4 mb-4">
        <label class="text-xs text-gray-600 w-36">Productive hours/shift: <strong>{{ productiveHours }}</strong>h</label>
        <input
          v-model.number="productiveHours"
          type="range"
          min="4"
          max="8"
          step="0.5"
          class="flex-1 accent-blue-600"
        />
      </div>
      <p v-if="analysisError" class="text-red-600 text-sm mb-2">{{ analysisError }}</p>
      <button
        @click="doRunAnalysis"
        :disabled="analyzing"
        class="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
      >
        {{ analyzing ? 'Analyzing…' : 'Run performance analysis →' }}
      </button>
    </div>

    <!-- Section 3: Results -->
    <div v-if="pr" class="space-y-4">
      <!-- KPI grid -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiCard label="Total Orders" :value="pr.kpi.total_orders.toLocaleString()" />
        <KpiCard label="Total Lines" :value="pr.kpi.total_lines.toLocaleString()" />
        <KpiCard label="Avg Lines/Order" :value="pr.kpi.avg_lines_per_order.toFixed(1)" />
        <KpiCard label="Avg Lines/Hour" :value="pr.kpi.avg_lines_per_hour.toFixed(1)" />
        <KpiCard label="Peak Lines/Hour" :value="pr.kpi.peak_lines_per_hour.toLocaleString()" />
        <KpiCard label="P90 Lines/Hour" :value="pr.kpi.p90_lines_per_hour.toFixed(0)" />
        <KpiCard label="Total Units" :value="pr.kpi.total_units.toLocaleString()" />
        <KpiCard label="Unique SKU" :value="pr.kpi.unique_sku.toLocaleString()" />
      </div>

      <!-- Chart 1: Daily Activity -->
      <div class="bg-white border border-gray-200 rounded-lg p-4">
        <h4 class="text-xs font-semibold text-gray-700 mb-2">Daily Activity</h4>
        <div ref="dailyChartEl" style="height:220px"></div>
      </div>

      <!-- Chart 2: Hourly Heatmap (only if has_hourly_data) -->
      <div v-if="pr.has_hourly_data" class="bg-white border border-gray-200 rounded-lg p-4">
        <h4 class="text-xs font-semibold text-gray-700 mb-2">Hourly Heatmap</h4>
        <div ref="heatmapEl" style="height:300px"></div>
      </div>

      <!-- SKU Pareto Table (top 50) -->
      <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-200">
          <h4 class="text-xs font-semibold text-gray-700">SKU Pareto (top 50)</h4>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-xs">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="px-3 py-2 text-left font-medium text-gray-600">Rank</th>
                <th class="px-3 py-2 text-left font-medium text-gray-600">SKU</th>
                <th class="px-3 py-2 text-right font-medium text-gray-600">Lines</th>
                <th class="px-3 py-2 text-center font-medium text-gray-600">ABC</th>
                <th class="px-3 py-2 text-right font-medium text-gray-600">Cumulative %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="row in pr.sku_pareto.slice(0, 50)" :key="row.sku" class="hover:bg-gray-50">
                <td class="px-3 py-1.5 text-gray-500">{{ row.frequency_rank }}</td>
                <td class="px-3 py-1.5 font-medium text-gray-800">{{ row.sku }}</td>
                <td class="px-3 py-1.5 text-right text-gray-700">{{ row.total_lines.toLocaleString() }}</td>
                <td class="px-3 py-1.5 text-center">
                  <span :class="['px-1.5 py-0.5 rounded text-xs font-medium', abcClass(row.abc_class)]">{{ row.abc_class }}</span>
                </td>
                <td class="px-3 py-1.5 text-right text-gray-700">{{ row.cumulative_pct.toFixed(1) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { RunDetail, MappingInspectResponse, PerformanceResult } from '@/api/runs'
import { runsApi } from '@/api/runs'
import KpiCard from '@/components/shared/KpiCard.vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{ (e: 'refreshed'): void }>()

// Orders wizard state
const fileInput = ref<HTMLInputElement>()
const selectedFile = ref<File | null>(null)
const inspecting = ref(false)
const ingesting = ref(false)
const analyzing = ref(false)
const uploadError = ref('')
const analysisError = ref('')
const ordersStep = ref<'upload' | 'mapping' | 'ingested'>('upload')
const inspectResult = ref<MappingInspectResponse | null>(null)
const ordersMapping = ref<Record<string, string>>({})
const productiveHours = ref(7.0)

// Chart refs
const dailyChartEl = ref<HTMLElement>()
const heatmapEl = ref<HTMLElement>()

const pr = computed(() => props.run.performance_result as PerformanceResult | null)

const requiredFields = computed(() =>
  (inspectResult.value?.schema_fields ?? []).filter(f => f.required)
)
const optionalFields = computed(() =>
  (inspectResult.value?.schema_fields ?? []).filter(f => !f.required)
)
const missingRequired = computed(() =>
  requiredFields.value.filter(f => !ordersMapping.value[f.name]).map(f => f.name)
)

onMounted(() => {
  // If orders already ingested on load, show ingested step
  if (props.run.status === 'orders_ingested' || props.run.status === 'performance_done') {
    ordersStep.value = 'ingested'
  }
  if (pr.value) renderCharts(pr.value)
})

watch(pr, (val) => {
  if (val) renderCharts(val)
})

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  uploadError.value = ''
}

async function doInspect() {
  if (!selectedFile.value) return
  inspecting.value = true
  uploadError.value = ''
  try {
    const { data } = await runsApi.inspectOrders(props.run.id, selectedFile.value)
    inspectResult.value = data
    const mapping: Record<string, string> = {}
    for (const field of data.schema_fields) {
      const sug = data.suggestions.find(s => s.suggested_target === field.name)
      mapping[field.name] = sug?.source_column ?? ''
    }
    ordersMapping.value = mapping
    ordersStep.value = 'mapping'
    emit('refreshed')
  } catch (e: unknown) {
    uploadError.value = (e as Error).message || 'Failed to read file.'
  } finally {
    inspecting.value = false
  }
}

async function doIngest() {
  ingesting.value = true
  uploadError.value = ''
  try {
    await runsApi.ingestOrders(props.run.id, ordersMapping.value)
    ordersStep.value = 'ingested'
    emit('refreshed')
  } catch (e: unknown) {
    uploadError.value = (e as Error).message || 'Ingestion failed.'
  } finally {
    ingesting.value = false
  }
}

async function doRunAnalysis() {
  analyzing.value = true
  analysisError.value = ''
  try {
    await runsApi.runPerformance(props.run.id, productiveHours.value)
    emit('refreshed')
  } catch (e: unknown) {
    analysisError.value = (e as Error).message || 'Analysis failed.'
  } finally {
    analyzing.value = false
  }
}

function renderCharts(data: PerformanceResult) {
  // Daily Activity bar chart
  if (dailyChartEl.value && data.daily_metrics.length > 0) {
    const trace = {
      x: data.daily_metrics.map(d => d.date),
      y: data.daily_metrics.map(d => d.lines),
      type: 'bar' as const,
      marker: { color: '#3b82f6' },
      name: 'Lines',
    }
    Plotly.newPlot(dailyChartEl.value, [trace], {
      margin: { t: 10, b: 40, l: 50, r: 10 },
      xaxis: { title: 'Date' },
      yaxis: { title: 'Lines' },
    }, { responsive: true, displayModeBar: false })
  }

  // Hourly Heatmap
  if (heatmapEl.value && data.has_hourly_data && data.datehour_metrics.length > 0) {
    const dates = [...new Set(data.datehour_metrics.map(d => d.date))].sort()
    const hours = Array.from({ length: 24 }, (_, i) => i)
    const z = dates.map(date =>
      hours.map(hour => {
        const found = data.datehour_metrics.find(d => d.date === date && d.hour === hour)
        return found ? found.lines : 0
      })
    )
    const trace = {
      z,
      x: hours.map(h => `${String(h).padStart(2, '0')}:00`),
      y: dates,
      type: 'heatmap' as const,
      colorscale: 'Blues',
      showscale: true,
    }
    Plotly.newPlot(heatmapEl.value, [trace], {
      margin: { t: 10, b: 60, l: 80, r: 10 },
      xaxis: { title: 'Hour' },
      yaxis: { title: 'Date', autorange: 'reversed' },
    }, { responsive: true, displayModeBar: false })
  }
}

function abcClass(cls: string) {
  if (cls === 'A') return 'bg-green-100 text-green-800'
  if (cls === 'B') return 'bg-yellow-100 text-yellow-800'
  return 'bg-gray-100 text-gray-600'
}
</script>
