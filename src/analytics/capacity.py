"""Capacity analysis - matching SKU to carriers."""

from dataclasses import dataclass, field
from itertools import permutations
from typing import Optional

import polars as pl

from src.core.types import (
    CarrierConfig,
    CarrierFitResult,
    FitResult,
    OrientationConstraint,
    LimitingFactor,
)
from src.core.config import BORDERLINE_THRESHOLD_MM


@dataclass
class CarrierStats:
    """Fit statistics for a single carrier."""
    carrier_id: str
    carrier_name: str
    fit_count: int
    borderline_count: int
    not_fit_count: int
    fit_percentage: float
    total_volume_m3: float  # Sum of unit SKU volumes that fit (fit + borderline)
    stock_volume_m3: float = 0.0  # Sum of (unit volume × stock_qty) for fitting SKUs


@dataclass
class CapacityAnalysisResult:
    """Capacity analysis result."""
    df: pl.DataFrame  # DataFrame with fit results
    total_sku: int
    fit_count: int
    borderline_count: int
    not_fit_count: int
    fit_percentage: float
    carriers_analyzed: list[str]
    carrier_stats: dict[str, CarrierStats] = field(default_factory=dict)  # Statistics per carrier


class CapacityAnalyzer:
    """Capacity analyzer - matching SKU to carriers."""

    # 6 possible orientations (permutations of L, W, H)
    ORIENTATIONS = list(permutations(["L", "W", "H"]))

    def __init__(
        self,
        carriers: list[CarrierConfig],
        borderline_threshold_mm: float = BORDERLINE_THRESHOLD_MM,
        default_utilization: float = 0.75,
    ) -> None:
        """Initialize the analyzer.

        Args:
            carriers: List of carriers to analyze
            borderline_threshold_mm: Threshold for BORDERLINE
            default_utilization: Default utilization coefficient
        """
        self.carriers = carriers
        self.borderline_threshold_mm = borderline_threshold_mm
        self.default_utilization = default_utilization

    def analyze_sku(
        self,
        sku: str,
        length_mm: float,
        width_mm: float,
        height_mm: float,
        weight_kg: float,
        constraint: OrientationConstraint = OrientationConstraint.ANY,
    ) -> list[CarrierFitResult]:
        """Analyze SKU fit to all carriers.

        Args:
            sku: SKU identifier
            length_mm, width_mm, height_mm: Dimensions in mm
            weight_kg: Weight in kg
            constraint: Orientation constraint

        Returns:
            List of CarrierFitResult for each carrier
        """
        results = []

        for carrier in self.carriers:
            if not carrier.is_active:
                continue

            fit_result = self._check_fit(
                sku, length_mm, width_mm, height_mm, weight_kg,
                carrier, constraint
            )
            results.append(fit_result)

        return results

    def _check_fit(
        self,
        sku: str,
        length_mm: float,
        width_mm: float,
        height_mm: float,
        weight_kg: float,
        carrier: CarrierConfig,
        constraint: OrientationConstraint,
    ) -> CarrierFitResult:
        """Check SKU fit to carrier."""
        dims = {"L": length_mm, "W": width_mm, "H": height_mm}

        # Generate allowed orientations
        orientations = self._get_allowed_orientations(constraint)

        best_fit = None
        best_orientation = None
        best_margin = float("-inf")

        for orientation in orientations:
            # Map SKU dimensions to carrier axes (X, Y, Z)
            sku_x = dims[orientation[0]]
            sku_y = dims[orientation[1]]
            sku_z = dims[orientation[2]]

            # Check dimensional fit
            margin_x = carrier.inner_length_mm - sku_x
            margin_y = carrier.inner_width_mm - sku_y
            margin_z = carrier.inner_height_mm - sku_z

            min_margin = min(margin_x, margin_y, margin_z)

            if min_margin >= 0:
                # Fits
                if min_margin > best_margin:
                    best_margin = min_margin
                    best_orientation = orientation

                    if min_margin < self.borderline_threshold_mm:
                        best_fit = FitResult.BORDERLINE
                    else:
                        best_fit = FitResult.FIT

        # If it doesn't fit dimensionally
        if best_fit is None:
            return CarrierFitResult(
                sku=sku,
                carrier_id=carrier.carrier_id,
                fit_status=FitResult.NOT_FIT,
                limiting_factor=LimitingFactor.DIMENSION,
            )

        # Check weight
        if weight_kg > carrier.max_weight_kg:
            return CarrierFitResult(
                sku=sku,
                carrier_id=carrier.carrier_id,
                fit_status=FitResult.NOT_FIT,
                limiting_factor=LimitingFactor.WEIGHT,
            )

        # Calculate how many units per carrier
        units_per_carrier = self._calculate_units_per_carrier(
            dims[best_orientation[0]],
            dims[best_orientation[1]],
            dims[best_orientation[2]],
            weight_kg,
            carrier,
        )

        return CarrierFitResult(
            sku=sku,
            carrier_id=carrier.carrier_id,
            fit_status=best_fit,
            best_orientation=best_orientation,
            units_per_carrier=units_per_carrier,
            limiting_factor=LimitingFactor.NONE,
            margin_mm=best_margin if best_fit == FitResult.BORDERLINE else None,
        )

    def _get_allowed_orientations(
        self,
        constraint: OrientationConstraint,
    ) -> list[tuple[str, str, str]]:
        """Get allowed orientations."""
        if constraint == OrientationConstraint.ANY:
            return self.ORIENTATIONS

        elif constraint == OrientationConstraint.UPRIGHT_ONLY:
            # Height must be on Z axis
            return [o for o in self.ORIENTATIONS if o[2] == "H"]

        elif constraint == OrientationConstraint.FLAT_ONLY:
            # Height must be smallest (X or Y)
            return [o for o in self.ORIENTATIONS if o[2] != "H"]

        return self.ORIENTATIONS

    def _calculate_units_per_carrier(
        self,
        sku_x: float,
        sku_y: float,
        sku_z: float,
        weight_kg: float,
        carrier: CarrierConfig,
    ) -> int:
        """Calculate how many units fit on the carrier."""
        # How many in each direction
        count_x = int(carrier.inner_length_mm // sku_x) if sku_x > 0 else 0
        count_y = int(carrier.inner_width_mm // sku_y) if sku_y > 0 else 0
        count_z = int(carrier.inner_height_mm // sku_z) if sku_z > 0 else 0

        volume_based = count_x * count_y * count_z

        # Weight constraint
        weight_based = int(carrier.max_weight_kg // weight_kg) if weight_kg > 0 else volume_based

        return min(volume_based, weight_based)

    def analyze_dataframe(
        self,
        df: pl.DataFrame,
        carrier_id: Optional[str] = None,
        prioritization_mode: bool = False,
    ) -> CapacityAnalysisResult:
        """Analyze entire DataFrame.

        Args:
            df: DataFrame with Masterdata
            carrier_id: Specific carrier (None = all)
            prioritization_mode: If True, assign each SKU to smallest fitting carrier

        Returns:
            CapacityAnalysisResult
        """
        # Filter only active carriers
        carriers_to_analyze = [c for c in self.carriers if c.is_active]
        if carrier_id:
            carriers_to_analyze = [c for c in carriers_to_analyze if c.carrier_id == carrier_id]

        # In prioritization mode, sort carriers by volume (smallest first)
        if prioritization_mode:
            carriers_to_analyze = sorted(
                carriers_to_analyze,
                key=lambda c: c.inner_volume_m3
            )

        results = []

        # Get required columns for processing
        required_cols = ["sku", "length_mm", "width_mm", "height_mm", "weight_kg"]
        available_cols = [c for c in required_cols if c in df.columns]
        if "stock_qty" in df.columns:
            available_cols.append("stock_qty")
        if "orientation_constraint" in df.columns:
            available_cols.append("orientation_constraint")

        rows = df.select(available_cols).to_dicts()

        for row in rows:
            sku = row["sku"]
            length = row.get("length_mm", 0) or 0
            width = row.get("width_mm", 0) or 0
            height = row.get("height_mm", 0) or 0
            weight = row.get("weight_kg", 0) or 0
            stock_qty = row.get("stock_qty", 0) or 0

            # Calculate volume_m3 for a single SKU unit
            sku_volume_m3 = (length * width * height) / 1_000_000_000
            # Stock volume = unit volume × stock quantity
            sku_stock_volume_m3 = sku_volume_m3 * stock_qty

            constraint = OrientationConstraint.ANY
            if "orientation_constraint" in row:
                try:
                    constraint = OrientationConstraint(row["orientation_constraint"])
                except (ValueError, TypeError):
                    pass

            sku_assigned = False
            for carrier in carriers_to_analyze:
                fit_result = self._check_fit(
                    sku, length, width, height, weight, carrier, constraint
                )

                if prioritization_mode:
                    # In prioritization mode: assign SKU to first fitting carrier
                    if fit_result.fit_status in [FitResult.FIT, FitResult.BORDERLINE]:
                        results.append({
                            "sku": sku,
                            "carrier_id": carrier.carrier_id,
                            "fit_status": fit_result.fit_status.value,
                            "units_per_carrier": fit_result.units_per_carrier,
                            "volume_m3": round(sku_volume_m3, 6),
                            "stock_volume_m3": round(sku_stock_volume_m3, 6),
                            "limiting_factor": fit_result.limiting_factor.value,
                            "margin_mm": float(fit_result.margin_mm) if fit_result.margin_mm is not None else None,
                        })
                        sku_assigned = True
                        break  # Stop after first fitting carrier
                else:
                    # Independent mode: add all results
                    results.append({
                        "sku": sku,
                        "carrier_id": carrier.carrier_id,
                        "fit_status": fit_result.fit_status.value,
                        "units_per_carrier": fit_result.units_per_carrier,
                        "volume_m3": round(sku_volume_m3, 6),
                        "stock_volume_m3": round(sku_stock_volume_m3, 6),
                        "limiting_factor": fit_result.limiting_factor.value,
                        "margin_mm": float(fit_result.margin_mm) if fit_result.margin_mm is not None else None,
                    })

            # In prioritization mode: if SKU doesn't fit any carrier, record as NOT_FIT
            if prioritization_mode and not sku_assigned and carriers_to_analyze:
                results.append({
                    "sku": sku,
                    "carrier_id": "NONE",  # Special marker - doesn't fit any carrier
                    "fit_status": FitResult.NOT_FIT.value,
                    "units_per_carrier": 0,
                    "volume_m3": round(sku_volume_m3, 6),
                    "stock_volume_m3": round(sku_stock_volume_m3, 6),
                    "limiting_factor": LimitingFactor.DIMENSION.value,
                    "margin_mm": None,
                })

        # Create DataFrame with explicit schema for columns with None
        result_df = pl.DataFrame(
            results,
            schema={
                "sku": pl.Utf8,
                "carrier_id": pl.Utf8,
                "fit_status": pl.Utf8,
                "units_per_carrier": pl.Int64,
                "volume_m3": pl.Float64,
                "stock_volume_m3": pl.Float64,
                "limiting_factor": pl.Utf8,
                "margin_mm": pl.Float64,
            }
        )

        # Global statistics (sum of all carriers - for compatibility)
        fit_count = result_df.filter(pl.col("fit_status") == "FIT").height
        borderline_count = result_df.filter(pl.col("fit_status") == "BORDERLINE").height
        not_fit_count = result_df.filter(pl.col("fit_status") == "NOT_FIT").height

        total = fit_count + borderline_count + not_fit_count
        fit_percentage = ((fit_count + borderline_count) / total * 100) if total > 0 else 0

        # Statistics per carrier
        carrier_stats: dict[str, CarrierStats] = {}
        for carrier in carriers_to_analyze:
            carrier_df = result_df.filter(pl.col("carrier_id") == carrier.carrier_id)
            c_fit = carrier_df.filter(pl.col("fit_status") == "FIT").height
            c_borderline = carrier_df.filter(pl.col("fit_status") == "BORDERLINE").height
            c_not_fit = carrier_df.filter(pl.col("fit_status") == "NOT_FIT").height
            c_total = c_fit + c_borderline + c_not_fit
            c_fit_pct = ((c_fit + c_borderline) / c_total * 100) if c_total > 0 else 0

            # Sum of volume_m3 for SKUs that fit (FIT or BORDERLINE)
            fitting_df = carrier_df.filter(pl.col("fit_status").is_in(["FIT", "BORDERLINE"]))
            c_volume_m3 = fitting_df["volume_m3"].sum() if fitting_df.height > 0 else 0.0
            c_stock_volume_m3 = fitting_df["stock_volume_m3"].sum() if fitting_df.height > 0 else 0.0

            carrier_stats[carrier.carrier_id] = CarrierStats(
                carrier_id=carrier.carrier_id,
                carrier_name=carrier.name,
                fit_count=c_fit,
                borderline_count=c_borderline,
                not_fit_count=c_not_fit,
                fit_percentage=round(c_fit_pct, 1),
                total_volume_m3=round(c_volume_m3, 2),
                stock_volume_m3=round(c_stock_volume_m3, 2),
            )

        # In prioritization mode, add stats for SKUs that don't fit any carrier
        if prioritization_mode:
            none_df = result_df.filter(pl.col("carrier_id") == "NONE")
            if none_df.height > 0:
                none_volume = none_df["volume_m3"].sum()
                none_stock_volume = none_df["stock_volume_m3"].sum()
                carrier_stats["NONE"] = CarrierStats(
                    carrier_id="NONE",
                    carrier_name="Does not fit any carrier",
                    fit_count=0,
                    borderline_count=0,
                    not_fit_count=none_df.height,
                    fit_percentage=0.0,
                    total_volume_m3=round(none_volume, 2),
                    stock_volume_m3=round(none_stock_volume, 2),
                )

        # Build list of analyzed carriers
        carriers_analyzed_ids = [c.carrier_id for c in carriers_to_analyze]
        if prioritization_mode and "NONE" in carrier_stats:
            carriers_analyzed_ids.append("NONE")

        return CapacityAnalysisResult(
            df=result_df,
            total_sku=df["sku"].n_unique(),
            fit_count=fit_count,
            borderline_count=borderline_count,
            not_fit_count=not_fit_count,
            fit_percentage=fit_percentage,
            carriers_analyzed=carriers_analyzed_ids,
            carrier_stats=carrier_stats,
        )


def analyze_capacity(
    df: pl.DataFrame,
    carriers: list[CarrierConfig],
) -> CapacityAnalysisResult:
    """Helper function for capacity analysis.

    Args:
        df: DataFrame with Masterdata
        carriers: List of carriers

    Returns:
        CapacityAnalysisResult
    """
    analyzer = CapacityAnalyzer(carriers)
    return analyzer.analyze_dataframe(df)
