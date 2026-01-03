
import pandas as pd

def validate_missing_values(input_path: str, report_path: str):
    """Sprawdza braki danych i zapisuje raport CSV."""
    df = pd.read_parquet(input_path)
    missing_report = df.isnull().sum().reset_index()
    missing_report.columns = ['Column', 'MissingCount']
    missing_report.to_csv(report_path, sep=';', index=False)
    return f"Raport braków zapisany jako {report_path}"
