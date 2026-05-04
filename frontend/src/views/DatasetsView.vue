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
            class="hidden"
            @change="onFileChange"
          />
          <div class="flex items-center gap-2">
            <button @click="fileInputRef?.click()" class="btn-apple-pill" style="font-size:13px">Choose file</button>
            <span v-if="selectedFile" class="text-xs truncate" style="color:var(--app-text-sec);max-width:160px">{{ selectedFile.name }}</span>
            <span v-else class="text-xs" style="color:var(--app-placeholder)">No file chosen</span>
          </div>
        </div>
        <div>
          <label class="label-apple" style="font-size:12px">Data type</label>
          <select v-model="importType" class="input-apple-sm" style="cursor:pointer">
            <option value="masterdata">Masterdata</option>
            <option value="orders">Orders</option>
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
        @mouseover="(e) => (e.currentTarget as HTMLElement).style.background='var(--table-row-hover)'"
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
                  ? 'font-size:11px;background:var(--badge-blue-bg);color:var(--badge-blue-color)'
                  : 'font-size:11px;background:var(--badge-green-bg);color:var(--badge-green-color)'"
              >
                {{ ds.file_type }}
              </span>
              <span style="font-size:12px;color:var(--app-text-sec)">{{ ds.row_count.toLocaleString() }} rows</span>
              <span style="font-size:12px;color:var(--app-text-sec)">{{ ds.size_mb }} MB</span>
            </div>
          </div>
        </div>

        <!-- Right: date + id + notes icon + delete -->
        <div class="flex items-center gap-4 flex-shrink-0">
          <span style="font-size:12px;color:var(--app-text-sec)">{{ formatDate(ds.created_at) }}</span>
          <span
            class="rounded px-1.5 py-0.5 font-mono"
            style="font-size:10px;background:var(--badge-default-bg);color:var(--app-text-sec);letter-spacing:0"
            :title="ds.id"
          >
            {{ ds.id.slice(0, 8) }}…
          </span>
          <button
            @click="openNotes(ds)"
            class="p-1.5 rounded transition-colors"
            :style="ds.notes ? 'color:#0071e3' : 'color:var(--app-placeholder)'"
            title="Notes"
          >
            <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
            </svg>
          </button>
          <!-- Delete / confirm -->
          <template v-if="confirmDeleteId === ds.id">
            <span class="text-xs mr-1" style="color:var(--app-text-sec)">Delete?</span>
            <button @click="doDelete(ds.id, ds.name)" class="text-xs font-medium mr-1" style="color:#ff3b30">Yes</button>
            <button @click="confirmDeleteId = null" class="text-xs" style="color:var(--app-text-sec)">No</button>
          </template>
          <button
            v-else
            @click="confirmDeleteId = ds.id"
            class="p-1.5 rounded transition-colors"
            style="color:var(--app-placeholder)"
            @mouseover="(e) => (e.currentTarget as HTMLElement).style.color='#ff3b30'"
            @mouseleave="(e) => (e.currentTarget as HTMLElement).style.color='var(--app-placeholder)'"
            title="Delete"
          >
            <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Notes modal -->
    <div
      v-if="notesDataset"
      class="fixed inset-0 flex items-center justify-center z-50"
      style="background:rgba(0,0,0,0.6)"
      @click.self="closeNotes"
    >
      <div class="card-apple-elevated w-full" style="max-width:480px">
        <div class="flex items-center justify-between mb-5">
          <h3 style="font-size:21px;font-weight:700;color:var(--app-text);letter-spacing:0.231px;line-height:1.19">Notes</h3>
          <button
            @click="closeNotes"
            style="color:var(--app-placeholder);background:none;border:none;cursor:pointer;padding:4px;transition:color 0.15s"
            @mouseover="(e: Event) => (e.currentTarget as HTMLElement).style.color='var(--app-text)'"
            @mouseleave="(e: Event) => (e.currentTarget as HTMLElement).style.color='var(--app-placeholder)'"
          >
            <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
            </svg>
          </button>
        </div>
        <textarea
          v-model="notesValue"
          @input="scheduleNotesSave"
          placeholder="Add notes about this dataset…"
          rows="5"
          class="input-apple resize-none"
          style="font-size:14px;letter-spacing:-0.224px"
        />
        <div class="mt-2 h-4">
          <span v-if="notesSaved" style="font-size:12px;color:#34c759">Saved</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { datasetsApi, type Dataset } from '@/api/datasets'
import { useNotificationsStore } from '@/stores/notifications'

const notify = useNotificationsStore()

const datasets = ref<Dataset[]>([])
const loading = ref(false)
const confirmDeleteId = ref<string | null>(null)

// ── Notes modal ───────────────────────────────────────────────────────────────

const notesDataset = ref<Dataset | null>(null)
const notesValue = ref('')
const notesSaved = ref(false)
let notesTimer: ReturnType<typeof setTimeout> | null = null

function openNotes(ds: Dataset) {
  notesDataset.value = ds
  notesValue.value = ds.notes ?? ''
  notesSaved.value = false
}

function closeNotes() {
  if (notesTimer) clearTimeout(notesTimer)
  notesDataset.value = null
}

function scheduleNotesSave() {
  notesSaved.value = false
  if (notesTimer) clearTimeout(notesTimer)
  notesTimer = setTimeout(async () => {
    if (!notesDataset.value) return
    try {
      const notes = notesValue.value.trim() || null
      const { data } = await datasetsApi.patch(notesDataset.value.id, notes)
      const idx = datasets.value.findIndex(d => d.id === data.id)
      if (idx !== -1) datasets.value[idx] = data
      if (notesDataset.value) notesDataset.value = data
      notesSaved.value = true
      notify.push({ type: 'success', title: 'Notes saved' })
      setTimeout(() => { notesSaved.value = false }, 2000)
    } catch {
      notify.push({ type: 'error', title: 'Failed to save notes' })
    }
  }, 500)
}

onUnmounted(() => { if (notesTimer) clearTimeout(notesTimer) })

// ── Import form ───────────────────────────────────────────────────────────────

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
  try {
    await datasetsApi.delete(id)
    datasets.value = datasets.value.filter(d => d.id !== id)
    confirmDeleteId.value = null
    notify.push({ type: 'success', title: 'Dataset deleted', message: name })
  } catch {
    notify.push({ type: 'error', title: 'Failed to delete dataset' })
  }
}

onMounted(loadDatasets)
</script>
