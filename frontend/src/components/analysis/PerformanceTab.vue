<template>
  <div class="space-y-6">

    <!-- Empty state -->
    <div v-if="!ovr && !pr" class="text-sm p-4" style="color:var(--app-placeholder)">
      No performance data yet. Import orders data in the Import tab first.
    </div>

    <!-- Section 2: Settings (after orders loaded) -->
    <div v-if="ovr" class="card-apple">
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Analysis settings</h3>
      <div class="max-w-64 mb-4">
        <label class="block text-xs mb-1" style="color:var(--app-text-sec)">Productive hours/shift: <strong>{{ productiveHours }}h</strong></label>
        <input
          v-model.number="productiveHours"
          type="range" min="4" max="8" step="0.5"
          class="w-full accent-[#0071e3]"
        />
      </div>
      <!-- Shifts per day — auto-detected, with manual override -->
      <div class="mb-4">
        <label class="block text-xs mb-1" style="color:var(--app-text-sec)">
          Shifts per day
          <span v-if="pr?.detected_shifts_per_day" style="font-weight:400;color:var(--app-placeholder)">
            · auto-detected from data: <strong style="color:var(--app-text-sec)">{{ pr.detected_shifts_per_day }}</strong>
          </span>
        </label>
        <div class="flex gap-4 text-xs" style="color:var(--app-text-sec)">
          <label class="flex items-center gap-1">
            <input v-model="shiftsPerDayOverride" type="radio" :value="null" class="accent-[#0071e3]" /> Auto
          </label>
          <label v-for="n in [1, 2, 3]" :key="n" class="flex items-center gap-1">
            <input v-model="shiftsPerDayOverride" type="radio" :value="n" class="accent-[#0071e3]" /> {{ n }} shift{{ n > 1 ? 's' : '' }}
          </label>
        </div>
      </div>
      <!-- Data scope — visible only when capacity_result has carriers -->
      <div v-if="availableCarriers.length" class="mb-4">
        <label class="block text-xs mb-1" style="color:var(--app-text-sec)">Data scope</label>
        <div class="flex gap-3 text-xs mb-2">
          <label class="flex items-center gap-1" style="color:var(--app-text-sec)">
            <input v-model="analysisScope" type="radio" value="all" /> Entire file
          </label>
          <label class="flex items-center gap-1" style="color:var(--app-text-sec)">
            <input v-model="analysisScope" type="radio" value="carriers" /> By carrier
          </label>
        </div>
        <div v-if="analysisScope === 'carriers'" class="flex flex-col gap-1 ml-1">
          <label
            v-for="c in availableCarriers"
            :key="c.id"
            class="flex items-center gap-2 text-xs"
            style="color:var(--app-text-sec)"
          >
            <input
              type="checkbox"
              :checked="analysisCarrierIds.has(c.id)"
              @change="(e) => toggleAnalysisCarrier(c.id, (e.target as HTMLInputElement).checked)"
              class="accent-[#0071e3]"
            />
            {{ c.name }}
          </label>
          <p v-if="analysisCarrierIds.size === 0" class="text-xs mt-1" style="color:#ff3b30">
            Select at least one carrier
          </p>
        </div>
      </div>

      <p v-if="analysisError" class="text-red-600 text-sm mb-2">{{ analysisError }}</p>
      <button @click="doRunAnalysis" :disabled="analyzing || !canRunAnalysis" class="btn-apple-primary">
        {{ analyzing ? 'Analyzing…' : 'Run performance analysis →' }}
      </button>
    </div>

    <!-- Section 3: Results -->
    <div v-if="pr" class="flex flex-col" style="gap:24px">
      <!-- KPI grid -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiCard label="Total Orders"    :value="pr.kpi.total_orders.toLocaleString()"       tooltip="Total number of distinct orders in the uploaded file." />
        <KpiCard label="Total Lines"     :value="pr.kpi.total_lines.toLocaleString()"        tooltip="Total number of order lines (one SKU per line)." />
        <KpiCard label="Avg Lines/Order" :value="pr.kpi.avg_lines_per_order.toFixed(1)"      tooltip="Average number of SKU lines per order." />
        <KpiCard label="Avg Pieces/Order" :value="(pr.kpi.avg_units_per_order ?? 0).toFixed(1)"      tooltip="Average number of picked items (pieces) per order." />
        <KpiCard label="P90 Lines/Hour"  :value="pr.kpi.p90_lines_per_hour.toFixed(0)"       tooltip="90th percentile of hourly line throughput — capacity planning baseline." />
        <KpiCard label="P95 Lines/Hour"  :value="pr.kpi.p95_lines_per_hour.toFixed(0)"       tooltip="95th percentile of hourly line throughput — capacity planning upper bound." />
        <KpiCard label="Total Pieces"    :value="pr.kpi.total_units.toLocaleString()"        tooltip="Total quantity of individual items across all order lines." />
        <KpiCard label="Unique SKU"      :value="pr.kpi.unique_sku.toLocaleString()"         tooltip="Number of distinct SKUs that appeared in orders." />
      </div>

      <!-- Throughput per Period table -->
      <div class="card-apple">
        <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">
          Throughput per Period
          <span style="font-size:11px;font-weight:400;color:var(--app-text-sec);margin-left:6px">
            ({{ pr.shifts_per_day ?? 2 }} shift{{ (pr.shifts_per_day ?? 2) !== 1 ? 's' : '' }}/day<template v-if="pr.shifts_source === 'manual'"> · manual</template><template v-else-if="pr.shifts_source === 'auto'"> · auto-detected</template>)
          </span>
        </h4>
        <div class="overflow-x-auto mt-3">
          <table class="w-full text-xs">
            <thead class="perf-thead">
              <tr class="perf-group-row">
                <th></th>
                <th colspan="3" class="perf-section-end perf-group-th" title="Aggregated per calendar day">Per Day</th>
                <th colspan="3" :class="pr.has_hourly_data ? 'perf-section-end perf-group-th' : 'perf-group-th'" title="Per Day ÷ shifts/day. Reacts to the Shifts per day setting.">Per Shift</th>
                <th
                  v-if="pr.has_hourly_data"
                  colspan="3"
                  class="perf-group-th perf-group-th-info"
                  title="Computed from observed (date, hour) data points. Independent of the Shifts per day setting — Max/Hr is the real peak, Avg/Med are over hours with activity."
                >
                  Per Hour <span style="font-weight:400;opacity:0.7">ⓘ</span>
                </th>
              </tr>
              <tr>
                <th class="px-3 py-2 text-left font-medium" style="color:var(--app-text-sec)">Metric</th>
                <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">Avg/Day</th>
                <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">Med/Day</th>
                <th class="px-3 py-2 text-center font-medium perf-section-end" style="color:var(--app-text-sec)">Max/Day</th>
                <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">Avg/Shift</th>
                <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">Med/Shift</th>
                <th class="px-3 py-2 text-center font-medium" :class="pr.has_hourly_data ? 'perf-section-end' : ''" style="color:var(--app-text-sec)">Max/Shift</th>
                <template v-if="pr.has_hourly_data">
                  <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">Avg/Hr</th>
                  <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">Med/Hr</th>
                  <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">Max/Hr</th>
                </template>
              </tr>
            </thead>
            <tbody>
              <tr class="perf-row">
                <td class="px-3 py-2 font-medium" style="color:var(--app-text)">Orders</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.avg_orders_per_day ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.median_orders_per_day ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center perf-section-end" style="color:var(--app-text-sec)">{{ (pr.kpi.max_orders_per_day ?? 0).toLocaleString() }}</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.avg_orders_per_shift ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.median_orders_per_shift ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center" :class="pr.has_hourly_data ? 'perf-section-end' : ''" style="color:var(--app-text-sec)">{{ (pr.kpi.max_orders_per_shift ?? 0).toFixed(0) }}</td>
                <template v-if="pr.has_hourly_data">
                  <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ pr.kpi.avg_orders_per_hour.toFixed(1) }}</td>
                  <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.median_orders_per_hour ?? 0).toFixed(1) }}</td>
                  <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.peak_orders_per_hour ?? 0).toLocaleString() }}</td>
                </template>
              </tr>
              <tr class="perf-row">
                <td class="px-3 py-2 font-medium" style="color:var(--app-text)">Lines</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.avg_lines_per_day ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.median_lines_per_day ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center perf-section-end" style="color:var(--app-text-sec)">{{ (pr.kpi.max_lines_per_day ?? 0).toLocaleString() }}</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.avg_lines_per_shift ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.median_lines_per_shift ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center" :class="pr.has_hourly_data ? 'perf-section-end' : ''" style="color:var(--app-text-sec)">{{ (pr.kpi.max_lines_per_shift ?? 0).toFixed(0) }}</td>
                <template v-if="pr.has_hourly_data">
                  <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ pr.kpi.avg_lines_per_hour.toFixed(1) }}</td>
                  <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.median_lines_per_hour ?? 0).toFixed(1) }}</td>
                  <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ pr.kpi.peak_lines_per_hour.toLocaleString() }}</td>
                </template>
              </tr>
              <tr class="perf-row">
                <td class="px-3 py-2 font-medium" style="color:var(--app-text)">Pieces</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.avg_units_per_day ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.median_units_per_day ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center perf-section-end" style="color:var(--app-text-sec)">{{ (pr.kpi.max_units_per_day ?? 0).toLocaleString() }}</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.avg_units_per_shift ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.median_units_per_shift ?? 0).toFixed(0) }}</td>
                <td class="px-3 py-2 text-center" :class="pr.has_hourly_data ? 'perf-section-end' : ''" style="color:var(--app-text-sec)">{{ (pr.kpi.max_units_per_shift ?? 0).toFixed(0) }}</td>
                <template v-if="pr.has_hourly_data">
                  <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ pr.kpi.avg_units_per_hour.toFixed(1) }}</td>
                  <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.median_units_per_hour ?? 0).toFixed(1) }}</td>
                  <td class="px-3 py-2 text-center" style="color:var(--app-text-sec)">{{ (pr.kpi.peak_units_per_hour ?? 0).toLocaleString() }}</td>
                </template>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Chart 1: Daily Activity -->
      <div class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Daily Activity</h4>
          <button @click="openZoom('daily', 'Daily Activity')" class="chart-zoom-btn" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="dailyChartEl" style="height:300px"></div>
      </div>

      <!-- Chart 2: Hourly Heatmap -->
      <div v-if="pr.has_hourly_data" class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Hourly Heatmap</h4>
          <button @click="openZoom('heatmap', 'Hourly Heatmap')" class="chart-zoom-btn" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="heatmapEl" style="height:380px"></div>
      </div>

      <!-- Chart 3: Hourly Throughput -->
      <div v-if="pr.has_hourly_data && pr.hourly_metrics?.length" class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Hourly Throughput</h4>
          <button @click="openZoom('hourly', 'Hourly Throughput')" class="chart-zoom-btn" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="hourlyThroughputEl" style="height:280px"></div>
      </div>

      <!-- Chart 4: Weekly Trend -->
      <div v-if="pr.weekly_trends?.length > 1" class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Weekly Trend</h4>
          <button @click="openZoom('weekly', 'Weekly Trend')" class="chart-zoom-btn" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="weeklyTrendEl" style="height:300px"></div>
      </div>

      <!-- Chart 5: Day-of-Week Profile -->
      <div v-if="pr.weekday_profile?.length" class="card-apple">
        <div class="flex items-center justify-between mb-2">
          <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Day-of-Week Profile (Avg Lines/Day)</h4>
          <button @click="openZoom('dow', 'Day-of-Week Profile')" class="chart-zoom-btn" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="dowProfileEl" style="height:260px"></div>
      </div>

      <!-- Lines per Order Distribution KPI cards -->
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
          <button @click="openZoom('linesPerOrder', 'Lines per Order Distribution')" class="chart-zoom-btn" title="Expand chart">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1 3.5V1H3.5M7.5 1H10v2.5M10 7.5V10H7.5M3.5 10H1V7.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div ref="linesPerOrderEl" style="height:280px"></div>
      </div>

      <!-- SKU Pareto Table -->
      <div class="card-apple-list overflow-hidden">
        <div class="px-4 py-3 flex flex-wrap gap-3 items-center justify-between perf-section-header">
          <div class="flex items-center gap-2 flex-wrap">
            <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">SKU Pareto</h4>
            <span v-if="pr.sku_pareto?.length" style="font-size:11px;color:var(--app-text-sec)">
              A: {{ abcPct('A') }}% · B: {{ abcPct('B') }}% · C: {{ abcPct('C') }}%
            </span>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <!-- Custom carrier dropdown with disabled states and tooltips -->
            <div v-if="availableCarriers.length" class="relative">
              <button
                @click="paretoCarrierDropdownOpen = !paretoCarrierDropdownOpen"
                class="input-apple-sm flex items-center gap-1.5"
                style="width:auto"
              >
                <span>{{ paretoCarrierFilter === 'ALL' ? 'All carriers' : (availableCarriers.find(c => c.id === paretoCarrierFilter)?.name ?? paretoCarrierFilter) }}</span>
                <svg width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
              </button>
              <!-- Backdrop -->
              <div v-if="paretoCarrierDropdownOpen" class="fixed inset-0 z-40" @click="paretoCarrierDropdownOpen = false" />
              <!-- Dropdown panel -->
              <div v-if="paretoCarrierDropdownOpen" class="absolute top-full left-0 mt-1 z-50 py-1 rounded-lg shadow-lg min-w-max" style="background:var(--card-bg,#fff);border:1px solid var(--border-color,rgba(0,0,0,0.12))">
                <button
                  @click="paretoCarrierFilter = 'ALL'; paretoCarrierDropdownOpen = false"
                  class="w-full text-left px-3 py-1.5 text-xs hover:bg-black/5"
                  :style="paretoCarrierFilter === 'ALL' ? 'color:#0071e3;font-weight:600' : 'color:var(--app-text)'"
                >All carriers</button>
                <div v-for="c in availableCarriers" :key="c.id" class="relative group">
                  <button
                    @click="!isCarrierDisabledInPareto(c.id) && !carrierHasNoData(c.id) && (paretoCarrierFilter = c.id, paretoCarrierDropdownOpen = false)"
                    class="w-full text-left px-3 py-1.5 text-xs"
                    :class="(isCarrierDisabledInPareto(c.id) || carrierHasNoData(c.id)) ? 'cursor-not-allowed' : 'hover:bg-black/5'"
                    :style="(isCarrierDisabledInPareto(c.id) || carrierHasNoData(c.id)) ? 'color:var(--app-placeholder)' : (paretoCarrierFilter === c.id ? 'color:#0071e3;font-weight:600' : 'color:var(--app-text)')"
                  >{{ c.name }}</button>
                  <div
                    v-if="isCarrierDisabledInPareto(c.id)"
                    class="absolute right-full top-1/2 -translate-y-1/2 mr-2 px-2 py-1 rounded text-xs whitespace-nowrap pointer-events-none z-50 opacity-0 group-hover:opacity-100 transition-opacity"
                    style="background:#1d1d1f;color:#fff"
                  >Not included in the current analysis scope</div>
                  <div
                    v-else-if="carrierHasNoData(c.id)"
                    class="absolute right-full top-1/2 -translate-y-1/2 mr-2 px-2 py-1 rounded text-xs whitespace-nowrap pointer-events-none z-50 opacity-0 group-hover:opacity-100 transition-opacity"
                    style="background:#1d1d1f;color:#fff"
                  >No data for this carrier</div>
                </div>
              </div>
            </div>
            <select v-model="paretoAbcFilter" class="input-apple-sm" style="width:auto">
              <option value="ALL">All</option>
              <option value="A"          :disabled="!abcFilterHasData.A">Class A</option>
              <option value="B"          :disabled="!abcFilterHasData.B">Class B</option>
              <option value="C"          :disabled="!abcFilterHasData.C">Class C</option>
              <option value="MASZYNA"    :disabled="!abcFilterHasData.MASZYNA">Machine</option>
              <option value="POZA"       :disabled="!abcFilterHasData.POZA">Non-machine</option>
              <option value="FIT"        :disabled="!abcFilterHasData.FIT">FIT</option>
              <option value="BORDERLINE" :disabled="!abcFilterHasData.BORDERLINE">Borderline</option>
              <option value="NOT_FIT"    :disabled="!abcFilterHasData.NOT_FIT">NOT FIT</option>
            </select>
            <button @click="exportParetoCsv" class="btn-apple-pill" style="font-size:12px;padding:5px 10px">Export CSV</button>
          </div>
        </div>
        <div class="px-4 pb-2 flex items-center gap-2" style="font-size:11px;color:var(--app-text-sec)">
          <span v-if="customTopN !== null">
            Threshold: top <strong style="color:var(--app-text)">{{ customTopN.toLocaleString() }} SKUs</strong>
            <button @click="customTopN = null; paretoVisibleCount = 50" class="ml-2 text-[#0071e3] hover:underline" style="font-size:11px">Reset threshold</button>
          </span>
          <span v-else>Threshold: <strong style="color:var(--app-text)">class A</strong> (default — click a row in Pareto Concentration to set a custom one)</span>
        </div>
        <div class="overflow-x-auto max-h-80">
          <table class="w-full text-xs">
            <thead class="perf-thead sticky top-0">
              <tr>
                <th class="px-3 py-2 text-left font-medium"  style="color:var(--app-text-sec)">Rank</th>
                <th class="px-3 py-2 text-left font-medium"  style="color:var(--app-text-sec)">SKU</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Lines</th>
                <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">ABC</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Cumulative %</th>
                <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">Recommendation</th>
                <th class="px-3 py-2 text-center font-medium" style="color:var(--app-text-sec)">Fit Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in visiblePareto" :key="row.sku" class="perf-row">
                <td class="px-3 py-1.5" style="color:var(--app-placeholder)">{{ row.frequency_rank }}</td>
                <td class="px-3 py-1.5 font-medium" style="color:var(--app-text)">{{ row.sku }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.total_lines.toLocaleString() }}</td>
                <td class="px-3 py-1.5 text-center">
                  <span :class="['px-1.5 py-0.5 rounded text-xs font-medium', abcClass(row.abc_class)]">{{ row.abc_class }}</span>
                </td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.cumulative_pct.toFixed(1) }}%</td>
                <td class="px-3 py-1.5 text-center">
                  <span :class="['px-1.5 py-0.5 rounded text-xs font-medium', rowRecommendation(row) === 'Machine' ? 'badge-fit' : 'badge-abc-c']">
                    {{ rowRecommendation(row) }}
                  </span>
                </td>
                <td class="px-3 py-1.5 text-center">
                  <span :class="['px-1.5 py-0.5 rounded text-xs font-medium', fitStatusClass(row.fit_status)]">
                    {{ fitStatusLabel(row.fit_status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="px-4 py-2 flex items-center justify-between">
          <p class="text-xs" style="color:var(--app-placeholder)">Showing {{ visiblePareto.length }} of {{ filteredPareto.length }} SKUs</p>
          <button
            v-if="visiblePareto.length < filteredPareto.length"
            @click="paretoVisibleCount = filteredPareto.length"
            class="text-xs text-[#0071e3] hover:underline"
          >Load more ({{ filteredPareto.length - visiblePareto.length }} remaining)</button>
        </div>
      </div>

      <!-- Pareto Concentration Table -->
      <div v-if="activeParetoaBands.length" class="card-apple-list overflow-hidden">
        <div class="px-4 py-3 flex flex-wrap gap-3 items-center justify-between perf-section-header">
          <div class="flex items-center gap-2 flex-wrap">
            <h4 style="font-size:12px;font-weight:600;color:var(--app-text);letter-spacing:-0.12px">Pareto Concentration</h4>
            <span v-if="paretoCarrierFilter !== 'ALL'" style="font-size:11px;color:var(--app-text-sec)">
              Carrier: <strong style="color:var(--app-text)">{{ availableCarriers.find(c => c.id === paretoCarrierFilter)?.name ?? paretoCarrierFilter }}</strong>
              · {{ carrierFilteredSkus.length.toLocaleString() }} SKUs
            </span>
            <span v-else style="font-size:11px;color:var(--app-text-sec)">Click a row to set the machine recommendation threshold</span>
          </div>
          <div class="flex items-center gap-2">
            <button v-if="customTopN !== null" @click="customTopN = null; paretoVisibleCount = 50" class="btn-apple-pill" style="font-size:12px;padding:5px 10px;color:#0071e3">Reset threshold</button>
            <button @click="exportParetoBandsCsv" class="btn-apple-pill" style="font-size:12px;padding:5px 10px">Export CSV</button>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-xs">
            <thead class="perf-thead sticky top-0">
              <tr>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">MovedSKU</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">CumulatedSKU</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Lines/Day</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Lines%</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Cumul.Lines%</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Pieces/Day</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Pieces%</th>
                <th class="px-3 py-2 text-right font-medium" style="color:var(--app-text-sec)">Cumul.Pieces%</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in activeParetoaBands"
                :key="row.moved_sku"
                class="perf-row"
                style="cursor:pointer"
                :style="customTopN === row.moved_sku ? 'background:rgba(0,113,227,0.10);' : ''"
                @click="setCustomTopN(row.moved_sku)"
              >
                <td class="px-3 py-1.5 text-right font-medium" style="color:var(--app-text)">{{ row.moved_sku.toLocaleString() }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.cumulated_sku_pct.toFixed(1) }}%</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.lines_day.toLocaleString() }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.lines_day_pct.toFixed(1) }}%</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.cumulated_lines_pct.toFixed(1) }}%</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.pieces_day.toLocaleString() }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.pieces_day_pct.toFixed(1) }}%</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.cumulated_pieces_pct.toFixed(1) }}%</td>
              </tr>
              <tr class="perf-row" style="font-weight:600;background:var(--table-header-bg)">
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text)">Total</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">100%</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ paretoBandTotals.lines_day.toLocaleString() }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">100%</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">100%</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ paretoBandTotals.pieces_day.toLocaleString() }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">100%</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">100%</td>
              </tr>
            </tbody>
          </table>
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
import type { RunDetail, PerformanceResult, OrdersValidationResult, PerformanceParetoBand } from '@/api/runs'
import { runsApi } from '@/api/runs'
import KpiCard from '@/components/shared/KpiCard.vue'
import ChartZoomModal from '@/components/shared/ChartZoomModal.vue'
import Plotly from 'plotly.js-dist-min'
import { useThemeStore } from '@/stores/theme'
import { useNotificationsStore } from '@/stores/notifications'
import { useAnalysisStore } from '@/stores/analysis'

