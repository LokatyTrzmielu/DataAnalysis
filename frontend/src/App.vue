<template>
  <div style="min-height:100vh">
    <ToastContainer />
    <AppTopNav v-if="auth.isAuthenticated" />
    <main :class="route.meta.fullscreen ? 'min-h-screen flex items-center justify-center' : 'mx-auto max-w-[980px] px-5 py-8'">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import ToastContainer from '@/components/shared/ToastContainer.vue'
import AppTopNav from '@/components/layout/AppTopNav.vue'

const auth = useAuthStore()
const route = useRoute()
useThemeStore()
</script>
