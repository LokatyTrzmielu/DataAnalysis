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
