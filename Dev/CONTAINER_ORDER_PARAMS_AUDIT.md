# Container Order — parameter handling audit

**Date:** 2026-05-18
**Trigger:** user reported that flipping scenarios in the Calculation tab produced no visible change in the result.
**Verdict:** every parameter is wired correctly *somewhere*. Three of them can legitimately appear inert from the user's seat — those are now mitigated by UI fixes (see *Mitigations* at the bottom), not by changing backend semantics.

---

## Per-parameter table

| Parameter | Wired? | Where the planner reads it | User-visible effect | Inert when… |
|---|---|---|---|---|
| `mode` | ✅ | `_eligible_catalog` (`container_planner.py:333`), `plan_containers` (`:703–712`) | switches selection algorithm and catalog size | never |
| `auto_max_variants` | ⚠ | `plan_containers:711` — only when `mode == "auto"` | controls greedy `k` → number of variants picked in auto | `mode in {guided, manual}` — hardcoded `k=8` in guided-standard, ignored elsewhere |
| `auto_goal` | ✅ | `_greedy_set_cover:553`, `_best_variant_for_sku:487–504` (always, even in manual) | greedy cost function + per-SKU best-variant pick | never |
| `guided_preset` | ✅ | `plan_containers:705–712` (3 distinct branches) | `simple` → 6-variant micro-catalog; `standard` → CATALOG_AUTO + greedy k=8; `full_coverage` → CATALOG_AUTO + greedy until 99% coverage | never |
| `manual_variant_codes` | ✅ | `plan_containers:703–704` | directly drives selection | empty list falls through to auto (by design) |
| `abc_classes` | ⚠ | `_filter_skus:323` — only when `performance_result` exists | drops SKUs outside selected classes | run has **no Performance results** → filter silently skipped |
| `only_machine` | ⚠ | `_filter_skus:326` — only when `performance_result` exists | drops SKUs flagged Non-machine | run has **no Performance results** → filter silently skipped |
| `include_borderline` | ✅ | `_filter_skus` (BORDERLINE row drop) | OFF excludes BORDERLINE-classified rows; ON includes them alongside FIT and NOT_FIT | now exposed in UI (was missing before 2026-05-18) |
| ~~fit_status NOT_FIT gate~~ | ❌ | **removed 2026-05-19** | (used to silently drop NOT_FIT rows in `_filter_skus`) | replaced by per-variant check in `_compute_fits` — NOT_FIT rows now reach the variant catalog and either get planned or become transparent orphans |
| Geometric fit check (orientations) | ✅ | `_sku_fits_variant` (`container_planner.py`) — rewritten 2026-05-19 to test all 6 (L,W,H) → (X,Y,Z) permutations, gated by per-SKU `orientation_constraint` forwarded from `capacity_result.rows` (default `ANY` → 6 orientations) | long-and-thin SKUs (cables/profiles/sheets) now fit cells they couldn't reach under the old 2-orientation horizontal-only check | the chosen orientation is internal-only — not surfaced in SKU table / exports (user decision 2026-05-19) |
| `impute_missing_dimensions` | ✅ | `_compute_fits:421` | OFF: SKUs with missing dims become orphans. ON: median imputation | never |
| `stock_multiplier` | ✅ | `_compute_fits:446` → `_locations_needed:263` | scales stock volume before location math | `min_locations_per_sku` floor can mask the effect for tiny stock |
| `location_fill_rate` | ✅ | `_locations_needed:263` | denominator in `ceil(stock_vol / (cell_vol × fill_rate))` | never |
| `min_locations_per_sku` | ✅ | `_locations_needed:268` | minimum locations enforced per SKU | never |
| `max_locations_per_sku` | ✅ | `_locations_needed:269–270` | SKUs requiring more become orphans | never |

Line references valid as of commit `5b3c2e5` (2026-05-18).

---

## What looks broken but isn't

### 1. `auto_max_variants` slider doesn't move anything in guided / manual mode

By design. The catalog size in guided mode is decided by the **preset**, not by a slider:

```text
guided + simple        →  6 variants (3 footprints × 2 heights), all selected
guided + standard      →  CATALOG_AUTO, greedy picks 8
guided + full_coverage →  CATALOG_AUTO, greedy adds variants until ≥ 99% coverage
manual                 →  user's checkboxed variant_codes
```

The UI already hides the slider when `mode !== 'auto'`, so this is mostly invisible.

### 2. `ABC classes` + `Only Machine` filters silently do nothing for some runs

Both filters consult `performance_result.sku_pareto` for the class / recommendation labels. If the source analysis has **no Performance run**, that map is empty and the filters are skipped — `_filter_skus` falls into "lenient mode" (`container_planner.py:317`). Until today the user had no signal that this was happening.

The UI now shows an inline hint under both controls when `currentRun.has_performance === false`:

> *Filter only takes effect when the source run has Performance results.*

### 3. `include_borderline` couldn't be toggled

The backend honours the parameter (it's checked on every row inside `_filter_skus`). The frontend simply had no checkbox / toggle — so the request always carried the default `true`, and SKUs marked BORDERLINE were always planned in. The toggle is now in row 1 of the Calculation parameters block, next to *Only Machine* and *Impute missing*.

---

## Mitigations (now shipped)

1. **`include_borderline` toggle** added to `ContainerOrderView.vue`. Defaults to ON for behavioural parity with old runs.
2. **Inert-mode hint** under ABC + Only Machine when the current run lacks Performance results.
3. **"Parameters actually used by the planner"** collapsible block under the Calculate button — prints `plan.params_echo`. Lets the user verify what the backend acted on without leaving the tab.
4. **Regression coverage** — `tests/test_container_planner_params.py` proves every numeric / enum parameter changes the output, plus three explicit *documented no-op* tests that pin the inert combinations.

No backend semantics were changed; everything was already wired correctly *for the cases it applies to*.

---

## Verifying yourself

```powershell
python -m pytest tests/test_container_planner_params.py -v
python -m pytest tests/test_container_planner.py tests/test_container_planner_params.py -q
```

To reproduce the user's original complaint manually:

1. Load a Container Order analysis whose source run has **no Performance results**.
2. Tick / untick `A` / `B` / `C` checkboxes → coverage and total bins do not change → expected, because Performance is missing.
3. Open the *"Parameters actually used"* fold-out under Calculate → confirm `abc_classes` is echoed but had no effect because `performance_result` was empty.
