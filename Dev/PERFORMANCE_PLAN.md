# Performance Module Enhancement + Orders Date/Time Import

**Branch:** `feature/performance`
**Status:** In progress
**Created:** 2026-02-08

---

## Context

Capacity Analysis is complete. Now we enhance Performance module and fix Orders import to handle various date/time formats from clients.

The user needs **date + full hour** granularity for estimating average technical throughput per hour. Minutes/seconds are irrelevant.

**Implementation order:** Part 1 → Part 2 → Part 3 (sequential).

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Date field required? | **Yes, always** | Clients always have date. Time-only scenario doesn't exist. |
| UI when no time data | **Hide hourly charts + show warning** | Show daily charts + SKU Pareto, hide throughput chart. Warning: "Hourly analysis unavailable - import data with time information." |
| Percentile source | **DateHour data points** | Current 24-point hourly profile gives meaningless percentiles. Real date+hour data (hundreds of points) is statistically valid. |
| Alias redistribution | **datetime/timestamp → `date`, time/hour → `time`** | Combined datetime strings map to `date` (parser detects datetime vs date-only). Pure time aliases go to `time`. |

---

## Part 1: Orders Date/Time Import Refactor

### Problem
Client data comes in different formats:
- Date + time in one column (e.g. `2024-01-15 14:30:00`)
- Date only (e.g. `2024-01-15`)
- Date and time in two separate columns

Current system expects a single `timestamp` column, which doesn't cover all scenarios.

### Solution
Replace single `timestamp` field with two fields in `ORDERS_SCHEMA`:
- **`date`** (required) - date or datetime column
- **`time`** (optional) - time column (only when date and time are separate)

### Tasks

- [x] **1.1** Update `ORDERS_SCHEMA` in `src/ingest/mapping.py`
  - Replace `timestamp` with `date` (required) and `time` (optional)
  - `date` aliases: "datetime", "timestamp", "date", "created", "order_date", "ship_date", "delivery_date", "fulfillment_date", "transaction_date", "created_at", "updated_at", "processed_date", "data", "data_zamowienia", "data_wysylki", "data_dostawy", "data_realizacji"
  - `time` aliases: "time", "hour", "czas", "godzina", "time_of_day", "order_time", "ship_time"

- [x] **1.2** Update `OrdersIngestPipeline` in `src/ingest/pipeline.py`
  - Replace timestamp parsing block (lines 216-232) with new logic:
    1. Parse `date` column → try datetime first, then date-only
    2. If `time` column mapped → parse it as time
    3. Combine into `timestamp` column:
       - If `date` already has time component → use it, truncate to hour
       - If `time` column exists → combine date + time, truncate to hour
       - If date-only (no time anywhere) → set time to 00:00, add warning
    4. Create helper columns: `order_date` (Date), `order_hour` (Int 0-23)
    5. Track `has_hourly_data` flag (add to warnings or IngestResult metadata)

- [x] **1.3** Update `OrdersProcessor.normalize()` in `src/model/orders.py`
  - Pipeline now produces `timestamp` column already → normalize() mainly handles edge cases
  - Keep creating `order_date`, `order_hour`, `weekday` helper columns

- [x] **1.4** Update tests in `tests/test_ingest.py`
  - Test: datetime in one column → date and hour extracted
  - Test: date-only column → works, warning about no hourly data
  - Test: separate date + time columns → combined correctly
  - Test: various date formats (ISO, European, US)

---

## Part 2: Performance Analytics Enhancement

### Current state
Backend (`src/analytics/performance.py`) has:
- HourlyMetrics (aggregated profile, 24 data points)
- DailyMetrics
- PerformanceKPI (totals, averages, peaks, percentiles from 24-point profile - **flawed**)
- ShiftPerformance

### New features

- [x] **2.1** Real Throughput Analysis (date+hour granularity)
  - New `DateHourMetrics` dataclass (date + hour + lines + orders + units)
  - New `_calculate_datehour_metrics()` method
  - **Fix:** Recalculate percentiles from actual date+hour data points (not 24-point profile)
  - Note: KPI values will change vs. current calculation (expected, correct behavior)

- [x] **2.2** Seasonality / Trends
  - New `WeeklyTrend` dataclass (week_number, year, lines, orders, units, avg_lines_per_hour)
  - New `MonthlyTrend` dataclass (month, year, lines, orders, units, avg_lines_per_hour)
  - New `_calculate_trends()` method
  - Day-of-week profile: dict mapping weekday (0-6) → avg lines per day

- [x] **2.3** SKU Frequency / Pareto
  - New `SKUFrequency` dataclass (sku, total_lines, total_units, total_orders, frequency_rank, cumulative_pct, abc_class)
  - New `_calculate_sku_pareto()` method
  - ABC classification (A: top 80%, B: next 15%, C: remaining 5%)

- [x] **2.4** Update `PerformanceAnalysisResult`
  - Add: `datehour_metrics`, `weekly_trends`, `monthly_trends`, `weekday_profile`, `sku_pareto`, `has_hourly_data`

- [x] **2.5** Update tests in `tests/test_analytics.py`

---

## Part 3: Performance UI Enhancement

File: `src/ui/views/performance_view.py`

- [x] **3.1** Update KPI section
  - Keep: Avg Lines/h, Peak Hour, Total Orders, Avg Lines/Order
  - Add: P95 Lines/h
  - Conditionally show hourly KPIs only when `has_hourly_data` is True

- [x] **3.2** New: Throughput chart
  - Time series scatter/line chart (date+hour granularity)
  - Horizontal reference lines for avg, P90, P95
  - **Only show when `has_hourly_data` is True**
  - Otherwise: warning banner "Hourly throughput analysis unavailable - import data with time information"

- [x] **3.3** New: Trends section
  - Weekly trend bar chart
  - Day-of-week profile chart

- [x] **3.4** New: SKU Pareto section
  - Pareto chart (bar + cumulative line)
  - ABC summary (counts + percentages)
  - Top 20 SKU table

- [x] **3.5** Layout organization
  - Follow Capacity view pattern: KPI → Charts → Tables
  - Use `render_section_header` for logical sections
  - Section order: KPI → Throughput → Daily Activity → Heatmap → Trends → SKU Pareto → Order Structure → Detailed Stats

---

## Files to modify (in order)

| # | File | Change |
|---|------|--------|
| 1 | `src/ingest/mapping.py` | ORDERS_SCHEMA: replace `timestamp` with `date` + `time` |
| 2 | `src/ingest/pipeline.py` | OrdersIngestPipeline: new date/time parsing logic |
| 3 | `src/model/orders.py` | OrdersProcessor.normalize() adjustment |
| 4 | `tests/test_ingest.py` | Tests for new date/time scenarios |
| 5 | `src/analytics/performance.py` | New dataclasses + methods (DateHour, Trends, SKU Pareto) |
| 6 | `tests/test_analytics.py` | Tests for new analytics |
| 7 | `src/ui/views/performance_view.py` | New charts + conditional sections |

---

## Verification checklist

- [ ] Import Orders with datetime in one column → date and hour extracted
- [ ] Import Orders with date-only column → works, warning about no hourly data
- [ ] Import Orders with separate date + time columns → combined correctly
- [ ] Performance analysis with hourly data → all new sections render
- [ ] Performance analysis without hourly data → throughput chart hidden, warning shown
- [ ] SKU Pareto shows ABC classification correctly
- [ ] All tests pass
