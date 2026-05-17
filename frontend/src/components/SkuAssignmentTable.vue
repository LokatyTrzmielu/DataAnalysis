<template>
  <div ref="rootRef">
    <!-- Header bar: title (optional) + counter -->
    <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
      <p v-if="title" style="font-size:13px;font-weight:600;color:var(--app-text);margin:0">
        {{ title }}
      </p>
      <span v-else></span>
      <span style="font-size:12px;color:var(--app-text-sec)">
        Showing {{ Math.min(visibleCount, filtered.length).toLocaleString() }} of
        {{ filtered.length.toLocaleString() }} SKUs (filtered) ·
        {{ baseAssignments.length.toLocaleString() }} {{ mode === 'imputed-only' ? 'imputed' : '' }} total
      </span>
    </div>

    <div class="overflow-x-auto" style="border:1px solid var(--app-border);border-radius:10px">
      <table class="w-full" style="font-size:12px;border-collapse:collapse;table-layout:fixed">
        <colgroup>
          <col style="width:24%" />
          <col style="width:14%" />
          <col style="width:9%" />
          <col style="width:7%" />
          <col style="width:13%" />
          <col style="width:15%" />
          <col style="width:9%" />
          <col style="width:9%" />
        </colgroup>
        <thead style="background:var(--table-header-bg)">
          <tr>
            <th class="filterable-th px-2 py-2 text-left">
              <span class="th-label" :class="{ active: !!search }">SKU</span>
              <button
                ref="trigSku"
                type="button"
                class="filter-trigger"
                :class="{ active: !!search, open: openFilter === 'sku' }"
                :title="search ? `SKU filter: ${search}` : 'Filter by SKU'"
                @click.stop="toggleFilter('sku', $event)"
              >▾</button>
            </th>
            <th class="filterable-th px-2 py-2 text-right">
              <span class="th-label" :class="{ active: mode === 'all' && !!imputedFilter }">Dimensions mm</span>
              <button
                v-if="mode === 'all'"
                ref="trigImputed"
                type="button"
                class="filter-trigger"
                :class="{ active: !!imputedFilter, open: openFilter === 'imputed' }"
                :title="imputedFilter ? `Status: ${imputedLabel(imputedFilter)}` : 'Filter by imputation status'"
                @click.stop="toggleFilter('imputed', $event)"
              >▾</button>
            </th>
            <th class="px-2 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Waga kg</th>
            <th class="filterable-th px-2 py-2 text-center">
              <span class="th-label" :class="{ active: !!abcFilter }">ABC</span>
              <button
                ref="trigAbc"
                type="button"
                class="filter-trigger"
                :class="{ active: !!abcFilter, open: openFilter === 'abc' }"
                :title="abcFilter ? `ABC filter: ${abcFilter}` : 'Filter by ABC class'"
                @click.stop="toggleFilter('abc', $event)"
              >▾</button>
            </th>
            <th class="filterable-th px-2 py-2 text-center">
              <span class="th-label" :class="{ active: !!recommendationFilter }">Recom.</span>
              <button
                ref="trigRec"
                type="button"
                class="filter-trigger"
                :class="{ active: !!recommendationFilter, open: openFilter === 'rec' }"
                :title="recommendationFilter ? `Recommendation: ${recommendationFilter}` : 'Filter by recommendation'"
                @click.stop="toggleFilter('rec', $event)"
              >▾</button>
            </th>
            <th class="filterable-th px-2 py-2 text-left">
              <span class="th-label" :class="{ active: !!assignmentFilter }">Variant</span>
              <button
                ref="trigAsn"
                type="button"
                class="filter-trigger"
                :class="{ active: !!assignmentFilter, open: openFilter === 'asn' }"
                :title="assignmentFilter ? `Assignment: ${assignmentFilter}` : 'Filter by assignment'"
                @click.stop="toggleFilter('asn', $event)"
              >▾</button>
            </th>
            <th class="px-2 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Locations</th>
            <th class="px-2 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Fill</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in visibleRows"
            :key="row.sku"
            style="border-top:1px solid var(--table-divider)"
          >
            <td class="px-2 py-1.5 cell-truncate" style="color:var(--app-text)" :title="rowTitle(row)">
              {{ row.sku }}
              <span
                v-if="row.fit_status === 'BORDERLINE'"
                class="chip-borderline"
                title="This SKU fits MiB with a small margin only (BORDERLINE from the Capacity analysis)."
              >borderline</span>
              <span
                v-if="row.dimensions_imputed"
                class="chip-imputed"
                title="Dimensions imputed with the median from the dataset."
              >imputed</span>
            </td>
            <td class="px-2 py-1.5 text-right cell-truncate" style="color:var(--app-text-sec)">
              {{ Math.round(row.length_mm) }}×{{ Math.round(row.width_mm) }}×{{ Math.round(row.height_mm) }}
            </td>
            <td class="px-2 py-1.5 text-right" style="color:var(--app-text-sec)">{{ row.weight_kg.toFixed(2) }}</td>
            <td class="px-2 py-1.5 text-center">
              <span v-if="row.abc_class" :class="`abc-chip abc-${row.abc_class}`">
                {{ row.abc_class }}
              </span>
              <span v-else style="color:var(--app-text-sec)">—</span>
            </td>
            <td class="px-2 py-1.5 text-center cell-truncate" style="color:var(--app-text-sec);font-size:11px" :title="row.recommendation || ''">
              {{ row.recommendation || '—' }}
            </td>
            <td class="px-2 py-1.5 cell-truncate" :title="row.variant_code || ''">
              <span v-if="row.variant_code" style="color:var(--app-text);font-family:monospace;font-size:11.5px">
                {{ row.variant_code }}
              </span>
              <span v-else style="color:#ef4444;font-size:11px" :title="row.orphan_reason || ''">
                {{ row.orphan_reason === 'missing_dimensions' ? 'missing dimensions' : 'no variant' }}
              </span>
            </td>
            <td class="px-2 py-1.5 text-right" style="color:var(--app-text)">{{ row.locations }}</td>
            <td class="px-2 py-1.5 text-right" style="color:var(--app-text-sec)">
              {{ row.cell_fill_pct.toFixed(0) }}%
            </td>
          </tr>
          <tr v-if="visibleRows.length === 0">
            <td colspan="8" class="px-2 py-6 text-center" style="color:var(--app-text-sec)">
              {{ baseAssignments.length === 0 ? emptyMessage : 'No SKUs match the filters.' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="filtered.length > pageSize" class="flex items-center justify-center mt-3">
      <button
        v-if="visibleCount < filtered.length"
        class="btn-apple-pill"
        style="font-size:12px"
        @click="loadAll"
      >Load all ({{ (filtered.length - visibleCount).toLocaleString() }} remaining)</button>
      <button
        v-else
        class="btn-apple-pill"
        style="font-size:12px"
        @click="collapse"
      >Collapse to {{ pageSize }} rows</button>
    </div>

    <!-- Filter popover: teleported to body so it isn't clipped by the table's
         overflow-x-auto wrapper. Position is recomputed from the trigger rect
         whenever the popover opens (and on scroll / resize while open). -->
    <Teleport to="body">
      <div
        v-if="openFilter"
        class="filter-pop"
        :style="popStyle"
        role="dialog"
        @click.stop
      >
        <template v-if="openFilter === 'sku'">
          <p class="pop-title">Filter SKU</p>
          <input
            v-model="search"
            type="text"
            placeholder="Search…"
            class="input-apple-sm"
            style="width:100%"
          />
        </template>

        <template v-else-if="openFilter === 'imputed'">
          <p class="pop-title">Imputation status</p>
          <label class="pop-radio"><input type="radio" value="" v-model="imputedFilter" /> All</label>
          <label class="pop-radio"><input type="radio" value="imputed" v-model="imputedFilter" /> Imputed only</label>
          <label class="pop-radio"><input type="radio" value="not_imputed" v-model="imputedFilter" /> Not imputed only</label>
        </template>

        <template v-else-if="openFilter === 'abc'">
          <p class="pop-title">ABC class</p>
          <label class="pop-radio"><input type="radio" value="" v-model="abcFilter" /> All</label>
          <label
            v-for="c in (['A','B','C'] as const)"
            :key="c"
            class="pop-radio"
            :class="{ disabled: !isAbcAllowed(c) }"
          >
            <input type="radio" :value="c" v-model="abcFilter" :disabled="!isAbcAllowed(c)" />
            Only {{ c }}
            <span v-if="!isAbcAllowed(c)" class="pop-hint">(not selected in Calculation tab)</span>
          </label>
        </template>

        <template v-else-if="openFilter === 'rec'">
          <p class="pop-title">Recommendation</p>
          <label class="pop-radio"><input type="radio" value="" v-model="recommendationFilter" /> All</label>
          <label class="pop-radio"><input type="radio" value="Machine" v-model="recommendationFilter" /> Machine</label>
          <label class="pop-radio"><input type="radio" value="Non-machine" v-model="recommendationFilter" /> Non-machine</label>
        </template>

        <template v-else-if="openFilter === 'asn'">
          <p class="pop-title">Assignment</p>
          <label class="pop-radio"><input type="radio" value="" v-model="assignmentFilter" /> All</label>
          <label class="pop-radio"><input type="radio" value="assigned" v-model="assignmentFilter" /> Assigned</label>
          <label class="pop-radio"><input type="radio" value="orphan" v-model="assignmentFilter" /> Unassigned</label>
        </template>

        <div class="pop-actions">
          <button type="button" class="btn-apple-pill pop-btn" @click="clearCurrentFilter">Clear</button>
          <button type="button" class="btn-apple-pill pop-btn" @click="openFilter = null">Close</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { AssignmentRow } from '@/api/containerOrder'

type FilterKey = 'sku' | 'imputed' | 'abc' | 'rec' | 'asn'

const props = withDefaults(defineProps<{
  assignments: AssignmentRow[]
  /** Whitelist from the Calculation tab. Empty/undefined = no restriction (all classes allowed). */
  selectedAbcClasses?: string[]
  /** 'all' shows every SKU; 'imputed-only' pre-filters to dimensions_imputed=true
   *  and hides the imputation filter (everything is already imputed). */
  mode?: 'all' | 'imputed-only'
  /** Optional table title shown above the header bar. */
  title?: string
}>(), {
  selectedAbcClasses: () => [],
  mode: 'all',
  title: '',
})

const rootRef = ref<HTMLElement | null>(null)
const trigSku = ref<HTMLButtonElement | null>(null)
const trigImputed = ref<HTMLButtonElement | null>(null)
const trigAbc = ref<HTMLButtonElement | null>(null)
const trigRec = ref<HTMLButtonElement | null>(null)
const trigAsn = ref<HTMLButtonElement | null>(null)

const search = ref('')
const abcFilter = ref('')
const imputedFilter = ref('')             // '' | 'imputed' | 'not_imputed'
const recommendationFilter = ref('')      // '' | 'Machine' | 'Non-machine'
const assignmentFilter = ref('')          // '' | 'assigned' | 'orphan'

const openFilter = ref<FilterKey | null>(null)
const popPos = ref<{ top: number; left: number } | null>(null)

const pageSize = 20
const visibleCount = ref(pageSize)

const baseAssignments = computed<AssignmentRow[]>(() => {
  if (props.mode === 'imputed-only') {
    return props.assignments.filter(a => a.dimensions_imputed)
  }
  return props.assignments
})

const emptyMessage = computed(() =>
  props.mode === 'imputed-only'
    ? 'No SKUs with imputed dimensions in this plan.'
    : 'No SKUs in this plan.',
)

function isAbcAllowed(cls: 'A' | 'B' | 'C'): boolean {
  if (!props.selectedAbcClasses || props.selectedAbcClasses.length === 0) return true
  return props.selectedAbcClasses.includes(cls)
}

function imputedLabel(v: string): string {
  if (v === 'imputed') return 'Imputed only'
  if (v === 'not_imputed') return 'Not imputed only'
  return 'All'
}

// Reset ABC filter if user tightens params and the chosen ABC is no longer allowed.
watch(() => props.selectedAbcClasses, () => {
  if (abcFilter.value && !isAbcAllowed(abcFilter.value as 'A' | 'B' | 'C')) {
    abcFilter.value = ''
  }
}, { deep: true })

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return baseAssignments.value.filter(r => {
    if (q && !r.sku.toLowerCase().includes(q)) return false
    if (abcFilter.value && r.abc_class !== abcFilter.value) return false
    if (imputedFilter.value === 'imputed' && !r.dimensions_imputed) return false
    if (imputedFilter.value === 'not_imputed' && r.dimensions_imputed) return false
    if (recommendationFilter.value && r.recommendation !== recommendationFilter.value) return false
    if (assignmentFilter.value === 'assigned' && !r.variant_code) return false
    if (assignmentFilter.value === 'orphan' && r.variant_code) return false
    return true
  })
})

