import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<{ id: string; email: string; name: string } | null>(
    JSON.parse(localStorage.getItem('user') || 'null'),
  )

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const { data } = await authApi.login(email, password)
    token.value = data.access_token
    user.value = { id: data.user_id, email: data.email, name: data.name }
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    // Navigate to login (avoid circular import by using window.location)
    window.location.href = '/login'
  }

  return { token, user, isAuthenticated, login, logout }
})
