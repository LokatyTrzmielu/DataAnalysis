<template>
  <div class="help-page">
    <h1 class="help-title">Help & Documentation</h1>
    <p class="help-subtitle">How Datavisor calculates and presents your results.</p>

    <div class="help-layout">
      <!-- Sticky sidebar -->
      <nav class="help-sidebar">
        <ul class="help-nav-list">
          <li v-for="s in sections" :key="s.id">
            <button
              class="help-nav-btn"
              :class="{ active: activeSection === s.id }"
              @click="scrollTo(s.id)"
            >
              <span class="help-nav-icon">{{ s.icon }}</span>
              {{ s.label }}
            </button>
          </li>
        </ul>
      </nav>

      <!-- Scrollable main content -->
      <main class="help-main" ref="mainRef">

        <!-- OVERVIEW -->
        <section id="overview" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">🗺</span>
            <h2 class="help-section-title">Overview</h2>
          </div>
          <p class="help-text">
            Datavisor is a warehouse analytics tool that helps you understand your order data,
            evaluate SKU-to-carrier fit, and produce reports for solution design. The typical
            workflow runs left to right through the analysis tabs:
          </p>
          <div class="help-flow">
            <div class="help-flow-step" v-for="(step, i) in flowSteps" :key="i">
              <span class="help-flow-num">{{ i + 1 }}</span>
              <div>
                <strong>{{ step.name }}</strong>
                <p>{{ step.desc }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- DASHBOARD -->
        <section id="dashboard" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">📊</span>
            <h2 class="help-section-title">Dashboard</h2>
          </div>
          <p class="help-text">
            The Dashboard is a landing page that gives you a quick view of your recent analyses.
            It does not perform its own calculations — it aggregates status information from other
            tabs and shows quick-action shortcuts.
          </p>
          <div class="help-card">
            <h3 class="help-card-title">What you see</h3>
            <ul class="help-list">
              <li><strong>Recent analyses</strong> — list of your last runs with name, date and status badge.</li>
              <li><strong>Quick actions</strong> — create a new analysis or resume the most recent one.</li>
              <li><strong>Status badges</strong> — reflect whether Import, Quality, Performance, and Capacity have been completed in a given run.</li>
            </ul>
          </div>
        </section>

        <!-- IMPORT -->
        <section id="import" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">📥</span>
            <h2 class="help-section-title">Import</h2>
          </div>
          <p class="help-text">
            Import loads two data files into the analysis: <strong>Masterdata</strong> (SKU dimensions)
            and <strong>Orders</strong> (transaction history). Both must be mapped to the correct
            columns before processing can begin.
          </p>

          <div class="help-card">
            <h3 class="help-card-title">Masterdata — required columns</h3>
            <div class="help-cols-table">
              <div class="help-col-row" v-for="col in masterdataColumns" :key="col.name">
                <code class="help-code-inline">{{ col.name }}</code>
                <span :class="col.required ? 'help-badge-req' : 'help-badge-opt'">{{ col.required ? 'required' : 'optional' }}</span>
                <span class="help-col-desc">{{ col.desc }}</span>
              </div>
            </div>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Orders — required columns</h3>
            <div class="help-cols-table">
              <div class="help-col-row" v-for="col in ordersColumns" :key="col.name">
                <code class="help-code-inline">{{ col.name }}</code>
                <span :class="col.required ? 'help-badge-req' : 'help-badge-opt'">{{ col.required ? 'required' : 'optional' }}</span>
                <span class="help-col-desc">{{ col.desc }}</span>
              </div>
            </div>
          </div>

          <div class="help-tip">
            <span class="help-tip-icon">💡</span>
            Column headers are matched automatically using fuzzy name matching. You can override any
            mapping manually before ingesting.
          </div>
        </section>

        <!-- QUALITY -->
        <section id="quality" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">🔍</span>
            <h2 class="help-section-title">Quality</h2>
          </div>
          <p class="help-text">
            The Quality tab validates both masterdata and orders before analysis, so that results are
            based on clean, trustworthy data. Each issue type is reported separately so you can
            prioritise fixes.
          </p>

          <div class="help-card">
            <h3 class="help-card-title">Masterdata quality metrics</h3>
            <div class="help-formula-block">
              <span class="help-formula-label">Quality Score (0–100 %)</span>
              <span class="help-formula">= weighted average of coverage and completeness indicators</span>
            </div>
            <div class="help-formula-block">
              <span class="help-formula-label">Dimension Coverage %</span>
              <span class="help-formula">= SKUs with L, W, H &gt; 0 / total SKUs × 100</span>
            </div>
            <div class="help-formula-block">
              <span class="help-formula-label">Weight Coverage %</span>
              <span class="help-formula">= SKUs with weight_kg &gt; 0 / total SKUs × 100</span>
            </div>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Issue types</h3>
            <ul class="help-list">
              <li><strong>Missing Critical</strong> — SKUs missing one or more required fields (sku, dimensions, weight).</li>
              <li><strong>Suspect Outliers</strong> — values more than 3 standard deviations from the mean; likely data entry errors.</li>
              <li><strong>Duplicates</strong> — same SKU ID appearing more than once in the file.</li>
              <li><strong>Conflicts</strong> — same SKU ID appearing with different dimension or weight values.</li>
              <li><strong>Imputed Dimensions / Weight</strong> — missing values estimated from product family averages.</li>
            </ul>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Orders validation metrics</h3>
            <div class="help-formula-block">
              <span class="help-formula-label">Calendar Coverage %</span>
              <span class="help-formula">= unique order days / total calendar days in range × 100</span>
            </div>
            <ul class="help-list" style="margin-top:12px">
              <li><strong>Date Gaps</strong> — calendar periods with no orders; may indicate warehouse closures or missing data.</li>
              <li><strong>Unknown SKUs</strong> — order lines referencing SKUs not in masterdata (cannot be analysed).</li>
              <li><strong>Qty Outliers</strong> — order quantities above mean + 3σ; likely bulk or test orders.</li>
            </ul>
          </div>
        </section>

        <!-- PERFORMANCE -->
        <section id="performance" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">⚡</span>
            <h2 class="help-section-title">Performance</h2>
          </div>
          <p class="help-text">
            The Performance tab analyses your order throughput and SKU demand patterns. Results are
            used to size the warehouse and plan shift schedules.
          </p>

          <div class="help-card">
            <h3 class="help-card-title">KPI metrics</h3>
            <div class="help-formula-block">
              <span class="help-formula-label">Avg Lines / Order</span>
              <span class="help-formula">= total order lines / total distinct orders</span>
            </div>
            <div class="help-formula-block">
              <span class="help-formula-label">Avg Pieces / Order</span>
              <span class="help-formula">= total quantity units / total distinct orders</span>
            </div>
            <div class="help-formula-block">
              <span class="help-formula-label">P90 / P95 Lines per Hour</span>
              <span class="help-formula">= sorted hourly volumes [ ceil(n × 0.90 / 0.95) ]</span>
            </div>
            <p class="help-text" style="margin-top:10px">
              P90 is the throughput level exceeded only 10 % of the time — a conservative capacity
              baseline. P95 provides a higher buffer for peak planning.
            </p>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Throughput aggregations</h3>
            <p class="help-text">
              Orders, Lines, and Pieces are summarised per Day, Shift, and Hour (if timestamp data
              is available). Each period shows: average, median, and maximum.
            </p>
            <div class="help-formula-block">
              <span class="help-formula-label">Shift metrics</span>
              <span class="help-formula">= daily totals ÷ number of configured shifts per day</span>
            </div>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">ABC Classification (Pareto)</h3>
            <p class="help-text">
              SKUs are ranked by total order lines (descending) and grouped by their share of
              cumulative demand:
            </p>
            <div class="help-abc-table">
              <div class="help-abc-row">
                <span class="help-abc-badge abc-a">A</span>
                <span>SKUs making up the <strong>top 80 %</strong> of all lines — highest velocity, most important.</span>
              </div>
              <div class="help-abc-row">
                <span class="help-abc-badge abc-b">B</span>
                <span>SKUs in the <strong>80–95 %</strong> cumulative range — medium velocity.</span>
              </div>
              <div class="help-abc-row">
                <span class="help-abc-badge abc-c">C</span>
                <span>SKUs in the <strong>95–100 %</strong> cumulative range — slow movers, long tail.</span>
              </div>
            </div>
            <div class="help-formula-block" style="margin-top:12px">
              <span class="help-formula-label">Cumulative % for SKU i</span>
              <span class="help-formula">= sum(lines₁ … linesᵢ) / total_lines × 100</span>
            </div>
          </div>
        </section>

        <!-- CAPACITY -->
        <section id="capacity" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">📦</span>
            <h2 class="help-section-title">Capacity</h2>
          </div>
          <p class="help-text">
            The Capacity tab checks whether each SKU fits inside your configured carriers
            (bins, boxes, trays). It tests all valid physical orientations and reports fit status,
            location requirements, and space utilisation.
          </p>

          <div class="help-card">
            <h3 class="help-card-title">Fit test — 6 orientations</h3>
            <p class="help-text">
              For each SKU, the system tests all 6 ways the box can be placed inside the carrier
              (every permutation of L × W × H). For each orientation it calculates three margins:
            </p>
            <div class="help-formula-block">
              <span class="help-formula-label">margin_x</span>
              <span class="help-formula">= carrier inner length − sku dimension on x-axis</span>
            </div>
            <div class="help-formula-block">
              <span class="help-formula-label">margin_y</span>
              <span class="help-formula">= carrier inner width  − sku dimension on y-axis</span>
            </div>
            <div class="help-formula-block">
              <span class="help-formula-label">margin_z</span>
              <span class="help-formula">= carrier inner height − sku dimension on z-axis</span>
            </div>
            <div class="help-status-table">
              <div class="help-status-row">
                <span class="help-status-badge status-fit">FIT</span>
                <span>All margins ≥ 0 and min(margin) &gt; borderline threshold (default 5 mm) and weight ≤ max.</span>
              </div>
              <div class="help-status-row">
                <span class="help-status-badge status-borderline">BORDERLINE</span>
                <span>All margins ≥ 0 but min(margin) ≤ borderline threshold — SKU fits but with very little clearance.</span>
              </div>
              <div class="help-status-row">
                <span class="help-status-badge status-notfit">NOT FIT</span>
                <span>Any margin &lt; 0 in all orientations, or SKU weight exceeds carrier maximum.</span>
              </div>
            </div>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Location & utilisation metrics</h3>
            <div class="help-formula-block">
              <span class="help-formula-label">Units per Carrier</span>
              <span class="help-formula">= min( floor(L/x) × floor(W/y) × floor(H/z),  floor(max_weight / sku_weight) )</span>
            </div>
            <div class="help-formula-block">
              <span class="help-formula-label">Locations Required</span>
              <span class="help-formula">= ceil( stock_qty / units_per_carrier )</span>
            </div>
            <div class="help-formula-block">
              <span class="help-formula-label">Filling Rate %</span>
              <span class="help-formula">= ( stock_qty × sku_volume ) / ( locations × carrier_volume ) × 100</span>
            </div>
            <p class="help-text" style="margin-top:10px">
              A high Filling Rate means the carrier space is used efficiently. A low rate means
              the SKU is much smaller than the carrier — consider a different carrier size.
            </p>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Analysis modes</h3>
            <ul class="help-list">
              <li>
                <strong>Independent</strong> — each SKU is tested against all carriers independently.
                A SKU can appear in multiple rows (one per carrier). Useful for comparing how a
                SKU fits across your carrier portfolio.
              </li>
              <li>
                <strong>Prioritized</strong> — carriers are assigned a priority rank (1, 2, 3…).
                Each SKU is assigned only to the first carrier it fits. Useful for routing rules.
              </li>
              <li>
                <strong>Best Fit</strong> — each SKU is assigned to the carrier with the highest
                Filling Rate. Minimises wasted space. Each SKU appears once in the results.
              </li>
            </ul>
          </div>
        </section>

        <!-- REPORTS -->
        <section id="reports" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">📄</span>
            <h2 class="help-section-title">Reports</h2>
          </div>
          <p class="help-text">
            The Reports tab exports analysis results in various formats for sharing, archiving,
            or importing into other tools.
          </p>

          <div class="help-card">
            <h3 class="help-card-title">Full reports</h3>
            <ul class="help-list">
              <li><strong>PDF</strong> — comprehensive formatted report covering Quality, Performance, and Capacity. Requires Capacity analysis to be completed.</li>
              <li><strong>ZIP</strong> — archive combining the PDF with all CSV exports in a single download.</li>
            </ul>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Data Quality CSVs</h3>
            <ul class="help-list">
              <li><strong>DQ_Summary</strong> — one-line-per-SKU summary of all quality flags.</li>
              <li><strong>DQ_MissingCritical</strong> — SKUs with required fields missing.</li>
              <li><strong>DQ_SuspectOutliers</strong> — dimension or weight values more than 3σ from the mean.</li>
              <li><strong>DQ_HighRiskBorderline</strong> — SKUs with very tight fit margins across all carriers.</li>
              <li><strong>DQ_Duplicates / DQ_Conflicts</strong> — duplicate and conflicting SKU records.</li>
            </ul>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Analysis CSVs</h3>
            <ul class="help-list">
              <li><strong>Capacity_Results</strong> — full SKU × carrier fit matrix with margins, fill rates, and location counts.</li>
              <li><strong>SKU_Pareto</strong> — ABC classification from the Performance tab, including cumulative line percentages.</li>
              <li><strong>SolDimTool_DashboardInput</strong> — pre-formatted input for SolDimTool v2.7.3 solution design software.</li>
            </ul>
          </div>
        </section>

      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const mainRef = ref<HTMLElement | null>(null)
const activeSection = ref('overview')

const sections = [
  { id: 'overview',    label: 'Overview',     icon: '🗺' },
  { id: 'dashboard',   label: 'Dashboard',    icon: '📊' },
  { id: 'import',      label: 'Import',       icon: '📥' },
  { id: 'quality',     label: 'Quality',      icon: '🔍' },
  { id: 'performance', label: 'Performance',  icon: '⚡' },
  { id: 'capacity',    label: 'Capacity',     icon: '📦' },
  { id: 'reports',     label: 'Reports',      icon: '📄' },
]

const flowSteps = [
  { name: 'Import',       desc: 'Load masterdata (SKU dimensions) and orders file, map columns.' },
  { name: 'Quality',      desc: 'Validate data completeness and flag issues before analysis.' },
  { name: 'Performance',  desc: 'Analyse throughput, peak hours, and ABC demand classification.' },
  { name: 'Capacity',     desc: 'Test SKU-to-carrier fit, calculate fill rates and location needs.' },
  { name: 'Reports',      desc: 'Export results to PDF, ZIP, or individual CSV files.' },
]

const masterdataColumns = [
  { name: 'sku',        required: true,  desc: 'Unique product code.' },
  { name: 'length_mm',  required: true,  desc: 'Outer length in millimetres.' },
  { name: 'width_mm',   required: true,  desc: 'Outer width in millimetres.' },
  { name: 'height_mm',  required: true,  desc: 'Outer height in millimetres.' },
  { name: 'weight_kg',  required: true,  desc: 'Gross weight in kilograms.' },
  { name: 'stock_qty',  required: true,  desc: 'Current stock quantity — used for location and fill-rate calculations.' },
]

const ordersColumns = [
  { name: 'order_id',   required: true,  desc: 'Unique identifier for the order.' },
  { name: 'sku',        required: true,  desc: 'Product code ordered; matched against masterdata.' },
  { name: 'quantity',   required: true,  desc: 'Number of units on this order line.' },
  { name: 'order_date', required: true,  desc: 'Date of order (YYYY-MM-DD). Needed for daily/trend charts.' },
  { name: 'timestamp',  required: false, desc: 'Full datetime (ISO 8601). Enables hourly throughput analysis.' },
]

function scrollTo(id: string) {
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

let observer: IntersectionObserver | null = null

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          activeSection.value = entry.target.id
        }
      }
    },
    { rootMargin: '-20% 0px -70% 0px', threshold: 0 }
  )
  sections.forEach(({ id }) => {
    const el = document.getElementById(id)
    if (el) observer!.observe(el)
  })
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>

