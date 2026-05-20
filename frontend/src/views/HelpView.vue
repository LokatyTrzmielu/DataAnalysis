<template>
  <div class="help-page">
    <h1 class="help-title">Help &amp; Documentation</h1>
    <p class="help-subtitle">How Datavisor calculates and presents your results — with worked examples.</p>

    <div class="help-layout">
      <!-- Sticky sidebar with collapsible groups -->
      <nav class="help-sidebar">
        <ul class="help-nav-list">
          <li v-for="node in navTree" :key="node.id">
            <!-- Pure group (no anchor, just expand/collapse) -->
            <template v-if="node.isGroup">
              <button class="help-nav-group" @click="toggleGroup(node.id)">
                <span class="help-nav-chevron">{{ expanded.has(node.id) ? '▾' : '▸' }}</span>
                <span class="help-nav-icon">{{ node.icon }}</span>
                {{ node.label }}
              </button>
              <ul v-show="expanded.has(node.id)" class="help-nav-sublist">
                <li v-for="child in node.children" :key="child.id">
                  <button
                    class="help-nav-btn level-1"
                    :class="{ active: activeSection === child.id }"
                    @click="scrollTo(child.id)"
                  >
                    <span class="help-nav-icon">{{ child.icon }}</span>
                    {{ child.label }}
                  </button>
                  <ul v-if="child.children" class="help-nav-sublist-2">
                    <li v-for="grand in child.children" :key="grand.id">
                      <button
                        class="help-nav-btn level-2"
                        :class="{ active: activeSection === grand.id }"
                        @click="scrollTo(grand.id)"
                      >
                        ↳ {{ grand.label }}
                      </button>
                    </li>
                  </ul>
                </li>
              </ul>
            </template>

            <!-- Leaf at root level (e.g. Overview, Sharing, Dashboard) -->
            <template v-else>
              <button
                class="help-nav-btn"
                :class="{ active: activeSection === node.id }"
                @click="scrollTo(node.id)"
              >
                <span class="help-nav-icon">{{ node.icon }}</span>
                {{ node.label }}
              </button>
            </template>
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
            workflow starts with reusable setup (Datasets, Carriers) and then runs left to right
            through the analysis tabs:
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

        <!-- IMPORT -->
        <section id="import" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">📥</span>
            <h2 class="help-section-title">Import</h2>
          </div>
          <p class="help-text">
            Import loads two data sources into the analysis: <strong>Masterdata</strong> (SKU dimensions)
            and <strong>Orders</strong> (transaction history). Both must be mapped to the correct
            columns before processing can begin. You can either upload fresh files or attach a saved
            <a href="#datasets" @click.prevent="scrollTo('datasets')">Dataset</a>.
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

          <div class="help-example-card">
            <span class="help-example-label">Example — fuzzy column matching</span>
            <pre class="help-example-body">File header:   SKU_NUM   |  Length [mm] |  Net_Weight_kg
Auto mapping:  → sku      |  → length_mm |  → weight_kg
Confidence:      0.92          0.88           0.95

You can override any mapping manually before ingesting.</pre>
          </div>

          <div class="help-tip">
            <span class="help-tip-icon">💡</span>
            Column headers are matched automatically using fuzzy name matching. Saved Datasets
            remember their mapping, so re-importing a similar export has 100 % auto-mapping accuracy.
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

            <div class="help-example-card">
              <span class="help-example-label">Example — coverage</span>
              <pre class="help-example-body">Total SKUs in masterdata:        5 000
SKUs with L, W, H &gt; 0:            4 280
SKUs with weight_kg &gt; 0:          4 690

Dimension Coverage = 4 280 / 5 000 × 100 = 85.6 %
Weight Coverage    = 4 690 / 5 000 × 100 = 93.8 %</pre>
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

            <div class="help-example-card">
              <span class="help-example-label">Example — outlier detection (length_mm)</span>
              <div class="help-steps-table">
                <div class="help-steps-row help-steps-head">
                  <span>Step</span><span>Operation</span><span>Value</span>
                </div>
                <div class="help-steps-row"><span>1</span><span>mean of length_mm across 5 000 SKUs</span><span>480 mm</span></div>
                <div class="help-steps-row"><span>2</span><span>standard deviation σ</span><span>120 mm</span></div>
                <div class="help-steps-row"><span>3</span><span>upper threshold = mean + 3σ</span><span>840 mm</span></div>
                <div class="help-steps-row"><span>4</span><span>SKU <code>BOLT-L-1200</code> length_mm</span><span>1 200 mm</span></div>
                <div class="help-steps-row help-steps-result"><span>→</span><span>1 200 &gt; 840 → flagged as Suspect Outlier</span><span>—</span></div>
              </div>
            </div>

            <div class="help-example-card">
              <span class="help-example-label">Example — imputation</span>
              <pre class="help-example-body">SKU "BOLT-M8-019" has no length_mm.
