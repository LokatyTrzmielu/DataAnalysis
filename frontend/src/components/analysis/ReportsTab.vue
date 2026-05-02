<template>
  <div class="space-y-4">
    <!-- Main downloads (ZIP + PDF) -->
    <div class="card-apple">
      <h3 class="mb-4" style="font-size:14px;font-weight:600;color:#1d1d1f;letter-spacing:-0.224px">Download full reports</h3>
      <div class="flex gap-3 flex-wrap">
        <button
          @click="downloadZip"
          :disabled="!run.capacity_result || downloadingZip"
          class="btn-apple-dark"
          style="opacity:1"
          :style="(!run.capacity_result || downloadingZip) ? 'opacity:0.4' : ''"
        >
          {{ downloadingZip ? 'Preparing…' : 'Download ZIP' }}
        </button>
        <button
          @click="downloadPdf"
          :disabled="!run.capacity_result || downloadingPdf"
          class="btn-apple-dark"
          :style="(!run.capacity_result || downloadingPdf) ? 'opacity:0.4' : ''"
        >
          {{ downloadingPdf ? 'Preparing…' : 'Download PDF' }}
        </button>
      </div>
      <p v-if="!run.capacity_result" class="mt-3" style="font-size:12px;color:rgba(0,0,0,0.48)">
        Run capacity analysis first to enable report download.
      </p>
      <p v-if="error" class="mt-3" style="font-size:14px;color:#ff3b30">{{ error }}</p>
    </div>

    <!-- DQ CSV reports -->
    <div class="card-apple">
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:#1d1d1f;letter-spacing:-0.224px">Data Quality CSV reports</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <button
          v-for="rep in dqReports"
          :key="rep.name"
          @click="downloadCsv(rep.name)"
          :disabled="!run.quality_result || downloading === rep.name"
          class="btn-apple-pill text-left"
          style="justify-content:flex-start"
          :style="(!run.quality_result || downloading === rep.name) ? 'opacity:0.4' : ''"
        >
          {{ downloading === rep.name ? 'Preparing…' : rep.label }}
        </button>
      </div>
      <p v-if="!run.quality_result" class="mt-3" style="font-size:12px;color:rgba(0,0,0,0.48)">
        Run quality check first to enable DQ reports.
      </p>
    </div>

    <!-- Capacity & Performance CSV -->
    <div class="card-apple">
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:#1d1d1f;letter-spacing:-0.224px">Analysis CSV reports</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <button
          @click="downloadCsv('Capacity_Results')"
          :disabled="!run.capacity_result || downloading === 'Capacity_Results'"
          class="btn-apple-pill text-left"
          style="justify-content:flex-start"
          :style="(!run.capacity_result || downloading === 'Capacity_Results') ? 'opacity:0.4' : ''"
        >
          {{ downloading === 'Capacity_Results' ? 'Preparing…' : 'Capacity Results' }}
        </button>
        <button
          @click="downloadCsv('SKU_Pareto')"
          :disabled="!run.performance_result || downloading === 'SKU_Pareto'"
          class="btn-apple-pill text-left"
          style="justify-content:flex-start"
          :style="(!run.performance_result || downloading === 'SKU_Pareto') ? 'opacity:0.4' : ''"
        >
          {{ downloading === 'SKU_Pareto' ? 'Preparing…' : 'SKU Pareto' }}
        </button>
      </div>
      <p v-if="!run.capacity_result && !run.performance_result" class="mt-3" style="font-size:12px;color:rgba(0,0,0,0.48)">
        Run capacity or performance analysis to enable these exports.
      </p>
    </div>

    <!-- Solution Design -->
    <div class="card-apple">
      <h3 class="mb-1" style="font-size:14px;font-weight:600;color:#1d1d1f;letter-spacing:-0.224px">Solution Design</h3>
      <p class="mb-3" style="font-size:12px;color:rgba(0,0,0,0.48)">
        Input values for SolDimTool v2.7.3 Dashboard (cells C16, C17, B21–B25, C21–C25, A29, A31, C29).
      </p>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <button
          @click="downloadCsv('SolDimTool_DashboardInput')"
          :disabled="!run.performance_result || downloading === 'SolDimTool_DashboardInput'"
          class="btn-apple-pill text-left"
          style="justify-content:flex-start"
          :style="(!run.performance_result || downloading === 'SolDimTool_DashboardInput') ? 'opacity:0.4' : ''"
        >
          {{ downloading === 'SolDimTool_DashboardInput' ? 'Preparing…' : 'SolDimTool Dashboard Input' }}
        </button>
      </div>
      <p v-if="!run.performance_result" class="mt-3" style="font-size:12px;color:rgba(0,0,0,0.48)">
        Run performance analysis first to enable this report.
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

async function blobErrorMessage(err: unknown): Promise<string> {
  try {
    const e = err as { response?: { data?: Blob; status?: number } }
    if (e?.response?.data instanceof Blob) {
      const text = await e.response.data.text()
      const parsed = JSON.parse(text)
      return parsed?.detail ?? text
    }
    return (e?.response?.status ? `HTTP ${e.response.status}` : String(err))
  } catch {
    return String(err)
  }
}

async function downloadZip() {
  downloadingZip.value = true
  error.value = ''
  try {
    const { data } = await runsApi.downloadZip(props.run.id)
    triggerDownload(data as Blob, `${props.run.client_name}_report.zip`)
  } catch (e) {
    error.value = 'ZIP download failed: ' + await blobErrorMessage(e)
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
  } catch (e) {
    error.value = 'PDF download failed: ' + await blobErrorMessage(e)
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
  } catch (e) {
    error.value = `Failed to download ${reportName}: ` + await blobErrorMessage(e)
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
