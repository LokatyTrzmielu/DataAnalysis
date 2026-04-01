<template>
  <!-- Backdrop -->
  <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="emit('close')">
    <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm">
      <h3 class="text-base font-semibold text-gray-800 mb-4">New analysis</h3>

      <label class="block text-sm font-medium text-gray-700 mb-1">Client name</label>
      <input
        v-model="clientName"
        type="text"
        placeholder="e.g. Acme Warehouse 2026"
        class="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
        @keydown.enter="create"
      />

      <p v-if="error" class="text-red-600 text-sm mb-3">{{ error }}</p>

      <div class="flex gap-2 justify-end">
        <button @click="emit('close')" class="text-sm text-gray-500 hover:text-gray-700 px-3 py-2">
          Cancel
        </button>
        <button
          @click="create"
          :disabled="!clientName.trim() || loading"
          class="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
        >
          {{ loading ? 'Creating…' : 'Create' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRunStore } from '@/stores/run'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'created', id: string): void
}>()

const runStore = useRunStore()
const clientName = ref('')
const loading = ref(false)
const error = ref('')

async function create() {
  if (!clientName.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    const run = await runStore.createRun(clientName.value.trim())
    emit('created', run.id)
  } catch {
    error.value = 'Failed to create analysis.'
  } finally {
    loading.value = false
  }
}
</script>
