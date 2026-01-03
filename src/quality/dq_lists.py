"""Listy problematycznych SKU dla raportow DQ."""

from dataclasses import dataclass, field
from typing import Optional

import polars as pl

from src.core.config import BORDERLINE_THRESHOLD_MM


@dataclass
class DQListItem:
    """Element listy DQ."""
    sku: str
    issue_type: str
    field: str
    value: Optional[str] = None
    details: Optional[str] = None


@dataclass
class DQLists:
    """Kolekcja list problematycznych SKU."""
    missing_critical: list[DQListItem] = field(default_factory=list)
    suspect_outliers: list[DQListItem] = field(default_factory=list)
    high_risk_borderline: list[DQListItem] = field(default_factory=list)
    duplicates: list[DQListItem] = field(default_factory=list)
    conflicts: list[DQListItem] = field(default_factory=list)
    collisions: list[DQListItem] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        """Calkowita liczba problemow."""
        return (
            len(self.missing_critical) +
            len(self.suspect_outliers) +
            len(self.high_risk_borderline) +
            len(self.duplicates) +
            len(self.conflicts) +
            len(self.collisions)
        )


class DQListBuilder:
    """Builder dla list DQ."""

    # Progi dla outlierow (wartosci podejrzane)
    OUTLIER_THRESHOLDS = {
        "length_mm": {"low": 10, "high": 2000},
        "width_mm": {"low": 10, "high": 2000},
        "height_mm": {"low": 5, "high": 1500},
        "weight_kg": {"low": 0.01, "high": 200},
    }

    def __init__(
        self,
        borderline_threshold_mm: float = BORDERLINE_THRESHOLD_MM,
    ) -> None:
        """Inicjalizacja buildera."""
        self.borderline_threshold_mm = borderline_threshold_mm

    def build_all_lists(
        self,
        df: pl.DataFrame,
        carrier_limits: Optional[dict[str, float]] = None,
    ) -> DQLists:
        """Zbuduj wszystkie listy DQ.

        Args:
            df: DataFrame z danymi Masterdata
            carrier_limits: Limity nosnikow dla borderline (opcjonalne)

        Returns:
            DQLists z wszystkimi listami
        """
        return DQLists(
            missing_critical=self._find_missing_critical(df),
            suspect_outliers=self._find_suspect_outliers(df),
            high_risk_borderline=self._find_high_risk_borderline(df, carrier_limits),
            duplicates=self._find_duplicates(df),
            conflicts=self._find_conflicts(df),
            collisions=[],  # Collisions sa wykrywane w module ingest
        )

    def _find_missing_critical(self, df: pl.DataFrame) -> list[DQListItem]:
        """Znajdz SKU z brakujacymi krytycznymi danymi."""
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
                    details=f"Brak krytycznej wartosci w {field}",
                ))

        return items

    def _find_suspect_outliers(self, df: pl.DataFrame) -> list[DQListItem]:
        """Znajdz SKU z podejrzanymi wartosciami (outliery)."""
        items = []

        for field, thresholds in self.OUTLIER_THRESHOLDS.items():
            if field not in df.columns:
                continue

            # Wartosci poza zakresem (ale > 0)
            outlier_mask = (
                (pl.col(field) > 0) &
                ((pl.col(field) < thresholds["low"]) | (pl.col(field) > thresholds["high"]))
            )
            outlier_rows = df.filter(outlier_mask)

            for row in outlier_rows.iter_rows(named=True):
                value = row[field]
                if value < thresholds["low"]:
                    detail = f"Bardzo mala wartosc: {value} < {thresholds['low']}"
                else:
                    detail = f"Bardzo duza wartosc: {value} > {thresholds['high']}"

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
        """Znajdz SKU z wymiarami blisko limitow nosnikow."""
        items = []

        if carrier_limits is None:
            # Domyslne limity typowego nosnika
            carrier_limits = {
                "length_mm": 600,
                "width_mm": 400,
                "height_mm": 350,
            }

        for field, limit in carrier_limits.items():
            if field not in df.columns:
                continue

            # Wartosci w zakresie (limit - threshold, limit]
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
                    details=f"Margines do limitu: {margin:.1f}mm (limit: {limit}mm)",
                ))

        return items

    def _find_duplicates(self, df: pl.DataFrame) -> list[DQListItem]:
        """Znajdz zduplikowane SKU."""
        items = []

        if "sku" not in df.columns:
            return items

        # Grupuj po SKU i znajdz duplikaty
        sku_counts = df.group_by("sku").agg(pl.len().alias("count"))
        duplicates = sku_counts.filter(pl.col("count") > 1)

        for row in duplicates.iter_rows(named=True):
            items.append(DQListItem(
                sku=str(row["sku"]),
                issue_type="duplicate",
                field="sku",
                value=str(row["count"]),
                details=f"SKU wystepuje {row['count']} razy",
            ))

        return items

    def _find_conflicts(self, df: pl.DataFrame) -> list[DQListItem]:
        """Znajdz SKU z konfliktami (rozne wartosci dla tego samego SKU)."""
        items = []

        if "sku" not in df.columns:
            return items

        # Znajdz SKU z wiecej niz 1 wystąpieniem
        sku_counts = df.group_by("sku").agg(pl.len().alias("count"))
        dup_skus = sku_counts.filter(pl.col("count") > 1)["sku"].to_list()

        if not dup_skus:
            return items

        # Dla kazdego zduplikowanego SKU sprawdz czy wartosci sie roznia
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
                        details=f"Rozne wartosci {field}: {unique_values}",
                    ))

        return items


def build_dq_lists(
    df: pl.DataFrame,
    carrier_limits: Optional[dict[str, float]] = None,
) -> DQLists:
    """Funkcja pomocnicza do budowy list DQ.

    Args:
        df: DataFrame z danymi Masterdata
        carrier_limits: Limity nosnikow

    Returns:
        DQLists
    """
    builder = DQListBuilder()
    return builder.build_all_lists(df, carrier_limits)
