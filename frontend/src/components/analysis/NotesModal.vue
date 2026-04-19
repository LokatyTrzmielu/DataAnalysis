<template>
  <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
      <div class="flex items-center justify-between mb-5">
        <h3 class="text-base font-semibold text-gray-800">Notes</h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
          <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>

      <textarea
        v-model="localNotes"
        @input="scheduleNotesSave"
        placeholder="Add notes about this analysis…"
        rows="5"
        class="w-full text-sm text-gray-700 border border-gray-200 rounded p-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
      <span v-if="notesSaved" class="text-xs text-green-500">Saved</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useRunStore } from '@/stores/run'

const props = defineProps<{ runId: string; initialNotes: string }>()
const emit = defineEmits<{ close: []; saved: [value: string] }>()

const runStore = useRunStore()
const localNotes = ref(props.initialNotes)
const notesSaved = ref(false)
let notesTimer: ReturnType<typeof setTimeout> | null = null

function scheduleNotesSave() {
  notesSaved.value = false
  if (notesTimer) clearTimeout(notesTimer)
  notesTimer = setTimeout(async () => {
    await runStore.patchRun(props.runId, { notes: localNotes.value })
    emit('saved', localNotes.value)
    notesSaved.value = true
    setTimeout(() => { notesSaved.value = false }, 2000)
  }, 500)
}

onUnmounted(() => { if (notesTimer) clearTimeout(notesTimer) })
</script>
