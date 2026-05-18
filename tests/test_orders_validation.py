"""Unit tests for OrdersValidator."""

from datetime import date, timedelta

import polars as pl
import pytest

from src.analytics.orders_validation import OrdersValidator


def _make_orders(
    n: int = 5,
    start_date: date = date(2024, 10, 1),
    include_hour: bool = True,
    skus: list[str] | None = None,
    quantities: list[int] | None = None,
) -> pl.DataFrame:
    """Build a minimal valid orders DataFrame for testing."""
    dates = [start_date + timedelta(days=i % n) for i in range(n)]
    default_skus = [f"SKU-{i:03d}" for i in range(n)]
    default_qty = [1] * n
    data: dict = {
        "order_id": [f"ORD-{i:04d}" for i in range(n)],
        "sku": skus if skus is not None else default_skus,
        "quantity": quantities if quantities is not None else default_qty,
        "order_date": dates,
    }
    if include_hour:
        data["order_hour"] = [10, 11, 14, 9, 15][:n]
    return pl.DataFrame(data)


# ============================================================================
# Summary KPIs
# ============================================================================


class TestOrdersValidatorSummary:
    def test_total_rows(self):
        df = _make_orders(5)
        result = OrdersValidator().validate(df)
        assert result["total_rows"] == 5

    def test_date_range(self):
        df = _make_orders(5, start_date=date(2024, 10, 1))
        result = OrdersValidator().validate(df)
        assert result["date_from"] == "2024-10-01"
        assert result["date_to"] == "2024-10-05"

    def test_unique_days(self):
        df = _make_orders(5, start_date=date(2024, 10, 1))
        result = OrdersValidator().validate(df)
        assert result["unique_days"] == 5

    def test_has_hourly_data_true(self):
        df = _make_orders(5, include_hour=True)
        result = OrdersValidator().validate(df)
        assert result["has_hourly_data"] is True

    def test_has_hourly_data_false(self):
        df = pl.DataFrame({
            "order_id": ["O1", "O2"],
            "sku": ["A", "B"],
            "quantity": [1, 2],
            "order_date": [date(2024, 10, 1), date(2024, 10, 2)],
            "order_hour": [0, 0],
        })
        result = OrdersValidator().validate(df)
        assert result["has_hourly_data"] is False

    def test_no_date_column(self):
        df = pl.DataFrame({"order_id": ["O1"], "sku": ["A"], "quantity": [1]})
        result = OrdersValidator().validate(df)
        assert result["date_from"] is None
        assert result["date_to"] is None
        assert result["unique_days"] == 0


# ============================================================================
# Missing SKUs
# ============================================================================


class TestOrdersValidatorMissingSkus:
    def test_no_missing_skus(self):
        df = _make_orders(3)
        result = OrdersValidator().validate(df)
        assert result["missing_sku_count"] == 0
        assert result["missing_sku_pct"] == 0.0

    def test_missing_sku_null(self):
        df = pl.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "sku": ["SKU-001", None, "SKU-003"],
            "quantity": [1, 1, 1],
            "order_date": [date(2024, 10, 1)] * 3,
        })
        result = OrdersValidator().validate(df)
        assert result["missing_sku_count"] == 1
        assert result["missing_sku_pct"] == pytest.approx(33.33, rel=0.01)

    def test_missing_sku_placeholder(self):
        placeholders = ["N/A", "n/a", "-", "0", "null", "UNKNOWN", ""]
        df = pl.DataFrame({
            "order_id": [f"O{i}" for i in range(len(placeholders))],
            "sku": placeholders,
            "quantity": [1] * len(placeholders),
            "order_date": [date(2024, 10, 1)] * len(placeholders),
        })
        result = OrdersValidator().validate(df)
        assert result["missing_sku_count"] == len(placeholders)

    def test_missing_sku_pct(self):
        df = pl.DataFrame({
            "order_id": ["O1", "O2", "O3", "O4"],
            "sku": ["SKU-001", "SKU-002", None, "N/A"],
            "quantity": [1, 1, 1, 1],
            "order_date": [date(2024, 10, 1)] * 4,
        })
        result = OrdersValidator().validate(df)
        assert result["missing_sku_count"] == 2
        assert result["missing_sku_pct"] == 50.0


# ============================================================================
# Date gaps
# ============================================================================


