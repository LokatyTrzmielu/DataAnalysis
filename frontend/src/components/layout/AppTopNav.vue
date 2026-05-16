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

    <!-- Right: tank status + theme toggle + user + icon buttons -->
    <div class="nav-right">
      <!-- Tank icon: always drives (idle), shoots when analyzing -->
      <span
        class="nav-tank"
        :class="{ 'is-shooting': analysis.isAnalyzing }"
        :title="analysis.isAnalyzing ? 'Analysis running...' : 'Ready'"
        role="status"
        :aria-label="analysis.isAnalyzing ? 'Analysis running' : 'Ready'"
      >
        <svg class="tank-svg" viewBox="0 0 52 22" overflow="visible" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <clipPath id="nav-tank-clip">
              <rect x="2" y="13" width="36" height="8" rx="4"/>
            </clipPath>
          </defs>
          <!-- Track base -->
          <rect x="2" y="13" width="36" height="8" rx="4" fill="rgba(255,255,255,0.20)"/>
          <!-- Track links – always scrolling -->
          <g clip-path="url(#nav-tank-clip)" class="tank-tracks">
            <rect x="0"  y="14" width="3" height="6" rx="0.5" fill="rgba(255,255,255,0.18)"/>
            <rect x="5"  y="14" width="3" height="6" rx="0.5" fill="rgba(255,255,255,0.18)"/>
            <rect x="10" y="14" width="3" height="6" rx="0.5" fill="rgba(255,255,255,0.18)"/>
            <rect x="15" y="14" width="3" height="6" rx="0.5" fill="rgba(255,255,255,0.18)"/>
            <rect x="20" y="14" width="3" height="6" rx="0.5" fill="rgba(255,255,255,0.18)"/>
            <rect x="25" y="14" width="3" height="6" rx="0.5" fill="rgba(255,255,255,0.18)"/>
            <rect x="30" y="14" width="3" height="6" rx="0.5" fill="rgba(255,255,255,0.18)"/>
            <rect x="35" y="14" width="3" height="6" rx="0.5" fill="rgba(255,255,255,0.18)"/>
            <rect x="40" y="14" width="3" height="6" rx="0.5" fill="rgba(255,255,255,0.18)"/>
          </g>
          <!-- Drive wheels -->
          <circle cx="6"  cy="17" r="4" fill="rgba(255,255,255,0.28)"/>
          <circle cx="34" cy="17" r="4" fill="rgba(255,255,255,0.28)"/>
          <!-- Hull body – low-poly trapezoid (darkest facet) -->
          <polygon points="4,13 36,13 34,8 6,8"  fill="rgba(255,255,255,0.35)"/>
          <!-- Upper hull – medium facet -->
          <polygon points="8,8 32,8 30,5 10,5"   fill="rgba(255,255,255,0.50)"/>
          <!-- Turret – lighter facet -->
          <polygon points="14,5 26,5 24,2 16,2"  fill="rgba(255,255,255,0.65)"/>
          <!-- Turret top highlight facet -->
          <polygon points="16,2 24,2 23.5,1 16.5,1" fill="rgba(255,255,255,0.30)"/>
          <!-- Gun barrel (recoils when shooting) -->
          <g class="tank-gun">
            <rect x="24" y="2" width="18" height="2" rx="1" fill="rgba(255,255,255,0.52)"/>
          </g>
          <!-- Muzzle flash (visible only when shooting) -->
          <g class="muzzle-flash">
            <circle cx="45" cy="3" r="2.5" fill="rgba(255,255,255,0.22)"/>
            <line x1="42" y1="3"   x2="50" y2="3"   stroke="rgba(255,255,255,0.95)" stroke-width="1.5" stroke-linecap="round"/>
            <line x1="42" y1="2"   x2="48" y2="-1"  stroke="rgba(255,255,255,0.70)" stroke-width="1"   stroke-linecap="round"/>
            <line x1="42" y1="4"   x2="48" y2="7"   stroke="rgba(255,255,255,0.70)" stroke-width="1"   stroke-linecap="round"/>
          </g>
        </svg>
      </span>

      <!-- Theme toggle -->
      <button @click="theme.toggle()" class="nav-theme-toggle" :title="theme.dark ? 'Switch to light mode' : 'Switch to dark mode'">
        <svg v-if="theme.dark" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
        <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </button>

      <!-- Settings – gear icon -->
      <RouterLink to="/settings" class="nav-icon-btn" :class="{ active: isActive('/settings') }" title="Settings">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
      </RouterLink>

      <!-- Help – question mark icon -->
      <RouterLink to="/help" class="nav-icon-btn" :class="{ active: isActive('/help') }" title="Help">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      </RouterLink>

      <!-- Sign out – power icon -->
      <button @click="auth.logout()" class="nav-icon-btn" title="Sign out">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18.36 6.64a9 9 0 1 1-12.73 0"/>
          <line x1="12" y1="2" x2="12" y2="12"/>
        </svg>
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
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

/* ── Tank icon ─────────────────────────────────────── */
.nav-tank {
  display: flex;
  align-items: center;
  cursor: default;
  user-select: none;
  opacity: 0.50;
  transition: opacity 0.4s ease;
}

.nav-tank.is-shooting {
  opacity: 1;
}

.tank-svg {
  width: 40px;
  height: 17px;
}

/* Idle: gentle horizontal cruise – always active */
.tank-svg {
  animation: tank-cruise 2.8s ease-in-out infinite;
}

/* Track links – always scrolling (idle pace) */
.tank-tracks {
  animation: track-roll 1s linear infinite;
}

/* Shooting: whole tank shakes down on recoil */
.nav-tank.is-shooting .tank-svg {
  animation: tank-shoot-shake 1.4s ease-in-out infinite;
}

/* Shooting: gun barrel recoils back */
.nav-tank.is-shooting .tank-gun {
  animation: gun-recoil 1.4s ease-in-out infinite;
}

/* Shooting: muzzle flash at gun tip */
.muzzle-flash { opacity: 0; }
.nav-tank.is-shooting .muzzle-flash {
  animation: muzzle-flash 1.4s ease-in-out infinite;
}

/* Shooting: faster track roll */
.nav-tank.is-shooting .tank-tracks {
  animation: track-roll 0.35s linear infinite;
}

@keyframes tank-cruise {
  0%   { transform: translateX(-1.5px); }
  50%  { transform: translateX(1.5px);  }
  100% { transform: translateX(-1.5px); }
}

@keyframes tank-shoot-shake {
  0%   { transform: translateY(0);     }
  7%   { transform: translateY(1.8px); }
  18%  { transform: translateY(0);     }
  100% { transform: translateY(0);     }
}

@keyframes gun-recoil {
  0%   { transform: translateX(0);    }
  6%   { transform: translateX(-3px); }
  18%  { transform: translateX(0);    }
  100% { transform: translateX(0);    }
}

@keyframes muzzle-flash {
  0%   { opacity: 0; transform: scaleX(0.4); }
  5%   { opacity: 1; transform: scaleX(1);   }
  14%  { opacity: 0; transform: scaleX(0.8); }
  100% { opacity: 0; transform: scaleX(0.4); }
}

@keyframes track-roll {
  from { transform: translateX(0);    }
  to   { transform: translateX(-5px); }
}

/* ── Icon buttons (settings / help / sign-out) ───── */
.nav-icon-btn {
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
  text-decoration: none;
}

.nav-icon-btn:hover,
.nav-icon-btn.active {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.10);
}

/* ── Theme toggle ─────────────────────────────────── */
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
</style>
