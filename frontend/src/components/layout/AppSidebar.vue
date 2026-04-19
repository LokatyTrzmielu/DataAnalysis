<template>
  <aside
    :class="collapsed ? 'w-16' : 'w-60'"
    class="flex flex-col h-screen sticky top-0 bg-white border-r border-gray-200 transition-all duration-200 shrink-0 overflow-y-auto"
  >
    <!-- Logo + toggle -->
    <div class="flex items-center h-14 px-3 border-b border-gray-200" :class="collapsed ? 'justify-center' : 'justify-between'">
      <div v-if="!collapsed" class="flex items-center gap-2">
        <svg class="w-5 h-5 text-blue-600 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zm6-4a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zm6-3a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
        </svg>
        <span class="font-semibold text-gray-800 text-sm tracking-wide">Datavisor</span>
      </div>
      <button
        @click="toggle"
        class="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <svg class="w-4 h-4 transition-transform" :class="collapsed ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
        </svg>
      </button>
    </div>

    <!-- Nav links -->
    <nav class="flex-1 py-3 flex flex-col gap-0.5 px-2">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="sidebar-link"
        :class="collapsed ? 'justify-center px-0' : 'px-3'"
        :title="collapsed ? item.label : undefined"
      >
        <component :is="item.icon" class="w-5 h-5 shrink-0" />
        <span v-if="!collapsed" class="text-sm">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <!-- Bottom: settings + user -->
    <div class="border-t border-gray-200 py-3 px-2 flex flex-col gap-0.5">
      <RouterLink
        to="/settings"
        class="sidebar-link"
        :class="collapsed ? 'justify-center px-0' : 'px-3'"
        title="Settings"
      >
        <IconSettings class="w-5 h-5 shrink-0" />
        <span v-if="!collapsed" class="text-sm">Settings</span>
      </RouterLink>

      <div class="mt-2 border-t border-gray-100 pt-2">
        <div v-if="!collapsed" class="flex items-center gap-2 px-3 py-1.5 text-xs text-gray-500 truncate">
          <IconUser class="w-4 h-4 shrink-0 text-gray-400" />
          <span class="truncate">{{ auth.user?.name }}</span>
        </div>
        <button
          @click="auth.logout()"
          class="sidebar-link w-full text-red-500 hover:text-red-700 hover:bg-red-50"
          :class="collapsed ? 'justify-center px-0' : 'px-3'"
          title="Logout"
        >
          <IconLogout class="w-5 h-5 shrink-0" />
          <span v-if="!collapsed" class="text-sm">Logout</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, defineComponent, h } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const collapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')

function toggle() {
  collapsed.value = !collapsed.value
  localStorage.setItem('sidebar-collapsed', String(collapsed.value))
  setTimeout(() => window.dispatchEvent(new Event('resize')), 210)
}

// Inline SVG icon components
const IconDashboard = defineComponent({
  render: () => h('svg', { viewBox: '0 0 20 20', fill: 'currentColor' }, [
    h('path', { d: 'M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z' }),
  ]),
})

const IconAnalyses = defineComponent({
  render: () => h('svg', { viewBox: '0 0 20 20', fill: 'currentColor' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z', 'clip-rule': 'evenodd' }),
  ]),
})

const IconCarriers = defineComponent({
  render: () => h('svg', { viewBox: '0 0 20 20', fill: 'currentColor' }, [
    h('path', { d: 'M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z' }),
    h('path', { d: 'M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1v-1h1a1 1 0 00.894-.553l2-4A1 1 0 0014 9h-3V5a1 1 0 00-1-1H3z' }),
    h('path', { d: 'M11 9h2.236l-1.5 3H11V9z' }),
  ]),
})

const IconSettings = defineComponent({
  render: () => h('svg', { viewBox: '0 0 20 20', fill: 'currentColor' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z', 'clip-rule': 'evenodd' }),
  ]),
})

const IconUser = defineComponent({
  render: () => h('svg', { viewBox: '0 0 20 20', fill: 'currentColor' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z', 'clip-rule': 'evenodd' }),
  ]),
})

const IconLogout = defineComponent({
  render: () => h('svg', { viewBox: '0 0 20 20', fill: 'currentColor' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z', 'clip-rule': 'evenodd' }),
  ]),
})

const navItems = [
  { to: '/', label: 'Dashboard', icon: IconDashboard },
  { to: '/runs', label: 'Analyses', icon: IconAnalyses },
  { to: '/carriers', label: 'Carriers', icon: IconCarriers },
]
</script>

<style scoped>
.sidebar-link {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  height: 2.25rem;
  border-radius: 0.375rem;
  color: #6b7280;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.15s, background-color 0.15s;
  width: 100%;
}
.sidebar-link:hover {
  color: #111827;
  background-color: #f3f4f6;
}
.router-link-active.sidebar-link {
  color: #2563eb;
  background-color: #eff6ff;
}
</style>
