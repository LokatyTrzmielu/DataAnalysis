<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-lg font-semibold text-gray-800">Analyses</h2>
      <button
        @click="showModal = true"
        class="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
      >
        New analysis
      </button>
    </div>

    <div v-if="runStore.loading" class="text-sm text-gray-400">Loading…</div>
    <div v-else-if="runStore.runs.length === 0" class="text-sm text-gray-400">No analyses yet.</div>
    <div v-else class="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
      <RouterLink
        v-for="run in runStore.runs"
        :key="run.id"
        :to="`/runs/${run.id}`"
        class="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
      >
        <div>
          <span class="text-sm font-medium text-gray-800">{{ run.client_name }}</span>
          <span class="ml-3 text-xs text-gray-400">{{ formatDate(run.created_at) }}</span>
        </div>
        <StatusBadge :status="run.status" />
      </RouterLink>
    </div>

    <NewRunModal v-if="showModal" @close="showModal = false" @created="onCreated" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useRunStore } from '@/stores/run'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import NewRunModal from '@/components/analysis/NewRunModal.vue'

const runStore = useRunStore()
const router = useRouter()
const showModal = ref(false)

onMounted(() => runStore.fetchRuns())

function onCreated(id: string) {
  showModal.value = false
  router.push(`/runs/${id}`)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
