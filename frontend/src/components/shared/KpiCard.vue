<template>
  <div class="card-apple">
    <p class="flex items-center gap-1" style="font-size:12px;color:var(--app-text-sec);letter-spacing:-0.12px;margin-bottom:6px">
      {{ label }}
      <HelpTip v-if="tooltip" :text="tooltip" />
    </p>
    <p style="font-size:21px;font-weight:600;color:var(--app-text);line-height:1.19;letter-spacing:-0.021px">{{ value }}</p>
  </div>
</template>

<script setup lang="ts">
import HelpTip from './HelpTip.vue'
defineProps<{ label: string; value: string | number | undefined; tooltip?: string }>()
</script>
