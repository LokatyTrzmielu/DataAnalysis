<template>
  <div ref="rootEl" class="relative">

    <!-- Trigger button -->
    <button
      type="button"
      @click="toggleOpen"
      :class="[
        'flex items-center justify-between gap-2 w-full px-3 py-2 rounded-lg border text-xs transition-all text-left',
        isOpen
          ? 'border-[#0071e3] ring-2 ring-[rgba(0,113,227,0.18)] bg-white'
          : hasError
            ? 'border-red-400 bg-white'
            : 'border-gray-200 bg-white hover:border-gray-300',
        'text-gray-700'
      ]"
    >
      <span :class="props.modelValue.size === 0 ? 'text-gray-400' : ''">
        {{ triggerLabel }}
      </span>
      <svg
        width="12" height="12" viewBox="0 0 12 12" fill="none"
        :class="['transition-transform flex-shrink-0 text-gray-400', isOpen ? 'rotate-180' : '']"
      >
        <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <!-- Selected chips row -->
    <div v-if="selectedCarriers.length" class="flex flex-wrap gap-1 mt-1.5">
      <span
        v-for="c in selectedCarriers"
        :key="c.carrier_id"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 border border-[#0071e3] text-[#0071e3]"
        style="font-size:11px"
      >
        <span class="truncate max-w-[140px]">{{ c.name || c.carrier_id }}</span>
        <button
          type="button"
          @click.stop="deselect(c.carrier_id)"
          class="opacity-60 hover:opacity-100 transition-opacity leading-none flex-shrink-0"
          aria-label="Remove"
        >×</button>
      </span>
    </div>

    <!-- Validation error -->
    <p v-if="hasError" class="text-xs text-red-500 mt-1">Select at least one carrier</p>

    <!-- Dropdown panel -->
    <div
      v-show="isOpen"
      class="absolute z-20 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg"
      style="top: 100%; left: 0; min-width: 260px; width: 100%;"
    >
      <!-- Quick actions -->
      <div class="flex items-center justify-between px-3 py-2 border-b border-gray-100">
        <button
          type="button"
          @click="selectAll"
          class="text-xs text-[#0071e3] hover:underline"
        >Select all</button>
        <button
          type="button"
          @click="clearAll"
          class="text-xs text-gray-400 hover:underline"
        >Clear</button>
      </div>

      <!-- Search input -->
      <div class="px-2 py-2 border-b border-gray-100">
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
          class="flex items-start gap-2 px-3 py-2 cursor-pointer hover:bg-gray-50 transition-colors select-none"
        >
          <!-- Custom checkbox -->
          <span
            :class="[
              'mt-0.5 flex-shrink-0 w-4 h-4 rounded border flex items-center justify-center transition-colors',
              props.modelValue.has(c.carrier_id)
                ? 'bg-[#0071e3] border-[#0071e3]'
                : 'border-gray-300 bg-white'
            ]"
          >
            <svg
              v-if="props.modelValue.has(c.carrier_id)"
              width="10" height="8" viewBox="0 0 10 8" fill="none"
            >
              <path d="M1 4l3 3 5-6" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
          <!-- Name + dimensions -->
          <span class="flex flex-col min-w-0">
            <span class="text-xs font-medium text-gray-800 truncate">{{ c.name || c.carrier_id }}</span>
            <span class="opacity-50 mt-0.5" style="font-size:10px">
              {{ c.inner_length_mm }}×{{ c.inner_width_mm }}×{{ c.inner_height_mm }} mm · max {{ c.max_weight_kg }} kg
            </span>
          </span>
        </li>
        <li
          v-if="!filteredCarriers.length"
          class="px-3 py-3 text-xs text-gray-400 text-center"
        >
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