const visibleRows = computed(() => filtered.value.slice(0, visibleCount.value))

// Reset the visible window whenever filters change.
watch([search, abcFilter, imputedFilter, recommendationFilter, assignmentFilter,
       () => props.assignments, () => props.mode], () => {
  visibleCount.value = pageSize
})

function loadAll() {
  visibleCount.value = filtered.value.length
}
function collapse() {
  visibleCount.value = pageSize
}

function rowTitle(row: AssignmentRow): string {
  if (row.dimensions_imputed) return `${row.sku} (dimensions imputed via median)`
  return row.sku
}

function triggerFor(key: FilterKey): HTMLButtonElement | null {
  switch (key) {
    case 'sku': return trigSku.value
    case 'imputed': return trigImputed.value
    case 'abc': return trigAbc.value
    case 'rec': return trigRec.value
    case 'asn': return trigAsn.value
  }
}

const POP_WIDTH = 240
const POP_MARGIN = 8

function computePopPos(key: FilterKey) {
  const el = triggerFor(key)
  if (!el) {
    popPos.value = null
    return
  }
  const rect = el.getBoundingClientRect()
  // Clamp left so popover doesn't overflow viewport on the right.
  const maxLeft = window.innerWidth - POP_WIDTH - POP_MARGIN
  const left = Math.min(Math.max(POP_MARGIN, rect.left), maxLeft)
  popPos.value = { top: rect.bottom + 6, left }
}

