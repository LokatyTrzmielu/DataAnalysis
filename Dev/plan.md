# Plan Implementacji DataAnalysis

## Podsumowanie

Budowa lokalnej aplikacji do analizy danych magazynowych (Masterdata + Orders) z UI w Streamlit.

**Stack:** Python 3.11+, DuckDB, Polars, Streamlit, Parquet
**Podejście:** Backend-first, nowy katalog `src/`
**Zakres:** Pełne MVP z PRD

---

## Struktura Katalogów

```
D:\VS\DataAnalysis\
├── src/
│   ├── core/           # Konfiguracja, typy, formatowanie
│   ├── ingest/         # Import danych, Mapping Wizard
│   ├── quality/        # Walidacja, DQ metrics, imputacja
│   ├── model/          # Masterdata, Orders processing
│   ├── analytics/      # DuckDB, capacity, performance
│   ├── reporting/      # Raporty CSV, manifest, ZIP
│   └── ui/             # Streamlit app + pages
├── tests/
│   └── fixtures/       # Syntetyczne dane testowe
├── runs/               # Wyniki analiz per klient
├── pyproject.toml
└── README.md
```

---

## Fazy Implementacji

### FAZA 0: Przygotowanie Projektu
**Pliki:**
- `src/core/config.py` - stałe konfiguracyjne (thresholds, utilization)
- `src/core/formatting.py` - formatowanie liczb (m³→6, kg→3, %→2)
- `src/core/paths.py` - zarządzanie ścieżkami runs/
- `src/core/types.py` - modele Pydantic (MasterdataRow, OrderRow, CarrierConfig, ShiftConfig)
- `pyproject.toml` - konfiguracja projektu

### FAZA 1: Dane Testowe
**Pliki:**
- `tests/fixtures/generate_fixtures.py` - generator syntetycznych danych
- `tests/fixtures/masterdata_clean.xlsx` - 1000 SKU poprawnych
- `tests/fixtures/masterdata_dirty.xlsx` - z błędami (0, NULL, ujemne, outliers)
- `tests/fixtures/orders_clean.csv` - 10000 linii zamówień
- `tests/fixtures/carriers.yml` - konfiguracja nośników Kardex
- `tests/fixtures/shifts_base.yml` - harmonogram zmian

### FAZA 2: Import Danych (Ingest)
**Pliki:**
- `src/ingest/readers.py` - odczyt XLSX/CSV/TXT (Polars)
- `src/ingest/mapping.py` - Mapping Wizard z auto-sugestiami
- `src/ingest/units.py` - detekcja i konwersja jednostek (mm/cm/m, kg/g)
- `src/ingest/sku_normalize.py` - normalizacja SKU + collision detection
- `src/ingest/pipeline.py` - integracja całego pipeline

**Logika Mapping Wizard:**
```python
MASTERDATA_SCHEMA = {
    "sku": ["sku", "item", "article", "artykul", "indeks"],
    "length": ["length", "dlugosc", "l", "dim_l"],
    "width": ["width", "szerokosc", "w", "dim_w"],
    "height": ["height", "wysokosc", "h", "dim_h"],
    "weight": ["weight", "waga", "mass", "kg"],
    "stock": ["stock", "qty", "ilosc", "zapas"],
}
```

### FAZA 3: Walidacja i Jakość Danych
**Pliki:**
- `src/quality/validators.py` - reguły walidacji (0=missing, negative=missing)
- `src/quality/dq_metrics.py` - Data Quality Scorecard (coverage %)
- `src/quality/dq_lists.py` - listy: MissingCritical, Outliers, Borderline, Duplicates, Conflicts, Collisions
- `src/quality/impute.py` - imputacja medianą z flagą RAW/ESTIMATED
- `src/quality/pipeline.py` - integracja

**Kluczowa logika:**
- `0` traktowane jako brak (dla wymiarów, wagi, ilości)
- Wartości ujemne = brak
- Imputacja globalna medianą
- Każdy SKU dostaje flagę: RAW lub ESTIMATED

### FAZA 4: Model Danych
**Pliki:**
- `src/model/masterdata.py` - konsolidacja duplikatów, kubatura
- `src/model/orders.py` - normalizacja, join z masterdata

### FAZA 5: Analityka Pojemnościowa
**Pliki:**
- `src/analytics/duckdb_runner.py` - warstwa DuckDB
- `src/analytics/capacity.py` - główna logika

