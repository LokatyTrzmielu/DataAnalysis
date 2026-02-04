"""Testy jednostkowe dla modulu reporting."""

import tempfile
from pathlib import Path

import polars as pl
import pytest

from src.reporting.csv_writer import CSVWriter, write_csv
from src.reporting.dq_reports import DQReportGenerator
from src.quality.dq_metrics import DataQualityMetrics, FieldCoverage
from src.quality.dq_lists import DQLists, DQListItem


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ============================================================================
# Testy CSVWriter
# ============================================================================


class TestCSVWriter:
    """Testy dla CSVWriter."""

    def test_write_basic(self):
        """Test podstawowego zapisu CSV."""
        df = pl.DataFrame({
            "col1": ["a", "b", "c"],
            "col2": [1, 2, 3],
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            writer = CSVWriter(separator=";")
            result_path = writer.write(df, output_path)

            assert result_path.exists()

            # Sprawdz zawartosc
            with open(result_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

            assert "col1;col2" in content
            assert "a;1" in content

    def test_write_with_bom(self):
        """Test zapisu z BOM."""
        df = pl.DataFrame({"col": ["value"]})

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            writer = CSVWriter(encoding="utf-8-sig")
            writer.write(df, output_path)

            # Sprawdz BOM
            with open(output_path, "rb") as f:
                first_bytes = f.read(3)

            assert first_bytes == b"\xef\xbb\xbf"

    def test_write_creates_parent_dirs(self):
        """Test tworzenia katalogow nadrzednych."""
        df = pl.DataFrame({"col": ["value"]})

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "test.csv"
            writer = CSVWriter()
            result_path = writer.write(df, output_path)

            assert result_path.exists()

    def test_write_key_value(self):
        """Test zapisu w formacie Key-Value."""
        data = [
            ("Section1", "Metric1", 100),
            ("Section1", "Metric2", 200),
            ("Section2", "Metric3", 300),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.csv"
            writer = CSVWriter()
            result_path = writer.write_key_value(data, output_path)

            assert result_path.exists()

            # Sprawdz zawartosc
            with open(result_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

            assert "Section;Metric;Value" in content
            assert "Section1;Metric1;100" in content

    def test_write_csv_helper(self):
        """Test funkcji pomocniczej write_csv."""
        df = pl.DataFrame({"col": ["a", "b"]})

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            result_path = write_csv(df, output_path)

            assert result_path.exists()


# ============================================================================
# Testy DQReportGenerator
# ============================================================================


class TestDQReportGenerator:
    """Testy dla DQReportGenerator."""

    def get_test_metrics(self) -> DataQualityMetrics:
        """Pobierz testowe metryki."""
        return DataQualityMetrics(
            total_records=100,
            unique_sku_count=95,
            sku_coverage=FieldCoverage(
                field_name="sku",
                total_records=100,
                non_null_count=100,
                null_count=0,
                zero_count=0,
                negative_count=0,
                valid_count=100,
                coverage_pct=100.0,
            ),
            length_coverage=FieldCoverage(
                field_name="length_mm",
                total_records=100,
                non_null_count=90,
                null_count=5,
                zero_count=3,
                negative_count=2,
                valid_count=85,
                coverage_pct=85.0,
            ),
            width_coverage=FieldCoverage(
                field_name="width_mm",
                total_records=100,
                non_null_count=92,
                null_count=4,
                zero_count=2,
                negative_count=2,
                valid_count=88,
                coverage_pct=88.0,
            ),
            height_coverage=FieldCoverage(
                field_name="height_mm",
                total_records=100,
                non_null_count=95,
                null_count=3,
                zero_count=1,
                negative_count=1,
                valid_count=93,
                coverage_pct=93.0,
            ),
            weight_coverage=FieldCoverage(
                field_name="weight_kg",
                total_records=100,
                non_null_count=97,
                null_count=2,
                zero_count=1,
                negative_count=0,
                valid_count=96,
                coverage_pct=96.0,
            ),
            dimensions_coverage_pct=80.0,
            weight_coverage_pct=96.0,
            stock_coverage_pct=100.0,
            complete_records=75,
            partial_records=20,
            empty_records=5,
        )

    def get_test_dq_lists(self) -> DQLists:
        """Pobierz testowe listy DQ."""
        return DQLists(
            missing_critical=[
                DQListItem(sku="SKU1", issue_type="missing", field="length_mm", value="NULL"),
                DQListItem(sku="SKU2", issue_type="missing", field="weight_kg", value="0"),
            ],
            suspect_outliers=[
                DQListItem(sku="SKU3", issue_type="outlier", field="length_mm", value="5000", details="Very large"),
            ],
            high_risk_borderline=[
                DQListItem(sku="SKU4", issue_type="borderline", field="length_mm", value="598", details="Near limit"),
            ],
            duplicates=[
                DQListItem(sku="SKU5", issue_type="duplicate", field="sku", value="2", details="Appears 2 times"),
            ],
            conflicts=[
                DQListItem(sku="SKU5", issue_type="conflict", field="length_mm", value="[100, 150]", details="Different values"),
            ],
            collisions=[],
        )

    def test_generate_summary(self):
        """Test generowania DQ_Summary.csv."""
        generator = DQReportGenerator()
        metrics = self.get_test_metrics()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "DQ_Summary.csv"
            result_path = generator.generate_summary(output_path, metrics)

            assert result_path.exists()

            with open(result_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

            assert "Total Records" in content
            assert "100" in content
            assert "Dimensions Coverage %" in content

    def test_generate_missing_critical(self):
        """Test generowania DQ_MissingCritical.csv."""
        generator = DQReportGenerator()
        dq_lists = self.get_test_dq_lists()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "DQ_MissingCritical.csv"
            result_path = generator.generate_missing_critical(output_path, dq_lists)

            assert result_path.exists()

            with open(result_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

            assert "SKU1" in content
            assert "length_mm" in content

    def test_generate_missing_critical_empty(self):
        """Test generowania pustego raportu."""
        generator = DQReportGenerator()
        empty_lists = DQLists()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "DQ_MissingCritical.csv"
            result_path = generator.generate_missing_critical(output_path, empty_lists)

            assert result_path.exists()

            # Powinien miec tylko naglowek
            with open(result_path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()

            assert len(lines) == 1  # tylko naglowek

    def test_generate_suspect_outliers(self):
        """Test generowania DQ_SuspectOutliers.csv."""
        generator = DQReportGenerator()
        dq_lists = self.get_test_dq_lists()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "DQ_SuspectOutliers.csv"
            result_path = generator.generate_suspect_outliers(output_path, dq_lists)

            assert result_path.exists()

            with open(result_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

            assert "SKU3" in content
            assert "5000" in content

    def test_generate_duplicates(self):
        """Test generowania DQ_Masterdata_Duplicates.csv."""
        generator = DQReportGenerator()
        dq_lists = self.get_test_dq_lists()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "DQ_Duplicates.csv"
            result_path = generator.generate_duplicates(output_path, dq_lists)

            assert result_path.exists()

            with open(result_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

            assert "SKU5" in content

    def test_generate_imputed_skus(self):
        """Test generowania DQ_ImputedSKUs.csv."""
        generator = DQReportGenerator()

        # DataFrame z flagami ESTIMATED
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 200.0, 300.0],
            "width_mm": [50.0, 60.0, 70.0],
            "height_mm": [30.0, 40.0, 50.0],
            "weight_kg": [1.5, 2.5, 3.5],
            "stock_qty": [10, 20, 30],
            "length_flag": ["MEASURED", "ESTIMATED", "MEASURED"],
            "width_flag": ["MEASURED", "MEASURED", "MEASURED"],
            "height_flag": ["ESTIMATED", "MEASURED", "MEASURED"],
            "weight_flag": ["MEASURED", "ESTIMATED", "MEASURED"],
            "stock_flag": ["MEASURED", "MEASURED", "MEASURED"],
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "DQ_ImputedSKUs.csv"
            result_path = generator.generate_imputed_skus(output_path, df)

            assert result_path.exists()

            with open(result_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

            # SKU1 ma ESTIMATED dla height
            assert "SKU1" in content
            assert "height_mm" in content

            # SKU2 ma ESTIMATED dla length i weight
            assert "SKU2" in content
            assert "length_mm" in content
            assert "weight_kg" in content

            # SKU3 nie ma ESTIMATED - nie powinno byc w raporcie
            lines = content.strip().split("\n")
            assert len(lines) == 3  # header + 2 SKU (SKU1, SKU2)

    def test_generate_imputed_skus_empty(self):
        """Test pustego raportu gdy brak imputowanych wartosci."""
        generator = DQReportGenerator()

        # DataFrame bez flag ESTIMATED
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [100.0, 200.0],
            "length_flag": ["MEASURED", "MEASURED"],
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "DQ_ImputedSKUs.csv"
            result_path = generator.generate_imputed_skus(output_path, df)

            assert result_path.exists()

            with open(result_path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()

            # Tylko naglowek
            assert len(lines) == 1

    def test_generate_imputed_skus_no_flags(self):
        """Test gdy DataFrame nie ma kolumn flag."""
        generator = DQReportGenerator()

        # DataFrame bez kolumn flag
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [100.0, 200.0],
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "DQ_ImputedSKUs.csv"
            result_path = generator.generate_imputed_skus(output_path, df)

            assert result_path.exists()

            with open(result_path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()

            # Tylko naglowek - pusty raport
            assert len(lines) == 1

    def test_generate_all(self):
        """Test generowania wszystkich raportow DQ."""
        generator = DQReportGenerator()
        metrics = self.get_test_metrics()
        dq_lists = self.get_test_dq_lists()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            paths = generator.generate_all(output_dir, metrics, dq_lists)

            # Bez df - 7 raportow
            assert len(paths) == 7
            assert all(p.exists() for p in paths)

            # Sprawdz nazwy plikow
            filenames = [p.name for p in paths]
            assert "DQ_Summary.csv" in filenames
            assert "DQ_MissingCritical.csv" in filenames
            assert "DQ_SuspectOutliers.csv" in filenames

    def test_generate_all_with_df(self):
        """Test generowania wszystkich raportow DQ z raportem ImputedSKUs."""
        generator = DQReportGenerator()
        metrics = self.get_test_metrics()
        dq_lists = self.get_test_dq_lists()

        # DataFrame z flagami
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [100.0, 200.0],
            "width_mm": [50.0, 60.0],
            "height_mm": [30.0, 40.0],
            "weight_kg": [1.5, 2.5],
            "stock_qty": [10, 20],
            "length_flag": ["MEASURED", "ESTIMATED"],
            "width_flag": ["MEASURED", "MEASURED"],
            "height_flag": ["MEASURED", "MEASURED"],
            "weight_flag": ["MEASURED", "MEASURED"],
            "stock_flag": ["MEASURED", "MEASURED"],
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            paths = generator.generate_all(output_dir, metrics, dq_lists, df=df)

            # Z df - 8 raportow
            assert len(paths) == 8
            assert all(p.exists() for p in paths)

            # Sprawdz nazwy plikow
            filenames = [p.name for p in paths]
            assert "DQ_Summary.csv" in filenames
            assert "DQ_ImputedSKUs.csv" in filenames


# ============================================================================
# Testy integracyjne
# ============================================================================


class TestReportingIntegration:
    """Testy integracyjne dla modulu reporting."""

    def test_full_reporting_pipeline(self):
        """Test pelnego pipeline'u raportowania."""
        from src.quality.dq_metrics import calculate_dq_metrics
        from src.quality.dq_lists import build_dq_lists

        # Dane testowe
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3", "SKU4", "SKU1"],
            "length_mm": [100.0, None, 0.0, 5000.0, 100.0],
            "width_mm": [50.0, 100.0, 150.0, 200.0, 50.0],
            "height_mm": [30.0, 60.0, 90.0, 120.0, 30.0],
            "weight_kg": [1.5, 3.0, 4.5, 6.0, 1.5],
            "stock_qty": [10, 20, 30, 40, 10],
        })

        # Oblicz metryki i listy
        metrics = calculate_dq_metrics(df)
        dq_lists = build_dq_lists(df)

        # Generuj raporty
        generator = DQReportGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            paths = generator.generate_all(output_dir, metrics, dq_lists)

            # Sprawdz wszystkie pliki
            assert len(paths) == 7
            assert all(p.exists() for p in paths)

            # Sprawdz summary
            summary_path = output_dir / "DQ_Summary.csv"
            with open(summary_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

            assert "Total Records" in content
            assert "5" in content  # 5 wierszy
