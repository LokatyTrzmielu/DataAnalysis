"""Masterdata processing - consolidation, volume calculation."""

from dataclasses import dataclass
from typing import Optional

import polars as pl

from src.core.types import DataQualityFlag


@dataclass
class MasterdataConsolidationResult:
    """Masterdata consolidation result."""
    df: pl.DataFrame
    original_count: int
    consolidated_count: int
    duplicates_merged: int
    conflicts_resolved: int


class MasterdataProcessor:
    """Masterdata processing."""

    def __init__(
        self,
        consolidation_strategy: str = "first",  # first, max, mean
    ) -> None:
        """Initialize processor.

        Args:
            consolidation_strategy: Conflict resolution strategy
                - "first": First value
                - "max": Maximum value
                - "mean": Average
        """
        self.consolidation_strategy = consolidation_strategy

    def consolidate_duplicates(self, df: pl.DataFrame) -> MasterdataConsolidationResult:
        """Consolidate duplicate SKUs.

        Args:
            df: DataFrame with Masterdata

        Returns:
            MasterdataConsolidationResult
        """
        original_count = len(df)

        # Find duplicates
        sku_counts = df.group_by("sku").agg(pl.len().alias("count"))
        duplicate_skus = sku_counts.filter(pl.col("count") > 1)["sku"].to_list()

        if not duplicate_skus:
            return MasterdataConsolidationResult(
                df=df,
                original_count=original_count,
                consolidated_count=original_count,
                duplicates_merged=0,
                conflicts_resolved=0,
            )

        # Separate into unique and duplicates
        unique_df = df.filter(~pl.col("sku").is_in(duplicate_skus))
        duplicate_df = df.filter(pl.col("sku").is_in(duplicate_skus))

        # Consolidate duplicates
        consolidated = self._consolidate_group(duplicate_df)

        # Merge
        result_df = pl.concat([unique_df, consolidated])

        return MasterdataConsolidationResult(
            df=result_df,
            original_count=original_count,
            consolidated_count=len(result_df),
            duplicates_merged=original_count - len(result_df),
            conflicts_resolved=len(duplicate_skus),
        )

    def _consolidate_group(self, df: pl.DataFrame) -> pl.DataFrame:
        """Consolidate a group of duplicate SKUs."""
        numeric_cols = ["length_mm", "width_mm", "height_mm", "weight_kg", "stock_qty"]
        flag_cols = ["length_flag", "width_flag", "height_flag", "weight_flag", "stock_flag"]

        agg_exprs = []

        for col in numeric_cols:
            if col not in df.columns:
                continue

            if self.consolidation_strategy == "max":
                agg_exprs.append(pl.col(col).max().alias(col))
            elif self.consolidation_strategy == "mean":
                agg_exprs.append(pl.col(col).mean().alias(col))
            else:  # first
                agg_exprs.append(pl.col(col).first().alias(col))

        for col in flag_cols:
            if col in df.columns:
                agg_exprs.append(pl.col(col).first().alias(col))

        if "orientation_constraint" in df.columns:
            agg_exprs.append(pl.col("orientation_constraint").first().alias("orientation_constraint"))

        return df.group_by("sku").agg(agg_exprs)

    def calculate_volume(self, df: pl.DataFrame) -> pl.DataFrame:
        """Calculate volume for each SKU.

        Args:
            df: DataFrame with dimensions

        Returns:
            DataFrame with volume_m3 column
        """
        if not all(c in df.columns for c in ["length_mm", "width_mm", "height_mm"]):
            return df

        return df.with_columns([
            (
                pl.col("length_mm") * pl.col("width_mm") * pl.col("height_mm") / 1_000_000_000
            ).alias("volume_m3")
        ])

    def add_size_category(self, df: pl.DataFrame) -> pl.DataFrame:
        """Add SKU size category.

        Args:
            df: DataFrame with dimensions

        Returns:
            DataFrame with size_category column
        """
        if "volume_m3" not in df.columns:
            df = self.calculate_volume(df)

        return df.with_columns([
            pl.when(pl.col("volume_m3") < 0.001)
            .then(pl.lit("XS"))
            .when(pl.col("volume_m3") < 0.01)
            .then(pl.lit("S"))
            .when(pl.col("volume_m3") < 0.05)
            .then(pl.lit("M"))
            .when(pl.col("volume_m3") < 0.1)
            .then(pl.lit("L"))
            .otherwise(pl.lit("XL"))
            .alias("size_category")
        ])

    def process(self, df: pl.DataFrame) -> pl.DataFrame:
        """Full Masterdata processing.

        Args:
            df: DataFrame with Masterdata

        Returns:
            Processed DataFrame
        """
        # 1. Consolidate duplicates
        consolidation = self.consolidate_duplicates(df)
        result = consolidation.df

        # 2. Calculate volume
        result = self.calculate_volume(result)

        # 3. Add size category
        result = self.add_size_category(result)

        return result


def process_masterdata(df: pl.DataFrame) -> pl.DataFrame:
    """Helper function for processing Masterdata.

    Args:
        df: DataFrame with Masterdata

    Returns:
        Processed DataFrame
    """
    processor = MasterdataProcessor()
    return processor.process(df)
