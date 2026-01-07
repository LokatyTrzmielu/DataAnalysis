"""Performance analysis - KPI, peaks, shifts."""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Optional

import polars as pl

from src.analytics.shifts import ShiftSchedule, ShiftInstance
from src.core.types import ShiftType
from src.core.config import PEAK_PERCENTILES


@dataclass
class HourlyMetrics:
    """Hourly metrics."""
    hour: int
    lines: int
    orders: int
    units: int
    unique_sku: int


@dataclass
class DailyMetrics:
    """Daily metrics."""
    date: date
    lines: int
    orders: int
    units: int
    unique_sku: int
    lines_per_hour: float
    orders_per_hour: float
    units_per_hour: float


@dataclass
class PerformanceKPI:
    """Key performance indicators."""
    # Totals
    total_lines: int
    total_orders: int
    total_units: int
    unique_sku: int

    # Averages
    avg_lines_per_hour: float
    avg_orders_per_hour: float
    avg_units_per_hour: float
    avg_unique_sku_per_hour: float

    # Per order/line
    avg_lines_per_order: float
    avg_units_per_line: float
    avg_units_per_order: float

    # Peaks
    peak_lines_per_hour: int
    peak_orders_per_hour: int
    peak_units_per_hour: int

    # Percentiles
    p90_lines_per_hour: float
    p95_lines_per_hour: float
    p99_lines_per_hour: float


@dataclass
class ShiftPerformance:
    """Performance per shift."""
    shift_type: str
    total_hours: float
    total_lines: int
    total_orders: int
    total_units: int
    lines_per_hour: float
    orders_per_hour: float
    percentage_of_work: float


@dataclass
class PerformanceAnalysisResult:
    """Performance analysis result."""
    kpi: PerformanceKPI
    hourly_metrics: list[HourlyMetrics]
    daily_metrics: list[DailyMetrics]
    shift_performance: list[ShiftPerformance]
    date_from: date
    date_to: date
    total_productive_hours: float


