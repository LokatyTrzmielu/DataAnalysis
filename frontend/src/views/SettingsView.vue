<template>
  <div class="max-w-xl">
    <h1 class="text-xl font-semibold text-gray-800 mb-6">Settings</h1>

    <!-- Account info -->
    <section class="bg-white rounded-lg border border-gray-200 p-5 mb-6">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Account</h2>
      <div class="space-y-3">
        <div class="flex items-center gap-3">
          <span class="w-24 text-sm text-gray-400 shrink-0">Name</span>
          <span class="text-sm text-gray-800 font-medium">{{ auth.user?.name }}</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="w-24 text-sm text-gray-400 shrink-0">Email</span>
          <span class="text-sm text-gray-800">{{ auth.user?.email }}</span>
        </div>
      </div>
    </section>

    <!-- Change password -->
    <section class="bg-white rounded-lg border border-gray-200 p-5">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Change password</h2>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm text-gray-600 mb-1">Current password</label>
          <input
            v-model="form.old_password"
            type="password"
            autocomplete="current-password"
            class="input"
            required
          />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">New password</label>
          <input
            v-model="form.new_password"
            type="password"
            autocomplete="new-password"
            class="input"
            required
            minlength="6"
          />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">Confirm new password</label>
          <input
            v-model="form.confirm"
            type="password"
            autocomplete="new-password"
            class="input"
            required
          />
        </div>

        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <p v-if="success" class="text-sm text-green-600">Password changed successfully.</p>

        <button
          type="submit"
          :disabled="loading"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors disabled:opacity-50"
        >
          {{ loading ? 'Saving…' : 'Save password' }}
        </button>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const auth = useAuthStore()

const form = reactive({ old_password: '', new_password: '', confirm: '' })
const loading = ref(false)
const error = ref('')
const success = ref(false)

async function submit() {
  error.value = ''
  success.value = false

  if (form.new_password !== form.confirm) {
    error.value = 'New passwords do not match.'
    return
  }

  loading.value = true
  try {
    await authApi.changePassword(form.old_password, form.new_password)
    success.value = true
    form.old_password = ''
    form.new_password = ''
    form.confirm = ''
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to change password.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}
</style>
