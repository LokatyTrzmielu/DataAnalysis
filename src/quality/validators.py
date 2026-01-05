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
)


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

    # Thresholds for outliers
    OUTLIER_THRESHOLDS = {
        "length_mm": {"min": 1, "max": 3000},
        "width_mm": {"min": 1, "max": 3000},
        "height_mm": {"min": 1, "max": 2000},
        "weight_kg": {"min": 0.001, "max": 500},
        "stock_qty": {"min": 0, "max": 1_000_000},
    }

    # IQR multiplier for dynamic outliers
    IQR_MULTIPLIER = 3.0

    def __init__(
        self,
        treat_zero_as_missing_dimensions: bool = TREAT_ZERO_AS_MISSING_DIMENSIONS,
        treat_zero_as_missing_weight: bool = TREAT_ZERO_AS_MISSING_WEIGHT,
        treat_zero_as_missing_quantities: bool = TREAT_ZERO_AS_MISSING_QUANTITIES,
        treat_negative_as_missing: bool = TREAT_NEGATIVE_AS_MISSING,
    ) -> None:
        """Initialize validator."""
        self.treat_zero_as_missing_dimensions = treat_zero_as_missing_dimensions
        self.treat_zero_as_missing_weight = treat_zero_as_missing_weight
        self.treat_zero_as_missing_quantities = treat_zero_as_missing_quantities
        self.treat_negative_as_missing = treat_negative_as_missing

    def validate(self, df: pl.DataFrame) -> ValidationResult:
        """Perform data validation.

        Args:
            df: DataFrame with Masterdata

        Returns:
            ValidationResult with validation results
        """
        issues: list[ValidationIssue] = []
        df_work = df.clone()

        # 1. Validate missing values (NULL)
        issues.extend(self._validate_missing(df_work))

        # 2. Validate zeros
        issues.extend(self._validate_zeros(df_work))

        # 3. Validate negative values
        issues.extend(self._validate_negatives(df_work))

        # 4. Validate outliers
        issues.extend(self._validate_outliers(df_work))

        # 5. Mark values as missing
        df_validated = self._mark_as_missing(df_work)

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
        issues = []
        required_fields = ["sku", "length_mm", "width_mm", "height_mm", "weight_kg"]

        for field in required_fields:
            if field not in df.columns:
                continue

            null_mask = df[field].is_null()
            null_skus = df.filter(null_mask)["sku"].to_list()

            for sku in null_skus:
                severity = ValidationSeverity.CRITICAL if field == "sku" else ValidationSeverity.WARNING
                issues.append(ValidationIssue(
                    sku=str(sku),
                    field=field,
                    issue_type=ValidationIssueType.MISSING_VALUE,
                    severity=severity,
                    original_value=None,
                    message=f"Missing value in field {field}",
                ))

        return issues

    def _validate_zeros(self, df: pl.DataFrame) -> list[ValidationIssue]:
        """Validate zero values."""
        issues = []

        # Dimensions
        if self.treat_zero_as_missing_dimensions:
            for field in ["length_mm", "width_mm", "height_mm"]:
                if field not in df.columns:
                    continue
                zero_mask = pl.col(field) == 0
                zero_rows = df.filter(zero_mask)
                for row in zero_rows.iter_rows(named=True):
                    issues.append(ValidationIssue(
                        sku=str(row["sku"]),
                        field=field,
                        issue_type=ValidationIssueType.ZERO_VALUE,
                        severity=ValidationSeverity.WARNING,
                        original_value="0",
                        message=f"Zero in dimension {field} - treated as missing",
                    ))

        # Weight
        if self.treat_zero_as_missing_weight and "weight_kg" in df.columns:
            zero_mask = pl.col("weight_kg") == 0
            zero_rows = df.filter(zero_mask)
            for row in zero_rows.iter_rows(named=True):
                issues.append(ValidationIssue(
                    sku=str(row["sku"]),
                    field="weight_kg",
                    issue_type=ValidationIssueType.ZERO_VALUE,
                    severity=ValidationSeverity.WARNING,
                    original_value="0",
                    message="Zero in weight - treated as missing",
                ))

        # Stock
        if self.treat_zero_as_missing_quantities and "stock_qty" in df.columns:
            zero_mask = pl.col("stock_qty") == 0
            zero_rows = df.filter(zero_mask)
            for row in zero_rows.iter_rows(named=True):
                issues.append(ValidationIssue(
                    sku=str(row["sku"]),
                    field="stock_qty",
                    issue_type=ValidationIssueType.ZERO_VALUE,
                    severity=ValidationSeverity.INFO,
                    original_value="0",
                    message="Zero stock",
                ))

        return issues

    def _validate_negatives(self, df: pl.DataFrame) -> list[ValidationIssue]:
        """Validate negative values."""
        if not self.treat_negative_as_missing:
            return []

        issues = []
        numeric_fields = ["length_mm", "width_mm", "height_mm", "weight_kg", "stock_qty"]

        for field in numeric_fields:
            if field not in df.columns:
                continue

            neg_mask = pl.col(field) < 0
            neg_rows = df.filter(neg_mask)

            for row in neg_rows.iter_rows(named=True):
                issues.append(ValidationIssue(
                    sku=str(row["sku"]),
                    field=field,
                    issue_type=ValidationIssueType.NEGATIVE_VALUE,
                    severity=ValidationSeverity.WARNING,
                    original_value=str(row[field]),
                    message=f"Negative value in {field}",
                ))

        return issues

    def _validate_outliers(self, df: pl.DataFrame) -> list[ValidationIssue]:
        """Validate outliers (values outside range)."""
        issues = []

        for field, thresholds in self.OUTLIER_THRESHOLDS.items():
            if field not in df.columns:
                continue

            # Static thresholds
            outlier_mask = (
                (pl.col(field) < thresholds["min"]) |
                (pl.col(field) > thresholds["max"])
            ) & pl.col(field).is_not_null() & (pl.col(field) > 0)

            outlier_rows = df.filter(outlier_mask)

            for row in outlier_rows.iter_rows(named=True):
                issues.append(ValidationIssue(
                    sku=str(row["sku"]),
                    field=field,
                    issue_type=ValidationIssueType.OUTLIER,
                    severity=ValidationSeverity.WARNING,
                    original_value=str(row[field]),
                    message=f"Value {row[field]} outside range [{thresholds['min']}, {thresholds['max']}]",
                ))

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
