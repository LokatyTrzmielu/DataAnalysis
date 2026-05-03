import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const dark = ref(localStorage.getItem('theme') === 'dark')

  watch(dark, (isDark) => {
    document.documentElement.classList.toggle('dark', isDark)
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }, { immediate: true })

  function toggle() { dark.value = !dark.value }

  return { dark, toggle }
})
