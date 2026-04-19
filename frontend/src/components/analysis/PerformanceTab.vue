<template>
  <div class="space-y-6">

    <!-- Section 2: Settings (after orders loaded) -->
    <div
      v-if="ovr"
      class="bg-white border border-gray-200 rounded-lg p-5"
    >
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Analysis settings</h3>
      <div class="max-w-64 mb-4">
        <label class="block text-xs text-gray-600 mb-1">Productive hours/shift: <strong>{{ productiveHours }}h</strong></label>
        <input
          v-model.number="productiveHours"
          type="range"
          min="4"
          max="8"
          step="0.5"
          class="w-full accent-blue-600"
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
        <KpiCard label="Total Orders" :value="pr.kpi.total_orders.toLocaleString()" tooltip="Total number of distinct orders in the uploaded file." />
        <KpiCard label="Total Lines" :value="pr.kpi.total_lines.toLocaleString()" tooltip="Total number of order lines (one SKU per line)." />
        <KpiCard label="Avg Lines/Order" :value="pr.kpi.avg_lines_per_order.toFixed(1)" tooltip="Average number of SKU lines per order." />
        <KpiCard label="Avg Lines/Hour" :value="pr.kpi.avg_lines_per_hour.toFixed(1)" tooltip="Average lines processed per productive hour, based on the configured hours/shift." />
        <KpiCard label="Peak Lines/Hour" :value="pr.kpi.peak_lines_per_hour.toLocaleString()" tooltip="Maximum lines processed in a single hour across all data." />
        <KpiCard label="P90 Lines/Hour" :value="pr.kpi.p90_lines_per_hour.toFixed(0)" tooltip="90th percentile of hourly throughput — useful for peak capacity planning." />
        <KpiCard label="Total Pieces" :value="pr.kpi.total_units.toLocaleString()" tooltip="Total quantity of individual items across all order lines." />
        <KpiCard label="Unique SKU" :value="pr.kpi.unique_sku.toLocaleString()" tooltip="Number of distinct SKUs that appeared in orders." />
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

      <!-- Chart 3: Hourly Throughput (only if has_hourly_data) -->
      <div v-if="pr.has_hourly_data && pr.hourly_metrics?.length" class="bg-white border border-gray-200 rounded-lg p-4">
        <h4 class="text-xs font-semibold text-gray-700 mb-2">Hourly Throughput</h4>
        <div ref="hourlyThroughputEl" style="height:200px"></div>
      </div>

      <!-- Chart 4: Weekly Trend (only if multiple weeks) -->
      <div v-if="pr.weekly_trends?.length > 1" class="bg-white border border-gray-200 rounded-lg p-4">
        <h4 class="text-xs font-semibold text-gray-700 mb-2">Weekly Trend</h4>
        <div ref="weeklyTrendEl" style="height:220px"></div>
      </div>

      <!-- Chart 5: Day-of-Week Profile -->
      <div v-if="pr.weekday_profile?.length" class="bg-white border border-gray-200 rounded-lg p-4">
        <h4 class="text-xs font-semibold text-gray-700 mb-2">Day-of-Week Profile (Avg Lines/Day)</h4>
        <div ref="dowProfileEl" style="height:180px"></div>
      </div>

      <!-- Chart 6: Lines per Order Distribution -->
      <div v-if="pr.lines_per_order_dist?.length" class="bg-white border border-gray-200 rounded-lg p-4">
        <h4 class="text-xs font-semibold text-gray-700 mb-2">Lines per Order Distribution</h4>
        <div ref="linesPerOrderEl" style="height:200px"></div>
      </div>

      <!-- SKU Pareto Table -->
      <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-200 flex flex-wrap gap-3 items-center justify-between">
          <h4 class="text-xs font-semibold text-gray-700">SKU Pareto</h4>
          <select v-model="paretoAbcFilter" class="text-xs border border-gray-300 rounded px-2 py-1">
            <option value="ALL">All ABC classes</option>
            <option value="A">Class A</option>
            <option value="B">Class B</option>
            <option value="C">Class C</option>
          </select>
        </div>
        <div class="overflow-x-auto max-h-80">
          <table class="w-full text-xs">
            <thead class="bg-gray-50 border-b border-gray-200 sticky top-0">
              <tr>
                <th class="px-3 py-2 text-left font-medium text-gray-600">Rank</th>
                <th class="px-3 py-2 text-left font-medium text-gray-600">SKU</th>
                <th class="px-3 py-2 text-right font-medium text-gray-600">Lines</th>
                <th class="px-3 py-2 text-center font-medium text-gray-600">ABC</th>
                <th class="px-3 py-2 text-right font-medium text-gray-600">Cumulative %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="row in filteredPareto" :key="row.sku" class="hover:bg-gray-50">
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
        <p class="text-xs text-gray-400 px-4 py-2">Showing {{ filteredPareto.length }} of {{ pr.sku_pareto.length }} SKUs</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { RunDetail, PerformanceResult, OrdersValidationResult } from '@/api/runs'
