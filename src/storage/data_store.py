"""Persistent dataset storage using DuckDB files."""

import hashlib
from pathlib import Path

import duckdb
import polars as pl


class DataStore:
    """Saves and loads Polars DataFrames as DuckDB files on disk."""

    def __init__(self, base_dir: Path = Path("data/datasets")) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, dataset_id: str) -> Path:
        return self.base_dir / f"{dataset_id}.duckdb"

    def save(self, dataset_id: str, df: pl.DataFrame, table: str) -> Path:
        """Write DataFrame as a named table into a DuckDB file."""
        path = self._path(dataset_id)
        with duckdb.connect(str(path)) as conn:
            conn.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM df")
        return path

    def load(self, dataset_id: str, table: str) -> pl.DataFrame:
        """Read a table from a DuckDB file into a Polars DataFrame."""
        path = self._path(dataset_id)
        with duckdb.connect(str(path), read_only=True) as conn:
            return conn.execute(f"SELECT * FROM {table}").pl()

    def preview(self, dataset_id: str, table: str, n: int = 10) -> list[dict]:
        """Return first n rows as a list of dicts."""
        path = self._path(dataset_id)
        with duckdb.connect(str(path), read_only=True) as conn:
            return conn.execute(f"SELECT * FROM {table} LIMIT {n}").df().to_dict(orient="records")

    def get_info(self, dataset_id: str) -> dict:
        """Return row counts and column names for all tables in the file."""
        path = self._path(dataset_id)
        info: dict = {"tables": {}, "size_mb": round(path.stat().st_size / 1_048_576, 2)}
        with duckdb.connect(str(path), read_only=True) as conn:
            tables = conn.execute("SHOW TABLES").fetchall()
            for (table,) in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                columns = [row[0] for row in conn.execute(f"DESCRIBE {table}").fetchall()]
                info["tables"][table] = {"row_count": count, "columns": columns}
        return info

    def exists(self, dataset_id: str) -> bool:
        return self._path(dataset_id).exists()

    def delete(self, dataset_id: str) -> None:
        self._path(dataset_id).unlink(missing_ok=True)


def hash_bytes(data: bytes) -> str:
    """Return SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()