const theme = useThemeStore()
const notify = useNotificationsStore()
const analysis = useAnalysisStore()

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{
  (e: 'refreshed'): void
  (e: 'navigate', tab: string): void
}>()

const analyzing = ref(false)
const analysisError = ref('')
const productiveHours = ref(7.0)
const shiftsPerDayOverride = ref<number | null>(
  ((props.run.analysis_config as { shifts_per_day_override?: number | null } | null)?.shifts_per_day_override) ?? null
)
const paretoAbcFilter = ref('ALL')
const paretoCarrierFilter = ref<string>('ALL')
const paretoCarrierDropdownOpen = ref(false)
const customTopN = ref<number | null>(null)

const analysisScope = ref<'all' | 'carriers'>('all')
const analysisCarrierIds = ref<Set<string>>(new Set())
const canRunAnalysis = computed(() =>
  analysisScope.value === 'all' || analysisCarrierIds.value.size > 0
)
function toggleAnalysisCarrier(id: string, checked: boolean) {
  const next = new Set(analysisCarrierIds.value)
  checked ? next.add(id) : next.delete(id)
  analysisCarrierIds.value = next
}

function isCarrierDisabledInPareto(carrierId: string): boolean {
  return analysisScope.value === 'carriers' && !analysisCarrierIds.value.has(carrierId)
}

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

