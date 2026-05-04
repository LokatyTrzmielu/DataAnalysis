<template>
  <div class="fixed inset-0 flex items-center justify-center z-50" style="background:rgba(0,0,0,0.6)" @click.self="$emit('close')">
    <div class="card-apple-elevated w-full" style="max-width:480px">
      <div class="flex items-center justify-between mb-5">
        <h3 style="font-size:21px;font-weight:700;color:var(--app-text);letter-spacing:0.231px;line-height:1.19">Notes</h3>
        <button @click="$emit('close')" style="color:var(--app-placeholder);background:none;border:none;cursor:pointer;padding:4px;transition:color 0.15s" @mouseover="(e: Event) => (e.currentTarget as HTMLElement).style.color='#1d1d1f'" @mouseleave="(e: Event) => (e.currentTarget as HTMLElement).style.color='rgba(0,0,0,0.32)'">
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
        class="input-apple resize-none"
        style="font-size:14px;letter-spacing:-0.224px"
      />
      <div class="mt-2 h-4">
        <span v-if="notesSaved" style="font-size:12px;color:#34c759">Saved</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useRunStore } from '@/stores/run'
import { useNotificationsStore } from '@/stores/notifications'

const props = defineProps<{ runId: string; initialNotes: string }>()
const emit = defineEmits<{ close: []; saved: [value: string] }>()

const runStore = useRunStore()
const notify = useNotificationsStore()
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
    notify.push({ type: 'success', title: 'Notes saved' })
    setTimeout(() => { notesSaved.value = false }, 2000)
  }, 500)
}

onUnmounted(() => { if (notesTimer) clearTimeout(notesTimer) })
</script>
