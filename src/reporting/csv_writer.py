"""Writer CSV zgodny z wymaganiami (separator ';', UTF-8 BOM)."""

from pathlib import Path
from typing import Any

import polars as pl

from src.core.config import CSV_SEPARATOR, CSV_ENCODING


class CSVWriter:
    """Writer plikow CSV zgodny z polskimi wymaganiami."""

    def __init__(
        self,
        separator: str = CSV_SEPARATOR,
        encoding: str = CSV_ENCODING,
    ) -> None:
        """Inicjalizacja writera.

        Args:
            separator: Separator kolumn (domyslnie ';')
            encoding: Kodowanie (domyslnie UTF-8 BOM)
        """
        self.separator = separator
        self.encoding = encoding

    def write(
        self,
        df: pl.DataFrame,
        file_path: str | Path,
        include_header: bool = True,
    ) -> Path:
        """Zapisz DataFrame do CSV.

        Args:
            df: DataFrame do zapisania
            file_path: Sciezka docelowa
            include_header: Czy wlaczyc naglowek

        Returns:
            Sciezka do zapisanego pliku
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Polars write_csv
        df.write_csv(
            file_path,
            separator=self.separator,
            include_header=include_header,
        )

        # Dodaj BOM jesli wymagane
        if "sig" in self.encoding.lower() or "bom" in self.encoding.lower():
            self._add_bom(file_path)

        return file_path

    def _add_bom(self, file_path: Path) -> None:
        """Dodaj BOM na poczatek pliku."""
        with open(file_path, "rb") as f:
            content = f.read()

        # Sprawdz czy BOM juz jest
        if not content.startswith(b"\xef\xbb\xbf"):
            with open(file_path, "wb") as f:
                f.write(b"\xef\xbb\xbf" + content)

    def write_key_value(
        self,
        data: list[tuple[str, str, Any]],
        file_path: str | Path,
        columns: tuple[str, str, str] = ("Section", "Metric", "Value"),
    ) -> Path:
        """Zapisz dane w formacie Key-Value (Section | Metric | Value).

        Args:
            data: Lista krotek (section, metric, value)
            file_path: Sciezka docelowa
            columns: Nazwy kolumn

        Returns:
            Sciezka do zapisanego pliku
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
    """Funkcja pomocnicza do zapisu CSV.

    Args:
        df: DataFrame do zapisania
        file_path: Sciezka docelowa

    Returns:
        Sciezka do zapisanego pliku
    """
    writer = CSVWriter()
    return writer.write(df, file_path)
