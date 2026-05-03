<template>
  <span class="relative group inline-flex cursor-help">
    <span class="helptip-badge">?</span>
    <span class="helptip-tooltip opacity-0 group-hover:opacity-100 transition-opacity">
      {{ text }}
    </span>
  </span>
</template>

<script setup lang="ts">
defineProps<{ text: string }>()
</script>

<style scoped>
.helptip-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--badge-default-bg);
  color: var(--app-text-sec);
  border: 1px solid var(--app-input-border);
  font-size: 9px;
  font-weight: 700;
  user-select: none;
  flex-shrink: 0;
}

.helptip-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 6px;
  width: 200px;
  padding: 8px 10px;
  font-size: 12px;
  letter-spacing: -0.12px;
  color: #ffffff;
  background: #3a3a3c;
  border-radius: 6px;
  pointer-events: none;
  line-height: 1.4;
  z-index: 30;
  white-space: normal;
}
</style>
