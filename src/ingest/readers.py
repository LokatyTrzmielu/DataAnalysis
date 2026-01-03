"""Odczyt plikow XLSX, CSV, TXT przy uzyciu Polars."""

from pathlib import Path
from typing import Literal

import polars as pl


FileType = Literal["xlsx", "csv", "txt", "auto"]


class FileReader:
    """Uniwersalny reader plikow danych."""

    # Mapowanie rozszerzen na typy
    EXTENSION_MAP = {
        ".xlsx": "xlsx",
        ".xls": "xlsx",
        ".csv": "csv",
        ".txt": "txt",
        ".tsv": "txt",
    }

    # Typowe separatory dla CSV/TXT
    COMMON_SEPARATORS = [";", ",", "\t", "|"]

    def __init__(self, file_path: str | Path) -> None:
        """Inicjalizacja readera.

        Args:
            file_path: Sciezka do pliku
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Plik nie istnieje: {self.file_path}")

    def detect_file_type(self) -> str:
        """Wykryj typ pliku na podstawie rozszerzenia."""
        ext = self.file_path.suffix.lower()
        file_type = self.EXTENSION_MAP.get(ext)
        if file_type is None:
            raise ValueError(f"Nieobslugiwane rozszerzenie: {ext}")
        return file_type

    def detect_separator(self, sample_lines: int = 5) -> str:
        """Wykryj separator dla plikow CSV/TXT.

        Args:
            sample_lines: Liczba linii do analizy

        Returns:
            Wykryty separator
        """
        with open(self.file_path, "r", encoding="utf-8-sig") as f:
            lines = [f.readline() for _ in range(sample_lines)]

        # Policz wystapienia separatorow
        separator_counts = {sep: 0 for sep in self.COMMON_SEPARATORS}
        for line in lines:
            for sep in self.COMMON_SEPARATORS:
                separator_counts[sep] += line.count(sep)

        # Wybierz separator z najwieksza liczba wystapien
        best_separator = max(separator_counts, key=separator_counts.get)

        # Jesli brak separatorow, domyslnie przecinek
        if separator_counts[best_separator] == 0:
            return ","

        return best_separator

    def detect_encoding(self) -> str:
        """Wykryj kodowanie pliku."""
        # Probuj UTF-8 z BOM
        try:
            with open(self.file_path, "rb") as f:
                first_bytes = f.read(3)
                if first_bytes == b"\xef\xbb\xbf":
                    return "utf-8-sig"
        except Exception:
            pass

        # Domyslnie UTF-8
        return "utf-8"

    def read(
        self,
        file_type: FileType = "auto",
        separator: str | None = None,
        sheet_id: int | None = None,
        sheet_name: str | None = None,
        skip_rows: int = 0,
        n_rows: int | None = None,
    ) -> pl.DataFrame:
        """Wczytaj plik do Polars DataFrame.

        Args:
            file_type: Typ pliku ("xlsx", "csv", "txt", "auto")
            separator: Separator dla CSV/TXT (auto-detect jesli None)
            sheet_id: Numer arkusza dla XLSX (1-based, domyslnie 1)
            sheet_name: Nazwa arkusza dla XLSX (alternatywa dla sheet_id)
            skip_rows: Ile wierszy pominac na poczatku
            n_rows: Ile wierszy wczytac (None = wszystkie)

        Returns:
            Polars DataFrame z danymi
        """
        if file_type == "auto":
            file_type = self.detect_file_type()

        if file_type == "xlsx":
            return self._read_xlsx(sheet_id, sheet_name, skip_rows, n_rows)
        else:
            return self._read_csv(separator, skip_rows, n_rows)

    def _read_xlsx(
        self,
        sheet_id: int | None = None,
        sheet_name: str | None = None,
        skip_rows: int = 0,
        n_rows: int | None = None,
    ) -> pl.DataFrame:
        """Wczytaj plik XLSX."""
        # Domyslnie pierwszy arkusz
        if sheet_id is None and sheet_name is None:
            sheet_id = 1

        read_opts = {}
        if skip_rows:
            read_opts["skip_rows"] = skip_rows
        if n_rows:
            read_opts["n_rows"] = n_rows

        df = pl.read_excel(
            self.file_path,
            sheet_id=sheet_id,
            sheet_name=sheet_name,
            read_options=read_opts if read_opts else None,
        )
        return self._normalize_columns(df)

    def _read_csv(
        self,
        separator: str | None = None,
        skip_rows: int = 0,
        n_rows: int | None = None,
    ) -> pl.DataFrame:
        """Wczytaj plik CSV/TXT."""
        if separator is None:
            separator = self.detect_separator()

        encoding = self.detect_encoding()

        df = pl.read_csv(
            self.file_path,
            separator=separator,
            encoding=encoding,
            skip_rows=skip_rows,
            n_rows=n_rows,
            infer_schema_length=10000,
            try_parse_dates=True,
            ignore_errors=True,
        )
        return self._normalize_columns(df)

    def _normalize_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Normalizuj nazwy kolumn."""
        # Usun biale znaki, zamien na lowercase
        new_names = {}
        for col in df.columns:
            normalized = col.strip().lower().replace(" ", "_")
            # Usun znaki specjalne
            normalized = "".join(c for c in normalized if c.isalnum() or c == "_")
            new_names[col] = normalized

        return df.rename(new_names)

    def get_preview(self, n_rows: int = 10) -> pl.DataFrame:
        """Pobierz podglad danych (pierwszych n wierszy)."""
        return self.read(n_rows=n_rows)

    def get_columns(self) -> list[str]:
        """Pobierz liste kolumn bez wczytywania calego pliku."""
        preview = self.get_preview(n_rows=1)
        return preview.columns

    def get_sheet_names(self) -> list[str]:
        """Pobierz liste arkuszy (tylko dla XLSX)."""
        if self.detect_file_type() != "xlsx":
            return []

        import openpyxl
        wb = openpyxl.load_workbook(self.file_path, read_only=True)
        names = wb.sheetnames
        wb.close()
        return names


def read_file(
    file_path: str | Path,
    file_type: FileType = "auto",
    **kwargs,
) -> pl.DataFrame:
    """Funkcja pomocnicza do szybkiego wczytania pliku.

    Args:
        file_path: Sciezka do pliku
        file_type: Typ pliku
        **kwargs: Dodatkowe argumenty dla FileReader.read()

    Returns:
        Polars DataFrame
    """
    reader = FileReader(file_path)
    return reader.read(file_type=file_type, **kwargs)
