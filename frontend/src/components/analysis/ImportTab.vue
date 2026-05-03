<template>
  <div class="space-y-6">

    <!-- ── Masterdata Section ── -->
    <div class="card-apple">
      <div class="flex items-center justify-between mb-3">
        <h3 style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Masterdata</h3>
        <span v-if="run.quality_result" class="flex items-center gap-1 text-xs text-green-600 font-medium">
          <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          Imported
        </span>
      </div>

      <!-- Done state -->
      <div v-if="run.quality_result && mdStep === 'done'" class="space-y-2">
        <p class="text-xs text-gray-600"><code>{{ mdUploadedFileName || mdFileName }}</code></p>
        <button @click="mdStep = 'upload'" class="text-xs text-gray-400 hover:text-gray-600 underline">Re-upload</button>
      </div>

      <!-- Step: upload -->
      <div v-else-if="mdStep === 'upload'">
        <p class="text-xs text-gray-500 mb-4">
          Upload an Excel (XLSX) or CSV file with product dimensions, weight, and stock data.
        </p>
        <input
          ref="mdFileInput"
          type="file"
          accept=".xlsx,.xls,.csv"
          class="block text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-600 hover:file:bg-blue-100"
          @change="onMdFileChange"
        />
        <p v-if="mdInspecting" class="text-xs text-gray-500 mt-3">Reading file…</p>
        <p v-if="mdError" class="text-red-600 text-sm mt-3">{{ mdError }}</p>
        <p v-if="run.masterdata_path && !mdSelectedFile" class="text-xs text-gray-400 mt-4">
          Previously uploaded: <code>{{ mdFileName }}</code>
        </p>
      </div>

      <!-- Step: mapping -->
      <div v-else-if="mdStep === 'mapping' && mdInspectResult" class="space-y-4">
        <div class="bg-white rounded">
          <div class="flex items-center justify-between mb-4">
            <p class="text-xs font-medium text-gray-600">Map columns</p>
            <button @click="mdStep = 'upload'" class="text-xs text-gray-400 hover:text-gray-600">← Back</button>
          </div>

          <!-- Required fields -->
          <div class="mb-4">
            <p class="text-xs font-semibold uppercase tracking-wide text-gray-700 mb-2">Required fields</p>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div v-for="field in mdRequiredFields" :key="field.name" class="flex flex-col gap-1">
                <label class="text-xs text-gray-600">
                  {{ field.name }}
                  <span v-if="mdIsDuplicate(field.name)" class="text-yellow-600 ml-1" title="Duplicate mapping">⚠</span>
                  <span v-else-if="!mdUserMapping[field.name]" class="text-red-500 ml-1">*</span>
                </label>
                <select
                  v-model="mdUserMapping[field.name]"
                  :class="['w-full text-xs border rounded px-2 py-1', !mdUserMapping[field.name] ? 'border-red-300 bg-red-50' : 'border-gray-300']"
                >
                  <option value="">— not mapped —</option>
                  <option v-for="col in mdInspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Optional fields (collapsible) -->
          <details class="mb-4">
            <summary class="text-xs font-semibold uppercase tracking-wide text-gray-500 cursor-pointer mb-2">Optional fields</summary>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-2">
              <div v-for="field in mdOptionalFields" :key="field.name" class="flex flex-col gap-1">
                <label class="text-xs text-gray-600">{{ field.name }}</label>
                <select v-model="mdUserMapping[field.name]" class="w-full text-xs border border-gray-300 rounded px-2 py-1">
                  <option value="">— not mapped —</option>
                  <option v-for="col in mdInspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
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
                  <th v-for="col in mdInspectResult.file_columns" :key="col" class="px-2 py-1 text-left text-gray-600 font-medium border-b border-gray-200 whitespace-nowrap">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in mdInspectResult.preview_rows" :key="i" class="border-b border-gray-100">
                  <td v-for="col in mdInspectResult.file_columns" :key="col" class="px-2 py-1 text-gray-700 whitespace-nowrap">{{ row[col] ?? '' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-if="mdMissingRequired.length > 0" class="text-xs text-red-600 mb-3">Missing required: {{ mdMissingRequired.join(', ') }}</p>
          <p v-if="mdDuplicateFields.length > 0" class="text-xs text-yellow-600 mb-3">Duplicate mappings: {{ mdDuplicateFields.join(', ') }}</p>
          <p v-if="mdError" class="text-red-600 text-sm mb-3">{{ mdError }}</p>

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
        <span v-if="run.orders_validation_result" class="flex items-center gap-1 text-xs text-green-600 font-medium">
          <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          Imported
        </span>
      </div>

      <!-- Done state -->
      <div v-if="run.orders_validation_result && ordersStep === 'done'" class="space-y-2">
        <p class="text-xs text-gray-600"><code>{{ ordersUploadedFileName || ordersFileName }}</code></p>
        <button @click="ordersStep = 'upload'" class="text-xs text-gray-400 hover:text-gray-600 underline">Re-upload</button>
      </div>

      <!-- Step: upload -->
      <div v-else-if="ordersStep === 'upload'">
        <p class="text-xs text-gray-500 mb-3">Upload an Excel or CSV file with order lines (order_id, sku, quantity, date).</p>
        <input
          ref="ordersFileInput"
          type="file"
          accept=".xlsx,.xls,.csv"
          class="block text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-600 hover:file:bg-blue-100"
          @change="onOrdersFileChange"
        />
        <p v-if="ordersInspecting" class="text-xs text-gray-500 mt-3">Reading file…</p>
        <p v-if="ordersUploadError" class="text-red-600 text-sm mt-2">{{ ordersUploadError }}</p>
        <p v-if="run.orders_path && !ordersSelectedFile" class="text-xs text-gray-400 mt-4">
          Previously uploaded: <code>{{ ordersFileName }}</code>
        </p>
      </div>

      <!-- Step: mapping -->
      <div v-else-if="ordersStep === 'mapping' && ordersInspectResult">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs font-medium text-gray-600">Map columns</p>
          <button @click="ordersStep = 'upload'" class="text-xs text-gray-400 hover:text-gray-600">← Back</button>
        </div>
        <!-- Required fields -->
        <div class="mb-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-gray-700 mb-2">Required fields</p>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div v-for="field in ordersRequiredFields" :key="field.name" class="flex flex-col gap-1">
              <label class="text-xs text-gray-600">
                {{ field.name }}
                <span v-if="!ordersMapping[field.name]" class="text-red-500 ml-1">*</span>
              </label>
              <select
                v-model="ordersMapping[field.name]"
                :class="['w-full text-xs border rounded px-2 py-1', !ordersMapping[field.name] ? 'border-red-300 bg-red-50' : 'border-gray-300']"
              >
                <option value="">— not mapped —</option>
                <option v-for="col in ordersInspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
          </div>
        </div>
        <!-- Optional fields (collapsible) -->
        <details class="mb-4">
          <summary class="text-xs font-semibold uppercase tracking-wide text-gray-500 cursor-pointer mb-2">Optional fields</summary>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-2">
            <div v-for="field in ordersOptionalFields" :key="field.name" class="flex flex-col gap-1">
              <label class="text-xs text-gray-600">{{ field.name }}</label>
              <select v-model="ordersMapping[field.name]" class="w-full text-xs border border-gray-300 rounded px-2 py-1">
                <option value="">— not mapped —</option>
                <option v-for="col in ordersInspectResult.file_columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
          </div>
        </details>
        <!-- Preview -->
        <div class="overflow-x-auto mb-3">
          <table class="text-xs border border-gray-200 rounded w-full">
            <thead class="bg-gray-50">
              <tr>
                <th v-for="col in ordersInspectResult.file_columns" :key="col" class="px-2 py-1 text-left text-gray-600 whitespace-nowrap">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in ordersInspectResult.preview_rows" :key="i" class="border-b border-gray-100">
                <td v-for="col in ordersInspectResult.file_columns" :key="col" class="px-2 py-1 text-gray-700 whitespace-nowrap">{{ row[col] ?? '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="ordersMissingRequired.length > 0" class="text-xs text-red-600 mb-2">Missing required: {{ ordersMissingRequired.join(', ') }}</p>
        <p v-if="ordersUploadError" class="text-red-600 text-sm mb-2">{{ ordersUploadError }}</p>
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
import { useNotificationsStore } from '@/stores/notifications'

const notify = useNotificationsStore()

const props = defineProps<{ run: RunDetail }>()
const emit = defineEmits<{
  (e: 'refreshed'): void
  (e: 'navigate', tab: string): void
}>()

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

const mdFileName = computed(() => {
  if (!props.run.masterdata_path) return ''
  return props.run.masterdata_path.split(/[\\/]/).pop() ?? ''
})

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
    mdError.value = (e as Error).message || 'Failed to read file.'
  } finally {
    mdInspecting.value = false
  }
}

async function doMdQuality() {
  mdRunning.value = true
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
    const msg = (e as Error).message || 'Quality check failed.'
    mdError.value = msg
    notify.push({ type: 'error', title: 'Quality check failed', message: msg })
  } finally {
    mdRunning.value = false
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

const ordersFileName = computed(() => {
  if (!props.run.orders_path) return ''
  return props.run.orders_path.split(/[\\/]/).pop() ?? ''
})

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
    ordersUploadError.value = (e as Error).message || 'Failed to read file.'
  } finally {
    ordersInspecting.value = false
  }
}

async function doOrdersIngest() {
  ordersIngesting.value = true
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
    const msg = (e as Error).message || 'Ingestion failed.'
    ordersUploadError.value = msg
    notify.push({ type: 'error', title: 'Import failed', message: msg })
  } finally {
    ordersIngesting.value = false
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
