<template>
  <div>
    <div v-if="!qr && !ovr" class="text-sm text-gray-400 p-4">
      No validation results yet. Import data in the Import tab first.
    </div>

    <div v-else class="flex flex-col" style="gap:24px">

      <!-- ── Masterdata section ── -->
      <details v-if="qr" open class="card-apple-list overflow-hidden">
        <summary class="px-4 py-3 cursor-pointer select-none flex items-center justify-between" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">
          <span>Masterdata</span>
          <svg class="w-4 h-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </summary>
        <div class="px-4 pb-4 pt-2 space-y-4">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <KpiCard label="Records" :value="qr.total_records" tooltip="Total number of products (SKUs) loaded from the file." />
            <KpiCard label="Quality score" :value="`${qr.overall_score?.toFixed(1)}%`" tooltip="Weighted overall data quality. 100% means no issues were found." />
            <KpiCard label="Dimension coverage" :value="`${qr.dimensions_coverage_pct?.toFixed(1)}%`" tooltip="Percentage of records with all three dimensions (length, width, height) present." />
            <KpiCard label="Weight coverage" :value="`${qr.weight_coverage_pct?.toFixed(1)}%`" tooltip="Percentage of records with weight data present." />
          </div>

          <div class="card-apple" style="background:#f5f5f7">
            <h3 class="mb-3" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Issue counts</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
              <div class="flex items-center justify-between gap-2">
                <span class="text-gray-500 flex items-center gap-1">
                  Missing critical
                  <HelpTip text="SKUs missing at least one required field (e.g. SKU code, dimensions, weight)." />
                </span>
                <span class="font-semibold text-gray-800">{{ qr.missing_critical_count }}</span>
              </div>
              <div class="flex items-center justify-between gap-2">
                <span class="text-gray-500 flex items-center gap-1">
                  Suspect outliers
                  <HelpTip text="SKUs with values statistically far from the dataset median — likely data entry errors." />
                </span>
                <span class="font-semibold text-gray-800">{{ qr.suspect_outliers_count }}</span>
              </div>
              <div class="flex items-center justify-between gap-2">
                <span class="text-gray-500 flex items-center gap-1">
                  Duplicates
                  <HelpTip text="SKUs appearing more than once with the same identifier." />
                </span>
                <span class="font-semibold text-gray-800">{{ qr.duplicates_count }}</span>
              </div>
              <div class="flex items-center justify-between gap-2">
                <span class="text-gray-500 flex items-center gap-1">
                  Conflicts
                  <HelpTip text="SKUs sharing the same identifier but with different dimension or weight values." />
                </span>
                <span class="font-semibold text-gray-800">{{ qr.conflicts_count }}</span>
              </div>
              <div class="flex items-center justify-between gap-2">
                <span class="text-gray-500 flex items-center gap-1">
                  Imputed dims
                  <HelpTip text="SKUs where missing dimensions were estimated from other records in the same product family." />
                </span>
                <span class="font-semibold text-gray-800">{{ qr.imputed_dimensions_count }}</span>
              </div>
              <div class="flex items-center justify-between gap-2">
                <span class="text-gray-500 flex items-center gap-1">
                  Imputed weight
                  <HelpTip text="SKUs where missing weight was estimated from similar products in the dataset." />
                </span>
                <span class="font-semibold text-gray-800">{{ qr.imputed_weight_count }}</span>
              </div>
            </div>
          </div>
        </div>
      </details>

      <!-- ── Orders section ── -->
      <details v-if="ovr" open class="card-apple-list overflow-hidden">
        <summary class="px-4 py-3 cursor-pointer select-none flex items-center justify-between" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">
          <span>Orders</span>
          <svg class="w-4 h-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </summary>
        <div class="px-4 pb-4 pt-2 space-y-4">

          <!-- A: Summary KPIs -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <KpiCard label="Total rows" :value="ovr.total_rows.toLocaleString()" tooltip="Total number of order lines imported." />
            <KpiCard label="Date range" :value="`${ovr.date_from} — ${ovr.date_to}`" tooltip="First and last order date in the dataset." />
            <KpiCard label="Unique days" :value="ovr.unique_days" tooltip="Number of distinct calendar days with at least one order." />
            <KpiCard label="Hourly data" :value="ovr.has_hourly_data ? 'Yes' : 'No'" tooltip="Whether the file contains hour-level timestamps." />
          </div>

          <!-- B: Date coverage -->
          <div class="card-apple" style="background:#f5f5f7">
            <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm mb-2">
              <span class="text-gray-700">
                Calendar coverage:
                <strong :class="ovr.date_coverage_pct >= 80 ? 'text-green-700' : ovr.date_coverage_pct >= 50 ? 'text-yellow-700' : 'text-red-700'">
                  {{ ovr.date_coverage_pct.toFixed(1) }}%
                </strong>
                ({{ ovr.unique_days }} of {{ ovr.total_calendar_days }} days)
              </span>
              <span v-if="ovr.max_gap_days > 0" class="text-gray-500">
                · Largest gap: <strong class="text-gray-700">{{ ovr.max_gap_days }} days</strong>
              </span>
              <span v-if="ovr.gap_count === 0" class="text-green-600 text-xs">No gaps</span>
            </div>
            <details v-if="ovr.gap_list.length > 0">
              <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                Show gaps ({{ ovr.gap_count }} total)
              </summary>
              <div class="overflow-x-auto mt-2">
                <table class="text-xs w-full">
                  <thead>
                    <tr class="text-gray-500 border-b border-gray-200">
                      <th class="pb-1 text-left font-medium">From</th>
                      <th class="pb-1 text-left font-medium pl-4">To</th>
                      <th class="pb-1 text-right font-medium">Days</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-100">
                    <tr v-for="(gap, i) in ovr.gap_list" :key="i" class="text-gray-700">
                      <td class="py-0.5">{{ gap.from }}</td>
                      <td class="py-0.5 pl-4">{{ gap.to }}</td>
                      <td class="py-0.5 text-right">{{ gap.days }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </details>
          </div>

          <!-- C: Data issues -->
          <div class="card-apple" style="background:#f5f5f7">
            <p class="text-xs font-medium text-gray-600 mb-3">Data issues</p>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 text-sm">
              <div>
                <span class="text-gray-500 text-xs">Missing SKUs</span>
                <p class="font-semibold" :class="ovr.missing_sku_count > 0 ? 'text-red-700' : 'text-gray-800'">
                  {{ ovr.missing_sku_count }}
                  <span v-if="ovr.missing_sku_count > 0" class="text-xs font-normal text-gray-500">({{ ovr.missing_sku_pct.toFixed(1) }}%)</span>
                </p>
              </div>
              <div>
                <span class="text-gray-500 text-xs">Qty null</span>
                <p class="font-semibold" :class="ovr.qty_null_count > 0 ? 'text-yellow-700' : 'text-gray-800'">{{ ovr.qty_null_count }}</p>
              </div>
              <div>
                <span class="text-gray-500 text-xs">Qty zero</span>
                <p class="font-semibold" :class="ovr.qty_zero_count > 0 ? 'text-yellow-700' : 'text-gray-800'">{{ ovr.qty_zero_count }}</p>
              </div>
              <div>
                <span class="text-gray-500 text-xs">Qty negative</span>
                <p class="font-semibold" :class="ovr.qty_negative_count > 0 ? 'text-red-700' : 'text-gray-800'">{{ ovr.qty_negative_count }}</p>
              </div>
              <div>
                <span class="text-gray-500 text-xs flex items-center gap-1">
                  Qty outliers
                  <HelpTip :text="`Values above threshold (mean + 3σ = ${ovr.qty_outlier_threshold.toFixed(0)}).`" />
                </span>
                <p class="font-semibold" :class="ovr.qty_outlier_count > 0 ? 'text-yellow-700' : 'text-gray-800'">{{ ovr.qty_outlier_count }}</p>
              </div>
            </div>
          </div>

          <!-- D: SKU cross-validation -->
          <div class="card-apple" style="background:#f5f5f7">
            <p class="text-xs font-medium text-gray-600 mb-3">SKU cross-validation</p>
            <div v-if="ovr.sku_xval_available" class="space-y-2">
              <details>
                <summary class="text-sm cursor-pointer hover:text-gray-700">
                  <span :class="ovr.orders_skus_not_in_masterdata_count > 0 ? 'text-yellow-700 font-medium' : 'text-gray-700'">
                    Unknown SKUs (in orders, not in masterdata): {{ ovr.orders_skus_not_in_masterdata_count }}
                  </span>
                </summary>
                <div v-if="ovr.orders_skus_not_in_masterdata.length > 0" class="mt-1 text-xs text-gray-600 pl-4 max-h-32 overflow-y-auto">
                  {{ ovr.orders_skus_not_in_masterdata.join(', ') }}
                  <span v-if="ovr.orders_skus_not_in_masterdata_count > ovr.orders_skus_not_in_masterdata.length" class="text-gray-400">
                    … and {{ ovr.orders_skus_not_in_masterdata_count - ovr.orders_skus_not_in_masterdata.length }} more
                  </span>
                </div>
              </details>
              <details>
                <summary class="text-sm cursor-pointer hover:text-gray-700">
                  <span class="text-gray-700">
                    Inactive SKUs (in masterdata, not in orders): {{ ovr.masterdata_skus_not_in_orders_count }}
                  </span>
                </summary>
                <div v-if="ovr.masterdata_skus_not_in_orders.length > 0" class="mt-1 text-xs text-gray-600 pl-4 max-h-32 overflow-y-auto">
                  {{ ovr.masterdata_skus_not_in_orders.join(', ') }}
                  <span v-if="ovr.masterdata_skus_not_in_orders_count > ovr.masterdata_skus_not_in_orders.length" class="text-gray-400">
                    … and {{ ovr.masterdata_skus_not_in_orders_count - ovr.masterdata_skus_not_in_orders.length }} more
                  </span>
                </div>
              </details>
            </div>
            <p v-else class="text-xs text-gray-400">Import masterdata to enable SKU cross-validation.</p>
          </div>

          <!-- E: Working pattern profile -->
          <div class="card-apple" style="background:#f5f5f7">
            <p class="text-xs font-medium text-gray-600 mb-3">Working pattern</p>
            <div v-if="Object.keys(ovr.weekday_distribution).length > 0">
              <div class="space-y-1.5">
                <div
                  v-for="(label, idx) in weekdayLabels"
                  :key="idx"
                  class="flex items-center gap-2 text-xs"
                >
                  <span class="w-8 text-gray-500 shrink-0">{{ label }}</span>
                  <div class="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div
                      class="h-3 rounded-full transition-all"
                      :style="{ background: idx === ovr.most_active_weekday ? '#0071e3' : 'rgba(0,113,227,0.3)', width: `${ovr.weekday_distribution[String(idx)] ?? 0}%` }"
                    ></div>
                  </div>
                  <span class="w-10 text-right text-gray-500">{{ (ovr.weekday_distribution[String(idx)] ?? 0).toFixed(1) }}%</span>
                </div>
              </div>
              <p class="text-xs text-gray-500 mt-2">
                Most active: <strong class="text-gray-700">{{ weekdayLabels[ovr.most_active_weekday ?? 0] }}</strong>
                · Least active: <strong class="text-gray-700">{{ weekdayLabels[ovr.least_active_weekday ?? 6] }}</strong>
              </p>
            </div>
            <p v-else class="text-xs text-gray-400">No weekday data available.</p>
          </div>

        </div>
      </details>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RunDetail, OrdersValidationResult } from '@/api/runs'
import KpiCard from '@/components/shared/KpiCard.vue'
import HelpTip from '@/components/shared/HelpTip.vue'

const props = defineProps<{ run: RunDetail }>()

const qr = computed(() => props.run.quality_result as Record<string, number> | null)
const ovr = computed(() => props.run.orders_validation_result as OrdersValidationResult | null)

const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
</script>
