import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAnalysisStore = defineStore('analysis', () => {
  const isAnalyzing = ref(false)
  function start() { isAnalyzing.value = true }
  function stop()  { isAnalyzing.value = false }
  return { isAnalyzing, start, stop }
})
