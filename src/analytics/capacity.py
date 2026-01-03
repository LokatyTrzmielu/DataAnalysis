"""Analiza pojemnosciowa - dopasowanie SKU do nosnikow."""

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
class CapacityAnalysisResult:
    """Wynik analizy pojemnosciowej."""
    df: pl.DataFrame  # DataFrame z wynikami dopasowania
    total_sku: int
    fit_count: int
    borderline_count: int
    not_fit_count: int
    fit_percentage: float
    carriers_analyzed: list[str]


class CapacityAnalyzer:
    """Analizator pojemnosci - dopasowanie SKU do nosnikow."""

    # 6 mozliwych orientacji (permutacje L, W, H)
    ORIENTATIONS = list(permutations(["L", "W", "H"]))

    def __init__(
        self,
        carriers: list[CarrierConfig],
        borderline_threshold_mm: float = BORDERLINE_THRESHOLD_MM,
        default_utilization: float = 0.75,
    ) -> None:
        """Inicjalizacja analizatora.

        Args:
            carriers: Lista nosnikow do analizy
            borderline_threshold_mm: Prog dla BORDERLINE
            default_utilization: Domyslny wspolczynnik wykorzystania
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
        """Analizuj dopasowanie SKU do wszystkich nosnikow.

        Args:
            sku: Identyfikator SKU
            length_mm, width_mm, height_mm: Wymiary w mm
            weight_kg: Waga w kg
            constraint: Ograniczenie orientacji

        Returns:
            Lista CarrierFitResult dla kazdego nosnika
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
        """Sprawdz dopasowanie SKU do nosnika."""
        dims = {"L": length_mm, "W": width_mm, "H": height_mm}

        # Generuj dozwolone orientacje
        orientations = self._get_allowed_orientations(constraint)

        best_fit = None
        best_orientation = None
        best_margin = float("-inf")

        for orientation in orientations:
            # Mapuj wymiary SKU na osie nosnika (X, Y, Z)
            sku_x = dims[orientation[0]]
            sku_y = dims[orientation[1]]
            sku_z = dims[orientation[2]]

            # Sprawdz dopasowanie gabarytowe
            margin_x = carrier.inner_length_mm - sku_x
            margin_y = carrier.inner_width_mm - sku_y
            margin_z = carrier.inner_height_mm - sku_z

            min_margin = min(margin_x, margin_y, margin_z)

            if min_margin >= 0:
                # Miesci sie
                if min_margin > best_margin:
                    best_margin = min_margin
                    best_orientation = orientation

                    if min_margin < self.borderline_threshold_mm:
                        best_fit = FitResult.BORDERLINE
                    else:
                        best_fit = FitResult.FIT

        # Jesli nie miesci sie gabarytowo
        if best_fit is None:
            return CarrierFitResult(
                sku=sku,
                carrier_id=carrier.carrier_id,
                fit_status=FitResult.NOT_FIT,
                limiting_factor=LimitingFactor.DIMENSION,
            )

        # Sprawdz wage
        if weight_kg > carrier.max_weight_kg:
            return CarrierFitResult(
                sku=sku,
                carrier_id=carrier.carrier_id,
                fit_status=FitResult.NOT_FIT,
                limiting_factor=LimitingFactor.WEIGHT,
            )

        # Oblicz ile sztuk na nosniku
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
        """Pobierz dozwolone orientacje."""
        if constraint == OrientationConstraint.ANY:
            return self.ORIENTATIONS

        elif constraint == OrientationConstraint.UPRIGHT_ONLY:
            # Wysokosc musi byc na osi Z
            return [o for o in self.ORIENTATIONS if o[2] == "H"]

        elif constraint == OrientationConstraint.FLAT_ONLY:
            # Wysokosc musi byc najmniejsza (X lub Y)
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
        """Oblicz ile sztuk miesci sie na nosniku."""
        # Ile w kazdym kierunku
        count_x = int(carrier.inner_length_mm // sku_x) if sku_x > 0 else 0
        count_y = int(carrier.inner_width_mm // sku_y) if sku_y > 0 else 0
        count_z = int(carrier.inner_height_mm // sku_z) if sku_z > 0 else 0

        volume_based = count_x * count_y * count_z

        # Ograniczenie wagowe
        weight_based = int(carrier.max_weight_kg // weight_kg) if weight_kg > 0 else volume_based

        return min(volume_based, weight_based)

    def analyze_dataframe(
        self,
        df: pl.DataFrame,
        carrier_id: Optional[str] = None,
    ) -> CapacityAnalysisResult:
        """Analizuj caly DataFrame.

        Args:
            df: DataFrame z Masterdata
            carrier_id: Konkretny nosnik (None = wszystkie)

        Returns:
            CapacityAnalysisResult
        """
        carriers_to_analyze = self.carriers
        if carrier_id:
            carriers_to_analyze = [c for c in self.carriers if c.carrier_id == carrier_id]

        results = []

        for row in df.iter_rows(named=True):
            sku = row["sku"]
            length = row.get("length_mm", 0) or 0
            width = row.get("width_mm", 0) or 0
            height = row.get("height_mm", 0) or 0
            weight = row.get("weight_kg", 0) or 0

            constraint = OrientationConstraint.ANY
            if "orientation_constraint" in row:
                try:
                    constraint = OrientationConstraint(row["orientation_constraint"])
                except (ValueError, TypeError):
                    pass

            for carrier in carriers_to_analyze:
                fit_result = self._check_fit(
                    sku, length, width, height, weight, carrier, constraint
                )
                results.append({
                    "sku": sku,
                    "carrier_id": carrier.carrier_id,
                    "fit_status": fit_result.fit_status.value,
                    "units_per_carrier": fit_result.units_per_carrier,
                    "limiting_factor": fit_result.limiting_factor.value,
                    "margin_mm": float(fit_result.margin_mm) if fit_result.margin_mm is not None else None,
                })

        # Tworzymy DataFrame z jawnym schematem dla kolumn z None
        result_df = pl.DataFrame(
            results,
            schema={
                "sku": pl.Utf8,
                "carrier_id": pl.Utf8,
                "fit_status": pl.Utf8,
                "units_per_carrier": pl.Int64,
                "limiting_factor": pl.Utf8,
                "margin_mm": pl.Float64,
            }
        )

        # Statystyki
        fit_count = result_df.filter(pl.col("fit_status") == "FIT").height
        borderline_count = result_df.filter(pl.col("fit_status") == "BORDERLINE").height
        not_fit_count = result_df.filter(pl.col("fit_status") == "NOT_FIT").height

        total = fit_count + borderline_count + not_fit_count
        fit_percentage = ((fit_count + borderline_count) / total * 100) if total > 0 else 0

        return CapacityAnalysisResult(
            df=result_df,
            total_sku=df["sku"].n_unique(),
            fit_count=fit_count,
            borderline_count=borderline_count,
            not_fit_count=not_fit_count,
            fit_percentage=fit_percentage,
            carriers_analyzed=[c.carrier_id for c in carriers_to_analyze],
        )


def analyze_capacity(
    df: pl.DataFrame,
    carriers: list[CarrierConfig],
) -> CapacityAnalysisResult:
    """Funkcja pomocnicza do analizy pojemnosciowej.

    Args:
        df: DataFrame z Masterdata
        carriers: Lista nosnikow

    Returns:
        CapacityAnalysisResult
    """
    analyzer = CapacityAnalyzer(carriers)
    return analyzer.analyze_dataframe(df)
