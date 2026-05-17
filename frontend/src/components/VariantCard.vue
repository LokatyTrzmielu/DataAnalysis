<template>
  <button
    type="button"
    @click="$emit('click')"
    class="variant-card text-left"
    :class="{ 'is-selected': selected }"
  >
    <div class="flex items-start justify-between mb-1.5">
      <span class="font-semibold" style="font-size:12px;color:var(--app-text);letter-spacing:-0.1px">
        {{ variant.code }}
      </span>
      <span
        class="rounded px-1.5"
        :style="`font-size:10px;background:${tierColor};color:#fff;line-height:16px`"
      >{{ variant.bin_height_mm }}mm</span>
    </div>

    <svg :viewBox="`0 0 ${vbW} ${vbH}`" class="block mb-1.5 variant-card-svg" style="width:100%" preserveAspectRatio="xMidYMid meet">
      <rect x="0" y="0" :width="vbW" :height="vbH" class="bin-bg" stroke-width="2" rx="4"/>
      <g v-for="(c, i) in cells" :key="i">
        <rect
          :x="c.x" :y="c.y" :width="c.w" :height="c.h"
          class="bin-cell" stroke-width="1.5"
        />
      </g>
    </svg>

    <p class="m-0" style="font-size:10.5px;color:var(--app-text-sec);line-height:1.35">
      {{ variant.cell_length_mm }}×{{ variant.cell_width_mm }}×{{ variant.cell_height_mm }} mm
    </p>
    <p v-if="skuCount !== undefined" class="m-0 mt-1" style="font-size:10.5px;color:var(--app-text);font-weight:500">
      {{ skuCount }} SKU · {{ binCount }} bins
      <span v-if="avgFill !== undefined" style="color:var(--app-text-sec);font-weight:400"> · {{ avgFill }}%</span>
    </p>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { VariantInfo } from '@/api/containerOrder'

const props = defineProps<{
  variant: VariantInfo
  selected?: boolean
  skuCount?: number
  binCount?: number
  avgFill?: number
}>()

defineEmits<{ click: [] }>()

// Bin interior is ~617 × 408. Aspect locked to that ratio.
const vbW = 617
const vbH = 408

const tierColor = computed(() => {
  switch (props.variant.bin_height_mm) {
    case 138: return '#93c5fd'
    case 188: return '#60a5fa'
    case 238: return '#3b82f6'
    case 288: return '#1d4ed8'
    default: return '#0071e3'
  }
})

const cells = computed(() => {
  const cw = props.variant.cell_length_mm
  const ch = props.variant.cell_width_mm
  const cols = Math.round(vbW / cw)
  const rows = Math.round(vbH / ch)
  const out: Array<{ x: number; y: number; w: number; h: number }> = []
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      out.push({ x: c * cw + 2, y: r * ch + 2, w: cw - 4, h: ch - 4 })
    }
  }
  return out
})
</script>

<style scoped>
.variant-card {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 10px;
  padding: 8px 10px;
  cursor: pointer;
  transition: border-color 120ms ease, background 120ms ease;
  text-align: left;
  overflow: hidden;             /* prevent dimension/counter text from spilling out
                                   when the card is squeezed by a tight grid row */
}
.variant-card > svg {
  flex: 1 1 0;                  /* shrink to whatever is left after header + counters */
  min-height: 0;
  max-height: 100%;
}
.variant-card > p {
  flex: 0 0 auto;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.variant-card:hover {
  border-color: #0071e3;
}
.variant-card.is-selected {
  border-color: #0071e3;
  background: rgba(0, 113, 227, 0.06);
  box-shadow: 0 0 0 2px rgba(0, 113, 227, 0.25);
}

/* Bin schematic uses CSS-driven fills/strokes so it adapts to dark mode. */
.variant-card-svg .bin-bg { fill: #f3f4f6; stroke: #cbd5e1; }
.variant-card-svg .bin-cell { fill: #dbeafe; stroke: #0071e3; }
:global(html.dark) .variant-card-svg .bin-bg { fill: #2c2c2e; stroke: #5a5a5e; }
:global(html.dark) .variant-card-svg .bin-cell { fill: rgba(0, 113, 227, 0.28); stroke: #0a84ff; }
</style>
