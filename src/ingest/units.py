"""Unit detection and conversion (mm/cm/m, kg/g)."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import polars as pl

from src.ingest.cleaning import clean_numeric_column


class LengthUnit(str, Enum):
    """Length units."""
    MM = "mm"
    CM = "cm"
    M = "m"
    INCH = "inch"


class WeightUnit(str, Enum):
    """Weight units."""
    KG = "kg"
    G = "g"
    LB = "lb"


# Conversion factors to base units (mm, kg)
LENGTH_TO_MM = {
    LengthUnit.MM: 1.0,
    LengthUnit.CM: 10.0,
    LengthUnit.M: 1000.0,
    LengthUnit.INCH: 25.4,
}

WEIGHT_TO_KG = {
    WeightUnit.KG: 1.0,
    WeightUnit.G: 0.001,
    WeightUnit.LB: 0.453592,
}


@dataclass
class UnitDetectionResult:
    """Unit detection result."""
    detected_unit: LengthUnit | WeightUnit
    confidence: float  # 0-1
    sample_values: list[float]
    converted_values: list[float]


class UnitDetector:
    """Unit detection based on values."""

    # Typical dimension ranges in mm
    DIMENSION_RANGES_MM = {
        "small": (10, 500),      # Small items
        "medium": (100, 1500),   # Medium items
        "large": (500, 3000),    # Large items
    }

    # Typical weight ranges in kg
    WEIGHT_RANGES_KG = {
        "light": (0.01, 5),      # Light
        "medium": (1, 50),       # Medium
        "heavy": (20, 200),      # Heavy
    }

    def detect_length_unit(
        self,
        values: Sequence[float],
        column_name: Optional[str] = None,
    ) -> UnitDetectionResult:
        """Detect length unit.

        Args:
            values: List of values to analyze
            column_name: Column name (may contain unit hint)

        Returns:
            UnitDetectionResult with detected unit
        """
        # Remove None and values <= 0
        clean_values = [v for v in values if v is not None and v > 0]
        if not clean_values:
            return UnitDetectionResult(
                detected_unit=LengthUnit.MM,
                confidence=0.0,
                sample_values=[],
                converted_values=[],
            )

        # Check column name
        if column_name:
            unit_from_name = self._detect_unit_from_name(column_name, "length")
            if unit_from_name and isinstance(unit_from_name, LengthUnit):
                return UnitDetectionResult(
                    detected_unit=unit_from_name,
                    confidence=0.9,
                    sample_values=list(clean_values[:10]),
                    converted_values=[v * LENGTH_TO_MM[unit_from_name] for v in clean_values[:10]],
                )

        # Statistical analysis
        median = sorted(clean_values)[len(clean_values) // 2]
        max_val = max(clean_values)
        min_val = min(clean_values)

        # Heuristics:
        # - If median < 10 -> probably meters or cm
        # - If median 10-100 -> probably cm
        # - If median > 100 -> probably mm

        if median < 5:
            # Probably meters
            detected = LengthUnit.M
            confidence = 0.7
        elif median < 100 and max_val < 500:
            # Probably cm
            detected = LengthUnit.CM
            confidence = 0.75
        else:
            # Probably mm
            detected = LengthUnit.MM
            confidence = 0.8

        return UnitDetectionResult(
            detected_unit=detected,
            confidence=confidence,
            sample_values=list(clean_values[:10]),
            converted_values=[v * LENGTH_TO_MM[detected] for v in clean_values[:10]],
        )

    def detect_weight_unit(
        self,
        values: Sequence[float],
        column_name: Optional[str] = None,
    ) -> UnitDetectionResult:
        """Detect weight unit.

        Args:
            values: List of values to analyze
            column_name: Column name

        Returns:
            UnitDetectionResult with detected unit
        """
        clean_values = [v for v in values if v is not None and v > 0]
        if not clean_values:
            return UnitDetectionResult(
                detected_unit=WeightUnit.G,  # Default to grams
                confidence=0.0,
                sample_values=[],
                converted_values=[],
            )

        # Check column name
        if column_name:
            unit_from_name = self._detect_unit_from_name(column_name, "weight")
            if unit_from_name and isinstance(unit_from_name, WeightUnit):
                return UnitDetectionResult(
                    detected_unit=unit_from_name,
                    confidence=0.9,
                    sample_values=list(clean_values[:10]),
                    converted_values=[v * WEIGHT_TO_KG[unit_from_name] for v in clean_values[:10]],
                )

        median = sorted(clean_values)[len(clean_values) // 2]
        max_val = max(clean_values)

        # Heuristics:
        # Default: grams (customer data is typically in grams)
        # Detect kg only if values are very small (typical product weight range 0.01-50 kg)

        if median < 10 and max_val < 100:
            # Probably kilograms - very small values
            detected = WeightUnit.KG
            confidence = 0.7
        else:
            # Default: grams
            detected = WeightUnit.G
            confidence = 0.85

        return UnitDetectionResult(
            detected_unit=detected,
            confidence=confidence,
            sample_values=list(clean_values[:10]),
            converted_values=[v * WEIGHT_TO_KG[detected] for v in clean_values[:10]],
        )

    def _detect_unit_from_name(
        self,
        column_name: str,
        unit_type: str,
    ) -> Optional[LengthUnit | WeightUnit]:
        """Detect unit from column name."""
        name_lower = column_name.lower()

        if unit_type == "length":
            if "_mm" in name_lower or "(mm)" in name_lower or name_lower.endswith("mm"):
                return LengthUnit.MM
            if "_cm" in name_lower or "(cm)" in name_lower or name_lower.endswith("cm"):
                return LengthUnit.CM
            if "_m" in name_lower or "(m)" in name_lower:
                return LengthUnit.M
            if "inch" in name_lower or "in" in name_lower:
                return LengthUnit.INCH

        elif unit_type == "weight":
            if "_kg" in name_lower or "(kg)" in name_lower or name_lower.endswith("kg"):
                return WeightUnit.KG
            # Check for grams - including "grams", "_g", "(g)"
            if "grams" in name_lower or "gram" in name_lower:
                return WeightUnit.G
            if "_g" in name_lower or "(g)" in name_lower or name_lower.endswith("g"):
                return WeightUnit.G
            if "lb" in name_lower or "pound" in name_lower:
                return WeightUnit.LB

        return None


class UnitConverter:
    """Unit conversion in DataFrame."""

    def __init__(self) -> None:
        self.detector = UnitDetector()

    def convert_dimensions_to_mm(
        self,
        df: pl.DataFrame,
        length_col: str,
        width_col: str,
        height_col: str,
        auto_detect: bool = True,
        source_unit: Optional[LengthUnit] = None,
    ) -> pl.DataFrame:
        """Convert dimensions to mm.

        Args:
            df: DataFrame with dimensions
            length_col, width_col, height_col: Column names
            auto_detect: Whether to auto-detect unit
            source_unit: Source unit (if known)

        Returns:
            DataFrame with dimensions in mm
        """
        if source_unit is None and auto_detect:
            # Detect unit based on first column
            sample = df.select(clean_numeric_column(pl.col(length_col))).to_series().drop_nulls().to_list()[:100]
            detection = self.detector.detect_length_unit(sample, length_col)
            if isinstance(detection.detected_unit, LengthUnit):
                source_unit = detection.detected_unit

        if source_unit is None:
            source_unit = LengthUnit.MM

        factor = LENGTH_TO_MM[source_unit]

        return df.with_columns([
            (clean_numeric_column(pl.col(length_col)) * factor).alias(length_col),
            (clean_numeric_column(pl.col(width_col)) * factor).alias(width_col),
            (clean_numeric_column(pl.col(height_col)) * factor).alias(height_col),
        ])

    def convert_weight_to_kg(
        self,
        df: pl.DataFrame,
        weight_col: str,
        auto_detect: bool = True,
        source_unit: Optional[WeightUnit] = None,
    ) -> pl.DataFrame:
        """Convert weight to kg.

        Args:
            df: DataFrame with weight
            weight_col: Weight column name
            auto_detect: Whether to auto-detect unit
            source_unit: Source unit (if known)

        Returns:
            DataFrame with weight in kg
        """
        if source_unit is None and auto_detect:
            sample = df.select(clean_numeric_column(pl.col(weight_col))).to_series().drop_nulls().to_list()[:100]
            detection = self.detector.detect_weight_unit(sample, weight_col)
            if isinstance(detection.detected_unit, WeightUnit):
                source_unit = detection.detected_unit

        if source_unit is None:
            source_unit = WeightUnit.KG

        factor = WEIGHT_TO_KG[source_unit]

        return df.with_columns([
            (clean_numeric_column(pl.col(weight_col)) * factor).alias(weight_col),
        ])