const availableCarriers = computed(() => {
  const cr = props.run.capacity_result
  if (!cr?.carriers_analyzed?.length) return []
  return cr.carriers_analyzed.map(cid => ({
    id: cid,
    name: (cr.carrier_stats as Record<string, { carrier_name?: string }>)[cid]?.carrier_name ?? cid,
  }))
})

const skuCarrierFitMap = computed(() => {
  const cr = props.run.capacity_result
  const map = new Map<string, Set<string>>()
  if (!cr?.rows) return map
  for (const row of cr.rows) {
    if (row.fit_status === 'FIT' || row.fit_status === 'BORDERLINE') {
      if (!map.has(row.sku)) map.set(row.sku, new Set())
      map.get(row.sku)!.add(row.carrier_id)
    }
  }
  return map
})

const carrierFilteredSkus = computed(() => {
  if (!pr.value) return []
  if (paretoCarrierFilter.value === 'ALL') return pr.value.sku_pareto
  return pr.value.sku_pareto.filter(r =>
    skuCarrierFitMap.value.get(r.sku)?.has(paretoCarrierFilter.value)
  )
})

function rowRecommendation(row: { frequency_rank: number; recommendation: string }): string {
  if (customTopN.value !== null) {
    return row.frequency_rank <= customTopN.value ? 'Machine' : 'Non-machine'
  }
  return row.recommendation
}

