<template>
  <div class="card-apple">
    <p class="flex items-center gap-1" style="font-size:12px;color:rgba(0,0,0,0.48);letter-spacing:-0.12px;margin-bottom:6px">
      {{ label }}
      <HelpTip v-if="tooltip" :text="tooltip" />
    </p>
    <p style="font-size:28px;font-weight:600;color:#1d1d1f;line-height:1.14;letter-spacing:0.196px">{{ value }}</p>
  </div>
</template>

<script setup lang="ts">
import HelpTip from './HelpTip.vue'
defineProps<{ label: string; value: string | number | undefined; tooltip?: string }>()
</script>
