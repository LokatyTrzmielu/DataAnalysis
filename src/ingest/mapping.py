"""Mapping Wizard - automatic and manual column mapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from src.ingest.mapping_history import MappingHistoryService


# ============================================================================
# Mapping schemas
# ============================================================================

MASTERDATA_SCHEMA = {
    "sku": {
        "aliases": [
            # English
            "sku", "item", "article", "product_id", "item_id", "code", "item_code",
            "product_code", "material", "material_id", "part", "part_number",
            "part_no", "pn", "upc", "ean", "barcode", "gtin", "catalog_number",
            "item_number", "item_no", "reference", "ref", "stock_code",
            # Polish
            "artykul", "indeks", "kod", "nr", "numer", "numer_artykulu",
            "kod_produktu", "kod_towaru", "indeks_materialowy", "indeks_towarowy",
            "symbol", "symbol_towaru", "towar", "produkt", "id_produktu", "id_towaru",
        ],
        "required": True,
        "description": "Unique SKU identifier",
    },
    "length": {
        "aliases": [
            # English
            "length", "l", "len", "dim_l", "length_mm", "length_cm", "length_m",
            "dimension_l", "lng", "long", "depth", "d", "dim_d",
            # Polish
            "dlugosc", "dl", "dlug", "wymiar_l", "wymiar_dlugosc", "glebokosc",
        ],
        "required": True,
        "description": "Length (mm or cm - will be converted)",
    },
    "width": {
        "aliases": [
            # English
            "width", "w", "wid", "dim_w", "width_mm", "width_cm", "width_m",
            "dimension_w", "breadth", "broad", "wdt",
            # Polish
            "szerokosc", "szer", "szerok", "wymiar_w", "wymiar_szerokosc",
        ],
        "required": True,
        "description": "Width (mm or cm)",
    },
    "height": {
        "aliases": [
            # English
            "height", "h", "hgt", "dim_h", "height_mm", "height_cm", "height_m",
            "dimension_h", "ht", "tall", "z", "dim_z",
            # Polish
            "wysokosc", "wys", "wysok", "wymiar_h", "wymiar_wysokosc",
        ],
        "required": True,
        "description": "Height (mm or cm)",
    },
    "weight": {
        "aliases": [
            # English
            "weight", "wgt", "mass", "kg", "weight_kg", "weight_g", "grams", "gram",
            "g", "weight_grams", "net_weight", "gross_weight", "unit_weight",
            "item_weight", "product_weight", "wt",
            # Polish
            "waga", "masa", "ciezar", "waga_kg", "waga_g", "waga_jednostkowa",
            "masa_netto", "masa_brutto",
        ],
        "required": True,
        "description": "Weight (g or kg - will be auto-detected)",
    },
    "stock": {
        "aliases": [
            # English
            "stock", "qty", "quantity", "stock_qty", "on_hand", "inventory",
            "available", "available_qty", "balance", "units", "pieces", "pcs",
            "count", "stock_level", "stock_quantity", "inventory_qty",
            # Polish
            "ilosc", "zapas", "stan", "szt", "sztuk", "stan_magazynowy",
            "dostepne", "ilosc_dostepna", "magazyn",
        ],
        "required": True,
        "description": "Stock quantity (EA)",
    },
}

ORDERS_SCHEMA = {
    "order_id": {
        "aliases": [
            # English
            "order_id", "order", "order_no", "order_number", "ordernr", "order_ref",
            "order_reference", "sales_order", "so", "so_number", "document_id",
            "doc_id", "transaction_id", "invoice", "invoice_no",
            # Polish
            "zamowienie", "nr_zamowienia", "numer_zamowienia", "id_zamowienia",
            "faktura", "nr_faktury", "dokument",
        ],
        "required": True,
        "description": "Order identifier",
    },
    "line_id": {
        "aliases": [
            # English
            "line_id", "line", "line_no", "line_number", "line_item", "item_line",
            "row", "row_id", "row_number", "sequence", "seq", "position",
            # Polish
            "linia", "pozycja", "nr_linii", "numer_linii", "wiersz",
        ],
        "required": False,
        "description": "Order line identifier",
    },
    "sku": {
        "aliases": [
            # English
            "sku", "item", "article", "product_id", "item_id", "code", "item_code",
            "product_code", "material", "part", "part_number",
            # Polish
            "artykul", "indeks", "kod", "kod_produktu", "kod_towaru",
            "symbol", "towar", "produkt",
        ],
        "required": True,
        "description": "Product SKU",
    },
    "quantity": {
        "aliases": [
            # English
            "quantity", "qty", "amount", "units", "pieces", "pcs", "count",
            "ordered_qty", "shipped_qty", "line_qty", "unit_count", "ea",
            # Polish
            "ilosc", "szt", "sztuk", "zamowiona_ilosc", "liczba",
        ],
        "required": True,
        "description": "Line quantity (EA)",
    },
    "date": {
        "aliases": [
            # English
            "datetime", "timestamp", "date", "created", "shipped",
            "order_date", "ship_date", "delivery_date", "fulfillment_date",
            "transaction_date", "created_at", "updated_at", "processed_date",
            # Polish
            "data", "data_zamowienia", "data_wysylki", "data_dostawy",
            "data_realizacji",
        ],
        "required": True,
        "description": "Date or datetime column",
    },
    "time": {
        "aliases": [
            # English
            "time", "hour", "time_of_day", "order_time", "ship_time",
            # Polish
            "czas", "godzina",
        ],
        "required": False,
        "description": "Time column (when date and time are separate)",
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
    """Wizard for column mapping with auto-suggestions and history learning."""

    def __init__(
        self,
        schema: dict[str, dict],
        schema_type: str = "masterdata",
        history_service: Optional[MappingHistoryService] = None,
    ) -> None:
        """Initialize wizard.

        Args:
            schema: Mapping schema (MASTERDATA_SCHEMA or ORDERS_SCHEMA)
            schema_type: "masterdata" or "orders"
            history_service: Optional history service for learning from corrections
        """
        self.schema = schema
        self.schema_type = schema_type
        self.history_service = history_service
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

    def auto_map(self, columns: list[str], client_name: str = "") -> MappingResult:
        """Automatic column mapping with history priority.

        Args:
            columns: List of columns from source file
            client_name: Optional client name for context-aware mapping

        Returns:
            MappingResult with suggested mappings
        """
        result = MappingResult()
        used_columns: set[str] = set()

        # Step 1: Try history mappings first (highest priority)
        if self.history_service is not None:
            history_entries = self.history_service.get_history_mappings(
                self.schema_type, client_name
            )

            for entry in history_entries:
                if entry.target_field not in self.schema:
                    continue
                if entry.target_field in result.mappings:
                    continue

                # Find matching column
                for column in columns:
                    if column in used_columns:
                        continue
                    normalized = self._normalize_column_name(column)
                    if normalized == entry.source_column:
                        # Check blacklist
                        if self.history_service.is_blacklisted(
                            column, entry.target_field, self.schema_type
                        ):
                            continue

                        result.mappings[entry.target_field] = ColumnMapping(
                            target_field=entry.target_field,
                            source_column=column,
                            confidence=0.95,  # History match
                            is_auto=True,
                        )
                        used_columns.add(column)
                        break

        # Step 2: Fall back to alias matching for unmapped fields
        for field_name, field_config in self.schema.items():
            if field_name in result.mappings:
                continue

            best_match = self._find_best_match(
                columns, field_config["aliases"], used_columns
            )

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

    def record_user_corrections(
        self,
        original: MappingResult,
        final: MappingResult,
        client_name: str = "",
    ) -> None:
        """Record user corrections to history.

        Compares original auto-mapping with final mapping after user edits.
        Only records mappings that were corrected by the user.

        Args:
            original: Original auto-mapping result
            final: Final mapping after user corrections
            client_name: Client name for context
        """
        if self.history_service is None:
            return

        for field_name, final_mapping in final.mappings.items():
            original_mapping = original.mappings.get(field_name)

            # Determine if this was a user correction
            is_correction = (
                original_mapping is None
                or original_mapping.source_column != final_mapping.source_column
                or not final_mapping.is_auto
            )

            # Only record corrections, not auto-matched values
            if is_correction:
                self.history_service.record_mapping(
                    source_column=final_mapping.source_column,
                    target_field=field_name,
                    schema_type=self.schema_type,
                    client_pattern=client_name,
                    is_user_correction=True,
                )


def create_masterdata_wizard(
    history_service: Optional[MappingHistoryService] = None,
) -> MappingWizard:
    """Create wizard for Masterdata.

    Args:
        history_service: Optional history service for learning

    Returns:
        MappingWizard configured for masterdata schema
    """
    return MappingWizard(MASTERDATA_SCHEMA, "masterdata", history_service)


def create_orders_wizard(
    history_service: Optional[MappingHistoryService] = None,
) -> MappingWizard:
    """Create wizard for Orders.

    Args:
        history_service: Optional history service for learning

    Returns:
        MappingWizard configured for orders schema
    """
    return MappingWizard(ORDERS_SCHEMA, "orders", history_service)
