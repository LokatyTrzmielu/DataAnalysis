<template>
  <div class="w-full flex items-center justify-center" style="min-height:calc(100vh - 0px)">
    <div class="card-apple-elevated w-full" style="max-width:380px">
      <h1 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:700;color:#1d1d1f;line-height:1.14;letter-spacing:-0.28px;margin-bottom:28px">
        Datavisor
      </h1>

      <!-- Sign in -->
      <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="label-apple">Email</label>
          <input v-model="login.email" type="email" required autocomplete="email" class="input-apple" />
        </div>
        <div>
          <label class="label-apple">Password</label>
          <input v-model="login.password" type="password" required autocomplete="current-password" class="input-apple" />
        </div>

        <p v-if="loginError" class="text-sm" style="color:#ff3b30">{{ loginError }}</p>

        <button type="submit" :disabled="loginLoading" class="btn-apple-primary w-full justify-center">
          {{ loginLoading ? 'Signing in…' : 'Sign in' }}
        </button>

        <p class="text-center text-sm" style="color:rgba(0,0,0,0.48);letter-spacing:-0.224px">
          No account?
          <button type="button" @click="switchMode('register')" style="color:#0066cc" class="hover:underline">
            Create one
          </button>
        </p>
      </form>

      <!-- Create account -->
      <form v-else @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="label-apple">Name</label>
          <input v-model="reg.name" type="text" required autocomplete="off" class="input-apple" />
        </div>
        <div>
          <label class="label-apple">Email</label>
          <input v-model="reg.email" type="email" required autocomplete="off" class="input-apple" />
        </div>
        <div>
          <label class="label-apple">Password</label>
          <input v-model="reg.password" type="password" required minlength="6" autocomplete="new-password" class="input-apple" />
        </div>

        <p v-if="regError" class="text-sm" style="color:#ff3b30">{{ regError }}</p>

        <button type="submit" :disabled="regLoading" class="btn-apple-primary w-full justify-center">
          {{ regLoading ? 'Creating…' : 'Create account' }}
        </button>

        <p class="text-center text-sm" style="color:rgba(0,0,0,0.48);letter-spacing:-0.224px">
          Already have an account?
          <button type="button" @click="switchMode('login')" style="color:#0066cc" class="hover:underline">
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
