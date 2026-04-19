<template>
  <div class="flex min-h-screen bg-gray-50">
    <ToastContainer />
    <AppSidebar v-if="auth.isAuthenticated" />
    <main class="flex-1 min-w-0 p-6">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ToastContainer from '@/components/shared/ToastContainer.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'

const auth = useAuthStore()
</script>
