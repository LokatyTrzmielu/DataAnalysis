<template>
  <div class="fixed inset-0 flex items-center justify-center z-50" style="background:rgba(0,0,0,0.6)" @click.self="$emit('close')">
    <div class="card-apple-elevated w-full" style="max-width:480px">
      <div class="flex items-center justify-between mb-5">
        <h3 style="font-size:21px;font-weight:700;color:#1d1d1f;letter-spacing:0.231px;line-height:1.19">Share analysis</h3>
        <button @click="$emit('close')" style="color:rgba(0,0,0,0.32);background:none;border:none;cursor:pointer;padding:4px;transition:color 0.15s" @mouseover="(e: Event) => (e.currentTarget as HTMLElement).style.color='#1d1d1f'" @mouseleave="(e: Event) => (e.currentTarget as HTMLElement).style.color='rgba(0,0,0,0.32)'">
          <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>

      <!-- Add share -->
      <form @submit.prevent="addShare" class="flex gap-2 mb-5">
        <input
          v-model="emailInput"
          type="email"
          placeholder="User email…"
          class="input-apple flex-1"
          required
        />
        <button type="submit" :disabled="adding" class="btn-apple-primary" style="white-space:nowrap">
          Share
        </button>
      </form>
      <p v-if="addError" class="mb-3" style="font-size:14px;color:#ff3b30">{{ addError }}</p>

      <!-- Current shares -->
      <div v-if="loading" style="font-size:14px;color:rgba(0,0,0,0.48)">Loading…</div>
      <div v-else-if="shares.length === 0" style="font-size:14px;color:rgba(0,0,0,0.48)">Not shared with anyone yet.</div>
      <ul v-else style="border-top:1px solid rgba(0,0,0,0.08)">
        <li v-for="s in shares" :key="s.user_id" class="flex items-center justify-between py-3" style="border-bottom:1px solid rgba(0,0,0,0.08)">
          <div>
            <span style="font-size:14px;font-weight:600;color:#1d1d1f;letter-spacing:-0.224px">{{ s.name }}</span>
            <span class="ml-2" style="font-size:12px;color:rgba(0,0,0,0.48)">{{ s.email }}</span>
          </div>
          <button
            @click="revoke(s.user_id)"
            style="font-size:12px;color:#ff3b30;background:none;border:none;cursor:pointer;padding:0"
            @mouseover="(e: Event) => (e.currentTarget as HTMLElement).style.color='#d93025'"
            @mouseleave="(e: Event) => (e.currentTarget as HTMLElement).style.color='#ff3b30'"
          >Revoke</button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { runsApi, type RunShareItem } from '@/api/runs'

const props = defineProps<{ runId: string }>()
defineEmits<{ close: [] }>()

const shares = ref<RunShareItem[]>([])
const loading = ref(true)
const emailInput = ref('')
const adding = ref(false)
const addError = ref('')

onMounted(async () => {
  try {
    const { data } = await runsApi.getShares(props.runId)
    shares.value = data
  } finally {
    loading.value = false
  }
})

async function addShare() {
  addError.value = ''
  adding.value = true
  try {
    const { data } = await runsApi.addShare(props.runId, emailInput.value)
    shares.value.push(data)
    emailInput.value = ''
  } catch (e: any) {
    addError.value = e?.response?.data?.detail ?? 'Failed to share.'
  } finally {
    adding.value = false
  }
}

async function revoke(userId: string) {
  await runsApi.removeShare(props.runId, userId)
  shares.value = shares.value.filter(s => s.user_id !== userId)
}
</script>