function carrierHasNoData(carrierId: string): boolean {
  if (!pr.value) return true
  return !pr.value.sku_pareto.some(r => skuCarrierFitMap.value.get(r.sku)?.has(carrierId))
}

const abcFilterHasData = computed(() => {
  const rows = carrierFilteredSkus.value
  return {
    A: rows.some(r => r.abc_class === 'A'),
    B: rows.some(r => r.abc_class === 'B'),
    C: rows.some(r => r.abc_class === 'C'),
    MASZYNA: rows.some(r => rowRecommendation(r) === 'Machine'),
    POZA: rows.some(r => rowRecommendation(r) === 'Non-machine'),
    FIT: rows.some(r => r.fit_status === 'FIT'),
    BORDERLINE: rows.some(r => r.fit_status === 'BORDERLINE'),
    NOT_FIT: rows.some(r => r.fit_status === 'NOT_FIT'),
  }
})

function setCustomTopN(n: number) {
  customTopN.value = customTopN.value === n ? null : n
  paretoVisibleCount.value = 50
}

const filteredPareto = computed(() => {
  const rows = carrierFilteredSkus.value
  if (paretoAbcFilter.value === 'ALL') return rows
  if (paretoAbcFilter.value === 'MASZYNA') return rows.filter(r => rowRecommendation(r) === 'Machine')
  if (paretoAbcFilter.value === 'POZA') return rows.filter(r => rowRecommendation(r) === 'Non-machine')
  if (paretoAbcFilter.value === 'FIT') return rows.filter(r => r.fit_status === 'FIT')
  if (paretoAbcFilter.value === 'BORDERLINE') return rows.filter(r => r.fit_status === 'BORDERLINE')
  if (paretoAbcFilter.value === 'NOT_FIT') return rows.filter(r => r.fit_status === 'NOT_FIT')
  return rows.filter(r => r.abc_class === paretoAbcFilter.value)
})