**Kluczowa logika:**
```python
# 6 orientacji (permutacje wymiarów)
# Constraints: ANY, UPRIGHT_ONLY, FLAT_ONLY
# Borderline threshold = 2mm
# FitResult: FIT / BORDERLINE / NOT_FIT
# N per carrier = ile sztuk mieści się na nośniku
# Machine sizing z utilization (VLM 0.75, MiB 0.68)
```

### FAZA 6: Analityka Wydajnościowa
**Pliki:**
- `src/analytics/shifts.py` - parsowanie YAML harmonogramu (base + overlay)
- `src/analytics/performance.py` - KPI, peaks

**Kluczowa logika:**
```python
# KPI: lines/h, orders/h, units/h, unique SKU/h
# Productive hours (domyślnie 7h z 8h zmiany)
# Peak analysis: max, P90, P95
# Udział overlay w pracy (%)
```

### FAZA 7: Raportowanie
**Pliki:**
- `src/reporting/csv_writer.py` - writer CSV (separator ';', UTF-8 BOM)
- `src/reporting/main_report.py` - Report_Main.csv (Key-Value)
- `src/reporting/dq_reports.py` - wszystkie raporty DQ
- `src/reporting/readme.py` - README.txt
- `src/reporting/manifest.py` - Manifest.json z SHA256
- `src/reporting/zip_export.py` - paczka ZIP

**Struktura raportów:**
```
reports/
├── Report_Main.csv          # Section | Metric | Value
├── DQ_Summary.csv
├── DQ_MissingCritical.csv
├── DQ_SuspectOutliers.csv
├── DQ_HighRiskBorderline.csv
├── DQ_Masterdata_Duplicates.csv
├── DQ_Masterdata_Conflicts.csv
├── DQ_SKU_Collisions.csv
├── README.txt
└── Manifest.json
```

### FAZA 8: UI Streamlit
**Pliki:**
- `src/ui/app.py` - główna aplikacja
- `src/ui/components/sidebar.py` - parametry analizy
- `src/ui/components/mapping_wizard.py` - interaktywny wizard
- `src/ui/pages/import_page.py` - upload plików
- `src/ui/pages/validation_page.py` - DQ scorecard, imputacja
- `src/ui/pages/analysis_page.py` - capacity + performance
- `src/ui/pages/reports_page.py` - podgląd + download ZIP

**Layout:**
- 4 zakładki: Import → Walidacja → Analiza → Raporty
- Sidebar: client name, utilization, productive hours, thresholds
- Progress bar podczas analizy

### FAZA 9: Integracja i Testy
- Testy integracyjne full pipeline
- Testy wydajnościowe (200k SKU, 2M orders)
- Dokumentacja

---

## Kolejność Implementacji (Backend-First)

```
FAZA 0 → FAZA 1 → FAZA 2 → FAZA 3 → FAZA 4 → FAZA 5 → FAZA 6 → FAZA 7 → FAZA 8 → FAZA 9
 core    fixtures   ingest   quality   model   capacity  perf    reports    UI     tests
```

---

## Kluczowe Pliki do Implementacji

1. **`src/core/types.py`** - fundament typów danych (Pydantic)
2. **`src/ingest/mapping.py`** - Mapping Wizard z auto-sugestiami
3. **`src/quality/impute.py`** - imputacja z flagami RAW/ESTIMATED
4. **`src/analytics/capacity.py`** - 6 orientacji, constraints, borderline
5. **`src/analytics/shifts.py`** - harmonogram zmian base + overlay
6. **`src/reporting/zip_export.py`** - finalizacja pipeline

---

## Decyzje Architektoniczne

| Decyzja | Uzasadnienie |
|---------|--------------|
| Polars zamiast Pandas | Wydajność na 2M wierszy |
| DuckDB dla agregacji | SQL bez ładowania całości do RAM |
| Pydantic dla typów | Type safety + walidacja |
| Parquet jako format pośredni | Kompresja + szybki dostęp |
| Session state w Streamlit | Zachowanie stanu między akcjami |

---

## Pliki Referencyjne z Dokumentacji

- `DataAnalysis_docs/DataAnalysis_PRD.md` - wymagania funkcjonalne
- `DataAnalysis_docs/customers_shifts.yml` - model harmonogramu zmian
- `DataAnalysis_docs/Format danych.txt` - formatowanie liczb w CSV
- `DataAnalysis_docs/Profil projektu.txt` - konfiguracja DQ i imputacji
- `DataAnalysis_docs/Struktura katalogów aplikacji.txt` - struktura modułów
- `DataAnalysis_docs/Struktura katalogów projektu.txt` - struktura runs/