const popStyle = computed(() => {
  if (!popPos.value) return { display: 'none' }
  return {
    position: 'fixed' as const,
    top: `${popPos.value.top}px`,
    left: `${popPos.value.left}px`,
    width: `${POP_WIDTH}px`,
  }
})

function toggleFilter(key: FilterKey, _e: MouseEvent) {
  if (openFilter.value === key) {
    openFilter.value = null
    return
  }
  openFilter.value = key
  nextTick(() => computePopPos(key))
}

function clearCurrentFilter() {
  switch (openFilter.value) {
    case 'sku': search.value = ''; break
    case 'imputed': imputedFilter.value = ''; break
    case 'abc': abcFilter.value = ''; break
    case 'rec': recommendationFilter.value = ''; break
    case 'asn': assignmentFilter.value = ''; break
  }
}

function onDocClick(_e: MouseEvent) {
  // Trigger buttons and the popover stop propagation themselves; if the click
  // bubbles all the way up to document, it was an outside click → close.
  if (openFilter.value) openFilter.value = null
}
function onScrollOrResize() {
  if (openFilter.value) computePopPos(openFilter.value)
}
function onEscape(e: KeyboardEvent) {
  if (e.key === 'Escape') openFilter.value = null
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onEscape)
  window.addEventListener('scroll', onScrollOrResize, true)
  window.addEventListener('resize', onScrollOrResize)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onEscape)
  window.removeEventListener('scroll', onScrollOrResize, true)
  window.removeEventListener('resize', onScrollOrResize)
})
</script>

