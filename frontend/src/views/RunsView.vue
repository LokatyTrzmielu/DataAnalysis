<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-800">Analyses</h2>
      <button
        @click="showModal = true"
        class="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
      >
        New analysis
      </button>
    </div>

    <!-- Toolbar: search + filter + sort -->
    <div class="flex flex-wrap gap-2 mb-4">
      <input
        v-model="search"
        type="search"
        placeholder="Search by name…"
        class="border border-gray-300 rounded px-3 py-1.5 text-sm w-52 focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
      <select v-model="statusFilter" class="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
        <option value="">All statuses</option>
        <option value="created">Created</option>
        <option value="quality_done">Quality done</option>
        <option value="orders_ingested">Orders ingested</option>
        <option value="capacity_done">Capacity done</option>
        <option value="performance_done">Performance done</option>
      </select>
      <select v-model="sort" class="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
        <option value="date_desc">Newest first</option>
        <option value="date_asc">Oldest first</option>
        <option value="name_asc">Name A–Z</option>
        <option value="name_desc">Name Z–A</option>
      </select>
    </div>

    <!-- List -->
    <div v-if="runStore.loading" class="text-sm text-gray-400">Loading…</div>
    <div v-else-if="runStore.runs.length === 0" class="text-sm text-gray-400">No analyses found.</div>
    <div v-else class="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
      <div
        v-for="run in runStore.runs"
        :key="run.id"
        class="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors group"
      >
        <!-- Name + date — clickable -->
        <RouterLink :to="`/runs/${run.id}`" class="flex-1 min-w-0 flex items-center gap-3">
          <span class="text-sm font-medium text-gray-800 truncate">{{ run.client_name }}</span>
          <span class="text-xs text-gray-400 shrink-0">{{ formatDate(run.created_at) }}</span>
          <span v-if="run.is_public" title="Public" class="text-xs text-blue-500">
            <svg class="w-3.5 h-3.5 inline" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clip-rule="evenodd"/>
            </svg>
          </span>
        </RouterLink>

        <!-- Actions -->
        <div class="flex items-center gap-1 shrink-0 ml-3">
          <StatusBadge :status="run.status" />

          <!-- Duplicate -->
          <button
            @click.prevent="onDuplicate(run.id)"
            class="p-1.5 rounded text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            title="Duplicate"
          >
            <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path d="M7 9a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2H9a2 2 0 01-2-2V9z"/>
              <path d="M5 3a2 2 0 00-2 2v6a2 2 0 002 2V5h8a2 2 0 00-2-2H5z"/>
            </svg>
          </button>

          <!-- Toggle public -->
          <button
            @click.prevent="onTogglePublic(run)"
            class="p-1.5 rounded transition-colors"
            :class="run.is_public ? 'text-blue-500 hover:bg-blue-50' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'"
            :title="run.is_public ? 'Make private' : 'Make public'"
          >
            <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clip-rule="evenodd"/>
            </svg>
          </button>

          <!-- Delete / confirm -->
          <template v-if="confirmDelete === run.id">
            <span class="text-xs text-gray-500 mr-1">Delete?</span>
            <button @click.prevent="onDelete(run.id)" class="text-xs text-red-600 font-medium hover:text-red-800 mr-1">Yes</button>
            <button @click.prevent="confirmDelete = null" class="text-xs text-gray-500 hover:text-gray-700">No</button>
          </template>
          <button
            v-else
            @click.prevent="confirmDelete = run.id"
            class="p-1.5 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
            title="Delete"
          >
            <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <NewRunModal v-if="showModal" @close="showModal = false" @created="onCreated" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useRunStore } from '@/stores/run'
import type { RunListItem } from '@/api/runs'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import NewRunModal from '@/components/analysis/NewRunModal.vue'

const runStore = useRunStore()
const router = useRouter()
const showModal = ref(false)
const confirmDelete = ref<string | null>(null)

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

function onCreated(id: string) {
  showModal.value = false
  router.push(`/runs/${id}`)
}

async function onDelete(id: string) {
  await runStore.deleteRun(id)
  confirmDelete.value = null
}

async function onDuplicate(id: string) {
  const run = await runStore.duplicateRun(id)
  router.push(`/runs/${run.id}`)
}

async function onTogglePublic(run: RunListItem) {
  await runStore.patchRun(run.id, { is_public: !run.is_public })
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
