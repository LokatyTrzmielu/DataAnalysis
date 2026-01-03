"""Mapping Wizard - automatyczne i reczne mapowanie kolumn."""

from dataclasses import dataclass, field
from typing import Optional

import polars as pl


# ============================================================================
# Schematy mapowania
# ============================================================================

MASTERDATA_SCHEMA = {
    "sku": {
        "aliases": ["sku", "item", "article", "artykul", "indeks", "item_id", "product_id", "kod", "code", "nr"],
        "required": True,
        "description": "Unikalny identyfikator SKU",
    },
    "length": {
        "aliases": ["length", "dlugosc", "l", "dim_l", "length_mm", "dl", "len"],
        "required": True,
        "description": "Dlugosc (mm lub cm - zostanie skonwertowane)",
    },
    "width": {
        "aliases": ["width", "szerokosc", "w", "dim_w", "width_mm", "szer", "wid"],
        "required": True,
        "description": "Szerokosc (mm lub cm)",
    },
    "height": {
        "aliases": ["height", "wysokosc", "h", "dim_h", "height_mm", "wys", "hgt"],
        "required": True,
        "description": "Wysokosc (mm lub cm)",
    },
    "weight": {
        "aliases": ["weight", "waga", "mass", "kg", "weight_kg", "masa", "wgt"],
        "required": True,
        "description": "Waga (kg lub g)",
    },
    "stock": {
        "aliases": ["stock", "qty", "ilosc", "zapas", "quantity", "stan", "stock_qty", "on_hand"],
        "required": False,
        "description": "Ilosc na stanie (EA)",
    },
}

ORDERS_SCHEMA = {
    "order_id": {
        "aliases": ["order_id", "order", "zamowienie", "order_no", "order_number", "nr_zamowienia", "ordernr"],
        "required": True,
        "description": "Identyfikator zamowienia",
    },
    "line_id": {
        "aliases": ["line_id", "line", "linia", "line_no", "line_number", "pozycja"],
        "required": False,
        "description": "Identyfikator linii zamowienia",
    },
    "sku": {
        "aliases": ["sku", "item", "article", "artykul", "indeks", "item_id", "product_id", "kod"],
        "required": True,
        "description": "SKU produktu",
    },
    "quantity": {
        "aliases": ["quantity", "qty", "ilosc", "amount", "szt", "pieces", "units"],
        "required": True,
        "description": "Ilosc w linii (EA)",
    },
    "timestamp": {
        "aliases": ["timestamp", "datetime", "date", "data", "czas", "time", "created", "shipped", "order_date"],
        "required": True,
        "description": "Data/czas realizacji",
    },
}


@dataclass
class ColumnMapping:
    """Mapowanie pojedynczej kolumny."""

    target_field: str  # Pole docelowe (np. "sku", "length")
    source_column: str  # Kolumna zrodlowa z pliku
    confidence: float = 1.0  # Pewnosc mapowania (0-1)
    is_auto: bool = True  # Czy automatycznie wykryte


