"""Mapping Wizard - automatic and manual column mapping."""

from dataclasses import dataclass, field
from typing import Optional

import polars as pl


# ============================================================================
# Mapping schemas
# ============================================================================

MASTERDATA_SCHEMA = {
    "sku": {
        "aliases": ["sku", "item", "article", "artykul", "indeks", "item_id", "product_id", "kod", "code", "nr"],
        "required": True,
        "description": "Unique SKU identifier",
    },
    "length": {
        "aliases": ["length", "dlugosc", "l", "dim_l", "length_mm", "dl", "len"],
        "required": True,
        "description": "Length (mm or cm - will be converted)",
    },
    "width": {
        "aliases": ["width", "szerokosc", "w", "dim_w", "width_mm", "szer", "wid"],
        "required": True,
        "description": "Width (mm or cm)",
    },
    "height": {
        "aliases": ["height", "wysokosc", "h", "dim_h", "height_mm", "wys", "hgt"],
        "required": True,
        "description": "Height (mm or cm)",
    },
    "weight": {
        "aliases": ["weight", "waga", "mass", "kg", "weight_kg", "masa", "wgt"],
        "required": True,
        "description": "Weight (kg or g)",
    },
    "stock": {
        "aliases": ["stock", "qty", "ilosc", "zapas", "quantity", "stan", "stock_qty", "on_hand"],
        "required": False,
        "description": "Stock quantity (EA)",
    },
}

ORDERS_SCHEMA = {
    "order_id": {
        "aliases": ["order_id", "order", "zamowienie", "order_no", "order_number", "nr_zamowienia", "ordernr"],
        "required": True,
        "description": "Order identifier",
    },
    "line_id": {
        "aliases": ["line_id", "line", "linia", "line_no", "line_number", "pozycja"],
        "required": False,
        "description": "Order line identifier",
    },
    "sku": {
        "aliases": ["sku", "item", "article", "artykul", "indeks", "item_id", "product_id", "kod"],
        "required": True,
        "description": "Product SKU",
    },
    "quantity": {
        "aliases": ["quantity", "qty", "ilosc", "amount", "szt", "pieces", "units"],
        "required": True,
        "description": "Line quantity (EA)",
    },
    "timestamp": {
        "aliases": ["timestamp", "datetime", "date", "data", "czas", "time", "created", "shipped", "order_date"],
        "required": True,
        "description": "Fulfillment date/time",
    },
}


@dataclass
class ColumnMapping:
    """Single column mapping."""

    target_field: str  # Target field (e.g., "sku", "length")
    source_column: str  # Source column from file
    confidence: float = 1.0  # Mapping confidence (0-1)
    is_auto: bool = True  # Whether auto-detected


@dataclass
class MappingResult:
    """Column mapping result."""

    mappings: dict[str, ColumnMapping] = field(default_factory=dict)
    unmapped_columns: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Whether all required fields are mapped."""
        return len(self.missing_required) == 0

    def get_source_column(self, target_field: str) -> Optional[str]:
        """Get source column for target field."""
        mapping = self.mappings.get(target_field)
        return mapping.source_column if mapping else None


class MappingWizard:
    """Wizard for column mapping with auto-suggestions."""

    def __init__(self, schema: dict[str, dict]) -> None:
        """Initialize wizard.

        Args:
            schema: Mapping schema (MASTERDATA_SCHEMA or ORDERS_SCHEMA)
        """
        self.schema = schema
        self._build_alias_index()

    def _build_alias_index(self) -> None:
        """Build alias -> target field index."""
        self.alias_index: dict[str, str] = {}
        for field_name, field_config in self.schema.items():
            for alias in field_config["aliases"]:
                self.alias_index[alias.lower()] = field_name

    def _normalize_column_name(self, name: str) -> str:
        """Normalize column name for comparison."""
        # Lowercase, remove whitespace and special characters
        normalized = name.lower().strip()
        normalized = normalized.replace(" ", "_").replace("-", "_")
        # Remove trailing underscores
        normalized = normalized.rstrip("_")
        return normalized

    def auto_map(self, columns: list[str]) -> MappingResult:
        """Automatic column mapping.

        Args:
            columns: List of columns from source file

        Returns:
            MappingResult with suggested mappings
        """
        result = MappingResult()
        used_columns: set[str] = set()

        # Try to map each field
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

        # Unmapped columns
        result.unmapped_columns = [c for c in columns if c not in used_columns]

        return result

    def _find_best_match(
        self,
        columns: list[str],
        aliases: list[str],
        used: set[str],
    ) -> Optional[tuple[str, float]]:
        """Find best column match for aliases.

        Returns:
            Tuple (column, confidence) or None
        """
        best_match = None
        best_score = 0.0

        for column in columns:
            if column in used:
                continue

            normalized = self._normalize_column_name(column)

            for alias in aliases:
                alias_normalized = alias.lower()

                # Exact match
                if normalized == alias_normalized:
                    return (column, 1.0)

                # Partial match
                if alias_normalized in normalized or normalized in alias_normalized:
                    score = len(alias_normalized) / max(len(normalized), len(alias_normalized))
                    if score > best_score:
                        best_score = score
                        best_match = column

        if best_match and best_score >= 0.5:
            return (best_match, best_score)

        return None

    def apply_mapping(self, df: pl.DataFrame, mapping: MappingResult) -> pl.DataFrame:
        """Apply mapping to DataFrame.

        Args:
            df: Original DataFrame
            mapping: Mapping result

        Returns:
            DataFrame with renamed columns
        """
        rename_map = {}
        select_columns = []

        for field_name, col_mapping in mapping.mappings.items():
            rename_map[col_mapping.source_column] = field_name
            select_columns.append(col_mapping.source_column)

        # Select and rename columns
        result = df.select(select_columns)
        result = result.rename(rename_map)

        return result

    def get_suggestions(self, column: str) -> list[tuple[str, float]]:
        """Get mapping suggestions for column.

        Args:
            column: Column name

        Returns:
            List of (target_field, confidence) sorted descending
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

        # Sort descending by confidence
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions


def create_masterdata_wizard() -> MappingWizard:
    """Create wizard for Masterdata."""
    return MappingWizard(MASTERDATA_SCHEMA)


def create_orders_wizard() -> MappingWizard:
    """Create wizard for Orders."""
    return MappingWizard(ORDERS_SCHEMA)
