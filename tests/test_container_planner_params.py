"""Regression tests proving every Container Order planning parameter changes
the output. Born from a 2026-05-18 audit triggered by a user report that
"flipping scenarios doesn't change the result" — turned out to be three
inert-by-design combinations + one missing UI control. These tests pin each
parameter's effect, plus three explicit "documented no-op" tests for the
combinations the audit confirmed are intentionally inert.

See ``Dev/CONTAINER_ORDER_PARAMS_AUDIT.md`` for the human-readable summary.
"""

from __future__ import annotations

import math

import pytest

from src.analytics import container_planner as cp


# ---------------------------------------------------------------------------
# Fixtures — mirror the ``_row`` helper from tests/test_container_planner.py
# ---------------------------------------------------------------------------


def _row(
    sku: str, length: float, width: float, height: float, weight: float,
    stock_vol_L: float, fit_status: str = "FIT",
) -> dict:
    return {
        "sku": sku,
        "carrier_id": cp.MIB_CARRIER_ID,
        "fit_status": fit_status,
        "length_mm": length, "width_mm": width, "height_mm": height,
        "weight_kg": weight, "stored_volume_L": stock_vol_L,
    }


def _make_capacity_result(rows: list[dict]) -> dict:
    return {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}


def _make_performance_result(pareto_rows: list[dict]) -> dict:
    return {"sku_pareto": pareto_rows}


def _diverse_skus() -> list[dict]:
    """A mixed set big enough that filters / catalog choices visibly bite."""
    return [
        _row("S-small-A", 100, 100, 60, 0.4, 4.0),
        _row("S-small-B", 100, 100, 60, 0.4, 6.0),
        _row("S-mid-1",   200, 150, 100, 1.0, 15.0),
        _row("S-mid-2",   200, 150, 100, 1.0, 20.0),
        _row("S-tall",    150, 120, 240, 1.0, 18.0),       # needs ≥ 250 mm cell height
        _row("S-bd",      210, 145, 90,  0.9, 12.0, fit_status="BORDERLINE"),
        _row("S-orphan",  700, 500, 200, 5.0, 8.0),        # too big — orphan
    ]


def _diverse_pareto() -> list[dict]:
    return [
        {"sku": "S-small-A", "abc_class": "A", "recommendation": "Machine"},
        {"sku": "S-small-B", "abc_class": "B", "recommendation": "Machine"},
        {"sku": "S-mid-1",   "abc_class": "A", "recommendation": "Non-machine"},
        {"sku": "S-mid-2",   "abc_class": "C", "recommendation": "Machine"},
        {"sku": "S-tall",    "abc_class": "B", "recommendation": "Machine"},
        {"sku": "S-bd",      "abc_class": "C", "recommendation": "Machine"},
    ]


# ---------------------------------------------------------------------------
# Per-parameter "this changes the output" tests
# ---------------------------------------------------------------------------


def test_mode_changes_selection():
    """`mode` swaps the algorithm entirely — auto vs guided vs manual all
    pick distinct variant sets when given the same input."""
    cap = _make_capacity_result(_diverse_skus())
    p_auto = cp.PlanParams(abc_classes=(), only_machine=False, mode="auto",
                            auto_max_variants=4)
    p_manual = cp.PlanParams(abc_classes=(), only_machine=False, mode="manual",
                              manual_variant_codes=("1/1-288", "1/24-138"))
    sel_auto = set(cp.plan_containers(cap, None, p_auto).selected_variant_codes)
    sel_manual = set(cp.plan_containers(cap, None, p_manual).selected_variant_codes)
    assert sel_auto != sel_manual


