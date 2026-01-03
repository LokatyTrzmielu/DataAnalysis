
import pandas as pd
import polars as pl
import duckdb

def import_and_convert_to_parquet(input_path: str, output_path: str):
    """Wczytuje plik CSV lub XLSX i zapisuje jako Parquet."""
    if input_path.lower().endswith('.csv'):
        df = pd.read_csv(input_path)
    elif input_path.lower().endswith('.xlsx'):
        df = pd.read_excel(input_path, engine='openpyxl')
    else:
        raise ValueError("Obsługiwane formaty: CSV, XLSX")
    df.to_parquet(output_path, index=False)
    return f"Plik zapisany jako {output_path}"