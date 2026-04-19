<template>
  <div v-if="run">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <RouterLink to="/runs" class="text-sm text-gray-400 hover:text-gray-600">← Analyses</RouterLink>
        <!-- Inline rename -->
        <div class="mt-1 flex items-center gap-2">
          <input
            v-if="renaming"
            ref="renameInput"
            v-model="renameValue"
            @blur="saveRename"
            @keydown.enter="saveRename"
            @keydown.escape="renaming = false"
            class="text-lg font-semibold text-gray-800 border-b border-blue-400 outline-none bg-transparent w-72"
          />
          <h2
            v-else
            class="text-lg font-semibold text-gray-800 cursor-pointer hover:text-blue-600"
            title="Click to rename"
            @click="startRename"
          >{{ run.client_name }}</h2>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="showNotes = true"
          :class="['flex items-center gap-1.5 px-3 py-1.5 text-sm border rounded transition-colors', notesValue ? 'text-blue-600 border-blue-400 bg-blue-50' : 'text-gray-600 border-gray-300 hover:bg-gray-50']"
          title="Notes"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
          </svg>
          Notes
        </button>
        <button
          @click="showShare = true"
          class="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50 transition-colors"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z"/>
          </svg>
          Share
        </button>
        <StatusBadge :status="run.status" />
      </div>
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
        <PerformanceTab :run="run" @refreshed="loadRun" @navigate="activeTab = $event" />
      </div>
      <div v-else-if="activeTab === 'reports'">
        <ReportsTab :run="run" />
      </div>
    </div>

    <NotesModal v-if="showNotes" :run-id="run.id" :initial-notes="notesValue" @close="showNotes = false" @saved="notesValue = $event" />
    <ShareModal v-if="showShare" :run-id="run.id" @close="showShare = false" />
  </div>

  <div v-else-if="loading" class="text-sm text-gray-400">Loading…</div>
  <div v-else class="text-sm text-red-500">Run not found.</div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useRunStore } from '@/stores/run'
import type { RunDetail } from '@/api/runs'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import ImportTab from '@/components/analysis/ImportTab.vue'
import QualityTab from '@/components/analysis/QualityTab.vue'
import CapacityTab from '@/components/analysis/CapacityTab.vue'
import PerformanceTab from '@/components/analysis/PerformanceTab.vue'
import ReportsTab from '@/components/analysis/ReportsTab.vue'
import ShareModal from '@/components/analysis/ShareModal.vue'
import NotesModal from '@/components/analysis/NotesModal.vue'

const route = useRoute()
const runStore = useRunStore()

const run = ref<RunDetail | null>(null)
const loading = ref(true)
const activeTab = ref('import')
const showShare = ref(false)
const showNotes = ref(false)

// Rename
const renaming = ref(false)
const renameValue = ref('')
const renameInput = ref<HTMLInputElement | null>(null)

function startRename() {
  renameValue.value = run.value?.client_name ?? ''
  renaming.value = true
  nextTick(() => renameInput.value?.select())
}

async function saveRename() {
  renaming.value = false
  if (!run.value || renameValue.value === run.value.client_name || !renameValue.value.trim()) return
  await runStore.patchRun(run.value.id, { client_name: renameValue.value.trim() })
  run.value = runStore.currentRun
}

// Notes
const notesValue = ref('')

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
  notesValue.value = run.value?.notes ?? ''
}

onMounted(async () => {
  await loadRun()
  loading.value = false
  if (run.value?.capacity_result) activeTab.value = 'capacity'
  else if (run.value?.quality_result || run.value?.orders_validation_result) activeTab.value = 'quality'
})
</script>