<style scoped>
.help-page {
  max-width: 880px;
}

.help-title {
  font-family: "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 28px;
  font-weight: 600;
  color: var(--app-text);
  line-height: 1.14;
  letter-spacing: -0.28px;
  margin-bottom: 6px;
}

.help-subtitle {
  font-size: 15px;
  color: var(--app-text-sec);
  letter-spacing: -0.15px;
  margin-bottom: 28px;
}

/* Two-column layout */
.help-layout {
  display: grid;
  grid-template-columns: 168px 1fr;
  gap: 32px;
  align-items: start;
}

/* Sticky sidebar */
.help-sidebar {
  position: sticky;
  top: 68px;
}

.help-nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.help-nav-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: 8px;
  border: none;
  background: none;
  cursor: pointer;
  font-family: "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 13px;
  font-weight: 400;
  color: var(--app-text-sec);
  letter-spacing: -0.13px;
  text-align: left;
  transition: background 0.15s, color 0.15s;
}

.help-nav-btn:hover {
  background: var(--app-border);
  color: var(--app-text);
}

.help-nav-btn.active {
  background: var(--app-border);
  color: var(--app-text);
  font-weight: 500;
}

.help-nav-icon {
  font-size: 14px;
  line-height: 1;
  flex-shrink: 0;
}

