<template>
  <div class="space-y-4">
    <!-- Main downloads (ZIP + PDF) -->
    <div class="bg-white border border-gray-200 rounded-lg p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-4">Download full reports</h3>
      <div class="flex gap-3 flex-wrap">
        <button
          @click="downloadZip"
          :disabled="!run.capacity_result || downloadingZip"
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

    <!-- DQ CSV reports -->
    <div class="bg-white border border-gray-200 rounded-lg p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Data Quality CSV reports</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <button
          v-for="rep in dqReports"
          :key="rep.name"
          @click="downloadCsv(rep.name)"
          :disabled="!run.quality_result || downloading === rep.name"
          class="bg-blue-50 hover:bg-blue-100 disabled:opacity-40 text-blue-700 text-xs font-medium px-3 py-2 rounded transition-colors text-left"
        >
          {{ downloading === rep.name ? 'Preparing…' : rep.label }}
        </button>
      </div>
      <p v-if="!run.quality_result" class="text-xs text-gray-400 mt-3">
        Run quality check first to enable DQ reports.
      </p>
    </div>

    <!-- Capacity & Performance CSV -->
    <div class="bg-white border border-gray-200 rounded-lg p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Analysis CSV reports</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <button
          @click="downloadCsv('Capacity_Results')"
          :disabled="!run.capacity_result || downloading === 'Capacity_Results'"
          class="bg-green-50 hover:bg-green-100 disabled:opacity-40 text-green-700 text-xs font-medium px-3 py-2 rounded transition-colors text-left"
        >
          {{ downloading === 'Capacity_Results' ? 'Preparing…' : 'Capacity Results' }}
        </button>
        <button
          @click="downloadCsv('SKU_Pareto')"
          :disabled="!run.performance_result || downloading === 'SKU_Pareto'"
          class="bg-green-50 hover:bg-green-100 disabled:opacity-40 text-green-700 text-xs font-medium px-3 py-2 rounded transition-colors text-left"
        >
          {{ downloading === 'SKU_Pareto' ? 'Preparing…' : 'SKU Pareto' }}
        </button>
      </div>
      <p v-if="!run.capacity_result && !run.performance_result" class="text-xs text-gray-400 mt-3">
        Run capacity or performance analysis to enable these exports.
      </p>
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
const downloading = ref<string | null>(null)
const error = ref('')

const dqReports = [
  { name: 'DQ_Summary', label: 'DQ Summary' },
  { name: 'DQ_MissingCritical', label: 'Missing Critical' },
  { name: 'DQ_SuspectOutliers', label: 'Suspect Outliers' },
  { name: 'DQ_HighRiskBorderline', label: 'High Risk Borderline' },
  { name: 'DQ_Duplicates', label: 'Duplicates' },
  { name: 'DQ_Conflicts', label: 'Conflicts' },
]

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

async function downloadCsv(reportName: string) {
  downloading.value = reportName
  error.value = ''
  try {
    const { data } = await runsApi.downloadCsvReport(props.run.id, reportName)
    triggerDownload(data as Blob, `${props.run.client_name}_${reportName}.csv`)
  } catch {
    error.value = `Failed to download ${reportName}.`
  } finally {
    downloading.value = null
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
