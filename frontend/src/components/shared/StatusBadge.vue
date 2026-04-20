<template>
  <span :class="['text-xs font-medium px-2 py-0.5 rounded-full', colorClass]">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  created:          { label: 'Created',     color: 'bg-[rgba(0,0,0,0.06)] text-[rgba(0,0,0,0.48)]' },
  ingested:         { label: 'Ingested',    color: 'bg-[rgba(0,113,227,0.08)] text-[#0066cc]' },
  quality_done:     { label: 'Quality',     color: 'bg-[rgba(0,113,227,0.08)] text-[#0066cc]' },
  orders_ingested:  { label: 'Orders',      color: 'bg-[rgba(0,113,227,0.08)] text-[#0066cc]' },
  capacity_done:    { label: 'Capacity',    color: 'bg-[rgba(52,199,89,0.12)] text-[#1a7f37]' },
  performance_done: { label: 'Performance', color: 'bg-[rgba(52,199,89,0.12)] text-[#1a7f37]' },
}

const info = computed(() => STATUS_MAP[props.status] ?? { label: props.status, color: 'bg-[rgba(0,0,0,0.06)] text-[rgba(0,0,0,0.48)]' })
const label = computed(() => info.value.label)
const colorClass = computed(() => info.value.color)
</script>