/* Main content */
.help-main {
  min-width: 0;
}

.help-section {
  margin-bottom: 48px;
  scroll-margin-top: 72px;
}

.help-section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--app-border);
}

.help-section-icon {
  font-size: 20px;
  line-height: 1;
}

.help-section-title {
  font-family: "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--app-text);
  letter-spacing: -0.22px;
  margin: 0;
}

.help-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--app-text);
  letter-spacing: -0.15px;
  margin-bottom: 14px;
}

/* Cards */
.help-card {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 16px 18px;
  margin-bottom: 12px;
}

.help-card-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--app-text-sec);
  letter-spacing: 0.12px;
  text-transform: uppercase;
  margin: 0 0 12px;
}

/* Formula blocks */
.help-formula-block {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 8px 16px;
  align-items: baseline;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--app-bg);
  border-left: 3px solid var(--color-apple-blue, #0071e3);
  margin-bottom: 8px;
  font-size: 13px;
}

.help-formula-label {
  font-weight: 600;
  color: var(--app-text);
  letter-spacing: -0.13px;
}

.help-formula {
  font-family: "SF Mono", "Menlo", "Monaco", "Courier New", monospace;
  font-size: 12px;
  color: var(--app-text-sec);
  letter-spacing: 0;
}

/* Code inline */
.help-code-inline {
  font-family: "SF Mono", "Menlo", "Monaco", "Courier New", monospace;
  font-size: 12px;
  background: var(--app-bg);
  border: 1px solid var(--app-border);
  border-radius: 4px;
  padding: 1px 6px;
  color: var(--app-text);
  white-space: nowrap;
}

