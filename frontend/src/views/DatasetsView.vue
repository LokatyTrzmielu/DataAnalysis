<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:var(--app-text);line-height:1.14;letter-spacing:-0.28px">
        Datasets
      </h2>
      <button @click="showForm = !showForm" class="btn-apple-primary">
        {{ showForm ? 'Cancel' : 'Import dataset' }}
      </button>
    </div>

    <!-- Import form -->
    <div v-if="showForm" class="card-apple mb-6">
      <h3 class="mb-4" style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">Import new dataset</h3>
      <div class="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label class="label-apple" style="font-size:12px">File (XLSX or CSV)</label>
          <input
            ref="fileInputRef"
            type="file"
            accept=".xlsx,.xls,.csv"
            class="input-apple-sm"
            style="cursor:pointer"
            @change="onFileChange"
          />
        </div>
        <div>
          <label class="label-apple" style="font-size:12px">Data type</label>
          <select v-model="importType" class="input-apple-sm" style="cursor:pointer">
            <option value="masterdata">Masterdata (SKU dimensions)</option>
            <option value="orders">Orders (order lines)</option>
          </select>
        </div>
      </div>
      <p v-if="importError" class="mb-3" style="font-size:13px;color:#ff3b30">{{ importError }}</p>
      <button
        @click="doImport"
        :disabled="!selectedFile || importing"
        class="btn-apple-primary"
      >
        {{ importing ? 'Importing…' : 'Import' }}
      </button>
    </div>

    <!-- Dataset list -->
    <div v-if="loading" style="font-size:14px;color:var(--app-text-sec)">Loading…</div>
    <div v-else-if="datasets.length === 0" style="font-size:14px;color:var(--app-text-sec)">
      No datasets imported yet. Use "Import dataset" to add one.
    </div>
    <div v-else class="card-apple-list">
      <div
        v-for="ds in datasets"
        :key="ds.id"
        class="flex items-center justify-between px-4 py-3"
        @mouseover="(e) => (e.currentTarget as HTMLElement).style.background='rgba(0,0,0,0.02)'"
        @mouseleave="(e) => (e.currentTarget as HTMLElement).style.background=''"
      >
        <!-- Left: name + badges -->
        <div class="flex items-center gap-3 min-w-0">
          <div class="min-w-0">
            <span style="font-size:15px;font-weight:500;color:var(--app-text);letter-spacing:-0.24px">{{ ds.name }}</span>
            <div class="flex items-center gap-2 mt-0.5">
              <span
                class="rounded px-1.5 py-0.5"
                :style="ds.file_type === 'masterdata'
                  ? 'font-size:11px;background:rgba(0,113,227,0.08);color:#0066cc'
                  : 'font-size:11px;background:rgba(52,199,89,0.1);color:#1a7a38'"
              >
                {{ ds.file_type }}
              </span>
              <span style="font-size:12px;color:var(--app-text-sec)">{{ ds.row_count.toLocaleString() }} rows</span>
              <span style="font-size:12px;color:var(--app-text-sec)">{{ ds.size_mb }} MB</span>
            </div>
          </div>
        </div>

        <!-- Right: date + id + delete -->
        <div class="flex items-center gap-4 flex-shrink-0">
          <span style="font-size:12px;color:var(--app-text-sec)">{{ formatDate(ds.created_at) }}</span>
          <span
            class="rounded px-1.5 py-0.5 font-mono"
            style="font-size:10px;background:rgba(0,0,0,0.05);color:var(--app-text-sec);letter-spacing:0"
            :title="ds.id"
          >
            {{ ds.id.slice(0, 8) }}…
          </span>
          <button
            @click="doDelete(ds.id, ds.name)"
            style="font-size:12px;color:#ff3b30;background:none;border:none;cursor:pointer;padding:0"
            @mouseover="(e) => (e.currentTarget as HTMLElement).style.color='#d93025'"
            @mouseleave="(e) => (e.currentTarget as HTMLElement).style.color='#ff3b30'"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { datasetsApi, type Dataset } from '@/api/datasets'
import { useNotificationsStore } from '@/stores/notifications'

const notify = useNotificationsStore()

const datasets = ref<Dataset[]>([])
const loading = ref(false)

const showForm = ref(false)
const selectedFile = ref<File | null>(null)
const importType = ref<'masterdata' | 'orders'>('masterdata')
const importing = ref(false)
const importError = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  importError.value = ''
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

async function loadDatasets() {
  loading.value = true
  try {
    const { data } = await datasetsApi.list()
    datasets.value = data.datasets
  } catch {
    notify.push({ type: 'error', title: 'Failed to load datasets' })
  } finally {
    loading.value = false
  }
}

async function doImport() {
  if (!selectedFile.value) return
  importing.value = true
  importError.value = ''
  try {
    const { data } = await datasetsApi.import(selectedFile.value, importType.value)
    datasets.value.unshift(data)
    notify.push({
      type: 'success',
      title: 'Dataset imported',
      message: `${data.name} · ${data.row_count.toLocaleString()} rows · ${data.size_mb} MB`,
    })
    showForm.value = false
    selectedFile.value = null
    if (fileInputRef.value) fileInputRef.value.value = ''
  } catch (e: unknown) {
    if (axios.isAxiosError(e) && e.response?.data?.detail) {
      importError.value = e.response.data.detail
    } else {
      importError.value = 'Import failed. Check the file format and try again.'
    }
    notify.push({ type: 'error', title: 'Import failed', message: importError.value })
  } finally {
    importing.value = false
  }
}

async function doDelete(id: string, name: string) {
  if (!confirm(`Delete dataset "${name}"? This cannot be undone.`)) return
  try {
    await datasetsApi.delete(id)
    datasets.value = datasets.value.filter(d => d.id !== id)
    notify.push({ type: 'success', title: 'Dataset deleted', message: name })
  } catch {
    notify.push({ type: 'error', title: 'Failed to delete dataset' })
  }
}

onMounted(loadDatasets)
</script>
