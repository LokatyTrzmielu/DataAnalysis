"""Container Order Planner — assigns SKUs from a completed analysis to Kardex VBM Box
variants and computes how many physical bins of each variant to order.

Data sources (read-only):
- capacity_result.rows  — per-SKU × carrier fit data (uses MiB 640x440 carrier "2")
- performance_result.sku_pareto  — per-SKU ABC class + Machine/Non-machine recommendation

Catalog source: Kardex VBM Box flyer (Dev/Calculators/Flyer_PL_Kardex-VBM-Box.pdf).
Base bin 640x440x138 mm, usable interior ~617x408 mm, dividers up to 288 mm height.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Literal


# Carrier ID for MiB 640x440 (the only bin supported by VBM Box) — from carriers.yml.
MIB_CARRIER_ID = "2"

# Bin base limits (from PDF).
BIN_MAX_WEIGHT_KG = 35.0
BIN_INTERIOR_LENGTH_MM = 617
BIN_INTERIOR_WIDTH_MM = 408
USABLE_AREA_MM2 = BIN_INTERIOR_LENGTH_MM * BIN_INTERIOR_WIDTH_MM

# Height tiers — dividers only work up to 288 mm.
HEIGHT_TIERS_MM = (138, 188, 238, 288)
# Subtract ~10 mm for bin floor to get usable interior height per cell.
HEIGHT_FLOOR_LOSS_MM = 10

# Footprint definitions: (code, label, length_mm, width_mm, locations_per_bin, in_auto_catalog)
# Lengths/widths chosen from PDF modularity (103/102 mm units).
FOOTPRINTS: tuple[tuple[str, str, int, int, int, bool], ...] = (
    ("1/1",      "1 cell (full bin)",       617, 408,  1, True),
    ("1/2L",     "2 cells (split length)",  309, 408,  2, True),
    ("1/2W",     "2 cells (split width)",   617, 204,  2, True),
    ("1/3W",     "3 cells (3× width)",      617, 136,  3, True),
    ("1/3L",     "3 cells (3× length)",     206, 408,  3, False),
    ("1/4",      "4 cells (2×2)",           309, 204,  4, True),
    ("1/6_3x2",  "6 cells (3L×2W)",         206, 204,  6, True),
    ("1/6_2x3",  "6 cells (2L×3W)",         309, 136,  6, False),
    ("1/8",      "8 cells (4L×2W)",         309, 102,  8, False),
    ("1/12_3x4", "12 cells (3L×4W)",        206, 102, 12, True),
    ("1/12_6x2", "12 cells (6L×2W)",        103, 204, 12, False),
    ("1/24",     "24 cells (6L×4W)",        103, 102, 24, False),
)


@dataclass(frozen=True)
class Variant:
    """One container variant = (footprint × height tier).

    `cell_*_mm` are the inside dimensions of a single cell after dividers.
    `locations_per_bin` is how many cells one physical bin provides.
    `max_weight_kg_per_cell` is the proportional weight cap (bin cap / cells).
    """

    code: str  # e.g. "1/4-188" — used as variant_id everywhere
    footprint_key: str  # e.g. "1/4"
    footprint_label: str
    cell_length_mm: int
    cell_width_mm: int
    cell_height_mm: int  # usable interior height of one cell
    bin_height_mm: int  # external bin tier (138/188/238/288)
    locations_per_bin: int
    max_weight_kg_per_cell: float
    cell_volume_L: float
    in_auto_catalog: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _build_catalog() -> list[Variant]:
    """Generate the full 48-variant catalog from FOOTPRINTS × HEIGHT_TIERS_MM."""
    variants: list[Variant] = []
    for fp_key, fp_label, fp_len, fp_wid, locs, in_auto in FOOTPRINTS:
        cell_area_mm2 = fp_len * fp_wid
        # Proportional weight cap: cell occupies (cells_used / 1) of bin area.
        # Equivalent: per-cell cap = total cap × (cell_area / usable_area).
        weight_per_cell = BIN_MAX_WEIGHT_KG * (cell_area_mm2 / USABLE_AREA_MM2)
        for tier in HEIGHT_TIERS_MM:
            cell_h = tier - HEIGHT_FLOOR_LOSS_MM
            cell_vol_L = (fp_len * fp_wid * cell_h) / 1_000_000.0  # mm³ → L
            variants.append(Variant(
                code=f"{fp_key}-{tier}",
                footprint_key=fp_key,
                footprint_label=fp_label,
                cell_length_mm=fp_len,
                cell_width_mm=fp_wid,
                cell_height_mm=cell_h,
                bin_height_mm=tier,
                locations_per_bin=locs,
                max_weight_kg_per_cell=round(weight_per_cell, 3),
                cell_volume_L=round(cell_vol_L, 3),
                in_auto_catalog=in_auto,
            ))
    return variants


CATALOG_FULL: list[Variant] = _build_catalog()
CATALOG_AUTO: list[Variant] = [v for v in CATALOG_FULL if v.in_auto_catalog]


# ---------------------------------------------------------------------------
# Parameters and result structures
# ---------------------------------------------------------------------------

Mode = Literal["auto", "guided", "manual"]
Goal = Literal["min_waste", "min_bins", "max_coverage"]
GuidedPreset = Literal["simple", "standard", "full_coverage"]


@dataclass
class PlanParams:
    """User-controlled parameters for a planning run."""

    # SKU filters (post-load)
    abc_classes: tuple[str, ...] = ("A", "B")  # subset of ("A","B","C"); empty = all
    only_machine: bool = True
    include_borderline: bool = True  # treat BORDERLINE same as FIT

    # Volumetric knobs
    stock_multiplier: float = 1.0  # 0.5..3.0
    location_fill_rate: float = 0.9  # 0.5..1.0
    min_locations_per_sku: int = 1
    max_locations_per_sku: int = 50000

    # Mode-specific
    mode: Mode = "auto"
    auto_max_variants: int = 6
    auto_goal: Goal = "min_waste"
    guided_preset: GuidedPreset = "standard"
    manual_variant_codes: tuple[str, ...] = ()  # codes from CATALOG_FULL

    def __post_init__(self) -> None:
        self.stock_multiplier = max(0.1, float(self.stock_multiplier))
        self.location_fill_rate = max(0.05, min(1.0, float(self.location_fill_rate)))
        self.min_locations_per_sku = max(1, int(self.min_locations_per_sku))
        self.max_locations_per_sku = max(self.min_locations_per_sku, int(self.max_locations_per_sku))
        self.auto_max_variants = max(1, min(48, int(self.auto_max_variants)))


@dataclass
class Assignment:
    sku: str
    variant_code: str | None  # None ⇒ orphan
    locations: int
    bins: int  # bins this SKU contributes (rounded up per-variant later)
    cell_fill_pct: float  # 0..100 — how full each location is
    abc_class: str | None
    recommendation: str | None
    length_mm: float
    width_mm: float
    height_mm: float
    weight_kg: float
    stock_volume_L: float


@dataclass
class VariantSummary:
    code: str
    footprint_key: str
    footprint_label: str
    bin_height_mm: int
    cell_length_mm: int
    cell_width_mm: int
    cell_height_mm: int
    locations_per_bin: int
    sku_count: int
    total_locations: int
    bins_required: int
    avg_fill_pct: float


@dataclass
class ContainerPlan:
    assignments: list[Assignment]
    summaries: list[VariantSummary]
    orphans: list[Assignment]  # subset of assignments where variant_code is None
    total_bins: int
    total_sku_planned: int
    total_sku_covered: int
    coverage_pct: float
    avg_fill_pct: float
    selected_variant_codes: list[str]
    params_echo: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------


def _sku_fits_variant(length: float, width: float, height: float, weight: float, v: Variant) -> bool:
    """Geometric + weight check. Try both orientations (rotate 90° in horizontal plane)."""
    if height > v.cell_height_mm:
        return False
    if weight > v.max_weight_kg_per_cell:
        return False
    fits_a = length <= v.cell_length_mm and width <= v.cell_width_mm
    fits_b = width <= v.cell_length_mm and length <= v.cell_width_mm
    return fits_a or fits_b


def _locations_needed(stock_vol_L: float, v: Variant, fill_rate: float,
                      min_loc: int, max_loc: int) -> int:
    if v.cell_volume_L <= 0:
        return min_loc
    raw = stock_vol_L / (v.cell_volume_L * fill_rate)
    n = max(min_loc, math.ceil(raw))
    return min(n, max_loc)


def _select_capacity_rows(capacity_result: dict | None) -> list[dict]:
    """Pick only MiB-carrier rows. Prefer FIT/BORDERLINE; keep NOT_FIT so caller can
    decide whether to drop them. Filtering happens later in plan_containers."""
    if not capacity_result or "rows" not in capacity_result:
        return []
    rows = [r for r in capacity_result["rows"] if r.get("carrier_id") == MIB_CARRIER_ID]
    return rows


def _abc_map(performance_result: dict | None) -> dict[str, dict]:
    """sku → {abc_class, recommendation, frequency_rank} from sku_pareto."""
    if not performance_result or "sku_pareto" not in performance_result:
        return {}
    return {
        r["sku"]: {
            "abc_class": r.get("abc_class"),
            "recommendation": r.get("recommendation"),
            "frequency_rank": r.get("frequency_rank"),
        }
        for r in performance_result["sku_pareto"]
        if r.get("sku")
    }


def _filter_skus(rows: list[dict], abc: dict[str, dict], params: PlanParams) -> list[dict]:
    """Apply ABC, recommendation, fit-status filters. Returns surviving rows."""
    allowed_fit = {"FIT", "BORDERLINE"} if params.include_borderline else {"FIT"}
    abc_set = set(params.abc_classes) if params.abc_classes else None
    out: list[dict] = []
    for row in rows:
        if row.get("fit_status") not in allowed_fit:
            continue
        meta = abc.get(row["sku"])
        if abc_set is not None and meta is not None:
            if meta.get("abc_class") not in abc_set:
                continue
        if params.only_machine and meta is not None:
            if meta.get("recommendation") != "Machine":
                continue
        out.append(row)
    return out


def _eligible_catalog(params: PlanParams) -> list[Variant]:
    """Catalog filtered by mode (auto = 7 footprints, manual = user-picked codes,
    guided = preset-derived)."""
    if params.mode == "manual":
        if params.manual_variant_codes:
            codes = set(params.manual_variant_codes)
            return [v for v in CATALOG_FULL if v.code in codes]
        return list(CATALOG_FULL)
    if params.mode == "guided":
        return _guided_catalog(params.guided_preset)
    return list(CATALOG_AUTO)


def _guided_catalog(preset: GuidedPreset) -> list[Variant]:
    if preset == "simple":
        keep = {"1/1", "1/4", "1/6_3x2"}
        keep_heights = {188, 288}
        return [v for v in CATALOG_FULL if v.footprint_key in keep and v.bin_height_mm in keep_heights]
    # "standard" and "full_coverage" use the auto catalog (algorithm later picks K).
    return list(CATALOG_AUTO)


@dataclass
class _SkuFit:
    sku: str
    row: dict
    abc_class: str | None
    recommendation: str | None
    candidates: dict[str, tuple[int, float]]  # variant_code → (locations, fill_pct)


def _compute_fits(rows: list[dict], abc: dict[str, dict], catalog: list[Variant],
                  params: PlanParams) -> list[_SkuFit]:
    fits: list[_SkuFit] = []
    for row in rows:
        sku = row["sku"]
        length = float(row.get("length_mm") or 0)
        width = float(row.get("width_mm") or 0)
        height = float(row.get("height_mm") or 0)
        weight = float(row.get("weight_kg") or 0)
        stock_vol_L = float(row.get("stored_volume_L") or 0) * params.stock_multiplier

        candidates: dict[str, tuple[int, float]] = {}
        for v in catalog:
            if not _sku_fits_variant(length, width, height, weight, v):
                continue
            locs = _locations_needed(
                stock_vol_L, v, params.location_fill_rate,
                params.min_locations_per_sku, params.max_locations_per_sku,
            )
            if locs <= 0:
                continue
            used_vol = stock_vol_L
            total_cell_vol = locs * v.cell_volume_L
            fill_pct = (used_vol / total_cell_vol * 100) if total_cell_vol > 0 else 0.0
            candidates[v.code] = (locs, round(fill_pct, 2))

        meta = abc.get(sku) or {}
        fits.append(_SkuFit(
            sku=sku, row=row,
            abc_class=meta.get("abc_class"),
            recommendation=meta.get("recommendation"),
            candidates=candidates,
        ))
    return fits


def _best_variant_for_sku(fit: _SkuFit, allowed: set[str], by_variant: dict[str, Variant],
                          goal: Goal) -> str | None:
    """Among `allowed` variants that this SKU fits, return the best one per goal."""
    options = [c for c in fit.candidates if c in allowed]
    if not options:
        return None
    if goal == "min_bins":
        # Smallest number of bins (locations / locations_per_bin, ceil).
        def cost(c: str) -> tuple[int, float]:
            locs = fit.candidates[c][0]
            bins = math.ceil(locs / by_variant[c].locations_per_bin)
            return (bins, -fit.candidates[c][1])  # tiebreak: higher fill is better
        return min(options, key=cost)
    if goal == "min_waste":
        # Highest fill % = least waste.
        return max(options, key=lambda c: fit.candidates[c][1])
    # max_coverage: any candidate already implies coverage; pick highest fill for stability.
    return max(options, key=lambda c: fit.candidates[c][1])


def _evaluate_selection(selection: set[str], fits: list[_SkuFit],
                        by_variant: dict[str, Variant], goal: Goal) -> tuple[float, dict]:
    """Score a candidate selection of variants. Lower score = better.

    Returns (score, debug_dict). An orphan SKU counts as full-volume waste / 1 bin
    of penalty so the greedy cannot improve its cost by leaving SKUs uncovered.
    """
    covered = 0
    total_bins = 0
    total_waste_L = 0.0
    orphan_penalty_bins = 0
    orphan_penalty_waste = 0.0
    per_variant_locs: dict[str, int] = {c: 0 for c in selection}

    for f in fits:
        v_code = _best_variant_for_sku(f, selection, by_variant, goal)
        if v_code is None:
            # Orphan — penalise heavily so greedy prefers covering it.
            stock_L = float(f.row.get("stored_volume_L") or 0)
            orphan_penalty_waste += stock_L if stock_L > 0 else 1.0
            orphan_penalty_bins += 1
            continue
        covered += 1
        locs, fill = f.candidates[v_code]
        per_variant_locs[v_code] += locs
        v = by_variant[v_code]
        total_waste_L += max(0.0, (locs * v.cell_volume_L) - (locs * v.cell_volume_L * fill / 100.0))
    for code, locs in per_variant_locs.items():
        if locs > 0:
            total_bins += math.ceil(locs / by_variant[code].locations_per_bin)

    debug = {"covered": covered, "bins": total_bins, "waste_L": total_waste_L}
    if goal == "max_coverage":
        # Negative coverage so lower-is-better; tiebreak on bins, then waste.
        return (-covered, total_bins, total_waste_L), debug  # type: ignore[return-value]
    if goal == "min_bins":
        # Orphans counted as 1 bin each — prevents trivial empty selection winning.
        return (total_bins + orphan_penalty_bins, -covered, total_waste_L), debug  # type: ignore[return-value]
    # min_waste: orphan SKU's full stock counts as waste.
    return (total_waste_L + orphan_penalty_waste, total_bins, -covered), debug  # type: ignore[return-value]


def _greedy_set_cover(fits: list[_SkuFit], catalog: list[Variant], k: int,
                      goal: Goal) -> set[str]:
    """Greedy: start empty, add the variant whose marginal improvement is best, until K."""
    by_variant = {v.code: v for v in catalog}
    candidate_codes = [v.code for v in catalog]
    chosen: set[str] = set()
    for _ in range(min(k, len(candidate_codes))):
        best_code: str | None = None
        best_score = None
        for code in candidate_codes:
            if code in chosen:
                continue
            score, _ = _evaluate_selection(chosen | {code}, fits, by_variant, goal)
            if best_score is None or score < best_score:
                best_score = score
                best_code = code
        if best_code is None:
            break
        chosen.add(best_code)
    return chosen


def _plan_from_selection(selection: set[str], fits: list[_SkuFit],
                         catalog: list[Variant], goal: Goal,
                         params: PlanParams) -> ContainerPlan:
    by_variant = {v.code: v for v in catalog}

    assignments: list[Assignment] = []
    orphans: list[Assignment] = []
    locs_per_variant: dict[str, int] = {c: 0 for c in selection}
    skus_per_variant: dict[str, int] = {c: 0 for c in selection}
    fill_sum_per_variant: dict[str, float] = {c: 0.0 for c in selection}

    for f in fits:
        v_code = _best_variant_for_sku(f, selection, by_variant, goal)
        row = f.row
        stock_L = float(row.get("stored_volume_L") or 0) * params.stock_multiplier
        if v_code is None:
            a = Assignment(
                sku=f.sku, variant_code=None, locations=0, bins=0, cell_fill_pct=0.0,
                abc_class=f.abc_class, recommendation=f.recommendation,
                length_mm=float(row.get("length_mm") or 0),
                width_mm=float(row.get("width_mm") or 0),
                height_mm=float(row.get("height_mm") or 0),
                weight_kg=float(row.get("weight_kg") or 0),
                stock_volume_L=round(stock_L, 3),
            )
            orphans.append(a)
            assignments.append(a)
            continue
        locs, fill = f.candidates[v_code]
        v = by_variant[v_code]
        bins_for_sku = math.ceil(locs / v.locations_per_bin)
        a = Assignment(
            sku=f.sku, variant_code=v_code, locations=locs, bins=bins_for_sku,
            cell_fill_pct=fill, abc_class=f.abc_class, recommendation=f.recommendation,
            length_mm=float(row.get("length_mm") or 0),
            width_mm=float(row.get("width_mm") or 0),
            height_mm=float(row.get("height_mm") or 0),
            weight_kg=float(row.get("weight_kg") or 0),
            stock_volume_L=round(stock_L, 3),
        )
        assignments.append(a)
        locs_per_variant[v_code] += locs
        skus_per_variant[v_code] += 1
        fill_sum_per_variant[v_code] += fill

    summaries: list[VariantSummary] = []
    total_bins = 0
    fill_acc = 0.0
    fill_n = 0
    for code, locs in locs_per_variant.items():
        if locs == 0:
            continue
        v = by_variant[code]
        bins = math.ceil(locs / v.locations_per_bin)
        total_bins += bins
        sku_n = skus_per_variant[code]
        avg_fill = (fill_sum_per_variant[code] / sku_n) if sku_n else 0.0
        fill_acc += fill_sum_per_variant[code]
        fill_n += sku_n
        summaries.append(VariantSummary(
            code=code,
            footprint_key=v.footprint_key,
            footprint_label=v.footprint_label,
            bin_height_mm=v.bin_height_mm,
            cell_length_mm=v.cell_length_mm,
            cell_width_mm=v.cell_width_mm,
            cell_height_mm=v.cell_height_mm,
            locations_per_bin=v.locations_per_bin,
            sku_count=sku_n,
            total_locations=locs,
            bins_required=bins,
            avg_fill_pct=round(avg_fill, 2),
        ))
    # Sort summaries: most bins first.
    summaries.sort(key=lambda s: (-s.bins_required, s.code))

    covered = len([a for a in assignments if a.variant_code is not None])
    planned = len(assignments)
    coverage = (covered / planned * 100) if planned else 0.0
    avg_fill = round(fill_acc / fill_n, 2) if fill_n else 0.0

    return ContainerPlan(
        assignments=assignments,
        summaries=summaries,
        orphans=orphans,
        total_bins=total_bins,
        total_sku_planned=planned,
        total_sku_covered=covered,
        coverage_pct=round(coverage, 2),
        avg_fill_pct=avg_fill,
        selected_variant_codes=[s.code for s in summaries],
        params_echo=asdict(params),
    )


def plan_containers(
    capacity_result: dict | None,
    performance_result: dict | None,
    params: PlanParams,
) -> ContainerPlan:
    """Top-level entry: build a complete ContainerPlan from analysis JSON columns + params."""
    rows = _select_capacity_rows(capacity_result)
    abc = _abc_map(performance_result)
    survivors = _filter_skus(rows, abc, params)
    catalog = _eligible_catalog(params)
    fits = _compute_fits(survivors, abc, catalog, params)

    if params.mode == "manual" and params.manual_variant_codes:
        selection = {c for c in params.manual_variant_codes if any(c == v.code for v in catalog)}
    elif params.mode == "guided" and params.guided_preset == "simple":
        selection = {v.code for v in catalog}  # use everything in simple preset (small set)
    elif params.mode == "guided" and params.guided_preset == "full_coverage":
        # Greedy until coverage stabilises (~99%) or all 28 variants used.
        selection = _greedy_until_coverage(fits, catalog, target_pct=99.0)
    else:
        k = params.auto_max_variants if params.mode == "auto" else 8  # standard preset = 8
        selection = _greedy_set_cover(fits, catalog, k=k, goal=params.auto_goal)

    return _plan_from_selection(selection, fits, catalog, params.auto_goal, params)


def _greedy_until_coverage(fits: list[_SkuFit], catalog: list[Variant],
                            target_pct: float, max_k: int = 28) -> set[str]:
    """Keep adding variants until coverage ≥ target_pct or we hit max_k."""
    by_variant = {v.code: v for v in catalog}
    chosen: set[str] = set()
    total = max(1, len(fits))
    for _ in range(min(max_k, len(catalog))):
        best_code = None
        best_score = None
        for v in catalog:
            if v.code in chosen:
                continue
            score, _ = _evaluate_selection(chosen | {v.code}, fits, by_variant, "max_coverage")
            if best_score is None or score < best_score:
                best_score = score
                best_code = v.code
        if best_code is None:
            break
        chosen.add(best_code)
        # Check coverage now.
        _, dbg = _evaluate_selection(chosen, fits, by_variant, "max_coverage")
        if (dbg["covered"] / total * 100) >= target_pct:
            break
    return chosen
