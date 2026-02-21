<template>
  <div>
    <div class="mb-6">
      <h2 class="text-lg font-semibold text-gray-800">Welcome, {{ auth.user?.name }}</h2>
      <p class="text-sm text-gray-500 mt-1">Warehouse capacity & performance analytics</p>
    </div>

    <!-- Quick actions -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      <button
        @click="newAnalysis"
        class="bg-blue-600 hover:bg-blue-700 text-white rounded-lg p-4 text-left transition-colors"
      >
        <div class="font-medium text-sm">New Analysis</div>
        <div class="text-xs opacity-80 mt-1">Start capacity / quality run</div>
      </button>
      <RouterLink
        to="/runs"
        class="bg-white border border-gray-200 hover:border-blue-400 rounded-lg p-4 text-left transition-colors block"
      >
        <div class="font-medium text-sm text-gray-800">History</div>
        <div class="text-xs text-gray-500 mt-1">Browse past analyses</div>
      </RouterLink>
      <RouterLink
        to="/carriers"
        class="bg-white border border-gray-200 hover:border-blue-400 rounded-lg p-4 text-left transition-colors block"
      >
        <div class="font-medium text-sm text-gray-800">Carriers</div>
        <div class="text-xs text-gray-500 mt-1">Manage carrier configs</div>
      </RouterLink>
    </div>

    <!-- Recent runs -->
    <div>
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Recent analyses</h3>
      <div v-if="runStore.loading" class="text-sm text-gray-400">Loading…</div>
      <div v-else-if="runStore.runs.length === 0" class="text-sm text-gray-400">
        No analyses yet. Create one above.
      </div>
      <div v-else class="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
        <RouterLink
          v-for="run in runStore.runs.slice(0, 5)"
          :key="run.id"
          :to="`/runs/${run.id}`"
          class="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
        >
          <div>
            <span class="text-sm font-medium text-gray-800">{{ run.client_name }}</span>
            <span class="ml-2 text-xs text-gray-400">{{ formatDate(run.created_at) }}</span>
          </div>
          <StatusBadge :status="run.status" />
        </RouterLink>
      </div>
    </div>

    <!-- New run modal -->
    <NewRunModal v-if="showModal" @close="showModal = false" @created="onCreated" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRunStore } from '@/stores/run'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import NewRunModal from '@/components/analysis/NewRunModal.vue'

const auth = useAuthStore()
const runStore = useRunStore()
const router = useRouter()
const showModal = ref(false)

onMounted(() => runStore.fetchRuns())

function newAnalysis() {
  showModal.value = true
}

function onCreated(id: string) {
  showModal.value = false
  router.push(`/runs/${id}`)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
