<template>
  <span :class="['status-chip', variantClass]">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const STATUS_MAP: Record<string, { label: string; variant: string }> = {
  created:          { label: 'Import',      variant: 'default' },
  ingested:         { label: 'Import',      variant: 'blue' },
  quality_done:     { label: 'Validation',  variant: 'blue' },
  orders_ingested:  { label: 'Performance', variant: 'blue' },
  capacity_done:    { label: 'Capacity',    variant: 'green' },
  performance_done: { label: 'Performance', variant: 'green' },
}

const info = computed(() => STATUS_MAP[props.status] ?? { label: props.status, variant: 'default' })
const label = computed(() => info.value.label)
const variantClass = computed(() => `is-${info.value.variant}`)
</script>

<style scoped>
.status-chip {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 980px;
  white-space: nowrap;
}

.status-chip.is-default {
  background: var(--badge-default-bg);
  color: var(--badge-default-color);
}

.status-chip.is-blue {
  background: var(--badge-blue-bg);
  color: var(--badge-blue-color);
}

.status-chip.is-green {
  background: var(--badge-green-bg);
  color: var(--badge-green-color);
}
</style>
