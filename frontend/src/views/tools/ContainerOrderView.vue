<template>
  <div>
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
      <RouterLink to="/tools" class="text-sm" style="color:var(--app-text-sec)">Tools</RouterLink>
      <span style="color:var(--app-text-sec)">›</span>
      <!-- Container Order glyph (same shape as on the Tools tile). Animates as a
           pulsing loading indicator while a plan is being computed. -->
      <svg
        class="page-icon"
        :class="{ 'is-loading': store.loading }"
        viewBox="0 0 20 20"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        aria-hidden="true"
      >
        <rect x="2.5" y="5.5" width="15" height="10" rx="1"/>
        <line x1="2.5" y1="10.5" x2="17.5" y2="10.5"/>
        <line x1="7.5" y1="5.5" x2="7.5" y2="15.5"/>
        <line x1="12.5" y1="5.5" x2="12.5" y2="15.5"/>
      </svg>
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:var(--app-text);line-height:1.14;letter-spacing:-0.28px">
        Container Order — Kardex VBM Box
      </h2>
    </div>

    <!-- Tabs -->
    <div class="tool-tab-nav">
      <button
        v-for="t in tabs"
        :key="t.id"
        type="button"
        class="tool-tab-btn"
        :class="{ active: step === t.id }"
        :disabled="t.disabled"
        :title="t.disabledReason"
        @click="!t.disabled && (step = t.id)"
      >
        {{ t.label }}
      </button>
    </div>

    <div class="pt-6">

      <!-- Step 1: select run -->
      <div v-if="step === 'select-run'">
        <p style="font-size:14px;font-weight:600;color:var(--app-text);margin-bottom:4px">Select a completed analysis</p>
        <p class="mb-4" style="font-size:13px;color:var(--app-text-sec);line-height:1.5">
          The list contains analyses with the MiB 640×440 carrier. <strong style="color:var(--app-text)">The tool plans only SKUs that physically fit in MiB</strong> — others (NOT_FIT for MiB) are excluded, regardless of whether they fit other carriers in the analysis.
        </p>

        <p v-if="store.loading" style="color:var(--app-text-sec);font-size:13px">Loading…</p>
        <p v-else-if="store.error" style="color:#ff3b30;font-size:13px">{{ store.error }}</p>
        <p v-else-if="store.eligible.length === 0" style="color:var(--app-text-sec);font-size:13px">
          No completed analyses with the MiB 640×440 carrier. Come back after running a capacity analysis that includes this carrier.
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
            <div class="flex items-center justify-between mb-1.5">
              <span style="font-size:14px;font-weight:600;color:var(--app-text)">{{ a.client_name }}</span>
              <span style="font-size:11.5px;color:var(--app-text-sec)">{{ formatDate(a.created_at) }}</span>
            </div>

            <!-- Primary line: what the tool will actually plan -->
            <div v-if="a.mib_planned_sku > 0" style="font-size:12.5px;color:var(--app-text);margin-bottom:3px">
              To plan (MiB 640×440):
              <strong style="color:#0071e3">{{ a.mib_planned_sku.toLocaleString() }} SKUs</strong>
              <span style="color:var(--app-text-sec)"> · {{ a.mib_fit_pct.toFixed(1) }}% fit in MiB</span>
            </div>
            <div v-else class="warning-text" style="font-size:12.5px;margin-bottom:3px">
              ⚠ <strong>0 SKUs fit in MiB 640×440</strong> — the tool cannot generate an order.
            </div>

            <!-- Secondary line: context (dataset-wide) -->
            <div class="flex flex-wrap items-center gap-x-3 gap-y-1" style="font-size:11.5px;color:var(--app-text-sec)">
              <span>of {{ a.sku_count.toLocaleString() }} SKUs in dataset</span>
              <span v-if="a.carriers_analyzed.length > 1">
                · {{ a.carriers_analyzed.length }} carriers in analysis
              </span>
              <span v-if="a.has_performance">
                · ABC: A {{ a.abc_distribution.A || 0 }} · B {{ a.abc_distribution.B || 0 }} · C {{ a.abc_distribution.C || 0 }}
              </span>
              <span v-else style="color:#f59e0b">· ⚠ no Performance (ABC filter unavailable)</span>
            </div>
          </button>
        </div>

        <button
          class="btn-apple-primary"
          :disabled="!store.currentRun || (store.currentRun?.mib_planned_sku ?? 0) === 0"
          @click="goToParams"
        >Use this analysis →</button>
      </div>

      <!-- Step 2: Calculation (params + results in one tab) -->
      <div v-else-if="step === 'review'">
        <div class="mb-4">
          <p style="font-size:14px;font-weight:600;color:var(--app-text);margin-bottom:2px">Plan calculation</p>
          <p style="font-size:12px;color:var(--app-text-sec)">
            <template v-if="store.currentRun">
              Analysis: <span style="color:var(--app-text);font-weight:500">{{ store.currentRun.client_name }}</span>
              ·
              <strong style="color:var(--app-text)">{{ store.currentRun.mib_planned_sku.toLocaleString() }} SKUs</strong>
              fitting MiB 640×440 (FIT + BORDERLINE)
            </template>
            <template v-else-if="store.sourceMissing">
              Plan restored from history — source analysis is no longer available.
            </template>
          </p>
        </div>

        <!-- Source-missing banner: user can still view + export, but cannot re-calc -->
        <div v-if="store.sourceMissing && store.plan" class="warning-panel mb-4 p-3 rounded-lg">
          <p class="warning-text" style="font-size:12.5px">
            <strong>⚠ Source analysis no longer available.</strong>
            You can still review and export this saved plan, but re-calculation with new
            parameters is disabled because the underlying analysis data was deleted.
          </p>
        </div>

        <!-- ─── Compact parameters block ─── -->
        <div class="params-compact mb-5">
          <!-- Row 1: ABC checkboxes + 2 toggles -->
          <div class="params-row">
            <div class="param-cell">
              <span class="param-label">ABC classes</span>
              <div class="flex gap-2.5" style="font-size:13px">
                <label v-for="c in ['A','B','C']" :key="c" class="flex items-center gap-1.5" style="color:var(--app-text)">
                  <input type="checkbox" :checked="store.params.abc_classes.includes(c)" @change="toggleAbc(c)" />
                  {{ c }}
                </label>
              </div>
            </div>
            <div class="param-cell toggle-inline" title="Filter out SKUs marked Non-machine based on Performance.">
              <span class="param-label" style="margin-bottom:0">Only Machine</span>
              <button
                type="button"
                class="toggle-switch"
                :class="{ 'is-on': store.params.only_machine }"
                :aria-pressed="store.params.only_machine"
                aria-label="Only Machine SKUs"
                @click="store.params.only_machine = !store.params.only_machine"
              ></button>
            </div>
            <div class="param-cell toggle-inline" title="OFF → SKUs with missing values fall into orphans with reason 'missing_dimensions'.">
              <span class="param-label" style="margin-bottom:0">Impute missing</span>
              <button
                type="button"
                class="toggle-switch"
                :class="{ 'is-on': store.params.impute_missing_dimensions }"
                :aria-pressed="store.params.impute_missing_dimensions"
                aria-label="Impute missing dimensions"
                @click="store.params.impute_missing_dimensions = !store.params.impute_missing_dimensions"
              ></button>
            </div>
          </div>

          <!-- Row 2: sliders -->
          <div class="params-row">
            <div class="param-cell slider-cell">
              <label class="param-label">Stock buffer <span class="param-value">×{{ store.params.stock_multiplier.toFixed(2) }}</span></label>
              <input type="range" min="0.5" max="3.0" step="0.1"
                     v-model.number="store.params.stock_multiplier" class="w-full" />
            </div>
            <div class="param-cell slider-cell">
              <label class="param-label">Fill rate <span class="param-value">{{ (store.params.location_fill_rate * 100).toFixed(0) }}%</span></label>
              <input type="range" min="0.5" max="1.0" step="0.05"
                     v-model.number="store.params.location_fill_rate" class="w-full" />
            </div>
            <div v-if="store.params.mode === 'auto'" class="param-cell slider-cell">
              <label class="param-label">Max variants <span class="param-value">{{ store.params.auto_max_variants }}</span></label>
              <input type="range" min="3" max="15" step="1"
                     v-model.number="store.params.auto_max_variants" class="w-full" />
            </div>
          </div>

          <!-- Row 3: mode pills + mode-specific dropdown + min/max + Calculate button -->
          <div class="params-row params-row-actions">
            <div class="param-cell">
              <span class="param-label">Mode</span>
              <div class="flex gap-1.5">
                <button
                  v-for="m in ['auto','guided','manual']" :key="m"
                  type="button"
                  @click="store.params.mode = m as 'auto' | 'guided' | 'manual'"
                  :class="store.params.mode === m ? 'btn-apple-primary' : 'btn-apple-pill'"
                  style="font-size:12px;padding:5px 11px"
                >{{ modeLabel(m) }}</button>
              </div>
            </div>
            <div v-if="store.params.mode === 'auto'" class="param-cell">
              <label class="param-label">Goal</label>
              <select v-model="store.params.auto_goal" class="input-apple-sm" style="width:200px">
                <option value="min_waste">Minimum waste</option>
                <option value="min_bins">Minimum bins</option>
                <option value="max_coverage">Max SKU coverage</option>
              </select>
            </div>
            <div v-else-if="store.params.mode === 'guided'" class="param-cell">
              <label class="param-label">Preset</label>
              <select v-model="store.params.guided_preset" class="input-apple-sm" style="width:240px">
                <option value="simple">Simple (3 footprints × 2 heights)</option>
                <option value="standard">Standard (greedy, 8)</option>
                <option value="full_coverage">Full coverage (up to 99%)</option>
              </select>
            </div>
            <div class="param-cell">
              <label class="param-label">Min loc.</label>
              <input type="number" min="1" v-model.number="store.params.min_locations_per_sku" class="input-apple-sm" style="width:80px" />
            </div>
            <div class="param-cell">
              <label class="param-label">Max loc.</label>
              <input type="number" min="1" v-model.number="store.params.max_locations_per_sku" class="input-apple-sm" style="width:96px" />
            </div>
            <div class="param-cell calc-cell">
              <button
                class="btn-apple-primary calc-btn"
                :disabled="store.loading || store.sourceMissing"
                :title="store.sourceMissing ? 'Source analysis is no longer available' : ''"
                @click="doCalculate"
              >
                <svg
                  v-if="store.loading"
                  class="calc-spinner"
                  viewBox="0 0 16 16"
                  width="14"
                  height="14"
                  aria-hidden="true"
                >
                  <circle
                    cx="8" cy="8" r="6"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-dasharray="28"
                    stroke-dashoffset="14"
                  />
                </svg>
                {{ store.loading ? 'Calculating…' : 'Calculate plan →' }}
              </button>
            </div>
          </div>

          <!-- Manual mode: variant picker (full-width row, only in manual) -->
          <div v-if="store.params.mode === 'manual'" class="params-row manual-row">
            <div style="flex:1 1 100%">
              <div class="flex items-center justify-between mb-1">
                <span class="param-label" style="margin-bottom:0">Pick variants (48 available)</span>
                <span style="font-size:11.5px;color:var(--app-text-sec)">
                  Selected: {{ store.params.manual_variant_codes.length }}
                </span>
              </div>
              <div class="flex gap-2 mb-2" style="font-size:11.5px">
                <button class="btn-apple-pill" style="font-size:11px;padding:3px 9px" @click="manualSelectAuto">+ Auto 28</button>
                <button class="btn-apple-pill" style="font-size:11px;padding:3px 9px" @click="manualSelectAll">+ All 48</button>
                <button class="btn-apple-pill" style="font-size:11px;padding:3px 9px" @click="manualClear">Clear</button>
              </div>
              <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-1 max-h-48 overflow-y-auto p-2 rounded-lg" style="background:var(--table-header-bg);font-size:11px">
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
          </div>

          <p v-if="store.error" class="mt-2" style="color:#ff3b30;font-size:13px;margin-bottom:0">{{ store.error }}</p>
        </div>

        <!-- ─── Results block (only after a plan exists) ─── -->
        <div v-if="store.plan">
          <div class="mb-4">
            <p style="font-size:14px;font-weight:600;color:var(--app-text);margin-bottom:2px">Planning results</p>
            <p style="font-size:12px;color:var(--app-text-sec)">
              Selected {{ store.plan.summaries.length }} variants ·
              coverage {{ store.plan.coverage_pct.toFixed(1) }}% ({{ store.plan.total_sku_covered }} / {{ store.plan.total_sku_planned }} SKUs)
            </p>
          </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-5">
          <!-- Variant cards grid (2/3 of row → 3 cards per row) -->
          <div class="lg:col-span-2">
            <p class="mb-2" style="font-size:12px;color:var(--app-text-sec);font-weight:500">Selected variants (click to view 3D)</p>
            <div class="variant-grid">
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

          <!-- 3D preview (1/3 of row) -->
          <div>
            <p class="mb-2" style="font-size:12px;color:var(--app-text-sec);font-weight:500">Bin 3D preview</p>
            <Bin3DPreview :variant="selectedVariantInfo" />
          </div>
        </div>

        <!-- Orphans warning -->
        <div v-if="store.plan.orphans.length > 0" class="warning-panel mb-4 p-3 rounded-lg">
          <p style="font-size:12.5px" class="warning-text">
            <strong>⚠ {{ store.plan.orphans.length }} unassigned SKUs</strong>
            — none of the selected variants fits them. Consider increasing the number of variants or switching to Manual mode.
          </p>
        </div>

        <SkuAssignmentTable
          :assignments="store.plan.assignments"
          :selected-abc-classes="store.params.abc_classes"
          title="SKU table"
        />

          <div class="flex justify-end gap-2 mt-5">
            <button
              v-if="store.currentSavedId"
              type="button"
              class="btn-apple-pill"
              disabled
              title="This plan is already stored in History."
            >Saved ✓</button>
            <button
              v-else
              type="button"
              class="btn-apple-pill"
              :disabled="savingPlan"
              @click="openSaveModal"
            >{{ savingPlan ? 'Saving…' : 'Save plan' }}</button>
            <button class="btn-apple-primary" @click="step = 'summary'">Next →</button>
          </div>
        </div>

        <!-- Placeholder when no plan has been computed yet. -->
        <div v-else class="empty-plan-hint">
          Adjust the parameters above and click <strong style="color:var(--app-text)">“Calculate plan →”</strong> to see the planning results.
        </div>
      </div>

      <!-- Step 3: summary -->
      <div v-else-if="step === 'summary' && store.plan">
        <p class="mb-4" style="font-size:14px;font-weight:600;color:var(--app-text)">Order summary</p>

        <!-- Hero counter -->
        <div class="text-center mb-5 p-5 rounded-xl" style="background:var(--table-header-bg)">
          <p style="font-size:12px;color:var(--app-text-sec);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:4px">
            Total bins to order
          </p>
          <p style="font-size:48px;font-weight:700;color:var(--app-text);line-height:1;letter-spacing:-1.5px">
            {{ store.plan.total_bins.toLocaleString() }}
          </p>
          <p style="font-size:12px;color:var(--app-text-sec);margin-top:6px">
            {{ store.plan.summaries.length }} variants · coverage {{ store.plan.coverage_pct.toFixed(1) }}% · avg fill {{ store.plan.avg_fill_pct.toFixed(0) }}%
          </p>
        </div>

        <!-- Variant order table — Bins, Bases and Frames give the procurement breakdown.
             Bases always equals Bins (1 base per physical bin); Frames depends on tier
             via (bin_height_mm - 138) / 50. -->
        <div class="overflow-x-auto mb-4" style="border:1px solid var(--app-border);border-radius:10px">
          <table class="w-full" style="font-size:12.5px;border-collapse:collapse;table-layout:fixed">
            <colgroup>
              <col style="width:12%" />
              <col style="width:26%" />
              <col style="width:9%" />
              <col style="width:9%" />
              <col style="width:10%" />
              <col style="width:9%" />
              <col style="width:9%" />
              <col style="width:9%" />
              <col style="width:7%" />
            </colgroup>
            <thead style="background:var(--table-header-bg)">
              <tr>
                <th class="px-3 py-2 text-left" style="color:var(--app-text-sec);font-weight:500">Variant</th>
                <th class="px-3 py-2 text-left" style="color:var(--app-text-sec);font-weight:500">Footprint</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Height mm</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">SKUs</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Locations</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Bins</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500" title="Base containers (1 per bin)">Bases</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500" title="EasyClick frames per variant (bins × frames_per_bin)">Frames</th>
                <th class="px-3 py-2 text-right" style="color:var(--app-text-sec);font-weight:500">Fill</th>
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
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text)">{{ s.bins_required }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text)">{{ s.total_frames_required }}</td>
                <td class="px-3 py-1.5 text-right" style="color:var(--app-text-sec)">{{ s.avg_fill_pct.toFixed(0) }}%</td>
              </tr>
              <tr style="background:var(--table-header-bg);font-weight:600">
                <td class="px-3 py-2" colspan="5" style="color:var(--app-text)">TOTAL</td>
                <td class="px-3 py-2 text-right" style="color:var(--app-text)">{{ store.plan.total_bins }}</td>
                <td class="px-3 py-2 text-right" style="color:var(--app-text)">{{ store.plan.total_bins }}</td>
                <td class="px-3 py-2 text-right" style="color:var(--app-text)">{{ store.plan.total_frames }}</td>
                <td class="px-3 py-2 text-right" style="color:var(--app-text-sec)">{{ store.plan.avg_fill_pct.toFixed(0) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="store.plan.orphans.length > 0" class="warning-text" style="font-size:12px">
          ⚠ {{ store.plan.orphans.length }} SKUs were not assigned — they will be listed in the “Orphans” sheet of the export.
        </p>

        <div class="flex justify-end mt-5">
          <button class="btn-apple-primary" @click="step = 'export'">Go to export →</button>
        </div>
      </div>

      <!-- Step 5: export -->
      <div v-else-if="step === 'export' && store.plan">
        <p class="mb-2" style="font-size:14px;font-weight:600;color:var(--app-text)">Export the order</p>
        <p class="mb-5" style="font-size:13px;color:var(--app-text-sec)">
          Choose a format. Excel contains 4 sheets (Order Summary, SKU Assignment, Parameters, Orphans). PDF — a 2-page summary.
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
              {{ fmt === 'xlsx' ? 'multi-sheet Excel' : fmt === 'pdf' ? '2-page report' : 'single sheet' }}
            </p>
            <p v-if="exporting === fmt" style="font-size:11px;color:#0071e3;margin-top:4px">Generating…</p>
          </button>
        </div>

        <div class="flex gap-3">
          <button class="btn-apple-pill" @click="reset">↺ New order</button>
          <RouterLink to="/tools" class="btn-apple-pill">← Back to Tools</RouterLink>
        </div>
      </div>

      <!-- Step 6: History (always reachable) -->
      <div v-else-if="step === 'history'">
        <div class="flex items-center justify-between mb-3">
          <div>
            <p style="font-size:14px;font-weight:600;color:var(--app-text);margin-bottom:2px">Saved plans</p>
            <p style="font-size:12px;color:var(--app-text-sec)">
              Plans you explicitly saved from the Calculation tab. Open one to restore parameters and results.
            </p>
          </div>
          <button class="btn-apple-pill" :disabled="store.savedPlansLoading" @click="refreshHistory">
            {{ store.savedPlansLoading ? 'Loading…' : '↻ Refresh' }}
          </button>
        </div>

        <p v-if="store.savedPlansError" style="color:#ff3b30;font-size:13px">{{ store.savedPlansError }}</p>

        <div v-if="!store.savedPlansLoading && store.savedPlans.length === 0" class="empty-history">
          No saved plans yet. After calculating, click <strong style="color:var(--app-text)">“Save plan”</strong> to keep a copy here.
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="p in store.savedPlans"
            :key="p.id"
            class="history-card"
          >
            <div class="flex items-start justify-between gap-3 mb-1.5">
              <div style="min-width:0;flex:1 1 auto">
                <div class="flex items-center gap-2 flex-wrap">
                  <span style="font-size:14px;font-weight:600;color:var(--app-text);overflow:hidden;text-overflow:ellipsis">{{ p.label }}</span>
                  <span class="mode-chip">{{ p.mode || '—' }}</span>
                  <span
                    v-if="!p.source_run_available"
                    class="chip-imputed"
                    title="The source analysis has been deleted."
                  >source missing</span>
                </div>
                <p v-if="p.client_name && p.client_name !== p.label" style="font-size:11.5px;color:var(--app-text-sec);margin:2px 0 0">
                  {{ p.client_name }}
                </p>
              </div>
              <span style="font-size:11.5px;color:var(--app-text-sec);white-space:nowrap">{{ formatDate(p.created_at) }}</span>
            </div>

            <div class="kpi-strip">
              <span><strong style="color:var(--app-text)">{{ p.total_bins.toLocaleString() }}</strong> bins</span>
              <span>·</span>
              <span><strong style="color:var(--app-text)">{{ p.total_frames.toLocaleString() }}</strong> frames</span>
              <span>·</span>
              <span>coverage <strong style="color:var(--app-text)">{{ p.coverage_pct.toFixed(1) }}%</strong></span>
              <span>·</span>
              <span><strong style="color:var(--app-text)">{{ p.total_sku_covered.toLocaleString() }}</strong> SKUs</span>
            </div>

            <div class="history-actions">
              <button class="btn-apple-pill" style="font-size:11.5px;padding:4px 11px" @click="loadFromHistory(p.id)">Load →</button>
              <button class="btn-apple-pill" style="font-size:11.5px;padding:4px 11px" @click="renamePrompt(p)">Rename</button>
              <button class="btn-apple-pill" style="font-size:11.5px;padding:4px 11px;color:#ff3b30" @click="deletePrompt(p)">Delete</button>
            </div>
          </div>
        </div>

        <div v-if="store.savedPlans.length < store.savedPlansTotal" class="flex items-center justify-center mt-4">
          <button class="btn-apple-pill" style="font-size:12px" @click="loadMoreHistory">
            Load more ({{ (store.savedPlansTotal - store.savedPlans.length).toLocaleString() }} remaining)
          </button>
        </div>
      </div>

    </div>

    <!-- Save plan modal -->
    <div v-if="saveModalOpen" class="save-modal-overlay" @click.self="closeSaveModal">
      <div class="card-apple-elevated save-modal">
        <h3 style="font-size:15px;font-weight:600;color:var(--app-text);margin:0 0 12px;letter-spacing:-0.24px">Save plan to history</h3>
        <label class="label-apple" style="font-size:12px">Label</label>
        <input
          ref="saveLabelInput"
          v-model="saveLabel"
          type="text"
          class="input-apple-sm"
          style="width:100%;margin-bottom:12px"
          @keydown.enter="confirmSave"
          @keydown.escape="closeSaveModal"
        />
        <label class="label-apple" style="font-size:12px">Notes (optional)</label>
        <textarea
          v-model="saveNotes"
          class="input-apple-sm"
          rows="3"
          style="width:100%;resize:vertical;font-family:inherit"
        ></textarea>
        <p v-if="saveError" style="color:#ff3b30;font-size:12.5px;margin-top:8px;margin-bottom:0">{{ saveError }}</p>
        <div class="flex justify-end gap-2 mt-4">
          <button class="btn-apple-pill" :disabled="savingPlan" @click="closeSaveModal">Cancel</button>
          <button class="btn-apple-primary" :disabled="savingPlan" @click="confirmSave">
            {{ savingPlan ? 'Saving…' : 'Save plan' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useContainerOrderStore } from '@/stores/containerOrder'
import { useNotificationsStore } from '@/stores/notifications'
import VariantCard from '@/components/VariantCard.vue'
import Bin3DPreview from '@/components/Bin3DPreview.vue'
import SkuAssignmentTable from '@/components/SkuAssignmentTable.vue'
import type { VariantInfo } from '@/api/containerOrder'

const store = useContainerOrderStore()
const notify = useNotificationsStore()

type Step = 'select-run' | 'review' | 'summary' | 'export' | 'history'
const step = ref<Step>('select-run')

const selectedVariantCode = ref<string | null>(null)
const exporting = ref<'' | 'xlsx' | 'pdf' | 'csv'>('')

// History — page size matches API default; "Load more" appends.
const historyPageSize = 20
const historyPage = ref(1)

// Save modal
const saveModalOpen = ref(false)
const saveLabel = ref('')
const saveNotes = ref('')
const saveError = ref('')
const savingPlan = ref(false)
const saveLabelInput = ref<HTMLInputElement | null>(null)

const tabs = computed<Array<{ id: Step; label: string; disabled: boolean; disabledReason: string }>>(() => {
  // After loading a saved plan, currentRun may be null while plan + sourceMissing
  // are set — still allow the Calculation tab so the user can view the snapshot.
  const hasRun = !!store.currentRun && (store.currentRun.mib_planned_sku ?? 0) > 0
  const reviewReachable = hasRun || !!store.plan
  const hasPlan = !!store.plan
  return [
    { id: 'select-run', label: 'Analysis', disabled: false, disabledReason: '' },
    { id: 'review', label: 'Calculation', disabled: !reviewReachable,
      disabledReason: reviewReachable ? '' : 'First pick an analysis with SKUs that fit MiB.' },
    { id: 'summary', label: 'Summary', disabled: !hasPlan,
      disabledReason: hasPlan ? '' : 'First click “Calculate plan →” in the Calculation tab.' },
    { id: 'export', label: 'Export', disabled: !hasPlan,
      disabledReason: hasPlan ? '' : 'First click “Calculate plan →” in the Calculation tab.' },
    { id: 'history', label: 'History', disabled: false, disabledReason: '' },
  ]
})

onMounted(async () => {
  await Promise.all([store.loadEligible(), store.loadCatalog()])
})

function formatDate(s: string): string {
  try {
    return new Date(s).toLocaleDateString('en-GB', {
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
  // Was a separate tab; the params block now lives at the top of the Calculation tab.
  step.value = 'review'
}

async function doCalculate() {
  const plan = await store.calculate()
  if (plan) {
    selectedVariantCode.value = plan.summaries[0]?.code || null
    step.value = 'review'
  } else {
    notify.push({ type: 'error', title: 'Calculation failed', message: store.error })
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
      type: 'success', title: 'File generated',
      message: `${format.toUpperCase()} — ${a.download}`,
    })
  } catch (e) {
    notify.push({
      type: 'error', title: 'Export failed',
      message: (e as Error).message || 'Please try again.',
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

// ── History tab ───────────────────────────────────────────────────────────

async function refreshHistory() {
  historyPage.value = 1
  await store.listSavedPlans(1, historyPageSize)
}

async function loadMoreHistory() {
  historyPage.value += 1
  // Append: fetch next page and merge. The store's listSavedPlans replaces the
  // list, so we briefly snapshot the current items, load, then prepend ours back.
  const existing = [...store.savedPlans]
  await store.listSavedPlans(historyPage.value, historyPageSize)
  store.savedPlans = [...existing, ...store.savedPlans.filter(p => !existing.find(e => e.id === p.id))]
}

async function loadFromHistory(planId: string) {
  const ok = await store.loadSavedPlan(planId)
  if (!ok) {
    notify.push({ type: 'error', title: 'Load failed', message: store.error })
    return
  }
  // Bring SKU table into a sensible state after load.
  selectedVariantCode.value = store.plan?.summaries[0]?.code || null
  step.value = 'review'
  if (store.sourceMissing) {
    notify.push({
      type: 'info',
      title: 'Source analysis missing',
      message: 'You can view and export this saved plan, but re-calculation is disabled.',
    })
  }
}

async function renamePrompt(p: { id: string; label: string }) {
  const next = window.prompt('Rename saved plan:', p.label)
  if (next === null) return
  const trimmed = next.trim()
  if (!trimmed || trimmed === p.label) return
  try {
    await store.renameSavedPlan(p.id, trimmed)
    notify.push({ type: 'success', title: 'Renamed', message: trimmed })
  } catch (e) {
    notify.push({ type: 'error', title: 'Rename failed', message: (e as Error).message || 'Try again.' })
  }
}

async function deletePrompt(p: { id: string; label: string }) {
  if (!window.confirm(`Delete saved plan “${p.label}”? This cannot be undone.`)) return
  try {
    await store.deleteSavedPlan(p.id)
    notify.push({ type: 'success', title: 'Deleted', message: p.label })
  } catch (e) {
    notify.push({ type: 'error', title: 'Delete failed', message: (e as Error).message || 'Try again.' })
  }
}

// ── Save plan modal ───────────────────────────────────────────────────────

function openSaveModal() {
  if (!store.plan || !store.currentRun) return
  const today = new Date().toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric' })
  saveLabel.value = `${store.currentRun.client_name} — ${today}`
  saveNotes.value = ''
  saveError.value = ''
  saveModalOpen.value = true
  // Focus the label input shortly after the modal mounts.
  setTimeout(() => saveLabelInput.value?.select(), 30)
}

function closeSaveModal() {
  if (savingPlan.value) return
  saveModalOpen.value = false
}

async function confirmSave() {
  if (savingPlan.value || !store.plan) return
  const label = saveLabel.value.trim()
  if (!label) {
    saveError.value = 'Please enter a label.'
    return
  }
  savingPlan.value = true
  saveError.value = ''
  try {
    await store.savePlan(label, saveNotes.value.trim() || undefined)
    saveModalOpen.value = false
    notify.push({ type: 'success', title: 'Plan saved to history', message: label })
  } catch (e) {
    saveError.value = (e as Error).message || 'Save failed. Try again.'
  } finally {
    savingPlan.value = false
  }
}

// Auto-load history when user opens that tab.
watch(step, (next) => {
  if (next === 'history' && store.savedPlans.length === 0 && !store.savedPlansLoading) {
    refreshHistory()
  }
})
</script>

<style scoped>
.tool-tab-nav {
  display: flex;
  border-bottom: 1px solid var(--app-border);
  gap: 0;
}
.tool-tab-btn {
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 400;
  letter-spacing: -0.224px;
  color: var(--app-text-sec);
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
  font-family: "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
}
.tool-tab-btn:hover:not(:disabled) { color: var(--app-text); }
.tool-tab-btn.active {
  color: #0071e3;
  border-bottom-color: #0071e3;
  font-weight: 600;
}
.tool-tab-btn:disabled {
  color: var(--app-text-sec);
  opacity: 0.45;
  cursor: not-allowed;
}

/* ─── Compact parameters block (lives on top of the Calculation tab) ───
   All controls stay visible while the user reviews the computed plan below,
   so they can tweak and re-run without leaving the tab. Three horizontal
   rows: (1) filters + toggles, (2) sliders, (3) mode + dropdown + numerics
   + Oblicz button. */
.params-compact {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 10px;
  padding: 14px 16px;
}
.params-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 14px 22px;
  margin-bottom: 12px;
}
.params-row:last-child { margin-bottom: 0; }
.params-row.manual-row { margin-top: 4px; }

.param-cell {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.param-cell.toggle-inline {
  flex-direction: row;
  align-items: center;
  gap: 10px;
  padding-bottom: 4px;
}
.param-cell.slider-cell {
  flex: 1 1 200px;
  max-width: 320px;
}
.param-cell.calc-cell {
  margin-left: auto;
  align-self: flex-end;
}

.param-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--app-text-sec);
  letter-spacing: 0.2px;
  margin-bottom: 4px;
  white-space: nowrap;
}
.param-value {
  color: var(--app-text);
  font-weight: 600;
  margin-left: 2px;
}

/* Placeholder shown in the Calculation tab before the first calculation. */
.empty-plan-hint {
  text-align: center;
  padding: 36px 16px;
  color: var(--app-text-sec);
  font-size: 13px;
  border: 1px dashed var(--app-border);
  border-radius: 10px;
}

/* ─── History tab ─── */
.empty-history {
  text-align: center;
  padding: 40px 16px;
  color: var(--app-text-sec);
  font-size: 13px;
  border: 1px dashed var(--app-border);
  border-radius: 10px;
}
.history-card {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 10px;
  padding: 12px 14px;
  transition: border-color 120ms ease, background 120ms ease;
}
.history-card:hover { border-color: #0071e3; }

.kpi-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0 6px;
  font-size: 11.5px;
  color: var(--app-text-sec);
  margin-bottom: 8px;
}

.history-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.mode-chip {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  padding: 1px 6px;
  line-height: 16px;
  border-radius: 4px;
  background: rgba(0, 113, 227, 0.10);
  color: #0071e3;
}
:global(html.dark) .mode-chip {
  background: rgba(0, 132, 255, 0.20);
  color: #5ab2ff;
}

/* ─── Save plan modal ─── */
.save-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1100;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.save-modal { width: 100%; max-width: 380px; }

/* Reused "imputed" chip — also used on history cards as the "source missing" badge. */
.chip-imputed {
  display: inline-block;
  font-size: 9.5px;
  font-weight: 600;
  line-height: 14px;
  background: #fef3c7;
  color: #92400e;
  border-radius: 4px;
  padding: 0 4px;
}
:global(html.dark) .chip-imputed {
  background: rgba(245, 158, 11, 0.20);
  color: #fcd34d;
}

/* Tool glyph beside the page title. Doubles as a loading indicator: pulses
   while a plan is being computed (store.loading). */
.page-icon {
  width: 26px;
  height: 26px;
  color: #0071e3;
  flex-shrink: 0;
}
.page-icon.is-loading {
  animation: page-icon-pulse 1s ease-in-out infinite;
}
@keyframes page-icon-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.4; transform: scale(0.9); }
}

/* Spinner inside the "Oblicz plan →" button while computing. */
.calc-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.calc-spinner {
  animation: calc-spinner-rotate 0.85s linear infinite;
  flex-shrink: 0;
}
@keyframes calc-spinner-rotate {
  to { transform: rotate(360deg); }
}

/* Warning text — readable on both light cards (dark brown on yellow) and dark
   cards (warm amber on near-black). Used for orphan and "no MiB SKUs" callouts. */
.warning-text { color: #92400e; }
:global(html.dark) .warning-text { color: #fcd34d; }

.warning-panel {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.4);
}
:global(html.dark) .warning-panel {
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.45);
}

/* Smaller, blue iOS-style toggle (overrides the global .toggle-switch). */
.toggle-switch {
  width: 34px;
  height: 20px;
  border-radius: 980px;
  background: rgba(120, 120, 128, 0.32);
  position: relative;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
  flex-shrink: 0;
  padding: 0;
  display: inline-block;
  vertical-align: middle;
}
.toggle-switch.is-on { background: #0071e3; }
.toggle-switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s;
}
.toggle-switch.is-on::after { transform: translateX(14px); }

/* Variant grid: matches Bin3DPreview height (320px) when there are few cards
   (2 rows × 6 cards fits exactly), but grows up to 480px for more variants
   before scrolling. Rows always at least 140px so card content (header + svg
   + counters) doesn't get crushed. */
.variant-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  min-height: 320px;
  max-height: 480px;
  overflow-y: auto;
  padding-right: 4px;
  align-content: stretch;
  grid-auto-rows: minmax(140px, 1fr);
}
@media (min-width: 640px) {
  .variant-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
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
