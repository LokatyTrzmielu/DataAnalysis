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
  background: rgba(0, 0, 0, 0.07);
  color: rgba(0, 0, 0, 0.55);
}
:global(html.dark) .status-chip.is-default {
  background: rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.80);
}

.status-chip.is-blue {
  background: rgba(0, 113, 227, 0.10);
  color: #0066cc;
}
:global(html.dark) .status-chip.is-blue {
  background: rgba(41, 151, 255, 0.18);
  color: #2997ff;
}

.status-chip.is-green {
  background: rgba(52, 199, 89, 0.12);
  color: #1a7f37;
}
:global(html.dark) .status-chip.is-green {
  background: rgba(52, 199, 89, 0.18);
  color: #34c759;
}
</style>
