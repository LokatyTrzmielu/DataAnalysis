"""Detekcja i konwersja jednostek (mm/cm/m, kg/g)."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import polars as pl


class LengthUnit(str, Enum):
    """Jednostki dlugosci."""
    MM = "mm"
    CM = "cm"
    M = "m"
    INCH = "inch"


class WeightUnit(str, Enum):
    """Jednostki wagi."""
    KG = "kg"
    G = "g"
    LB = "lb"


# Wspolczynniki konwersji do jednostek bazowych (mm, kg)
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
    """Wynik detekcji jednostki."""
    detected_unit: LengthUnit | WeightUnit
    confidence: float  # 0-1
    sample_values: list[float]
    converted_values: list[float]


class UnitDetector:
    """Detekcja jednostek na podstawie wartosci."""

    # Typowe zakresy wymiarow w mm
    DIMENSION_RANGES_MM = {
        "small": (10, 500),      # Male przedmioty
        "medium": (100, 1500),   # Srednie przedmioty
        "large": (500, 3000),    # Duze przedmioty
    }

    # Typowe zakresy wag w kg
    WEIGHT_RANGES_KG = {
        "light": (0.01, 5),      # Lekkie
        "medium": (1, 50),       # Srednie
        "heavy": (20, 200),      # Ciezkie
    }

    def detect_length_unit(
        self,
        values: list[float],
        column_name: Optional[str] = None,
    ) -> UnitDetectionResult:
        """Wykryj jednostke dlugosci.

        Args:
            values: Lista wartosci do analizy
            column_name: Nazwa kolumny (moze zawierac podpowiedz jednostki)

        Returns:
            UnitDetectionResult z wykryta jednostka
        """
        # Usun None i wartosci <= 0
        clean_values = [v for v in values if v is not None and v > 0]
        if not clean_values:
            return UnitDetectionResult(
                detected_unit=LengthUnit.MM,
                confidence=0.0,
                sample_values=[],
                converted_values=[],
            )

        # Sprawdz nazwe kolumny
        if column_name:
            unit_from_name = self._detect_unit_from_name(column_name, "length")
            if unit_from_name:
                return UnitDetectionResult(
                    detected_unit=unit_from_name,
                    confidence=0.9,
                    sample_values=clean_values[:10],
                    converted_values=[v * LENGTH_TO_MM[unit_from_name] for v in clean_values[:10]],
                )

        # Analiza statystyczna
        median = sorted(clean_values)[len(clean_values) // 2]
        max_val = max(clean_values)
        min_val = min(clean_values)

        # Heurystyki:
        # - Jesli mediana < 10 -> prawdopodobnie metry lub cm
        # - Jesli mediana 10-100 -> prawdopodobnie cm
        # - Jesli mediana > 100 -> prawdopodobnie mm

        if median < 5:
            # Prawdopodobnie metry
            detected = LengthUnit.M
            confidence = 0.7
        elif median < 100 and max_val < 500:
            # Prawdopodobnie cm
            detected = LengthUnit.CM
            confidence = 0.75
        else:
            # Prawdopodobnie mm
            detected = LengthUnit.MM
            confidence = 0.8

        return UnitDetectionResult(
            detected_unit=detected,
            confidence=confidence,
            sample_values=clean_values[:10],
            converted_values=[v * LENGTH_TO_MM[detected] for v in clean_values[:10]],
        )

    def detect_weight_unit(
        self,
        values: list[float],
        column_name: Optional[str] = None,
    ) -> UnitDetectionResult:
        """Wykryj jednostke wagi.

        Args:
            values: Lista wartosci do analizy
            column_name: Nazwa kolumny

        Returns:
            UnitDetectionResult z wykryta jednostka
        """
        clean_values = [v for v in values if v is not None and v > 0]
        if not clean_values:
            return UnitDetectionResult(
                detected_unit=WeightUnit.KG,
                confidence=0.0,
                sample_values=[],
                converted_values=[],
            )

        # Sprawdz nazwe kolumny
        if column_name:
            unit_from_name = self._detect_unit_from_name(column_name, "weight")
            if unit_from_name:
                return UnitDetectionResult(
                    detected_unit=unit_from_name,
                    confidence=0.9,
                    sample_values=clean_values[:10],
                    converted_values=[v * WEIGHT_TO_KG[unit_from_name] for v in clean_values[:10]],
                )

        median = sorted(clean_values)[len(clean_values) // 2]

        # Heurystyki:
        # - Jesli mediana > 100 -> prawdopodobnie gramy
        # - Jesli mediana < 100 -> prawdopodobnie kg

        if median > 500:
            detected = WeightUnit.G
            confidence = 0.8
        else:
            detected = WeightUnit.KG
            confidence = 0.85

        return UnitDetectionResult(
            detected_unit=detected,
            confidence=confidence,
            sample_values=clean_values[:10],
            converted_values=[v * WEIGHT_TO_KG[detected] for v in clean_values[:10]],
        )

    def _detect_unit_from_name(
        self,
        column_name: str,
        unit_type: str,
    ) -> Optional[LengthUnit | WeightUnit]:
        """Wykryj jednostke z nazwy kolumny."""
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
            if "_g" in name_lower or "(g)" in name_lower or name_lower.endswith("g"):
                return WeightUnit.G
            if "lb" in name_lower or "pound" in name_lower:
                return WeightUnit.LB

        return None


class UnitConverter:
    """Konwersja jednostek w DataFrame."""

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
        """Konwertuj wymiary do mm.

        Args:
            df: DataFrame z wymiarami
            length_col, width_col, height_col: Nazwy kolumn
            auto_detect: Czy automatycznie wykryc jednostke
            source_unit: Jednostka zrodlowa (jesli znana)

        Returns:
            DataFrame z wymiarami w mm
        """
        if source_unit is None and auto_detect:
            # Wykryj jednostke na podstawie pierwszej kolumny
            sample = df[length_col].drop_nulls().to_list()[:100]
            detection = self.detector.detect_length_unit(sample, length_col)
            source_unit = detection.detected_unit

        if source_unit is None:
            source_unit = LengthUnit.MM

        factor = LENGTH_TO_MM[source_unit]

        if factor == 1.0:
            return df

        # Konwertuj wszystkie kolumny wymiarow
        return df.with_columns([
            (pl.col(length_col) * factor).alias(length_col),
            (pl.col(width_col) * factor).alias(width_col),
            (pl.col(height_col) * factor).alias(height_col),
        ])

    def convert_weight_to_kg(
        self,
        df: pl.DataFrame,
        weight_col: str,
        auto_detect: bool = True,
        source_unit: Optional[WeightUnit] = None,
    ) -> pl.DataFrame:
        """Konwertuj wage do kg.

        Args:
            df: DataFrame z waga
            weight_col: Nazwa kolumny wagi
            auto_detect: Czy automatycznie wykryc jednostke
            source_unit: Jednostka zrodlowa (jesli znana)

        Returns:
            DataFrame z waga w kg
        """
        if source_unit is None and auto_detect:
            sample = df[weight_col].drop_nulls().to_list()[:100]
            detection = self.detector.detect_weight_unit(sample, weight_col)
            source_unit = detection.detected_unit

        if source_unit is None:
            source_unit = WeightUnit.KG

        factor = WEIGHT_TO_KG[source_unit]

        if factor == 1.0:
            return df

        return df.with_columns([
            (pl.col(weight_col) * factor).alias(weight_col),
        ])
