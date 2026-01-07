"""Ingest module - import danych, Mapping Wizard."""

from src.ingest.readers import FileReader, read_file
from src.ingest.mapping import (
    MappingWizard,
    MappingResult,
    ColumnMapping,
    MASTERDATA_SCHEMA,
    ORDERS_SCHEMA,
    create_masterdata_wizard,
    create_orders_wizard,
)
from src.ingest.mapping_history import (
    MappingHistoryService,
    MappingHistoryEntry,
)
from src.ingest.units import (
    UnitDetector,
    UnitConverter,
    LengthUnit,
    WeightUnit,
)
from src.ingest.sku_normalize import (
    SKUNormalizer,
    NormalizationResult,
    SKUCollision,
    normalize_sku_column,
)
from src.ingest.pipeline import (
    IngestResult,
    MasterdataIngestPipeline,
    OrdersIngestPipeline,
    ingest_masterdata,
    ingest_orders,
)

__all__ = [
    # Readers
    "FileReader",
    "read_file",
    # Mapping
    "MappingWizard",
    "MappingResult",
    "ColumnMapping",
    "MASTERDATA_SCHEMA",
    "ORDERS_SCHEMA",
    "create_masterdata_wizard",
    "create_orders_wizard",
    # Mapping History
    "MappingHistoryService",
    "MappingHistoryEntry",
    # Units
    "UnitDetector",
    "UnitConverter",
    "LengthUnit",
    "WeightUnit",
    # SKU
    "SKUNormalizer",
    "NormalizationResult",
    "SKUCollision",
    "normalize_sku_column",
    # Pipeline
    "IngestResult",
    "MasterdataIngestPipeline",
    "OrdersIngestPipeline",
    "ingest_masterdata",
    "ingest_orders",
]