import { runsApi } from '@/api/runs'
import KpiCard from '@/components/shared/KpiCard.vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{
  (e: 'refreshed'): void
  (e: 'navigate', tab: string): void
}>()

const analyzing = ref(false)
const analysisError = ref('')
const productiveHours = ref(7.0)
const paretoAbcFilter = ref('ALL')

// Chart refs
const dailyChartEl = ref<HTMLElement>()
const heatmapEl = ref<HTMLElement>()
const hourlyThroughputEl = ref<HTMLElement>()
const weeklyTrendEl = ref<HTMLElement>()
const dowProfileEl = ref<HTMLElement>()
const linesPerOrderEl = ref<HTMLElement>()

const pr = computed(() => props.run.performance_result as PerformanceResult | null)
const ovr = computed(() => props.run.orders_validation_result as OrdersValidationResult | null)

const filteredPareto = computed(() => {
  if (!pr.value) return []
  const rows = pr.value.sku_pareto
  if (paretoAbcFilter.value === 'ALL') return rows
  return rows.filter(r => r.abc_class === paretoAbcFilter.value)
})

onMounted(() => {
  if (pr.value) renderCharts(pr.value)
})

watch(pr, (val) => {
  if (val) renderCharts(val)
})

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

  // Hourly Throughput
  if (hourlyThroughputEl.value && data.has_hourly_data && data.hourly_metrics?.length > 0) {
    const sorted = [...data.hourly_metrics].sort((a, b) => a.hour - b.hour)
    Plotly.newPlot(hourlyThroughputEl.value, [{
      x: sorted.map(h => `${String(h.hour).padStart(2, '0')}:00`),
      y: sorted.map(h => h.lines),
      type: 'bar' as const,
      marker: { color: '#6366f1' },
      name: 'Lines',
    }], {
      margin: { t: 10, b: 40, l: 50, r: 10 },
      xaxis: { title: 'Hour of Day' },
      yaxis: { title: 'Lines' },
    }, { responsive: true, displayModeBar: false })
  }

  // Weekly Trend
  if (weeklyTrendEl.value && data.weekly_trends?.length > 1) {
    Plotly.newPlot(weeklyTrendEl.value, [{
      x: data.weekly_trends.map(w => `W${String(w.week).padStart(2, '0')} ${w.year}`),
      y: data.weekly_trends.map(w => w.lines),
      type: 'bar' as const,
      marker: { color: '#10b981' },
      name: 'Lines',
    }], {
      margin: { t: 10, b: 60, l: 50, r: 10 },
      xaxis: { title: 'Week', tickangle: -45 },
      yaxis: { title: 'Lines' },
    }, { responsive: true, displayModeBar: false })
  }

  // Day-of-Week Profile
  if (dowProfileEl.value && data.weekday_profile?.length > 0) {
    Plotly.newPlot(dowProfileEl.value, [{
      x: data.weekday_profile.map(d => d.day),
      y: data.weekday_profile.map(d => d.avg_lines),
      type: 'bar' as const,
      marker: { color: '#f59e0b' },
      name: 'Avg Lines',
    }], {
      margin: { t: 10, b: 40, l: 50, r: 10 },
      xaxis: { title: 'Day of Week' },
      yaxis: { title: 'Avg Lines/Day' },
    }, { responsive: true, displayModeBar: false })
  }

  // Lines per Order Distribution
  if (linesPerOrderEl.value && data.lines_per_order_dist?.length > 0) {
    Plotly.newPlot(linesPerOrderEl.value, [{
      x: data.lines_per_order_dist.map(b => b.bin),
      y: data.lines_per_order_dist.map(b => b.count),
      type: 'bar' as const,
      marker: { color: '#ec4899' },
      name: 'Orders',
    }], {
      margin: { t: 10, b: 40, l: 50, r: 10 },
      xaxis: { title: 'Lines per Order' },
      yaxis: { title: 'Number of Orders' },
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
      colorscale: [[0, '#ffffff'], [0.001, '#dbeafe'], [0.5, '#3b82f6'], [1, '#1d4ed8']] as [number, string][],
      zmin: 0,
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
