"""Problematic SKU lists for DQ reports."""

from dataclasses import dataclass, field
from typing import Optional

import polars as pl

from src.core.config import BORDERLINE_THRESHOLD_MM
from src.core.types import CarrierConfig
from src.core.dimension_checker import DimensionChecker


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
        enable_outlier_detection: bool = True,
        carriers: list[CarrierConfig] | None = None,
    ) -> None:
        """Initialize builder.

        Args:
            borderline_threshold_mm: Threshold for borderline detection
            enable_outlier_detection: Whether to detect outliers
            carriers: List of carrier configurations for rotation-aware
                dimensional + weight outlier detection
        """
        self.borderline_threshold_mm = borderline_threshold_mm
        self.enable_outlier_detection = enable_outlier_detection
        self.carriers = carriers

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

    def build_validation_lists(self, df: pl.DataFrame) -> DQLists:
        """Build DQ lists for validation step (no outliers/borderline).

        This method is used in the validation pipeline where outlier and
        borderline detection is not performed (moved to capacity analysis).

        Args:
            df: DataFrame with Masterdata

        Returns:
            DQLists with missing_critical, duplicates, conflicts only
        """
        return DQLists(
            missing_critical=self._find_missing_critical(df),
            suspect_outliers=[],  # Handled in capacity analysis
            high_risk_borderline=[],  # Handled in capacity analysis
            duplicates=self._find_duplicates(df),
            conflicts=self._find_conflicts(df),
            collisions=[],
        )

    def build_capacity_lists(
        self,
        df: pl.DataFrame,
        carrier_limits: Optional[dict[str, float]] = None,
    ) -> DQLists:
        """Build DQ lists for capacity step (outliers and borderline only).

        This method is used in capacity analysis where outlier detection
        uses rotation-aware fitting with configured carriers.

        Args:
            df: DataFrame with Masterdata
            carrier_limits: Carrier limits for borderline detection

        Returns:
            DQLists with suspect_outliers and high_risk_borderline only
        """
        return DQLists(
            missing_critical=[],  # Handled in validation
            suspect_outliers=self._find_suspect_outliers(df),
            high_risk_borderline=self._find_high_risk_borderline(df, carrier_limits),
            duplicates=[],  # Handled in validation
            conflicts=[],  # Handled in validation
            collisions=[],
        )

    def _find_missing_critical(self, df: pl.DataFrame) -> list[DQListItem]:
        """Find SKUs with missing critical data."""
        items: list[DQListItem] = []
        critical_fields = ["length_mm", "width_mm", "height_mm", "weight_kg"]

        for field in critical_fields:
            if field not in df.columns:
                continue

            # NULL lub <= 0
            missing_mask = pl.col(field).is_null() | (pl.col(field) <= 0)
            missing_rows = df.filter(missing_mask).select(["sku", field]).to_dicts()

            items.extend([
                DQListItem(
                    sku=str(row["sku"]),
                    issue_type="missing_critical",
                    field=field,
                    value=str(row.get(field, "NULL")),
                    details=f"Missing critical value in {field}",
                )
                for row in missing_rows
            ])

        return items

    def _find_suspect_outliers(self, df: pl.DataFrame) -> list[DQListItem]:
        """Find outliers - items that don't fit any carrier (dimensions + weight).

        An outlier is an SKU that cannot fit in ANY active carrier considering:
        - Dimensions with all 6 possible rotations
        - Weight must be <= carrier max_weight_kg

        No static thresholds - carriers define the limits.
        """
        if not self.enable_outlier_detection or not self.carriers:
            return []

        return self._find_dimensional_outliers_with_rotation(df)

    def _find_dimensional_outliers_with_rotation(
        self, df: pl.DataFrame
    ) -> list[DQListItem]:
        """Find outliers using rotation-aware carrier fit check with weight.

        An item is a suspect outlier only if it cannot fit in ANY active
        carrier considering:
        - All 6 possible dimension rotations
        - Weight <= carrier max_weight_kg
        """
        items: list[DQListItem] = []

        required_cols = ["sku", "length_mm", "width_mm", "height_mm"]
        if not all(c in df.columns for c in required_cols):
            return items

        has_weight = "weight_kg" in df.columns

        # Filter rows with valid positive dimensions
        valid_df = df.filter(
            (pl.col("length_mm") > 0)
            & (pl.col("width_mm") > 0)
            & (pl.col("height_mm") > 0)
        )

        # Track SKUs that are outliers
        checked_skus: set[str] = set()

        # Select columns including weight if available
        select_cols = required_cols + (["weight_kg"] if has_weight else [])

        for row in valid_df.select(select_cols).to_dicts():
            sku = str(row["sku"])
            if sku in checked_skus:
                continue

            length = row["length_mm"]
            width = row["width_mm"]
            height = row["height_mm"]
            weight = row.get("weight_kg") if has_weight else None

            # Check if cannot fit any carrier with rotation AND weight
            if self.carriers and not DimensionChecker.can_fit_any_carrier(
                length, width, height, self.carriers, weight_kg=weight
            ):
                # Determine the reason (dimensions or weight)
                # Check if it would fit without weight constraint
                fits_dimensions = DimensionChecker.can_fit_any_carrier(
                    length, width, height, self.carriers, weight_kg=None
                )

                if fits_dimensions and weight is not None:
                    # Weight is the problem
                    max_weight = max(
                        c.max_weight_kg for c in self.carriers if c.is_active
                    )
                    items.append(
                        DQListItem(
                            sku=sku,
                            issue_type="suspect_outlier",
                            field="weight_kg",
                            value=f"{weight}",
                            details=(
                                f"Weight {weight}kg exceeds max carrier capacity "
                                f"({max_weight}kg)"
                            ),
                        )
                    )
                else:
                    # Dimensions are the problem
                    max_carrier_dim = DimensionChecker.get_max_allowed_dimension(
                        self.carriers
                    )
                    max_item_dim = max(length, width, height)

                    items.append(
                        DQListItem(
                            sku=sku,
                            issue_type="suspect_outlier",
                            field="dimensions",
                            value=f"L={length}, W={width}, H={height}",
                            details=(
                                f"Cannot fit any carrier with rotation "
                                f"(max dimension {max_item_dim}mm > "
                                f"max carrier axis {max_carrier_dim}mm)"
                            ),
                        )
                    )
                checked_skus.add(sku)

        return items

    def _find_high_risk_borderline(
        self,
        df: pl.DataFrame,
        carrier_limits: Optional[dict[str, float]] = None,
    ) -> list[DQListItem]:
        """Find SKUs with dimensions close to carrier limits."""
        items: list[DQListItem] = []

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
            borderline_rows = df.filter(borderline_mask).select(["sku", field]).to_dicts()

            items.extend([
                DQListItem(
                    sku=str(row["sku"]),
                    issue_type="high_risk_borderline",
                    field=field,
                    value=str(row[field]),
                    details=f"Margin to limit: {limit - row[field]:.1f}mm (limit: {limit}mm)",
                )
                for row in borderline_rows
            ])

        return items

    def _find_duplicates(self, df: pl.DataFrame) -> list[DQListItem]:
        """Find duplicate SKUs."""
        if "sku" not in df.columns:
            return []

        # Group by SKU and find duplicates
        sku_counts = df.group_by("sku").agg(pl.len().alias("count"))
        duplicates = sku_counts.filter(pl.col("count") > 1).to_dicts()

        return [
            DQListItem(
                sku=str(row["sku"]),
                issue_type="duplicate",
                field="sku",
                value=str(row["count"]),
                details=f"SKU appears {row['count']} times",
            )
            for row in duplicates
        ]

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