Family prefix "BOLT-M8-" has 42 SKUs with valid lengths.
Average length of family: 24 mm → imputed as 24 mm.

The Imputed Dimensions report lists every such SKU so you can
confirm or replace the estimate with measured data.</pre>
            </div>
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

            <div class="help-example-card">
              <span class="help-example-label">Example — calendar coverage</span>
              <pre class="help-example-body">Order range:   2026-01-01 → 2026-03-31 (90 days)
Unique days with at least one order:    74
Calendar Coverage = 74 / 90 × 100 = 82.2 %

The 16 missing days are listed under "Date Gaps" — verify whether
they reflect closures (OK) or missing extract data (action needed).</pre>
            </div>
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

          <div id="performance-kpi" class="help-card help-anchor">
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

            <div class="help-example-card">
              <span class="help-example-label">Example — lines and pieces per order</span>
              <pre class="help-example-body">Dataset:        50 000 order lines / 12 000 distinct orders
Total pieces:   136 800 units

Avg Lines  / Order = 50 000 / 12 000  = 4.17 lines
Avg Pieces / Order = 136 800 / 12 000 = 11.40 units</pre>
            </div>

            <div class="help-example-card">
              <span class="help-example-label">Example — P90 of hourly lines</span>
              <pre class="help-example-body">240 working hours collected.
Hourly line counts sorted ascending.

Index P90 = ceil(240 × 0.90) = 216
Value at position 216 = 142 lines/h

