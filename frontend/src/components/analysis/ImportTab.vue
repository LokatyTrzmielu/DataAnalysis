<template>
  <div class="space-y-6">
    <div class="bg-white border border-gray-200 rounded-lg p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-4">Upload Masterdata</h3>
      <p class="text-xs text-gray-500 mb-4">
        Upload an Excel (XLSX) or CSV file with product dimensions, weight, and stock data.
      </p>
      <input
        ref="fileInput"
        type="file"
        accept=".xlsx,.xls,.csv"
        class="block text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-600 hover:file:bg-blue-100"
        @change="onFileChange"
      />

      <p v-if="error" class="text-red-600 text-sm mt-3">{{ error }}</p>
      <p v-if="success" class="text-green-600 text-sm mt-3">{{ success }}</p>

      <button
        v-if="selectedFile"
        @click="upload"
        :disabled="uploading"
        class="mt-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
      >
        {{ uploading ? 'Running quality check…' : 'Import & validate' }}
      </button>
    </div>

    <!-- Current file info -->
    <div v-if="props.run.masterdata_path" class="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <p class="text-xs text-gray-500">
        Masterdata file on server: <code class="text-gray-700">{{ fileName }}</code>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RunDetail } from '@/api/runs'
import { runsApi } from '@/api/runs'

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{ (e: 'refreshed'): void }>()

const fileInput = ref<HTMLInputElement>()
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const error = ref('')
const success = ref('')

const fileName = computed(() => {
  if (!props.run.masterdata_path) return ''
  return props.run.masterdata_path.split('/').pop() ?? ''
})

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  error.value = ''
  success.value = ''
}

async function upload() {
  if (!selectedFile.value) return
  uploading.value = true
  error.value = ''
  success.value = ''
  try {
    await runsApi.runQuality(props.run.id, selectedFile.value)
    success.value = 'File imported and validated successfully.'
    emit('refreshed')
  } catch (e: unknown) {
    error.value = (e as Error).message || 'Upload failed.'
  } finally {
    uploading.value = false
  }
}
</script>
