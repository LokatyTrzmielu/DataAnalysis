<template>
  <div style="min-height:100vh">
    <ToastContainer />
    <ScrollToTop />
    <AppTopNav v-if="auth.isAuthenticated" />
    <main :class="mainClass" :style="mainStyle">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import ToastContainer from '@/components/shared/ToastContainer.vue'
import AppTopNav from '@/components/layout/AppTopNav.vue'
import ScrollToTop from '@/components/shared/ScrollToTop.vue'

const auth = useAuthStore()
const route = useRoute()
useThemeStore()

const mainClass = computed(() => {
  if (route.meta.fullscreen) return 'min-h-screen flex items-center justify-center'
  if (route.meta.hasSidebar) return 'pr-6 py-8'
  return 'mx-auto max-w-[1400px] px-6 py-8'
})

const mainStyle = computed<Record<string, string> | undefined>(() => {
  if (!route.meta.hasSidebar) return undefined
  return {
    paddingLeft: 'calc(var(--app-sidebar-w, 264px) + 24px)',
    transition: 'padding-left 0.25s ease',
  }
})
</script>
