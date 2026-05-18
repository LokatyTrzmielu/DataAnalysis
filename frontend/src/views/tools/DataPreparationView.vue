<template>
  <div>
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
      <RouterLink to="/tools" class="text-sm" style="color:var(--app-text-sec)">Tools</RouterLink>
      <span style="color:var(--app-text-sec)">›</span>
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:var(--app-text);line-height:1.14;letter-spacing:-0.28px">
        Data Preparation
      </h2>
    </div>

    <div class="card-apple" style="max-width:720px">

      <!-- Step: type-select -->
      <div v-if="step === 'type-select'">
        <p style="font-size:14px;font-weight:600;color:var(--app-text);margin-bottom:4px">What type of data are you merging?</p>
        <p class="mb-5" style="font-size:13px;color:var(--app-text-sec)">Select the data type. All files must share the same column structure.</p>
        <div class="flex gap-3">
          <button @click="fileType = 'masterdata'; step = 'upload'" class="btn-apple-primary">Masterdata</button>
          <button @click="fileType = 'orders'; step = 'upload'" class="btn-apple-primary">Orders</button>
        </div>
      </div>

      <!-- Step: upload -->
      <div v-else-if="step === 'upload'">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p style="font-size:14px;font-weight:600;color:var(--app-text);margin-bottom:2px">Select files to merge</p>
            <p style="font-size:12px;color:var(--app-text-sec)">
              Type: <span class="font-medium" style="color:var(--app-text)">{{ fileType }}</span> · Excel or CSV · min. 1 file
            </p>
          </div>
          <button @click="step = 'type-select'; selectedFiles = []" class="text-xs" style="color:var(--app-text-sec)">← Back</button>
        </div>

        <!-- Hidden native input + styled trigger -->
        <input
          ref="fileInputRef"
          type="file"
          multiple
          accept=".xlsx,.xls,.csv"
          class="hidden"
          @change="onFilesChange"
        />
        <button
          @click="fileInputRef?.click()"
          class="btn-apple-pill mb-4"
          style="font-size:13px"
        >
          + Add files
        </button>

        <!-- File list -->
        <div v-if="selectedFiles.length > 0" class="space-y-1.5 mb-4">
          <div
            v-for="(f, i) in selectedFiles"
            :key="i"
            class="flex items-center justify-between px-3 py-2 rounded-lg"
            style="background:var(--table-header-bg);font-size:13px"
          >
            <span style="color:var(--app-text)">{{ f.name }}</span>
            <div class="flex items-center gap-3">
              <span style="color:var(--app-text-sec)">{{ (f.size / 1024).toFixed(0) }} KB</span>
              <button @click="removeFile(i)" style="color:#ff3b30;background:none;border:none;cursor:pointer;font-size:12px;padding:0">Remove</button>
            </div>
          </div>
        </div>

        <p v-if="uploadError" class="text-sm mb-3" style="color:#ff3b30">{{ uploadError }}</p>

        <button
          @click="doInspect"
          :disabled="selectedFiles.length === 0 || inspecting"
          class="btn-apple-primary"
        >
          {{ inspecting ? 'Reading file…' : 'Inspect first file →' }}
        </button>
      </div>

      <!-- Step: mapping -->
      <div v-else-if="step === 'mapping' && inspectResult">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p style="font-size:14px;font-weight:600;color:var(--app-text);margin-bottom:2px">Map columns</p>
            <p style="font-size:12px;color:var(--app-text-sec)">Mapping will be applied to all {{ selectedFiles.length }} file{{ selectedFiles.length > 1 ? 's' : '' }}.</p>
          </div>
          <button @click="step = 'upload'" class="text-xs" style="color:var(--app-text-sec)">← Back</button>
        </div>

        <!-- Required fields -->
        <div class="mb-4">
          <p class="text-xs font-semibold uppercase tracking-wide mb-2" style="color:var(--app-text)">Required fields</p>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div v-for="field in requiredFields" :key="field.name" class="flex flex-col gap-1">
              <label class="text-xs" style="color:var(--app-text-sec)">
                {{ field.name }}
                <span v-if="isDuplicate(field.name)" class="ml-1" style="color:#ff9500" title="Duplicate mapping">⚠</span>
                <span v-else-if="!userMapping[field.name]" class="ml-1" style="color:#ff3b30">*</span>
              </label>
              <select
                v-model="userMapping[field.name]"
                class="w-full text-xs rounded px-2 py-1"
                :style="!userMapping[field.name]
                  ? 'border:1px solid #ff3b30;background:var(--app-input-bg);color:var(--app-text)'
                  : 'border:1px solid var(--app-input-border);background:var(--app-input-bg);color:var(--app-text)'"
              >
                <option value="">— not mapped —</option>
                <option v-for="col in inspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Optional fields -->
        <details class="mb-4">
          <summary class="text-xs font-semibold uppercase tracking-wide cursor-pointer mb-2" style="color:var(--app-text-sec)">Optional fields</summary>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-2">
            <div v-for="field in optionalFields" :key="field.name" class="flex flex-col gap-1">
              <label class="text-xs" style="color:var(--app-text-sec)">{{ field.name }}</label>
              <select
                v-model="userMapping[field.name]"
                class="w-full text-xs rounded px-2 py-1"
                style="border:1px solid var(--app-input-border);background:var(--app-input-bg);color:var(--app-text)"
              >
                <option value="">— not mapped —</option>
                <option v-for="col in inspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
          </div>
        </details>

        <!-- Preview -->
        <div class="overflow-x-auto mb-4">
          <p class="text-xs font-medium mb-1" style="color:var(--app-text-sec)">File preview (first file, 5 rows)</p>
          <table class="text-xs rounded w-full" style="border:1px solid var(--app-border)">
            <thead style="background:var(--table-header-bg)">
              <tr>
                <th
                  v-for="col in inspectResult.file_columns"
                  :key="col"
                  class="px-2 py-1 text-left font-medium whitespace-nowrap"
                  style="color:var(--app-text-sec);border-bottom:1px solid var(--table-divider)"
                >{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in inspectResult.preview_rows" :key="i" style="border-bottom:1px solid var(--table-divider)">
                <td v-for="col in inspectResult.file_columns" :key="col" class="px-2 py-1 whitespace-nowrap" style="color:var(--app-text)">{{ row[col] ?? '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="missingRequired.length > 0" class="text-xs mb-3" style="color:#ff3b30">Missing required: {{ missingRequired.join(', ') }}</p>
        <p v-if="duplicateFields.length > 0" class="text-xs mb-3" style="color:#ff9500">Duplicate mappings: {{ duplicateFields.join(', ') }}</p>

        <button
          @click="step = 'confirm'"
          :disabled="missingRequired.length > 0 || duplicateFields.length > 0"
          class="btn-apple-primary"
        >
          Continue →
        </button>
      </div>

      <!-- Step: confirm -->
      <div v-else-if="step === 'confirm'">
        <div class="flex items-center justify-between mb-4">
          <p style="font-size:14px;font-weight:600;color:var(--app-text)">Confirm & save</p>
          <button @click="step = 'mapping'" class="text-xs" style="color:var(--app-text-sec)">← Back</button>
        </div>

        <div class="space-y-3 mb-5">
          <div class="flex items-center gap-3 px-3 py-2.5 rounded-lg" style="background:var(--table-header-bg)">
            <span class="text-xs" style="color:var(--app-text-sec);width:80px">Type</span>
            <span class="text-xs font-medium" style="color:var(--app-text)">{{ fileType }}</span>
          </div>
          <div class="flex items-center gap-3 px-3 py-2.5 rounded-lg" style="background:var(--table-header-bg)">
            <span class="text-xs" style="color:var(--app-text-sec);width:80px">Files</span>
            <span class="text-xs font-medium" style="color:var(--app-text)">{{ selectedFiles.length }} file{{ selectedFiles.length > 1 ? 's' : '' }} ({{ selectedFiles.map(f => f.name).join(', ') }})</span>
          </div>
          <div class="flex items-center gap-3 px-3 py-2.5 rounded-lg" style="background:var(--table-header-bg)">
            <span class="text-xs" style="color:var(--app-text-sec);width:80px">Columns mapped</span>
            <span class="text-xs font-medium" style="color:var(--app-text)">{{ Object.values(userMapping).filter(Boolean).length }}</span>
          </div>
        </div>

        <div class="mb-5">
          <label class="text-xs font-medium block mb-1" style="color:var(--app-text-sec)">Dataset name</label>
          <input
            v-model="datasetName"
            type="text"
            class="input-apple-sm"
            placeholder="e.g. merged_masterdata_2024"
            style="max-width:320px"
          />
        </div>

        <p v-if="mergeError" class="text-sm mb-3" style="color:#ff3b30">{{ mergeError }}</p>

        <button
          @click="doMerge"
          :disabled="merging"
          class="btn-apple-primary"
        >
          {{ merging ? 'Merging…' : 'Merge & save to Datasets →' }}
        </button>
      </div>

      <!-- Step: done -->
      <div v-else-if="step === 'done' && savedDataset">
        <div class="flex items-center gap-2 mb-4">
          <span class="flex items-center gap-1 font-medium" style="font-size:12px;color:#34c759">
            <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            Done
          </span>
          <p style="font-size:14px;font-weight:600;color:var(--app-text)">Dataset created</p>
        </div>
        <div class="px-3 py-2.5 rounded-lg mb-5 space-y-1" style="background:var(--table-header-bg)">
          <p class="text-xs" style="color:var(--app-text)"><span style="color:var(--app-text-sec)">Name: </span>{{ savedDataset.name }}</p>
          <p class="text-xs" style="color:var(--app-text)"><span style="color:var(--app-text-sec)">Rows: </span>{{ savedDataset.row_count.toLocaleString() }}</p>
          <p class="text-xs" style="color:var(--app-text)"><span style="color:var(--app-text-sec)">Size: </span>{{ savedDataset.size_mb }} MB</p>
        </div>
        <div class="flex gap-3">
          <RouterLink to="/datasets" class="btn-apple-primary">Go to Datasets →</RouterLink>
          <button @click="reset" class="btn-apple-pill">Merge another</button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { MappingInspectResponse } from '@/api/runs'
import type { Dataset } from '@/api/datasets'
import { toolsApi } from '@/api/tools'
import { useNotificationsStore } from '@/stores/notifications'

const notify = useNotificationsStore()

type Step = 'type-select' | 'upload' | 'mapping' | 'confirm' | 'done'

const step = ref<Step>('type-select')
const fileType = ref<'masterdata' | 'orders'>('masterdata')

// Upload
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFiles = ref<File[]>([])
const uploadError = ref('')
const inspecting = ref(false)
const inspectResult = ref<MappingInspectResponse | null>(null)

// Mapping
const userMapping = ref<Record<string, string>>({})

// Confirm
const datasetName = ref('')
const merging = ref(false)
const mergeError = ref('')
const savedDataset = ref<Dataset | null>(null)

const requiredFields = computed(() =>
  (inspectResult.value?.schema_fields ?? []).filter(f => f.required)
)
const optionalFields = computed(() =>
  (inspectResult.value?.schema_fields ?? []).filter(f => !f.required)
)
const missingRequired = computed(() =>
  requiredFields.value.filter(f => !userMapping.value[f.name]).map(f => f.name)
)
const duplicateFields = computed(() => {
  const values = Object.values(userMapping.value).filter(Boolean)
  const seen = new Set<string>()
  const dups = new Set<string>()
  for (const v of values) {
    if (seen.has(v)) dups.add(v)
    seen.add(v)
  }
  return [...dups]
})

function isDuplicate(fieldName: string) {
  const col = userMapping.value[fieldName]
  return col ? duplicateFields.value.includes(col) : false
}

function onFilesChange(e: Event) {
  const input = e.target as HTMLInputElement
  const newFiles = Array.from(input.files ?? [])
  const existingNames = new Set(selectedFiles.value.map(f => f.name))
  selectedFiles.value = [...selectedFiles.value, ...newFiles.filter(f => !existingNames.has(f.name))]
  uploadError.value = ''
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function removeFile(index: number) {
  selectedFiles.value = selectedFiles.value.filter((_, i) => i !== index)
}

async function doInspect() {
  const firstFile = selectedFiles.value[0]
  if (!firstFile) return
  inspecting.value = true
  uploadError.value = ''
  try {
    const { data } = await toolsApi.inspectFile(firstFile, fileType.value)
    inspectResult.value = data
    const mapping: Record<string, string> = {}
    for (const field of data.schema_fields) {
      const sug = data.suggestions.find(s => s.suggested_target === field.name)
      mapping[field.name] = sug?.source_column ?? ''
    }
    userMapping.value = mapping
    datasetName.value = `merged_${firstFile.name.replace(/\.[^.]+$/, '')}`
    step.value = 'mapping'
  } catch (e: unknown) {
    uploadError.value = (e as Error).message || 'Failed to read file.'
  } finally {
    inspecting.value = false
  }
}

async function doMerge() {
  merging.value = true
  mergeError.value = ''
  try {
    const { data } = await toolsApi.mergeFiles(
      selectedFiles.value,
      fileType.value,
      userMapping.value,
      datasetName.value.trim() || undefined,
    )
    savedDataset.value = data
    step.value = 'done'
    notify.push({
      type: 'success',
      title: 'Dataset created',
      message: `${data.name} · ${data.row_count.toLocaleString()} rows · ${data.size_mb} MB`,
    })
  } catch (e: unknown) {
    const msg = (e as Error).message || 'Merge failed.'
    mergeError.value = msg
    notify.push({ type: 'error', title: 'Merge failed', message: msg })
  } finally {
    merging.value = false
  }
}

function reset() {
  step.value = 'type-select'
  fileType.value = 'masterdata'
  selectedFiles.value = []
  inspectResult.value = null
  userMapping.value = {}
  datasetName.value = ''
  mergeError.value = ''
  uploadError.value = ''
  savedDataset.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}
</script>
