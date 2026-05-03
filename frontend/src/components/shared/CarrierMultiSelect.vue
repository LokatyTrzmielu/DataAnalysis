<template>
  <div ref="rootEl" class="relative">

    <!-- Trigger button -->
    <button
      type="button"
      @click="toggleOpen"
      :class="['cms-trigger', isOpen ? 'is-open' : hasError ? 'is-error' : '']"
    >
      <span :class="props.modelValue.size === 0 ? 'cms-placeholder' : 'cms-value'">
        {{ triggerLabel }}
      </span>
      <svg
        width="12" height="12" viewBox="0 0 12 12" fill="none"
        :class="['cms-chevron', isOpen ? 'rotate-180' : '']"
      >
        <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <!-- Selected chips row -->
    <div v-if="selectedCarriers.length" class="flex flex-wrap gap-1 mt-1.5">
      <span
        v-for="c in selectedCarriers"
        :key="c.carrier_id"
        class="cms-chip"
      >
        <span class="truncate max-w-[140px]">{{ c.name || c.carrier_id }}</span>
        <button
          type="button"
          @click.stop="deselect(c.carrier_id)"
          class="cms-chip-remove"
          aria-label="Remove"
        >×</button>
      </span>
    </div>

    <!-- Validation error -->
    <p v-if="hasError" class="text-xs text-red-500 mt-1">Select at least one carrier</p>

    <!-- Dropdown panel -->
    <div
      v-show="isOpen"
      class="cms-panel"
    >
      <!-- Quick actions -->
      <div class="cms-panel-actions">
        <button type="button" @click="selectAll" class="cms-action-btn is-primary">Select all</button>
        <button type="button" @click="clearAll" class="cms-action-btn">Clear</button>
      </div>

      <!-- Search input -->
      <div class="cms-search-row">
        <input
          ref="searchEl"
          v-model="query"
          type="text"
          placeholder="Search carriers…"
          class="input-apple-sm w-full"
          @keydown.escape.stop="close"
        />
      </div>

      <!-- Carrier list -->
      <ul class="overflow-y-auto" style="max-height: 240px;">
        <li
          v-for="c in filteredCarriers"
          :key="c.carrier_id"
          @click="toggle(c.carrier_id)"
          class="cms-list-item"
        >
          <!-- Custom checkbox -->
          <span :class="['cms-checkbox', props.modelValue.has(c.carrier_id) ? 'is-checked' : '']">
            <svg v-if="props.modelValue.has(c.carrier_id)" width="10" height="8" viewBox="0 0 10 8" fill="none">
              <path d="M1 4l3 3 5-6" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
          <!-- Name + dimensions -->
          <span class="flex flex-col min-w-0">
            <span class="cms-item-name">{{ c.name || c.carrier_id }}</span>
            <span class="cms-item-dims">
              {{ c.inner_length_mm }}×{{ c.inner_width_mm }}×{{ c.inner_height_mm }} mm · max {{ c.max_weight_kg }} kg
            </span>
          </span>
        </li>
        <li v-if="!filteredCarriers.length" class="cms-empty">
          No carriers match "{{ query }}"
        </li>
      </ul>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import type { Carrier } from '@/api/carriers'

const props = defineProps<{
  carriers: Carrier[]
  modelValue: Set<string>
  showError?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: Set<string>): void
}>()

const isOpen = ref(false)
const query = ref('')
const rootEl = ref<HTMLElement>()
const searchEl = ref<HTMLInputElement>()

const selectedCarriers = computed(() =>
  props.carriers.filter(c => props.modelValue.has(c.carrier_id))
)

const filteredCarriers = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.carriers
  return props.carriers.filter(c =>
    (c.name || c.carrier_id).toLowerCase().includes(q)
  )
})

const triggerLabel = computed(() => {
  const n = props.modelValue.size
  if (n === 0) return 'Select carriers…'
  if (n === 1) {
    const c = props.carriers.find(x => props.modelValue.has(x.carrier_id))
    return c?.name || c?.carrier_id || '1 carrier selected'
  }
  if (n === 2) {
    return props.carriers
      .filter(c => props.modelValue.has(c.carrier_id))
      .map(c => c.name || c.carrier_id)
      .join(', ')
  }
  return `${n} carriers selected`
})

