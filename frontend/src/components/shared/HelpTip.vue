<template>
  <span class="relative group inline-flex cursor-help">
    <span class="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-gray-100 text-gray-400 text-[9px] font-bold border border-gray-300 select-none">?</span>
    <span class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 w-52 px-2.5 py-1.5 text-xs text-white bg-gray-700 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-30 pointer-events-none leading-snug">
      {{ text }}
    </span>
  </span>
</template>

<script setup lang="ts">
defineProps<{ text: string }>()
</script>
