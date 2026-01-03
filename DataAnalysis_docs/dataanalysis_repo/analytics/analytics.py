import pandas as pd
import itertools

def calculate_kpi(input_path: str):
    """Oblicza KPI: linie/h i SKU/h z danych Orders."""
    df = pd.read_parquet(input_path)
    if 'timestamp' not in df.columns or 'sku' not in df.columns:
        raise ValueError("Brak wymaganych kolumn: timestamp, sku")
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    lines_per_hour = df.groupby('hour').size()
    sku_per_hour = df.groupby('hour')['sku'].nunique()
    return {
        'lines_per_hour': lines_per_hour.to_dict(),
        'sku_per_hour': sku_per_hour.to_dict()
    }

def fit_check(parquet_path: str, report_path: str,
              max_dims=(600, 400, 300), max_weight=30.0, borderline_threshold=2.0):
    """
    Sprawdza dopasowanie SKU do nośnika z testem 6 orientacji.
    :param parquet_path: ścieżka do pliku Parquet z kolumnami: dlugosc, szerokosc, wysokosc, waga
    :param report_path: ścieżka do raportu CSV
    :param max_dims: (max_dlugosc, max_szerokosc, max_wysokosc) w mm
    :param max_weight: maksymalna waga w kg
    :param borderline_threshold: próg dla statusu BORDERLINE w mm
    :return: DataFrame z kolumną 'fit_status'
    """
    df = pd.read_parquet(parquet_path)
    required_cols = ['dlugosc', 'szerokosc', 'wysokosc', 'waga']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Brak wymaganej kolumny: {col}")

    statuses = []
    for _, row in df.iterrows():
        dims = [row['dlugosc'], row['szerokosc'], row['wysokosc']]
        weight = row['waga']
        fit = False
        borderline = False

        # Sprawdzenie wagi
        if weight > max_weight:
            statuses.append('NOT FIT')
            continue

        # Test 6 orientacji (wszystkie permutacje wymiarów)
        for perm in itertools.permutations(dims, 3):
            diff = [max_dims[i] - perm[i] for i in range(3)]
            if all(d >= 0 for d in diff):
                fit = True
                if any(0 < d <= borderline_threshold for d in diff):
                    borderline = True
                break

        if fit and borderline:
            statuses.append('BORDERLINE')
        elif fit:
            statuses.append('FIT')
        else:
            statuses.append('NOT FIT')

    df['fit_status'] = statuses
    df.to_csv(report_path, sep=';', index=False, encoding='utf-8-sig')
    return df

def performance_analysis_with_shifts(parquet_path: str, shifts: dict, report_path: str):
    """
    Analiza wydajnościowa z uwzględnieniem harmonogramu zmian.
    :param parquet_path: ścieżka do pliku Parquet z Orders (kolumny: timestamp, sku)
    :param shifts: słownik z harmonogramem zmian, np. {"Shift1": (6, 14), "Shift2": (14, 22)}
    :param report_path: ścieżka do raportu CSV
    :return: DataFrame z KPI per zmiana
    """
    df = pd.read_parquet(parquet_path)
    if 'timestamp' not in df.columns or 'sku' not in df.columns:
        raise ValueError("Brak wymaganych kolumn: timestamp, sku")

    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour

    results = []
    for shift_name, (start, end) in shifts.items():
        shift_df = df[(df['hour'] >= start) & (df['hour'] < end)]
        lines = len(shift_df)
        unique_sku = shift_df['sku'].nunique()
        results.append({
            "Shift": shift_name,
            "StartHour": start,
            "EndHour": end,
            "Lines": lines,
            "UniqueSKU": unique_sku,
            "LinesPerHour": round(lines / (end - start), 2)
        })

    # Zapis raportu
    report_df = pd.DataFrame(results)
    report_df.to_csv(report_path, sep=';', index=False, encoding='utf-8-sig')
    return report_df
