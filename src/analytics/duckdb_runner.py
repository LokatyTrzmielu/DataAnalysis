"""Warstwa DuckDB do agregacji i analiz SQL."""

from pathlib import Path
from typing import Optional

import duckdb
import polars as pl


class DuckDBRunner:
    """Runner zapytan DuckDB."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        """Inicjalizacja runnera.

        Args:
            db_path: Sciezka do bazy (None = in-memory)
        """
        self.db_path = str(db_path) if db_path else ":memory:"
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Polaczenie do bazy."""
        if self._conn is None:
            self._conn = duckdb.connect(self.db_path)
        return self._conn

    def close(self) -> None:
        """Zamknij polaczenie."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def register_df(self, name: str, df: pl.DataFrame) -> None:
        """Zarejestruj DataFrame jako tabele.

        Args:
            name: Nazwa tabeli
            df: Polars DataFrame
        """
        # DuckDB moze bezposrednio czytac Polars DataFrames
        self.conn.register(name, df)

    def query(self, sql: str) -> pl.DataFrame:
        """Wykonaj zapytanie SQL.

        Args:
            sql: Zapytanie SQL

        Returns:
            Polars DataFrame z wynikiem
        """
        result = self.conn.execute(sql).pl()
        return result

    def aggregate_orders_by_hour(self, orders_table: str = "orders") -> pl.DataFrame:
        """Agreguj zamowienia per godzina."""
        return self.query(f"""
            SELECT
                EXTRACT(HOUR FROM timestamp) as hour,
                COUNT(*) as lines,
                COUNT(DISTINCT order_id) as orders,
                SUM(quantity) as units,
                COUNT(DISTINCT sku) as unique_sku
            FROM {orders_table}
            GROUP BY EXTRACT(HOUR FROM timestamp)
            ORDER BY hour
        """)

    def aggregate_orders_by_date(self, orders_table: str = "orders") -> pl.DataFrame:
        """Agreguj zamowienia per dzien."""
        return self.query(f"""
            SELECT
                DATE_TRUNC('day', timestamp) as date,
                COUNT(*) as lines,
                COUNT(DISTINCT order_id) as orders,
                SUM(quantity) as units,
                COUNT(DISTINCT sku) as unique_sku
            FROM {orders_table}
            GROUP BY DATE_TRUNC('day', timestamp)
            ORDER BY date
        """)

    def aggregate_orders_by_sku(self, orders_table: str = "orders") -> pl.DataFrame:
        """Agreguj zamowienia per SKU."""
        return self.query(f"""
            SELECT
                sku,
                COUNT(*) as lines,
                COUNT(DISTINCT order_id) as orders,
                SUM(quantity) as units
            FROM {orders_table}
            GROUP BY sku
            ORDER BY units DESC
        """)

    def calculate_abc_analysis(
        self,
        orders_table: str = "orders",
        value_column: str = "quantity",
    ) -> pl.DataFrame:
        """Wykonaj analize ABC."""
        return self.query(f"""
            WITH sku_totals AS (
                SELECT
                    sku,
                    SUM({value_column}) as total_value,
                    COUNT(*) as frequency
                FROM {orders_table}
                GROUP BY sku
            ),
            ranked AS (
                SELECT
                    *,
                    SUM(total_value) OVER (ORDER BY total_value DESC) as cumulative_value,
                    SUM(total_value) OVER () as grand_total
                FROM sku_totals
            )
            SELECT
                sku,
                total_value,
                frequency,
                cumulative_value,
                (cumulative_value / grand_total * 100) as cumulative_pct,
                CASE
                    WHEN (cumulative_value / grand_total * 100) <= 80 THEN 'A'
                    WHEN (cumulative_value / grand_total * 100) <= 95 THEN 'B'
                    ELSE 'C'
                END as abc_class
            FROM ranked
            ORDER BY total_value DESC
        """)

    def join_orders_masterdata(
        self,
        orders_table: str = "orders",
        masterdata_table: str = "masterdata",
    ) -> pl.DataFrame:
        """Polacz Orders z Masterdata."""
        return self.query(f"""
            SELECT
                o.*,
                m.length_mm,
                m.width_mm,
                m.height_mm,
                m.weight_kg,
                m.volume_m3,
                o.quantity * m.volume_m3 as line_volume_m3,
                o.quantity * m.weight_kg as line_weight_kg
            FROM {orders_table} o
            LEFT JOIN {masterdata_table} m ON o.sku = m.sku
        """)


def create_runner(db_path: Optional[str | Path] = None) -> DuckDBRunner:
    """Utworz runner DuckDB.

    Args:
        db_path: Sciezka do bazy (None = in-memory)

    Returns:
        DuckDBRunner
    """
    return DuckDBRunner(db_path)