→ 90 % of hours run at ≤ 142 lines/h.
→ Size pickers / packers for sustained 142 lines/h.</pre>
            </div>
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

          <div id="performance-abc" class="help-card help-anchor">
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

            <div class="help-example-card">
              <span class="help-example-label">Example — classification cuts (first rows of a sorted list)</span>
              <div class="help-steps-table abc-grid">
                <div class="help-steps-row help-steps-head">
                  <span>Rank</span><span>SKU</span><span>Lines</span><span>Cumul. %</span><span>Class</span>
                </div>
                <div class="help-steps-row"><span>1</span><span>SKU-A17</span><span>1 240</span><span>6.7 %</span><span><b class="abc-tag abc-a">A</b></span></div>
                <div class="help-steps-row"><span>…</span><span>…</span><span>…</span><span>…</span><span><b class="abc-tag abc-a">A</b></span></div>
                <div class="help-steps-row"><span>142</span><span>SKU-X09</span><span>74</span><span>80.1 %</span><span><b class="abc-tag abc-a">A</b></span></div>
                <div class="help-steps-row"><span>143</span><span>SKU-J51</span><span>72</span><span>80.5 %</span><span><b class="abc-tag abc-b">B</b></span></div>
                <div class="help-steps-row"><span>…</span><span>…</span><span>…</span><span>…</span><span><b class="abc-tag abc-b">B</b></span></div>
                <div class="help-steps-row"><span>418</span><span>SKU-R02</span><span>14</span><span>95.0 %</span><span><b class="abc-tag abc-b">B</b></span></div>
                <div class="help-steps-row"><span>419</span><span>SKU-V77</span><span>13</span><span>95.1 %</span><span><b class="abc-tag abc-c">C</b></span></div>
                <div class="help-steps-row help-steps-result"><span>→</span><span>Cut A→B</span><span>at rank 142</span><span>(80 %)</span><span>—</span></div>
                <div class="help-steps-row help-steps-result"><span>→</span><span>Cut B→C</span><span>at rank 418</span><span>(95 %)</span><span>—</span></div>
              </div>
            </div>
          </div>

          <div id="performance-pareto" class="help-card help-anchor">
            <h3 class="help-card-title">Pareto Concentration table</h3>
            <p class="help-text">
              This table answers a key question: <em>how much of the daily workload is generated
              by the top N SKUs?</em> SKUs are sorted by total order lines (same order as ABC),
              then grouped into incremental bands — top 10, next 10, next 10, etc. Each row shows
              the <strong>incremental</strong> contribution of that band, not the cumulative total.
            </p>
            <div style="display:flex;flex-direction:column;gap:8px;margin-top:10px">
              <div v-for="col in paretoBandColumns" :key="col.name">
                <code class="help-code-inline">{{ col.name }}</code>
                <p class="help-col-desc" style="margin-top:3px" v-html="col.desc"></p>
              </div>
            </div>
            <div class="help-tip" style="margin-top:12px;flex-direction:column;gap:4px">
              <strong><span class="help-tip-icon">💡</span> How to read a row:</strong>
              <span>If the row <em>MovedSKU = 10</em> shows Lines% = 31 % and Cumul.Lines% = 31 %, it means the top 10 SKUs alone generate 31 % of all daily order lines. The next row (MovedSKU = 20) shows the <em>additional</em> contribution of SKUs #11–20. The <strong>Total</strong> row sums every band and always equals 100 %.</span>
            </div>
            <div class="help-tip" style="margin-top:8px;flex-direction:column;gap:4px">
              <strong><span class="help-tip-icon">📐</span> Practical use:</strong>
              <span>A steep drop between the first few bands (e.g. top 10 SKUs = 30 %, next 10 = 8 %) signals a highly concentrated assortment — a small golden-zone picking area will handle the bulk of volume. A flat distribution suggests a broad assortment with no clear fast movers.</span>
            </div>

            <div class="help-example-card">
              <span class="help-example-label">Example — first three bands</span>
              <div class="help-steps-table pareto-grid">
                <div class="help-steps-row help-steps-head">
                  <span>MovedSKU</span><span>Lines/Day</span><span>Lines%</span><span>Cumul.Lines%</span>
                </div>
                <div class="help-steps-row"><span>10</span><span>620</span><span>31 %</span><span>31 %</span></div>
                <div class="help-steps-row"><span>20</span><span>240</span><span>12 %</span><span>43 %</span></div>
                <div class="help-steps-row"><span>50</span><span>360</span><span>18 %</span><span>61 %</span></div>
                <div class="help-steps-row help-steps-result"><span>…</span><span>…</span><span>…</span><span>up to 100 %</span></div>
              </div>
              <p class="help-col-desc" style="margin-top:8px">
                Drop from 31 % → 12 % between band 1 and band 2 = highly concentrated head:
                the first 10 SKUs do nearly 3× the work of the next 10. A golden-zone of ~20
                fast-pick locations would already cover 43 % of daily lines.
              </p>
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
            location requirements, and space utilisation. Configure carrier inner dimensions and
            weight limits under <a href="#carriers" @click.prevent="scrollTo('carriers')">Carriers</a>.
          </p>

          <div id="capacity-fit" class="help-card help-anchor">
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

            <div class="help-example-card">
              <span class="help-example-label">Example — SKU 80 × 60 × 40 mm in carrier 100 × 70 × 50 mm (threshold 5 mm)</span>
              <div class="help-steps-table fit-grid">
                <div class="help-steps-row help-steps-head">
                  <span>Orientation (x · y · z)</span><span>margin_x</span><span>margin_y</span><span>margin_z</span><span>min</span><span>Status</span>
                </div>
                <div class="help-steps-row"><span>80 · 60 · 40</span><span>20</span><span>10</span><span>10</span><span>10</span><span><b class="abc-tag status-fit">FIT</b></span></div>
                <div class="help-steps-row"><span>80 · 40 · 60</span><span>20</span><span>30</span><span>-10</span><span>-10</span><span><b class="abc-tag status-notfit">NOT FIT</b></span></div>
                <div class="help-steps-row"><span>60 · 80 · 40</span><span>40</span><span>-10</span><span>10</span><span>-10</span><span><b class="abc-tag status-notfit">NOT FIT</b></span></div>
                <div class="help-steps-row"><span>60 · 40 · 80</span><span>40</span><span>30</span><span>-30</span><span>-30</span><span><b class="abc-tag status-notfit">NOT FIT</b></span></div>
                <div class="help-steps-row"><span>40 · 80 · 60</span><span>60</span><span>-10</span><span>-10</span><span>-10</span><span><b class="abc-tag status-notfit">NOT FIT</b></span></div>
                <div class="help-steps-row"><span>40 · 60 · 80</span><span>60</span><span>10</span><span>-30</span><span>-30</span><span><b class="abc-tag status-notfit">NOT FIT</b></span></div>
              </div>
              <p class="help-col-desc" style="margin-top:8px">
                At least one orientation FITs → SKU result = <b class="abc-tag status-fit">FIT</b>
                (best orientation 80 · 60 · 40, min margin = 10 mm).
                The same SKU re-tested in a carrier 82 × 62 × 41 mm would return
                <b class="abc-tag status-borderline">BORDERLINE</b> (best min = 1 mm, ≤ 5 mm threshold).
              </p>
            </div>
          </div>

          <div id="capacity-loc" class="help-card help-anchor">
            <h3 class="help-card-title">Location &amp; utilisation metrics</h3>
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

            <div class="help-example-card">
              <span class="help-example-label">Example — units per carrier &amp; filling rate</span>
              <pre class="help-example-body">Carrier inner:  400 × 300 × 250 mm,  max_weight = 25 kg
