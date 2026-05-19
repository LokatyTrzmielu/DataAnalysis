<template>
  <aside
    :class="['dashboard-sidebar', { 'is-collapsed': collapsed }]"
    :style="{ width: collapsed ? '72px' : '264px' }"
  >
    <!-- Header: New Analysis + collapse toggle -->
    <div class="sidebar-header">
      <button
        v-if="!collapsed"
        @click="showModal = true"
        class="btn-apple-primary"
        style="width:100%;justify-content:center;font-size:14px;padding:9px 12px"
      >
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"/>
        </svg>
        <span>New Analysis</span>
      </button>
      <button
        v-else
        @click="showModal = true"
        class="sidebar-icon-btn sidebar-new-icon"
        title="New Analysis"
        aria-label="New Analysis"
      >
        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"/>
        </svg>
      </button>

      <div class="sidebar-title-row">
        <span v-if="!collapsed" class="sidebar-title">Recent</span>
        <button
          @click="collapsed = !collapsed"
          class="sidebar-icon-btn sidebar-collapse-btn"
          :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        >
          <svg v-if="collapsed" width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 4l6 6-6 6"/>
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M13 4l-6 6 6 6"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- List -->
    <div v-if="runStore.loading && runStore.runs.length === 0" class="sidebar-empty">
      {{ collapsed ? '…' : 'Loading…' }}
    </div>
    <div v-else-if="runStore.runs.length === 0" class="sidebar-empty">
      <template v-if="!collapsed">No analyses yet. Create one above.</template>
    </div>

    <!-- Expanded list -->
    <div v-else-if="!collapsed" class="card-apple-list sidebar-list">
      <div v-for="run in runStore.runs.slice(0, 20)" :key="run.id">
        <div
          :class="['flex items-center justify-between px-3 py-2.5 transition-colors cursor-pointer', selectedId === run.id ? 'is-selected' : 'sidebar-row-hover']"
          @click="emit('select', run.id)"
          @dblclick="onOpenRun(run)"
        >
          <div class="flex-1 min-w-0 text-left">
            <div style="font-size:13px;color:var(--app-text);letter-spacing:-0.08px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:500">
              {{ run.client_name }}
            </div>
            <div class="flex items-center gap-2 mt-0.5">
              <StatusBadge :status="run.status" />
              <span style="font-size:11px;color:var(--app-text-sec)">{{ formatDate(run.created_at) }}</span>
            </div>
          </div>
          <button
            @click.stop="toggleNotes(run.id)"
            class="p-1 rounded transition-colors ml-1 flex-shrink-0"
            :style="openNotesId === run.id || run.notes ? 'color:#0071e3' : 'color:var(--app-placeholder)'"
            title="Notes"
            aria-label="Toggle notes"
          >
            <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
            </svg>
          </button>
        </div>
        <div v-if="openNotesId === run.id" class="px-3 pb-2">
          <textarea
            :value="run.notes ?? ''"
            @input="onNotesInput(run.id, ($event.target as HTMLTextAreaElement).value)"
            placeholder="Add notes about this analysis…"
            rows="2"
            class="input-apple-sm resize-none"
            style="font-size:13px"
          />
        </div>
      </div>
    </div>

    <!-- Collapsed rail -->
    <div v-else class="sidebar-rail">
      <button
        v-for="run in runStore.runs.slice(0, 20)"
        :key="run.id"
        @click="emit('select', run.id)"
        @dblclick="onOpenRun(run)"
        :class="['sidebar-avatar', { 'is-selected': selectedId === run.id }]"
        :title="`${run.client_name} · ${formatDate(run.created_at)}`"
        :aria-label="run.client_name"
      >
        {{ initial(run.client_name) }}
      </button>
    </div>

    <NewRunModal v-if="showModal" @close="showModal = false" @created="onCreated" />
  </aside>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRunStore } from '@/stores/run'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import NewRunModal from '@/components/analysis/NewRunModal.vue'
import type { RunListItem } from '@/api/runs'

