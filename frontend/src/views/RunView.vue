<template>
  <div v-if="run">
    <!-- Header -->
    <div class="mb-6">
      <!-- Top row: back button left, action buttons right -->
      <div class="flex items-center justify-between">
        <RouterLink to="/runs" class="btn-apple-pill" style="text-decoration:none;font-size:13px">← Analyses</RouterLink>
        <div class="flex items-center gap-2">
        <StatusBadge :status="run.status" />
        <button
          @click="showNotes = true"
          class="btn-apple-pill"
          :style="notesValue ? 'color:#0071e3;border-color:#0071e3' : ''"
          title="Notes"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
          </svg>
          Notes
        </button>
        <button
          @click="showShare = true"
          class="btn-apple-pill"
          title="Share"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z"/>
          </svg>
          Share
        </button>
        </div>
      </div>
      <!-- Bottom row: analysis name -->
      <div class="mt-2 flex items-center gap-2">
        <input
          v-if="renaming"
          ref="renameInput"
          v-model="renameValue"
          @blur="saveRename"
          @keydown.enter="saveRename"
          @keydown.escape="renaming = false"
          class="run-rename-input"
        />
        <h2
          v-else
          class="run-title"
          title="Click to rename"
          @click="startRename"
        >{{ run.client_name }}</h2>
      </div>
    </div>

    <!-- Tabs -->
    <div class="run-tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="run-tab-btn"
        :class="{ active: activeTab === tab.id }"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab content -->
    <div class="pt-6 mb-6">
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

  <div v-else-if="loading" style="font-size:14px;color:var(--app-text-sec)">Loading…</div>
  <div v-else style="font-size:14px;color:#ff3b30">Run not found.</div>
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
  const tabParam = route.query.tab as string | undefined
  if (tabParam && tabs.some(t => t.id === tabParam)) {
    activeTab.value = tabParam
  } else if (run.value?.performance_result) {
    activeTab.value = 'performance'
  } else if (run.value?.capacity_result) {
    activeTab.value = 'capacity'
  } else if (run.value?.quality_result || run.value?.orders_validation_result) {
    activeTab.value = 'quality'
  }
})
</script>

<style scoped>
.run-back-link {
  font-size: 14px;
  letter-spacing: -0.224px;
  color: #0066cc;
  text-decoration: none;
  transition: text-decoration 0.1s;
}
.run-back-link:hover { text-decoration: underline; }

.run-title {
  font-family: "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 21px;
  font-weight: 700;
  color: #1d1d1f;
  line-height: 1.19;
  letter-spacing: 0.231px;
  cursor: pointer;
  transition: color 0.15s;
}
.run-title:hover { color: #0071e3; }

.run-rename-input {
  font-size: 21px;
  font-weight: 700;
  color: #1d1d1f;
  border: none;
  border-bottom: 2px solid #0071e3;
  outline: none;
  background: transparent;
  width: 320px;
  line-height: 1.19;
  font-family: "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif;
}

.run-tab-nav {
  display: flex;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  gap: 0;
}

.run-tab-btn {
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 400;
  letter-spacing: -0.224px;
  color: rgba(0, 0, 0, 0.48);
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
  font-family: "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
}

.run-tab-btn:hover { color: #1d1d1f; }

.run-tab-btn.active {
  color: #0071e3;
  border-bottom-color: #0071e3;
  font-weight: 600;
}
</style>
