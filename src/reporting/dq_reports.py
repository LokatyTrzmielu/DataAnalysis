"""Generowanie raportow Data Quality."""

from pathlib import Path

import polars as pl

from src.quality.dq_metrics import DataQualityMetrics
from src.quality.dq_lists import DQLists
from src.reporting.csv_writer import CSVWriter


class DQReportGenerator:
    """Generator raportow Data Quality."""

    def __init__(self) -> None:
        """Inicjalizacja generatora."""
        self.writer = CSVWriter()

    def generate_summary(
        self,
        output_path: Path,
        metrics: DataQualityMetrics,
    ) -> Path:
        """Generuj DQ_Summary.csv."""
        data = [
            ("Overview", "Total Records", metrics.total_records),
            ("Overview", "Unique SKU", metrics.unique_sku_count),
            ("Coverage", "Dimensions Coverage %", f"{metrics.dimensions_coverage_pct:.2f}"),
            ("Coverage", "Weight Coverage %", f"{metrics.weight_coverage_pct:.2f}"),
            ("Coverage", "Stock Coverage %", f"{metrics.stock_coverage_pct:.2f}"),
            ("Completeness", "Complete Records", metrics.complete_records),
            ("Completeness", "Partial Records", metrics.partial_records),
            ("Completeness", "Empty Records", metrics.empty_records),
        ]

        # Szczegoly per pole
        for coverage in [
            metrics.length_coverage,
            metrics.width_coverage,
            metrics.height_coverage,
            metrics.weight_coverage,
        ]:
            data.append((f"Field: {coverage.field_name}", "Valid Count", coverage.valid_count))
            data.append((f"Field: {coverage.field_name}", "Null Count", coverage.null_count))
            data.append((f"Field: {coverage.field_name}", "Zero Count", coverage.zero_count))
            data.append((f"Field: {coverage.field_name}", "Coverage %", f"{coverage.coverage_pct:.2f}"))

        return self.writer.write_key_value(data, output_path)

    def generate_missing_critical(
        self,
        output_path: Path,
        dq_lists: DQLists,
    ) -> Path:
        """Generuj DQ_MissingCritical.csv."""
        if not dq_lists.missing_critical:
            # Pusty plik z naglowkiem
            df = pl.DataFrame({
                "sku": [],
                "field": [],
                "value": [],
                "details": [],
            })
        else:
            df = pl.DataFrame({
                "sku": [i.sku for i in dq_lists.missing_critical],
                "field": [i.field for i in dq_lists.missing_critical],
                "value": [i.value or "" for i in dq_lists.missing_critical],
                "details": [i.details or "" for i in dq_lists.missing_critical],
            })

        return self.writer.write(df, output_path)

    def generate_suspect_outliers(
        self,
        output_path: Path,
        dq_lists: DQLists,
    ) -> Path:
        """Generuj DQ_SuspectOutliers.csv."""
        if not dq_lists.suspect_outliers:
            df = pl.DataFrame({
                "sku": [],
                "field": [],
                "value": [],
                "details": [],
            })
        else:
            df = pl.DataFrame({
                "sku": [i.sku for i in dq_lists.suspect_outliers],
                "field": [i.field for i in dq_lists.suspect_outliers],
                "value": [i.value or "" for i in dq_lists.suspect_outliers],
                "details": [i.details or "" for i in dq_lists.suspect_outliers],
            })

        return self.writer.write(df, output_path)

    def generate_high_risk_borderline(
        self,
        output_path: Path,
        dq_lists: DQLists,
    ) -> Path:
        """Generuj DQ_HighRiskBorderline.csv."""
        if not dq_lists.high_risk_borderline:
            df = pl.DataFrame({
                "sku": [],
                "field": [],
                "value": [],
                "details": [],
            })
        else:
            df = pl.DataFrame({
                "sku": [i.sku for i in dq_lists.high_risk_borderline],
                "field": [i.field for i in dq_lists.high_risk_borderline],
                "value": [i.value or "" for i in dq_lists.high_risk_borderline],
                "details": [i.details or "" for i in dq_lists.high_risk_borderline],
            })

        return self.writer.write(df, output_path)

    def generate_duplicates(
        self,
        output_path: Path,
        dq_lists: DQLists,
    ) -> Path:
        """Generuj DQ_Masterdata_Duplicates.csv."""
        if not dq_lists.duplicates:
            df = pl.DataFrame({
                "sku": [],
                "count": [],
                "details": [],
            })
        else:
            df = pl.DataFrame({
                "sku": [i.sku for i in dq_lists.duplicates],
                "count": [i.value or "" for i in dq_lists.duplicates],
                "details": [i.details or "" for i in dq_lists.duplicates],
            })

        return self.writer.write(df, output_path)

    def generate_conflicts(
        self,
        output_path: Path,
        dq_lists: DQLists,
    ) -> Path:
        """Generuj DQ_Masterdata_Conflicts.csv."""
        if not dq_lists.conflicts:
            df = pl.DataFrame({
                "sku": [],
                "field": [],
                "values": [],
                "details": [],
            })
        else:
            df = pl.DataFrame({
                "sku": [i.sku for i in dq_lists.conflicts],
                "field": [i.field for i in dq_lists.conflicts],
                "values": [i.value or "" for i in dq_lists.conflicts],
                "details": [i.details or "" for i in dq_lists.conflicts],
            })

        return self.writer.write(df, output_path)

    def generate_collisions(
        self,
        output_path: Path,
        dq_lists: DQLists,
    ) -> Path:
        """Generuj DQ_SKU_Collisions.csv."""
        if not dq_lists.collisions:
            df = pl.DataFrame({
                "normalized_sku": [],
                "original_skus": [],
                "collision_type": [],
            })
        else:
            df = pl.DataFrame({
                "normalized_sku": [i.sku for i in dq_lists.collisions],
                "original_skus": [i.value or "" for i in dq_lists.collisions],
                "collision_type": [i.details or "" for i in dq_lists.collisions],
            })

        return self.writer.write(df, output_path)

    def generate_all(
        self,
        output_dir: Path,
        metrics: DataQualityMetrics,
        dq_lists: DQLists,
    ) -> list[Path]:
        """Generuj wszystkie raporty DQ.

        Args:
            output_dir: Katalog wynikowy
            metrics: Metryki jakosci
            dq_lists: Listy problemow

        Returns:
            Lista sciezek do wygenerowanych plikow
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        paths = [
            self.generate_summary(output_dir / "DQ_Summary.csv", metrics),
            self.generate_missing_critical(output_dir / "DQ_MissingCritical.csv", dq_lists),
            self.generate_suspect_outliers(output_dir / "DQ_SuspectOutliers.csv", dq_lists),
            self.generate_high_risk_borderline(output_dir / "DQ_HighRiskBorderline.csv", dq_lists),
            self.generate_duplicates(output_dir / "DQ_Masterdata_Duplicates.csv", dq_lists),
            self.generate_conflicts(output_dir / "DQ_Masterdata_Conflicts.csv", dq_lists),
            self.generate_collisions(output_dir / "DQ_SKU_Collisions.csv", dq_lists),
        ]

        return paths
