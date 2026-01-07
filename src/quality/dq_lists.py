"""Problematic SKU lists for DQ reports."""

from dataclasses import dataclass, field
from typing import Optional

import polars as pl

from src.core.config import BORDERLINE_THRESHOLD_MM, OUTLIER_THRESHOLDS


@dataclass
class DQListItem:
    """DQ list item."""
    sku: str
    issue_type: str
    field: str
    value: Optional[str] = None
    details: Optional[str] = None


@dataclass
class DQLists:
    """Collection of problematic SKU lists."""
    missing_critical: list[DQListItem] = field(default_factory=list)
    suspect_outliers: list[DQListItem] = field(default_factory=list)
    high_risk_borderline: list[DQListItem] = field(default_factory=list)
    duplicates: list[DQListItem] = field(default_factory=list)
    conflicts: list[DQListItem] = field(default_factory=list)
    collisions: list[DQListItem] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        """Total number of issues."""
        return (
            len(self.missing_critical) +
            len(self.suspect_outliers) +
            len(self.high_risk_borderline) +
            len(self.duplicates) +
            len(self.conflicts) +
            len(self.collisions)
        )


class DQListBuilder:
    """Builder for DQ lists."""

    def __init__(
        self,
        borderline_threshold_mm: float = BORDERLINE_THRESHOLD_MM,
        outlier_thresholds: dict | None = None,
        enable_outlier_detection: bool = True,
    ) -> None:
        """Initialize builder."""
        self.borderline_threshold_mm = borderline_threshold_mm
        self.enable_outlier_detection = enable_outlier_detection
        # Use unified thresholds from config, converting min/max to low/high format
        if outlier_thresholds:
            self.outlier_thresholds = outlier_thresholds
        else:
            self.outlier_thresholds = {
                field: {"low": bounds["min"], "high": bounds["max"]}
                for field, bounds in OUTLIER_THRESHOLDS.items()
                if field != "stock_qty"  # stock_qty is not checked for outliers in DQ lists
            }

    def build_all_lists(
        self,
        df: pl.DataFrame,
        carrier_limits: Optional[dict[str, float]] = None,
    ) -> DQLists:
        """Build all DQ lists.

        Args:
            df: DataFrame with Masterdata
            carrier_limits: Carrier limits for borderline (optional)

        Returns:
            DQLists with all lists
        """
        return DQLists(
            missing_critical=self._find_missing_critical(df),
            suspect_outliers=self._find_suspect_outliers(df),
            high_risk_borderline=self._find_high_risk_borderline(df, carrier_limits),
            duplicates=self._find_duplicates(df),
            conflicts=self._find_conflicts(df),
            collisions=[],  # Collisions are detected in the ingest module
        )

    def _find_missing_critical(self, df: pl.DataFrame) -> list[DQListItem]:
        """Find SKUs with missing critical data."""
        items = []
        critical_fields = ["length_mm", "width_mm", "height_mm", "weight_kg"]

        for field in critical_fields:
            if field not in df.columns:
                continue

            # NULL lub <= 0
            missing_mask = pl.col(field).is_null() | (pl.col(field) <= 0)
            missing_rows = df.filter(missing_mask)

            for row in missing_rows.iter_rows(named=True):
                items.append(DQListItem(
                    sku=str(row["sku"]),
                    issue_type="missing_critical",
                    field=field,
                    value=str(row.get(field, "NULL")),
                    details=f"Missing critical value in {field}",
                ))

        return items

    def _find_suspect_outliers(self, df: pl.DataFrame) -> list[DQListItem]:
        """Find SKUs with suspicious values (outliers)."""
        items = []

        if not self.enable_outlier_detection:
            return items

        for field, thresholds in self.outlier_thresholds.items():
            if field not in df.columns:
                continue

            # Values outside range (but > 0)
            outlier_mask = (
                (pl.col(field) > 0) &
                ((pl.col(field) < thresholds["low"]) | (pl.col(field) > thresholds["high"]))
            )
            outlier_rows = df.filter(outlier_mask)

            for row in outlier_rows.iter_rows(named=True):
                value = row[field]
                if value < thresholds["low"]:
                    detail = f"Very small value: {value} < {thresholds['low']}"
                else:
                    detail = f"Very large value: {value} > {thresholds['high']}"

                items.append(DQListItem(
                    sku=str(row["sku"]),
                    issue_type="suspect_outlier",
                    field=field,
                    value=str(value),
                    details=detail,
                ))

        return items

    def _find_high_risk_borderline(
        self,
        df: pl.DataFrame,
        carrier_limits: Optional[dict[str, float]] = None,
    ) -> list[DQListItem]:
        """Find SKUs with dimensions close to carrier limits."""
        items = []

        if carrier_limits is None:
            # Default limits for a typical carrier
            carrier_limits = {
                "length_mm": 600,
                "width_mm": 400,
                "height_mm": 350,
            }

        for field, limit in carrier_limits.items():
            if field not in df.columns:
                continue

            # Values in range (limit - threshold, limit]
            lower_bound = limit - self.borderline_threshold_mm
            borderline_mask = (
                (pl.col(field) > lower_bound) &
                (pl.col(field) <= limit)
            )
            borderline_rows = df.filter(borderline_mask)

            for row in borderline_rows.iter_rows(named=True):
                value = row[field]
                margin = limit - value
                items.append(DQListItem(
                    sku=str(row["sku"]),
                    issue_type="high_risk_borderline",
                    field=field,
                    value=str(value),
                    details=f"Margin to limit: {margin:.1f}mm (limit: {limit}mm)",
                ))

        return items

    def _find_duplicates(self, df: pl.DataFrame) -> list[DQListItem]:
        """Find duplicate SKUs."""
        items = []

        if "sku" not in df.columns:
            return items

        # Group by SKU and find duplicates
        sku_counts = df.group_by("sku").agg(pl.len().alias("count"))
        duplicates = sku_counts.filter(pl.col("count") > 1)

        for row in duplicates.iter_rows(named=True):
            items.append(DQListItem(
                sku=str(row["sku"]),
                issue_type="duplicate",
                field="sku",
                value=str(row["count"]),
                details=f"SKU appears {row['count']} times",
            ))

        return items

    def _find_conflicts(self, df: pl.DataFrame) -> list[DQListItem]:
        """Find SKUs with conflicts (different values for the same SKU)."""
        items = []

        if "sku" not in df.columns:
            return items

        # Find SKUs with more than 1 occurrence
        sku_counts = df.group_by("sku").agg(pl.len().alias("count"))
        dup_skus = sku_counts.filter(pl.col("count") > 1)["sku"].to_list()

        if not dup_skus:
            return items

        # For each duplicate SKU check if values differ
        value_fields = ["length_mm", "width_mm", "height_mm", "weight_kg"]
        available_fields = [f for f in value_fields if f in df.columns]

        for sku in dup_skus:
            sku_rows = df.filter(pl.col("sku") == sku)

            for field in available_fields:
                unique_values = sku_rows[field].drop_nulls().unique().to_list()
                if len(unique_values) > 1:
                    items.append(DQListItem(
                        sku=str(sku),
                        issue_type="conflict",
                        field=field,
                        value=str(unique_values),
                        details=f"Different values for {field}: {unique_values}",
                    ))

        return items


def build_dq_lists(
    df: pl.DataFrame,
    carrier_limits: Optional[dict[str, float]] = None,
) -> DQLists:
    """Helper function to build DQ lists.

    Args:
        df: DataFrame with Masterdata
        carrier_limits: Carrier limits

    Returns:
        DQLists
    """
    builder = DQListBuilder()
    return builder.build_all_lists(df, carrier_limits)