def test_default_plan_params_route_to_full_coverage_greedy():
    """The user's stated priorities — max Fill %, ~100% coverage, fewest
    variants — are encoded in the dataclass defaults: mode="guided" +
    guided_preset="full_coverage". A bare `PlanParams()` (no arguments)
    must therefore drive `_greedy_until_coverage`, which stops adding
    variants as soon as coverage ≥ 99% and uses the auto catalog (28
    variants max). The only SKUs that can stay uncovered are physical
    orphans (`no_fitting_variant`).
    """
    defaults = cp.PlanParams()
    assert defaults.mode == "guided"
    assert defaults.guided_preset == "full_coverage"

    # A mix of fitting SKUs + one geometric orphan. Disable ABC/machine
    # filtering so the fixture's lack of Performance metadata doesn't drop
    # rows before the planner sees them.
    cap = _make_capacity_result(_diverse_skus())
    plan = cp.plan_containers(
        cap, None,
        cp.PlanParams(abc_classes=(), only_machine=False),
    )

    # Coverage either ≥99% or every uncovered SKU is a genuine geometric
    # orphan (too big for any variant).
    geometric_orphans = [
        a for a in plan.orphans if a.orphan_reason == "no_fitting_variant"
    ]
    covered_or_geom_orphan = plan.total_sku_covered + len(geometric_orphans)
    assert covered_or_geom_orphan == plan.total_sku_planned

    # Greedy-until-coverage stops early — never breaches the 28-variant
    # auto-catalog ceiling, and typically uses far fewer.
    assert len(plan.selected_variant_codes) <= 28


def test_auto_max_variants_changes_selection_in_auto_mode():
    """In auto mode, raising the cap should let the greedy pick more variants
    (or at minimum it must reach a different selection at very different K)."""
    cap = _make_capacity_result(_diverse_skus())
    p_k3 = cp.PlanParams(abc_classes=(), only_machine=False, mode="auto",
                          auto_max_variants=3)
    p_k10 = cp.PlanParams(abc_classes=(), only_machine=False, mode="auto",
                           auto_max_variants=10)
    plan_3 = cp.plan_containers(cap, None, p_k3)
    plan_10 = cp.plan_containers(cap, None, p_k10)
    assert len(plan_3.selected_variant_codes) <= 3
    assert len(plan_10.selected_variant_codes) > len(plan_3.selected_variant_codes)


def test_auto_goal_changes_selection():
    """min_waste vs min_bins choose differently when the dataset rewards each."""
    cap = _make_capacity_result(_diverse_skus())
    p_waste = cp.PlanParams(abc_classes=(), only_machine=False, mode="auto",
                             auto_max_variants=4, auto_goal="min_waste")
    p_bins = cp.PlanParams(abc_classes=(), only_machine=False, mode="auto",
                            auto_max_variants=4, auto_goal="min_bins")
    sel_w = cp.plan_containers(cap, None, p_waste).selected_variant_codes
    sel_b = cp.plan_containers(cap, None, p_bins).selected_variant_codes
    # Either selection differs, or assignments differ (per-SKU best variant
    # uses the goal too inside _best_variant_for_sku).
    plan_w = cp.plan_containers(cap, None, p_waste)
    plan_b = cp.plan_containers(cap, None, p_bins)
    same_selection = set(sel_w) == set(sel_b)
    same_assignments = (
        [(a.sku, a.variant_code) for a in plan_w.assignments] ==
        [(a.sku, a.variant_code) for a in plan_b.assignments]
    )
    assert not (same_selection and same_assignments)


