<template>
  <div class="space-y-6">

    <!-- ── Masterdata Section ── -->
    <div class="card-apple">
      <div class="flex items-center justify-between mb-3">
        <h3 style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Masterdata</h3>
        <span v-if="run.quality_result" class="flex items-center gap-1 text-xs font-medium" style="color:#34c759">
          <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          Imported
        </span>
      </div>

      <!-- Done state -->
      <div v-if="run.quality_result && mdStep === 'done'" class="space-y-2">
        <p class="text-xs" style="color:var(--app-text-sec)"><code>{{ mdUploadedFileName || mdFileName }}</code></p>
        <button @click="mdStep = 'upload'" class="text-xs underline" style="color:var(--app-text-sec);background:none;border:none;cursor:pointer;padding:0">Re-upload</button>
      </div>

      <!-- Step: upload -->
      <div v-else-if="mdStep === 'upload'">
        <!-- Mode toggle -->
        <div class="flex gap-1 mb-4 p-0.5 rounded-lg w-fit" style="background:var(--table-header-bg)">
          <button
            @click="mdMode = 'file'"
            class="text-xs px-3 py-1 rounded-md transition-colors"
            :style="mdMode === 'file'
              ? 'background:var(--app-surface);color:var(--app-text);box-shadow:0 1px 2px rgba(0,0,0,0.15);font-weight:500'
              : 'background:transparent;color:var(--app-text-sec)'"
          >Upload file</button>
          <button
            @click="mdMode = 'dataset'; loadMdDatasets()"
            class="text-xs px-3 py-1 rounded-md transition-colors"
            :style="mdMode === 'dataset'
              ? 'background:var(--app-surface);color:var(--app-text);box-shadow:0 1px 2px rgba(0,0,0,0.15);font-weight:500'
              : 'background:transparent;color:var(--app-text-sec)'"
          >From dataset</button>
        </div>

        <!-- File upload mode -->
        <div v-if="mdMode === 'file'">
          <p class="text-xs mb-4" style="color:var(--app-text-sec)">
            Upload an Excel (XLSX) or CSV file with product dimensions, weight, and stock data.
          </p>
          <input ref="mdFileInput" type="file" accept=".xlsx,.xls,.csv" class="hidden" @change="onMdFileChange" />
          <div class="flex items-center gap-2">
            <button @click="mdFileInput?.click()" class="btn-apple-pill" style="font-size:13px">Choose file</button>
            <span v-if="mdSelectedFile" class="text-xs" style="color:var(--app-text-sec)">{{ mdSelectedFile.name }}</span>
            <span v-else class="text-xs" style="color:var(--app-placeholder)">No file chosen</span>
          </div>
          <p v-if="mdInspecting" class="text-xs mt-3" style="color:var(--app-text-sec)">Reading file…</p>
          <p v-if="mdError" class="text-sm mt-3" style="color:#ff3b30">{{ mdError }}</p>
          <p v-if="run.masterdata_path && !mdSelectedFile" class="text-xs mt-4" style="color:var(--app-text-sec)">
            Previously uploaded: <code>{{ mdFileName }}</code>
          </p>
        </div>

        <!-- Dataset mode -->
        <div v-else>
          <p class="text-xs mb-3" style="color:var(--app-text-sec)">Select a previously imported masterdata dataset.</p>
          <p v-if="mdDatasetsLoading" class="text-xs" style="color:var(--app-text-sec)">Loading datasets…</p>
          <p v-else-if="mdDatasets.length === 0" class="text-xs" style="color:var(--app-text-sec)">No masterdata datasets found. Import one in the Datasets section first.</p>
          <div v-else class="space-y-2 mb-3">
            <label
              v-for="ds in mdDatasets"
              :key="ds.id"
              class="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer"
              :style="mdSelectedDatasetId === ds.id
                ? 'border:1px solid var(--badge-blue-color);background:var(--badge-blue-bg)'
                : 'border:1px solid var(--app-border)'"
            >
              <input type="radio" :value="ds.id" v-model="mdSelectedDatasetId" class="text-blue-600" />
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium truncate" style="color:var(--app-text)">{{ ds.name }}</p>
                <p class="text-xs" style="color:var(--app-text-sec)">{{ ds.row_count.toLocaleString() }} rows · {{ ds.size_mb }} MB · {{ formatDate(ds.created_at) }}</p>
              </div>
            </label>
          </div>
          <p v-if="mdError" class="text-sm mb-2" style="color:#ff3b30">{{ mdError }}</p>
          <button
            v-if="mdDatasets.length > 0"
            @click="doMdFromDataset"
            :disabled="!mdSelectedDatasetId || mdRunning"
            class="btn-apple-primary"
          >
            {{ mdRunning ? 'Importing…' : 'Use this dataset →' }}
          </button>
        </div>
      </div>

      <!-- Step: mapping -->
      <div v-else-if="mdStep === 'mapping' && mdInspectResult" class="space-y-4">
        <div>
          <div class="flex items-center justify-between mb-4">
            <p class="text-xs font-medium" style="color:var(--app-text-sec)">Map columns</p>
            <button @click="mdStep = 'upload'" class="text-xs" style="color:var(--app-text-sec);background:none;border:none;cursor:pointer">← Back</button>
          </div>

          <!-- Required fields -->
          <div class="mb-4">
            <p class="text-xs font-semibold uppercase tracking-wide mb-2" style="color:var(--app-text)">Required fields</p>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div v-for="field in mdRequiredFields" :key="field.name" class="flex flex-col gap-1">
                <label class="text-xs" style="color:var(--app-text-sec)">
                  {{ field.name }}
                  <span v-if="mdIsDuplicate(field.name)" class="ml-1" style="color:#ff9500" title="Duplicate mapping">⚠</span>
                  <span v-else-if="!mdUserMapping[field.name]" class="ml-1" style="color:#ff3b30">*</span>
                </label>
                <select
                  v-model="mdUserMapping[field.name]"
                  class="w-full text-xs rounded px-2 py-1"
                  :style="!mdUserMapping[field.name]
                    ? 'border:1px solid #ff3b30;background:var(--app-input-bg);color:var(--app-text)'
                    : 'border:1px solid var(--app-input-border);background:var(--app-input-bg);color:var(--app-text)'"
                >
                  <option value="">— not mapped —</option>
                  <option v-for="col in mdInspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Optional fields -->
          <details class="mb-4">
            <summary class="text-xs font-semibold uppercase tracking-wide cursor-pointer mb-2" style="color:var(--app-text-sec)">Optional fields</summary>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-2">
              <div v-for="field in mdOptionalFields" :key="field.name" class="flex flex-col gap-1">
                <label class="text-xs" style="color:var(--app-text-sec)">{{ field.name }}</label>
                <select
                  v-model="mdUserMapping[field.name]"
                  class="w-full text-xs rounded px-2 py-1"
                  style="border:1px solid var(--app-input-border);background:var(--app-input-bg);color:var(--app-text)"
                >
                  <option value="">— not mapped —</option>
                  <option v-for="col in mdInspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
                </select>
              </div>
            </div>
          </details>

          <!-- Preview table -->
          <div class="overflow-x-auto mb-4">
            <p class="text-xs font-medium mb-1" style="color:var(--app-text-sec)">File preview (5 rows)</p>
            <table class="text-xs rounded w-full" style="border:1px solid var(--app-border)">
              <thead style="background:var(--table-header-bg)">
                <tr>
                  <th v-for="col in mdInspectResult.file_columns" :key="col" class="px-2 py-1 text-left font-medium whitespace-nowrap" style="color:var(--app-text-sec);border-bottom:1px solid var(--table-divider)">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in mdInspectResult.preview_rows" :key="i" style="border-bottom:1px solid var(--table-divider)">
                  <td v-for="col in mdInspectResult.file_columns" :key="col" class="px-2 py-1 whitespace-nowrap" style="color:var(--app-text)">{{ row[col] ?? '' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-if="mdMissingRequired.length > 0" class="text-xs mb-3" style="color:#ff3b30">Missing required: {{ mdMissingRequired.join(', ') }}</p>
          <p v-if="mdDuplicateFields.length > 0" class="text-xs mb-3" style="color:#ff9500">Duplicate mappings: {{ mdDuplicateFields.join(', ') }}</p>
          <p v-if="mdError" class="text-sm mb-3" style="color:#ff3b30">{{ mdError }}</p>

          <button
            @click="doMdQuality"
            :disabled="mdRunning || mdMissingRequired.length > 0 || mdDuplicateFields.length > 0"
            class="btn-apple-primary"
          >
            {{ mdRunning ? 'Running quality check…' : 'Run quality check →' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Orders Section ── -->
    <div class="card-apple">
      <div class="flex items-center justify-between mb-3">
        <h3 style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Orders</h3>
        <span v-if="run.orders_validation_result" class="flex items-center gap-1 text-xs font-medium" style="color:#34c759">
          <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          Imported
        </span>
      </div>

      <!-- Done state -->
      <div v-if="run.orders_validation_result && ordersStep === 'done'" class="space-y-2">
        <p class="text-xs" style="color:var(--app-text-sec)"><code>{{ ordersUploadedFileName || ordersFileName }}</code></p>
        <button @click="ordersStep = 'upload'" class="text-xs underline" style="color:var(--app-text-sec);background:none;border:none;cursor:pointer;padding:0">Re-upload</button>
      </div>

      <!-- Step: upload -->
      <div v-else-if="ordersStep === 'upload'">
        <!-- Mode toggle -->
        <div class="flex gap-1 mb-4 p-0.5 rounded-lg w-fit" style="background:var(--table-header-bg)">
          <button
            @click="ordersMode = 'file'"
            class="text-xs px-3 py-1 rounded-md transition-colors"
            :style="ordersMode === 'file'
              ? 'background:var(--app-surface);color:var(--app-text);box-shadow:0 1px 2px rgba(0,0,0,0.15);font-weight:500'
              : 'background:transparent;color:var(--app-text-sec)'"
          >Upload file</button>
          <button
            @click="ordersMode = 'dataset'; loadOrdersDatasets()"
            class="text-xs px-3 py-1 rounded-md transition-colors"
            :style="ordersMode === 'dataset'
              ? 'background:var(--app-surface);color:var(--app-text);box-shadow:0 1px 2px rgba(0,0,0,0.15);font-weight:500'
              : 'background:transparent;color:var(--app-text-sec)'"
          >From dataset</button>
        </div>

        <!-- File upload mode -->
        <div v-if="ordersMode === 'file'">
          <p class="text-xs mb-3" style="color:var(--app-text-sec)">Upload an Excel or CSV file with order lines (order_id, sku, quantity, date).</p>
          <input ref="ordersFileInput" type="file" accept=".xlsx,.xls,.csv" class="hidden" @change="onOrdersFileChange" />
          <div class="flex items-center gap-2">
            <button @click="ordersFileInput?.click()" class="btn-apple-pill" style="font-size:13px">Choose file</button>
            <span v-if="ordersSelectedFile" class="text-xs" style="color:var(--app-text-sec)">{{ ordersSelectedFile.name }}</span>
            <span v-else class="text-xs" style="color:var(--app-placeholder)">No file chosen</span>
          </div>
          <p v-if="ordersInspecting" class="text-xs mt-3" style="color:var(--app-text-sec)">Reading file…</p>
          <p v-if="ordersUploadError" class="text-sm mt-2" style="color:#ff3b30">{{ ordersUploadError }}</p>
          <p v-if="run.orders_path && !ordersSelectedFile" class="text-xs mt-4" style="color:var(--app-text-sec)">
            Previously uploaded: <code>{{ ordersFileName }}</code>
          </p>
        </div>

        <!-- Dataset mode -->
        <div v-else>
          <p class="text-xs mb-3" style="color:var(--app-text-sec)">Select a previously imported orders dataset.</p>
          <p v-if="ordersDatasetsLoading" class="text-xs" style="color:var(--app-text-sec)">Loading datasets…</p>
          <p v-else-if="ordersDatasets.length === 0" class="text-xs" style="color:var(--app-text-sec)">No orders datasets found. Import one in the Datasets section first.</p>
          <div v-else class="space-y-2 mb-3">
            <label
              v-for="ds in ordersDatasets"
              :key="ds.id"
              class="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer"
              :style="ordersSelectedDatasetId === ds.id
                ? 'border:1px solid var(--badge-blue-color);background:var(--badge-blue-bg)'
                : 'border:1px solid var(--app-border)'"
            >
              <input type="radio" :value="ds.id" v-model="ordersSelectedDatasetId" class="text-blue-600" />
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium truncate" style="color:var(--app-text)">{{ ds.name }}</p>
                <p class="text-xs" style="color:var(--app-text-sec)">{{ ds.row_count.toLocaleString() }} rows · {{ ds.size_mb }} MB · {{ formatDate(ds.created_at) }}</p>
              </div>
            </label>
          </div>
          <p v-if="ordersUploadError" class="text-sm mb-2" style="color:#ff3b30">{{ ordersUploadError }}</p>
          <button
            v-if="ordersDatasets.length > 0"
            @click="doOrdersFromDataset"
            :disabled="!ordersSelectedDatasetId || ordersIngesting"
            class="btn-apple-primary"
          >
            {{ ordersIngesting ? 'Importing…' : 'Use this dataset →' }}
          </button>
        </div>
      </div>

      <!-- Step: mapping -->
      <div v-else-if="ordersStep === 'mapping' && ordersInspectResult">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs font-medium" style="color:var(--app-text-sec)">Map columns</p>
          <button @click="ordersStep = 'upload'" class="text-xs" style="color:var(--app-text-sec);background:none;border:none;cursor:pointer">← Back</button>
        </div>
        <!-- Required fields -->
        <div class="mb-4">
          <p class="text-xs font-semibold uppercase tracking-wide mb-2" style="color:var(--app-text)">Required fields</p>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div v-for="field in ordersRequiredFields" :key="field.name" class="flex flex-col gap-1">
              <label class="text-xs" style="color:var(--app-text-sec)">
                {{ field.name }}
                <span v-if="!ordersMapping[field.name]" class="ml-1" style="color:#ff3b30">*</span>
              </label>
              <select
                v-model="ordersMapping[field.name]"
                class="w-full text-xs rounded px-2 py-1"
                :style="!ordersMapping[field.name]
                  ? 'border:1px solid #ff3b30;background:var(--app-input-bg);color:var(--app-text)'
                  : 'border:1px solid var(--app-input-border);background:var(--app-input-bg);color:var(--app-text)'"
              >
                <option value="">— not mapped —</option>
                <option v-for="col in ordersInspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
          </div>
        </div>
        <!-- Optional fields -->
        <details class="mb-4">
          <summary class="text-xs font-semibold uppercase tracking-wide cursor-pointer mb-2" style="color:var(--app-text-sec)">Optional fields</summary>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-2">
            <div v-for="field in ordersOptionalFields" :key="field.name" class="flex flex-col gap-1">
              <label class="text-xs" style="color:var(--app-text-sec)">{{ field.name }}</label>
              <select
                v-model="ordersMapping[field.name]"
                class="w-full text-xs rounded px-2 py-1"
                style="border:1px solid var(--app-input-border);background:var(--app-input-bg);color:var(--app-text)"
              >
                <option value="">— not mapped —</option>
                <option v-for="col in ordersInspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
          </div>
        </details>
        <!-- Preview -->
        <div class="overflow-x-auto mb-3">
          <table class="text-xs rounded w-full" style="border:1px solid var(--app-border)">
            <thead style="background:var(--table-header-bg)">
              <tr>
                <th v-for="col in ordersInspectResult.file_columns" :key="col" class="px-2 py-1 text-left whitespace-nowrap" style="color:var(--app-text-sec);border-bottom:1px solid var(--table-divider)">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in ordersInspectResult.preview_rows" :key="i" style="border-bottom:1px solid var(--table-divider)">
                <td v-for="col in ordersInspectResult.file_columns" :key="col" class="px-2 py-1 whitespace-nowrap" style="color:var(--app-text)">{{ row[col] ?? '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="ordersMissingRequired.length > 0" class="text-xs mb-2" style="color:#ff3b30">Missing required: {{ ordersMissingRequired.join(', ') }}</p>
        <p v-if="ordersUploadError" class="text-sm mb-2" style="color:#ff3b30">{{ ordersUploadError }}</p>
        <button
          @click="doOrdersIngest"
          :disabled="ordersIngesting || ordersMissingRequired.length > 0"
          class="btn-apple-primary"
        >
          {{ ordersIngesting ? 'Running quality check…' : 'Run quality check →' }}
        </button>
      </div>
    </div>

    <!-- ── Proceed without full import modal ── -->
    <div
      v-if="showProceedModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="showProceedModal = false"
    >
      <div class="card-apple-elevated w-full mx-4" style="max-width:360px">
        <h3 style="font-size:17px;font-weight:600;color:var(--app-text);margin-bottom:8px">Missing import</h3>
        <p style="font-size:14px;color:var(--app-text-ter);letter-spacing:-0.224px;margin-bottom:20px">{{ proceedModalMessage }} Proceed to Validation anyway?</p>
        <div class="flex justify-end gap-2">
          <button
            @click="showProceedModal = false"
            style="font-size:14px;color:var(--app-text-sec);background:none;border:none;cursor:pointer;padding:8px 12px"
          >
            Cancel
          </button>
          <button
            @click="onProceedConfirm"
            class="btn-apple-primary"
          >
            Proceed
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { RunDetail, MappingInspectResponse } from '@/api/runs'
import { runsApi } from '@/api/runs'
import type { Dataset } from '@/api/datasets'
import { datasetsApi } from '@/api/datasets'
import { extractApiError } from '@/api/client'
import { useNotificationsStore } from '@/stores/notifications'
import { useAnalysisStore } from '@/stores/analysis'

const notify = useNotificationsStore()
const analysis = useAnalysisStore()

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{
  (e: 'refreshed'): void
  (e: 'navigate', tab: string): void
}>()

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' })
}

// ── Masterdata wizard ────────────────────────────────────────────────────────

const mdFileInput = ref<HTMLInputElement>()
const mdSelectedFile = ref<File | null>(null)
const mdUploadedFileName = ref('')
const mdInspecting = ref(false)
const mdRunning = ref(false)
const mdError = ref('')
const mdStep = ref<'upload' | 'mapping' | 'done'>('upload')
const mdInspectResult = ref<MappingInspectResponse | null>(null)
const mdUserMapping = ref<Record<string, string>>({})
const mdMode = ref<'file' | 'dataset'>('file')
const mdDatasets = ref<Dataset[]>([])
const mdDatasetsLoading = ref(false)
const mdSelectedDatasetId = ref('')

const mdFileName = computed(() => props.run.masterdata_original_filename || '')

const mdRequiredFields = computed(() =>
  (mdInspectResult.value?.schema_fields ?? []).filter(f => f.required)
)
const mdOptionalFields = computed(() =>
  (mdInspectResult.value?.schema_fields ?? []).filter(f => !f.required)
)
const mdMissingRequired = computed(() =>
  mdRequiredFields.value.filter(f => !mdUserMapping.value[f.name]).map(f => f.name)
)
const mdMappingSummary = computed(() =>
  mdRequiredFields.value
    .filter(f => mdUserMapping.value[f.name])
    .map(f => ({ field: f.name, col: mdUserMapping.value[f.name] }))
)
const mdDuplicateFields = computed(() => {
  const values = Object.values(mdUserMapping.value).filter(Boolean)
  const seen = new Set<string>()
  const dups = new Set<string>()
  for (const v of values) {
    if (seen.has(v)) dups.add(v)
    seen.add(v)
  }
  return [...dups]
})

function mdIsDuplicate(fieldName: string) {
  const col = mdUserMapping.value[fieldName]
  if (!col) return false
  return mdDuplicateFields.value.includes(col)
}

async function loadMdDatasets() {
  if (mdDatasets.value.length > 0) return
  mdDatasetsLoading.value = true
  try {
    const { data } = await datasetsApi.list()
    mdDatasets.value = data.datasets.filter(d => d.file_type === 'masterdata')
  } catch {
    // ignore
  } finally {
    mdDatasetsLoading.value = false
  }
}

function onMdFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  mdSelectedFile.value = input.files?.[0] ?? null
  mdUploadedFileName.value = mdSelectedFile.value?.name ?? ''
  mdError.value = ''
  if (mdSelectedFile.value) doMdInspect()
}

async function doMdInspect() {
  if (!mdSelectedFile.value) return
  mdInspecting.value = true
  analysis.start()
  mdError.value = ''
  try {
    const { data } = await runsApi.inspectMasterdata(props.run.id, mdSelectedFile.value)
    mdInspectResult.value = data
    const mapping: Record<string, string> = {}
    for (const field of data.schema_fields) {
      const sug = data.suggestions.find(s => s.suggested_target === field.name)
      mapping[field.name] = sug?.source_column ?? ''
    }
    mdUserMapping.value = mapping
    mdStep.value = 'mapping'
  } catch (e: unknown) {
    mdError.value = extractApiError(e) || 'Failed to read file.'
  } finally {
    mdInspecting.value = false
    analysis.stop()
  }
}

async function doMdFromDataset() {
  if (!mdSelectedDatasetId.value) return
  mdRunning.value = true
  analysis.start()
  mdError.value = ''
  try {
    const ds = mdDatasets.value.find(d => d.id === mdSelectedDatasetId.value)
    await runsApi.useMasterdataDataset(props.run.id, mdSelectedDatasetId.value)
    mdUploadedFileName.value = ds?.name ?? 'dataset'
    mdStep.value = 'done'
    emit('refreshed')
    notify.push({
      type: 'success',
      title: 'Import complete',
      message: `${ds?.name ?? 'Dataset'} · ${ds?.row_count.toLocaleString() ?? ''} rows`,
    })
    if (props.run.orders_validation_result) {
      emit('navigate', 'quality')
    } else {
      proceedModalMessage.value = 'Orders have not been imported yet.'
      showProceedModal.value = true
    }
  } catch (e: unknown) {
    const msg = extractApiError(e) || 'Import failed.'
    mdError.value = msg
    notify.push({ type: 'error', title: 'Import failed', message: msg })
  } finally {
    mdRunning.value = false
    analysis.stop()
  }
}

async function doMdQuality() {
  mdRunning.value = true
  analysis.start()
  mdError.value = ''
  try {
    await runsApi.runQualityWithMapping(props.run.id, null, mdUserMapping.value)
    mdStep.value = 'done'
    emit('refreshed')
    notify.push({
      type: 'success',
      title: 'Import complete',
      message: `${mdUploadedFileName.value} · ${mdMappingSummary.value.length} columns mapped`,
    })
    if (props.run.orders_validation_result) {
      emit('navigate', 'quality')
    } else {
      proceedModalMessage.value = 'Orders have not been imported yet.'
      showProceedModal.value = true
    }
  } catch (e: unknown) {
    const msg = extractApiError(e) || 'Quality check failed.'
    mdError.value = msg
    notify.push({ type: 'error', title: 'Quality check failed', message: msg })
  } finally {
    mdRunning.value = false
    analysis.stop()
  }
}

// ── Orders wizard ────────────────────────────────────────────────────────────

const ordersFileInput = ref<HTMLInputElement>()
const ordersSelectedFile = ref<File | null>(null)
const ordersUploadedFileName = ref('')
const ordersInspecting = ref(false)
const ordersIngesting = ref(false)
const ordersUploadError = ref('')
const ordersStep = ref<'upload' | 'mapping' | 'done'>('upload')
const ordersInspectResult = ref<MappingInspectResponse | null>(null)
const ordersMapping = ref<Record<string, string>>({})
const ordersMode = ref<'file' | 'dataset'>('file')
const ordersDatasets = ref<Dataset[]>([])
const ordersDatasetsLoading = ref(false)
const ordersSelectedDatasetId = ref('')

const ordersFileName = computed(() => props.run.orders_original_filename || '')

const ordersRequiredFields = computed(() =>
  (ordersInspectResult.value?.schema_fields ?? []).filter(f => f.required)
)
const ordersOptionalFields = computed(() =>
  (ordersInspectResult.value?.schema_fields ?? []).filter(f => !f.required)
)
const ordersMissingRequired = computed(() =>
  ordersRequiredFields.value.filter(f => !ordersMapping.value[f.name]).map(f => f.name)
)
const ordersMappingSummary = computed(() =>
  ordersRequiredFields.value
    .filter(f => ordersMapping.value[f.name])
    .map(f => ({ field: f.name, col: ordersMapping.value[f.name] }))
)

async function loadOrdersDatasets() {
  if (ordersDatasets.value.length > 0) return
  ordersDatasetsLoading.value = true
  try {
    const { data } = await datasetsApi.list()
    ordersDatasets.value = data.datasets.filter(d => d.file_type === 'orders')
  } catch {
    // ignore
  } finally {
    ordersDatasetsLoading.value = false
  }
}

function onOrdersFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  ordersSelectedFile.value = input.files?.[0] ?? null
  ordersUploadedFileName.value = ordersSelectedFile.value?.name ?? ''
  ordersUploadError.value = ''
  if (ordersSelectedFile.value) doOrdersInspect()
}

async function doOrdersInspect() {
  if (!ordersSelectedFile.value) return
  ordersInspecting.value = true
  analysis.start()
  ordersUploadError.value = ''
  try {
    const { data } = await runsApi.inspectOrders(props.run.id, ordersSelectedFile.value)
    ordersInspectResult.value = data
    const mapping: Record<string, string> = {}
    for (const field of data.schema_fields) {
      const sug = data.suggestions.find(s => s.suggested_target === field.name)
      mapping[field.name] = sug?.source_column ?? ''
    }
    ordersMapping.value = mapping
    ordersStep.value = 'mapping'
    emit('refreshed')
  } catch (e: unknown) {
    ordersUploadError.value = extractApiError(e) || 'Failed to read file.'
  } finally {
    ordersInspecting.value = false
    analysis.stop()
  }
}

async function doOrdersFromDataset() {
  if (!ordersSelectedDatasetId.value) return
  ordersIngesting.value = true
  analysis.start()
  ordersUploadError.value = ''
  try {
    const ds = ordersDatasets.value.find(d => d.id === ordersSelectedDatasetId.value)
    await runsApi.useOrdersDataset(props.run.id, ordersSelectedDatasetId.value)
    ordersUploadedFileName.value = ds?.name ?? 'dataset'
    ordersStep.value = 'done'
    emit('refreshed')
    notify.push({
      type: 'success',
      title: 'Import complete',
      message: `${ds?.name ?? 'Dataset'} · ${ds?.row_count.toLocaleString() ?? ''} rows`,
    })
    if (props.run.quality_result) {
      emit('navigate', 'quality')
    } else {
      proceedModalMessage.value = 'Masterdata has not been imported yet.'
      showProceedModal.value = true
    }
  } catch (e: unknown) {
    const msg = extractApiError(e) || 'Import failed.'
    ordersUploadError.value = msg
    notify.push({ type: 'error', title: 'Import failed', message: msg })
  } finally {
    ordersIngesting.value = false
    analysis.stop()
  }
}

async function doOrdersIngest() {
  ordersIngesting.value = true
  analysis.start()
  ordersUploadError.value = ''
  try {
    await runsApi.ingestOrders(props.run.id, ordersMapping.value)
    ordersStep.value = 'done'
    emit('refreshed')
    notify.push({
      type: 'success',
      title: 'Import complete',
      message: `${ordersUploadedFileName.value} · ${ordersMappingSummary.value.length} columns mapped`,
    })
    if (props.run.quality_result) {
      emit('navigate', 'quality')
    } else {
      proceedModalMessage.value = 'Masterdata has not been imported yet.'
      showProceedModal.value = true
    }
  } catch (e: unknown) {
    const msg = extractApiError(e) || 'Ingestion failed.'
    ordersUploadError.value = msg
    notify.push({ type: 'error', title: 'Import failed', message: msg })
  } finally {
    ordersIngesting.value = false
    analysis.stop()
  }
}

// ── Proceed modal ────────────────────────────────────────────────────────────

const showProceedModal = ref(false)
const proceedModalMessage = ref('')

function onProceedConfirm() {
  showProceedModal.value = false
  emit('navigate', 'quality')
}

// ── Init ─────────────────────────────────────────────────────────────────────

onMounted(() => {
  if (props.run.quality_result) mdStep.value = 'done'
  if (props.run.orders_validation_result) ordersStep.value = 'done'
})
</script>
