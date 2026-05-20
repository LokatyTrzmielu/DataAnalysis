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
            "sku", "item", "article", "product", "product_id", "product_no",
            "product_number", "prod_id", "prodno", "prod_no", "item_id",
            "item_code", "item_number", "item_no", "itemno", "itemnr",
            "article_id", "article_code", "article_no", "article_number",
            "articleno", "artno", "code", "product_code", "material",
            "material_id", "material_no", "material_number", "materialno",
            "materialnumber", "matnr", "mat_no", "part", "part_number",
            "part_no", "partno", "pn", "upc", "ean", "ean13", "ean_code",
            "barcode", "barcode_ean", "gtin", "catalog_number", "catalog_no",
            "catalogue_number", "reference", "ref", "ref_no", "model",
            "model_no", "model_number", "variant", "variant_id", "vendor_code",
            "supplier_code", "supplier_id", "sap_code", "iso_code", "asin",
            "manufacturer_code", "manufacturer_id",
            # Polish
            "artykul", "art", "art_nr", "nr_artykulu", "numer_artykulu",
            "nazwa_artykulu", "indeks", "indeks_handlowy", "indeks_materialowy",
            "indeks_materialu", "indeks_towarowy", "indeks_towaru",
            "indeks_wewnetrzny", "nazwa_indeks", "nazwa_indeksu",
            "numer_indeksu", "id_indeksu", "kod", "kod_produktu",
            "kod_towaru", "kod_wewnetrzny", "kod_kreskowy", "nr", "nr_kat",
            "numer", "numer_katalogowy", "symbol", "symbol_towaru",
            "symbol_produktu", "towar", "produkt", "id_produktu",
            "id_towaru", "nazwa", "nazwa_produktu", "nazwa_towaru",
            "model_produktu", "wariant", "asortyment", "asortyment_id",
        ],
        "required": True,
        "description": "Unique SKU identifier",
    },
    "length": {
        "aliases": [
            # English
            "length", "l", "len", "lenght", "lng", "long", "depth", "d",
            "dim_l", "dim_d", "dimension_l", "dimension_d",
            "length_mm", "length_cm", "length_m", "length_inch", "length_in",
            "outer_length", "pack_length", "box_length", "carton_length",
            "case_length", "unit_length",
            # Polish
            "dlugosc", "dl", "dlug", "dlugosc_mm", "dlugosc_cm",
            "dl_mm", "dl_cm", "wymiar_l", "wymiar_d", "wymiar_dlugosc",
            "glebokosc", "gleb", "karton_dlugosc", "karton_dl",
            "dlugosc_opakowania", "dlugosc_kartonu",
            "bok_a", "wymiar_a",
        ],
        "required": True,
        "description": "Length (mm or cm - will be converted)",
    },
    "width": {
        "aliases": [
            # English
            "width", "w", "wid", "wdt", "breadth", "broad",
            "dim_w", "dimension_w",
            "width_mm", "width_cm", "width_m", "width_inch", "width_in",
            "outer_width", "pack_width", "box_width", "carton_width",
            "case_width", "unit_width",
            # Polish
            "szerokosc", "szer", "szerok", "szerokosc_mm", "szerokosc_cm",
            "szer_mm", "szer_cm", "wymiar_w", "wymiar_s", "wymiar_szerokosc",
            "karton_szerokosc", "karton_szer", "szerokosc_opakowania",
            "szerokosc_kartonu", "bok_b", "wymiar_b",
        ],
        "required": True,
        "description": "Width (mm or cm)",
    },
    "height": {
        "aliases": [
            # English
            "height", "h", "hgt", "ht", "tall", "z",
            "dim_h", "dim_z", "dimension_h", "dimension_z",
            "height_mm", "height_cm", "height_m", "height_inch", "height_in",
            "outer_height", "pack_height", "box_height", "carton_height",
            "case_height", "unit_height", "thickness",
            # Polish
            "wysokosc", "wys", "wysok", "wysokosc_mm", "wysokosc_cm",
            "wys_mm", "wys_cm", "wymiar_h", "wymiar_z", "wymiar_wysokosc",
            "karton_wysokosc", "karton_wys", "wysokosc_opakowania",
            "wysokosc_kartonu", "bok_c", "wymiar_c", "grubosc",
        ],
        "required": True,
        "description": "Height (mm or cm)",
    },
    "weight": {
        "aliases": [
            # English
            "weight", "wgt", "wt", "mass", "kg", "g", "grams", "gram",
            "weight_kg", "weight_g", "weight_grams", "weight_lbs", "weight_oz",
            "net_weight", "gross_weight", "unit_weight", "unit_weight_kg",
            "unit_mass", "item_weight", "product_weight", "pack_weight",
            "box_weight", "carton_weight", "case_weight",
            "peso",
            # Polish
            "waga", "wagajedn", "waga_jednostkowa", "waga_jedn",
            "waga_kg", "waga_g", "waga_netto", "waga_brutto",
            "masa", "masa_kg", "masa_g", "masa_netto", "masa_brutto",
            "ciezar", "ciezar_jednostkowy", "ciezar_kg",
        ],
        "required": True,
        "description": "Weight (g or kg - will be auto-detected)",
    },
    "stock": {
        "aliases": [
            # English
            "stock", "qty", "quantity", "stock_qty", "stock_quantity",
            "stock_level", "stock_on_hand", "stock_count", "current_stock",
            "actual_stock", "wms_stock", "warehouse_stock",
            "on_hand", "on_hand_qty", "oh_qty", "qty_on_hand",
            "quantity_on_hand", "quantity_in_stock", "in_stock",
            "inventory", "inventory_qty", "inventory_count", "inventory_level",
            "available", "available_qty", "available_quantity",
            "balance", "units", "pieces", "pcs", "count", "free_stock",
            # Polish
            "ilosc", "ilosc_na_stanie", "ilosc_w_mag", "ilosc_dostepna", "ilosc_w_magazynie",
            "liczba", "liczba_szt", "liczba_sztuk",
            "zapas", "zapasy", "stan", "stany", "stan_mag",
            "stany_magazynowe", "stan_magazynowy", "stan_magazynu",
            "stan_aktualny", "magazyn", "mag",
            "dostepne", "dostepnosc", "do_wydania", "wolne", "wolny_stan",
            "szt", "sztuk", "sztuki",
        ],
        "required": True,
        "description": "Stock quantity (EA)",
    },
}

