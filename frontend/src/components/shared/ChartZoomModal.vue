<template>
  <div
    class="fixed inset-0 flex items-center justify-center z-50"
    style="background:rgba(0,0,0,0.55)"
    @click.self="emit('close')"
  >
    <div class="card-apple-elevated flex flex-col w-full" style="max-width:92vw;max-height:92vh">
      <div class="flex items-center justify-between" style="flex-shrink:0;margin-bottom:16px">
        <h3 style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">{{ title }}</h3>
        <button
          @click="emit('close')"
          class="hover:bg-black/[.06] transition-colors"
          style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:6px;color:rgba(0,0,0,0.4)"
          title="Close"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <div ref="zoomChartEl" style="flex:1;min-height:0;height:72vh"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps<{
  title: string
  traces: any[]
  layout: any
}>()

const emit = defineEmits<{ (e: 'close'): void }>()
const zoomChartEl = ref<HTMLElement>()

function handleKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => {
  window.addEventListener('keydown', handleKey)
  if (zoomChartEl.value) {
    Plotly.newPlot(zoomChartEl.value, props.traces, props.layout, {
      responsive: true,
      displayModeBar: true,
    })
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKey)
  if (zoomChartEl.value) Plotly.purge(zoomChartEl.value)
})
</script>
