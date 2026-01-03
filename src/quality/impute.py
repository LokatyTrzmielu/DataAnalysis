"""Imputacja brakujacych wartosci z flagami RAW/ESTIMATED."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import polars as pl

from src.core.types import DataQualityFlag


class ImputationMethod(str, Enum):
    """Metoda imputacji."""
    MEDIAN = "median"
    MEAN = "mean"
    MODE = "mode"


class ImputationScope(str, Enum):
    """Zakres imputacji."""
    GLOBAL = "global"  # Globalna mediana/srednia
    PER_CATEGORY = "per_category"  # Per kategoria (jesli dostepna)


@dataclass
class ImputationStats:
    """Statystyki imputacji dla pola."""
    field_name: str
    original_missing: int
    imputed_count: int
    imputation_value: float
    method: ImputationMethod


@dataclass
class ImputationResult:
    """Wynik imputacji."""
    df: pl.DataFrame
    stats: list[ImputationStats] = field(default_factory=list)
    total_imputed: int = 0
    total_records: int = 0

    @property
    def imputation_rate(self) -> float:
        """Procent zaimputowanych rekordow."""
        if self.total_records == 0:
            return 0.0
        return (self.total_imputed / self.total_records) * 100


class Imputer:
    """Imputacja brakujacych wartosci."""

    # Pola do imputacji z ich flagami
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
        """Inicjalizacja imputera.

        Args:
            method: Metoda imputacji
            scope: Zakres imputacji
            treat_zero_as_missing: Czy traktowac 0 jako brak
        """
        self.method = method
        self.scope = scope
        self.treat_zero_as_missing = treat_zero_as_missing

    def impute(
        self,
        df: pl.DataFrame,
        fields: Optional[list[str]] = None,
    ) -> ImputationResult:
        """Wykonaj imputacje brakujacych wartosci.

        Args:
            df: DataFrame z danymi
            fields: Lista pol do imputacji (None = wszystkie dostepne)

        Returns:
            ImputationResult z danymi i statystykami
        """
        if fields is None:
            fields = [f for f in self.IMPUTABLE_FIELDS.keys() if f in df.columns]

        result_df = df.clone()
        stats: list[ImputationStats] = []
        total_imputed = 0

        for field_name in fields:
            if field_name not in result_df.columns:
                continue

            flag_name = self.IMPUTABLE_FIELDS.get(field_name)
            if flag_name is None:
                continue

            # Dodaj kolumne flagi jesli nie istnieje
            if flag_name not in result_df.columns:
                result_df = result_df.with_columns([
                    pl.lit(DataQualityFlag.RAW.value).alias(flag_name)
                ])

            # Wykonaj imputacje
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
        """Imputuj pojedyncze pole."""
        # Okresl maske brakow
        if self.treat_zero_as_missing:
            missing_mask = pl.col(field_name).is_null() | (pl.col(field_name) <= 0)
        else:
            missing_mask = pl.col(field_name).is_null()

        # Policz braki
        missing_count = df.filter(missing_mask).height
        if missing_count == 0:
            return df, None

        # Oblicz wartosc imputacji
        valid_values = df.filter(~missing_mask)[field_name]
        if valid_values.len() == 0:
            return df, None

        imputation_value = self._calculate_imputation_value(valid_values)

        # Zastosuj imputacje
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
        """Oblicz wartosc do imputacji."""
        if self.method == ImputationMethod.MEDIAN:
            return values.median()
        elif self.method == ImputationMethod.MEAN:
            return values.mean()
        elif self.method == ImputationMethod.MODE:
            mode = values.mode()
            return mode[0] if len(mode) > 0 else values.median()
        else:
            return values.median()


def impute_missing(
    df: pl.DataFrame,
    method: ImputationMethod = ImputationMethod.MEDIAN,
    fields: Optional[list[str]] = None,
) -> ImputationResult:
    """Funkcja pomocnicza do imputacji.

    Args:
        df: DataFrame z danymi
        method: Metoda imputacji
        fields: Lista pol do imputacji

    Returns:
        ImputationResult
    """
    imputer = Imputer(method=method)
    return imputer.impute(df, fields)
