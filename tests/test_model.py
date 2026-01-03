"""Testy jednostkowe dla modulu model."""

from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from src.model.masterdata import (
    MasterdataProcessor,
    MasterdataConsolidationResult,
    process_masterdata,
)
from src.model.orders import (
    OrdersProcessor,
    OrdersProcessingResult,
    process_orders,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ============================================================================
# Testy MasterdataProcessor
# ============================================================================


class TestMasterdataProcessor:
    """Testy dla MasterdataProcessor."""

    def test_consolidate_no_duplicates(self):
        """Test konsolidacji bez duplikatow."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 200.0, 300.0],
            "width_mm": [50.0, 100.0, 150.0],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, 3.0, 4.5],
        })

        processor = MasterdataProcessor()
        result = processor.consolidate_duplicates(df)

        assert result.original_count == 3
        assert result.consolidated_count == 3
        assert result.duplicates_merged == 0

    def test_consolidate_with_duplicates_first(self):
        """Test konsolidacji z duplikatami - strategia first."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU1", "SKU2"],
            "length_mm": [100.0, 150.0, 200.0],
            "width_mm": [50.0, 75.0, 100.0],
            "height_mm": [30.0, 45.0, 60.0],
            "weight_kg": [1.5, 2.0, 3.0],
        })

        processor = MasterdataProcessor(consolidation_strategy="first")
        result = processor.consolidate_duplicates(df)

        assert result.consolidated_count == 2
        assert result.duplicates_merged == 1

        # Sprawdz czy SKU1 ma pierwsza wartosc
        sku1_row = result.df.filter(pl.col("sku") == "SKU1")
        assert sku1_row["length_mm"][0] == 100.0

    def test_consolidate_with_duplicates_max(self):
        """Test konsolidacji z duplikatami - strategia max."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU1", "SKU2"],
            "length_mm": [100.0, 150.0, 200.0],
            "width_mm": [50.0, 75.0, 100.0],
            "height_mm": [30.0, 45.0, 60.0],
            "weight_kg": [1.5, 2.0, 3.0],
        })

        processor = MasterdataProcessor(consolidation_strategy="max")
        result = processor.consolidate_duplicates(df)

        # Sprawdz czy SKU1 ma maksymalna wartosc
        sku1_row = result.df.filter(pl.col("sku") == "SKU1")
        assert sku1_row["length_mm"][0] == 150.0

    def test_consolidate_with_duplicates_mean(self):
        """Test konsolidacji z duplikatami - strategia mean."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU1", "SKU2"],
            "length_mm": [100.0, 200.0, 300.0],
            "width_mm": [50.0, 100.0, 150.0],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.0, 3.0, 4.5],
        })

        processor = MasterdataProcessor(consolidation_strategy="mean")
        result = processor.consolidate_duplicates(df)

        # Sprawdz czy SKU1 ma srednia wartosc
        sku1_row = result.df.filter(pl.col("sku") == "SKU1")
        assert sku1_row["length_mm"][0] == 150.0  # (100 + 200) / 2
        assert sku1_row["weight_kg"][0] == 2.0    # (1 + 3) / 2

    def test_calculate_volume(self):
        """Test obliczania kubatury."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [1000.0, 2000.0],
            "width_mm": [1000.0, 1000.0],
            "height_mm": [1000.0, 500.0],
        })

        processor = MasterdataProcessor()
        result = processor.calculate_volume(df)

        assert "volume_m3" in result.columns
        assert result["volume_m3"][0] == 1.0  # 1000*1000*1000 / 10^9 = 1
        assert result["volume_m3"][1] == 1.0  # 2000*1000*500 / 10^9 = 1

    def test_add_size_category(self):
        """Test dodawania kategorii wielkosci."""
        # Dobieramy wymiary tak aby uzyskac rozne kategorie:
        # XS: volume < 0.001 m3 (np. 50x50x50 = 0.000125 m3)
        # S: volume 0.001-0.01 m3 (np. 100x100x100 = 0.001 m3)
        # M: volume 0.01-0.05 m3 (np. 200x200x200 = 0.008 m3)
        # L: volume 0.05-0.1 m3 (np. 400x400x350 = 0.056 m3)
        # XL: volume > 0.1 m3 (np. 500x500x500 = 0.125 m3)
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3", "SKU4", "SKU5"],
            "length_mm": [50.0, 100.0, 200.0, 400.0, 500.0],
            "width_mm": [50.0, 100.0, 200.0, 400.0, 500.0],
            "height_mm": [50.0, 100.0, 200.0, 350.0, 500.0],
        })

        processor = MasterdataProcessor()
        result = processor.add_size_category(df)

        assert "size_category" in result.columns
        categories = result["size_category"].to_list()

        # Sprawdz czy mamy rozne kategorie
        assert len(set(categories)) >= 3  # Powinno byc co najmniej 3 rozne kategorie

    def test_process_full(self):
        """Test pelnego przetwarzania."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU1", "SKU2"],
            "length_mm": [100.0, 150.0, 200.0],
            "width_mm": [50.0, 75.0, 100.0],
            "height_mm": [30.0, 45.0, 60.0],
            "weight_kg": [1.5, 2.0, 3.0],
        })

        result = process_masterdata(df)

        assert len(result) == 2  # Po konsolidacji
        assert "volume_m3" in result.columns
        assert "size_category" in result.columns


