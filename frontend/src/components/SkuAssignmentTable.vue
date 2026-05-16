<template>
  <div>
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <input
        v-model="search"
        type="text"
        placeholder="Szukaj SKU…"
        class="input-apple-sm"
        style="width:200px"
      />
      <select v-model="abcFilter" class="input-apple-sm" style="width:130px">
        <option value="">ABC: wszystkie</option>
        <option value="A">tylko A</option>
        <option value="B">tylko B</option>
        <option value="C">tylko C</option>
      </select>
      <select v-model="statusFilter" class="input-apple-sm" style="width:170px">
        <option value="">Status: wszystkie</option>
        <option value="assigned">Przypisane</option>
        <option value="orphan">Bez przypisania</option>
      </select>
      <span class="ml-auto" style="font-size:12px;color:var(--app-text-sec)">
        {{ filtered.length.toLocaleString() }} / {{ assignments.length.toLocaleString() }} SKU
      </span>
    </div>

    <div class="overflow-x-auto" style="border:1px solid var(--app-border);border-radius:10px">
      <table class="w-full" style="font-size:12px;border-collapse:collapse">
        <thead style="background:var(--table-header-bg)">
          <tr>
            <th class="px-2 py-2 text-left" style="color:var(--app-text-sec);font-weight:500">SKU</th>
            <th class="px-2 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Wymiary mm</th>
            <th class="px-2 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Waga kg</th>
            <th class="px-2 py-2 text-center" style="color:var(--app-text-sec);font-weight:500">ABC</th>
            <th class="px-2 py-2 text-center" style="color:var(--app-text-sec);font-weight:500">Rekom.</th>
            <th class="px-2 py-2 text-left" style="color:var(--app-text-sec);font-weight:500">Wariant</th>
            <th class="px-2 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Lokacji</th>
            <th class="px-2 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Wypeł.</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in pageRows"
            :key="row.sku"
            style="border-top:1px solid var(--table-divider)"
          >
            <td class="px-2 py-1.5" style="color:var(--app-text)">{{ row.sku }}</td>
            <td class="px-2 py-1.5 text-right" style="color:var(--app-text-sec)">
              {{ Math.round(row.length_mm) }}×{{ Math.round(row.width_mm) }}×{{ Math.round(row.height_mm) }}
            </td>
            <td class="px-2 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.weight_kg.toFixed(2) }}</td>
            <td class="px-2 py-1.5 text-center">
              <span v-if="row.abc_class" :style="abcChipStyle(row.abc_class)" class="rounded px-1.5">
                {{ row.abc_class }}
              </span>
              <span v-else style="color:var(--app-text-sec)">—</span>
            </td>
            <td class="px-2 py-1.5 text-center" style="color:var(--app-text-sec);font-size:11px">
              {{ row.recommendation || '—' }}
            </td>
            <td class="px-2 py-1.5">
              <span v-if="row.variant_code" style="color:var(--app-text);font-family:monospace;font-size:11.5px">
                {{ row.variant_code }}
              </span>
              <span v-else style="color:#ef4444;font-size:11px">brak wariantu</span>
            </td>
            <td class="px-2 py-1.5 text-right" style="color:var(--app-text)">{{ row.locations }}</td>
            <td class="px-2 py-1.5 text-right" style="color:var(--app-text-sec)">
              {{ row.cell_fill_pct.toFixed(0) }}%
            </td>
          </tr>
          <tr v-if="pageRows.length === 0">
            <td colspan="8" class="px-2 py-6 text-center" style="color:var(--app-text-sec)">
              Brak SKU pasujących do filtrów.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="filtered.length > pageSize" class="flex items-center justify-between mt-3">
      <button
        class="btn-apple-pill"
        :disabled="page === 1"
        style="font-size:12px"
        @click="page = Math.max(1, page - 1)"
      >← Poprzednia</button>
      <span style="font-size:12px;color:var(--app-text-sec)">
        Strona {{ page }} z {{ totalPages }}
      </span>
      <button
        class="btn-apple-pill"
        :disabled="page === totalPages"
        style="font-size:12px"
        @click="page = Math.min(totalPages, page + 1)"
      >Następna →</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { AssignmentRow } from '@/api/containerOrder'

const props = defineProps<{ assignments: AssignmentRow[] }>()

const search = ref('')
const abcFilter = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = 100

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return props.assignments.filter(r => {
    if (q && !r.sku.toLowerCase().includes(q)) return false
    if (abcFilter.value && r.abc_class !== abcFilter.value) return false
    if (statusFilter.value === 'assigned' && !r.variant_code) return false
    if (statusFilter.value === 'orphan' && r.variant_code) return false
    return true
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))
const pageRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filtered.value.slice(start, start + pageSize)
})

watch([filtered, totalPages], () => {
  if (page.value > totalPages.value) page.value = totalPages.value
})

function abcChipStyle(cls: string): string {
  const colors: Record<string, string> = {
    A: 'background:#dcfce7;color:#15803d',
    B: 'background:#fef3c7;color:#a16207',
    C: 'background:#f3f4f6;color:#6b7280',
  }
  return `font-size:10.5px;font-weight:600;padding:1px 6px;line-height:16px;${colors[cls] || ''}`
}
</script>
