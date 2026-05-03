<template>
  <div class="fixed inset-0 flex items-center justify-center z-50" style="background:rgba(0,0,0,0.6)" @click.self="emit('close')">
    <div class="card-apple-elevated w-full" style="max-width:360px">
      <h3 style="font-size:21px;font-weight:700;color:var(--app-text);letter-spacing:0.231px;line-height:1.19;margin-bottom:20px">New analysis</h3>

      <label class="label-apple">Client name</label>
      <input
        v-model="clientName"
        type="text"
        placeholder="e.g. Acme Warehouse 2026"
        class="input-apple mb-4"
        @keydown.enter="create"
      />

      <p v-if="error" class="mb-3" style="font-size:14px;color:#ff3b30">{{ error }}</p>

      <div class="flex gap-2 justify-end">
        <button @click="emit('close')" style="font-size:14px;color:var(--app-text-sec);background:none;border:none;cursor:pointer;padding:8px 12px;letter-spacing:-0.224px" class="hover:text-[#1d1d1f] transition-colors">
          Cancel
        </button>
        <button
          @click="create"
          :disabled="!clientName.trim() || loading"
          class="btn-apple-primary"
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