SKU:             80 × 60 × 40 mm,  weight = 0.12 kg,  stock_qty = 600

Geometry:        floor(400/80) × floor(300/60) × floor(250/40)
              =  5 × 5 × 6
              =  150 units

Weight cap:      floor(25 / 0.12) = 208 units
Units / Carrier = min(150, 208)  = 150 units

Locations       = ceil(600 / 150) = 4 locations

SKU volume      = 80 × 60 × 40    = 192 000 mm³
Carrier volume  = 400 × 300 × 250 = 30 000 000 mm³

Filling Rate    = (600 × 192 000) / (4 × 30 000 000) × 100
              =  115 200 000 / 120 000 000 × 100
              =  96.0 %</pre>
            </div>
          </div>

          <div id="capacity-modes" class="help-card help-anchor">
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

            <div class="help-example-card">
              <span class="help-example-label">Example — same SKU under three modes</span>
              <pre class="help-example-body">SKU "WIDGET-X" — fits in C1 (Fill = 38 %) and C2 (Fill = 81 %).
C1 has priority 1, C2 priority 2.

Independent  → 2 rows: WIDGET-X × C1, WIDGET-X × C2
Prioritized  → 1 row : WIDGET-X × C1  (first carrier matched)
Best Fit     → 1 row : WIDGET-X × C2  (higher Filling Rate)</pre>
            </div>
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
              <li><strong>Pareto_Bands</strong> — Pareto Concentration table: incremental Lines/Day and Pieces/Day per top-N SKU band. Same data as the table in the Performance tab.</li>
              <li><strong>SolDimTool_DashboardInput</strong> — pre-formatted input for SolDimTool v2.7.3 solution design software.</li>
            </ul>
          </div>
        </section>

        <!-- DATASETS -->
        <section id="datasets" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">🧾</span>
            <h2 class="help-section-title">Datasets</h2>
          </div>
          <p class="help-text">
            A <strong>Dataset</strong> is a reusable source file (XLSX / CSV) with its column mapping
            already saved. Once you ingest a file as a Dataset, you can attach it to as many runs
            as you like without re-uploading or re-mapping. Datasets live under
            <code class="help-code-inline">/datasets</code>.
          </p>

          <div class="help-card">
            <h3 class="help-card-title">Workflow</h3>
            <ol class="help-list" style="list-style:decimal">
              <li><strong>Upload</strong> — pick an XLSX or CSV file and choose its type: <em>Masterdata</em> or <em>Orders</em>.</li>
              <li><strong>Inspect</strong> — the system reads the headers and proposes column mappings using fuzzy name matching.</li>
              <li><strong>Map</strong> — review the proposed mapping; manually override any field. Required fields are highlighted.</li>
              <li><strong>Save</strong> — name the dataset; the file and its mapping are stored together.</li>
              <li><strong>Use</strong> — in the New Run modal, pick the saved dataset from the dropdown; no further mapping needed.</li>
            </ol>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">When to use Datasets vs Import</h3>
            <ul class="help-list">
              <li><strong>Use a Dataset</strong> when you'll run multiple analyses on the same data (e.g. exploring different carrier configurations against one Q1 extract).</li>
              <li><strong>Use Import directly</strong> for one-off runs or when the file is unique to that analysis.</li>
            </ul>
          </div>

          <div class="help-tip">
            <span class="help-tip-icon">💡</span>
            The same file uploaded twice produces a second Dataset (no automatic deduplication).
            Rename or delete obsolete datasets from the list to keep the dropdown tidy.
          </div>
        </section>

        <!-- CARRIERS -->
        <section id="carriers" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">🚚</span>
            <h2 class="help-section-title">Carriers</h2>
          </div>
          <p class="help-text">
            Carriers are the bins, boxes, trays, or totes the Capacity analysis tests against.
            Configure them once under <code class="help-code-inline">/carriers</code> and reuse
            them across runs. Every Capacity number — units per carrier, locations, filling rate —
            depends on these settings, so set them carefully.
          </p>

          <div class="help-card">
            <h3 class="help-card-title">Required fields</h3>
            <div class="help-cols-table">
              <div class="help-col-row" v-for="col in carrierColumns" :key="col.name">
                <code class="help-code-inline">{{ col.name }}</code>
                <span :class="col.required ? 'help-badge-req' : 'help-badge-opt'">{{ col.required ? 'required' : 'optional' }}</span>
                <span class="help-col-desc" v-html="col.desc"></span>
              </div>
            </div>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Inner vs outer dimensions</h3>
            <p class="help-text">
              Capacity always uses <strong>inner</strong> dimensions — the usable cavity. If you
              only know outer dimensions, subtract wall thickness (typically 6–10 mm per side for
              plastic totes, 15–20 mm for cardboard).
            </p>
          </div>

          <div class="help-example-card">
            <span class="help-example-label">Example — borderline threshold</span>
            <pre class="help-example-body">borderline_threshold = 5 mm