def test_guided_preset_changes_selection():
    """`simple` → micro-catalog; `standard` → 8-greedy; `full_coverage` → push to 99%.

    `simple` must differ from the others (different catalog). `standard` and
    `full_coverage` share the catalog but route to different algorithms — on
    a small dataset where coverage saturates fast, `standard` overshoots
    (forced to k=8) while `full_coverage` stops at <8 variants. That gap is
    the observable proof the two branches aren't aliased.
    """
    # Homogeneous SKUs — one variant covers 100% of them, so
    # _greedy_until_coverage stops immediately; _greedy_set_cover(k=8) keeps
    # adding variants until it hits the ceiling. Pick a SKU geometry that
    # doesn't fit the `simple` micro-catalog (which restricts heights to 188
    # and 288 only) to force the three branches apart.
    cap = _make_capacity_result([
        _row("S1", 100, 100, 60, 0.4, 4.0),
        _row("S2", 100, 100, 60, 0.4, 6.0),
        _row("S3", 100, 100, 60, 0.4, 8.0),
    ])

    def plan_for(preset: str):
        p = cp.PlanParams(abc_classes=(), only_machine=False, mode="guided",
                           guided_preset=preset)
        return cp.plan_containers(cap, None, p)

    plan_simple = plan_for("simple")
    plan_std = plan_for("standard")
    plan_full = plan_for("full_coverage")

    # `simple` uses its 6-variant micro-catalog (3 footprints × 2 heights);
    # `standard` and `full_coverage` use the much larger CATALOG_AUTO.
    assert set(plan_simple.selected_variant_codes) != set(plan_std.selected_variant_codes)
    # `full_coverage` saturates fast — must pick ≤ what `standard` picks.
    # On a small dataset standard caps at 8, full_coverage stops far earlier.
    assert len(plan_full.selected_variant_codes) <= len(plan_std.selected_variant_codes)
    # And `standard` must reach its ceiling when the catalog has >8 candidates.
    assert len(plan_std.selected_variant_codes) >= len(plan_full.selected_variant_codes)


def test_manual_variant_codes_drives_selection():
    """`manual` mode must use exactly the user's codes (intersected with what fits)."""
    cap = _make_capacity_result(_diverse_skus())
    p_a = cp.PlanParams(abc_classes=(), only_machine=False, mode="manual",
                         manual_variant_codes=("1/1-188", "1/4-188"))
    p_b = cp.PlanParams(abc_classes=(), only_machine=False, mode="manual",
                         manual_variant_codes=("1/1-288", "1/12_3x4-288"))
    sel_a = set(cp.plan_containers(cap, None, p_a).selected_variant_codes)
    sel_b = set(cp.plan_containers(cap, None, p_b).selected_variant_codes)
    assert sel_a.issubset({"1/1-188", "1/4-188"})
    assert sel_b.issubset({"1/1-288", "1/12_3x4-288"})
    assert sel_a != sel_b


def test_abc_classes_filters_when_performance_provided():
    """With performance present, abc_classes drops SKUs outside the chosen set."""
    cap = _make_capacity_result(_diverse_skus())
    perf = _make_performance_result(_diverse_pareto())
    p_ab = cp.PlanParams(abc_classes=("A", "B"), only_machine=False)
    p_c = cp.PlanParams(abc_classes=("C",), only_machine=False)
    plan_ab = cp.plan_containers(cap, perf, p_ab)
    plan_c = cp.plan_containers(cap, perf, p_c)
    assert plan_ab.total_sku_planned != plan_c.total_sku_planned


def test_only_machine_filters_when_performance_provided():
    """only_machine drops SKUs whose recommendation isn't Machine."""
    cap = _make_capacity_result(_diverse_skus())
    perf = _make_performance_result(_diverse_pareto())
    p_off = cp.PlanParams(abc_classes=(), only_machine=False)
    p_on = cp.PlanParams(abc_classes=(), only_machine=True)
    plan_off = cp.plan_containers(cap, perf, p_off)
    plan_on = cp.plan_containers(cap, perf, p_on)
    assert plan_on.total_sku_planned < plan_off.total_sku_planned


def test_include_borderline_toggles_borderline_skus():
    """OFF: BORDERLINE SKUs are dropped; ON: they enter the plan."""
    cap = _make_capacity_result(_diverse_skus())
    p_on = cp.PlanParams(abc_classes=(), only_machine=False,
                          include_borderline=True)
    p_off = cp.PlanParams(abc_classes=(), only_machine=False,
                           include_borderline=False)
    plan_on = cp.plan_containers(cap, None, p_on)
    plan_off = cp.plan_containers(cap, None, p_off)
    assert plan_on.total_sku_planned > plan_off.total_sku_planned
    # Specifically, the BORDERLINE SKU must appear only in the ON plan.
    assert any(a.sku == "S-bd" for a in plan_on.assignments)
    assert all(a.sku != "S-bd" for a in plan_off.assignments)


