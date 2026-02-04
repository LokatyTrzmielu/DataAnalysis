"""Generate Data Quality reports."""

from pathlib import Path

import polars as pl

from src.quality.dq_metrics import DataQualityMetrics
from src.quality.dq_lists import DQLists
from src.reporting.csv_writer import CSVWriter


class DQReportGenerator:
    """Data Quality reports generator."""

    def __init__(self) -> None:
        """Initialize the generator."""
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

        # Details per field
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
            # Empty file with header
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

    def generate_imputed_skus(
        self,
        output_path: Path,
        df: pl.DataFrame,
    ) -> Path:
        """Generuj DQ_ImputedSKUs.csv.

        Lista SKU z imputowanymi (uzupełnionymi) wartościami.

        Args:
            output_path: Output file path
            df: DataFrame with flag columns

        Returns:
            Path to generated file
        """
        flag_columns = {
            "length_flag": "length_mm",
            "width_flag": "width_mm",
            "height_flag": "height_mm",
            "weight_flag": "weight_kg",
            "stock_flag": "stock_qty",
        }

        # Check if flag columns exist
        existing_flags = [col for col in flag_columns if col in df.columns]

        if not existing_flags:
            # No flag columns - empty report
            result_df = pl.DataFrame({
                "sku": [],
                "imputed_fields": [],
                "length_mm": [],
                "width_mm": [],
                "height_mm": [],
                "weight_kg": [],
                "stock_qty": [],
            })
            return self.writer.write(result_df, output_path)

        # Build filter: any flag = "ESTIMATED"
        filter_expr = pl.lit(False)
        for flag_col in existing_flags:
            filter_expr = filter_expr | (pl.col(flag_col) == "ESTIMATED")

        imputed_df = df.filter(filter_expr)

        if imputed_df.is_empty():
            result_df = pl.DataFrame({
                "sku": [],
                "imputed_fields": [],
                "length_mm": [],
                "width_mm": [],
                "height_mm": [],
                "weight_kg": [],
                "stock_qty": [],
            })
            return self.writer.write(result_df, output_path)

        # Build imputed_fields string for each row
        rows = []
        for row in imputed_df.iter_rows(named=True):
            imputed_fields = []
            for flag_col, value_col in flag_columns.items():
                if flag_col in row and row[flag_col] == "ESTIMATED":
                    imputed_fields.append(value_col)

            rows.append({
                "sku": row.get("sku", ""),
                "imputed_fields": ", ".join(imputed_fields),
                "length_mm": row.get("length_mm"),
                "width_mm": row.get("width_mm"),
                "height_mm": row.get("height_mm"),
                "weight_kg": row.get("weight_kg"),
                "stock_qty": row.get("stock_qty"),
            })

        result_df = pl.DataFrame(rows)
        return self.writer.write(result_df, output_path)

    def generate_all(
        self,
        output_dir: Path,
        metrics: DataQualityMetrics,
        dq_lists: DQLists,
        df: pl.DataFrame | None = None,
    ) -> list[Path]:
        """Generate all DQ reports.

        Args:
            output_dir: Output directory
            metrics: Quality metrics
            dq_lists: Issue lists
            df: DataFrame with flag columns (for imputed SKUs report)

        Returns:
            List of paths to generated files
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

        # Add imputed SKUs report if DataFrame provided
        if df is not None:
            paths.append(
                self.generate_imputed_skus(output_dir / "DQ_ImputedSKUs.csv", df)
            )

        return paths