class TestOrdersValidatorDateGaps:
    def test_no_gaps_consecutive_days(self):
        df = pl.DataFrame({
            "order_id": [f"O{i}" for i in range(5)],
            "sku": ["A"] * 5,
            "quantity": [1] * 5,
            "order_date": [date(2024, 10, 1) + timedelta(days=i) for i in range(5)],
        })
        result = OrdersValidator().validate(df)
        assert result["gap_count"] == 0
        assert result["date_coverage_pct"] == 100.0

    def test_gap_detected(self):
        # Dates: Oct 1, Oct 2, Oct 5 — gap Oct 3–4
        df = pl.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "sku": ["A", "B", "C"],
            "quantity": [1, 1, 1],
            "order_date": [date(2024, 10, 1), date(2024, 10, 2), date(2024, 10, 5)],
        })
        result = OrdersValidator().validate(df)
        assert result["gap_count"] == 1
        assert result["max_gap_days"] == 2
        assert len(result["gap_list"]) == 1
        assert result["gap_list"][0]["from"] == "2024-10-03"
        assert result["gap_list"][0]["to"] == "2024-10-04"

    def test_coverage_pct(self):
        # 3 active days out of 5 calendar days
        df = pl.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "sku": ["A", "B", "C"],
            "quantity": [1, 1, 1],
            "order_date": [date(2024, 10, 1), date(2024, 10, 3), date(2024, 10, 5)],
        })
        result = OrdersValidator().validate(df)
        assert result["date_coverage_pct"] == 60.0
        assert result["total_calendar_days"] == 5

    def test_single_day_no_gap(self):
        df = pl.DataFrame({
            "order_id": ["O1"],
            "sku": ["A"],
            "quantity": [1],
            "order_date": [date(2024, 10, 1)],
        })
        result = OrdersValidator().validate(df)
        assert result["gap_count"] == 0
        assert result["date_coverage_pct"] == 100.0


# ============================================================================
# Quantity anomalies
# ============================================================================


class TestOrdersValidatorQuantityAnomalies:
    def test_no_anomalies(self):
        df = _make_orders(5, quantities=[1, 2, 3, 2, 1])
        result = OrdersValidator().validate(df)
        assert result["qty_null_count"] == 0
        assert result["qty_zero_count"] == 0
        assert result["qty_negative_count"] == 0

    def test_null_count(self):
        df = pl.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "sku": ["A", "B", "C"],
            "quantity": [1, None, 3],
            "order_date": [date(2024, 10, 1)] * 3,
        })
        result = OrdersValidator().validate(df)
        assert result["qty_null_count"] == 1

    def test_zero_count(self):
        df = pl.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "sku": ["A", "B", "C"],
            "quantity": [1, 0, 3],
            "order_date": [date(2024, 10, 1)] * 3,
        })
        result = OrdersValidator().validate(df)
        assert result["qty_zero_count"] == 1

    def test_negative_count(self):
        df = pl.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "sku": ["A", "B", "C"],
            "quantity": [1, -5, 3],
            "order_date": [date(2024, 10, 1)] * 3,
        })
        result = OrdersValidator().validate(df)
        assert result["qty_negative_count"] == 1

    def test_outlier_detection(self):
        # 100 normal values (1-3) + 1 extreme outlier (1 000 000)
        # With 100 consistent low values the mean and std are stable enough
        # that mean+3σ correctly flags the extreme value.
        normal = [1, 2, 3] * 33 + [2]  # 100 values, mean≈2, std≈0.8
        extreme = [1_000_000]
        quantities = normal + extreme
        n = len(quantities)
        df = pl.DataFrame({
            "order_id": [f"O{i}" for i in range(n)],
            "sku": ["A"] * n,
            "quantity": quantities,
            "order_date": [date(2024, 10, 1)] * n,
        })
        result = OrdersValidator().validate(df)
        assert result["qty_outlier_count"] >= 1
        assert result["qty_outlier_threshold"] > 0

    def test_no_quantity_column(self):
        df = pl.DataFrame({"order_id": ["O1"], "sku": ["A"]})
        result = OrdersValidator().validate(df)
        assert result["qty_null_count"] == 0
        assert result["qty_outlier_count"] == 0

    def test_sample_rows_collected_per_issue(self):
        """Each qty issue type stores the offending rows (capped) so the
        Excel export can list them on their own sheet."""
        df = pl.DataFrame({
            "order_id": ["O1", "O2", "O3", "O4"],
            "sku": ["A", "B", "C", "D"],
            "quantity": [None, 0, -2, 5],
            "order_date": [date(2024, 10, 1)] * 4,
        })
        result = OrdersValidator().validate(df)
        assert {r["order_id"] for r in result["qty_null_rows"]} == {"O1"}
        assert {r["order_id"] for r in result["qty_zero_rows"]} == {"O2"}
        assert {r["order_id"] for r in result["qty_negative_rows"]} == {"O3"}
        # Each row includes the cleaned numeric quantity under the canonical key.
        assert result["qty_zero_rows"][0]["quantity"] == 0
        assert result["qty_negative_rows"][0]["quantity"] == -2