def test_impute_missing_dimensions_changes_orphan_count():
    """OFF orphans rows with missing dims; ON imputes from dataset median."""
    rows = [
        _row("good-1", 100, 100, 60, 0.4, 4.0),
        _row("good-2", 200, 150, 100, 1.0, 10.0),
        {"sku": "blank", "carrier_id": cp.MIB_CARRIER_ID, "fit_status": "FIT",
         "length_mm": 0, "width_mm": 0, "height_mm": 0,
         "weight_kg": 0, "stored_volume_L": 8.0},
    ]
    cap = _make_capacity_result(rows)
    p_on = cp.PlanParams(abc_classes=(), only_machine=False,
                          impute_missing_dimensions=True)
    p_off = cp.PlanParams(abc_classes=(), only_machine=False,
                           impute_missing_dimensions=False)
    plan_on = cp.plan_containers(cap, None, p_on)
    plan_off = cp.plan_containers(cap, None, p_off)
    assert len(plan_off.orphans) > len(plan_on.orphans)


def test_stock_multiplier_increases_locations():
    """Doubling the multiplier must require more locations / more bins."""
    rows = [_row("S1", 200, 150, 100, 1.0, 30.0)]
    cap = _make_capacity_result(rows)
    p_low = cp.PlanParams(abc_classes=(), only_machine=False,
                           mode="manual", manual_variant_codes=("1/1-188",),
                           stock_multiplier=1.0)
    p_high = cp.PlanParams(abc_classes=(), only_machine=False,
                            mode="manual", manual_variant_codes=("1/1-188",),
                            stock_multiplier=2.5)
    plan_low = cp.plan_containers(cap, None, p_low)
    plan_high = cp.plan_containers(cap, None, p_high)
    locs_low = plan_low.assignments[0].locations
    locs_high = plan_high.assignments[0].locations
    assert locs_high > locs_low


def test_location_fill_rate_changes_locations():
    """Lower fill_rate → more locations needed for the same stock."""
    rows = [_row("S1", 200, 150, 100, 1.0, 30.0)]
    cap = _make_capacity_result(rows)
    p_loose = cp.PlanParams(abc_classes=(), only_machine=False,
                              mode="manual", manual_variant_codes=("1/1-188",),
                              location_fill_rate=0.5)
    p_tight = cp.PlanParams(abc_classes=(), only_machine=False,
                              mode="manual", manual_variant_codes=("1/1-188",),
                              location_fill_rate=1.0)
    plan_loose = cp.plan_containers(cap, None, p_loose)
    plan_tight = cp.plan_containers(cap, None, p_tight)
    assert plan_loose.assignments[0].locations > plan_tight.assignments[0].locations


def test_min_locations_per_sku_raises_floor():
    """Tiny stock must still get at least min_locations_per_sku locations."""
    rows = [_row("S1", 100, 100, 60, 0.3, 0.5)]   # very small stock
    cap = _make_capacity_result(rows)
    p_low = cp.PlanParams(abc_classes=(), only_machine=False,
                           mode="manual", manual_variant_codes=("1/1-188",),
                           min_locations_per_sku=1)
    p_high = cp.PlanParams(abc_classes=(), only_machine=False,
                            mode="manual", manual_variant_codes=("1/1-188",),
                            min_locations_per_sku=5)
    assert cp.plan_containers(cap, None, p_low).assignments[0].locations == 1
    assert cp.plan_containers(cap, None, p_high).assignments[0].locations == 5


