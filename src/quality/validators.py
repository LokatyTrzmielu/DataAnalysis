"""Masterdata validation rules."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import polars as pl

from src.core.config import (
    TREAT_ZERO_AS_MISSING_DIMENSIONS,
    TREAT_ZERO_AS_MISSING_WEIGHT,
    TREAT_ZERO_AS_MISSING_QUANTITIES,
    TREAT_NEGATIVE_AS_MISSING,
    OUTLIER_THRESHOLDS,
)
from src.core.types import CarrierConfig
from src.core.dimension_checker import DimensionChecker


class ValidationSeverity(str, Enum):
    """Issue severity level."""
    CRITICAL = "critical"  # Blocks analysis
    WARNING = "warning"    # Requires attention
    INFO = "info"          # Informational


class ValidationIssueType(str, Enum):
    """Validation issue type."""
    MISSING_VALUE = "missing_value"
    ZERO_VALUE = "zero_value"
    NEGATIVE_VALUE = "negative_value"
    OUTLIER = "outlier"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"
    INVALID_FORMAT = "invalid_format"


@dataclass
class ValidationIssue:
    """Single validation issue."""
    sku: str
    field: str
    issue_type: ValidationIssueType
    severity: ValidationSeverity
    original_value: Optional[str] = None
    message: Optional[str] = None


@dataclass
class ValidationResult:
    """Validation result."""
    is_valid: bool
    issues: list[ValidationIssue]
    df_validated: pl.DataFrame
    total_records: int
    valid_records: int
    critical_issues: int
    warning_issues: int


class MasterdataValidator:
    """Masterdata validator."""

    # IQR multiplier for dynamic outliers
    IQR_MULTIPLIER = 3.0

    def __init__(
        self,
        treat_zero_as_missing_dimensions: bool = TREAT_ZERO_AS_MISSING_DIMENSIONS,
        treat_zero_as_missing_weight: bool = TREAT_ZERO_AS_MISSING_WEIGHT,
        treat_zero_as_missing_quantities: bool = TREAT_ZERO_AS_MISSING_QUANTITIES,
        treat_negative_as_missing: bool = TREAT_NEGATIVE_AS_MISSING,
        enable_outlier_validation: bool = True,
        outlier_thresholds: dict | None = None,
        carriers: list[CarrierConfig] | None = None,
    ) -> None:
        """Initialize validator.

        Args:
            enable_outlier_validation: Whether to validate outliers
            outlier_thresholds: Custom thresholds dict, e.g.:
                {"length_mm": {"min": 1, "max": 3000}, ...}
            carriers: List of carrier configurations for rotation-aware
                dimensional outlier detection
        """
        self.treat_zero_as_missing_dimensions = treat_zero_as_missing_dimensions
        self.treat_zero_as_missing_weight = treat_zero_as_missing_weight
        self.treat_zero_as_missing_quantities = treat_zero_as_missing_quantities
        self.treat_negative_as_missing = treat_negative_as_missing
        self.enable_outlier_validation = enable_outlier_validation
        self.carriers = carriers

        # Merge custom thresholds with defaults from config
        self.outlier_thresholds = {k: v.copy() for k, v in OUTLIER_THRESHOLDS.items()}
        if outlier_thresholds:
            for field, bounds in outlier_thresholds.items():
                if field in self.outlier_thresholds:
                    self.outlier_thresholds[field].update(bounds)

    def validate(self, df: pl.DataFrame) -> ValidationResult:
        """Perform data validation.

        Args:
            df: DataFrame with Masterdata

        Returns:
            ValidationResult with validation results
        """
        issues: list[ValidationIssue] = []

        # 1. Validate missing values (NULL)
        issues.extend(self._validate_missing(df))

        # 2. Validate zeros
        issues.extend(self._validate_zeros(df))

        # 3. Validate negative values
        issues.extend(self._validate_negatives(df))

        # 4. Validate outliers
        issues.extend(self._validate_outliers(df))

        # 5. Mark values as missing
        df_validated = self._mark_as_missing(df)

        # Summary
        critical = sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL)
        warning = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)

        # Count valid records (without critical issues)
        critical_skus = {i.sku for i in issues if i.severity == ValidationSeverity.CRITICAL}
        valid_records = len(df) - len(critical_skus)

        return ValidationResult(
            is_valid=(critical == 0),
            issues=issues,
            df_validated=df_validated,
            total_records=len(df),
            valid_records=valid_records,
            critical_issues=critical,
            warning_issues=warning,
        )

    def _validate_missing(self, df: pl.DataFrame) -> list[ValidationIssue]:
        """Validate missing values (NULL)."""
        issues: list[ValidationIssue] = []
        required_fields = ["sku", "length_mm", "width_mm", "height_mm", "weight_kg"]

        for field in required_fields:
            if field not in df.columns:
                continue

            null_skus = df.filter(df[field].is_null()).select("sku").to_series().to_list()
            severity = ValidationSeverity.CRITICAL if field == "sku" else ValidationSeverity.WARNING

            issues.extend([
                ValidationIssue(
                    sku=str(sku),
                    field=field,
                    issue_type=ValidationIssueType.MISSING_VALUE,
                    severity=severity,
                    original_value=None,
                    message=f"Missing value in field {field}",
                )
                for sku in null_skus
            ])

        return issues

    def _validate_zeros(self, df: pl.DataFrame) -> list[ValidationIssue]:
        """Validate zero values."""
        issues: list[ValidationIssue] = []

        # Dimensions
        if self.treat_zero_as_missing_dimensions:
            for field in ["length_mm", "width_mm", "height_mm"]:
                if field not in df.columns:
                    continue
                zero_skus = df.filter(pl.col(field) == 0).select("sku").to_series().to_list()
                issues.extend([
                    ValidationIssue(
                        sku=str(sku),
                        field=field,
                        issue_type=ValidationIssueType.ZERO_VALUE,
                        severity=ValidationSeverity.WARNING,
                        original_value="0",
                        message=f"Zero in dimension {field} - treated as missing",
                    )
                    for sku in zero_skus
                ])

        # Weight
        if self.treat_zero_as_missing_weight and "weight_kg" in df.columns:
            zero_skus = df.filter(pl.col("weight_kg") == 0).select("sku").to_series().to_list()
            issues.extend([
                ValidationIssue(
                    sku=str(sku),
                    field="weight_kg",
                    issue_type=ValidationIssueType.ZERO_VALUE,
                    severity=ValidationSeverity.WARNING,
                    original_value="0",
                    message="Zero in weight - treated as missing",
                )
                for sku in zero_skus
            ])

        # Stock
        if self.treat_zero_as_missing_quantities and "stock_qty" in df.columns:
            zero_skus = df.filter(pl.col("stock_qty") == 0).select("sku").to_series().to_list()
            issues.extend([
                ValidationIssue(
                    sku=str(sku),
                    field="stock_qty",
                    issue_type=ValidationIssueType.ZERO_VALUE,
                    severity=ValidationSeverity.INFO,
                    original_value="0",
                    message="Zero stock",
                )
                for sku in zero_skus
            ])

        return issues

    def _validate_negatives(self, df: pl.DataFrame) -> list[ValidationIssue]:
        """Validate negative values."""
        if not self.treat_negative_as_missing:
            return []

        issues: list[ValidationIssue] = []
        numeric_fields = ["length_mm", "width_mm", "height_mm", "weight_kg", "stock_qty"]

        for field in numeric_fields:
            if field not in df.columns:
                continue

            neg_rows = df.filter(pl.col(field) < 0).select(["sku", field]).to_dicts()
            issues.extend([
                ValidationIssue(
                    sku=str(row["sku"]),
                    field=field,
                    issue_type=ValidationIssueType.NEGATIVE_VALUE,
                    severity=ValidationSeverity.WARNING,
                    original_value=str(row[field]),
                    message=f"Negative value in {field}",
                )
                for row in neg_rows
            ])

        return issues

    def _validate_outliers(self, df: pl.DataFrame) -> list[ValidationIssue]:
        """Validate outliers (values outside range).

        Uses two complementary validation methods:
        1. Static thresholds - ALWAYS applied for ALL fields (dimensions + weight)
        2. Rotation-aware carrier fit - ADDITIONALLY applied if carriers configured

        This ensures static thresholds are never bypassed, while still providing
        the rotation-aware check for items that don't fit any carrier.
        """
        issues: list[ValidationIssue] = []

        if not self.enable_outlier_validation:
            return issues

        # ALWAYS apply static thresholds for ALL fields
        for field, thresholds in self.outlier_thresholds.items():
            if field not in df.columns:
                continue
            issues.extend(self._validate_static_outliers(df, field, thresholds))

        # ADDITIONALLY check rotation-aware for dimensions (if carriers configured)
        if self.carriers:
            issues.extend(self._validate_dimensional_outliers_with_rotation(df))

        return issues

    def _validate_static_outliers(
        self, df: pl.DataFrame, field: str, thresholds: dict
    ) -> list[ValidationIssue]:
        """Validate outliers using static min/max thresholds."""
        issues: list[ValidationIssue] = []

        outlier_mask = (
            (pl.col(field) < thresholds["min"]) |
            (pl.col(field) > thresholds["max"])
        ) & pl.col(field).is_not_null() & (pl.col(field) > 0)

        outlier_rows = df.filter(outlier_mask).select(["sku", field]).to_dicts()
        min_val, max_val = thresholds["min"], thresholds["max"]

        issues.extend([
            ValidationIssue(
                sku=str(row["sku"]),
                field=field,
                issue_type=ValidationIssueType.OUTLIER,
                severity=ValidationSeverity.WARNING,
                original_value=str(row[field]),
                message=f"Value {row[field]} outside range [{min_val}, {max_val}]",
            )
            for row in outlier_rows
        ])

        return issues

    def _validate_dimensional_outliers_with_rotation(
        self, df: pl.DataFrame
    ) -> list[ValidationIssue]:
        """Validate dimensional outliers using rotation-aware carrier fit check.

        An item is a dimensional outlier only if it cannot fit in ANY active
        carrier with ANY of the 6 possible rotations.
        """
        issues: list[ValidationIssue] = []

        required_cols = ["sku", "length_mm", "width_mm", "height_mm"]
        if not all(c in df.columns for c in required_cols):
            return issues

        # Filter rows with valid positive dimensions
        valid_df = df.filter(
            (pl.col("length_mm") > 0)
            & (pl.col("width_mm") > 0)
            & (pl.col("height_mm") > 0)
        )

        # Track SKUs that are dimensional outliers
        checked_skus: set[str] = set()

        for row in valid_df.select(required_cols).to_dicts():
            sku = str(row["sku"])
            if sku in checked_skus:
                continue

            length = row["length_mm"]
            width = row["width_mm"]
            height = row["height_mm"]

            # Check if cannot fit any carrier with rotation
            if not DimensionChecker.can_fit_any_carrier(
                length, width, height, self.carriers
            ):
                max_carrier_dim = DimensionChecker.get_max_allowed_dimension(
                    self.carriers
                )
                max_item_dim = max(length, width, height)

                issues.append(
                    ValidationIssue(
                        sku=sku,
                        field="dimensions",
                        issue_type=ValidationIssueType.OUTLIER,
                        severity=ValidationSeverity.WARNING,
                        original_value=f"L={length}, W={width}, H={height}",
                        message=(
                            f"Cannot fit any carrier with rotation "
                            f"(max dimension {max_item_dim}mm > "
                            f"max carrier axis {max_carrier_dim}mm)"
                        ),
                    )
                )
                checked_skus.add(sku)

        return issues

    def _mark_as_missing(self, df: pl.DataFrame) -> pl.DataFrame:
        """Mark problematic values as NULL."""
        result = df.clone()

        # Dimensions - replace 0 and negative with NULL
        if self.treat_zero_as_missing_dimensions:
            for field in ["length_mm", "width_mm", "height_mm"]:
                if field in result.columns:
                    result = result.with_columns([
                        pl.when(pl.col(field) <= 0)
                        .then(None)
                        .otherwise(pl.col(field))
                        .alias(field)
                    ])

        # Weight
        if self.treat_zero_as_missing_weight and "weight_kg" in result.columns:
            result = result.with_columns([
                pl.when(pl.col("weight_kg") <= 0)
                .then(None)
                .otherwise(pl.col("weight_kg"))
                .alias("weight_kg")
            ])

        # Negative values in remaining fields
        if self.treat_negative_as_missing:
            for field in ["stock_qty"]:
                if field in result.columns:
                    result = result.with_columns([
                        pl.when(pl.col(field) < 0)
                        .then(None)
                        .otherwise(pl.col(field))
                        .alias(field)
                    ])

        return result
