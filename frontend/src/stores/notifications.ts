import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'info'
  title: string
  message?: string
}

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])

  function push(n: Omit<Notification, 'id'>, duration = 5000) {
    const id = crypto.randomUUID()
    notifications.value.push({ ...n, id })
    setTimeout(() => remove(id), duration)
  }

  function remove(id: string) {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  return { notifications, push, remove }
})
