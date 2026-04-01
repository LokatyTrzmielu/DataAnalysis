<template>
  <div class="toast-container">
    <TransitionGroup name="toast" tag="div" class="toast-stack">
      <AppToast
        v-for="n in store.notifications"
        :key="n.id"
        :notification="n"
      />
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useNotificationsStore } from '@/stores/notifications'
import AppToast from './AppToast.vue'

const store = useNotificationsStore()
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 1.25rem;
  right: 1.25rem;
  z-index: 9999;
  pointer-events: none;
}

.toast-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.toast-stack > * {
  pointer-events: all;
}

/* TransitionGroup animations */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(110%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(110%);
}

.toast-move {
  transition: transform 0.25s ease;
}
</style>