const paretoVisibleCount = ref(50)
const visiblePareto = computed(() => filteredPareto.value.slice(0, paretoVisibleCount.value))

watch(paretoAbcFilter, () => { paretoVisibleCount.value = 50 })
watch(paretoCarrierFilter, () => { paretoVisibleCount.value = 50 })
watch(customTopN, () => { paretoVisibleCount.value = 50 })

// Reset pareto carrier filter if the selected carrier becomes disabled by analysis scope change or has no data
watch([analysisScope, analysisCarrierIds], () => {
  if (paretoCarrierFilter.value !== 'ALL' && isCarrierDisabledInPareto(paretoCarrierFilter.value)) {
    paretoCarrierFilter.value = 'ALL'
  }
})

// Reset ABC filter if selected option has no data (e.g. after carrier filter changes)
watch(abcFilterHasData, (hasData) => {
  const key = paretoAbcFilter.value as keyof typeof hasData
  if (paretoAbcFilter.value !== 'ALL' && !hasData[key]) {
    paretoAbcFilter.value = 'ALL'
  }
})

onMounted(() => {
  if (pr.value) renderCharts(pr.value)
})

watch(pr, (val) => {
  if (val) nextTick(() => renderCharts(val))
})

watch(() => theme.dark, () => {
  if (pr.value) nextTick(() => renderCharts(pr.value!))
})

