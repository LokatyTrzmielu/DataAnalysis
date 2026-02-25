<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Top nav (only when authenticated) -->
    <nav v-if="auth.isAuthenticated" class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <div class="flex items-center gap-6">
          <span class="font-semibold text-gray-800 text-sm tracking-wide">Datavisor</span>
          <RouterLink to="/" class="nav-link">Dashboard</RouterLink>
          <RouterLink to="/runs" class="nav-link">Analyses</RouterLink>
          <RouterLink to="/carriers" class="nav-link">Carriers</RouterLink>
        </div>
        <div class="flex items-center gap-3 text-sm text-gray-500">
          <span>{{ auth.user?.name }}</span>
          <button @click="auth.logout()" class="text-red-500 hover:text-red-700 text-xs">
            Logout
          </button>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 py-6">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<style>
.nav-link {
  font-size: 0.875rem;
  color: #4b5563;
  font-weight: 500;
  transition: color 0.15s;
  text-decoration: none;
}
.nav-link:hover {
  color: #111827;
}
.router-link-active.nav-link {
  color: #2563eb;
}
</style>
