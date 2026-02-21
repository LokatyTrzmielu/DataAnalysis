<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-lg font-semibold text-gray-800">Carriers</h2>
      <button
        @click="showForm = !showForm"
        class="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
      >
        {{ showForm ? 'Cancel' : 'Add carrier' }}
      </button>
    </div>

    <!-- Add carrier form -->
    <div v-if="showForm" class="bg-white border border-gray-200 rounded-lg p-4 mb-6">
      <h3 class="text-sm font-medium text-gray-700 mb-4">New carrier</h3>
      <div class="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label class="block text-xs text-gray-600 mb-1">Carrier ID</label>
          <input v-model="form.carrier_id" class="input-field" placeholder="e.g. NOSNIK_4" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Name</label>
          <input v-model="form.name" class="input-field" placeholder="600x400x220" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Length (mm)</label>
          <input v-model.number="form.inner_length_mm" type="number" class="input-field" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Width (mm)</label>
          <input v-model.number="form.inner_width_mm" type="number" class="input-field" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Height (mm)</label>
          <input v-model.number="form.inner_height_mm" type="number" class="input-field" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Max weight (kg)</label>
          <input v-model.number="form.max_weight_kg" type="number" step="0.1" class="input-field" />
        </div>
      </div>
      <p v-if="formError" class="text-red-600 text-sm mb-3">{{ formError }}</p>
      <button
        @click="addCarrier"
        :disabled="saving"
        class="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded disabled:opacity-50"
      >
        {{ saving ? 'Saving…' : 'Save' }}
      </button>
    </div>

    <!-- Carrier list -->
    <div v-if="carriersStore.loading" class="text-sm text-gray-400">Loading…</div>
    <div v-else class="bg-white border border-gray-200 rounded-lg divide-y divide-gray-100">
      <div
        v-for="c in carriersStore.carriers"
        :key="c.carrier_id"
        class="flex items-center justify-between px-4 py-3"
      >
        <div>
          <span class="text-sm font-medium text-gray-800">{{ c.name }}</span>
          <span class="ml-2 text-xs text-gray-400">{{ c.carrier_id }}</span>
          <span
            v-if="!c.is_active"
            class="ml-2 text-xs bg-gray-100 text-gray-500 rounded px-1"
          >inactive</span>
          <span
            v-if="c.is_predefined"
            class="ml-2 text-xs bg-blue-50 text-blue-600 rounded px-1"
          >predefined</span>
        </div>
        <div class="flex items-center gap-4 text-xs text-gray-500">
          <span>{{ c.inner_length_mm }}×{{ c.inner_width_mm }}×{{ c.inner_height_mm }} mm</span>
          <span>{{ c.max_weight_kg }} kg</span>
          <button
            v-if="!c.is_predefined"
            @click="remove(c.carrier_id)"
            class="text-red-500 hover:text-red-700"
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

<style>
.input-field {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  padding: 0.375rem 0.625rem;
  font-size: 0.875rem;
}
.input-field:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.4);
}
</style>
