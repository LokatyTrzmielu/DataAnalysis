<template>
  <section class="card-apple mb-6">
    <h2 class="mb-4" style="font-size:12px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.12px;text-transform:uppercase">
      Time saved
    </h2>

    <div v-if="loading" style="font-size:14px;color:var(--app-text-sec)">Loading…</div>

    <div v-else-if="error" style="font-size:14px;color:#ff3b30">
      Couldn't load time savings.
    </div>

    <template v-else-if="summary">
      <!-- Headline number -->
      <div class="flex items-baseline gap-3 mb-1">
        <span style="font-size:36px;font-weight:600;color:var(--app-text);letter-spacing:-0.72px;line-height:1">
          ⏱ {{ formatDuration(summary.total_seconds) }}
        </span>
      </div>
      <p class="mb-4" style="font-size:14px;color:var(--app-text-sec);letter-spacing:-0.224px">
        across {{ summary.total_events }} {{ summary.total_events === 1 ? 'operation' : 'operations' }}
      </p>

      <!-- Empty state -->
      <p v-if="summary.total_events === 0" style="font-size:13px;color:var(--app-text-sec);letter-spacing:-0.21px">
        Run your first analysis to start saving time.
      </p>

      <!-- Breakdown -->
      <div v-else>
        <div style="height:1px;background:var(--app-border);margin:8px 0 16px 0"></div>
        <div class="mb-3" style="display:flex;align-items:center;gap:6px">
          <p style="font-size:11px;font-weight:600;color:var(--app-text-sec);letter-spacing:0.11px;text-transform:uppercase;margin:0">
            By type
          </p>
          <button
            type="button"
            @click="showInfo = !showInfo"
            :aria-expanded="showInfo"
            aria-label="How is this calculated?"
            title="How is this calculated?"
            style="display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;border:1px solid var(--app-border);border-radius:50%;background:transparent;color:var(--app-text-sec);font-size:10px;font-weight:600;cursor:pointer;padding:0;line-height:1"
          >
            ?
          </button>
        </div>

        <!-- Explainer popover -->
        <div
          v-if="showInfo"
          class="mb-4"
          style="border:1px solid var(--app-border);border-radius:10px;padding:12px 14px;font-size:12px;line-height:1.55;color:var(--app-text);background:rgba(127,127,127,0.05)"
        >
          <p style="font-weight:600;margin:0 0 6px 0;font-size:12px">How time is estimated</p>
          <p style="color:var(--app-text-sec);margin:0 0 10px 0">
            Each operation records the manual time the same work would take in Excel / SQL —
            opening files, mapping columns, VLOOKUP / pivot tables, waiting for macros and queries to finish.
            The number is an estimate, not a stopwatch.
          </p>
          <ul style="list-style:none;padding:0;margin:0;display:grid;gap:4px">
            <li><strong>Masterdata import</strong> — 15 min base + 5 min per 1 000 rows</li>
            <li><strong>Orders import</strong> — 20 min base + 4 min per 1 000 rows</li>
            <li><strong>Quality (DQ) analysis</strong> — 30 min base + 3 min per 1 000 rows</li>
            <li><strong>Capacity analysis</strong> — 45 min base + 10 min per 1 000 SKU + 5 min per carrier</li>
            <li>
              <strong>Performance + SKU Pareto</strong> — 40 min base + 1 min per 1 000 lines + 25 min for ABC Pareto
              <span style="color:var(--app-text-sec)">(capped at 6 h per run, because manual SQL aggregations scale sub-linearly)</span>
            </li>
            <li><strong>Report ZIP</strong> — 25 min base + 2 min per CSV file</li>
            <li><strong>Report PDF</strong> — 45 min base + 5 min per chart</li>
          </ul>
          <p style="color:var(--app-text-sec);margin:10px 0 0 0;font-size:11px">
            Total = sum of every event recorded for your account. Counter is strictly per-user — you only see your own work.
          </p>
        </div>

        <div class="space-y-2">
          <div v-for="row in summary.breakdown" :key="row.event_type"
               style="display:grid;grid-template-columns:1fr auto auto;gap:12px;align-items:baseline">
            <span style="font-size:14px;color:var(--app-text);letter-spacing:-0.224px">{{ row.label }}</span>
            <span style="font-size:13px;color:var(--app-text-sec);letter-spacing:-0.21px">{{ row.count }}×</span>
            <span style="font-size:14px;font-weight:600;color:var(--app-text);letter-spacing:-0.224px;text-align:right;min-width:64px">
              {{ formatDuration(row.seconds) }}
            </span>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { timeSavingsApi, formatDuration, type TimeSavingSummary } from '@/api/timeSavings'

const summary = ref<TimeSavingSummary | null>(null)
const loading = ref(true)
const error = ref(false)
const showInfo = ref(false)

onMounted(async () => {
  try {
    const resp = await timeSavingsApi.getSummary()
    summary.value = resp.data
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})
</script>