ORDERS_SCHEMA = {
    "order_id": {
        "aliases": [
            # English
            "order_id", "order", "orderid", "orderno", "ordernr",
            "order_no", "order_number", "order_nr", "order_ref",
            "order_reference", "sales_order", "sales_order_no",
            "sales_order_number", "so", "so_no", "so_number",
            "document_id", "document_no", "document_number", "doc_id",
            "doc_no", "doc_number", "transaction_id", "transaction_no",
            "invoice", "invoice_id", "invoice_no", "invoice_number",
            "pick_id", "pickorder", "pick_order", "pick_no", "pick_number",
            "wave", "wave_id", "wave_no", "wz", "wz_id", "wz_no", "nr_wz",
            "wz_nr", "delivery", "delivery_id", "delivery_no",
            "delivery_number", "shipment", "shipment_id", "shipment_no",
            "ship_no", "ship_id", "release", "release_id",
            # Polish
            "zamowienie", "zamowienia", "nr_zamowienia", "numer_zamowienia",
            "id_zamowienia", "zam", "zam_nr", "nr_zam",
            "faktura", "fv", "nr_faktury", "numer_faktury",
            "dokument", "dokumenty", "nr_dokumentu", "numer_dokumentu",
            "id_dokumentu", "wydanie", "wydanie_zewnetrzne",
            "zlecenie", "zlecenia", "nr_zlecenia", "numer_zlecenia",
            "id_zlecenia", "wysylka", "nr_wysylki", "transakcja",
        ],
        "required": True,
        "description": "Order identifier",
    },
    "sku": {
        "aliases": [
            # English
            "sku", "item", "item_id", "item_code", "item_no", "item_number",
            "itemno", "article", "article_id", "article_code", "article_no",
            "article_number", "product", "product_id", "product_code",
            "product_no", "product_number", "code", "material",
            "material_id", "material_no", "material_number", "matnr",
            "part", "part_no", "part_number", "partno", "pn",
            "model", "model_no", "model_number", "barcode", "ean",
            "ean13", "gtin", "upc", "reference", "ref", "ref_no",
            "asin", "vendor_code", "supplier_code", "sap_code",
            # Polish
            "artykul", "art", "art_nr", "nr_artykulu", "indeks",
            "indeks_handlowy", "indeks_towaru", "indeks_materialu",
            "kod", "kod_produktu", "kod_towaru", "kod_kreskowy",
            "kod_wewnetrzny", "symbol", "symbol_towaru", "symbol_produktu",
            "towar", "produkt", "id_produktu", "id_towaru", "nazwa",
            "nazwa_produktu", "nazwa_towaru", "numer_indeksu",
            "id_indeksu", "model_produktu", "wariant",
        ],
        "required": True,
        "description": "Product SKU",
    },
    "quantity": {
        "aliases": [
            # English
            "quantity", "qty", "amount", "units", "pieces", "pcs", "count",
            "ea", "each", "unit_count", "line_qty", "line_quantity",
            "ordered_qty", "ordered_quantity", "order_qty", "order_quantity",
            "qty_ordered", "quantity_ordered", "shipped_qty",
            "shipped_quantity", "qty_shipped", "picked", "picked_qty",
            "picked_quantity", "qty_picked", "delivered_qty",
            "delivered_quantity", "requested_qty",
            # Polish
            "ilosc", "ilosc_zamowiona", "zamowiona_ilosc",
            "ilosc_skompletowana", "ilosc_wydana", "ilosc_dostarczona",
            "szt", "sztuk", "sztuki", "liczba", "liczba_sztuk",
            "liczba_szt", "zamowiona", "wydane", "skompletowane",
        ],
        "required": True,
        "description": "Line quantity (EA)",
    },
    "date": {
        "aliases": [
            # English
            "datetime", "timestamp", "time_stamp", "date", "dt",
            "created", "created_at", "creation_date", "create_date",
            "shipped", "shipped_at", "ship_date", "shipment_date",
            "order_date", "order_dt", "orderdate", "order_created",
            "delivery_date", "deliverydate", "fulfillment_date",
            "transaction_date", "updated_at", "processed_date",
            "process_date", "pick_date", "release_date", "request_date",
            "due_date", "day", "business_date",
            # Polish
            "data", "data_zamowienia", "data_zam", "data_zlozenia",
            "data_utworzenia", "data_zalozenia", "data_dokumentu",
            "data_wysylki", "data_dostawy", "data_realizacji",
            "data_kompletacji", "data_wydania", "dzien",
            "data_transakcji", "data_pickingu", "data_zlecenia",
        ],
        "required": True,
        "description": "Date or datetime column",
    },
    "time": {
        "aliases": [
            # English
            "time", "hour", "time_of_day", "order_time", "ship_time",
            "pick_time", "creation_time", "create_time", "transaction_time",
            "process_time",
            # Polish
            "czas", "czas_zamowienia", "godzina", "godzina_zamowienia",
            "godz", "godz_zamowienia", "czas_realizacji",
            "czas_utworzenia", "czas_wydania",
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

        # Step 2: Exact-alias pass across all fields BEFORE any partial matching.
        # Prevents a partial alias of one field (e.g. "stock_code" in sku) from
        # stealing a column that exactly matches another field (e.g. "stock" → stock).
        for field_name, field_config in self.schema.items():
            if field_name in result.mappings:
                continue

            exact = self._find_exact_match(
                columns, field_config["aliases"], used_columns
            )
            if exact:
                result.mappings[field_name] = ColumnMapping(
                    target_field=field_name,
                    source_column=exact,
                    confidence=1.0,
                    is_auto=True,
                )
                used_columns.add(exact)

        # Step 3: Partial-match pass for fields still unmapped.
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

    def _find_exact_match(
        self,
        columns: list[str],
        aliases: list[str],
        used: set[str],
    ) -> Optional[str]:
        """Find first column whose normalized name equals any alias exactly."""
        alias_set = {a.lower() for a in aliases}
        for column in columns:
            if column in used:
                continue
            if self._normalize_column_name(column) in alias_set:
                return column
        return None

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

        if best_match and best_score >= 0.4:
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
