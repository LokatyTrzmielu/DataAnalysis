<template>
  <div class="space-y-6">
    <!-- Upload + run capacity -->
    <div class="bg-white border border-gray-200 rounded-lg p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Run capacity analysis</h3>
      <div class="flex gap-3 items-end flex-wrap">
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
        <div class="flex gap-3 items-center text-sm">
          <label class="flex items-center gap-1.5 text-gray-600">
            <input v-model="prioritizationMode" type="checkbox" />
            Prioritization
          </label>
          <label class="flex items-center gap-1.5 text-gray-600">
            <input v-model="bestFitMode" type="checkbox" />
            Best fit
          </label>
        </div>
        <button
          @click="runCapacity"
          :disabled="running || (!selectedFile && !run.masterdata_path)"
          class="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
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

      <!-- Per-carrier table -->
      <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RunDetail, CapacityResult } from '@/api/runs'
import { runsApi } from '@/api/runs'
import KpiCard from '@/components/shared/KpiCard.vue'

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{ (e: 'refreshed'): void }>()

const fileInput = ref<HTMLInputElement>()
const selectedFile = ref<File | null>(null)
const running = ref(false)
const error = ref('')
const prioritizationMode = ref(false)
const bestFitMode = ref(false)

const cr = computed(() => props.run.capacity_result as CapacityResult | null)

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  error.value = ''
}

async function runCapacity() {
  running.value = true
  error.value = ''
  try {
    await runsApi.runCapacity(props.run.id, selectedFile.value!, {
      prioritization_mode: prioritizationMode.value,
      best_fit_mode: bestFitMode.value,
    })
    emit('refreshed')
  } catch (e: unknown) {
    error.value = (e as Error).message || 'Analysis failed.'
  } finally {
    running.value = false
  }
}
</script>
