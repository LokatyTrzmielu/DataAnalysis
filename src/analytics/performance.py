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
class DateHourMetrics:
    """Metrics per date+hour (real throughput data point)."""
    date: date
    hour: int
    lines: int
    orders: int
    units: int


@dataclass
class WeeklyTrend:
    """Weekly trend metrics."""
    year: int
    week_number: int
    lines: int
    orders: int
    units: int
    avg_lines_per_hour: float


@dataclass
class MonthlyTrend:
    """Monthly trend metrics."""
    year: int
    month: int
    lines: int
    orders: int
    units: int
    avg_lines_per_hour: float


@dataclass
class SKUFrequency:
    """SKU frequency / Pareto analysis."""
    sku: str
    total_lines: int
    total_units: int
    total_orders: int
    frequency_rank: int
    cumulative_pct: float
    abc_class: str  # "A", "B", or "C"


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
    # New fields
    datehour_metrics: list[DateHourMetrics] = field(default_factory=list)
    weekly_trends: list[WeeklyTrend] = field(default_factory=list)
    monthly_trends: list[MonthlyTrend] = field(default_factory=list)
    weekday_profile: dict[int, float] = field(default_factory=dict)
    sku_pareto: list[SKUFrequency] = field(default_factory=list)
    has_hourly_data: bool = False


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

        # Ensure timestamp is datetime type
        ts_dtype = df["timestamp"].dtype
        if not str(ts_dtype).startswith("Datetime"):
            if ts_dtype == pl.Utf8:
                df = df.with_columns([
                    pl.col("timestamp").str.to_datetime(strict=False)
                ])
            elif ts_dtype in [pl.Int64, pl.Int32, pl.UInt64, pl.UInt32]:
                # Assume Unix timestamp in seconds
                df = df.with_columns([
                    pl.from_epoch(pl.col("timestamp"), time_unit="s").alias("timestamp")
                ])
            else:
                raise ValueError(f"Cannot convert timestamp column of type {ts_dtype} to datetime")

        # Date range
        ts_min = df["timestamp"].min()
        ts_max = df["timestamp"].max()
        if ts_min is None or ts_max is None:
            raise ValueError("DataFrame has no valid timestamps")
        if isinstance(ts_min, datetime):
            date_from = ts_min.date()
        else:
            raise ValueError(f"Cannot extract date from timestamp min: {type(ts_min)}")
        if isinstance(ts_max, datetime):
            date_to = ts_max.date()
        else:
            raise ValueError(f"Cannot extract date from timestamp max: {type(ts_max)}")

        # Detect hourly data: check if any non-midnight timestamps exist
        has_hourly_data = df.filter(
            (pl.col("timestamp").dt.hour() != 0)
            | (pl.col("timestamp").dt.minute() != 0)
        ).height > 0

        # 1. Calculate hourly metrics (aggregated profile)
        hourly = self._calculate_hourly_metrics(df)

        # 2. Calculate daily metrics
        daily = self._calculate_daily_metrics(df)

        # 3. Calculate date+hour metrics (real throughput data points)
        datehour = self._calculate_datehour_metrics(df)

        # 4. Calculate KPI (uses datehour for percentiles)
        kpi = self._calculate_kpi(df, datehour)

        # 5. Calculate trends
        weekly_trends, monthly_trends, weekday_profile = self._calculate_trends(df, datehour)

        # 6. Calculate SKU Pareto
        sku_pareto = self._calculate_sku_pareto(df)

        # 7. Calculate performance per shift
        shift_perf = self._calculate_shift_performance(df, date_from, date_to)

        # 8. Calculate total productive hours
        total_hours = self._calculate_total_productive_hours(date_from, date_to)

        return PerformanceAnalysisResult(
            kpi=kpi,
            hourly_metrics=hourly,
            daily_metrics=daily,
            shift_performance=shift_perf,
            date_from=date_from,
            date_to=date_to,
            total_productive_hours=total_hours,
            datehour_metrics=datehour,
            weekly_trends=weekly_trends,
            monthly_trends=monthly_trends,
            weekday_profile=weekday_profile,
            sku_pareto=sku_pareto,
            has_hourly_data=has_hourly_data,
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

    def _calculate_datehour_metrics(self, df: pl.DataFrame) -> list[DateHourMetrics]:
        """Calculate metrics per date+hour (real throughput data points)."""
        datehour_df = df.group_by([
            pl.col("timestamp").dt.date().alias("date"),
            pl.col("timestamp").dt.hour().alias("hour"),
        ]).agg([
            pl.len().alias("lines"),
            pl.col("order_id").n_unique().alias("orders"),
            pl.col("quantity").sum().alias("units"),
        ]).sort(["date", "hour"])

        return [
            DateHourMetrics(
                date=row["date"],
                hour=row["hour"],
                lines=row["lines"],
                orders=row["orders"],
                units=row["units"],
            )
            for row in datehour_df.to_dicts()
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
        datehour: list[DateHourMetrics],
    ) -> PerformanceKPI:
        """Calculate KPI using real date+hour data points for percentiles."""
        total_lines = len(df)
        total_orders = df["order_id"].n_unique()
        total_units = int(df["quantity"].sum() or 0)
        unique_sku = df["sku"].n_unique()

        # Averages per order/line
        avg_lines_per_order = total_lines / total_orders if total_orders > 0 else 0
        avg_units_per_line = total_units / total_lines if total_lines > 0 else 0
        avg_units_per_order = total_units / total_orders if total_orders > 0 else 0

        # Use real date+hour data points (statistically valid)
        if datehour:
            lines_values = [dh.lines for dh in datehour]
            orders_values = [dh.orders for dh in datehour]
            units_values = [dh.units for dh in datehour]

            avg_lines_per_hour = sum(lines_values) / len(lines_values)
            avg_orders_per_hour = sum(orders_values) / len(orders_values)
            avg_units_per_hour = sum(units_values) / len(units_values)
            avg_unique_sku_per_hour = 0.0  # Not available from datehour

            peak_lines = max(lines_values)
            peak_orders = max(orders_values)
            peak_units = max(units_values)

            # Percentiles from real data points (hundreds of points)
            sorted_lines = sorted(lines_values)
            n = len(sorted_lines)
            p90 = sorted_lines[min(int(n * 0.90), n - 1)] if n > 0 else 0
            p95 = sorted_lines[min(int(n * 0.95), n - 1)] if n > 0 else 0
            p99 = sorted_lines[min(int(n * 0.99), n - 1)] if n > 0 else 0
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

    def _calculate_trends(
        self,
        df: pl.DataFrame,
        datehour: list[DateHourMetrics],
    ) -> tuple[list[WeeklyTrend], list[MonthlyTrend], dict[int, float]]:
        """Calculate weekly/monthly trends and weekday profile."""
        # Weekly trends
        weekly_df = df.with_columns([
            pl.col("timestamp").dt.iso_year().alias("year"),
            pl.col("timestamp").dt.week().alias("week"),
        ]).group_by(["year", "week"]).agg([
            pl.len().alias("lines"),
            pl.col("order_id").n_unique().alias("orders"),
            pl.col("quantity").sum().alias("units"),
        ]).sort(["year", "week"])

        # Count date+hour data points per week for avg_lines_per_hour
        dh_df = pl.DataFrame([
            {"year": dh.date.isocalendar()[0], "week": dh.date.isocalendar()[1], "lines": dh.lines}
            for dh in datehour
        ]) if datehour else pl.DataFrame({"year": [], "week": [], "lines": []})

        dh_weekly = {}
        if len(dh_df) > 0:
            dh_agg = dh_df.group_by(["year", "week"]).agg([
                pl.col("lines").mean().alias("avg_lph"),
            ])
            for row in dh_agg.to_dicts():
                dh_weekly[(row["year"], row["week"])] = row["avg_lph"]

        weekly_trends = [
            WeeklyTrend(
                year=row["year"],
                week_number=row["week"],
                lines=row["lines"],
                orders=row["orders"],
                units=row["units"],
                avg_lines_per_hour=dh_weekly.get((row["year"], row["week"]), 0.0),
            )
            for row in weekly_df.to_dicts()
        ]

        # Monthly trends
        monthly_df = df.with_columns([
            pl.col("timestamp").dt.year().alias("year"),
            pl.col("timestamp").dt.month().alias("month"),
        ]).group_by(["year", "month"]).agg([
            pl.len().alias("lines"),
            pl.col("order_id").n_unique().alias("orders"),
            pl.col("quantity").sum().alias("units"),
        ]).sort(["year", "month"])

        dh_monthly = {}
        if len(dh_df) > 0:
            dh_m = pl.DataFrame([
                {"year": dh.date.year, "month": dh.date.month, "lines": dh.lines}
                for dh in datehour
            ])
            dh_m_agg = dh_m.group_by(["year", "month"]).agg([
                pl.col("lines").mean().alias("avg_lph"),
            ])
            for row in dh_m_agg.to_dicts():
                dh_monthly[(row["year"], row["month"])] = row["avg_lph"]

        monthly_trends = [
            MonthlyTrend(
                year=row["year"],
                month=row["month"],
                lines=row["lines"],
                orders=row["orders"],
                units=row["units"],
                avg_lines_per_hour=dh_monthly.get((row["year"], row["month"]), 0.0),
            )
            for row in monthly_df.to_dicts()
        ]

        # Weekday profile: avg lines per day for each weekday (0=Mon, 6=Sun)
        weekday_df = df.with_columns([
            pl.col("timestamp").dt.weekday().alias("weekday"),
            pl.col("timestamp").dt.date().alias("_date"),
        ]).group_by(["weekday", "_date"]).agg([
            pl.len().alias("lines"),
        ]).group_by("weekday").agg([
            pl.col("lines").mean().alias("avg_lines"),
        ]).sort("weekday")

        weekday_profile = {
            row["weekday"]: round(row["avg_lines"], 1)
            for row in weekday_df.to_dicts()
        }

        return weekly_trends, monthly_trends, weekday_profile

    def _calculate_sku_pareto(self, df: pl.DataFrame) -> list[SKUFrequency]:
        """Calculate SKU frequency / Pareto with ABC classification."""
        if "sku" not in df.columns:
            return []

        sku_df = df.group_by("sku").agg([
            pl.len().alias("total_lines"),
            pl.col("quantity").sum().alias("total_units"),
            pl.col("order_id").n_unique().alias("total_orders"),
        ]).sort("total_lines", descending=True)

        total_lines_all = sku_df["total_lines"].sum()
        if total_lines_all == 0:
            return []

        results = []
        cumulative = 0

        for rank, row in enumerate(sku_df.to_dicts(), start=1):
            cumulative += row["total_lines"]
            cumulative_pct = cumulative / total_lines_all * 100

            # ABC: A = top 80%, B = next 15% (80-95%), C = rest (95-100%)
            if cumulative_pct <= 80:
                abc_class = "A"
            elif cumulative_pct <= 95:
                abc_class = "B"
            else:
                abc_class = "C"

            results.append(SKUFrequency(
                sku=row["sku"],
                total_lines=row["total_lines"],
                total_units=row["total_units"],
                total_orders=row["total_orders"],
                frequency_rank=rank,
                cumulative_pct=round(cumulative_pct, 2),
                abc_class=abc_class,
            ))

        return results

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