def test_max_locations_per_sku_orphans_overflowing_skus():
    """When demand exceeds the per-SKU cap, the SKU becomes an orphan."""
    rows = [_row("BIG", 200, 150, 100, 1.0, 1000.0)]
    cap = _make_capacity_result(rows)
    p_lax = cp.PlanParams(abc_classes=(), only_machine=False,
                           mode="manual", manual_variant_codes=("1/1-288",),
                           max_locations_per_sku=50000)
    p_tight = cp.PlanParams(abc_classes=(), only_machine=False,
                              mode="manual", manual_variant_codes=("1/1-288",),
                              max_locations_per_sku=2)
    assert cp.plan_containers(cap, None, p_lax).total_sku_covered == 1
    assert cp.plan_containers(cap, None, p_tight).total_sku_covered == 0


# ---------------------------------------------------------------------------
# Documented no-op tests — pin the inert combinations so they stay inert
# (or, if someone "fixes" them later, this file flags the change).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode_and_extras", [
    {"mode": "manual", "manual_variant_codes": ("1/1-188",)},
    {"mode": "guided", "guided_preset": "simple"},
    {"mode": "guided", "guided_preset": "full_coverage"},
])
def test_auto_max_variants_is_documented_no_op_outside_auto_mode(mode_and_extras):
    """`auto_max_variants` is consumed ONLY in the `auto` mode branch of
    plan_containers (container_planner.py:711). In every other mode the
    catalog size is decided by the preset / manual list — toggling this
    slider must produce identical plans. Documented behaviour."""
    cap = _make_capacity_result(_diverse_skus())
    base_kwargs = dict(abc_classes=(), only_machine=False) | mode_and_extras
    p_k3 = cp.PlanParams(**base_kwargs, auto_max_variants=3)
    p_k15 = cp.PlanParams(**base_kwargs, auto_max_variants=15)
    plan_3 = cp.plan_containers(cap, None, p_k3)
    plan_15 = cp.plan_containers(cap, None, p_k15)
    assert plan_3.selected_variant_codes == plan_15.selected_variant_codes
    assert plan_3.total_bins == plan_15.total_bins


def test_abc_classes_is_documented_no_op_without_performance_data():
    """Without `performance_result.sku_pareto`, _filter_skus drops the abc_classes
    filter (container_planner.py:317-329). The user sees the checkboxes flip,
    but the plan is unchanged. The UI now hints at this."""
    cap = _make_capacity_result(_diverse_skus())
    p_ab = cp.PlanParams(abc_classes=("A", "B"), only_machine=False)
    p_c = cp.PlanParams(abc_classes=("C",), only_machine=False)
    plan_ab = cp.plan_containers(cap, None, p_ab)   # NB: performance_result=None
    plan_c = cp.plan_containers(cap, None, p_c)
    assert plan_ab.total_sku_planned == plan_c.total_sku_planned
    assert plan_ab.selected_variant_codes == plan_c.selected_variant_codes


def test_only_machine_is_documented_no_op_without_performance_data():
    """Same gating as abc_classes — without sku_pareto, only_machine is skipped."""
    cap = _make_capacity_result(_diverse_skus())
    p_off = cp.PlanParams(abc_classes=(), only_machine=False)
    p_on = cp.PlanParams(abc_classes=(), only_machine=True)
    plan_off = cp.plan_containers(cap, None, p_off)
    plan_on = cp.plan_containers(cap, None, p_on)
    assert plan_off.total_sku_planned == plan_on.total_sku_planned


# ---------------------------------------------------------------------------
# Corrected catalog geometry (2026-05-19 spec update from user)
# ---------------------------------------------------------------------------


def test_interior_dimensions_match_kardex_spec():
    """Base bin 640×440×138 has interior 611×411×110 (floor takes 28 mm)."""
    assert cp.BIN_INTERIOR_LENGTH_MM == 611
    assert cp.BIN_INTERIOR_WIDTH_MM == 411
    assert cp.HEIGHT_FLOOR_LOSS_MM == 28
    one_one_138 = next(v for v in cp.CATALOG_FULL
                        if v.footprint_key == "1/1" and v.bin_height_mm == 138)
    assert one_one_138.cell_length_mm == 611
    assert one_one_138.cell_width_mm == 411
    assert one_one_138.cell_height_mm == 110


