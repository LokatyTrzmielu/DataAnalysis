"""Uniwersalne funkcje czyszczenia danych numerycznych."""

import polars as pl


def clean_numeric_column(col: pl.Expr) -> pl.Expr:
    """Czyści kolumnę numeryczną z europejskich formatów.

    Obsługuje: przecinek jako separator dziesiętny, notację naukową (1,0E+0),
    kropki jako separatory tysięcy (1.234,56).

    Strategia: jeśli wartość zawiera przecinek, to kropki traktowane są jako
    separatory tysięcy (usuwane), a przecinek jako separator dziesiętny (→ kropka).
    """
    cleaned = col.cast(pl.Utf8).str.strip_chars()

    has_comma = cleaned.str.contains(",")

    # Ścieżka europejska: usuwamy kropki (tysiące), zamieniamy przecinek na kropkę
    european = (
        cleaned
        .str.replace_all(r"\.", "")  # usuń kropki-tysiące
        .str.replace_all(",", ".")   # przecinek → kropka
    )

    # Wybieramy ścieżkę w zależności od obecności przecinka
    result = pl.when(has_comma).then(european).otherwise(cleaned)

    return result.cast(pl.Float64, strict=False)
