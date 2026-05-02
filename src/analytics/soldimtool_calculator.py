"""SolDimTool Dashboard Input calculator."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

import polars as pl

from src.analytics.performance import PerformanceAnalysisResult


@dataclass
class SolDimToolInputs:
    """Calculated inputs for SolDimTool v2.7.3 Dashboard."""

    # Orders/Day — cell C16
    orders_per_day_mean: float
    orders_per_day_median: float
    orders_per_day_p90: float
    orders_per_day_recommended: int
    orders_recommended_basis: str  # "mediana" or "P90 (silna sezonowość)"

    # Orderlines/Order — cell C17
    ol_per_order_mean: float
    ol_per_order_median: float
    ol_per_order_p90: float
    ol_per_order_recommended: float

    # Hours/Day — cell A29
    hours_per_day: int
    time_detected: bool
    window_min_hour: Optional[float]
    window_max_hour: Optional[float]
    window_median: Optional[float]

    # Adjusting View — cell A31
    adjusting_view: str  # "hourly view" | "daily view"

    # System Factor — cell C29 (always default)
    system_factor: float

    # Orders/Batch — cells B21–B25
    max_batch: int
    batch_sizes: list[int]

    # Commonality — cells C21–C25
    sku_available: bool
    base_commonality: Optional[float]
    commonality_values: list[float]

    # Validation warnings
    warnings: list[str] = field(default_factory=list)


class SolDimToolCalculator:
    """Calculates SolDimTool Dashboard input values from PerformanceAnalysisResult."""

    def calculate(self, result: PerformanceAnalysisResult) -> SolDimToolInputs:
        """Calculate all Dashboard inputs from a completed performance analysis.

        Args:
            result: Completed PerformanceAnalysisResult

        Returns:
            SolDimToolInputs with recommended values and warnings
        """
        warnings: list[str] = []

        # 1. Orders/Day (C16)
        daily_orders = [dm.orders for dm in result.daily_metrics]
        orders_mean, orders_median, orders_p90, orders_recommended, orders_basis = (
            self._calc_orders_per_day(daily_orders, warnings)
        )

        # 2. Orderlines/Order (C17)
        ol_mean, ol_median, ol_p90, ol_recommended = self._calc_ol_per_order(
            result.filtered_df, warnings
        )

        # 3. Hours/Day (A29)
        hours_per_day, time_detected, win_min, win_max, win_median = (
            self._calc_hours_per_day(result, warnings)
        )

        # 4. Adjusting View (A31)
        adjusting_view = "hourly view" if hours_per_day <= 8 else "daily view"

        # 5. Orders/Batch (B21–B25)
        max_batch = max(5, min(math.floor(orders_recommended / 4), 100))
        if max_batch <= 5 and orders_recommended < 20:
            warnings.append(
                "Bardzo mała liczba zleceń dziennie — zakres batch size może być niereprezentacyjny."
            )
        batch_sizes = _suggest_batch_sizes(max_batch)

        # 6. Commonality (C21–C25)
        sku_available, base_commonality, commonality_values = self._calc_commonality(
            result.filtered_df, warnings
        )

        return SolDimToolInputs(
            orders_per_day_mean=orders_mean,
            orders_per_day_median=orders_median,
            orders_per_day_p90=orders_p90,
            orders_per_day_recommended=orders_recommended,
            orders_recommended_basis=orders_basis,
            ol_per_order_mean=ol_mean,
            ol_per_order_median=ol_median,
            ol_per_order_p90=ol_p90,
            ol_per_order_recommended=ol_recommended,
            hours_per_day=hours_per_day,
            time_detected=time_detected,
            window_min_hour=win_min,
            window_max_hour=win_max,
            window_median=win_median,
            adjusting_view=adjusting_view,
            system_factor=0.10,
            max_batch=max_batch,
            batch_sizes=batch_sizes,
            sku_available=sku_available,
            base_commonality=base_commonality,
            commonality_values=commonality_values,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calc_orders_per_day(
        self, daily_orders: list[int], warnings: list[str]
    ) -> tuple[float, float, float, int, str]:
        if not daily_orders:
            warnings.append("Brak danych dziennych — nie można obliczyć Orders/Day.")
            return 0.0, 0.0, 0.0, 0, "brak danych"

        sorted_orders = sorted(daily_orders)
        n = len(sorted_orders)
        mean = round(sum(sorted_orders) / n, 1)
        median = round(_percentile(sorted_orders, 50), 1)
        p90 = round(_percentile(sorted_orders, 90), 1)

        if median < 10:
            warnings.append("Bardzo mała liczba zleceń — zweryfikuj zakres dat danych.")

        if median > 0 and p90 / median > 2.0:
            warnings.append(
                "Silna sezonowość (P90/mediana > 2×) — rozważ użycie P90 zamiast mediany dla C16."
            )

        if median > 0 and p90 / median > 1.5:
            return mean, median, p90, int(p90), "P90 (silna sezonowość)"

        return mean, median, p90, int(median), "mediana"

    def _calc_ol_per_order(
        self, df: object, warnings: list[str]
    ) -> tuple[float, float, float, float]:
        if df is None or not isinstance(df, pl.DataFrame) or len(df) == 0:
            warnings.append("Brak danych zleceń — nie można obliczyć Orderlines/Order.")
            return 0.0, 0.0, 0.0, 1.0

        if "order_id" not in df.columns:
            warnings.append("Brak kolumny order_id — nie można obliczyć Orderlines/Order.")
            return 0.0, 0.0, 0.0, 1.0

        per_order = df.group_by("order_id").agg(pl.len().alias("line_count"))
        counts = sorted(per_order["line_count"].to_list())

        if not counts:
            return 0.0, 0.0, 0.0, 1.0

        mean = round(sum(counts) / len(counts), 2)
        median = round(_percentile(counts, 50), 2)
        p90 = round(_percentile(counts, 90), 2)

        if mean > 50:
            warnings.append(
                "Wysoka liczba linii/zlecenie — sprawdź czy dane nie są na poziomie linii zamiast zleceń."
            )
        if mean < 1:
            warnings.append(
                "Liczba linii/zlecenie < 1 — błąd agregacji lub niekompletne dane."
            )

        return mean, median, p90, mean

    def _calc_hours_per_day(
        self, result: PerformanceAnalysisResult, warnings: list[str]
    ) -> tuple[int, bool, Optional[float], Optional[float], Optional[float]]:
        if not result.has_hourly_data or not result.datehour_metrics:
            warnings.append(
                "Brak danych czasowych — Hours/Day ustawione na domyślne 8h."
            )
            return 8, False, None, None, None

        by_date: dict[object, list[int]] = {}
        for dh in result.datehour_metrics:
            by_date.setdefault(dh.date, []).append(dh.hour)

        windows = [max(hours) - min(hours) for hours in by_date.values()]
        if not windows:
            warnings.append(
                "Brak danych czasowych — Hours/Day ustawione na domyślne 8h."
            )
            return 8, False, None, None, None

        win_median = _percentile(sorted(windows), 50)
        hours_per_day = min(24, max(1, math.ceil(win_median + 0.5)))

        all_hours = [h for hours in by_date.values() for h in hours]
        win_min = float(min(all_hours))
        win_max = float(max(all_hours))

        if hours_per_day > 16:
            warnings.append(
                "Wykryte okno operacyjne > 16h — możliwe dane z wielu zmian lub błąd w danych czasowych."
            )

        return hours_per_day, True, win_min, win_max, round(win_median, 2)

    def _calc_commonality(
        self, df: object, warnings: list[str]
    ) -> tuple[bool, Optional[float], list[float]]:
        if (
            df is None
            or not isinstance(df, pl.DataFrame)
            or "sku" not in df.columns
            or "order_id" not in df.columns
        ):
            warnings.append(
                "Brak kolumny SKU — Commonality oparte na wartościach domyślnych."
            )
            return False, None, [0.00, 0.05, 0.10, 0.15, 0.20]

        base = _estimate_commonality(df)
        return True, base, _commonality_range(base)


# ------------------------------------------------------------------
# Pure functions (no state)
# ------------------------------------------------------------------

def _percentile(sorted_values: list, p: float) -> float:
    """Linear-interpolation percentile from a pre-sorted list."""
    n = len(sorted_values)
    if n == 0:
        return 0.0
    if n == 1:
        return float(sorted_values[0])
    idx = (p / 100) * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    return sorted_values[lo] * (1 - (idx - lo)) + sorted_values[hi] * (idx - lo)


def _suggest_batch_sizes(max_batch: int) -> list[int]:
    """Generate 5 log-scale batch size candidates from 1 to max_batch."""
    raw = [
        1,
        max(2, round(max_batch * 0.10)),
        max(3, round(max_batch * 0.25)),
        max(4, round(max_batch * 0.50)),
        max_batch,
    ]
    seen: list[int] = []
    for v in raw:
        if v not in seen:
            seen.append(v)
    while len(seen) < 5:
        gaps = [(seen[i + 1] - seen[i], i) for i in range(len(seen) - 1)]
        _, idx = max(gaps)
        seen.insert(idx + 1, (seen[idx] + seen[idx + 1]) // 2)
    return sorted(seen[:5])


def _estimate_commonality(
    df: pl.DataFrame, batch_size: int = 10, sample_batches: int = 500
) -> float:
    """Estimate SKU commonality by sampling random batches."""
    orders = df["order_id"].unique().to_list()
    if len(orders) < 2:
        return 0.0

    rng = random.Random(42)
    hits: list[float] = []
    for _ in range(sample_batches):
        sampled = rng.sample(orders, min(batch_size, len(orders)))
        lines = df.filter(pl.col("order_id").is_in(sampled))["sku"].to_list()
        if len(lines) < 2:
            continue
        batch_hits = sum(1 for i in range(1, len(lines)) if lines[i] == lines[i - 1])
        hits.append(batch_hits / (len(lines) - 1))

    return round(sum(hits) / len(hits), 3) if hits else 0.0


def _commonality_range(base: float) -> list[float]:
    """Generate 5 evenly-spaced commonality values around base."""
    lo = max(0.0, base - 0.05)
    hi = min(0.25, base + 0.10)
    step = (hi - lo) / 4
    return [round(lo + i * step, 2) for i in range(5)]
