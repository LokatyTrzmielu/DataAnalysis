<template>
  <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
      <div class="flex items-center justify-between mb-5">
        <h3 class="text-base font-semibold text-gray-800">Share analysis</h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
          <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>

      <!-- Add share -->
      <form @submit.prevent="addShare" class="flex gap-2 mb-5">
        <input
          v-model="emailInput"
          type="email"
          placeholder="User email…"
          class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <button
          type="submit"
          :disabled="adding"
          class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors disabled:opacity-50"
        >
          Share
        </button>
      </form>
      <p v-if="addError" class="text-sm text-red-600 mb-3">{{ addError }}</p>

      <!-- Current shares -->
      <div v-if="loading" class="text-sm text-gray-400">Loading…</div>
      <div v-else-if="shares.length === 0" class="text-sm text-gray-400">Not shared with anyone yet.</div>
      <ul v-else class="divide-y divide-gray-100">
        <li v-for="s in shares" :key="s.user_id" class="flex items-center justify-between py-2">
          <div>
            <span class="text-sm font-medium text-gray-800">{{ s.name }}</span>
            <span class="ml-2 text-xs text-gray-400">{{ s.email }}</span>
          </div>
          <button
            @click="revoke(s.user_id)"
            class="text-xs text-red-500 hover:text-red-700"
          >Revoke</button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { runsApi, type RunShareItem } from '@/api/runs'

const props = defineProps<{ runId: string }>()
defineEmits<{ close: [] }>()

const shares = ref<RunShareItem[]>([])
const loading = ref(true)
const emailInput = ref('')
const adding = ref(false)
const addError = ref('')

onMounted(async () => {
  try {
    const { data } = await runsApi.getShares(props.runId)
    shares.value = data
  } finally {
    loading.value = false
  }
})

async function addShare() {
  addError.value = ''
  adding.value = true
  try {
    const { data } = await runsApi.addShare(props.runId, emailInput.value)
    shares.value.push(data)
    emailInput.value = ''
  } catch (e: any) {
    addError.value = e?.response?.data?.detail ?? 'Failed to share.'
  } finally {
    adding.value = false
  }
}

async function revoke(userId: string) {
  await runsApi.removeShare(props.runId, userId)
  shares.value = shares.value.filter(s => s.user_id !== userId)
}
</script>
