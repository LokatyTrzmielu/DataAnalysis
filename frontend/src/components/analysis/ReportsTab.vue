<template>
  <div class="space-y-4">
    <div class="bg-white border border-gray-200 rounded-lg p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-4">Download reports</h3>

      <div class="flex gap-3 flex-wrap">
        <button
          @click="downloadZip"
          :disabled="!run.capacity_result || downloading"
          class="bg-gray-700 hover:bg-gray-800 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
        >
          {{ downloading ? 'Preparing…' : 'Download ZIP' }}
        </button>
      </div>

      <p v-if="!run.capacity_result" class="text-xs text-gray-400 mt-3">
        Run capacity analysis first to enable report download.
      </p>
      <p v-if="error" class="text-red-600 text-sm mt-3">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { RunDetail } from '@/api/runs'
import { runsApi } from '@/api/runs'

const props = defineProps<{ run: RunDetail }>()

const downloading = ref(false)
const error = ref('')

async function downloadZip() {
  downloading.value = true
  error.value = ''
  try {
    const { data } = await runsApi.downloadZip(props.run.id)
    const url = URL.createObjectURL(data as Blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${props.run.client_name}_report.zip`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    error.value = 'Download failed.'
  } finally {
    downloading.value = false
  }
}
</script>
