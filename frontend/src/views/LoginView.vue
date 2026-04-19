<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="bg-white shadow rounded-lg p-8 w-full max-w-sm">
      <h1 class="text-xl font-semibold text-gray-800 mb-6">Datavisor</h1>

      <!-- Sign in -->
      <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            v-model="login.email"
            type="email"
            required
            autocomplete="email"
            class="input"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
            v-model="login.password"
            type="password"
            required
            autocomplete="current-password"
            class="input"
          />
        </div>

        <p v-if="loginError" class="text-red-600 text-sm">{{ loginError }}</p>

        <button type="submit" :disabled="loginLoading" class="btn-primary">
          {{ loginLoading ? 'Signing in…' : 'Sign in' }}
        </button>

        <p class="text-center text-sm text-gray-500">
          No account?
          <button type="button" @click="switchMode('register')" class="text-blue-600 hover:underline">
            Create one
          </button>
        </p>
      </form>

      <!-- Create account -->
      <form v-else @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input v-model="reg.name" type="text" required autocomplete="off" class="input" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input v-model="reg.email" type="email" required autocomplete="off" class="input" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input v-model="reg.password" type="password" required minlength="6" autocomplete="new-password" class="input" />
        </div>

        <p v-if="regError" class="text-red-600 text-sm">{{ regError }}</p>

        <button type="submit" :disabled="regLoading" class="btn-primary">
          {{ regLoading ? 'Creating…' : 'Create account' }}
        </button>

        <p class="text-center text-sm text-gray-500">
          Already have an account?
          <button type="button" @click="switchMode('login')" class="text-blue-600 hover:underline">
            Sign in
          </button>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const auth = useAuthStore()
const router = useRouter()

const mode = ref<'login' | 'register'>('login')

const login = reactive({ email: '', password: '' })
const loginLoading = ref(false)
const loginError = ref('')

const reg = reactive({ name: '', email: '', password: '' })
const regLoading = ref(false)
const regError = ref('')

function switchMode(to: 'login' | 'register') {
  mode.value = to
  loginError.value = ''
  regError.value = ''
}

async function handleLogin() {
  loginLoading.value = true
  loginError.value = ''
  try {
    await auth.login(login.email, login.password)
    router.push('/')
  } catch {
    loginError.value = 'Invalid email or password.'
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  regLoading.value = true
  regError.value = ''
  try {
    await authApi.createUser(reg.email, reg.name, reg.password)
    await auth.login(reg.email, reg.password)
    router.push('/')
  } catch (e: any) {
    regError.value = e?.response?.data?.detail ?? 'Failed to create account.'
  } finally {
    regLoading.value = false
  }
}
</script>

<style scoped>
.input {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}
.btn-primary {
  width: 100%;
  background-color: #2563eb;
  color: white;
  font-weight: 500;
  padding: 0.5rem 0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: background-color 0.15s;
}
.btn-primary:hover:not(:disabled) {
  background-color: #1d4ed8;
}
.btn-primary:disabled {
  opacity: 0.5;
}
</style>
