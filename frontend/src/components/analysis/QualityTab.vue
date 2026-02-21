<template>
  <div>
    <div v-if="!qr" class="text-sm text-gray-400">
      No quality results yet. Import masterdata in the Import tab first.
    </div>
    <div v-else class="space-y-4">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiCard label="Records" :value="qr.total_records" />
        <KpiCard label="Quality score" :value="`${qr.overall_score?.toFixed(1)}%`" />
        <KpiCard label="Dimension coverage" :value="`${qr.dimensions_coverage_pct?.toFixed(1)}%`" />
        <KpiCard label="Weight coverage" :value="`${qr.weight_coverage_pct?.toFixed(1)}%`" />
      </div>

      <div class="bg-white border border-gray-200 rounded-lg p-4">
        <h3 class="text-sm font-semibold text-gray-700 mb-3">Issue counts</h3>
        <div class="grid grid-cols-3 gap-3 text-sm">
          <div>
            <span class="text-gray-500">Missing critical</span>
            <p class="font-semibold text-gray-800">{{ qr.missing_critical_count }}</p>
          </div>
          <div>
            <span class="text-gray-500">Suspect outliers</span>
            <p class="font-semibold text-gray-800">{{ qr.suspect_outliers_count }}</p>
          </div>
          <div>
            <span class="text-gray-500">Duplicates</span>
            <p class="font-semibold text-gray-800">{{ qr.duplicates_count }}</p>
          </div>
          <div>
            <span class="text-gray-500">Conflicts</span>
            <p class="font-semibold text-gray-800">{{ qr.conflicts_count }}</p>
          </div>
          <div>
            <span class="text-gray-500">Imputed dims</span>
            <p class="font-semibold text-gray-800">{{ qr.imputed_dimensions_count }}</p>
          </div>
          <div>
            <span class="text-gray-500">Imputed weight</span>
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

const props = defineProps<{ run: RunDetail }>()
const qr = computed(() => props.run.quality_result as Record<string, number> | null)
</script>