async function doRunAnalysis() {
  analyzing.value = true
  analysis.start()
  analysisError.value = ''
  try {
    const carrierIds = analysisScope.value === 'carriers'
      ? [...analysisCarrierIds.value]
      : []
    await runsApi.runPerformance(props.run.id, productiveHours.value, carrierIds, shiftsPerDayOverride.value)
    emit('refreshed')
    notify.push({ type: 'success', title: 'Analysis complete' })
  } catch (e: unknown) {
    analysisError.value = (e as Error).message || 'Analysis failed.'
  } finally {
    analyzing.value = false
    analysis.stop()
  }
}

function renderCharts(data: PerformanceResult) {
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

  const WEEKDAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const weekdayOf = (s: string) => {
    const [y, m, d] = s.split('-').map(Number)
    return WEEKDAY_NAMES[new Date(y, m - 1, d).getDay()]
  }
  const labelFont = { size: 10, color: fontColor }

  if (dailyChartEl.value && data.daily_metrics.length > 0) {
    const dailyTraces = [{
      x: data.daily_metrics.map(d => d.date),
      y: data.daily_metrics.map(d => d.lines),
      customdata: data.daily_metrics.map(d => weekdayOf(d.date)),
      hovertemplate: '<b>%{customdata}</b><br>Lines: %{y:,}<extra></extra>',
      text: data.daily_metrics.map(d => d.lines.toLocaleString()),
      textposition: 'outside' as const,
      textfont: labelFont,
      cliponaxis: false,
      type: 'bar' as const,
      marker: { color: '#0071e3' },
      name: 'Lines',
    }]
    const dailyLayout = { ...base, margin: { t: 24, b: 40, l: 50, r: 10 }, xaxis: { ...ax, title: 'Date' }, yaxis: { ...ax, title: 'Lines' } }
    Plotly.newPlot(dailyChartEl.value, dailyTraces, dailyLayout, { responsive: true, displayModeBar: false })
    chartStore.daily = { traces: dailyTraces, layout: dailyLayout }
  }

  if (hourlyThroughputEl.value && data.has_hourly_data && data.hourly_metrics?.length > 0) {
    const sorted = [...data.hourly_metrics].sort((a, b) => a.hour - b.hour)
    const hourlyTraces = [{
      x: sorted.map(h => `${String(h.hour).padStart(2, '0')}:00`),
      y: sorted.map(h => h.lines),
      text: sorted.map(h => h.lines.toLocaleString()),
      textposition: 'outside' as const,
      textfont: labelFont,
      cliponaxis: false,
      type: 'bar' as const,
      marker: { color: '#0071e3' },
      name: 'Lines',
    }]
    const hourlyLayout = { ...base, margin: { t: 24, b: 40, l: 50, r: 10 }, xaxis: { ...ax, title: 'Hour of Day' }, yaxis: { ...ax, title: 'Lines' } }
    Plotly.newPlot(hourlyThroughputEl.value, hourlyTraces, hourlyLayout, { responsive: true, displayModeBar: false })
    chartStore.hourly = { traces: hourlyTraces, layout: hourlyLayout }
  }

  if (weeklyTrendEl.value && data.weekly_trends?.length > 1) {
    const weeklyTraces = [{
      x: data.weekly_trends.map(w => `W${String(w.week).padStart(2, '0')} ${w.year}`),
      y: data.weekly_trends.map(w => w.lines),
      text: data.weekly_trends.map(w => w.lines.toLocaleString()),
      textposition: 'outside' as const,
      textfont: labelFont,
      cliponaxis: false,
      type: 'bar' as const,
      marker: { color: '#0071e3' },
      name: 'Lines',
    }]
    const weeklyLayout = { ...base, margin: { t: 24, b: 60, l: 50, r: 10 }, xaxis: { ...ax, title: 'Week', tickangle: -45 }, yaxis: { ...ax, title: 'Lines' } }
    Plotly.newPlot(weeklyTrendEl.value, weeklyTraces, weeklyLayout, { responsive: true, displayModeBar: false })
    chartStore.weekly = { traces: weeklyTraces, layout: weeklyLayout }
  }

  if (dowProfileEl.value && data.weekday_profile?.length > 0) {
    const dowTraces = [{
      x: data.weekday_profile.map(d => d.day),
      y: data.weekday_profile.map(d => d.avg_lines),
      text: data.weekday_profile.map(d => d.avg_lines.toLocaleString(undefined, { maximumFractionDigits: 1 })),
      textposition: 'outside' as const,
      textfont: labelFont,
      cliponaxis: false,
      type: 'bar' as const,
      marker: { color: '#0071e3' },
      name: 'Avg Lines',
    }]
    const dowLayout = { ...base, margin: { t: 24, b: 40, l: 50, r: 10 }, xaxis: { ...ax, title: 'Day of Week' }, yaxis: { ...ax, title: 'Avg Lines/Day' } }
    Plotly.newPlot(dowProfileEl.value, dowTraces, dowLayout, { responsive: true, displayModeBar: false })
    chartStore.dow = { traces: dowTraces, layout: dowLayout }
  }

  if (linesPerOrderEl.value && data.lines_per_order_dist?.length > 0) {
    const lpoTraces = [{
      x: data.lines_per_order_dist.map(b => b.bin),
      y: data.lines_per_order_dist.map(b => b.count),
      text: data.lines_per_order_dist.map(b => b.count.toLocaleString()),
      textposition: 'outside' as const,
      textfont: labelFont,
      cliponaxis: false,
      type: 'bar' as const,
      marker: { color: '#0071e3' },
      name: 'Orders',
    }]
    const lpoLayout = { ...base, margin: { t: 24, b: 40, l: 50, r: 10 }, xaxis: { ...ax, title: 'Lines per Order', type: 'category' as const, categoryorder: 'array' as const, categoryarray: data.lines_per_order_dist.map(b => b.bin) }, yaxis: { ...ax, title: 'Number of Orders' } }
    Plotly.newPlot(linesPerOrderEl.value, lpoTraces, lpoLayout, { responsive: true, displayModeBar: false })
    chartStore.linesPerOrder = { traces: lpoTraces, layout: lpoLayout }
  }

  if (heatmapEl.value && data.has_hourly_data && data.datehour_metrics.length > 0) {
    const dates = [...new Set(data.datehour_metrics.map(d => d.date))].sort()
    const hours = Array.from({ length: 24 }, (_, i) => i)
    const z = dates.map(date =>
      hours.map(hour => {
        const found = data.datehour_metrics.find(d => d.date === date && d.hour === hour)
        return found ? found.lines : 0
      })
    )
    const heatmapZero = isDark ? '#1a1a1c' : '#f0f4ff'
    const heatmapTraces = [{
      z,
      x: hours.map(h => `${String(h).padStart(2, '0')}:00`),
      y: dates,
      type: 'heatmap' as const,
      colorscale: [[0, heatmapZero], [0.001, isDark ? '#1e3a5f' : '#dbeafe'], [0.5, '#0071e3'], [1, '#003d82']] as [number, string][],
      zmin: 0,
      showscale: true,
    }]
    const heatmapLayout = { ...base, margin: { t: 10, b: 60, l: 80, r: 10 }, xaxis: { ...ax, title: 'Hour' }, yaxis: { ...ax, title: 'Date', autorange: 'reversed' } }
    Plotly.newPlot(heatmapEl.value, heatmapTraces, heatmapLayout, { responsive: true, displayModeBar: false })
    chartStore.heatmap = { traces: heatmapTraces, layout: heatmapLayout }
  }
}

