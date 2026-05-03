<template>
  <div class="space-y-6">

    <!-- Empty state -->
    <div v-if="!ovr && !pr" class="text-sm text-gray-400 p-4">
      No performance data yet. Import orders data in the Import tab first.
    </div>

    <!-- Section 2: Settings (after orders loaded) -->
    <div
      v-if="ovr"
      class="card-apple"
    >
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Analysis settings</h3>
      <div class="max-w-64 mb-4">
        <label class="block text-xs text-gray-600 mb-1">Productive hours/shift: <strong>{{ productiveHours }}h</strong></label>
        <input
          v-model.number="productiveHours"
          type="range"
          min="4"
          max="8"
          step="0.5"
          class="w-full accent-[#0071e3]"
        />
      </div>
      <p v-if="analysisError" class="text-red-600 text-sm mb-2">{{ analysisError }}</p>
      <button
        @click="doRunAnalysis"
        :disabled="analyzing"
        class="btn-apple-primary"
      >
        {{ analyzing ? 'Analyzing…' : 'Run performance analysis →' }}
      </button>
    </div>

    <!-- Section 3: Results -->
    <div v-if="pr" class="flex flex-col" style="gap:24px">
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
      <div class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Daily Activity</h4>
          <button @click="openZoom('daily', 'Daily Activity')" class="hover:bg-black/[.06] transition-colors" style="display:flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:4px;color:rgba(0,0,0,0.3)" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="dailyChartEl" style="height:220px"></div>
      </div>

      <!-- Chart 2: Hourly Heatmap (only if has_hourly_data) -->
      <div v-if="pr.has_hourly_data" class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Hourly Heatmap</h4>
          <button @click="openZoom('heatmap', 'Hourly Heatmap')" class="hover:bg-black/[.06] transition-colors" style="display:flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:4px;color:rgba(0,0,0,0.3)" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="heatmapEl" style="height:300px"></div>
      </div>

      <!-- Chart 3: Hourly Throughput (only if has_hourly_data) -->
      <div v-if="pr.has_hourly_data && pr.hourly_metrics?.length" class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Hourly Throughput</h4>
          <button @click="openZoom('hourly', 'Hourly Throughput')" class="hover:bg-black/[.06] transition-colors" style="display:flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:4px;color:rgba(0,0,0,0.3)" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="hourlyThroughputEl" style="height:200px"></div>
      </div>

      <!-- Chart 4: Weekly Trend (only if multiple weeks) -->
      <div v-if="pr.weekly_trends?.length > 1" class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Weekly Trend</h4>
          <button @click="openZoom('weekly', 'Weekly Trend')" class="hover:bg-black/[.06] transition-colors" style="display:flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:4px;color:rgba(0,0,0,0.3)" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="weeklyTrendEl" style="height:220px"></div>
      </div>

      <!-- Chart 5: Day-of-Week Profile -->
      <div v-if="pr.weekday_profile?.length" class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Day-of-Week Profile (Avg Lines/Day)</h4>
          <button @click="openZoom('dow', 'Day-of-Week Profile')" class="hover:bg-black/[.06] transition-colors" style="display:flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:4px;color:rgba(0,0,0,0.3)" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="dowProfileEl" style="height:180px"></div>
      </div>

      <!-- KPI cards: Lines per Order Distribution -->
      <div v-if="pr.lines_per_order_dist?.length">
        <h4 class="mb-2" style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Lines per Order Distribution</h4>
        <div class="grid grid-cols-4 gap-3">
          <KpiCard
            v-for="bin in pr.lines_per_order_dist"
            :key="bin.bin"
            :label="bin.bin === '1' ? '1 line' : bin.bin + ' lines'"
            :value="bin.count.toLocaleString()"
            :tooltip="`Orders with ${bin.bin} line(s): ${bin.count.toLocaleString()} (${((bin.count / pr.kpi.total_orders) * 100).toFixed(1)}% of all orders)`"
          />
        </div>
      </div>

      <!-- Chart 6: Lines per Order Distribution -->
      <div v-if="pr.lines_per_order_dist?.length" class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Lines per Order Distribution — Chart</h4>
          <button @click="openZoom('linesPerOrder', 'Lines per Order Distribution')" class="hover:bg-black/[.06] transition-colors" style="display:flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:4px;color:rgba(0,0,0,0.3)" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="linesPerOrderEl" style="height:200px"></div>
      </div>

      <!-- SKU Pareto Table -->
      <div class="card-apple-list overflow-hidden">
        <div class="px-4 py-3 flex flex-wrap gap-3 items-center justify-between" style="border-bottom:1px solid rgba(0,0,0,0.08)">
          <div class="flex items-center gap-2 flex-wrap">
            <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">SKU Pareto</h4>
            <span v-if="pr.sku_pareto?.length" style="font-size:11px;color:var(--app-text-sec)">
              A: {{ abcPct('A') }}% · B: {{ abcPct('B') }}% · C: {{ abcPct('C') }}%
            </span>
          </div>
          <div class="flex items-center gap-2">
            <select v-model="paretoAbcFilter" class="input-apple-sm" style="width:auto">
              <option value="ALL">All ABC classes</option>
              <option value="A">Class A</option>
              <option value="B">Class B</option>
              <option value="C">Class C</option>
            </select>
            <button @click="exportParetoCsv" class="btn-apple-pill" style="font-size:12px;padding:5px 10px">Export CSV</button>
          </div>
        </div>
        <div class="overflow-x-auto max-h-80">
          <table class="w-full text-xs">
            <thead class="sticky top-0" style="background:rgba(0,0,0,0.03);border-bottom:1px solid rgba(0,0,0,0.08)">
              <tr>
                <th class="px-3 py-2 text-left font-medium" style="color:var(--app-text-sec)">Rank</th>
                <th class="px-3 py-2 text-left font-medium" style="color:var(--app-text-sec)">SKU</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Lines</th>
                <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">ABC</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Cumulative %</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in visiblePareto" :key="row.sku" class="hover:bg-black/[.02]" style="border-top:1px solid rgba(0,0,0,0.06)">
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
        <div class="px-4 py-2 flex items-center justify-between">
          <p class="text-xs text-gray-400">Showing {{ visiblePareto.length }} of {{ filteredPareto.length }} SKUs</p>
          <button
            v-if="visiblePareto.length < filteredPareto.length"
            @click="paretoVisibleCount = filteredPareto.length"
            class="text-xs text-[#0071e3] hover:underline"
          >Load more ({{ filteredPareto.length - visiblePareto.length }} remaining)</button>
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
import { ref, computed, watch, onMounted } from 'vue'
import type { RunDetail, PerformanceResult, OrdersValidationResult } from '@/api/runs'
import { runsApi } from '@/api/runs'
import KpiCard from '@/components/shared/KpiCard.vue'
import ChartZoomModal from '@/components/shared/ChartZoomModal.vue'
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

