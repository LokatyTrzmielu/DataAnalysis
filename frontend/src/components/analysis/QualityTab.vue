<template>
  <div>
    <div v-if="!qr" class="text-sm text-gray-400">
      No quality results yet. Import masterdata in the Import tab first.
    </div>
    <div v-else class="space-y-4">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiCard
          label="Records"
          :value="qr.total_records"
          tooltip="Total number of products (SKUs) loaded from the file."
        />
        <KpiCard
          label="Quality score"
          :value="`${qr.overall_score?.toFixed(1)}%`"
          tooltip="Weighted overall data quality. 100% means no issues were found."
        />
        <KpiCard
          label="Dimension coverage"
          :value="`${qr.dimensions_coverage_pct?.toFixed(1)}%`"
          tooltip="Percentage of records with all three dimensions (length, width, height) present."
        />
        <KpiCard
          label="Weight coverage"
          :value="`${qr.weight_coverage_pct?.toFixed(1)}%`"
          tooltip="Percentage of records with weight data present."
        />
      </div>

      <div class="bg-white border border-gray-200 rounded-lg p-4">
        <h3 class="text-sm font-semibold text-gray-700 mb-3">Issue counts</h3>
        <div class="grid grid-cols-3 gap-3 text-sm">
          <div>
            <span class="text-gray-500 flex items-center gap-1">
              Missing critical
              <HelpTip text="SKUs missing at least one required field (e.g. SKU code, dimensions, weight)." />
            </span>
            <p class="font-semibold text-gray-800">{{ qr.missing_critical_count }}</p>
          </div>
          <div>
            <span class="text-gray-500 flex items-center gap-1">
              Suspect outliers
              <HelpTip text="SKUs with values statistically far from the dataset median — likely data entry errors." />
            </span>
            <p class="font-semibold text-gray-800">{{ qr.suspect_outliers_count }}</p>
          </div>
          <div>
            <span class="text-gray-500 flex items-center gap-1">
              Duplicates
              <HelpTip text="SKUs appearing more than once with the same identifier." />
            </span>
            <p class="font-semibold text-gray-800">{{ qr.duplicates_count }}</p>
          </div>
          <div>
            <span class="text-gray-500 flex items-center gap-1">
              Conflicts
              <HelpTip text="SKUs sharing the same identifier but with different dimension or weight values." />
            </span>
            <p class="font-semibold text-gray-800">{{ qr.conflicts_count }}</p>
          </div>
          <div>
            <span class="text-gray-500 flex items-center gap-1">
              Imputed dims
              <HelpTip text="SKUs where missing dimensions were estimated from other records in the same product family." />
            </span>
            <p class="font-semibold text-gray-800">{{ qr.imputed_dimensions_count }}</p>
          </div>
          <div>
            <span class="text-gray-500 flex items-center gap-1">
              Imputed weight
              <HelpTip text="SKUs where missing weight was estimated from similar products in the dataset." />
            </span>
            <p class="font-semibold text-gray-800">{{ qr.imputed_weight_count }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RunDetail } from '@/api/runs'
import KpiCard from '@/components/shared/KpiCard.vue'
import HelpTip from '@/components/shared/HelpTip.vue'

const props = defineProps<{ run: RunDetail }>()
const qr = computed(() => props.run.quality_result as Record<string, number> | null)
</script>
