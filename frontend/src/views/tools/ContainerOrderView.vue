<template>
  <div>
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
      <RouterLink to="/tools" class="text-sm" style="color:var(--app-text-sec)">Tools</RouterLink>
      <span style="color:var(--app-text-sec)">›</span>
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:var(--app-text);line-height:1.14;letter-spacing:-0.28px">
        Container Order — Kardex VBM Box
      </h2>
    </div>

    <div class="card-apple" style="max-width:1100px">

      <!-- Step indicator -->
      <div class="flex items-center gap-2 mb-5" style="font-size:11.5px;color:var(--app-text-sec)">
        <span :class="{ 'step-active': step === 'select-run' }">1. Analiza</span>
        <span>›</span>
        <span :class="{ 'step-active': step === 'params' }">2. Parametry</span>
        <span>›</span>
        <span :class="{ 'step-active': step === 'review' }">3. Przegląd</span>
        <span>›</span>
        <span :class="{ 'step-active': step === 'summary' }">4. Podsumowanie</span>
        <span>›</span>
        <span :class="{ 'step-active': step === 'export' }">5. Eksport</span>
      </div>

      <!-- Step 1: select run -->
      <div v-if="step === 'select-run'">
        <p style="font-size:14px;font-weight:600;color:var(--app-text);margin-bottom:4px">Wybierz ukończoną analizę</p>
        <p class="mb-4" style="font-size:13px;color:var(--app-text-sec)">
          Lista zawiera tylko analizy, w których przeprowadzono Capacity dla nośnika MiB 640×440.
        </p>

        <p v-if="store.loading" style="color:var(--app-text-sec);font-size:13px">Ładowanie…</p>
        <p v-else-if="store.error" style="color:#ff3b30;font-size:13px">{{ store.error }}</p>
        <p v-else-if="store.eligible.length === 0" style="color:var(--app-text-sec);font-size:13px">
          Brak ukończonych analiz z nośnikiem MiB 640×440. Wróć po uruchomieniu analizy pojemnościowej z tym nośnikiem.
        </p>

        <div v-else class="space-y-2 mb-5">
          <button
            v-for="a in store.eligible"
            :key="a.run_id"
            type="button"
            class="run-card"
            :class="{ 'is-selected': store.currentRun?.run_id === a.run_id }"
            @click="store.selectRun(a)"
          >
            <div class="flex items-center justify-between mb-1">
              <span style="font-size:14px;font-weight:600;color:var(--app-text)">{{ a.client_name }}</span>
              <span style="font-size:11.5px;color:var(--app-text-sec)">{{ formatDate(a.created_at) }}</span>
            </div>
            <div class="flex flex-wrap items-center gap-4" style="font-size:12px;color:var(--app-text-sec)">
              <span>SKU: <strong style="color:var(--app-text)">{{ a.sku_count.toLocaleString() }}</strong></span>
              <span>FIT: <strong style="color:var(--app-text)">{{ a.fit_pct.toFixed(1) }}%</strong></span>
              <span v-if="a.has_performance">
                ABC: A {{ a.abc_distribution.A || 0 }} · B {{ a.abc_distribution.B || 0 }} · C {{ a.abc_distribution.C || 0 }}
              </span>
              <span v-else style="color:#f59e0b">⚠ brak Performance (filtr ABC niedostępny)</span>
            </div>
          </button>
        </div>

        <button
          class="btn-apple-primary"
          :disabled="!store.currentRun"
          @click="goToParams"
        >Użyj tej analizy →</button>
      </div>

      <!-- Step 2: parameters -->
      <div v-else-if="step === 'params'">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p style="font-size:14px;font-weight:600;color:var(--app-text);margin-bottom:2px">Parametry planowania</p>
            <p style="font-size:12px;color:var(--app-text-sec)">
              Analiza: <span style="color:var(--app-text);font-weight:500">{{ store.currentRun?.client_name }}</span>
            </p>
          </div>
          <button @click="step = 'select-run'" class="text-xs" style="color:var(--app-text-sec)">← Wróć</button>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 mb-5">
          <!-- ABC -->
          <div>
            <label class="label-apple">Klasy ABC do planowania</label>
            <div class="flex gap-3" style="font-size:13px">
              <label v-for="c in ['A','B','C']" :key="c" class="flex items-center gap-1.5" style="color:var(--app-text)">
                <input type="checkbox" :checked="store.params.abc_classes.includes(c)" @change="toggleAbc(c)" />
                {{ c }}
              </label>
            </div>
          </div>

          <!-- Machine toggle -->
          <div>
            <label class="label-apple">Tylko SKU "Machine"</label>
            <label class="toggle-switch">
              <input type="checkbox" v-model="store.params.only_machine" />
              <span class="toggle-slider"></span>
            </label>
          </div>

          <!-- Stock multiplier -->
          <div>
            <label class="label-apple">Bufor zapasu (×{{ store.params.stock_multiplier.toFixed(2) }})</label>
            <input type="range" min="0.5" max="3.0" step="0.1"
                   v-model.number="store.params.stock_multiplier" class="w-full" />
          </div>

          <!-- Fill rate -->
          <div>
            <label class="label-apple">Wypełnienie lokalizacji ({{ (store.params.location_fill_rate * 100).toFixed(0) }}%)</label>
            <input type="range" min="0.5" max="1.0" step="0.05"
                   v-model.number="store.params.location_fill_rate" class="w-full" />
          </div>

          <!-- Min/Max locations -->
          <div>
            <label class="label-apple">Min lokacji / SKU</label>
            <input type="number" min="1" v-model.number="store.params.min_locations_per_sku" class="input-apple-sm" style="width:120px" />
          </div>
          <div>
            <label class="label-apple">Max lokacji / SKU</label>
            <input type="number" min="1" v-model.number="store.params.max_locations_per_sku" class="input-apple-sm" style="width:120px" />
          </div>
        </div>

        <!-- Mode -->
        <div class="mb-4">
          <label class="label-apple">Tryb doboru wariantów</label>
          <div class="flex flex-wrap gap-2" style="font-size:13px">
            <button
              v-for="m in ['auto','guided','manual']" :key="m"
              type="button"
              @click="store.params.mode = m as 'auto' | 'guided' | 'manual'"
              :class="store.params.mode === m ? 'btn-apple-primary' : 'btn-apple-pill'"
              style="font-size:12.5px;padding:6px 14px"
            >{{ modeLabel(m) }}</button>
          </div>
        </div>

        <!-- Auto sub-params -->
        <div v-if="store.params.mode === 'auto'" class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 mb-4 p-3 rounded-lg" style="background:var(--table-header-bg)">
          <div>
            <label class="label-apple">Maks. liczba wariantów ({{ store.params.auto_max_variants }})</label>
            <input type="range" min="3" max="15" step="1"
                   v-model.number="store.params.auto_max_variants" class="w-full" />
          </div>
          <div>
            <label class="label-apple">Cel optymalizacji</label>
            <select v-model="store.params.auto_goal" class="input-apple-sm" style="width:100%;max-width:280px">
              <option value="min_waste">Minimum marnotrawstwa</option>
              <option value="min_bins">Minimum pojemników</option>
              <option value="max_coverage">Maksymalne pokrycie SKU</option>
            </select>
          </div>
        </div>

        <!-- Guided sub-params -->
        <div v-else-if="store.params.mode === 'guided'" class="mb-4 p-3 rounded-lg" style="background:var(--table-header-bg)">
          <label class="label-apple">Preset</label>
          <select v-model="store.params.guided_preset" class="input-apple-sm" style="width:100%;max-width:320px">
            <option value="simple">Prosta operacja (3 footprinty × 2 wys.)</option>
            <option value="standard">Standardowa (greedy, 8 wariantów)</option>
            <option value="full_coverage">Pełne pokrycie (greedy do 99%)</option>
          </select>
        </div>

        <!-- Manual sub-params -->
        <div v-else-if="store.params.mode === 'manual'" class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <p style="font-size:13px;color:var(--app-text);font-weight:500">Wybierz warianty (48 dostępnych)</p>
            <span style="font-size:12px;color:var(--app-text-sec)">
              Zaznaczone: {{ store.params.manual_variant_codes.length }}
            </span>
          </div>
          <div class="flex gap-2 mb-2" style="font-size:11.5px">
            <button class="btn-apple-pill" style="font-size:11px;padding:4px 10px" @click="manualSelectAuto">+ Auto-zestaw 28</button>
            <button class="btn-apple-pill" style="font-size:11px;padding:4px 10px" @click="manualSelectAll">+ Wszystkie 48</button>
            <button class="btn-apple-pill" style="font-size:11px;padding:4px 10px" @click="manualClear">Wyczyść</button>
          </div>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-1.5 max-h-72 overflow-y-auto p-2 rounded-lg" style="background:var(--table-header-bg);font-size:11px">
            <label
              v-for="v in store.catalogFull" :key="v.code"
              class="flex items-center gap-1.5 px-1.5 py-1 rounded"
              style="cursor:pointer;color:var(--app-text)"
            >
              <input type="checkbox" :checked="store.params.manual_variant_codes.includes(v.code)" @change="toggleManual(v.code)" />
              <span style="font-family:monospace">{{ v.code }}</span>
            </label>
          </div>
        </div>

        <p v-if="store.error" style="color:#ff3b30;font-size:13px" class="mb-3">{{ store.error }}</p>

        <button
          class="btn-apple-primary"
          :disabled="store.loading"
          @click="doCalculate"
        >{{ store.loading ? 'Obliczanie…' : 'Oblicz plan →' }}</button>
      </div>

      <!-- Step 3: review -->
      <div v-else-if="step === 'review' && store.plan">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p style="font-size:14px;font-weight:600;color:var(--app-text);margin-bottom:2px">Przegląd przypisania SKU → wariant</p>
            <p style="font-size:12px;color:var(--app-text-sec)">
              Wybrano {{ store.plan.summaries.length }} wariantów ·
              pokrycie {{ store.plan.coverage_pct.toFixed(1) }}% ({{ store.plan.total_sku_covered }} / {{ store.plan.total_sku_planned }} SKU)
            </p>
          </div>
          <button @click="step = 'params'" class="text-xs" style="color:var(--app-text-sec)">← Wróć</button>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
          <!-- Variant cards grid -->
          <div>
            <p class="mb-2" style="font-size:12px;color:var(--app-text-sec);font-weight:500">Wybrane warianty (kliknij, by zobaczyć 3D)</p>
            <div class="grid grid-cols-2 gap-2 max-h-80 overflow-y-auto pr-1">
              <VariantCard
                v-for="s in store.plan.summaries" :key="s.code"
                :variant="variantInfoFor(s.code)"
                :selected="selectedVariantCode === s.code"
                :sku-count="s.sku_count"
                :bin-count="s.bins_required"
                :avg-fill="s.avg_fill_pct"
                @click="selectedVariantCode = s.code"
              />
            </div>
          </div>

          <!-- 3D preview -->
          <div>
            <p class="mb-2" style="font-size:12px;color:var(--app-text-sec);font-weight:500">Podgląd 3D pojemnika</p>
            <Bin3DPreview :variant="selectedVariantInfo" />
          </div>
        </div>

        <!-- Orphans warning -->
        <div v-if="store.plan.orphans.length > 0" class="mb-4 p-3 rounded-lg" style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.4)">
          <p style="font-size:12.5px;color:#92400e">
            <strong>⚠ {{ store.plan.orphans.length }} SKU bez przypisania</strong>
            — żaden z wybranych wariantów ich nie pomieści. Rozważ zwiększenie liczby wariantów (krok 2) lub przejście w tryb Manual.
          </p>
        </div>

        <SkuAssignmentTable :assignments="store.plan.assignments" />

        <div class="flex justify-end mt-5">
          <button class="btn-apple-primary" @click="step = 'summary'">Dalej →</button>
        </div>
      </div>

      <!-- Step 4: summary -->
      <div v-else-if="step === 'summary' && store.plan">
        <div class="flex items-center justify-between mb-4">
          <p style="font-size:14px;font-weight:600;color:var(--app-text)">Podsumowanie zamówienia</p>
          <button @click="step = 'review'" class="text-xs" style="color:var(--app-text-sec)">← Wróć</button>
        </div>

        <!-- Hero counter -->
        <div class="text-center mb-5 p-5 rounded-xl" style="background:var(--table-header-bg)">
          <p style="font-size:12px;color:var(--app-text-sec);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:4px">
            Łącznie pojemników do zamówienia
          </p>
          <p style="font-size:48px;font-weight:700;color:var(--app-text);line-height:1;letter-spacing:-1.5px">
            {{ store.plan.total_bins.toLocaleString() }}
          </p>
          <p style="font-size:12px;color:var(--app-text-sec);margin-top:6px">
            {{ store.plan.summaries.length }} wariantów · pokrycie {{ store.plan.coverage_pct.toFixed(1) }}% · śr. wypełnienie {{ store.plan.avg_fill_pct.toFixed(0) }}%
          </p>
        </div>

        <!-- Table with manual ± adjustments -->
        <div class="overflow-x-auto mb-4" style="border:1px solid var(--app-border);border-radius:10px">
          <table class="w-full" style="font-size:12.5px;border-collapse:collapse">
            <thead style="background:var(--table-header-bg)">
              <tr>
                <th class="px-3 py-2 text-left" style="color:var(--app-text-sec);font-weight:500">Wariant</th>
                <th class="px-3 py-2 text-left" style="color:var(--app-text-sec);font-weight:500">Footprint</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Wys mm</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">SKU</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Lokacji</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Pojemniki</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Wyp.</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in store.plan.summaries" :key="s.code" style="border-top:1px solid var(--table-divider)">
                <td class="px-3 py-1.5" style="color:var(--app-text);font-family:monospace;font-size:11.5px">{{ s.code }}</td>
                <td class="px-3 py-1.5" style="color:var(--app-text-sec)">{{ s.footprint_label }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text)">{{ s.bin_height_mm }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text)">{{ s.sku_count }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text)">{{ s.total_locations }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text);font-weight:600">{{ s.bins_required }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ s.avg_fill_pct.toFixed(0) }}%</td>
              </tr>
              <tr style="background:var(--table-header-bg);font-weight:600">
                <td class="px-3 py-2" colspan="5" style="color:var(--app-text)">RAZEM</td>
                <td class="px-3 py-2 text-right" style="color:var(--app-text)">{{ store.plan.total_bins }}</td>
                <td class="px-3 py-2 text-right" style="color:var(--app-text-sec)">{{ store.plan.avg_fill_pct.toFixed(0) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="store.plan.orphans.length > 0" style="font-size:12px;color:#92400e">
          ⚠ {{ store.plan.orphans.length }} SKU nie zostało przypisanych — będą wymienione w arkuszu "Orphans" eksportu.
        </p>

        <div class="flex justify-end mt-5">
          <button class="btn-apple-primary" @click="step = 'export'">Przejdź do eksportu →</button>
        </div>
      </div>

      <!-- Step 5: export -->
      <div v-else-if="step === 'export' && store.plan">
        <div class="flex items-center justify-between mb-4">
          <p style="font-size:14px;font-weight:600;color:var(--app-text)">Eksportuj zamówienie</p>
          <button @click="step = 'summary'" class="text-xs" style="color:var(--app-text-sec)">← Wróć</button>
        </div>

        <p class="mb-5" style="font-size:13px;color:var(--app-text-sec)">
          Wybierz format. Excel zawiera 4 arkusze (Order Summary, SKU Assignment, Parameters, Orphans). PDF — 2-stronicowe podsumowanie.
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
          <button
            v-for="fmt in (['xlsx','pdf','csv'] as const)" :key="fmt"
            class="card-apple text-center"
            :disabled="exporting !== ''"
            style="cursor:pointer"
            @click="doExport(fmt)"
          >
            <p style="font-size:32px;font-weight:700;color:#0071e3;letter-spacing:-1px;margin-bottom:2px">
              {{ fmt.toUpperCase() }}
            </p>
            <p style="font-size:12px;color:var(--app-text-sec)">
              {{ fmt === 'xlsx' ? 'multi-sheet Excel' : fmt === 'pdf' ? '2-stronicowy raport' : 'jeden arkusz' }}
            </p>
            <p v-if="exporting === fmt" style="font-size:11px;color:#0071e3;margin-top:4px">Generowanie…</p>
          </button>
        </div>

        <div class="flex gap-3">
          <button class="btn-apple-pill" @click="reset">↺ Nowe zamówienie</button>
          <RouterLink to="/tools" class="btn-apple-pill">← Wróć do Tools</RouterLink>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useContainerOrderStore } from '@/stores/containerOrder'
import { useNotificationsStore } from '@/stores/notifications'
import VariantCard from '@/components/VariantCard.vue'
import Bin3DPreview from '@/components/Bin3DPreview.vue'
import SkuAssignmentTable from '@/components/SkuAssignmentTable.vue'
import type { VariantInfo } from '@/api/containerOrder'

const store = useContainerOrderStore()
const notify = useNotificationsStore()

type Step = 'select-run' | 'params' | 'review' | 'summary' | 'export'
const step = ref<Step>('select-run')

const selectedVariantCode = ref<string | null>(null)
const exporting = ref<'' | 'xlsx' | 'pdf' | 'csv'>('')

onMounted(async () => {
  await Promise.all([store.loadEligible(), store.loadCatalog()])
})

function formatDate(s: string): string {
  try {
    return new Date(s).toLocaleDateString('pl-PL', {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  } catch {
    return s
  }
}

function modeLabel(m: string): string {
  return m === 'auto' ? 'Auto' : m === 'guided' ? 'Guided' : 'Manual'
}

function toggleAbc(c: string) {
  const set = new Set<string>(store.params.abc_classes)
  if (set.has(c)) set.delete(c)
  else set.add(c)
  store.params.abc_classes = Array.from(set)
}

function toggleManual(code: string) {
  const set = new Set<string>(store.params.manual_variant_codes)
  if (set.has(code)) set.delete(code)
  else set.add(code)
  store.params.manual_variant_codes = Array.from(set)
}

function manualSelectAuto() {
  store.params.manual_variant_codes = [...store.catalogAutoCodes]
}
function manualSelectAll() {
  store.params.manual_variant_codes = store.catalogFull.map(v => v.code)
}
function manualClear() {
  store.params.manual_variant_codes = []
}

function goToParams() {
  step.value = 'params'
}

async function doCalculate() {
  const plan = await store.calculate()
  if (plan) {
    selectedVariantCode.value = plan.summaries[0]?.code || null
    step.value = 'review'
  } else {
    notify.push({ type: 'error', title: 'Obliczenie nieudane', message: store.error })
  }
}

const variantMap = computed(() => {
  const m: Record<string, VariantInfo> = {}
  for (const v of store.catalogFull) m[v.code] = v
  return m
})

function variantInfoFor(code: string): VariantInfo {
  return variantMap.value[code] || {
    code, footprint_key: '', footprint_label: '',
    cell_length_mm: 0, cell_width_mm: 0, cell_height_mm: 0, bin_height_mm: 0,
    locations_per_bin: 1, max_weight_kg_per_cell: 0, cell_volume_L: 0,
    in_auto_catalog: false,
  }
}

const selectedVariantInfo = computed<VariantInfo | null>(() => {
  return selectedVariantCode.value ? variantInfoFor(selectedVariantCode.value) : null
})

async function doExport(format: 'xlsx' | 'pdf' | 'csv') {
  if (!store.plan || !store.currentRun) return
  exporting.value = format
  try {
    const blob = await store.exportFile(format)
    if (!blob) return
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const safe = (store.currentRun.client_name || 'analysis').replace(/[^a-zA-Z0-9_-]/g, '_')
    a.download = `container_order_${safe}.${format}`
    a.click()
    URL.revokeObjectURL(url)
    notify.push({
      type: 'success', title: 'Wygenerowano plik',
      message: `${format.toUpperCase()} — ${a.download}`,
    })
  } catch (e) {
    notify.push({
      type: 'error', title: 'Eksport nieudany',
      message: (e as Error).message || 'Spróbuj ponownie.',
    })
  } finally {
    exporting.value = ''
  }
}

function reset() {
  store.reset()
  selectedVariantCode.value = null
  step.value = 'select-run'
}
</script>

<style scoped>
.step-active {
  color: var(--app-text);
  font-weight: 600;
}
.run-card {
  display: block;
  width: 100%;
  text-align: left;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 10px;
  padding: 12px 14px;
  cursor: pointer;
  transition: border-color 120ms ease, background 120ms ease;
}
.run-card:hover {
  border-color: #0071e3;
}
.run-card.is-selected {
  border-color: #0071e3;
  background: rgba(0, 113, 227, 0.06);
  box-shadow: 0 0 0 2px rgba(0, 113, 227, 0.25);
}
</style>
