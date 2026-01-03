"""Analytics module - DuckDB, capacity, performance."""

from src.analytics.duckdb_runner import (
    DuckDBRunner,
    create_runner,
)
from src.analytics.capacity import (
    CapacityAnalyzer,
    CapacityAnalysisResult,
    analyze_capacity,
)
from src.analytics.shifts import (
    ShiftSchedule,
    ShiftInstance,
    ShiftScheduleLoader,
    load_shifts,
)
from src.analytics.performance import (
    PerformanceAnalyzer,
    PerformanceAnalysisResult,
    PerformanceKPI,
    HourlyMetrics,
    DailyMetrics,
    ShiftPerformance,
    analyze_performance,
)

__all__ = [
    # DuckDB
    "DuckDBRunner",
    "create_runner",
    # Capacity
    "CapacityAnalyzer",
    "CapacityAnalysisResult",
    "analyze_capacity",
    # Shifts
    "ShiftSchedule",
    "ShiftInstance",
    "ShiftScheduleLoader",
    "load_shifts",
    # Performance
    "PerformanceAnalyzer",
    "PerformanceAnalysisResult",
    "PerformanceKPI",
    "HourlyMetrics",
    "DailyMetrics",
    "ShiftPerformance",
    "analyze_performance",
]
