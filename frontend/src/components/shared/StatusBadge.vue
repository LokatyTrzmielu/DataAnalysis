<template>
  <span :class="['text-xs font-medium px-2 py-0.5 rounded-full', colorClass]">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  created: { label: 'Created', color: 'bg-gray-100 text-gray-600' },
  ingested: { label: 'Ingested', color: 'bg-blue-50 text-blue-600' },
  quality_done: { label: 'Quality', color: 'bg-purple-50 text-purple-600' },
  capacity_done: { label: 'Capacity', color: 'bg-green-50 text-green-700' },
  performance_done: { label: 'Performance', color: 'bg-emerald-50 text-emerald-700' },
}

const info = computed(() => STATUS_MAP[props.status] ?? { label: props.status, color: 'bg-gray-100 text-gray-500' })
const label = computed(() => info.value.label)
const colorClass = computed(() => info.value.color)
</script>