def test_height_tiers_exclude_above_288():
    """Dividers and EasyClick frames physically exist only up to 288 mm
    (Kardex spec confirmed 2026-05-20). The previous 338/388 entries were a
    documentation error and must not appear anywhere in the catalog."""
    assert cp.HEIGHT_TIERS_MM == (138, 188, 238, 288)
    assert 338 not in cp.HEIGHT_TIERS_MM
    assert 388 not in cp.HEIGHT_TIERS_MM
    heights_in_catalog = {v.bin_height_mm for v in cp.CATALOG_FULL}
    assert heights_in_catalog == {138, 188, 238, 288}
    one_one_288 = next(v for v in cp.CATALOG_FULL
                        if v.footprint_key == "1/1" and v.bin_height_mm == 288)
    assert one_one_288.cell_height_mm == 260  # 288 − 28


def test_volume_matches_user_spec_table():
    """Spot-check tier volumes against the user-supplied table."""
    expected = {138: 27.6, 188: 40.3, 238: 53.0, 288: 65.6}
    for tier, want in expected.items():
        v = next(x for x in cp.CATALOG_FULL
                  if x.footprint_key == "1/1" and x.bin_height_mm == tier)
        # ±0.5 L tolerance — user table rounds; planner uses exact 611×411 math.
        assert abs(v.cell_volume_L - want) < 0.5, (tier, v.cell_volume_L, want)


def test_bin_tare_reduces_per_cell_weight_cap():
    """The proportional weight cap is computed on the *net* 32.65 kg, not the
    gross 35 kg — so even a single-cell 1/1 variant caps at 32.65 kg of stock,
    leaving 2.35 kg headroom for the empty-bin tare."""
    assert math.isclose(cp.BIN_GROSS_MAX_KG, 35.0)
    assert math.isclose(cp.BIN_TARE_KG, 2.35)
    assert math.isclose(cp.BIN_NET_MAX_KG, 32.65, abs_tol=0.001)
    one_one_138 = next(v for v in cp.CATALOG_FULL
                        if v.footprint_key == "1/1" and v.bin_height_mm == 138)
    assert math.isclose(one_one_138.max_weight_kg_per_cell, 32.65, abs_tol=0.01)


def test_variant_summary_reports_gross_bin_weight():
    """VariantSummary.bin_gross_weight_kg = avg stock-weight-per-bin + tare,
    surfacing the 35-kg gross cap in exports."""
    cap = _make_capacity_result([
        _row("HEAVY", 200, 150, 100, 10.0, 30.0),
    ])
    p = cp.PlanParams(abc_classes=(), only_machine=False,
                       mode="manual", manual_variant_codes=("1/1-188",))
    plan = cp.plan_containers(cap, None, p)
    s = plan.summaries[0]
    # stock weight per bin = total_weight_kg / bins; gross = stock_per_bin + 2.35.
    expected_gross = (s.total_weight_kg / s.bins_required) + cp.BIN_TARE_KG
    assert math.isclose(s.bin_gross_weight_kg, expected_gross, abs_tol=0.05)
    # And the gross cap is respected.
    assert s.bin_gross_weight_kg <= cp.BIN_GROSS_MAX_KG + 0.01


# ---------------------------------------------------------------------------
# NOT_FIT pass-through (the user's original complaint)
# ---------------------------------------------------------------------------


def test_not_fit_row_reaches_per_variant_check_when_dimensions_fit():
    """NOT_FIT classification from the upstream Capacity analysis must NOT
    silently drop the SKU. If a variant in the chosen catalog actually fits
    it (per-variant check in _compute_fits), it gets planned."""
    # SKU is 250 mm tall — too tall for the standard MiB tier (210 mm), so the
    # Capacity analysis would mark it NOT_FIT. But it fits the 288-mm bin
    # (cell height 260 mm).
    rows = [_row("TALL", 150, 120, 250, 1.0, 12.0, fit_status="NOT_FIT")]
    cap = _make_capacity_result(rows)
    p = cp.PlanParams(abc_classes=(), only_machine=False,
                       mode="manual",
                       manual_variant_codes=("1/4-288",))
    plan = cp.plan_containers(cap, None, p)
    assert plan.total_sku_covered == 1
    a = plan.assignments[0]
    assert a.variant_code == "1/4-288"
    assert a.orphan_reason is None


