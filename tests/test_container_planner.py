"""Tests for src.analytics.container_planner."""

from __future__ import annotations

import math

import pytest

from src.analytics import container_planner as cp


# ---------------------------------------------------------------------------
# Catalog sanity
# ---------------------------------------------------------------------------


def test_catalog_full_has_48_variants():
    assert len(cp.CATALOG_FULL) == 48


def test_catalog_auto_has_28_variants():
    assert len(cp.CATALOG_AUTO) == 28
    assert all(v.in_auto_catalog for v in cp.CATALOG_AUTO)


def test_height_tiers_match_pdf():
    tiers = sorted({v.bin_height_mm for v in cp.CATALOG_FULL})
    assert tiers == [138, 188, 238, 288]


def test_footprints_present():
    keys = {v.footprint_key for v in cp.CATALOG_FULL}
    expected = {"1/1", "1/2L", "1/2W", "1/3W", "1/3L", "1/4",
                "1/6_3x2", "1/6_2x3", "1/8", "1/12_3x4", "1/12_6x2", "1/24"}
    assert keys == expected


def test_full_bin_weight_cap_equals_kardex_spec():
    full = next(v for v in cp.CATALOG_FULL if v.footprint_key == "1/1")
    # 1/1 occupies the entire usable area → full 35 kg cap.
    assert math.isclose(full.max_weight_kg_per_cell, 35.0, rel_tol=0.02)


def test_variant_frames_per_bin_derived_from_height():
    """EasyClick formula: frames_per_bin = (bin_height_mm - 138) // 50."""
    by_height = {v.bin_height_mm: v.frames_per_bin
                 for v in cp.CATALOG_FULL if v.footprint_key == "1/1"}
    assert by_height == {138: 0, 188: 1, 238: 2, 288: 3}