# ============================================================================
# SKU cross-validation
# ============================================================================


class TestOrdersValidatorSkuCrossValidation:
    def test_no_masterdata_path(self):
        df = _make_orders(3)
        result = OrdersValidator().validate(df, masterdata_path=None)
        assert result["sku_xval_available"] is False
        assert result["orders_skus_not_in_masterdata_count"] == 0
        assert result["masterdata_skus_not_in_orders_count"] == 0

    def test_nonexistent_masterdata_path(self, tmp_path):
        df = _make_orders(3)
        result = OrdersValidator().validate(df, masterdata_path=tmp_path / "nonexistent.csv")
        assert result["sku_xval_available"] is False

    def test_path_without_mapping_skips_cross_validation(self, tmp_path):
        """Regression: pre-quality-check masterdata files must NOT trigger
        heuristic SKU detection. Reported case: a 'Material' column was
        auto-mapped to SKU and surfaced bogus unknown/inactive SKUs."""
        md_file = tmp_path / "masterdata.csv"
        md_file.write_text("Material;length_mm;width_mm\nA;100;50\nB;200;60\n", encoding="utf-8")

        df = _make_orders(3)
        result = OrdersValidator().validate(df, masterdata_path=md_file, masterdata_mapping=None)
        assert result["sku_xval_available"] is False
        assert result["orders_skus_not_in_masterdata_count"] == 0
        assert result["masterdata_skus_not_in_orders_count"] == 0

    def test_explicit_masterdata_df_enables_cross_validation(self):
        df = _make_orders(3)  # SKU-000, SKU-001, SKU-002
        md_df = pl.DataFrame({"sku": ["SKU-000", "SKU-001", "SKU-EXTRA"]})
        result = OrdersValidator().validate(df, masterdata_df=md_df)
        assert result["sku_xval_available"] is True
        # SKU-002 in orders is not in masterdata; SKU-EXTRA in masterdata is not in orders.
        assert result["orders_skus_not_in_masterdata_count"] == 1
        assert result["masterdata_skus_not_in_orders_count"] == 1


# ============================================================================
# Weekday profile
# ============================================================================


class TestOrdersValidatorWeekdayProfile:
    def test_weekday_distribution_present(self):
        # Multiple dates across different weekdays
        df = pl.DataFrame({
            "order_id": [f"O{i}" for i in range(7)],
            "sku": ["A"] * 7,
            "quantity": [1] * 7,
            "order_date": [date(2024, 10, 7) + timedelta(days=i) for i in range(7)],  # Mon–Sun
        })
        result = OrdersValidator().validate(df)
        assert len(result["weekday_distribution"]) == 7
        total_pct = sum(result["weekday_distribution"].values())
        assert total_pct == pytest.approx(100.0, rel=0.01)

    def test_most_and_least_active(self):
        # Heavily skewed: 5 Monday records vs 1 other day
        dates = [date(2024, 10, 7)] * 5 + [date(2024, 10, 8)]  # 5 Mon + 1 Tue
        df = pl.DataFrame({
            "order_id": [f"O{i}" for i in range(6)],
            "sku": ["A"] * 6,
            "quantity": [1] * 6,
            "order_date": dates,
        })
        result = OrdersValidator().validate(df)
        assert result["most_active_weekday"] is not None
        assert result["least_active_weekday"] is not None
        assert result["most_active_weekday"] != result["least_active_weekday"]

    def test_no_date_column_returns_empty(self):
        df = pl.DataFrame({"order_id": ["O1"], "sku": ["A"], "quantity": [1]})
        result = OrdersValidator().validate(df)
        assert result["weekday_distribution"] == {}
        assert result["most_active_weekday"] is None