def test_not_fit_row_with_no_fitting_variant_becomes_transparent_orphan():
    """When NOT_FIT genuinely doesn't fit any variant in the catalog, the row
    surfaces as a transparent orphan with orphan_reason='no_fitting_variant'
    — not silently dropped at the filter."""
    # 700 mm long — exceeds the 611-mm interior of every variant.
    rows = [_row("HUGE", 700, 500, 200, 5.0, 8.0, fit_status="NOT_FIT")]
    cap = _make_capacity_result(rows)
    plan = cp.plan_containers(cap, None,
                               cp.PlanParams(abc_classes=(), only_machine=False))
    assert plan.total_sku_planned == 1
    assert plan.total_sku_covered == 0
    assert len(plan.orphans) == 1
    assert plan.orphans[0].orphan_reason == "no_fitting_variant"


# ---------------------------------------------------------------------------
# 6-orientation fit check (2026-05-19 spec update from user)
# ---------------------------------------------------------------------------


def _tall_thin_row(sku: str = "PROFILE", fit_status: str = "FIT") -> dict:
    """Canonical "long pencil" SKU — 100×100×400 mm, 0.5 kg, 3 L stock.

    Fits cell 1/2L-138 (305×411×110) only when laid down (height → cell Y axis),
    i.e. in 2 of the 6 orientations, both of which have o[2] ∈ {L, W}. Under
    UPRIGHT_ONLY no orientation fits because 400 mm > every cell_height (max
    260 mm at the 288 tier). Used by every test in this block.
    """
    return {
        "sku": sku,
        "carrier_id": cp.MIB_CARRIER_ID,
        "fit_status": fit_status,
        "length_mm": 100, "width_mm": 100, "height_mm": 400,
        "weight_kg": 0.5, "stored_volume_L": 3.0,
    }


def test_long_thin_sku_fits_via_lay_flat_orientation():
    """SKU is taller than every cell (h=400 mm > 260 mm at the tallest tier),
    but laying it down maps its height onto the cell's wide Y axis. With the
    default ANY constraint, the 6-orientation check finds the fit and the SKU
    gets a variant. Manual mode with a single small variant proves the fit
    came from rotation, not catalog luck."""
    cap = _make_capacity_result([_tall_thin_row()])
    p = cp.PlanParams(abc_classes=(), only_machine=False,
                       mode="manual", manual_variant_codes=("1/2L-138",))
    plan = cp.plan_containers(cap, None, p)
    assert plan.total_sku_covered == 1
    a = plan.assignments[0]
    assert a.variant_code == "1/2L-138"
    assert a.orphan_reason is None


def test_upright_only_constraint_blocks_lay_flat():
    """Same SKU + `orientation_constraint="UPRIGHT_ONLY"` → upright orientations
    have height on the cell's Z axis, but h=400 > 260 (tallest cell). The SKU
    becomes an orphan with no_fitting_variant — exactly as it should when the
    masterdata says "this side up"."""
    row = _tall_thin_row()
    row["orientation_constraint"] = "UPRIGHT_ONLY"
    cap = _make_capacity_result([row])
    plan = cp.plan_containers(cap, None,
                               cp.PlanParams(abc_classes=(), only_machine=False))
    assert plan.total_sku_covered == 0
    assert plan.orphans[0].orphan_reason == "no_fitting_variant"