# ============================================================================
# Testy OrdersProcessor
# ============================================================================


class TestOrdersProcessor:
    """Testy dla OrdersProcessor."""

    def test_normalize_timestamp_string(self):
        """Test normalizacji timestamp ze stringa."""
        df = pl.DataFrame({
            "order_id": ["ORD1", "ORD2"],
            "sku": ["SKU1", "SKU2"],
            "quantity": [1, 2],
            "timestamp": ["2024-10-15 10:30:00", "2024-10-16 14:45:00"],
        })

        processor = OrdersProcessor()
        result = processor.normalize(df)

        assert result["timestamp"].dtype == pl.Datetime
        assert "order_date" in result.columns
        assert "order_hour" in result.columns
        assert "weekday" in result.columns

    def test_normalize_quantity(self):
        """Test normalizacji quantity."""
        df = pl.DataFrame({
            "order_id": ["ORD1", "ORD2"],
            "sku": ["SKU1", "SKU2"],
            "quantity": [1.0, 2.5],  # floaty
            "timestamp": ["2024-10-15 10:30:00", "2024-10-16 14:45:00"],
        })

        processor = OrdersProcessor()
        result = processor.normalize(df)

        assert result["quantity"].dtype == pl.Int64

    def test_join_with_masterdata(self):
        """Test laczenia z Masterdata."""
        orders_df = pl.DataFrame({
            "order_id": ["ORD1", "ORD2", "ORD3"],
            "sku": ["SKU1", "SKU2", "SKU3"],
            "quantity": [1, 2, 3],
        })

        masterdata_df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [100.0, 200.0],
            "width_mm": [50.0, 100.0],
            "height_mm": [30.0, 60.0],
            "weight_kg": [1.5, 3.0],
            "volume_m3": [0.00015, 0.0012],
        })

        processor = OrdersProcessor()
        result = processor.join_with_masterdata(orders_df, masterdata_df)

        # SKU3 nie ma danych w masterdata
        assert result["length_mm"][2] is None
        assert result["line_volume_m3"][0] == 0.00015  # 0.00015 * 1
        assert result["line_weight_kg"][0] == 1.5      # 1.5 * 1

    def test_calculate_stats(self):
        """Test obliczania statystyk."""
        df = pl.DataFrame({
            "order_id": ["ORD1", "ORD1", "ORD2"],
            "sku": ["SKU1", "SKU2", "SKU1"],
            "quantity": [2, 3, 5],
            "timestamp": [
                datetime(2024, 10, 15, 10, 30),
                datetime(2024, 10, 15, 10, 30),
                datetime(2024, 10, 16, 14, 45),
            ],
        })

        processor = OrdersProcessor()
        stats = processor.calculate_stats(df)

        assert stats["total_lines"] == 3
        assert stats["total_orders"] == 2
        assert stats["total_units"] == 10
        assert stats["unique_sku"] == 2
        assert stats["avg_lines_per_order"] == 1.5

    def test_process_full(self):
        """Test pelnego przetwarzania."""
        orders_df = pl.DataFrame({
            "order_id": ["ORD1", "ORD2"],
            "sku": ["SKU1", "SKU2"],
            "quantity": [1, 2],
            "timestamp": ["2024-10-15 10:30:00", "2024-10-16 14:45:00"],
        })

        masterdata_df = pl.DataFrame({
            "sku": ["SKU1"],
            "length_mm": [100.0],
            "width_mm": [50.0],
            "height_mm": [30.0],
            "weight_kg": [1.5],
            "volume_m3": [0.00015],
        })

        result = process_orders(orders_df, masterdata_df)

        assert result.total_orders == 2
        assert result.total_lines == 2
        assert result.total_units == 3
        assert result.unique_sku == 2
        assert "SKU2" in result.unmatched_sku

    def test_process_without_masterdata(self):
        """Test przetwarzania bez Masterdata."""
        orders_df = pl.DataFrame({
            "order_id": ["ORD1", "ORD2"],
            "sku": ["SKU1", "SKU2"],
            "quantity": [1, 2],
            "timestamp": ["2024-10-15 10:30:00", "2024-10-16 14:45:00"],
        })

        result = process_orders(orders_df)

        assert result.total_orders == 2
        assert result.total_lines == 2
        assert len(result.unmatched_sku) == 0