const zoomChart = ref<{ title: string; traces: any[]; layout: any } | null>(null)
const chartStore: Record<string, { traces: any[]; layout: any }> = {}
function openZoom(key: string, title: string) {
  const d = chartStore[key]
  if (d) zoomChart.value = { title, ...d }
}

const pr = computed(() => props.run.performance_result as PerformanceResult | null)
const ovr = computed(() => props.run.orders_validation_result as OrdersValidationResult | null)

const filteredPareto = computed(() => {
  if (!pr.value) return []
  const rows = pr.value.sku_pareto
  if (paretoAbcFilter.value === 'ALL') return rows
  return rows.filter(r => r.abc_class === paretoAbcFilter.value)
})

const paretoVisibleCount = ref(50)
const visiblePareto = computed(() => filteredPareto.value.slice(0, paretoVisibleCount.value))

watch(paretoAbcFilter, () => { paretoVisibleCount.value = 50 })

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
  const base = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif', size: 11, color: 'rgba(0,0,0,0.48)' },
  }
  const ax = { gridcolor: 'rgba(0,0,0,0.08)', zerolinecolor: 'rgba(0,0,0,0.12)' }

  // Daily Activity bar chart
  if (dailyChartEl.value && data.daily_metrics.length > 0) {
    const dailyTraces = [{ x: data.daily_metrics.map(d => d.date), y: data.daily_metrics.map(d => d.lines), type: 'bar' as const, marker: { color: '#0071e3' }, name: 'Lines' }]
    const dailyLayout = { ...base, margin: { t: 10, b: 40, l: 50, r: 10 }, xaxis: { ...ax, title: 'Date' }, yaxis: { ...ax, title: 'Lines' } }
    Plotly.newPlot(dailyChartEl.value, dailyTraces, dailyLayout, { responsive: true, displayModeBar: false })
    chartStore.daily = { traces: dailyTraces, layout: dailyLayout }
  }

  // Hourly Throughput
  if (hourlyThroughputEl.value && data.has_hourly_data && data.hourly_metrics?.length > 0) {
    const sorted = [...data.hourly_metrics].sort((a, b) => a.hour - b.hour)
    const hourlyTraces = [{ x: sorted.map(h => `${String(h.hour).padStart(2, '0')}:00`), y: sorted.map(h => h.lines), type: 'bar' as const, marker: { color: '#0071e3' }, name: 'Lines' }]
    const hourlyLayout = { ...base, margin: { t: 10, b: 40, l: 50, r: 10 }, xaxis: { ...ax, title: 'Hour of Day' }, yaxis: { ...ax, title: 'Lines' } }
    Plotly.newPlot(hourlyThroughputEl.value, hourlyTraces, hourlyLayout, { responsive: true, displayModeBar: false })
    chartStore.hourly = { traces: hourlyTraces, layout: hourlyLayout }
  }

  // Weekly Trend
  if (weeklyTrendEl.value && data.weekly_trends?.length > 1) {
    const weeklyTraces = [{ x: data.weekly_trends.map(w => `W${String(w.week).padStart(2, '0')} ${w.year}`), y: data.weekly_trends.map(w => w.lines), type: 'bar' as const, marker: { color: '#0071e3' }, name: 'Lines' }]
    const weeklyLayout = { ...base, margin: { t: 10, b: 60, l: 50, r: 10 }, xaxis: { ...ax, title: 'Week', tickangle: -45 }, yaxis: { ...ax, title: 'Lines' } }
    Plotly.newPlot(weeklyTrendEl.value, weeklyTraces, weeklyLayout, { responsive: true, displayModeBar: false })
    chartStore.weekly = { traces: weeklyTraces, layout: weeklyLayout }
  }

  // Day-of-Week Profile
  if (dowProfileEl.value && data.weekday_profile?.length > 0) {
    const dowTraces = [{ x: data.weekday_profile.map(d => d.day), y: data.weekday_profile.map(d => d.avg_lines), type: 'bar' as const, marker: { color: '#0071e3' }, name: 'Avg Lines' }]
    const dowLayout = { ...base, margin: { t: 10, b: 40, l: 50, r: 10 }, xaxis: { ...ax, title: 'Day of Week' }, yaxis: { ...ax, title: 'Avg Lines/Day' } }
    Plotly.newPlot(dowProfileEl.value, dowTraces, dowLayout, { responsive: true, displayModeBar: false })
    chartStore.dow = { traces: dowTraces, layout: dowLayout }
  }

  // Lines per Order Distribution
  if (linesPerOrderEl.value && data.lines_per_order_dist?.length > 0) {
    const lpoTraces = [{ x: data.lines_per_order_dist.map(b => b.bin), y: data.lines_per_order_dist.map(b => b.count), type: 'bar' as const, marker: { color: '#0071e3' }, name: 'Orders' }]
    const lpoLayout = { ...base, margin: { t: 10, b: 40, l: 50, r: 10 }, xaxis: { ...ax, title: 'Lines per Order' }, yaxis: { ...ax, title: 'Number of Orders' } }
    Plotly.newPlot(linesPerOrderEl.value, lpoTraces, lpoLayout, { responsive: true, displayModeBar: false })
    chartStore.linesPerOrder = { traces: lpoTraces, layout: lpoLayout }
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
    const heatmapTraces = [{
      z,
      x: hours.map(h => `${String(h).padStart(2, '0')}:00`),
      y: dates,
      type: 'heatmap' as const,
      colorscale: [[0, '#ffffff'], [0.001, '#dbeafe'], [0.5, '#0071e3'], [1, '#003d82']] as [number, string][],
      zmin: 0,
      showscale: true,
    }]
    const heatmapLayout = { ...base, margin: { t: 10, b: 60, l: 80, r: 10 }, xaxis: { ...ax, title: 'Hour' }, yaxis: { ...ax, title: 'Date', autorange: 'reversed' } }
    Plotly.newPlot(heatmapEl.value, heatmapTraces, heatmapLayout, { responsive: true, displayModeBar: false })
    chartStore.heatmap = { traces: heatmapTraces, layout: heatmapLayout }
  }
}

function abcClass(cls: string) {
  if (cls === 'A') return 'bg-green-100 text-green-800'
  if (cls === 'B') return 'bg-yellow-100 text-yellow-800'
  return 'bg-gray-100 text-gray-600'
}

function abcPct(cls: string) {
  if (!pr.value?.sku_pareto?.length) return '0.0'
  const count = pr.value.sku_pareto.filter(r => r.abc_class === cls).length
  return ((count / pr.value.sku_pareto.length) * 100).toFixed(1)
}

function exportParetoCsv() {
  if (!pr.value?.sku_pareto?.length) return
  const headers = ['rank', 'sku', 'lines', 'abc_class', 'cumulative_pct']
  const rows = pr.value.sku_pareto.map(r => [
    r.frequency_rank,
    r.sku,
    r.total_lines,
    r.abc_class,
    r.cumulative_pct.toFixed(2) + '%',
  ])
  const csv = '﻿' + [headers, ...rows].map(r => r.map(v => `"${v}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'sku_pareto.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>