/* Lists */
.help-list {
  padding-left: 20px;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.help-list li {
  font-size: 14px;
  line-height: 1.55;
  color: var(--app-text);
  letter-spacing: -0.14px;
}

/* Column mapping table */
.help-cols-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.help-col-row {
  display: grid;
  grid-template-columns: 160px 72px 1fr;
  gap: 8px;
  align-items: center;
  font-size: 13px;
}

.help-col-desc {
  color: var(--app-text-sec);
  letter-spacing: -0.13px;
}

.help-badge-req {
  font-size: 11px;
  font-weight: 500;
  color: #ffffff;
  background: #0071e3;
  border-radius: 4px;
  padding: 1px 6px;
  text-align: center;
  letter-spacing: 0;
}

.help-badge-opt {
  font-size: 11px;
  font-weight: 500;
  color: var(--app-text-sec);
  background: var(--app-bg);
  border: 1px solid var(--app-border);
  border-radius: 4px;
  padding: 1px 6px;
  text-align: center;
  letter-spacing: 0;
}

/* Tip box */
.help-tip {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  background: rgba(0, 113, 227, 0.06);
  border: 1px solid rgba(0, 113, 227, 0.18);
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 13px;
  color: var(--app-text);
  letter-spacing: -0.13px;
  line-height: 1.5;
  margin-top: 4px;
}

.help-tip-icon {
  font-size: 15px;
  flex-shrink: 0;
  margin-top: 1px;
}

/* ABC table */
.help-abc-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.help-abc-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--app-text);
  letter-spacing: -0.14px;
}