def test_variant_summary_carries_frames_per_bin_and_total():
    """Plan summary should expose frames_per_bin and total_frames_required so
    UI and exports can show the base-vs-frame procurement breakdown."""
    # 6 small SKUs into 1/6_3x2-188 (locations_per_bin=6, frames_per_bin=1).
    rows = [
        _row(f"S{i}", 100, 100, 60, 0.5, stock_vol_L=2) for i in range(6)
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(abc_classes=(), only_machine=False,
                           mode="manual",
                           manual_variant_codes=("1/6_3x2-188",))
    plan = cp.plan_containers(cap, None, params)
    assert len(plan.summaries) == 1
    s = plan.summaries[0]
    assert s.frames_per_bin == 1
    assert s.bins_required == 1
    assert s.total_frames_required == 1  # 1 bin × 1 frame


def test_container_plan_aggregates_total_frames_across_variants():
    """ContainerPlan.total_frames sums frames over every variant in the plan."""
    # Mix small + medium SKUs over a manual catalog of two height tiers.
    rows = [
        _row("A1", 100, 100, 60, 0.4, 2),    # fits 138 or higher
        _row("A2", 100, 100, 60, 0.4, 2),
        _row("B1", 200, 150, 200, 1.0, 8),   # needs height >= 200, fits 238/288
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(
        abc_classes=(), only_machine=False,
        mode="manual",
        # Force two distinct height tiers: 138 (0 frames) and 238 (2 frames).
        manual_variant_codes=("1/6_3x2-138", "1/1-238"),
    )
    plan = cp.plan_containers(cap, None, params)
    # Expect total_frames = sum over selected variants of bins × frames_per_bin.
    expected = sum(s.bins_required * s.frames_per_bin for s in plan.summaries)
    assert plan.total_frames == expected
    # And at least one variant must contribute frames (the 238-mm tier).
    assert plan.total_frames > 0


def test_sixth_footprint_has_proportional_weight():
    sixth = next(v for v in cp.CATALOG_FULL if v.footprint_key == "1/6_3x2" and v.bin_height_mm == 138)
    # 206×204 / (617×408) ≈ 0.1669 → ~5.84 kg per cell.
    assert 5.5 < sixth.max_weight_kg_per_cell < 6.0


# ---------------------------------------------------------------------------
# Fitting + locations
# ---------------------------------------------------------------------------


def _row(sku: str, length: float, width: float, height: float, weight: float,
         stock_vol_L: float, fit_status: str = "FIT") -> dict:
    return {
        "sku": sku,
        "carrier_id": cp.MIB_CARRIER_ID,
        "fit_status": fit_status,
        "length_mm": length, "width_mm": width, "height_mm": height,
        "weight_kg": weight, "stored_volume_L": stock_vol_L,
    }


def test_small_sku_fits_smallest_variants():
    v_24 = next(v for v in cp.CATALOG_FULL if v.footprint_key == "1/24" and v.bin_height_mm == 138)
    # Tiny SKU 50×50×80 mm, 0.1 kg.
    assert cp._sku_fits_variant(50, 50, 80, 0.1, v_24)


def test_oversized_sku_orphans():
    # SKU larger than the full bin interior.
    big_row = _row("BIG-1", length=700, width=500, height=200, weight=2, stock_vol_L=10)
    cap = {"rows": [big_row], "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    plan = cp.plan_containers(cap, None, cp.PlanParams(abc_classes=(), only_machine=False))
    assert plan.total_sku_planned == 1
    assert plan.total_sku_covered == 0
    assert len(plan.orphans) == 1
    assert plan.orphans[0].variant_code is None


def test_sku_rotation_allowed():
    """An SKU that doesn't fit in (L,W) orientation should still fit if rotated 90°."""
    v_quarter = next(v for v in cp.CATALOG_FULL if v.footprint_key == "1/4" and v.bin_height_mm == 188)
    # Cell is 309×204×178. SKU 200×280×100 fits only after rotation.
    assert cp._sku_fits_variant(200, 280, 100, 1.0, v_quarter)


def test_weight_overrun_blocks_fit():
    v_sixth = next(v for v in cp.CATALOG_FULL if v.footprint_key == "1/6_3x2" and v.bin_height_mm == 138)
    # Cell cap is ~5.8 kg; 8 kg should NOT fit even with small dimensions.
    assert not cp._sku_fits_variant(50, 50, 50, 8.0, v_sixth)


def test_locations_needed_rounds_up_and_respects_fill_rate():
    v_full = next(v for v in cp.CATALOG_FULL if v.footprint_key == "1/1" and v.bin_height_mm == 138)
    # Cell vol ≈ 32.2 L, fill_rate 0.5 → effective ≈ 16.1 L per loc → 100 L stock → 7 locs.
    n = cp._locations_needed(stock_vol_L=100, v=v_full, fill_rate=0.5,
                              min_loc=1, max_loc=50000)
    assert n == math.ceil(100 / (v_full.cell_volume_L * 0.5))


def test_locations_needed_returns_zero_when_demand_exceeds_max_loc():
    """A tight per-SKU cap should make the SKU not fit this variant at all."""
    v_24 = next(v for v in cp.CATALOG_FULL if v.footprint_key == "1/24" and v.bin_height_mm == 138)
    # cell_volume_L ≈ 1.34 L. 100 L of stock at fill 0.9 needs ~83 locations.
    # With max_loc=10, the variant must report it cannot hold the stock.
    n = cp._locations_needed(stock_vol_L=100, v=v_24, fill_rate=0.9,
                              min_loc=1, max_loc=10)
    assert n == 0


def test_locations_needed_keeps_variant_when_within_max_loc():
    v_full = next(v for v in cp.CATALOG_FULL if v.footprint_key == "1/1" and v.bin_height_mm == 138)
    # 100 L of stock easily fits in <=5 of the 32.2 L cells.
    n = cp._locations_needed(stock_vol_L=100, v=v_full, fill_rate=0.9,
                              min_loc=1, max_loc=10)
    assert 0 < n <= 10


def test_max_locations_per_sku_orphans_when_no_variant_fits_under_cap():
    """SKU stock so large that even the biggest variant exceeds max_loc → orphan."""
    # 1000 L of stock; even 1/1-288 cell (~245 L) needs ~5 locations at fill 0.9.
    # With max_loc=2, every variant should fail and the SKU becomes an orphan.
    rows = [_row("BIG-STOCK", 200, 150, 100, 1.0, stock_vol_L=1000)]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(abc_classes=(), only_machine=False,
                           max_locations_per_sku=2)
    plan = cp.plan_containers(cap, None, params)
    assert plan.total_sku_planned == 1
    assert plan.total_sku_covered == 0
    assert len(plan.orphans) == 1


def test_max_locations_per_sku_picks_larger_variant_when_smaller_one_exceeds_cap():
    """Smaller variant needs too many locations under cap, larger one fits → use larger."""
    # 50 L of stock. 1/24-138 cell ≈ 1.34 L → needs ~42 locs at fill 0.9.
    # 1/1-138 cell ≈ 32.2 L → needs ~2 locs. With max_loc=5, only 1/1 qualifies.
    rows = [_row("MID-STOCK", 200, 150, 80, 1.0, stock_vol_L=50)]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(abc_classes=(), only_machine=False,
                           mode="manual",
                           manual_variant_codes=("1/24-138", "1/1-138"),
                           max_locations_per_sku=5)
    plan = cp.plan_containers(cap, None, params)
    assert plan.total_sku_covered == 1
    assigned = next(a for a in plan.assignments if a.variant_code is not None)
    assert assigned.variant_code == "1/1-138"
    assert assigned.locations <= 5


def _row_no_dims(sku: str, stock_vol_L: float = 1.0) -> dict:
    """Row with missing/zero dimensions and weight — the scenario we are fixing."""
    return {
        "sku": sku,
        "carrier_id": cp.MIB_CARRIER_ID,
        "fit_status": "FIT",
        "length_mm": 0, "width_mm": 0, "height_mm": 0,
        "weight_kg": 0, "stored_volume_L": stock_vol_L,
    }


def test_imputation_off_orphans_sku_with_missing_dimensions():
    """With imputation disabled, a zero-dim SKU is orphaned with a clear reason —
    even if there are perfectly fine SKUs alongside it in the dataset."""
    rows = [
        _row("good", 100, 80, 80, 0.3, 4),
        _row_no_dims("blank"),
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(abc_classes=(), only_machine=False,
                           impute_missing_dimensions=False)
    plan = cp.plan_containers(cap, None, params)
    orphan = next(a for a in plan.assignments if a.sku == "blank")
    assert orphan.variant_code is None
    assert orphan.orphan_reason == "missing_dimensions"
    assigned = next(a for a in plan.assignments if a.sku == "good")
    assert assigned.variant_code is not None


def test_imputation_on_uses_dataset_median_for_missing_dimensions():
    """With imputation enabled, a zero-dim SKU is filled with median values
    from the rest of the dataset and matched against the catalog."""
    rows = [
        _row("a", 100, 80, 80, 0.3, 4),
        _row("b", 120, 90, 100, 0.4, 5),
        _row("c", 110, 85, 90, 0.35, 4.5),
        _row_no_dims("blank", stock_vol_L=4),
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(abc_classes=(), only_machine=False,
                           impute_missing_dimensions=True)
    plan = cp.plan_containers(cap, None, params)
    blank = next(a for a in plan.assignments if a.sku == "blank")
    assert blank.variant_code is not None, "imputed SKU should be assigned"
    assert blank.dimensions_imputed is True
    assert blank.orphan_reason is None
    # Imputed values should be the median of the other three rows (110, 85, 90).
    assert blank.length_mm == 110
    assert blank.width_mm == 85
    assert blank.height_mm == 90


def test_imputation_on_orphans_when_no_dataset_median_available():
    """If ALL rows have missing dimensions, there's no median to impute from.
    The SKU should still end up as an orphan rather than silently fit anything."""
    rows = [_row_no_dims("only-blank")]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(abc_classes=(), only_machine=False,
                           impute_missing_dimensions=True)
    plan = cp.plan_containers(cap, None, params)
    blank = plan.assignments[0]
    assert blank.variant_code is None
    assert blank.orphan_reason == "missing_dimensions"


def test_pcs_per_location_matches_stock_divided_by_locations():
    """For an assigned SKU, pcs_per_location must be ceil(stock_qty / locations),
    where stock_qty = stock_volume_L / unit_volume_L. Orphans stay at 0."""
    import math
    rows = [{
        "sku": "ABC",
        "carrier_id": cp.MIB_CARRIER_ID,
        "fit_status": "FIT",
        "length_mm": 80, "width_mm": 60, "height_mm": 40, "weight_kg": 0.3,
        "stored_volume_L": 300.0,  # 1562.5 pcs of 0.192 L each
    }]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    plan = cp.plan_containers(
        cap, None, cp.PlanParams(abc_classes=(), only_machine=False),
    )
    a = plan.assignments[0]
    assert a.variant_code is not None
    unit_vol_L = a.length_mm * a.width_mm * a.height_mm / 1_000_000
    expected_stock_qty = a.stock_volume_L / unit_vol_L
    expected_pcs_per_loc = math.ceil(expected_stock_qty / a.locations)
    assert a.pcs_per_location == expected_pcs_per_loc
    # Capacity (pcs/loc × locations) must be enough to hold the stock.
    assert a.pcs_per_location * a.locations >= expected_stock_qty


def test_pcs_per_location_is_zero_for_orphans():
    """Orphans (no fitting variant or missing dims) report pcs_per_location = 0
    so the UI can render '—' instead of a misleading number."""
    rows = [_row_no_dims("blank-sku")]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    plan = cp.plan_containers(
        cap, None,
        cp.PlanParams(abc_classes=(), only_machine=False,
                      impute_missing_dimensions=False),
    )
    blank = plan.assignments[0]
    assert blank.variant_code is None
    assert blank.pcs_per_location == 0


def test_dataset_medians_helper_skips_zero_values():
    """Direct unit test of the median helper — zeros must NOT skew the median."""
    rows = [
        {"length_mm": 100, "width_mm": 50, "height_mm": 20, "weight_kg": 0.5},
        {"length_mm": 200, "width_mm": 60, "height_mm": 30, "weight_kg": 0.6},
        {"length_mm": 300, "width_mm": 70, "height_mm": 40, "weight_kg": 0.7},
        # Zero row — should be filtered out:
        {"length_mm": 0, "width_mm": 0, "height_mm": 0, "weight_kg": 0},
    ]
    medians = cp._dataset_medians(rows)
    assert medians["length_mm"] == 200
    assert medians["width_mm"] == 60
    assert medians["height_mm"] == 30
    assert medians["weight_kg"] == 0.6


def test_fill_pct_never_exceeds_100():
    """Once the max-loc cap orphans overstuffed SKUs, fill_pct on every assigned SKU
    must be a sane <=100 number — there should be no 'overstuffed' reports left."""
    rows = [
        _row(f"s{i}", 80 + (i % 5) * 30, 60 + (i % 4) * 30, 80, 0.3, stock_vol_L=20 + i)
        for i in range(40)
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    plan = cp.plan_containers(cap, None,
                              cp.PlanParams(abc_classes=(), only_machine=False,
                                            max_locations_per_sku=3))
    for a in plan.assignments:
        if a.variant_code is not None:
            assert 0.0 <= a.cell_fill_pct <= 100.0, (
                f"SKU {a.sku} reports impossible fill_pct={a.cell_fill_pct}"
            )


# ---------------------------------------------------------------------------
# Bin-total weight enforcement (stacking)
# ---------------------------------------------------------------------------


def test_locations_needed_bumps_when_stacking_exceeds_weight_cap():
    """Lightweight units that would volumetrically fill a cell to a weight
    above max_weight_kg_per_cell must trigger additional locations so the
    per-cell load (and therefore the per-bin load) stays under cap."""
    v_quarter = next(v for v in cp.CATALOG_FULL
                     if v.footprint_key == "1/4" and v.bin_height_mm == 138)
    # Unit 100×80×80 mm = 0.64 L, 1.0 kg. 100 units → 64 L total stock, 100 kg total.
    # Cell ≈ 8.07 L, cell cap ≈ 8.76 kg.
    # Volume-only: ceil(64 / (8.07 × 0.9)) ≈ 9 locs.
    # Weight stacking: ceil(100 / 8.76) ≈ 12 locs → expect at least 12.
    unit_vol_L = (100 * 80 * 80) / 1_000_000.0
    n = cp._locations_needed(
        stock_vol_L=64.0, v=v_quarter, fill_rate=0.9,
        min_loc=1, max_loc=50000,
        unit_vol_L=unit_vol_L, unit_weight_kg=1.0,
    )
    n_vol_only = cp._locations_needed(
        stock_vol_L=64.0, v=v_quarter, fill_rate=0.9,
        min_loc=1, max_loc=50000,
    )
    assert n > n_vol_only, "weight stacking must add locations beyond volume math"
    # Total per-cell weight after the bump must respect the cap.
    weight_per_cell = 100.0 / n
    assert weight_per_cell <= v_quarter.max_weight_kg_per_cell + 1e-9


def test_locations_needed_unchanged_when_weight_within_cap():
    """When stacking weight is well below the cell cap, location count must
    match the volume-only formula (no regression on the common case)."""
    v_full = next(v for v in cp.CATALOG_FULL
                  if v.footprint_key == "1/1" and v.bin_height_mm == 138)
    unit_vol_L = (100 * 100 * 100) / 1_000_000.0  # 1 L per unit
    n_weighted = cp._locations_needed(
        stock_vol_L=100.0, v=v_full, fill_rate=0.5,
        min_loc=1, max_loc=50000,
        unit_vol_L=unit_vol_L, unit_weight_kg=0.1,  # very light
    )
    n_vol_only = cp._locations_needed(
        stock_vol_L=100.0, v=v_full, fill_rate=0.5,
        min_loc=1, max_loc=50000,
    )
    assert n_weighted == n_vol_only


def test_plan_bin_total_weight_stays_under_cap():
    """End-to-end: after planning, total_weight_kg / bins_required ≤ 35 for
    every variant in the summary — bin weight cap respected."""
    # Mix of SKUs, some heavy enough to push per-cell weight close to cap.
    rows = [
        _row(f"s{i}", 100, 80, 80, 1.0, stock_vol_L=10 + i) for i in range(20)
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    plan = cp.plan_containers(
        cap, None,
        cp.PlanParams(abc_classes=(), only_machine=False),
    )
    for s in plan.summaries:
        avg_bin_weight = s.total_weight_kg / s.bins_required if s.bins_required else 0
        assert avg_bin_weight <= cp.BIN_MAX_WEIGHT_KG + 1e-6, (
            f"variant {s.code} avg bin weight {avg_bin_weight:.2f} exceeds "
            f"{cp.BIN_MAX_WEIGHT_KG} kg cap"
        )


# ---------------------------------------------------------------------------
# Dividers column
# ---------------------------------------------------------------------------


def test_variant_summary_dividers_required_equals_bins_times_locations():
    """dividers_required is the procurement value the user orders — must equal
    bins × locations_per_bin for every variant in the plan."""
    rows = [_row(f"s{i}", 100, 80, 80, 0.3, stock_vol_L=3) for i in range(12)]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    plan = cp.plan_containers(
        cap, None,
        cp.PlanParams(abc_classes=(), only_machine=False),
    )
    assert plan.summaries, "plan must produce at least one variant"
    for s in plan.summaries:
        assert s.dividers_required == s.bins_required * s.locations_per_bin


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_abc_filter_keeps_only_selected_classes():
    rows = [_row("A1", 50, 50, 50, 0.1, 1), _row("C1", 50, 50, 50, 0.1, 1)]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    perf = {"sku_pareto": [
        {"sku": "A1", "abc_class": "A", "recommendation": "Machine"},
        {"sku": "C1", "abc_class": "C", "recommendation": "Machine"},
    ]}
    plan = cp.plan_containers(cap, perf,
                              cp.PlanParams(abc_classes=("A",), only_machine=True))
    skus = {a.sku for a in plan.assignments}
    assert skus == {"A1"}


def test_only_machine_filter_drops_non_machine():
    rows = [_row("M1", 50, 50, 50, 0.1, 1), _row("N1", 50, 50, 50, 0.1, 1)]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    perf = {"sku_pareto": [
        {"sku": "M1", "abc_class": "A", "recommendation": "Machine"},
        {"sku": "N1", "abc_class": "A", "recommendation": "Non-machine"},
    ]}
    plan = cp.plan_containers(cap, perf, cp.PlanParams(abc_classes=("A",), only_machine=True))
    assert {a.sku for a in plan.assignments} == {"M1"}


def test_strict_filtering_excludes_skus_without_perf_metadata_when_filter_specific():
    """When Performance was run (some SKUs have ``sku_pareto`` entries) and the
    user selected a specific ABC subset OR ``only_machine``, SKUs missing from
    the perf data are EXCLUDED — they cannot be assumed to satisfy the filter.

    Avoids the UI confusion where a SKU shows up in results with "—" in the
    ABC/Recom. columns even though the user opted into a strict filter."""
    rows = [
        _row("known-C-machine", 50, 50, 50, 0.1, 1),
        _row("known-A-machine", 50, 50, 50, 0.1, 1),
        _row("unknown", 50, 50, 50, 0.1, 1),
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    perf = {"sku_pareto": [
        {"sku": "known-C-machine", "abc_class": "C", "recommendation": "Machine"},
        {"sku": "known-A-machine", "abc_class": "A", "recommendation": "Machine"},
        # "unknown" intentionally missing from sku_pareto
    ]}
    plan = cp.plan_containers(cap, perf,
                              cp.PlanParams(abc_classes=("C",), only_machine=True))
    skus = {a.sku for a in plan.assignments}
    # Only the C+Machine SKU survives. A is excluded by ABC, unknown by both.
    assert skus == {"known-C-machine"}


def test_no_performance_data_skips_abc_filter():
    rows = [_row("S1", 50, 50, 50, 0.1, 1)]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    # When perf is None, ABC/recommendation filters are ignored (SKU is unknown to perf).
    plan = cp.plan_containers(cap, None, cp.PlanParams(abc_classes=("A",), only_machine=True))
    assert plan.total_sku_planned == 1


def test_carrier_filter_skips_non_mib_rows():
    rows = [
        _row("X", 50, 50, 50, 0.1, 1),  # MiB row
        {**_row("Y", 50, 50, 50, 0.1, 1), "carrier_id": "99"},  # different carrier
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID, "99"]}
    plan = cp.plan_containers(cap, None,
                              cp.PlanParams(abc_classes=(), only_machine=False))
    assert {a.sku for a in plan.assignments} == {"X"}


# ---------------------------------------------------------------------------
# Set cover / mode selection
# ---------------------------------------------------------------------------


def test_auto_mode_picks_at_most_k_variants():
    rows = [
        _row("s1", 100, 80, 100, 0.5, 5),
        _row("s2", 250, 180, 150, 1.5, 8),
        _row("s3", 580, 380, 80, 12, 20),
        _row("s4", 60, 50, 80, 0.2, 2),
        _row("s5", 300, 200, 200, 4, 12),
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(abc_classes=(), only_machine=False, mode="auto",
                           auto_max_variants=2)
    plan = cp.plan_containers(cap, None, params)
    assert len(plan.summaries) <= 2


def test_manual_mode_uses_only_supplied_codes():
    rows = [_row("s1", 100, 80, 60, 0.3, 4)]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    # Pick a single very-large variant that surely fits the small SKU.
    params = cp.PlanParams(abc_classes=(), only_machine=False, mode="manual",
                           manual_variant_codes=("1/1-138",))
    plan = cp.plan_containers(cap, None, params)
    assert plan.selected_variant_codes == ["1/1-138"]


def test_guided_simple_preset_uses_only_3_footprints():
    rows = [
        _row(f"s{i}", 100, 80, 80, 0.3, 4) for i in range(20)
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(abc_classes=(), only_machine=False, mode="guided",
                           guided_preset="simple")
    plan = cp.plan_containers(cap, None, params)
    selected = {v.split("-")[0] for v in plan.selected_variant_codes}
    assert selected <= {"1/1", "1/4", "1/6_3x2"}


# ---------------------------------------------------------------------------
# Plan integrity
# ---------------------------------------------------------------------------


def test_six_small_skus_share_one_six_cell_bin():
    """6 small SKUs assigned to a 6-cell variant, each needing 1 location,
    should consolidate into ONE physical bin (ceil(6 / 6) = 1).

    Confirms that ``bins_required`` is computed from the *sum* of locations
    per variant (so multiple SKUs share cells within the same bin), not from
    per-SKU bin counts that would naively round up to 1 each → 6 bins."""
    rows = [
        # Small SKUs that easily fit in a 1/6_3x2 cell (206×204×128 mm ≈ 5.4 L).
        # Stock 2 L each → 1 location at fill 0.9.
        _row(f"S{i}", 100, 100, 60, 0.5, stock_vol_L=2) for i in range(6)
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(abc_classes=(), only_machine=False,
                           mode="manual",
                           manual_variant_codes=("1/6_3x2-138",))
    plan = cp.plan_containers(cap, None, params)
    assert plan.total_sku_covered == 6
    assert len(plan.summaries) == 1
    s = plan.summaries[0]
    assert s.locations_per_bin == 6
    assert s.total_locations == 6   # 1 location per SKU
    assert s.bins_required == 1     # ceil(6 / 6) = 1
    assert plan.total_bins == 1


def test_plan_summary_bins_match_sum_of_per_variant_bins():
    rows = [
        _row(f"s{i}", 90 + i, 70 + i, 80, 0.4, 5 + i * 0.2) for i in range(60)
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    plan = cp.plan_containers(cap, None,
                              cp.PlanParams(abc_classes=(), only_machine=False))
    assert plan.total_bins == sum(s.bins_required for s in plan.summaries)
    assert plan.total_sku_planned == 60
    assert plan.total_sku_covered + len(plan.orphans) == plan.total_sku_planned


def test_coverage_target_for_full_coverage_preset():
    rows = [
        _row(f"s{i}", 80 + (i % 5) * 30, 60 + (i % 4) * 30, 80 + (i % 3) * 20, 0.3, 4)
        for i in range(100)
    ]
    cap = {"rows": rows, "carriers_analyzed": [cp.MIB_CARRIER_ID]}
    params = cp.PlanParams(abc_classes=(), only_machine=False, mode="guided",
                           guided_preset="full_coverage")
    plan = cp.plan_containers(cap, None, params)
    assert plan.coverage_pct >= 99.0