SKU A: best orientation, min(margin) = 8 mm  → FIT
SKU B: best orientation, min(margin) = 3 mm  → BORDERLINE  (≤ 5 mm)
SKU C: best orientation, min(margin) = -2 mm → NOT FIT     (any margin &lt; 0)

Borderline SKUs technically fit but may jam on conveyor or be unsafe
to grip — use the DQ_HighRiskBorderline report to review them.</pre>
          </div>
        </section>

        <!-- TOOLS › DATA PREPARATION -->
        <section id="tool-data-prep" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">🧩</span>
            <h2 class="help-section-title">Tools › Data Preparation</h2>
          </div>
          <p class="help-text">
            Data Preparation merges multiple Excel or CSV files into a single dataset ready for
            analysis. Useful when you receive monthly extracts, exports from multiple warehouses,
            or one masterdata file per supplier and need to combine them.
          </p>

          <div class="help-card">
            <h3 class="help-card-title">Workflow</h3>
            <ol class="help-list" style="list-style:decimal">
              <li><strong>Select type</strong> — Masterdata or Orders. Determines which required columns are expected.</li>
              <li><strong>Upload N files</strong> — drag/drop or pick several XLSX/CSV files at once.</li>
              <li><strong>Map columns per file</strong> — each file can have different column names for the same logical field (e.g. <code class="help-code-inline">SKU</code>, <code class="help-code-inline">Item_Code</code>, <code class="help-code-inline">ProductID</code>). Map each to the canonical name once.</li>
              <li><strong>Merge &amp; validate</strong> — files are concatenated, duplicates flagged, header conflicts surfaced.</li>
              <li><strong>Save as Dataset</strong> — output is stored as a regular Dataset, ready for any run.</li>
            </ol>
          </div>

          <div class="help-example-card">
            <span class="help-example-label">Example — three masterdata files merged</span>
            <pre class="help-example-body">File 1 (warehouse_PL.xlsx):     5 000 rows, SKU column = "SKU"
File 2 (warehouse_DE.xlsx):     5 000 rows, SKU column = "Item_Code"
File 3 (warehouse_FR.csv):      5 000 rows, SKU column = "ProductID"

After mapping all three to canonical "sku" + merge:

Total rows:               15 000
Unique SKUs:              14 982
Duplicates flagged:           18 → reviewed in the merge summary
Output Dataset:           "EU_master_2026Q1" (saved, ready to use)</pre>
          </div>
        </section>

        <!-- TOOLS › CONTAINER ORDER -->
        <section id="tool-container-ord" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">📦</span>
            <h2 class="help-section-title">Tools › Container Order</h2>
          </div>
          <p class="help-text">
            Container Order produces an optimal mix of <strong>Kardex VBM Box</strong> variants
            and quantities from a completed analysis. The output is a single-page plan you can
            attach to a purchase order or quote.
          </p>

          <div class="help-card">
            <h3 class="help-card-title">How the optimal plan is built</h3>
            <div class="help-steps-table prep-grid">
              <div class="help-steps-row help-steps-head">
                <span>Step</span><span>Operation</span><span>Output</span>
              </div>
              <div class="help-steps-row"><span>1</span><span>Read Capacity results in Best Fit mode</span><span>SKU → carrier mapping</span></div>
              <div class="help-steps-row"><span>2</span><span>Group SKUs by chosen carrier variant</span><span>per-variant location count</span></div>
              <div class="help-steps-row"><span>3</span><span>Sum locations per variant (× safety reserve if set)</span><span>required locations per variant</span></div>
              <div class="help-steps-row"><span>4</span><span>Convert locations → containers using Kardex divider layout</span><span>container count per variant</span></div>
              <div class="help-steps-row help-steps-result"><span>→</span><span>One-click plan ready (Advanced fold-out for tweaks)</span><span>variant mix + totals</span></div>
            </div>
          </div>

          <div class="help-tip" style="flex-direction:column;gap:4px">
            <strong><span class="help-tip-icon">📐</span> Kardex 288 mm divider limit</strong>
            <span>The Kardex VBM Box divider system enforces a 288 mm maximum interior depth per
            cell. Any SKU deeper than 288 mm is routed to a variant without the depth divider —
            the planner handles this automatically; you'll see the affected variants flagged in
            the Advanced fold-out.</span>
          </div>
        </section>

        <!-- SHARING -->
        <section id="sharing" class="help-section">
          <div class="help-section-header">
            <span class="help-section-icon">🔗</span>
            <h2 class="help-section-title">Sharing</h2>
          </div>
          <p class="help-text">
            Analyses can be shared with other Datavisor users or made publicly visible. Shared
            users get read-only access — they can view all tabs and download reports, but cannot
            rename, edit notes, delete, or change sharing settings.
          </p>

          <div class="help-card">
            <h3 class="help-card-title">Share with a specific user</h3>
            <ul class="help-list">
              <li>Open the analysis and click <strong>Share</strong> in the top-right header.</li>
              <li>Enter the other user's email address and confirm. They will immediately see the analysis in their Analyses list with a <strong>Shared</strong> badge.</li>
              <li>You can view and revoke individual shares from the same Share panel.</li>
            </ul>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Make an analysis public</h3>
            <ul class="help-list">
              <li>In the Analyses list, click the <strong>globe icon</strong> next to the analysis name to toggle public access on or off.</li>
              <li>Public analyses appear in every user's Analyses list, also marked with a globe icon.</li>
              <li>Only the owner can revert a public analysis back to private.</li>
            </ul>
          </div>

          <div class="help-card">
            <h3 class="help-card-title">Access levels</h3>
            <div class="help-access-table">
              <div class="help-access-row help-access-head">
                <span>Action</span><span>Owner</span><span>Viewer (shared / public)</span>
              </div>
              <div class="help-access-row" v-for="row in accessRows" :key="row.action">
                <span>{{ row.action }}</span>
                <span class="help-access-tick" v-if="row.owner">✓</span>
                <span class="help-access-dash" v-else>—</span>
                <span class="help-access-tick" v-if="row.viewer">✓</span>
                <span class="help-access-dash" v-else>—</span>
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
              <li><strong>KPI cards</strong> — shifts/day and performance scope summaries for the most recent run.</li>
            </ul>
          </div>
        </section>

      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

interface NavNode {
  id: string
  label: string
  icon?: string
  isGroup?: boolean
  children?: NavNode[]
}

const navTree: NavNode[] = [
  { id: 'overview', label: 'Overview', icon: '🗺' },
  {
    id: 'process', label: 'Process', icon: '🧭', isGroup: true,
    children: [
      { id: 'import',      label: 'Import',      icon: '📥' },
      { id: 'quality',     label: 'Quality',     icon: '🔍' },
      { id: 'performance', label: 'Performance', icon: '⚡',
        children: [
          { id: 'performance-kpi',    label: 'KPI metrics' },
          { id: 'performance-abc',    label: 'ABC Classification' },
          { id: 'performance-pareto', label: 'Pareto Concentration' },
        ],
      },
      { id: 'capacity',    label: 'Capacity',    icon: '📦',
        children: [
          { id: 'capacity-fit',   label: 'Fit test (6 orientations)' },
          { id: 'capacity-loc',   label: 'Locations & utilisation' },
          { id: 'capacity-modes', label: 'Analysis modes' },
        ],
      },
      { id: 'reports',     label: 'Reports',     icon: '📄' },
    ],
  },
  {
    id: 'data', label: 'Data & Carriers', icon: '🗂', isGroup: true,
    children: [
      { id: 'datasets', label: 'Datasets', icon: '🧾' },
      { id: 'carriers', label: 'Carriers', icon: '🚚' },
    ],
  },
  {
    id: 'tools', label: 'Tools', icon: '🛠', isGroup: true,
    children: [
      { id: 'tool-data-prep',     label: 'Data Preparation', icon: '🧩' },
      { id: 'tool-container-ord', label: 'Container Order',  icon: '📦' },
    ],
  },
  { id: 'sharing',   label: 'Sharing',   icon: '🔗' },
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
]

const mainRef = ref<HTMLElement | null>(null)
const activeSection = ref('overview')
const expanded = ref<Set<string>>(new Set(['process']))

function toggleGroup(id: string) {
  const next = new Set(expanded.value)
  next.has(id) ? next.delete(id) : next.add(id)
  expanded.value = next
}

