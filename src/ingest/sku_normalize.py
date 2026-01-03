"""Normalizacja SKU i detekcja kolizji."""

import re
from dataclasses import dataclass, field

import polars as pl


@dataclass
class SKUCollision:
    """Kolizja SKU po normalizacji."""
    normalized_sku: str
    original_skus: list[str]
    collision_type: str  # "case", "whitespace", "special_chars"


@dataclass
class NormalizationResult:
    """Wynik normalizacji SKU."""
    df: pl.DataFrame
    collisions: list[SKUCollision] = field(default_factory=list)
    total_original: int = 0
    total_normalized: int = 0
    total_collisions: int = 0


class SKUNormalizer:
    """Normalizacja i walidacja SKU."""

    def __init__(
        self,
        uppercase: bool = True,
        strip_whitespace: bool = True,
        remove_special_chars: bool = False,
        replace_chars: dict[str, str] | None = None,
    ) -> None:
        """Inicjalizacja normalizera.

        Args:
            uppercase: Czy konwertowac do uppercase
            strip_whitespace: Czy usuwac biale znaki
            remove_special_chars: Czy usuwac znaki specjalne
            replace_chars: Mapowanie znakow do zamiany
        """
        self.uppercase = uppercase
        self.strip_whitespace = strip_whitespace
        self.remove_special_chars = remove_special_chars
        self.replace_chars = replace_chars or {}

    def normalize_sku(self, sku: str) -> str:
        """Normalizuj pojedynczy SKU.

        Args:
            sku: Oryginalny SKU

        Returns:
            Znormalizowany SKU
        """
        if sku is None:
            return ""

        result = str(sku)

        # Usun biale znaki
        if self.strip_whitespace:
            result = result.strip()
            result = re.sub(r"\s+", "", result)

        # Zamien znaki
        for old, new in self.replace_chars.items():
            result = result.replace(old, new)

        # Usun znaki specjalne
        if self.remove_special_chars:
            result = re.sub(r"[^a-zA-Z0-9\-_]", "", result)

        # Uppercase
        if self.uppercase:
            result = result.upper()

        return result

    def normalize_dataframe(
        self,
        df: pl.DataFrame,
        sku_column: str = "sku",
        output_column: str | None = None,
    ) -> NormalizationResult:
        """Normalizuj kolumne SKU w DataFrame.

        Args:
            df: DataFrame z kolumna SKU
            sku_column: Nazwa kolumny SKU
            output_column: Nazwa kolumny wynikowej (domyslnie nadpisuje)

        Returns:
            NormalizationResult z danymi i kolizjami
        """
        if output_column is None:
            output_column = sku_column

        # Pobierz oryginalne SKU
        original_skus = df[sku_column].to_list()
        total_original = len(original_skus)

        # Normalizuj
        normalized_skus = [self.normalize_sku(sku) for sku in original_skus]

        # Dodaj kolumne ze znormalizowanymi SKU
        result_df = df.with_columns([
            pl.Series(output_column, normalized_skus),
        ])

        # Wykryj kolizje
        collisions = self._detect_collisions(original_skus, normalized_skus)

        # Unikalne SKU po normalizacji
        total_normalized = len(set(normalized_skus))

        return NormalizationResult(
            df=result_df,
            collisions=collisions,
            total_original=total_original,
            total_normalized=total_normalized,
            total_collisions=len(collisions),
        )

    def _detect_collisions(
        self,
        original_skus: list[str],
        normalized_skus: list[str],
    ) -> list[SKUCollision]:
        """Wykryj kolizje po normalizacji.

        Kolizja wystepuje gdy rozne oryginalne SKU
        maja taki sam znormalizowany SKU.
        """
        # Grupuj oryginalne SKU po znormalizowanych
        normalized_to_original: dict[str, set[str]] = {}
        for orig, norm in zip(original_skus, normalized_skus):
            if norm not in normalized_to_original:
                normalized_to_original[norm] = set()
            normalized_to_original[norm].add(str(orig))

        collisions = []
        for norm_sku, orig_set in normalized_to_original.items():
            if len(orig_set) > 1:
                # Okresl typ kolizji
                collision_type = self._determine_collision_type(list(orig_set))
                collisions.append(SKUCollision(
                    normalized_sku=norm_sku,
                    original_skus=sorted(orig_set),
                    collision_type=collision_type,
                ))

        return collisions

    def _determine_collision_type(self, skus: list[str]) -> str:
        """Okresl typ kolizji."""
        # Sprawdz czy roznica tylko w wielkosci liter
        lowered = [s.lower() for s in skus]
        if len(set(lowered)) == 1:
            return "case"

        # Sprawdz czy roznica tylko w bialych znakach
        stripped = [re.sub(r"\s+", "", s) for s in skus]
        if len(set(stripped)) == 1:
            return "whitespace"

        return "special_chars"


def normalize_sku_column(
    df: pl.DataFrame,
    sku_column: str = "sku",
    uppercase: bool = True,
) -> NormalizationResult:
    """Funkcja pomocnicza do normalizacji SKU.

    Args:
        df: DataFrame
        sku_column: Nazwa kolumny SKU
        uppercase: Czy konwertowac do uppercase

    Returns:
        NormalizationResult
    """
    normalizer = SKUNormalizer(uppercase=uppercase)
    return normalizer.normalize_dataframe(df, sku_column)