defineProps<{ selectedId: string | null }>()
const emit = defineEmits<{
  (e: 'select', id: string): void
  (e: 'created', id: string): void
  (e: 'open', id: string, tab: string): void
}>()

const runStore = useRunStore()
const STORAGE_KEY = 'dashboard.sidebar.collapsed'
const SIDEBAR_W_EXPANDED = '264px'
const SIDEBAR_W_COLLAPSED = '72px'
const collapsed = ref<boolean>(typeof window !== 'undefined' && localStorage.getItem(STORAGE_KEY) === 'true')

function syncWidthVar() {
  if (typeof document === 'undefined') return
  document.documentElement.style.setProperty(
    '--app-sidebar-w',
    collapsed.value ? SIDEBAR_W_COLLAPSED : SIDEBAR_W_EXPANDED,
  )
}
watch(collapsed, v => {
  try { localStorage.setItem(STORAGE_KEY, String(v)) } catch { /* ignore */ }
  syncWidthVar()
})
onMounted(syncWidthVar)
onBeforeUnmount(() => {
  if (typeof document !== 'undefined') {
    document.documentElement.style.removeProperty('--app-sidebar-w')
  }
})

const showModal = ref(false)
const openNotesId = ref<string | null>(null)
let notesTimer: ReturnType<typeof setTimeout> | null = null

function toggleNotes(id: string) {
  openNotesId.value = openNotesId.value === id ? null : id
}

function onNotesInput(id: string, value: string) {
  if (notesTimer) clearTimeout(notesTimer)
  notesTimer = setTimeout(async () => {
    await runStore.patchRun(id, { notes: value })
  }, 500)
}

function onCreated(id: string) {
  showModal.value = false
  emit('created', id)
}

function tabFromStatus(status: string): string {
  if (status === 'performance_done' || status === 'orders_ingested') return 'performance'
  if (status === 'capacity_done') return 'capacity'
  if (status === 'quality_done') return 'quality'
  return 'import'
}

function onOpenRun(run: RunListItem) {
  emit('open', run.id, tabFromStatus(run.status))
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function initial(name: string): string {
  const trimmed = name.trim()
  return trimmed.length ? trimmed[0]!.toUpperCase() : '?'
}
</script>

<style scoped>
.dashboard-sidebar {
  position: fixed;
  left: 0;
  top: 48px;
  height: calc(100vh - 48px);
  z-index: 50;
  background: var(--app-surface);
  border-right: 1px solid var(--app-border);
  box-shadow: rgba(0, 0, 0, 0.04) 1px 0 3px;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
  transition: width 0.25s ease;
}

.sidebar-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}

.sidebar-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
  min-height: 22px;
}

.sidebar-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: var(--app-text-sec);
}

.sidebar-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 6px;
  color: var(--app-text-sec);
  transition: background 0.15s, color 0.15s;
  padding: 0;
}
.sidebar-icon-btn:hover {
  background: var(--table-row-hover);
  color: var(--app-text);
}

.sidebar-new-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  margin: 0 auto;
  background: #0071e3;
  color: #fff;
}
.sidebar-new-icon:hover {
  background: #0077ed;
  color: #fff;
}

.sidebar-collapse-btn {
  margin-left: auto;
}
.is-collapsed .sidebar-collapse-btn {
  margin: 0 auto;
}

.sidebar-empty {
  font-size: 13px;
  color: var(--app-text-sec);
  padding: 4px 8px;
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
}

.sidebar-row-hover:hover {
  background: var(--table-row-hover);
}
.is-selected {
  background: rgba(0, 113, 227, 0.08);
}
.is-selected:hover {
  background: rgba(0, 113, 227, 0.12);
}

.sidebar-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
  padding: 6px 0;
}

.sidebar-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: -0.2px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--app-border);
  color: var(--app-text);
  transition: background 0.15s ease, color 0.15s ease;
}
.sidebar-avatar:hover {
  background: var(--app-text-sec);
  color: var(--app-surface);
}
.sidebar-avatar.is-selected {
  background: #0071e3;
  color: #fff;
}
.sidebar-avatar.is-selected:hover {
  background: #0077ed;
  color: #fff;
}
</style>
