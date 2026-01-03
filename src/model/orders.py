"""Przetwarzanie danych Orders - normalizacja, join z Masterdata."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import polars as pl


@dataclass
class OrdersProcessingResult:
    """Wynik przetwarzania Orders."""
    df: pl.DataFrame
    total_orders: int
    total_lines: int
    total_units: int
    unique_sku: int
    date_from: datetime
    date_to: datetime
    unmatched_sku: list[str]


class OrdersProcessor:
    """Przetwarzanie danych zamowien."""

    def __init__(self) -> None:
        """Inicjalizacja procesora."""
        pass

    def normalize(self, df: pl.DataFrame) -> pl.DataFrame:
        """Normalizuj dane zamowien.

        Args:
            df: DataFrame z danymi Orders

        Returns:
            Znormalizowany DataFrame
        """
        result = df.clone()

        # Upewnij sie ze timestamp jest datetime
        if "timestamp" in result.columns:
            if result["timestamp"].dtype == pl.Utf8:
                result = result.with_columns([
                    pl.col("timestamp").str.to_datetime(strict=False).alias("timestamp")
                ])

        # Upewnij sie ze quantity jest int
        if "quantity" in result.columns:
            result = result.with_columns([
                pl.col("quantity").cast(pl.Int64).alias("quantity")
            ])

        # Dodaj kolumny pomocnicze
        if "timestamp" in result.columns:
            result = result.with_columns([
                pl.col("timestamp").dt.date().alias("order_date"),
                pl.col("timestamp").dt.hour().alias("order_hour"),
                pl.col("timestamp").dt.weekday().alias("weekday"),
            ])

        return result

    def join_with_masterdata(
        self,
        orders_df: pl.DataFrame,
        masterdata_df: pl.DataFrame,
        sku_column: str = "sku",
    ) -> pl.DataFrame:
        """Polacz Orders z Masterdata.

        Args:
            orders_df: DataFrame z Orders
            masterdata_df: DataFrame z Masterdata
            sku_column: Nazwa kolumny SKU

        Returns:
            Polaczony DataFrame
        """
        # Wybierz kolumny z Masterdata
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

        # Oblicz line_volume i line_weight
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
        """Oblicz statystyki zamowien.

        Args:
            df: DataFrame z Orders

        Returns:
            Slownik ze statystykami
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
        """Pelne przetwarzanie Orders.

        Args:
            orders_df: DataFrame z Orders
            masterdata_df: DataFrame z Masterdata (opcjonalny)

        Returns:
            OrdersProcessingResult
        """
        # 1. Normalizacja
        result = self.normalize(orders_df)

        # 2. Join z Masterdata
        unmatched_sku = []
        if masterdata_df is not None:
            # Znajdz niezmapowane SKU
            order_skus = set(result["sku"].unique().to_list())
            md_skus = set(masterdata_df["sku"].unique().to_list())
            unmatched_sku = list(order_skus - md_skus)

            result = self.join_with_masterdata(result, masterdata_df)

        # 3. Statystyki
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
    """Funkcja pomocnicza do przetwarzania Orders.

    Args:
        orders_df: DataFrame z Orders
        masterdata_df: DataFrame z Masterdata (opcjonalny)

    Returns:
        OrdersProcessingResult
    """
    processor = OrdersProcessor()
    return processor.process(orders_df, masterdata_df)
