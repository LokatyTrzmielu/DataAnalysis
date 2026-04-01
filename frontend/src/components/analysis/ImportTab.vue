<template>
  <div class="space-y-6">
    <!-- Step 1: Upload -->
    <div v-if="step === 'upload'" class="bg-white border border-gray-200 rounded-lg p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-2">Step 1 — Upload masterdata file</h3>
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
      <p v-if="inspecting" class="text-xs text-gray-500 mt-3">Reading file…</p>
      <p v-if="error" class="text-red-600 text-sm mt-3">{{ error }}</p>
      <p v-if="props.run.masterdata_path" class="text-xs text-gray-400 mt-4">
        Previously uploaded: <code>{{ fileName }}</code>
      </p>
    </div>

    <!-- Step 2: Column mapping -->
    <div v-else-if="step === 'mapping' && inspectResult" class="space-y-4">
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-gray-700">Step 2 — Map columns</h3>
          <button @click="step = 'upload'" class="text-xs text-gray-400 hover:text-gray-600">← Back</button>
        </div>

        <!-- Required fields -->
        <div class="mb-4">
          <p class="text-xs font-medium text-gray-600 mb-2">Required fields</p>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div
              v-for="field in requiredFields"
              :key="field.name"
              class="flex flex-col gap-1"
            >
              <label class="text-xs text-gray-600">
                {{ field.name }}
                <span v-if="isDuplicate(field.name)" class="text-yellow-600 ml-1" title="Duplicate mapping">⚠</span>
                <span v-else-if="!userMapping[field.name]" class="text-red-500 ml-1">*</span>
              </label>
              <select
                v-model="userMapping[field.name]"
                :class="[
                  'w-full text-xs border rounded px-2 py-1',
                  !userMapping[field.name] ? 'border-red-300 bg-red-50' : 'border-gray-300',
                ]"
              >
                <option value="">— not mapped —</option>
                <option v-for="col in inspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Optional fields (collapsible) -->
        <details class="mb-4">
          <summary class="text-xs font-medium text-gray-500 cursor-pointer mb-2">Optional fields</summary>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-2">
            <div
              v-for="field in optionalFields"
              :key="field.name"
              class="flex flex-col gap-1"
            >
              <label class="text-xs text-gray-600">{{ field.name }}</label>
              <select
                v-model="userMapping[field.name]"
                class="w-full text-xs border border-gray-300 rounded px-2 py-1"
              >
                <option value="">— not mapped —</option>
                <option v-for="col in inspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
          </div>
        </details>

        <!-- Preview table -->
        <div class="overflow-x-auto mb-4">
          <p class="text-xs font-medium text-gray-600 mb-1">File preview (5 rows)</p>
          <table class="text-xs border border-gray-200 rounded w-full">
            <thead class="bg-gray-50">
              <tr>
                <th
                  v-for="col in inspectResult.file_columns"
                  :key="col"
                  class="px-2 py-1 text-left text-gray-600 font-medium border-b border-gray-200 whitespace-nowrap"
                >{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in inspectResult.preview_rows" :key="i" class="border-b border-gray-100">
                <td
                  v-for="col in inspectResult.file_columns"
                  :key="col"
                  class="px-2 py-1 text-gray-700 whitespace-nowrap"
                >{{ row[col] ?? '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Validation warnings -->
        <p v-if="missingRequired.length > 0" class="text-xs text-red-600 mb-3">
          Missing required: {{ missingRequired.join(', ') }}
        </p>
        <p v-if="duplicateFields.length > 0" class="text-xs text-yellow-600 mb-3">
          Duplicate mappings: {{ duplicateFields.join(', ') }}
        </p>
        <p v-if="error" class="text-red-600 text-sm mb-3">{{ error }}</p>

        <button
          @click="doQuality"
          :disabled="running || missingRequired.length > 0 || duplicateFields.length > 0"
          class="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
        >
          {{ running ? 'Running quality check…' : 'Run quality check →' }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RunDetail, MappingInspectResponse } from '@/api/runs'
import { runsApi } from '@/api/runs'
import { useNotificationsStore } from '@/stores/notifications'

const notify = useNotificationsStore()

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{
  (e: 'refreshed'): void
  (e: 'navigate', tab: string): void
}>()

const fileInput = ref<HTMLInputElement>()
const selectedFile = ref<File | null>(null)
const uploadedFileName = ref('')
const inspecting = ref(false)
const running = ref(false)
const error = ref('')
const step = ref<'upload' | 'mapping' | 'done'>('upload')
const inspectResult = ref<MappingInspectResponse | null>(null)
const userMapping = ref<Record<string, string>>({})

const fileName = computed(() => {
  if (!props.run.masterdata_path) return ''
  return props.run.masterdata_path.split(/[\\/]/).pop() ?? ''
})

const requiredFields = computed(() =>
  (inspectResult.value?.schema_fields ?? []).filter(f => f.required)
)
const optionalFields = computed(() =>
  (inspectResult.value?.schema_fields ?? []).filter(f => !f.required)
)

const missingRequired = computed(() =>
  requiredFields.value.filter(f => !userMapping.value[f.name]).map(f => f.name)
)

const mappingSummary = computed(() =>
  requiredFields.value
    .filter(f => userMapping.value[f.name])
    .map(f => ({ field: f.name, col: userMapping.value[f.name] }))
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
  if (!col) return false
  return duplicateFields.value.includes(col)
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  uploadedFileName.value = selectedFile.value?.name ?? ''
  error.value = ''
  if (selectedFile.value) doInspect()
}

async function doInspect() {
  if (!selectedFile.value) return
  inspecting.value = true
  error.value = ''
  try {
    const { data } = await runsApi.inspectMasterdata(props.run.id, selectedFile.value)
    inspectResult.value = data
    // Pre-fill mapping from suggestions
    const mapping: Record<string, string> = {}
    for (const field of data.schema_fields) {
      const sug = data.suggestions.find(s => s.suggested_target === field.name)
      mapping[field.name] = sug?.source_column ?? ''
    }
    userMapping.value = mapping
    step.value = 'mapping'
  } catch (e: unknown) {
    error.value = (e as Error).message || 'Failed to read file.'
  } finally {
    inspecting.value = false
  }
}

async function doQuality() {
  running.value = true
  error.value = ''
  try {
    await runsApi.runQualityWithMapping(props.run.id, null, userMapping.value)
    emit('refreshed')
    notify.push({
      type: 'success',
      title: 'Import complete',
      message: `${uploadedFileName.value} · ${mappingSummary.value.length} columns mapped`,
    })
    emit('navigate', 'quality')
  } catch (e: unknown) {
    const msg = (e as Error).message || 'Quality check failed.'
    error.value = msg
    notify.push({ type: 'error', title: 'Quality check failed', message: msg })
  } finally {
    running.value = false
  }
}

function reset() {
  step.value = 'upload'
  selectedFile.value = null
  inspectResult.value = null
  userMapping.value = {}
  error.value = ''
  uploadedFileName.value = ''
  if (fileInput.value) fileInput.value.value = ''
}
</script>
