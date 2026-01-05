"""CSV writer compliant with requirements (separator ';', UTF-8 BOM)."""

from pathlib import Path
from typing import Any

import polars as pl

from src.core.config import CSV_SEPARATOR, CSV_ENCODING


class CSVWriter:
    """CSV file writer compliant with requirements."""

    def __init__(
        self,
        separator: str = CSV_SEPARATOR,
        encoding: str = CSV_ENCODING,
    ) -> None:
        """Initialize the writer.

        Args:
            separator: Column separator (default ';')
            encoding: Encoding (default UTF-8 BOM)
        """
        self.separator = separator
        self.encoding = encoding

    def write(
        self,
        df: pl.DataFrame,
        file_path: str | Path,
        include_header: bool = True,
    ) -> Path:
        """Write DataFrame to CSV.

        Args:
            df: DataFrame to save
            file_path: Destination path
            include_header: Whether to include header

        Returns:
            Path to the saved file
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Polars write_csv
        df.write_csv(
            file_path,
            separator=self.separator,
            include_header=include_header,
        )

        # Add BOM if required
        if "sig" in self.encoding.lower() or "bom" in self.encoding.lower():
            self._add_bom(file_path)

        return file_path

    def _add_bom(self, file_path: Path) -> None:
        """Add BOM at the beginning of the file."""
        with open(file_path, "rb") as f:
            content = f.read()

        # Check if BOM already exists
        if not content.startswith(b"\xef\xbb\xbf"):
            with open(file_path, "wb") as f:
                f.write(b"\xef\xbb\xbf" + content)

    def write_key_value(
        self,
        data: list[tuple[str, str, Any]],
        file_path: str | Path,
        columns: tuple[str, str, str] = ("Section", "Metric", "Value"),
    ) -> Path:
        """Write data in Key-Value format (Section | Metric | Value).

        Args:
            data: List of tuples (section, metric, value)
            file_path: Destination path
            columns: Column names

        Returns:
            Path to the saved file
        """
        df = pl.DataFrame({
            columns[0]: [d[0] for d in data],
            columns[1]: [d[1] for d in data],
            columns[2]: [str(d[2]) for d in data],
        })
        return self.write(df, file_path)


def write_csv(
    df: pl.DataFrame,
    file_path: str | Path,
) -> Path:
    """Helper function to write CSV.

    Args:
        df: DataFrame to save
        file_path: Destination path

    Returns:
        Path to the saved file
    """
    writer = CSVWriter()
    return writer.write(df, file_path)