@dataclass
class MappingResult:
    """Wynik mapowania kolumn."""

    mappings: dict[str, ColumnMapping] = field(default_factory=dict)
    unmapped_columns: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Czy wszystkie wymagane pola sa zmapowane."""
        return len(self.missing_required) == 0

    def get_source_column(self, target_field: str) -> Optional[str]:
        """Pobierz kolumne zrodlowa dla pola docelowego."""
        mapping = self.mappings.get(target_field)
        return mapping.source_column if mapping else None


class MappingWizard:
    """Wizard do mapowania kolumn z auto-sugestiami."""

    def __init__(self, schema: dict[str, dict]) -> None:
        """Inicjalizacja wizarda.

        Args:
            schema: Schemat mapowania (MASTERDATA_SCHEMA lub ORDERS_SCHEMA)
        """
        self.schema = schema
        self._build_alias_index()

    def _build_alias_index(self) -> None:
        """Zbuduj indeks alias -> pole docelowe."""
        self.alias_index: dict[str, str] = {}
        for field_name, field_config in self.schema.items():
            for alias in field_config["aliases"]:
                self.alias_index[alias.lower()] = field_name

    def _normalize_column_name(self, name: str) -> str:
        """Normalizuj nazwe kolumny do porownania."""
        # Lowercase, usun biale znaki i znaki specjalne
        normalized = name.lower().strip()
        normalized = normalized.replace(" ", "_").replace("-", "_")
        # Usun podkreslniki na koncu
        normalized = normalized.rstrip("_")
        return normalized

    def auto_map(self, columns: list[str]) -> MappingResult:
        """Automatyczne mapowanie kolumn.

        Args:
            columns: Lista kolumn z pliku zrodlowego

        Returns:
            MappingResult z sugerowanymi mapowaniami
        """
        result = MappingResult()
        used_columns: set[str] = set()

        # Probuj zmapowac kazde pole
        for field_name, field_config in self.schema.items():
            best_match = self._find_best_match(columns, field_config["aliases"], used_columns)

            if best_match:
                column, confidence = best_match
                result.mappings[field_name] = ColumnMapping(
                    target_field=field_name,
                    source_column=column,
                    confidence=confidence,
                    is_auto=True,
                )
                used_columns.add(column)
            elif field_config["required"]:
                result.missing_required.append(field_name)

        # Kolumny niezmapowane
        result.unmapped_columns = [c for c in columns if c not in used_columns]

        return result

    def _find_best_match(
        self,
        columns: list[str],
        aliases: list[str],
        used: set[str],
    ) -> Optional[tuple[str, float]]:
        """Znajdz najlepsze dopasowanie kolumny do aliasow.

        Returns:
            Tuple (kolumna, pewnosc) lub None
        """
        best_match = None
        best_score = 0.0

        for column in columns:
            if column in used:
                continue

            normalized = self._normalize_column_name(column)

            for alias in aliases:
                alias_normalized = alias.lower()

                # Dokladne dopasowanie
                if normalized == alias_normalized:
                    return (column, 1.0)

                # Czesciowe dopasowanie
                if alias_normalized in normalized or normalized in alias_normalized:
                    score = len(alias_normalized) / max(len(normalized), len(alias_normalized))
                    if score > best_score:
                        best_score = score
                        best_match = column

        if best_match and best_score >= 0.5:
            return (best_match, best_score)

        return None

    def apply_mapping(self, df: pl.DataFrame, mapping: MappingResult) -> pl.DataFrame:
        """Zastosuj mapowanie do DataFrame.

        Args:
            df: Oryginalny DataFrame
            mapping: Wynik mapowania

        Returns:
            DataFrame z przemianowanymi kolumnami
        """
        rename_map = {}
        select_columns = []

        for field_name, col_mapping in mapping.mappings.items():
            rename_map[col_mapping.source_column] = field_name
            select_columns.append(col_mapping.source_column)

        # Wybierz i przemianuj kolumny
        result = df.select(select_columns)
        result = result.rename(rename_map)

        return result

    def get_suggestions(self, column: str) -> list[tuple[str, float]]:
        """Pobierz sugestie mapowania dla kolumny.

        Args:
            column: Nazwa kolumny

        Returns:
            Lista (pole_docelowe, pewnosc) posortowana malejaco
        """
        suggestions = []
        normalized = self._normalize_column_name(column)

        for field_name, field_config in self.schema.items():
            best_score = 0.0

            for alias in field_config["aliases"]:
                alias_normalized = alias.lower()

                if normalized == alias_normalized:
                    best_score = 1.0
                    break
                elif alias_normalized in normalized or normalized in alias_normalized:
                    score = len(alias_normalized) / max(len(normalized), len(alias_normalized))
                    best_score = max(best_score, score)

            if best_score > 0:
                suggestions.append((field_name, best_score))

        # Sortuj malejaco po pewnosci
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions


def create_masterdata_wizard() -> MappingWizard:
    """Utworz wizard dla Masterdata."""
    return MappingWizard(MASTERDATA_SCHEMA)


def create_orders_wizard() -> MappingWizard:
    """Utworz wizard dla Orders."""
    return MappingWizard(ORDERS_SCHEMA)
