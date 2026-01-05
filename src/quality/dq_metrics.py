"""Data Quality Scorecard - data quality metrics."""

from dataclasses import dataclass, field
from typing import Optional

import polars as pl

from src.core.types import DQScorecard


@dataclass
class FieldCoverage:
    """Data coverage for a single field."""
    field_name: str
    total_records: int
    non_null_count: int
    null_count: int
    zero_count: int
    negative_count: int
    valid_count: int
    coverage_pct: float

    @property
    def missing_count(self) -> int:
        """Count of missing values (NULL + 0 + negative)."""
        return self.null_count + self.zero_count + self.negative_count


@dataclass
class DataQualityMetrics:
    """Complete data quality metrics."""
    total_records: int
    unique_sku_count: int

    # Field coverage
    sku_coverage: FieldCoverage
    length_coverage: FieldCoverage
    width_coverage: FieldCoverage
    height_coverage: FieldCoverage
    weight_coverage: FieldCoverage
    stock_coverage: Optional[FieldCoverage] = None

    # Aggregated metrics
    dimensions_coverage_pct: float = 0.0
    weight_coverage_pct: float = 0.0
    stock_coverage_pct: float = 0.0

    # Additional statistics
    complete_records: int = 0  # All fields populated
    partial_records: int = 0  # Some fields missing
    empty_records: int = 0    # All fields empty

    def to_scorecard(self) -> DQScorecard:
        """Convert to DQScorecard."""
        return DQScorecard(
            total_records=self.total_records,
            dimensions_coverage_pct=self.dimensions_coverage_pct,
            weight_coverage_pct=self.weight_coverage_pct,
            stock_coverage_pct=self.stock_coverage_pct,
        )


class DataQualityCalculator:
    """Data quality metrics calculator."""

    def __init__(
        self,
        treat_zero_as_missing: bool = True,
        treat_negative_as_missing: bool = True,
    ) -> None:
        """Initialize calculator."""
        self.treat_zero_as_missing = treat_zero_as_missing
        self.treat_negative_as_missing = treat_negative_as_missing

    def calculate(self, df: pl.DataFrame) -> DataQualityMetrics:
        """Calculate data quality metrics.

        Args:
            df: DataFrame with Masterdata

        Returns:
            DataQualityMetrics with calculated metrics
        """
        total = len(df)

        # SKU coverage
        sku_coverage = self._calculate_field_coverage(df, "sku", is_numeric=False)

        # Dimensions coverage
        length_coverage = self._calculate_field_coverage(df, "length_mm")
        width_coverage = self._calculate_field_coverage(df, "width_mm")
        height_coverage = self._calculate_field_coverage(df, "height_mm")

        # Weight coverage
        weight_coverage = self._calculate_field_coverage(df, "weight_kg")

        # Stock coverage (optional)
        stock_coverage = None
        if "stock_qty" in df.columns:
            stock_coverage = self._calculate_field_coverage(df, "stock_qty")

        # Aggregated metrics
        # Dimensions - all 3 must be present
        dim_valid = self._count_complete_dimensions(df)
        dimensions_coverage_pct = (dim_valid / total * 100) if total > 0 else 0.0

        weight_coverage_pct = weight_coverage.coverage_pct
        stock_coverage_pct = stock_coverage.coverage_pct if stock_coverage else 0.0

        # Complete/partial/empty records
        complete, partial, empty = self._count_record_completeness(df)

        # Unique SKU
        unique_sku = df["sku"].n_unique() if "sku" in df.columns else 0

        return DataQualityMetrics(
            total_records=total,
            unique_sku_count=unique_sku,
            sku_coverage=sku_coverage,
            length_coverage=length_coverage,
            width_coverage=width_coverage,
            height_coverage=height_coverage,
            weight_coverage=weight_coverage,
            stock_coverage=stock_coverage,
            dimensions_coverage_pct=dimensions_coverage_pct,
            weight_coverage_pct=weight_coverage_pct,
            stock_coverage_pct=stock_coverage_pct,
            complete_records=complete,
            partial_records=partial,
            empty_records=empty,
        )

    def _calculate_field_coverage(
        self,
        df: pl.DataFrame,
        field: str,
        is_numeric: bool = True,
    ) -> FieldCoverage:
        """Calculate coverage for a single field."""
        if field not in df.columns:
            return FieldCoverage(
                field_name=field,
                total_records=len(df),
                non_null_count=0,
                null_count=len(df),
                zero_count=0,
                negative_count=0,
                valid_count=0,
                coverage_pct=0.0,
            )

        total = len(df)
        col = df[field]

        # NULL count
        null_count = col.null_count()
        non_null_count = total - null_count

        # Zero/negative counts (only for numeric)
        zero_count = 0
        negative_count = 0

        if is_numeric:
            zero_count = (col == 0).sum()
            negative_count = (col < 0).sum()

        # Valid count
        if is_numeric and self.treat_zero_as_missing:
            if self.treat_negative_as_missing:
                valid_count = (col > 0).sum()
            else:
                valid_count = ((col != 0) & col.is_not_null()).sum()
        else:
            valid_count = non_null_count

        coverage_pct = (valid_count / total * 100) if total > 0 else 0.0

        return FieldCoverage(
            field_name=field,
            total_records=total,
            non_null_count=non_null_count,
            null_count=null_count,
            zero_count=zero_count,
            negative_count=negative_count,
            valid_count=valid_count,
            coverage_pct=coverage_pct,
        )

    def _count_complete_dimensions(self, df: pl.DataFrame) -> int:
        """Count records with complete dimensions."""
        dim_cols = ["length_mm", "width_mm", "height_mm"]
        if not all(c in df.columns for c in dim_cols):
            return 0

        if self.treat_zero_as_missing:
            mask = (
                (pl.col("length_mm") > 0) &
                (pl.col("width_mm") > 0) &
                (pl.col("height_mm") > 0)
            )
        else:
            mask = (
                pl.col("length_mm").is_not_null() &
                pl.col("width_mm").is_not_null() &
                pl.col("height_mm").is_not_null()
            )

        return df.filter(mask).height

    def _count_record_completeness(self, df: pl.DataFrame) -> tuple[int, int, int]:
        """Count complete/partial/empty records.

        Returns:
            (complete, partial, empty)
        """
        required_fields = ["length_mm", "width_mm", "height_mm", "weight_kg"]
        available_fields = [f for f in required_fields if f in df.columns]

        if not available_fields:
            return 0, 0, len(df)

        # Add column with valid field count
        valid_count_expr = pl.lit(0)
        for field in available_fields:
            if self.treat_zero_as_missing:
                valid_count_expr = valid_count_expr + (pl.col(field) > 0).cast(pl.Int32)
            else:
                valid_count_expr = valid_count_expr + pl.col(field).is_not_null().cast(pl.Int32)

        df_with_count = df.with_columns([
            valid_count_expr.alias("_valid_count")
        ])

        total_fields = len(available_fields)
        complete = df_with_count.filter(pl.col("_valid_count") == total_fields).height
        empty = df_with_count.filter(pl.col("_valid_count") == 0).height
        partial = len(df) - complete - empty

        return complete, partial, empty


def calculate_dq_metrics(df: pl.DataFrame) -> DataQualityMetrics:
    """Helper function to calculate DQ metrics.

    Args:
        df: DataFrame with Masterdata

    Returns:
        DataQualityMetrics
    """
    calculator = DataQualityCalculator()
    return calculator.calculate(df)
