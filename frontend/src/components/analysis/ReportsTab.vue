<template>
  <div class="space-y-4">
    <!-- Source files reference -->
    <div v-if="run.masterdata_original_filename || run.orders_original_filename" class="card-apple">
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Source files</h3>
      <div class="space-y-1">
        <p v-if="run.masterdata_original_filename" class="text-xs" style="color:var(--app-text-sec)">
          Masterdata: <code>{{ run.masterdata_original_filename }}</code>
        </p>
        <p v-if="run.orders_original_filename" class="text-xs" style="color:var(--app-text-sec)">
          Orders: <code>{{ run.orders_original_filename }}</code>
        </p>
      </div>
    </div>

    <!-- Main downloads (ZIP + PDF + Excel) -->
    <div class="card-apple">
      <h3 class="mb-4" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Download full reports</h3>
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
          :disabled="!canDownloadPdf || downloadingPdf"
          class="btn-apple-dark"
          :style="(!canDownloadPdf || downloadingPdf) ? 'opacity:0.4' : ''"
        >
          {{ downloadingPdf ? 'Preparing…' : 'Download PDF' }}
        </button>
        <button
          @click="downloadXlsx"
          :disabled="!canDownloadXlsx || downloadingXlsx"
          class="btn-apple-dark"
          :style="(!canDownloadXlsx || downloadingXlsx) ? 'opacity:0.4' : ''"
        >
          {{ downloadingXlsx ? 'Preparing…' : 'Download Excel' }}
        </button>
      </div>
      <p v-if="!run.capacity_result" class="mt-3" style="font-size:12px;color:var(--app-text-sec)">
        ZIP requires capacity results. PDF works with capacity, performance, or both. Excel covers data quality.
      </p>
      <p v-if="error" class="mt-3" style="font-size:14px;color:#ff3b30">{{ error }}</p>
    </div>

    <!-- Masterdata Issues -->
    <div class="card-apple">
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Masterdata Issues</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <button
          v-for="rep in masterdataReports"
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
      <p v-if="!run.quality_result" class="mt-3" style="font-size:12px;color:var(--app-text-sec)">
        Run quality check on Masterdata first to enable these reports.
      </p>
    </div>

    <!-- Orders Issues -->
    <div class="card-apple">
      <h3 class="mb-1" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Orders Issues</h3>
      <p class="mb-3" style="font-size:12px;color:var(--app-text-sec)">
        Date gaps, missing/invalid quantities, and SKU cross-validation against Masterdata.
        Full lists are available in the Excel export above.
      </p>
      <div v-if="ovr" class="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
        <div>
          <span class="text-xs" style="color:var(--app-text-sec)">Date gaps</span>
          <p class="font-semibold" style="color:var(--app-text)">{{ ovr.gap_count }}</p>
        </div>
        <div>
          <span class="text-xs" style="color:var(--app-text-sec)">Missing SKUs</span>
          <p class="font-semibold" :style="ovr.missing_sku_count > 0 ? 'color:#ff3b30' : 'color:var(--app-text)'">{{ ovr.missing_sku_count }}</p>
        </div>
        <div>
          <span class="text-xs" style="color:var(--app-text-sec)">Qty anomalies</span>
          <p class="font-semibold" style="color:var(--app-text)">{{ qtyAnomalies }}</p>
        </div>
        <div>
          <span class="text-xs" style="color:var(--app-text-sec)">Unknown SKUs</span>
          <p class="font-semibold" style="color:var(--app-text)">{{ ovr.orders_skus_not_in_masterdata_count }}</p>
        </div>
        <div>
          <span class="text-xs" style="color:var(--app-text-sec)">Inactive SKUs</span>
          <p class="font-semibold" style="color:var(--app-text)">{{ ovr.masterdata_skus_not_in_orders_count }}</p>
        </div>
      </div>
      <p v-else class="mt-2" style="font-size:12px;color:var(--app-text-sec)">
        Ingest Orders first to enable order-level data quality reporting.
      </p>
    </div>

    <!-- Capacity & Performance CSV -->
    <div class="card-apple">
      <h3 class="mb-3" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Analysis CSV reports</h3>
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
        <button
          @click="downloadCsv('Pareto_Bands')"
          :disabled="!run.performance_result || downloading === 'Pareto_Bands'"
          class="btn-apple-pill text-left"
          style="justify-content:flex-start"
          :style="(!run.performance_result || downloading === 'Pareto_Bands') ? 'opacity:0.4' : ''"
        >
          {{ downloading === 'Pareto_Bands' ? 'Preparing…' : 'Pareto Bands' }}
        </button>
      </div>
      <p v-if="!run.capacity_result && !run.performance_result" class="mt-3" style="font-size:12px;color:var(--app-text-sec)">
        Run capacity or performance analysis to enable these exports.
      </p>
    </div>

    <!-- Solution Design -->
    <div class="card-apple">
      <h3 class="mb-1" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Solution Design</h3>
      <p class="mb-3" style="font-size:12px;color:var(--app-text-sec)">
        Input values for SolDimTool v2.7.3 Dashboard.
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
      <p v-if="!run.performance_result" class="mt-3" style="font-size:12px;color:var(--app-text-sec)">
        Run performance analysis first to enable this report.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RunDetail, OrdersValidationResult } from '@/api/runs'
import { runsApi } from '@/api/runs'

const props = defineProps<{ run: RunDetail }>()

const downloadingZip = ref(false)
const downloadingPdf = ref(false)
const downloadingXlsx = ref(false)
const downloading = ref<string | null>(null)
const error = ref('')

const masterdataReports = [
  { name: 'DQ_Summary', label: 'DQ Summary' },
  { name: 'DQ_MissingCritical', label: 'Missing Critical' },
  { name: 'DQ_SuspectOutliers', label: 'Suspect Outliers' },
  { name: 'DQ_HighRiskBorderline', label: 'High Risk Borderline' },
  { name: 'DQ_Duplicates', label: 'Duplicates' },
  { name: 'DQ_Conflicts', label: 'Conflicts' },
]

const ovr = computed(() => props.run.orders_validation_result as OrdersValidationResult | null)

const qtyAnomalies = computed(() => {
  const o = ovr.value
  if (!o) return 0
  return o.qty_null_count + o.qty_zero_count + o.qty_negative_count + o.qty_outlier_count
})

const canDownloadPdf = computed(
  () => !!(props.run.capacity_result || props.run.performance_result),
)

const canDownloadXlsx = computed(
  () => !!(props.run.quality_result || props.run.orders_validation_result),
)

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

async function downloadXlsx() {
  downloadingXlsx.value = true
  error.value = ''
  try {
    const { data } = await runsApi.downloadDqXlsx(props.run.id)
    triggerDownload(data as Blob, `${props.run.client_name}_data_quality.xlsx`)
  } catch (e) {
    error.value = 'Excel download failed: ' + await blobErrorMessage(e)
  } finally {
    downloadingXlsx.value = false
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
