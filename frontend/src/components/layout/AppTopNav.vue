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
      <RouterLink to="/datasets" class="nav-link" :class="{ active: isActive('/datasets') }">Datasets</RouterLink>
      <RouterLink to="/carriers" class="nav-link" :class="{ active: isActive('/carriers') }">Carriers</RouterLink>
      <RouterLink to="/tools" class="nav-link" :class="{ active: isActive('/tools') }">Tools</RouterLink>
    </div>

    <!-- Right: theme toggle + settings + user + logout -->
    <div class="nav-right">
      <Transition name="runner-fade">
        <span
          v-if="analysis.isAnalyzing"
          class="nav-runner"
          aria-label="Analysis running"
          role="status"
        >{{ currentIcon }}</span>
      </Transition>

      <button @click="theme.toggle()" class="nav-theme-toggle" :title="theme.dark ? 'Switch to light mode' : 'Switch to dark mode'">
        <!-- Sun (shown in dark mode → click to go light) -->
        <svg v-if="theme.dark" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
        <!-- Moon (shown in light mode → click to go dark) -->
        <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </button>
      <span class="nav-user">{{ auth.user?.name }}</span>
      <RouterLink to="/settings" class="nav-link" :class="{ active: isActive('/settings') }">Settings</RouterLink>
      <RouterLink to="/help" class="nav-link" :class="{ active: isActive('/help') }">Help</RouterLink>
      <button @click="auth.logout()" class="nav-logout">Sign out</button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useAnalysisStore } from '@/stores/analysis'

const auth = useAuthStore()
const theme = useThemeStore()
const route = useRoute()
const analysis = useAnalysisStore()

function isActive(path: string) { return route.path.startsWith(path) }
function isExact(path: string)  { return route.path === path }

const ICONS = ['🏃', '🏃‍♂️', '🏃‍♀️', '💨', '⚡', '🚀', '🔥']
const currentIcon = ref(ICONS[0])
let intervalId: ReturnType<typeof setInterval> | null = null

function startCycling() {
  currentIcon.value = ICONS[Math.floor(Math.random() * ICONS.length)]
  intervalId = setInterval(() => {
    currentIcon.value = ICONS[Math.floor(Math.random() * ICONS.length)]
  }, 500)
}

function stopCycling() {
  if (intervalId !== null) { clearInterval(intervalId); intervalId = null }
}

watch(() => analysis.isAnalyzing, (active) => {
  if (active) startCycling()
  else stopCycling()
})

onUnmounted(stopCycling)
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
  background: var(--nav-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--nav-border);
  transition: background 0.25s, border-color 0.25s;
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

.nav-theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: none;
  border: none;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.60);
  border-radius: 6px;
  transition: color 0.15s, background 0.15s;
  padding: 0;
}

.nav-theme-toggle:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.10);
}

.nav-runner {
  font-size: 16px;
  line-height: 1;
  display: flex;
  align-items: center;
  animation: runner-bounce 0.5s ease infinite alternate;
  cursor: default;
  user-select: none;
}

@keyframes runner-bounce {
  from { transform: translateY(0px); }
  to   { transform: translateY(-3px); }
}

.runner-fade-enter-active,
.runner-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.runner-fade-enter-from,
.runner-fade-leave-to {
  opacity: 0;
  transform: scale(0.6);
}
</style>
