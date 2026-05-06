<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-5">
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:var(--app-text);line-height:1.14;letter-spacing:-0.28px">
        Analyses
      </h2>
      <button @click="showModal = true" class="btn-apple-primary">
        New analysis
      </button>
    </div>

    <!-- Toolbar: search + filter + sort -->
    <div class="flex flex-wrap gap-2 mb-4">
      <input
        v-model="search"
        type="search"
        placeholder="Search by name…"
        class="input-apple-sm"
        style="width:200px"
      />
      <select v-model="statusFilter" class="input-apple-sm" style="width:auto;cursor:pointer">
        <option value="">All statuses</option>
        <option value="created">Created</option>
        <option value="quality_done">Quality done</option>
        <option value="orders_ingested">Orders ingested</option>
        <option value="capacity_done">Capacity done</option>
        <option value="performance_done">Performance done</option>
      </select>
      <select v-model="sort" class="input-apple-sm" style="width:auto;cursor:pointer">
        <option value="date_desc">Newest first</option>
        <option value="date_asc">Oldest first</option>
        <option value="name_asc">Name A–Z</option>
        <option value="name_desc">Name Z–A</option>
      </select>
    </div>

    <!-- Selection bar -->
    <div v-if="selectedIds.size > 0" class="flex items-center gap-3 mb-3 px-1">
      <!-- select-all / indeterminate checkbox -->
      <div
        @click="toggleSelectAll"
        class="w-4 h-4 rounded flex-shrink-0 flex items-center justify-center cursor-pointer"
        :style="allSelected || someSelected
          ? 'background:#0071e3;border:1.5px solid #0071e3'
          : 'border:1.5px solid var(--app-border);background:var(--app-surface)'"
      >
        <svg v-if="allSelected" viewBox="0 0 10 8" class="w-2.5" fill="none">
          <path d="M1 4l2.5 2.5L9 1" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <svg v-else-if="someSelected" viewBox="0 0 10 2" class="w-2.5" fill="none">
          <path d="M1 1h8" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>

      <span style="font-size:13px;color:var(--app-text-sec)">{{ selectedIds.size }} selected</span>
      <div style="flex:1"/>

      <template v-if="!confirmBulkDelete">
        <button
          @click="confirmBulkDelete = true"
          style="font-size:13px;font-weight:500;color:#ff3b30;background:none;border:none;cursor:pointer;padding:4px 8px"
        >Delete selected</button>
        <button
          @click="clearSelection"
          style="font-size:13px;color:var(--app-text-sec);background:none;border:none;cursor:pointer;padding:4px 8px"
        >Clear</button>
      </template>
      <template v-else>
        <span style="font-size:13px;color:var(--app-text-sec)">
          Delete {{ selectedIds.size }} {{ selectedIds.size === 1 ? 'analysis' : 'analyses' }}?
        </span>
        <button
          @click="onDeleteSelected"
          style="font-size:13px;font-weight:600;color:#ff3b30;background:none;border:none;cursor:pointer;padding:4px 8px"
        >Yes, delete</button>
        <button
          @click="confirmBulkDelete = false"
          style="font-size:13px;color:var(--app-text-sec);background:none;border:none;cursor:pointer;padding:4px 8px"
        >Cancel</button>
      </template>
    </div>

    <!-- List -->
    <div v-if="runStore.loading" style="font-size:14px;color:var(--app-text-sec)">Loading…</div>
    <div v-else-if="runStore.runs.length === 0" style="font-size:14px;color:var(--app-text-sec)">No analyses found.</div>
    <div v-else class="card-apple-list">
      <div v-for="run in runStore.runs" :key="run.id">
        <div
          class="flex items-center justify-between px-4 py-3 transition-colors"
          style="cursor:default"
          @mouseover="(e) => (e.currentTarget as HTMLElement).style.background='var(--table-row-hover)'"
          @mouseleave="(e) => (e.currentTarget as HTMLElement).style.background=''"
        >
          <!-- Checkbox -->
          <div
            @click.prevent="toggleSelect(run.id)"
            class="w-4 h-4 rounded flex-shrink-0 flex items-center justify-center cursor-pointer mr-3 transition-colors"
            :style="selectedIds.has(run.id)
              ? 'background:#0071e3;border:1.5px solid #0071e3'
              : 'border:1.5px solid var(--app-border);background:var(--app-surface)'"
          >
            <svg v-if="selectedIds.has(run.id)" viewBox="0 0 10 8" class="w-2.5" fill="none">
              <path d="M1 4l2.5 2.5L9 1" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>

          <!-- Name — clickable -->
          <RouterLink :to="`/runs/${run.id}`" class="flex-1 min-w-0 flex items-center gap-3" style="text-decoration:none">
            <span style="font-size:17px;color:var(--app-text);letter-spacing:-0.374px" class="truncate">{{ run.client_name }}</span>
            <span v-if="run.is_public" title="Public" style="color:#0071e3">
              <svg class="w-3.5 h-3.5 inline" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clip-rule="evenodd"/>
              </svg>
            </span>
          </RouterLink>

          <!-- Actions -->
          <div class="flex items-center gap-2 shrink-0 ml-3">
            <StatusBadge :status="run.status" />
            <span class="shrink-0" style="font-size:12px;color:var(--app-text-sec)">{{ formatDate(run.created_at) }}</span>

            <!-- Notes -->
            <button
              @click.prevent="toggleNotes(run.id)"
              class="p-1.5 rounded transition-colors"
              :style="openNotesId === run.id || run.notes ? 'color:#0071e3' : 'color:var(--app-placeholder)'"
              title="Notes"
            >
              <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
              </svg>
            </button>

            <!-- Toggle public -->
            <button
              @click.prevent="onTogglePublic(run)"
              class="p-1.5 rounded transition-colors"
              :style="run.is_public ? 'color:#0071e3' : 'color:var(--app-placeholder)'"
              :title="run.is_public ? 'Make private' : 'Make public'"
            >
              <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clip-rule="evenodd"/>
              </svg>
            </button>

            <!-- Delete / confirm -->
            <template v-if="confirmDelete === run.id">
              <span class="text-xs mr-1" style="color:var(--app-text-sec)">Delete?</span>
              <button @click.prevent="onDelete(run.id)" class="text-xs font-medium mr-1" style="color:#ff3b30">Yes</button>
              <button @click.prevent="confirmDelete = null" class="text-xs" style="color:var(--app-text-sec)">No</button>
            </template>
            <button
              v-else
              @click.prevent="confirmDelete = run.id"
              class="p-1.5 rounded transition-colors"
              style="color:var(--app-placeholder)"
              @mouseover="(e) => (e.currentTarget as HTMLElement).style.color='#ff3b30'"
              @mouseleave="(e) => (e.currentTarget as HTMLElement).style.color='var(--app-placeholder)'"
              title="Delete"
            >
              <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Notes textarea -->
        <div v-if="openNotesId === run.id" class="px-4 pb-3">
          <textarea
            :value="run.notes ?? ''"
            @input="onNotesInput(run.id, ($event.target as HTMLTextAreaElement).value)"
            placeholder="Add notes about this analysis…"
            rows="2"
            class="input-apple-sm resize-none"
            style="font-size:14px"
          />
        </div>
      </div>
    </div>

    <NewRunModal v-if="showModal" @close="showModal = false" @created="onCreated" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useRunStore } from '@/stores/run'
