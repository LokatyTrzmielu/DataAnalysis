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
          {{ downloadingZip ? 'Preparing…' : 'Download ZIP' }}
        </button>
        <button
          @click="downloadPdf"
          :disabled="!run.capacity_result || downloadingPdf"
          class="bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
        >
          {{ downloadingPdf ? 'Preparing…' : 'Download PDF' }}
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

const downloadingZip = ref(false)
const downloadingPdf = ref(false)
const downloading = downloadingZip  // alias for template backward compat
const error = ref('')

async function downloadZip() {
  downloadingZip.value = true
  error.value = ''
  try {
    const { data } = await runsApi.downloadZip(props.run.id)
    triggerDownload(data as Blob, `${props.run.client_name}_report.zip`)
  } catch {
    error.value = 'ZIP download failed.'
  } finally {
    downloadingZip.value = false
  }
}

async function downloadPdf() {
  downloadingPdf.value = true
  error.value = ''
  try {
    const { data } = await runsApi.downloadPdf(props.run.id)
    triggerDownload(data as Blob, `${props.run.client_name}_report.pdf`)
  } catch {
    error.value = 'PDF download failed.'
  } finally {
    downloadingPdf.value = false
  }
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>
