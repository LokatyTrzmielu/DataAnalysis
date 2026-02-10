"""Orders data processing - normalization, join with Masterdata."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import polars as pl


@dataclass
class OrdersProcessingResult:
    """Orders processing result."""
    df: pl.DataFrame
    total_orders: int
    total_lines: int
    total_units: int
    unique_sku: int
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    unmatched_sku: list[str]


class OrdersProcessor:
    """Orders data processing."""

    def __init__(self) -> None:
        """Initialize processor."""
        pass

    def normalize(self, df: pl.DataFrame) -> pl.DataFrame:
        """Normalize orders data.

        Pipeline already produces timestamp, order_date, order_hour columns.
        This method handles edge cases and adds remaining helper columns.

        Args:
            df: DataFrame with Orders data

        Returns:
            Normalized DataFrame
        """
        result = df.clone()

        # Ensure timestamp is datetime (fallback if not from pipeline)
        if "timestamp" in result.columns:
            if result["timestamp"].dtype == pl.Utf8:
                result = result.with_columns([
                    pl.col("timestamp").str.to_datetime(strict=False).alias("timestamp")
                ])

        # Ensure quantity is int
        if "quantity" in result.columns:
            result = result.with_columns([
                pl.col("quantity").cast(pl.Int64).alias("quantity")
            ])

        # Add helper columns if not already present (pipeline may have created them)
        if "timestamp" in result.columns:
            if "order_date" not in result.columns:
                result = result.with_columns([
                    pl.col("timestamp").dt.date().alias("order_date"),
                ])
            if "order_hour" not in result.columns:
                result = result.with_columns([
                    pl.col("timestamp").dt.hour().alias("order_hour"),
                ])
            if "weekday" not in result.columns:
                result = result.with_columns([
                    pl.col("timestamp").dt.weekday().alias("weekday"),
                ])

        return result

    def join_with_masterdata(
        self,
        orders_df: pl.DataFrame,
        masterdata_df: pl.DataFrame,
        sku_column: str = "sku",
    ) -> pl.DataFrame:
        """Join Orders with Masterdata.

        Args:
            orders_df: DataFrame with Orders
            masterdata_df: DataFrame with Masterdata
            sku_column: SKU column name

        Returns:
            Joined DataFrame
        """
        # Select columns from Masterdata
        md_cols = [sku_column]
        for col in ["length_mm", "width_mm", "height_mm", "weight_kg", "volume_m3", "size_category"]:
            if col in masterdata_df.columns:
                md_cols.append(col)

        md_subset = masterdata_df.select(md_cols)

        # Left join
        result = orders_df.join(
            md_subset,
            on=sku_column,
            how="left",
        )

        # Calculate line_volume and line_weight
        if "volume_m3" in result.columns and "quantity" in result.columns:
            result = result.with_columns([
                (pl.col("volume_m3") * pl.col("quantity")).alias("line_volume_m3")
            ])

        if "weight_kg" in result.columns and "quantity" in result.columns:
            result = result.with_columns([
                (pl.col("weight_kg") * pl.col("quantity")).alias("line_weight_kg")
            ])

        return result

    def calculate_stats(self, df: pl.DataFrame) -> dict:
        """Calculate orders statistics.

        Args:
            df: DataFrame with Orders

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_lines": len(df),
            "total_orders": df["order_id"].n_unique() if "order_id" in df.columns else 0,
            "total_units": df["quantity"].sum() if "quantity" in df.columns else 0,
            "unique_sku": df["sku"].n_unique() if "sku" in df.columns else 0,
        }

        if "timestamp" in df.columns:
            stats["date_from"] = df["timestamp"].min()
            stats["date_to"] = df["timestamp"].max()

        if stats["total_orders"] > 0:
            stats["avg_lines_per_order"] = stats["total_lines"] / stats["total_orders"]
        if stats["total_lines"] > 0:
            stats["avg_units_per_line"] = stats["total_units"] / stats["total_lines"]

        return stats

    def process(
        self,
        orders_df: pl.DataFrame,
        masterdata_df: Optional[pl.DataFrame] = None,
    ) -> OrdersProcessingResult:
        """Full Orders processing.

        Args:
            orders_df: DataFrame with Orders
            masterdata_df: DataFrame with Masterdata (optional)

        Returns:
            OrdersProcessingResult
        """
        # 1. Normalization
        result = self.normalize(orders_df)

        # 2. Join with Masterdata
        unmatched_sku = []
        if masterdata_df is not None:
            # Find unmapped SKUs
            order_skus = set(result["sku"].unique().to_list())
            md_skus = set(masterdata_df["sku"].unique().to_list())
            unmatched_sku = list(order_skus - md_skus)

            result = self.join_with_masterdata(result, masterdata_df)

        # 3. Statistics
        stats = self.calculate_stats(result)

        return OrdersProcessingResult(
            df=result,
            total_orders=stats.get("total_orders", 0),
            total_lines=stats.get("total_lines", 0),
            total_units=stats.get("total_units", 0),
            unique_sku=stats.get("unique_sku", 0),
            date_from=stats.get("date_from"),
            date_to=stats.get("date_to"),
            unmatched_sku=unmatched_sku,
        )


def process_orders(
    orders_df: pl.DataFrame,
    masterdata_df: Optional[pl.DataFrame] = None,
) -> OrdersProcessingResult:
    """Helper function for processing Orders.

    Args:
        orders_df: DataFrame with Orders
        masterdata_df: DataFrame with Masterdata (optional)

    Returns:
        OrdersProcessingResult
    """
    processor = OrdersProcessor()
    return processor.process(orders_df, masterdata_df)