import { useNotificationsStore } from '@/stores/notifications'
import type { RunListItem } from '@/api/runs'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import NewRunModal from '@/components/analysis/NewRunModal.vue'

const runStore = useRunStore()
const router = useRouter()
const notify = useNotificationsStore()
const showModal = ref(false)
const confirmDelete = ref<string | null>(null)
const selectedIds = ref(new Set<string>())
const confirmBulkDelete = ref(false)
const openNotesId = ref<string | null>(null)
let notesTimer: ReturnType<typeof setTimeout> | null = null

const search = ref('')
const statusFilter = ref('')
const sort = ref('date_desc')

function load() {
  runStore.fetchRuns({
    search: search.value || undefined,
    status_filter: statusFilter.value || undefined,
    sort: sort.value,
  })
}

onMounted(load)
watch([search, statusFilter, sort], load)

const allSelected = computed(() =>
  runStore.runs.length > 0 && runStore.runs.every(r => selectedIds.value.has(r.id))
)

const someSelected = computed(() =>
  !allSelected.value && runStore.runs.some(r => selectedIds.value.has(r.id))
)

function toggleSelect(id: string) {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
  confirmBulkDelete.value = false
}

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value.clear()
  } else {
    runStore.runs.forEach(r => selectedIds.value.add(r.id))
  }
  confirmBulkDelete.value = false
}

function clearSelection() {
  selectedIds.value.clear()
  confirmBulkDelete.value = false
}

function onCreated(id: string) {
  showModal.value = false
  router.push(`/runs/${id}`)
}

async function onDelete(id: string) {
  try {
    await runStore.deleteRun(id)
    confirmDelete.value = null
    selectedIds.value.delete(id)
    notify.push({ type: 'success', title: 'Analysis deleted' })
  } catch {
    notify.push({ type: 'error', title: 'Failed to delete analysis' })
  }
}

async function onDeleteSelected() {
  const ids = [...selectedIds.value]
  try {
    await Promise.all(ids.map(id => runStore.deleteRun(id)))
    selectedIds.value.clear()
    confirmBulkDelete.value = false
    notify.push({ type: 'success', title: `${ids.length} ${ids.length === 1 ? 'analysis' : 'analyses'} deleted` })
  } catch {
    confirmBulkDelete.value = false
    notify.push({ type: 'error', title: 'Failed to delete some analyses' })
  }
}

function toggleNotes(id: string) {
  openNotesId.value = openNotesId.value === id ? null : id
}

function onNotesInput(id: string, value: string) {
  if (notesTimer) clearTimeout(notesTimer)
  notesTimer = setTimeout(async () => {
    await runStore.patchRun(id, { notes: value })
  }, 500)
}

async function onTogglePublic(run: RunListItem) {
  await runStore.patchRun(run.id, { is_public: !run.is_public })
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