const hasError = computed(() => !!props.showError && props.modelValue.size === 0)

function toggle(id: string) {
  const next = new Set(props.modelValue)
  next.has(id) ? next.delete(id) : next.add(id)
  emit('update:modelValue', next)
}

function deselect(id: string) { toggle(id) }
function selectAll() { emit('update:modelValue', new Set(props.carriers.map(c => c.carrier_id))) }
function clearAll() { emit('update:modelValue', new Set()) }

function toggleOpen() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    query.value = ''
    nextTick(() => searchEl.value?.focus())
  }
}

function close() { isOpen.value = false }

function handleDocumentClick(e: MouseEvent) {
  if (!rootEl.value?.contains(e.target as Node)) isOpen.value = false
}

function handleDocumentKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isOpen.value) isOpen.value = false
}

onMounted(() => {
  document.addEventListener('mousedown', handleDocumentClick)
  document.addEventListener('keydown', handleDocumentKeydown)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleDocumentClick)
  document.removeEventListener('keydown', handleDocumentKeydown)
})
</script>

<style scoped>
/* ── Trigger button ── */
.cms-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 7px 12px;
  border-radius: 8px;
  border: 1px solid var(--app-input-border);
  background: var(--app-input-bg);
  color: var(--app-text);
  font-family: inherit;
  font-size: 14px;
  letter-spacing: -0.224px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.25s;
}
.cms-trigger:hover { border-color: var(--app-input-border); }
.cms-trigger.is-open {
  border-color: #0071e3;
  box-shadow: 0 0 0 2px rgba(0, 113, 227, 0.20);
}
.cms-trigger.is-error { border-color: #ff3b30; }

.cms-placeholder { color: var(--app-placeholder); }
.cms-value       { color: var(--app-text); }

.cms-chevron {
  flex-shrink: 0;
  color: var(--app-placeholder);
  transition: transform 0.15s;
}

/* ── Selected chips ── */
.cms-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 980px;
  background: rgba(0, 113, 227, 0.10);
  border: 1px solid rgba(0, 113, 227, 0.30);
  color: #0071e3;
  font-size: 11px;
}
.cms-chip-remove {
  opacity: 0.6;
  background: none;
  border: none;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  color: inherit;
  flex-shrink: 0;
  transition: opacity 0.15s;
}
.cms-chip-remove:hover { opacity: 1; }

/* ── Dropdown panel ── */
.cms-panel {
  position: absolute;
  z-index: 20;
  top: 100%;
  left: 0;
  margin-top: 4px;
  min-width: 260px;
  width: 100%;
  background: var(--app-input-bg);
  border: 1px solid var(--app-input-border);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}

.cms-panel-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--table-divider);
}

.cms-search-row {
  padding: 8px;
  border-bottom: 1px solid var(--table-divider);
}

.cms-action-btn {
  font-size: 12px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--app-text-sec);
  transition: color 0.15s;
}
.cms-action-btn:hover { text-decoration: underline; color: var(--app-text); }
.cms-action-btn.is-primary { color: #0071e3; }
.cms-action-btn.is-primary:hover { color: #0077ed; }

/* ── Carrier list items ── */
.cms-list-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  border-top: 1px solid var(--table-divider);
  transition: background 0.1s;
}
.cms-list-item:first-child { border-top: none; }
.cms-list-item:hover { background: var(--table-row-hover); }

.cms-checkbox {
  margin-top: 2px;
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid var(--app-input-border);
  background: var(--app-input-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, border-color 0.15s;
}
.cms-checkbox.is-checked {
  background: #0071e3;
  border-color: #0071e3;
}

.cms-item-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--app-text);
}
.cms-item-dims {
  font-size: 10px;
  color: var(--app-placeholder);
  margin-top: 2px;
}

.cms-empty {
  padding: 12px;
  font-size: 12px;
  color: var(--app-placeholder);
  text-align: center;
}
</style>