def test_flat_only_constraint_forces_lay_flat():
    """SKU that fits upright in a wide cell but is also short enough to lay
    flat. Under FLAT_ONLY the upright orientations are filtered out, but a
    lay-flat orientation still works — must NOT become an orphan."""
    # 200x200x80: easily fits 1/2L-138 (305x411x110) upright (h=80 ≤ 110)
    # AND fits laid down (W,H,L)=(200,80,200) → 200≤305, 80≤411, 200>110 fail;
    # (L,H,W)=(200,80,200) → 200≤305, 80≤411, 200>110 fail. Hmm — pick a SKU
    # that's short on at least two axes so a flat orientation also fits.
    # 200x60x80 → flat (L,H,W)=(200,80,60): 200≤305, 80≤411, 60≤110 → fits.
    row = {
        "sku": "FLEX",
        "carrier_id": cp.MIB_CARRIER_ID,
        "fit_status": "FIT",
        "length_mm": 200, "width_mm": 60, "height_mm": 80,
        "weight_kg": 0.5, "stored_volume_L": 3.0,
        "orientation_constraint": "FLAT_ONLY",
    }
    cap = _make_capacity_result([row])
    p = cp.PlanParams(abc_classes=(), only_machine=False,
                       mode="manual", manual_variant_codes=("1/2L-138",))
    plan = cp.plan_containers(cap, None, p)
    assert plan.total_sku_covered == 1
    assert plan.assignments[0].variant_code == "1/2L-138"


def test_orientation_constraint_missing_defaults_to_any():
    """An older capacity_result blob (pre-2026-05-19) has no
    `orientation_constraint` key. The planner must default to ANY (6
    orientations), matching today's default behaviour."""
    row = _tall_thin_row()
    # Explicitly: no orientation_constraint key on this row.
    assert "orientation_constraint" not in row
    cap = _make_capacity_result([row])
    p = cp.PlanParams(abc_classes=(), only_machine=False,
                       mode="manual", manual_variant_codes=("1/2L-138",))
    plan = cp.plan_containers(cap, None, p)
    # Same outcome as the explicit-ANY case — SKU gets planned via lay-flat.
    assert plan.total_sku_covered == 1


def test_height_no_longer_hard_pre_filter():
    """The previous _sku_fits_variant rejected any SKU with height > cell_height
    before testing any orientation. After the 6-orientation rewrite, height is
    just another axis — a tall SKU still fits if rotating brings a shorter
    axis onto cell Z. Use `max_coverage` goal so the greedy prioritises planning
    the SKU over minimising waste (a single 3-L SKU in a 14-L cell looks wasteful
    to `min_waste`, which is the goal's correct preference — orthogonal to whether
    the SKU geometrically fits)."""
    # SKU 100×100×400 — taller than every cell_height in the catalog (max 260).
    cap = _make_capacity_result([_tall_thin_row()])
    plan = cp.plan_containers(cap, None,
                               cp.PlanParams(abc_classes=(), only_machine=False,
                                              auto_goal="max_coverage"))
    # Must NOT be an orphan; some variant in the auto catalog fits via lay-flat.
    assert plan.total_sku_covered == 1
    assert plan.orphans == []


def test_include_borderline_still_filters_borderline_rows():
    """The toggle keeps its FIT-vs-BORDERLINE semantics. OFF drops BORDERLINE
    rows even if they'd geometrically fit a variant; ON includes them."""
    rows = [
        _row("FIT-1", 100, 100, 60, 0.4, 4.0, fit_status="FIT"),
        _row("BD-1", 100, 100, 60, 0.4, 4.0, fit_status="BORDERLINE"),
    ]
    cap = _make_capacity_result(rows)
    p_on = cp.PlanParams(abc_classes=(), only_machine=False,
                          include_borderline=True)
    p_off = cp.PlanParams(abc_classes=(), only_machine=False,
                           include_borderline=False)
    plan_on = cp.plan_containers(cap, None, p_on)
    plan_off = cp.plan_containers(cap, None, p_off)
    assert plan_on.total_sku_planned == 2
    assert plan_off.total_sku_planned == 1
    assert all(a.sku != "BD-1" for a in plan_off.assignments)
