<template>
  <div :class="['toast', `toast--${notification.type}`]" role="alert">
    <div class="toast__body">
      <p class="toast__title">{{ notification.title }}</p>
      <p v-if="notification.message" class="toast__message">{{ notification.message }}</p>
    </div>
    <button class="toast__close" @click="store.remove(notification.id)" aria-label="Close">×</button>
    <div class="toast__progress" />
  </div>
</template>

<script setup lang="ts">
import type { Notification } from '@/stores/notifications'
import { useNotificationsStore } from '@/stores/notifications'

defineProps<{ notification: Notification }>()
const store = useNotificationsStore()
</script>

<style scoped>
.toast {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 320px;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.10), 0 1px 3px rgba(0, 0, 0, 0.06);
  padding: 14px 40px 14px 16px;
  border-left: 3px solid transparent;
  overflow: hidden;
}

.toast--success { border-left-color: #22c55e; }
.toast--error   { border-left-color: #ef4444; }
.toast--info    { border-left-color: #3b82f6; }

.toast__body {
  flex: 1;
  min-width: 0;
}

.toast__title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
  line-height: 1.4;
}

.toast__message {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 3px 0 0;
  font-family: ui-monospace, 'Cascadia Code', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toast__close {
  position: absolute;
  top: 10px;
  right: 12px;
  font-size: 1rem;
  line-height: 1;
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
  transition: color 0.15s;
}
.toast__close:hover { color: #374151; }

.toast__progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  width: 100%;
  transform-origin: left;
  animation: progress 5s linear forwards;
}

.toast--success .toast__progress { background: #22c55e; }
.toast--error   .toast__progress { background: #ef4444; }
.toast--info    .toast__progress { background: #3b82f6; }

@keyframes progress {
  from { transform: scaleX(1); }
  to   { transform: scaleX(0); }
}
</style>
