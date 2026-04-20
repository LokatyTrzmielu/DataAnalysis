<template>
  <div :class="['toast', `toast--${notification.type}`]" role="alert">
    <div class="toast__body">
      <p class="toast__title">
        <span class="toast__dot" />{{ notification.title }}
      </p>
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
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: rgba(0, 0, 0, 0.22) 3px 5px 30px 0px;
  padding: 14px 40px 14px 16px;
  border: none;
  overflow: hidden;
}

.toast__body {
  flex: 1;
  min-width: 0;
}

.toast__dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
  flex-shrink: 0;
}

.toast--success .toast__dot { background: #34c759; }
.toast--error   .toast__dot { background: #ff3b30; }
.toast--info    .toast__dot { background: #0071e3; }

.toast__title {
  font-family: "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  letter-spacing: -0.224px;
  margin: 0;
  line-height: 1.4;
  display: flex;
  align-items: center;
}

.toast__message {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.48);
  letter-spacing: -0.12px;
  margin: 3px 0 0;
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
  color: rgba(0, 0, 0, 0.32);
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
  transition: color 0.15s;
}
.toast__close:hover { color: #1d1d1f; }

.toast__progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  width: 100%;
  transform-origin: left;
  animation: progress 5s linear forwards;
}

.toast--success .toast__progress { background: #34c759; }
.toast--error   .toast__progress { background: #ff3b30; }
.toast--info    .toast__progress { background: #0071e3; }

@keyframes progress {
  from { transform: scaleX(1); }
  to   { transform: scaleX(0); }
}
</style>
