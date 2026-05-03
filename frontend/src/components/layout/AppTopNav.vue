<template>
  <nav class="apple-nav">
    <!-- Logo -->
    <RouterLink to="/" class="nav-logo">
      <svg class="nav-logo-icon" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zm6-4a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zm6-3a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
      </svg>
      <span class="nav-logo-text">Datavisor</span>
    </RouterLink>

    <!-- Center links -->
    <div class="nav-links">
      <RouterLink to="/" class="nav-link" :class="{ active: isExact('/') }">Dashboard</RouterLink>
      <RouterLink to="/runs" class="nav-link" :class="{ active: isActive('/runs') }">Analyses</RouterLink>
      <RouterLink to="/carriers" class="nav-link" :class="{ active: isActive('/carriers') }">Carriers</RouterLink>
    </div>

    <!-- Right: settings + user + logout -->
    <div class="nav-right">
      <span class="nav-user">{{ auth.user?.name }}</span>
      <RouterLink to="/settings" class="nav-link" :class="{ active: isActive('/settings') }">Settings</RouterLink>
      <button @click="auth.logout()" class="nav-logout">Sign out</button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()

function isActive(path: string) {
  return route.path.startsWith(path)
}
function isExact(path: string) {
  return route.path === path
}
</script>

<style scoped>
.apple-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  background: rgba(0, 0, 0, 0.82);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid transparent;
  transition: background 0.25s, border-color 0.25s;
}

:global(html.dark) .apple-nav {
  background: rgba(60, 60, 67, 0.72);
  border-bottom-color: rgba(255, 255, 255, 0.10);
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #ffffff;
  text-decoration: none;
  flex-shrink: 0;
}

.nav-logo-icon {
  width: 16px;
  height: 16px;
  color: #ffffff;
}

.nav-logo-text {
  font-family: "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.224px;
  color: #ffffff;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 28px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.nav-link {
  font-family: "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 12px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.72);
  text-decoration: none;
  letter-spacing: -0.12px;
  transition: color 0.15s;
  white-space: nowrap;
}

.nav-link:hover,
.nav-link.active {
  color: #ffffff;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 0;
}

.nav-user {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.36);
  letter-spacing: -0.12px;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-logout {
  font-family: "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 12px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.6);
  background: none;
  border: none;
  cursor: pointer;
  letter-spacing: -0.12px;
  transition: color 0.15s;
  padding: 0;
}

.nav-logout:hover { color: #ffffff; }
</style>
