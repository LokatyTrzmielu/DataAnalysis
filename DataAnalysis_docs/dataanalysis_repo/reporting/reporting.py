import pandas as pd
import csv
import os
import zipfile

def generate_main_report(report_path: str, data: dict):
    """Generuje raport główny w formacie Key-Value."""
    with open(report_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Sekcja', 'Metryka', 'Wartość'])
        for section, metrics in data.items():
            for metric, value in metrics.items():
                writer.writerow([section, metric, value])
    return f"Raport główny zapisany jako {report_path}"

def generate_data_quality_scorecard(parquet_path: str, report_path: str):
    """
    Generuje raport Data Quality Scorecard z oceną jakości danych.
    :param parquet_path: ścieżka do pliku Parquet
    :param report_path: ścieżka do raportu CSV
    :return: słownik z metrykami jakości
    """
    df = pd.read_parquet(parquet_path)
    total_rows = len(df)

    # Metryki jakości
    missing_values = df.isnull().sum().sum()
    missing_ratio = round((missing_values / (total_rows * len(df.columns))) * 100, 2)

    duplicate_rows = df.duplicated().sum()
    duplicate_ratio = round((duplicate_rows / total_rows) * 100, 2)

    outliers_detected = 0
    # Prosty test outlierów: wartości ujemne w kolumnach numerycznych
    for col in df.select_dtypes(include=["number"]).columns:
        outliers_detected += (df[col] < 0).sum()

    # Scorecard
    scorecard = {
        "Total Rows": total_rows,
        "Missing Values": missing_values,
        "Missing Ratio (%)": missing_ratio,
        "Duplicate Rows": duplicate_rows,
        "Duplicate Ratio (%)": duplicate_ratio,
        "Outliers Detected": outliers_detected
    }

    # Zapis do CSV
    with open(report_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Metryka", "Wartość"])
        for metric, value in scorecard.items():
            writer.writerow([metric, value])

    return scorecard

def generate_reports_package(report_files: list, zip_path: str):
    """
    Tworzy paczkę ZIP z raportami analizy.
    :param report_files: lista ścieżek do plików raportów (CSV, TXT)
    :param zip_path: ścieżka do pliku ZIP
    :return: ścieżka do utworzonego pliku ZIP
    """
    # Tworzenie paczki ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in report_files:
            if os.path.exists(file):
                zipf.write(file, os.path.basename(file))
            else:
                print(f"Plik {file} nie istnieje i nie został dodany do paczki.")
    return zip_path
