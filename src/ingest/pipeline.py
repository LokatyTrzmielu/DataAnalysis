"""Data import pipeline - integration of all steps."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import polars as pl

from src.ingest.readers import FileReader
from src.ingest.mapping import (
    MappingWizard,
    MappingResult,
    create_masterdata_wizard,
    create_orders_wizard,
)
from src.ingest.units import UnitConverter, LengthUnit, WeightUnit
from src.ingest.sku_normalize import SKUNormalizer, NormalizationResult


@dataclass
class IngestResult:
    """Data import result."""
    df: pl.DataFrame
    mapping_result: MappingResult
    sku_normalization: Optional[NormalizationResult] = None
    source_file: Optional[Path] = None
    rows_imported: int = 0
    columns_mapped: int = 0
    warnings: list[str] = field(default_factory=list)


class MasterdataIngestPipeline:
    """Masterdata import pipeline."""

    def __init__(
        self,
        auto_detect_units: bool = True,
        normalize_sku: bool = True,
        length_unit: Optional[LengthUnit] = None,
        weight_unit: Optional[WeightUnit] = None,
    ) -> None:
        """Initialize pipeline.

        Args:
            auto_detect_units: Automatic unit detection
            normalize_sku: SKU normalization
            length_unit: Length unit (if known)
            weight_unit: Weight unit (if known)
        """
        self.auto_detect_units = auto_detect_units
        self.normalize_sku = normalize_sku
        self.length_unit = length_unit
        self.weight_unit = weight_unit

        self.wizard = create_masterdata_wizard()
        self.unit_converter = UnitConverter()
        self.sku_normalizer = SKUNormalizer(uppercase=True)

    def run(
        self,
        file_path: str | Path,
        mapping: Optional[MappingResult] = None,
        **read_kwargs,
    ) -> IngestResult:
        """Run import pipeline.

        Args:
            file_path: Path to file
            mapping: Ready mapping (if None, automatic)
            **read_kwargs: Additional arguments for FileReader

        Returns:
            IngestResult with data and metadata
        """
        warnings: list[str] = []
        file_path = Path(file_path)

        # 1. Read file
        reader = FileReader(file_path)
        df = reader.read(**read_kwargs)

        # 2. Column mapping
        if mapping is None:
            mapping = self.wizard.auto_map(df.columns)

        if not mapping.is_complete:
            missing = ", ".join(mapping.missing_required)
            warnings.append(f"Missing required columns: {missing}")

        # Apply mapping
        df = self.wizard.apply_mapping(df, mapping)

        # 3. Unit conversion (if we have dimensions)
        if all(col in df.columns for col in ["length", "width", "height"]):
            df = self.unit_converter.convert_dimensions_to_mm(
                df,
                length_col="length",
                width_col="width",
                height_col="height",
                auto_detect=self.auto_detect_units,
                source_unit=self.length_unit,
            )
            # Rename to target names
            df = df.rename({
                "length": "length_mm",
                "width": "width_mm",
                "height": "height_mm",
            })

        if "weight" in df.columns:
            df = self.unit_converter.convert_weight_to_kg(
                df,
                weight_col="weight",
                auto_detect=self.auto_detect_units,
                source_unit=self.weight_unit,
            )
            df = df.rename({"weight": "weight_kg"})

        if "stock" in df.columns:
            df = df.rename({"stock": "stock_qty"})

        # 4. SKU normalization
        sku_result = None
        if self.normalize_sku and "sku" in df.columns:
            sku_result = self.sku_normalizer.normalize_dataframe(df, "sku")
            df = sku_result.df

            if sku_result.total_collisions > 0:
                warnings.append(
                    f"Detected {sku_result.total_collisions} SKU collisions after normalization"
                )

        return IngestResult(
            df=df,
            mapping_result=mapping,
            sku_normalization=sku_result,
            source_file=file_path,
            rows_imported=len(df),
            columns_mapped=len(mapping.mappings),
            warnings=warnings,
        )


class OrdersIngestPipeline:
    """Orders import pipeline."""

    def __init__(
        self,
        normalize_sku: bool = True,
    ) -> None:
        """Initialize pipeline.

        Args:
            normalize_sku: SKU normalization
        """
        self.normalize_sku = normalize_sku
        self.wizard = create_orders_wizard()
        self.sku_normalizer = SKUNormalizer(uppercase=True)

    def run(
        self,
        file_path: str | Path,
        mapping: Optional[MappingResult] = None,
        **read_kwargs,
    ) -> IngestResult:
        """Run import pipeline.

        Args:
            file_path: Path to file
            mapping: Ready mapping (if None, automatic)
            **read_kwargs: Additional arguments for FileReader

        Returns:
            IngestResult with data and metadata
        """
        warnings: list[str] = []
        file_path = Path(file_path)

        # 1. Read file
        reader = FileReader(file_path)
        df = reader.read(**read_kwargs)

        # 2. Column mapping
        if mapping is None:
            mapping = self.wizard.auto_map(df.columns)

        if not mapping.is_complete:
            missing = ", ".join(mapping.missing_required)
            warnings.append(f"Missing required columns: {missing}")

        # Apply mapping
        df = self.wizard.apply_mapping(df, mapping)

        # 3. SKU normalization
        sku_result = None
        if self.normalize_sku and "sku" in df.columns:
            sku_result = self.sku_normalizer.normalize_dataframe(df, "sku")
            df = sku_result.df

        # 4. Timestamp parsing
        if "timestamp" in df.columns:
            # Ensure timestamp is datetime
            if df["timestamp"].dtype == pl.Utf8:
                df = df.with_columns([
                    pl.col("timestamp").str.to_datetime(
                        format=None,  # Auto-detect
                        strict=False,
                    ).alias("timestamp")
                ])

        return IngestResult(
            df=df,
            mapping_result=mapping,
            sku_normalization=sku_result,
            source_file=file_path,
            rows_imported=len(df),
            columns_mapped=len(mapping.mappings),
            warnings=warnings,
        )


def ingest_masterdata(
    file_path: str | Path,
    **kwargs,
) -> IngestResult:
    """Helper function for Masterdata import.

    Args:
        file_path: Path to file
        **kwargs: Arguments for MasterdataIngestPipeline

    Returns:
        IngestResult
    """
    pipeline = MasterdataIngestPipeline(**kwargs)
    return pipeline.run(file_path)


def ingest_orders(
    file_path: str | Path,
    **kwargs,
) -> IngestResult:
    """Helper function for Orders import.

    Args:
        file_path: Path to file
        **kwargs: Arguments for OrdersIngestPipeline

    Returns:
        IngestResult
    """
    pipeline = OrdersIngestPipeline(**kwargs)
    return pipeline.run(file_path)
