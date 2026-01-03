"""Data Quality Scorecard - metryki jakosci danych."""

from dataclasses import dataclass, field
from typing import Optional

import polars as pl

from src.core.types import DQScorecard


@dataclass
class FieldCoverage:
    """Pokrycie danych dla pojedynczego pola."""
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
        """Liczba brakujacych wartosci (NULL + 0 + ujemne)."""
        return self.null_count + self.zero_count + self.negative_count


@dataclass
class DataQualityMetrics:
    """Pelne metryki jakosci danych."""
    total_records: int
    unique_sku_count: int

    # Pokrycie pol
    sku_coverage: FieldCoverage
    length_coverage: FieldCoverage
    width_coverage: FieldCoverage
    height_coverage: FieldCoverage
    weight_coverage: FieldCoverage
    stock_coverage: Optional[FieldCoverage] = None

    # Zagregowane metryki
    dimensions_coverage_pct: float = 0.0
    weight_coverage_pct: float = 0.0
    stock_coverage_pct: float = 0.0

    # Dodatkowe statystyki
    complete_records: int = 0  # Wszystkie pola wypelnione
    partial_records: int = 0  # Czesc pol brakuje
    empty_records: int = 0    # Wszystkie pola puste

    def to_scorecard(self) -> DQScorecard:
        """Konwertuj do DQScorecard."""
        return DQScorecard(
            total_records=self.total_records,
            dimensions_coverage_pct=self.dimensions_coverage_pct,
            weight_coverage_pct=self.weight_coverage_pct,
            stock_coverage_pct=self.stock_coverage_pct,
        )


class DataQualityCalculator:
    """Kalkulator metryk jakosci danych."""

    def __init__(
        self,
        treat_zero_as_missing: bool = True,
        treat_negative_as_missing: bool = True,
    ) -> None:
        """Inicjalizacja kalkulatora."""
        self.treat_zero_as_missing = treat_zero_as_missing
        self.treat_negative_as_missing = treat_negative_as_missing

    def calculate(self, df: pl.DataFrame) -> DataQualityMetrics:
        """Oblicz metryki jakosci danych.

        Args:
            df: DataFrame z danymi Masterdata

        Returns:
            DataQualityMetrics z obliczonymi metrykami
        """
        total = len(df)

        # Pokrycie SKU
        sku_coverage = self._calculate_field_coverage(df, "sku", is_numeric=False)

        # Pokrycie wymiarow
        length_coverage = self._calculate_field_coverage(df, "length_mm")
        width_coverage = self._calculate_field_coverage(df, "width_mm")
        height_coverage = self._calculate_field_coverage(df, "height_mm")

        # Pokrycie wagi
        weight_coverage = self._calculate_field_coverage(df, "weight_kg")

        # Pokrycie stock (opcjonalne)
        stock_coverage = None
        if "stock_qty" in df.columns:
            stock_coverage = self._calculate_field_coverage(df, "stock_qty")

        # Zagregowane metryki
        # Wymiary - wszystkie 3 musza byc obecne
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
        """Oblicz pokrycie dla pojedynczego pola."""
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

        # Zero/negative counts (tylko dla numeric)
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
        """Policz rekordy z kompletnymi wymiarami."""
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
        """Policz rekordy complete/partial/empty.

        Returns:
            (complete, partial, empty)
        """
        required_fields = ["length_mm", "width_mm", "height_mm", "weight_kg"]
        available_fields = [f for f in required_fields if f in df.columns]

        if not available_fields:
            return 0, 0, len(df)

        # Dodaj kolumne z liczba valid pol
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
    """Funkcja pomocnicza do obliczenia metryk DQ.

    Args:
        df: DataFrame z danymi Masterdata

    Returns:
        DataQualityMetrics
    """
    calculator = DataQualityCalculator()
    return calculator.calculate(df)