function abcClass(cls: string) {
  if (cls === 'A') return 'badge-fit'
  if (cls === 'B') return 'badge-bl'
  return 'badge-abc-c'
}

function fitStatusClass(status: string | null | undefined): string {
  if (status === 'FIT') return 'badge-fit'
  if (status === 'BORDERLINE') return 'badge-bl'
  if (status === 'NOT_FIT') return 'badge-nf'
  return 'badge-abc-c'
}

function fitStatusLabel(status: string | null | undefined): string {
  if (status === 'FIT') return 'FIT'
  if (status === 'BORDERLINE') return 'Borderline'
  if (status === 'NOT_FIT') return 'NOT FIT'
  return 'N/A'
}

function abcPct(cls: string) {
  const skus = carrierFilteredSkus.value
  if (!skus.length) return '0.0'
  const count = skus.filter(r => r.abc_class === cls).length
  return ((count / skus.length) * 100).toFixed(1)
}

function exportParetoCsv() {
  if (!pr.value?.sku_pareto?.length) return
  const headers = ['rank', 'sku', 'lines', 'abc_class', 'cumulative_pct', 'recommendation', 'fit_status']
  const rows = pr.value.sku_pareto.map(r => [
    r.frequency_rank,
    r.sku,
    r.total_lines,
    r.abc_class,
    r.cumulative_pct.toFixed(2) + '%',
    rowRecommendation(r),
    fitStatusLabel(r.fit_status),
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

const activeParetoaBands = computed((): PerformanceParetoBand[] => {
  if (!pr.value) return []
  if (paretoCarrierFilter.value === 'ALL') return pr.value.pareto_bands ?? []

  const sorted = [...carrierFilteredSkus.value].sort((a, b) => b.total_lines - a.total_lines)
  if (!sorted.length) return []

  const totalDays = Math.max(pr.value.daily_metrics.length, 1)
  const totalSkus = sorted.length
  const totalLinesAll = sorted.reduce((s, r) => s + r.total_lines, 0)
  const totalUnitsAll = sorted.reduce((s, r) => s + r.total_units, 0)
  if (totalLinesAll === 0) return []

  const totalLinesDay = totalLinesAll / totalDays
  const totalPiecesDay = totalUnitsAll / totalDays

  const FIXED = [10,20,30,40,50,60,70,80,90,100,200,300,400,500,600,700,800,900,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,15000,20000,25000,30000,40000,50000]
  const breakpoints = [...FIXED.filter(bp => bp < totalSkus), totalSkus]

  const results: PerformanceParetoBand[] = []
  let prevBp = 0
  let cumulLines = 0
  let cumulUnits = 0

  for (const bp of breakpoints) {
    const band = sorted.slice(prevBp, bp)
    const bandLines = band.reduce((s, r) => s + r.total_lines, 0)
    const bandUnits = band.reduce((s, r) => s + r.total_units, 0)
    cumulLines += bandLines
    cumulUnits += bandUnits
    const linesDay = bandLines / totalDays
    const piecesDay = bandUnits / totalDays
    results.push({
      moved_sku: bp,
      cumulated_sku_pct: Math.round(bp / totalSkus * 1000) / 10,
      lines_day: Math.round(linesDay * 10) / 10,
      lines_day_pct: totalLinesDay ? Math.round(linesDay / totalLinesDay * 1000) / 10 : 0,
      cumulated_lines_pct: Math.round(cumulLines / totalLinesAll * 1000) / 10,
      pieces_day: Math.round(piecesDay * 10) / 10,
      pieces_day_pct: totalPiecesDay ? Math.round(piecesDay / totalPiecesDay * 1000) / 10 : 0,
      cumulated_pieces_pct: totalUnitsAll ? Math.round(cumulUnits / totalUnitsAll * 1000) / 10 : 0,
    })
    prevBp = bp
  }
  return results
})

const paretoBandTotals = computed(() => {
  const bands = activeParetoaBands.value
  return {
    lines_day: Math.round(bands.reduce((s, b) => s + b.lines_day, 0)),
    pieces_day: Math.round(bands.reduce((s, b) => s + b.pieces_day, 0)),
  }
})

function exportParetoBandsCsv() {
  const bands = activeParetoaBands.value
  if (!bands?.length) return
  const headers = ['moved_sku', 'cumulated_sku_pct', 'lines_day', 'lines_day_pct', 'cumulated_lines_pct', 'pieces_day', 'pieces_day_pct', 'cumulated_pieces_pct']
  const rows = bands.map(b => [b.moved_sku, b.cumulated_sku_pct + '%', b.lines_day, b.lines_day_pct + '%', b.cumulated_lines_pct + '%', b.pieces_day, b.pieces_day_pct + '%', b.cumulated_pieces_pct + '%'])
  const totals = paretoBandTotals.value
  rows.push(['Total', '100%', totals.lines_day, '100%', '100%', totals.pieces_day, '100%', '100%'])
  const csv = '﻿' + [headers, ...rows].map(r => r.map(v => `"${v}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'pareto_bands.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.perf-thead {
  background: var(--table-header-bg);
  border-bottom: 1px solid var(--table-divider);
}

.perf-section-header {
  border-bottom: 1px solid var(--table-divider);
}

.perf-row {
  border-top: 1px solid var(--table-divider);
}
.perf-row:hover { background: var(--table-row-hover); }

/* Throughput per Period — section grouping */
.perf-section-end {
  border-right: 1px solid var(--table-divider);
}
.perf-group-row > th {
  border-bottom: 1px solid var(--table-divider);
}
.perf-group-th {
  padding: 6px 12px 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  text-align: center;
  color: var(--app-text-sec);
}
.perf-group-th-info { cursor: help; }

/* ABC badge classes shared with CapacityTab */
.badge-fit   { background: var(--badge-fit-bg); color: var(--badge-fit-color); }
.badge-bl    { background: var(--badge-bl-bg);  color: var(--badge-bl-color); }
.badge-nf    { background: var(--badge-nf-bg);  color: var(--badge-nf-color); }
.badge-abc-c { background: var(--table-header-bg); color: var(--app-text-sec); }

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