class PerformanceAnalyzer:
    """Performance analyzer."""

    def __init__(
        self,
        shift_schedule: Optional[ShiftSchedule] = None,
        productive_hours_per_shift: float = 7.0,
    ) -> None:
        """Initialize the analyzer.

        Args:
            shift_schedule: Shift schedule (optional)
            productive_hours_per_shift: Productive hours per shift
        """
        self.shift_schedule = shift_schedule
        self.productive_hours_per_shift = productive_hours_per_shift

    def analyze(self, df: pl.DataFrame) -> PerformanceAnalysisResult:
        """Perform performance analysis.

        Args:
            df: DataFrame with Orders

        Returns:
            PerformanceAnalysisResult
        """
        # Make sure we have required columns
        if "timestamp" not in df.columns:
            raise ValueError("DataFrame must contain 'timestamp' column")

        # Date range
        date_from = df["timestamp"].min().date()
        date_to = df["timestamp"].max().date()

        # 1. Calculate hourly metrics
        hourly = self._calculate_hourly_metrics(df)

        # 2. Calculate daily metrics
        daily = self._calculate_daily_metrics(df)

        # 3. Calculate KPI
        kpi = self._calculate_kpi(df, hourly)

        # 4. Calculate performance per shift
        shift_perf = self._calculate_shift_performance(df, date_from, date_to)

        # 5. Calculate total productive hours
        total_hours = self._calculate_total_productive_hours(date_from, date_to)

        return PerformanceAnalysisResult(
            kpi=kpi,
            hourly_metrics=hourly,
            daily_metrics=daily,
            shift_performance=shift_perf,
            date_from=date_from,
            date_to=date_to,
            total_productive_hours=total_hours,
        )

    def _calculate_hourly_metrics(self, df: pl.DataFrame) -> list[HourlyMetrics]:
        """Calculate metrics per hour."""
        # Aggregation per hour
        hourly_df = df.group_by(pl.col("timestamp").dt.hour().alias("hour")).agg([
            pl.len().alias("lines"),
            pl.col("order_id").n_unique().alias("orders"),
            pl.col("quantity").sum().alias("units"),
            pl.col("sku").n_unique().alias("unique_sku"),
        ]).sort("hour")

        return [
            HourlyMetrics(
                hour=row["hour"],
                lines=row["lines"],
                orders=row["orders"],
                units=row["units"],
                unique_sku=row["unique_sku"],
            )
            for row in hourly_df.to_dicts()
        ]

    def _calculate_daily_metrics(self, df: pl.DataFrame) -> list[DailyMetrics]:
        """Calculate metrics per day."""
        daily_df = df.group_by(pl.col("timestamp").dt.date().alias("date")).agg([
            pl.len().alias("lines"),
            pl.col("order_id").n_unique().alias("orders"),
            pl.col("quantity").sum().alias("units"),
            pl.col("sku").n_unique().alias("unique_sku"),
        ]).sort("date")

        return [
            DailyMetrics(
                date=row["date"],
                lines=row["lines"],
                orders=row["orders"],
                units=row["units"],
                unique_sku=row["unique_sku"],
                lines_per_hour=row["lines"] / self.productive_hours_per_shift,
                orders_per_hour=row["orders"] / self.productive_hours_per_shift,
                units_per_hour=row["units"] / self.productive_hours_per_shift,
            )
            for row in daily_df.to_dicts()
        ]

    def _calculate_kpi(
        self,
        df: pl.DataFrame,
        hourly: list[HourlyMetrics],
    ) -> PerformanceKPI:
        """Calculate KPI."""
        total_lines = len(df)
        total_orders = df["order_id"].n_unique()
        total_units = df["quantity"].sum()
        unique_sku = df["sku"].n_unique()

        # Averages per order/line
        avg_lines_per_order = total_lines / total_orders if total_orders > 0 else 0
        avg_units_per_line = total_units / total_lines if total_lines > 0 else 0
        avg_units_per_order = total_units / total_orders if total_orders > 0 else 0

        # Hourly metrics
        if hourly:
            lines_values = [h.lines for h in hourly]
            orders_values = [h.orders for h in hourly]
            units_values = [h.units for h in hourly]
            sku_values = [h.unique_sku for h in hourly]

            avg_lines_per_hour = sum(lines_values) / len(lines_values)
            avg_orders_per_hour = sum(orders_values) / len(orders_values)
            avg_units_per_hour = sum(units_values) / len(units_values)
            avg_unique_sku_per_hour = sum(sku_values) / len(sku_values)

            peak_lines = max(lines_values)
            peak_orders = max(orders_values)
            peak_units = max(units_values)

            # Percentiles
            sorted_lines = sorted(lines_values)
            n = len(sorted_lines)
            p90 = sorted_lines[int(n * 0.90)] if n > 0 else 0
            p95 = sorted_lines[int(n * 0.95)] if n > 0 else 0
            p99 = sorted_lines[int(n * 0.99)] if n > 0 else 0
        else:
            avg_lines_per_hour = avg_orders_per_hour = avg_units_per_hour = 0
            avg_unique_sku_per_hour = 0
            peak_lines = peak_orders = peak_units = 0
            p90 = p95 = p99 = 0

        return PerformanceKPI(
            total_lines=total_lines,
            total_orders=total_orders,
            total_units=total_units,
            unique_sku=unique_sku,
            avg_lines_per_hour=avg_lines_per_hour,
            avg_orders_per_hour=avg_orders_per_hour,
            avg_units_per_hour=avg_units_per_hour,
            avg_unique_sku_per_hour=avg_unique_sku_per_hour,
            avg_lines_per_order=avg_lines_per_order,
            avg_units_per_line=avg_units_per_line,
            avg_units_per_order=avg_units_per_order,
            peak_lines_per_hour=peak_lines,
            peak_orders_per_hour=peak_orders,
            peak_units_per_hour=peak_units,
            p90_lines_per_hour=p90,
            p95_lines_per_hour=p95,
            p99_lines_per_hour=p99,
        )

    def _calculate_shift_performance(
        self,
        df: pl.DataFrame,
        date_from: date,
        date_to: date,
    ) -> list[ShiftPerformance]:
        """Calculate performance per shift type."""
        if self.shift_schedule is None:
            return []

        base_hours = self.shift_schedule.calculate_total_hours(
            date_from, date_to, ShiftType.BASE
        )
        overlay_hours = self.shift_schedule.calculate_total_hours(
            date_from, date_to, ShiftType.OVERLAY
        )
        total_hours = base_hours + overlay_hours

        total_lines = len(df)
        total_orders = df["order_id"].n_unique()
        total_units = df["quantity"].sum()

        results = []

        if base_hours > 0:
            base_pct = base_hours / total_hours if total_hours > 0 else 0
            results.append(ShiftPerformance(
                shift_type="BASE",
                total_hours=base_hours,
                total_lines=int(total_lines * base_pct),
                total_orders=int(total_orders * base_pct),
                total_units=int(total_units * base_pct),
                lines_per_hour=total_lines * base_pct / base_hours,
                orders_per_hour=total_orders * base_pct / base_hours,
                percentage_of_work=base_pct * 100,
            ))

        if overlay_hours > 0:
            overlay_pct = overlay_hours / total_hours if total_hours > 0 else 0
            results.append(ShiftPerformance(
                shift_type="OVERLAY",
                total_hours=overlay_hours,
                total_lines=int(total_lines * overlay_pct),
                total_orders=int(total_orders * overlay_pct),
                total_units=int(total_units * overlay_pct),
                lines_per_hour=total_lines * overlay_pct / overlay_hours,
                orders_per_hour=total_orders * overlay_pct / overlay_hours,
                percentage_of_work=overlay_pct * 100,
            ))

        return results

    def _calculate_total_productive_hours(
        self,
        date_from: date,
        date_to: date,
    ) -> float:
        """Calculate total number of productive hours."""
        if self.shift_schedule:
            return self.shift_schedule.calculate_total_hours(date_from, date_to)

        # Default: working days * 2 shifts * productive_hours
        days = (date_to - date_from).days + 1
        working_days = sum(
            1 for i in range(days)
            if (date_from + timedelta(days=i)).weekday() < 5
        )
        return working_days * 2 * self.productive_hours_per_shift


def analyze_performance(
    df: pl.DataFrame,
    shift_schedule: Optional[ShiftSchedule] = None,
) -> PerformanceAnalysisResult:
    """Helper function for performance analysis.

    Args:
        df: DataFrame with Orders
        shift_schedule: Shift schedule (optional)

    Returns:
        PerformanceAnalysisResult
    """
    analyzer = PerformanceAnalyzer(shift_schedule)
    return analyzer.analyze(df)