function findGroupOf(id: string): string | null {
  for (const g of navTree) {
    if (!g.isGroup) continue
    for (const child of g.children ?? []) {
      if (child.id === id) return g.id
      for (const grand of child.children ?? []) {
        if (grand.id === id) return g.id
      }
    }
  }
  return null
}

watch(activeSection, (id) => {
  const groupId = findGroupOf(id)
  if (groupId && !expanded.value.has(groupId)) {
    expanded.value = new Set([...expanded.value, groupId])
  }
})

function collectAnchorIds(nodes: NavNode[]): string[] {
  const ids: string[] = []
  for (const n of nodes) {
    if (!n.isGroup) ids.push(n.id)
    if (n.children) ids.push(...collectAnchorIds(n.children))
  }
  return ids
}

function scrollTo(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const flowSteps = [
  { name: 'Datasets (optional)', desc: 'Save reusable source files with column mappings so multiple runs can share the same data.' },
  { name: 'Carriers (one-time)', desc: 'Configure your bins / boxes: inner dimensions, max weight, borderline threshold, priority.' },
  { name: 'Import',       desc: 'Load masterdata (SKU dimensions) and orders file, map columns — or attach a saved Dataset.' },
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

const carrierColumns = [
  { name: 'name',                    required: true,  desc: 'Display name of the carrier (bin, box, tote…).' },
  { name: 'inner_length_mm',         required: true,  desc: 'Usable interior length.' },
  { name: 'inner_width_mm',          required: true,  desc: 'Usable interior width.' },
  { name: 'inner_height_mm',         required: true,  desc: 'Usable interior height.' },
  { name: 'max_weight_kg',           required: true,  desc: 'Maximum load. SKUs heavier than this never fit.' },
  { name: 'borderline_threshold_mm', required: false, desc: 'Margin below which a fit is downgraded to <b>BORDERLINE</b> (default 5 mm).' },
  { name: 'priority',                required: false, desc: 'Used by the <em>Prioritized</em> analysis mode (1 = first choice).' },
]

const paretoBandColumns = [
  { name: 'MovedSKU',       desc: 'Cumulative count of top-ranked SKUs at this band boundary (10, 20 … 1 000, 2 000 … total).' },
  { name: 'CumulatedSKU%',  desc: 'MovedSKU as a percentage of all unique SKUs that had at least one order line.' },
  { name: 'Lines/Day',      desc: 'Average daily order lines generated by SKUs <em>in this incremental band only</em> (= band total lines ÷ number of analysis days).' },
  { name: 'Lines%',         desc: "This band's Lines/Day as a share of the overall daily line volume." },
  { name: 'Cumul.Lines%',   desc: 'Running total of Lines% — how much of all lines is covered by the top N SKUs cumulatively.' },
  { name: 'Pieces/Day',     desc: 'Average daily pieces (units) from SKUs in this band.' },
  { name: 'Pieces%',        desc: "This band's Pieces/Day as a share of total daily pieces." },
  { name: 'Cumul.Pieces%',  desc: 'Running total of Pieces% across all SKUs up to this band.' },
]

const accessRows = [
  { action: 'View tabs & results',         owner: true, viewer: true  },
  { action: 'Download reports & CSVs',     owner: true, viewer: true  },
  { action: 'Rename analysis',             owner: true, viewer: false },
  { action: 'Add / edit notes',            owner: true, viewer: false },
  { action: 'Toggle public',               owner: true, viewer: false },
  { action: 'Manage shares',               owner: true, viewer: false },
  { action: 'Delete analysis',             owner: true, viewer: false },
]

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
    { rootMargin: '-20% 0px -70% 0px', threshold: 0 },
  )
  for (const id of collectAnchorIds(navTree)) {
    const el = document.getElementById(id)
    if (el) observer.observe(el)
  }
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>

<style scoped>
.help-page {
  /* No max-width here — uses the 1400 px wrapper from App.vue */
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
  grid-template-columns: 220px 1fr;
  gap: 40px;
  align-items: start;
}

/* Sticky sidebar */
.help-sidebar {
  position: sticky;
  top: 68px;
  max-height: calc(100vh - 88px);
  overflow-y: auto;
  padding-right: 4px;
}

.help-nav-list,
.help-nav-sublist,
.help-nav-sublist-2 {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.help-nav-sublist {
  margin-top: 2px;
  margin-bottom: 4px;
  padding-left: 8px;
  border-left: 1px solid var(--app-border);
  margin-left: 12px;
}

.help-nav-sublist-2 {
  margin-top: 2px;
  margin-bottom: 4px;
  padding-left: 14px;
}

.help-nav-btn,
.help-nav-group {
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

.help-nav-group {
  font-weight: 600;
  color: var(--app-text);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  padding: 9px 10px 5px;
}

.help-nav-chevron {
  width: 10px;
  font-size: 10px;
  color: var(--app-text-sec);
  flex-shrink: 0;
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

.help-nav-btn.level-2 {
  font-size: 12px;
  color: var(--app-text-sec);
  padding: 5px 8px;
}

.help-nav-btn.level-2.active {
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
  margin-bottom: 56px;
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

.help-text a {
  color: var(--color-apple-blue, #0071e3);
  text-decoration: none;
}
.help-text a:hover { text-decoration: underline; }

/* Cards */
.help-card {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 16px 18px;
  margin-bottom: 12px;
}

.help-anchor {
  scroll-margin-top: 80px;
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
  grid-template-columns: 220px 1fr;
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

/* Inline code */
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
  grid-template-columns: 220px 80px 1fr;
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

/* Worked-example card */
.help-example-card {
  background: rgba(52, 199, 89, 0.06);
  border: 1px solid rgba(52, 199, 89, 0.20);
  border-left: 3px solid #34c759;
  border-radius: 10px;
  padding: 12px 14px 14px;
  margin-top: 12px;
}

html.dark .help-example-card {
  background: rgba(52, 199, 89, 0.08);
  border-color: rgba(52, 199, 89, 0.30);
  border-left-color: #34c759;
}

.help-example-label {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: #1e8c40;
  margin-bottom: 8px;
}

html.dark .help-example-label { color: #34c759; }

.help-example-body {
  margin: 0;
  font-family: "SF Mono", "Menlo", "Monaco", "Courier New", monospace;
  font-size: 12px;
  line-height: 1.55;
  color: var(--app-text);
  white-space: pre-wrap;
  word-break: break-word;
}

/* Steps table — used for multi-step worked examples */
.help-steps-table {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  overflow: hidden;
  margin-top: 8px;
  background: var(--app-surface);
}

.help-steps-row {
  display: grid;
  grid-template-columns: 60px 1fr 1fr;
  gap: 8px;
  padding: 7px 10px;
  font-size: 12px;
  align-items: center;
  border-bottom: 1px solid var(--app-border);
}

.help-steps-row:last-child { border-bottom: none; }
.help-steps-row:nth-child(even) { background: var(--app-bg); }

.help-steps-row > span:first-child {
  font-family: "SF Mono", "Menlo", "Monaco", "Courier New", monospace;
  text-align: center;
  color: var(--app-text-sec);
}

.help-steps-row > span:nth-child(3) {
  font-family: "SF Mono", "Menlo", "Monaco", "Courier New", monospace;
}

.help-steps-head {
  background: var(--app-bg) !important;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--app-text-sec);
}

.help-steps-head > span { font-family: inherit !important; text-align: left !important; }

.help-steps-result {
  background: rgba(52, 199, 89, 0.07) !important;
  font-weight: 500;
}

.help-steps-result > span:first-child {
  color: #1e8c40;
  font-weight: 700;
}

html.dark .help-steps-result {
  background: rgba(52, 199, 89, 0.10) !important;
}
html.dark .help-steps-result > span:first-child {
  color: #34c759;
}

/* ABC variant — 5 columns */
.help-steps-table.abc-grid .help-steps-row {
  grid-template-columns: 60px 110px 80px 90px 60px;
}

/* Pareto variant — 4 columns */
.help-steps-table.pareto-grid .help-steps-row {
  grid-template-columns: 90px 90px 80px 110px;
}

/* Fit-test variant — 6 columns */
.help-steps-table.fit-grid .help-steps-row {
  grid-template-columns: 130px 80px 80px 80px 60px 90px;
}

/* Container Order variant — 3 columns */
.help-steps-table.prep-grid .help-steps-row {
  grid-template-columns: 60px 1.5fr 1fr;
}

.abc-tag {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  letter-spacing: 0;
}

/* Access table (Sharing) */
.help-access-table {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--app-surface);
}

.help-access-row {
  display: grid;
  grid-template-columns: 220px 100px 1fr;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  border-bottom: 1px solid var(--app-border);
  align-items: center;
}

.help-access-row:last-child { border-bottom: none; }
.help-access-row:nth-child(even) { background: var(--app-bg); }

.help-access-head {
  background: var(--app-bg) !important;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--app-text-sec);
}

.help-access-tick { color: #1e8c40; font-weight: 700; text-align: center; }
.help-access-dash { color: var(--app-text-sec); text-align: center; }

html.dark .help-access-tick { color: #34c759; }
</style>
