"""Imputation of missing values with RAW/ESTIMATED flags."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import polars as pl

from src.core.types import DataQualityFlag


class ImputationMethod(str, Enum):
    """Imputation method."""
    MEDIAN = "median"
    MEAN = "mean"
    MODE = "mode"


class ImputationScope(str, Enum):
    """Imputation scope."""
    GLOBAL = "global"  # Global median/mean
    PER_CATEGORY = "per_category"  # Per category (if available)


@dataclass
class ImputationStats:
    """Imputation statistics for a field."""
    field_name: str
    original_missing: int
    imputed_count: int
    imputation_value: float
    method: ImputationMethod


@dataclass
class ImputationResult:
    """Imputation result."""
    df: pl.DataFrame
    stats: list[ImputationStats] = field(default_factory=list)
    total_imputed: int = 0
    total_records: int = 0

    @property
    def imputation_rate(self) -> float:
        """Percentage of imputed records."""
        if self.total_records == 0:
            return 0.0
        return (self.total_imputed / self.total_records) * 100


class Imputer:
    """Missing values imputation."""

    # Fields for imputation with their flags
    IMPUTABLE_FIELDS = {
        "length_mm": "length_flag",
        "width_mm": "width_flag",
        "height_mm": "height_flag",
        "weight_kg": "weight_flag",
        "stock_qty": "stock_flag",
    }

    def __init__(
        self,
        method: ImputationMethod = ImputationMethod.MEDIAN,
        scope: ImputationScope = ImputationScope.GLOBAL,
        treat_zero_as_missing: bool = True,
    ) -> None:
        """Initialize imputer.

        Args:
            method: Imputation method
            scope: Imputation scope
            treat_zero_as_missing: Whether to treat 0 as missing
        """
        self.method = method
        self.scope = scope
        self.treat_zero_as_missing = treat_zero_as_missing

    def impute(
        self,
        df: pl.DataFrame,
        fields: Optional[list[str]] = None,
    ) -> ImputationResult:
        """Perform imputation of missing values.

        Args:
            df: DataFrame with data
            fields: List of fields to impute (None = all available)

        Returns:
            ImputationResult with data and statistics
        """
        if fields is None:
            fields = [f for f in self.IMPUTABLE_FIELDS.keys() if f in df.columns]

        result_df = df
        stats: list[ImputationStats] = []
        total_imputed = 0

        for field_name in fields:
            if field_name not in result_df.columns:
                continue

            flag_name = self.IMPUTABLE_FIELDS.get(field_name)
            if flag_name is None:
                continue

            # Add flag column if it doesn't exist
            if flag_name not in result_df.columns:
                result_df = result_df.with_columns([
                    pl.lit(DataQualityFlag.RAW.value).alias(flag_name)
                ])

            # Perform imputation
            result_df, stat = self._impute_field(result_df, field_name, flag_name)
            if stat:
                stats.append(stat)
                total_imputed += stat.imputed_count

        return ImputationResult(
            df=result_df,
            stats=stats,
            total_imputed=total_imputed,
            total_records=len(df),
        )

    def _impute_field(
        self,
        df: pl.DataFrame,
        field_name: str,
        flag_name: str,
    ) -> tuple[pl.DataFrame, Optional[ImputationStats]]:
        """Impute single field."""
        # Determine missing mask
        if self.treat_zero_as_missing:
            missing_mask = pl.col(field_name).is_null() | (pl.col(field_name) <= 0)
        else:
            missing_mask = pl.col(field_name).is_null()

        # Count missing
        missing_count = df.filter(missing_mask).height
        if missing_count == 0:
            return df, None

        # Calculate imputation value
        valid_values = df.filter(~missing_mask)[field_name]
        if valid_values.len() == 0:
            return df, None

        imputation_value = self._calculate_imputation_value(valid_values)

        # Apply imputation
        result_df = df.with_columns([
            pl.when(missing_mask)
            .then(imputation_value)
            .otherwise(pl.col(field_name))
            .alias(field_name),

            pl.when(missing_mask)
            .then(pl.lit(DataQualityFlag.ESTIMATED.value))
            .otherwise(pl.col(flag_name))
            .alias(flag_name),
        ])

        stat = ImputationStats(
            field_name=field_name,
            original_missing=missing_count,
            imputed_count=missing_count,
            imputation_value=imputation_value,
            method=self.method,
        )

        return result_df, stat

    def _calculate_imputation_value(self, values: pl.Series) -> float:
        """Calculate value for imputation."""

        def to_float(val: object) -> float:
            """Convert polars scalar to float safely."""
            if val is None:
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            # For other numeric types, try conversion
            try:
                return float(val)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return 0.0

        if self.method == ImputationMethod.MEDIAN:
            return to_float(values.median())
        elif self.method == ImputationMethod.MEAN:
            return to_float(values.mean())
        elif self.method == ImputationMethod.MODE:
            mode = values.mode()
            if len(mode) > 0:
                return to_float(mode[0])
            return to_float(values.median())
        else:
            return to_float(values.median())


def impute_missing(
    df: pl.DataFrame,
    method: ImputationMethod = ImputationMethod.MEDIAN,
    fields: Optional[list[str]] = None,
) -> ImputationResult:
    """Helper function for imputation.

    Args:
        df: DataFrame with data
        method: Imputation method
        fields: List of fields to impute

    Returns:
        ImputationResult
    """
    imputer = Imputer(method=method)
    return imputer.impute(df, fields)
