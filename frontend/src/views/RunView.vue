<template>
  <div v-if="run">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <RouterLink to="/runs" class="text-sm text-gray-400 hover:text-gray-600">← Analyses</RouterLink>
        <h2 class="text-lg font-semibold text-gray-800 mt-1">{{ run.client_name }}</h2>
      </div>
      <StatusBadge :status="run.status" />
    </div>

    <!-- Tabs -->
    <div class="mb-0">
      <nav class="flex gap-1 items-end">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'px-4 py-2 text-sm font-medium rounded-t-md border transition-colors cursor-pointer',
            activeTab === tab.id
              ? 'border-blue-400 bg-white text-blue-600 -mb-px relative z-10 border-b-white'
              : 'border-gray-300 bg-gray-50 text-gray-500 hover:bg-white hover:text-gray-700',
          ]"
        >
          {{ tab.label }}
        </button>
      </nav>
    </div>

    <!-- Tab content -->
    <div class="border border-gray-200 rounded-b-lg rounded-tr-lg mb-6">
      <div v-if="activeTab === 'import'">
        <ImportTab :run="run" @refreshed="loadRun" @navigate="activeTab = $event" />
      </div>
      <div v-else-if="activeTab === 'quality'">
        <QualityTab :run="run" @refreshed="loadRun" />
      </div>
      <div v-else-if="activeTab === 'capacity'">
        <CapacityTab :run="run" @refreshed="loadRun" />
      </div>
      <div v-else-if="activeTab === 'performance'">
        <PerformanceTab :run="run" @refreshed="loadRun" />
      </div>
      <div v-else-if="activeTab === 'reports'">
        <ReportsTab :run="run" />
      </div>
    </div>
  </div>

  <div v-else-if="loading" class="text-sm text-gray-400">Loading…</div>
  <div v-else class="text-sm text-red-500">Run not found.</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useRunStore } from '@/stores/run'
import type { RunDetail } from '@/api/runs'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import ImportTab from '@/components/analysis/ImportTab.vue'
import QualityTab from '@/components/analysis/QualityTab.vue'
import CapacityTab from '@/components/analysis/CapacityTab.vue'
import PerformanceTab from '@/components/analysis/PerformanceTab.vue'
import ReportsTab from '@/components/analysis/ReportsTab.vue'

const route = useRoute()
const runStore = useRunStore()

const run = ref<RunDetail | null>(null)
const loading = ref(true)
const activeTab = ref('import')

const tabs = [
  { id: 'import', label: 'Import' },
  { id: 'quality', label: 'Validation' },
  { id: 'capacity', label: 'Capacity' },
  { id: 'performance', label: 'Performance' },
  { id: 'reports', label: 'Reports' },
]

async function loadRun() {
  await runStore.fetchRun(route.params.id as string)
  run.value = runStore.currentRun
}

onMounted(async () => {
  await loadRun()
  loading.value = false
  // Auto-advance to first completed tab
  if (run.value?.capacity_result) activeTab.value = 'capacity'
  else if (run.value?.quality_result) activeTab.value = 'quality'
})
</script>
