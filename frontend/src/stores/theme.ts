import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const stored = localStorage.getItem('theme')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const dark = ref(stored ? stored === 'dark' : prefersDark)

  watch(dark, (isDark) => {
    document.documentElement.classList.toggle('dark', isDark)
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }, { immediate: true })

  function toggle() { dark.value = !dark.value }

  return { dark, toggle }
})
