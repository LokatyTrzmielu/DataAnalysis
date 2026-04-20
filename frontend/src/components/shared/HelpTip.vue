<template>
  <span class="relative group inline-flex cursor-help">
    <span style="display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;border-radius:50%;background:rgba(0,0,0,0.06);color:rgba(0,0,0,0.48);font-size:9px;font-weight:700;border:1px solid rgba(0,0,0,0.1);user-select:none">?</span>
    <span style="position:absolute;bottom:100%;left:50%;transform:translateX(-50%);margin-bottom:6px;width:200px;padding:8px 10px;font-size:12px;letter-spacing:-0.12px;color:#fff;background:#1d1d1f;border-radius:6px;pointer-events:none;line-height:1.4;z-index:30" class="opacity-0 group-hover:opacity-100 transition-opacity">
      {{ text }}
    </span>
  </span>
</template>

<script setup lang="ts">
defineProps<{ text: string }>()
</script>
