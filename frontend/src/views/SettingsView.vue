<template>
  <div style="max-width:480px">
    <h1 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:var(--app-text);line-height:1.14;letter-spacing:-0.28px;margin-bottom:24px">
      Settings
    </h1>

    <!-- Account info -->
    <section class="card-apple mb-6">
      <h2 class="mb-4" style="font-size:12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.12px;text-transform:uppercase">Account</h2>
      <div class="space-y-3">
        <div class="flex items-center gap-3">
          <span style="width:80px;font-size:14px;color:var(--app-text-sec);letter-spacing:-0.224px;flex-shrink:0">Name</span>
          <span style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">{{ auth.user?.name }}</span>
        </div>
        <div class="flex items-center gap-3">
          <span style="width:80px;font-size:14px;color:var(--app-text-sec);letter-spacing:-0.224px;flex-shrink:0">Email</span>
          <span style="font-size:14px;color:var(--app-text);letter-spacing:-0.224px">{{ auth.user?.email }}</span>
        </div>
      </div>
    </section>

    <!-- Time saved -->
    <TimeSavedCard />

    <!-- Change password -->
    <section class="card-apple">
      <h2 class="mb-4" style="font-size:12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.12px;text-transform:uppercase">Change password</h2>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="label-apple">Current password</label>
          <input v-model="form.old_password" type="password" autocomplete="current-password" class="input-apple" required />
        </div>
        <div>
          <label class="label-apple">New password</label>
          <input v-model="form.new_password" type="password" autocomplete="new-password" class="input-apple" required minlength="6" />
        </div>
        <div>
          <label class="label-apple">Confirm new password</label>
          <input v-model="form.confirm" type="password" autocomplete="new-password" class="input-apple" required />
        </div>

        <p v-if="error" style="font-size:14px;color:#ff3b30">{{ error }}</p>
        <p v-if="success" style="font-size:14px;color:#34c759">Password changed successfully.</p>

        <button type="submit" :disabled="loading" class="btn-apple-primary">
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
import { useNotificationsStore } from '@/stores/notifications'
import TimeSavedCard from '@/components/settings/TimeSavedCard.vue'

const auth = useAuthStore()
const notify = useNotificationsStore()

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
    notify.push({ type: 'success', title: 'Password changed' })
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to change password.'
  } finally {
    loading.value = false
  }
}
</script>
