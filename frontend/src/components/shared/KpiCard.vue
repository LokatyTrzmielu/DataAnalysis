<template>
  <div class="bg-white border border-gray-200 rounded-lg p-4">
    <p class="text-xs text-gray-500 mb-1">{{ label }}</p>
    <p class="text-xl font-bold text-gray-800">{{ value }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; value: string | number | undefined }>()
</script>