.help-abc-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  letter-spacing: 0;
}

.abc-a { background: rgba(52, 199, 89, 0.15); color: #1e8c40; }
.abc-b { background: rgba(0, 113, 227, 0.12); color: #0055b3; }
.abc-c { background: rgba(0, 0, 0, 0.08);      color: var(--app-text-sec); }

html.dark .abc-a { background: rgba(52, 199, 89, 0.18); color: #34c759; }
html.dark .abc-b { background: rgba(0, 113, 227, 0.18); color: #2997ff; }
html.dark .abc-c { background: rgba(255,255,255,0.10);  color: var(--app-text-sec); }

/* Status table */
.help-status-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 14px;
}

.help-status-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 14px;
  color: var(--app-text);
  letter-spacing: -0.14px;
  line-height: 1.5;
}

.help-status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 88px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
  letter-spacing: 0.05px;
  margin-top: 2px;
}

.status-fit        { background: rgba(52, 199, 89, 0.12); color: #1e8c40; }
.status-borderline { background: rgba(255, 159, 10, 0.12); color: #b06800; }
.status-notfit     { background: rgba(255, 59, 48, 0.10); color: #c0392b; }

html.dark .status-fit        { background: rgba(52, 199, 89, 0.18); color: #34c759; }
html.dark .status-borderline { background: rgba(255, 159, 10, 0.18); color: #ff9f0a; }
html.dark .status-notfit     { background: rgba(255, 59, 48, 0.15); color: #ff453a; }

/* Flow steps */
.help-flow {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-top: 4px;
}

.help-flow-step {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid var(--app-border);
  font-size: 14px;
  color: var(--app-text);
}

.help-flow-step:last-child {
  border-bottom: none;
}

.help-flow-step p {
  margin: 2px 0 0;
  color: var(--app-text-sec);
  font-size: 13px;
  letter-spacing: -0.13px;
}

.help-flow-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-apple-blue, #0071e3);
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
  margin-top: 1px;
}
</style>
