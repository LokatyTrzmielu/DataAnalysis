<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:#1d1d1f;line-height:1.14;letter-spacing:-0.28px">
        Carriers
      </h2>
      <button @click="showForm = !showForm" class="btn-apple-primary">
        {{ showForm ? 'Cancel' : 'Add carrier' }}
      </button>
    </div>

    <!-- Add carrier form -->
    <div v-if="showForm" class="card-apple mb-6">
      <h3 class="mb-4" style="font-size:14px;font-weight:600;color:#1d1d1f;letter-spacing:-0.224px">New carrier</h3>
      <div class="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label class="label-apple" style="font-size:12px">Carrier ID</label>
          <input v-model="form.carrier_id" class="input-apple-sm" placeholder="e.g. NOSNIK_4" />
        </div>
        <div>
          <label class="label-apple" style="font-size:12px">Name</label>
          <input v-model="form.name" class="input-apple-sm" placeholder="600x400x220" />
        </div>
        <div>
          <label class="label-apple" style="font-size:12px">Length (mm)</label>
          <input v-model.number="form.inner_length_mm" type="number" class="input-apple-sm" />
        </div>
        <div>
          <label class="label-apple" style="font-size:12px">Width (mm)</label>
          <input v-model.number="form.inner_width_mm" type="number" class="input-apple-sm" />
        </div>
        <div>
          <label class="label-apple" style="font-size:12px">Height (mm)</label>
          <input v-model.number="form.inner_height_mm" type="number" class="input-apple-sm" />
        </div>
        <div>
          <label class="label-apple" style="font-size:12px">Max weight (kg)</label>
          <input v-model.number="form.max_weight_kg" type="number" step="0.1" class="input-apple-sm" />
        </div>
      </div>
      <p v-if="formError" class="mb-3" style="font-size:14px;color:#ff3b30">{{ formError }}</p>
      <button @click="addCarrier" :disabled="saving" class="btn-apple-primary">
        {{ saving ? 'Saving…' : 'Save' }}
      </button>
    </div>

    <!-- Carrier list -->
    <div v-if="carriersStore.loading" style="font-size:14px;color:rgba(0,0,0,0.48)">Loading…</div>
    <div v-else class="card-apple-list">
      <div
        v-for="c in carriersStore.carriers"
        :key="c.carrier_id"
        class="flex items-center justify-between px-4 py-3"
      >
        <div>
          <span style="font-size:17px;color:#1d1d1f;letter-spacing:-0.374px">{{ c.name }}</span>
          <span class="ml-2" style="font-size:12px;color:rgba(0,0,0,0.48)">{{ c.carrier_id }}</span>
          <span
            v-if="!c.is_active"
            class="ml-2 rounded px-1.5 py-0.5"
            style="font-size:11px;background:rgba(0,0,0,0.06);color:rgba(0,0,0,0.48)"
          >inactive</span>
          <span
            v-if="c.is_predefined"
            class="ml-2 rounded px-1.5 py-0.5"
            style="font-size:11px;background:rgba(0,113,227,0.08);color:#0066cc"
          >predefined</span>
        </div>
        <div class="flex items-center gap-4" style="font-size:12px;color:rgba(0,0,0,0.48)">
          <span>{{ c.inner_length_mm }}×{{ c.inner_width_mm }}×{{ c.inner_height_mm }} mm</span>
          <span>{{ c.max_weight_kg }} kg</span>
          <button
            v-if="!c.is_predefined"
            @click="remove(c.carrier_id)"
            style="font-size:12px;color:#ff3b30;background:none;border:none;cursor:pointer;padding:0"
            @mouseover="(e) => (e.currentTarget as HTMLElement).style.color='#d93025'"
            @mouseleave="(e) => (e.currentTarget as HTMLElement).style.color='#ff3b30'"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useCarriersStore } from '@/stores/carriers'

const carriersStore = useCarriersStore()
const showForm = ref(false)
const saving = ref(false)
const formError = ref('')

const form = reactive({
  carrier_id: '',
  name: '',
  inner_length_mm: 0,
  inner_width_mm: 0,
  inner_height_mm: 0,
  max_weight_kg: 0,
})

onMounted(() => carriersStore.fetchCarriers())

async function addCarrier() {
  formError.value = ''
  saving.value = true
  try {
    await carriersStore.createCarrier({ ...form })
    showForm.value = false
    Object.assign(form, { carrier_id: '', name: '', inner_length_mm: 0, inner_width_mm: 0, inner_height_mm: 0, max_weight_kg: 0 })
  } catch {
    formError.value = 'Failed to save carrier. Check all fields.'
  } finally {
    saving.value = false
  }
}

async function remove(carrierId: string) {
  if (!confirm('Delete this carrier?')) return
  await carriersStore.deleteCarrier(carrierId)
}
</script>
