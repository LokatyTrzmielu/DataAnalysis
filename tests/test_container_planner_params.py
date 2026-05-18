"""Regression tests proving every Container Order planning parameter changes
the output. Born from a 2026-05-18 audit triggered by a user report that
"flipping scenarios doesn't change the result" — turned out to be three
inert-by-design combinations + one missing UI control. These tests pin each
parameter's effect, plus three explicit "documented no-op" tests for the
combinations the audit confirmed are intentionally inert.

See ``Dev/CONTAINER_ORDER_PARAMS_AUDIT.md`` for the human-readable summary.
"""

from __future__ import annotations

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
    # Two homogeneous SKUs — one variant covers 100% of them, so
    # _greedy_until_coverage stops immediately; _greedy_set_cover(k=8) keeps
    # adding variants until it hits the ceiling.
    cap = _make_capacity_result([
        _row("S1", 100, 100, 60, 0.4, 4.0),
        _row("S2", 100, 100, 60, 0.4, 6.0),
    ])

    def plan_for(preset: str):
        p = cp.PlanParams(abc_classes=(), only_machine=False, mode="guided",
                           guided_preset=preset)
        return cp.plan_containers(cap, None, p)

    plan_simple = plan_for("simple")
    plan_std = plan_for("standard")
    plan_full = plan_for("full_coverage")

    # `simple` uses its 6-variant micro-catalog → cannot match `standard`'s
    # 28-variant catalog selection.
    assert set(plan_simple.selected_variant_codes) != set(plan_std.selected_variant_codes)
    assert set(plan_simple.selected_variant_codes) != set(plan_full.selected_variant_codes)
    # `full_coverage` saturates fast — must pick *fewer* variants than the
    # k=8 forced ceiling of `standard`.
    assert len(plan_full.selected_variant_codes) < len(plan_std.selected_variant_codes)


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
