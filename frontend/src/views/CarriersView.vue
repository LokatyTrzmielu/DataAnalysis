<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:var(--app-text);line-height:1.14;letter-spacing:-0.28px">
        Carriers
      </h2>
      <button @click="toggleCreate" class="btn-apple-primary">
        {{ showForm && !editingCarrierId ? 'Cancel' : 'Add carrier' }}
      </button>
    </div>

    <!-- Form (create or edit) -->
    <div v-if="showForm" class="card-apple mb-6">
      <div class="flex items-center justify-between mb-4">
        <h3 style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px">
          {{ editingCarrierId ? 'Edit carrier' : 'New carrier' }}
        </h3>
        <button
          v-if="editingCarrierId"
          @click="cancelEdit"
          style="font-size:12px;color:var(--app-text-sec);background:none;border:none;cursor:pointer;padding:0"
        >Cancel</button>
      </div>
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
        <div v-if="editingCarrierId" class="flex items-center gap-2" style="padding-top:20px">
          <input type="checkbox" v-model="form.is_active" id="is_active" style="cursor:pointer" />
          <label for="is_active" class="label-apple" style="font-size:12px;cursor:pointer;margin:0">Active</label>
        </div>
      </div>
      <p v-if="formError" class="mb-3" style="font-size:14px;color:#ff3b30">{{ formError }}</p>
      <button @click="saveCarrier" :disabled="saving" class="btn-apple-primary">
        {{ saving ? 'Saving…' : 'Save' }}
      </button>
    </div>

    <!-- Carrier list -->
    <div v-if="carriersStore.loading" style="font-size:14px;color:var(--app-text-sec)">Loading…</div>
    <div v-else class="card-apple-list">
      <div
        v-for="c in carriersStore.carriers"
        :key="c.carrier_id"
        class="flex items-center justify-between px-4 py-3"
      >
        <div>
          <span style="font-size:17px;color:var(--app-text);letter-spacing:-0.374px">{{ c.name }}</span>
          <span class="ml-2" style="font-size:12px;color:var(--app-text-sec)">{{ c.carrier_id }}</span>
          <span
            v-if="!c.is_active"
            class="ml-2 rounded px-1.5 py-0.5"
            style="font-size:11px;background:rgba(0,0,0,0.06);color:var(--app-text-sec)"
          >inactive</span>
          <span
            v-if="c.is_predefined"
            class="ml-2 rounded px-1.5 py-0.5"
            style="font-size:11px;background:rgba(0,113,227,0.08);color:#0066cc"
          >predefined</span>
        </div>
        <div class="flex items-center gap-4" style="font-size:12px;color:var(--app-text-sec)">
          <span>{{ c.inner_length_mm }}×{{ c.inner_width_mm }}×{{ c.inner_height_mm }} mm</span>
          <span>{{ c.max_weight_kg }} kg</span>
          <button
            @click="startEdit(c)"
            style="font-size:12px;color:#0071e3;background:none;border:none;cursor:pointer;padding:0"
            @mouseover="(e) => (e.currentTarget as HTMLElement).style.color='#0066cc'"
            @mouseleave="(e) => (e.currentTarget as HTMLElement).style.color='#0071e3'"
          >Edit</button>
          <button
            v-if="!c.is_predefined"
            @click="remove(c.carrier_id)"
            style="font-size:12px;color:#ff3b30;background:none;border:none;cursor:pointer;padding:0"
            @mouseover="(e) => (e.currentTarget as HTMLElement).style.color='#d93025'"
            @mouseleave="(e) => (e.currentTarget as HTMLElement).style.color='#ff3b30'"
          >Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useCarriersStore } from '@/stores/carriers'
import type { Carrier } from '@/api/carriers'

const carriersStore = useCarriersStore()
const showForm = ref(false)
const editingCarrierId = ref<string | null>(null)
const saving = ref(false)
const formError = ref('')

const form = reactive({
  carrier_id: '',
  name: '',
  inner_length_mm: 0,
  inner_width_mm: 0,
  inner_height_mm: 0,
  max_weight_kg: 0,
  is_active: true,
})

onMounted(() => carriersStore.fetchCarriers())

function toggleCreate() {
  if (showForm.value && !editingCarrierId.value) {
    showForm.value = false
  } else {
    editingCarrierId.value = null
    Object.assign(form, { carrier_id: '', name: '', inner_length_mm: 0, inner_width_mm: 0, inner_height_mm: 0, max_weight_kg: 0, is_active: true })
    showForm.value = true
    formError.value = ''
  }
}

function startEdit(c: Carrier) {
  editingCarrierId.value = c.carrier_id
  Object.assign(form, {
    carrier_id: c.carrier_id,
    name: c.name,
    inner_length_mm: c.inner_length_mm,
    inner_width_mm: c.inner_width_mm,
    inner_height_mm: c.inner_height_mm,
    max_weight_kg: c.max_weight_kg,
    is_active: c.is_active,
  })
  showForm.value = true
  formError.value = ''
}

function cancelEdit() {
  showForm.value = false
  editingCarrierId.value = null
}

async function saveCarrier() {
  formError.value = ''
  saving.value = true
  try {
    if (editingCarrierId.value) {
      await carriersStore.updateCarrier(editingCarrierId.value, {
        carrier_id: form.carrier_id,
        name: form.name,
        inner_length_mm: form.inner_length_mm,
        inner_width_mm: form.inner_width_mm,
        inner_height_mm: form.inner_height_mm,
        max_weight_kg: form.max_weight_kg,
        is_active: form.is_active,
      })
    } else {
      await carriersStore.createCarrier({ ...form })
    }
    showForm.value = false
    editingCarrierId.value = null
    Object.assign(form, { carrier_id: '', name: '', inner_length_mm: 0, inner_width_mm: 0, inner_height_mm: 0, max_weight_kg: 0, is_active: true })
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