# ============================================================================
# Testy integracyjne
# ============================================================================


class TestModelIntegration:
    """Testy integracyjne dla modulu model."""

    def test_full_pipeline(self):
        """Test pelnego pipeline'u przetwarzania."""
        # Dane Masterdata z duplikatami
        masterdata_df = pl.DataFrame({
            "sku": ["SKU1", "SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 150.0, 200.0, 300.0],
            "width_mm": [50.0, 75.0, 100.0, 150.0],
            "height_mm": [30.0, 45.0, 60.0, 90.0],
            "weight_kg": [1.5, 2.0, 3.0, 4.5],
            "stock_qty": [10, 15, 20, 30],
        })

        # Przetworzenie Masterdata
        processed_md = process_masterdata(masterdata_df)
        assert len(processed_md) == 3  # Po konsolidacji

        # Dane Orders
        orders_df = pl.DataFrame({
            "order_id": ["ORD1", "ORD1", "ORD2"],
            "sku": ["SKU1", "SKU2", "SKU4"],  # SKU4 nie istnieje
            "quantity": [2, 3, 1],
            "timestamp": [
                "2024-10-15 10:30:00",
                "2024-10-15 10:30:00",
                "2024-10-16 14:45:00",
            ],
        })

        # Przetworzenie Orders z join do Masterdata
        orders_result = process_orders(orders_df, processed_md)

        assert orders_result.total_orders == 2
        assert orders_result.total_lines == 3
        assert "SKU4" in orders_result.unmatched_sku

        # Sprawdz czy join dziala
        assert "volume_m3" in orders_result.df.columns
        assert orders_result.df["volume_m3"][2] is None  # SKU4 nie ma danych

    def test_with_fixtures(self):
        """Test z plikami fixtures."""
        from src.ingest.readers import read_file

        # Wczytaj masterdata
        md_df = read_file(FIXTURES_DIR / "masterdata_clean.csv")
        processed_md = process_masterdata(md_df)

        assert "volume_m3" in processed_md.columns
        assert "size_category" in processed_md.columns
        assert len(processed_md) > 0

        # Wczytaj orders
        orders_df = read_file(FIXTURES_DIR / "orders_clean.csv")
        orders_result = process_orders(orders_df, processed_md)

        assert orders_result.total_orders > 0
        assert orders_result.total_lines > 0