<style scoped>
.cell-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ABC class chips — explicit light + dark variants so they don't look like
   bleached stickers on dark backgrounds. */
.abc-chip {
  display: inline-block;
  font-size: 10.5px;
  font-weight: 600;
  padding: 1px 6px;
  line-height: 16px;
  border-radius: 4px;
}
.abc-A { background: #dcfce7; color: #15803d; }
.abc-B { background: #fef3c7; color: #a16207; }
.abc-C { background: #f3f4f6; color: #6b7280; }
:global(html.dark) .abc-A { background: rgba(34, 197, 94, 0.18); color: #86efac; }
:global(html.dark) .abc-B { background: rgba(245, 158, 11, 0.18); color: #fcd34d; }
:global(html.dark) .abc-C { background: rgba(148, 163, 184, 0.18); color: #cbd5e1; }

/* "Imputed" chip next to SKU. */
.chip-imputed {
  display: inline-block;
  font-size: 9.5px;
  font-weight: 600;
  line-height: 14px;
  background: #fef3c7;
  color: #92400e;
  border-radius: 4px;
  padding: 0 4px;
  margin-left: 4px;
  vertical-align: middle;
}
:global(html.dark) .chip-imputed {
  background: rgba(245, 158, 11, 0.2);
  color: #fcd34d;
}

/* "Borderline" chip — same chip shape as "imputed", different colour so the
   two read as distinct hazards at a glance. */
.chip-borderline {
  display: inline-block;
  font-size: 9.5px;
  font-weight: 600;
  line-height: 14px;
  background: #ffedd5;
  color: #9a3412;
  border-radius: 4px;
  padding: 0 4px;
  margin-left: 4px;
  vertical-align: middle;
}
:global(html.dark) .chip-borderline {
  background: rgba(249, 115, 22, 0.22);
  color: #fdba74;
}

/* ───────── Excel-style header filters ───────── */

.filterable-th {
  color: var(--app-text-sec);
  font-weight: 500;
  white-space: nowrap;
}
.th-label { transition: color 0.12s; }
.th-label.active { color: #0071e3; font-weight: 600; }

.filter-trigger {
  appearance: none;
  background: transparent;
  border: none;
  padding: 0 4px;
  margin-left: 2px;
  font-size: 10px;
  line-height: 1;
  color: var(--app-text-sec);
  cursor: pointer;
  border-radius: 3px;
  transition: background 0.12s, color 0.12s;
}
.filter-trigger:hover { background: rgba(0, 113, 227, 0.08); color: var(--app-text); }
.filter-trigger.active { color: #0071e3; font-weight: 700; }
.filter-trigger.open { background: rgba(0, 113, 227, 0.12); color: #0071e3; }
</style>

<!-- Teleported popover styles must be NON-scoped so they apply outside the
     component's DOM tree (in <body>). -->
<style>
.filter-pop {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 8px;
  padding: 10px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
  z-index: 1000;
  font-size: 12.5px;
  color: var(--app-text);
}
.filter-pop .pop-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-transform: uppercase;
  color: var(--app-text-sec);
  margin: 0 0 8px;
}
.filter-pop .pop-radio {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: var(--app-text);
  cursor: pointer;
  padding: 3px 0;
}
.filter-pop .pop-radio.disabled {
  color: var(--app-text-sec);
  opacity: 0.5;
  cursor: not-allowed;
}
.filter-pop .pop-hint {
  font-size: 10.5px;
  color: var(--app-text-sec);
  margin-left: 4px;
}
.filter-pop .pop-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 10px;
}
.filter-pop .pop-btn {
  font-size: 11.5px;
  padding: 4px 10px;
}
</style>
