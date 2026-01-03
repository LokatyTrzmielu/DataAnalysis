# DataAnalysis - Lista Zadań

## FAZA 0: Przygotowanie Projektu

- [ ] Utworzenie struktury katalogów (`src/`, `tests/`, `runs/`)
- [ ] Utworzenie `pyproject.toml` z zależnościami
- [ ] Implementacja `src/core/__init__.py`
- [ ] Implementacja `src/core/config.py` - stałe konfiguracyjne
- [ ] Implementacja `src/core/formatting.py` - formatowanie liczb
- [ ] Implementacja `src/core/paths.py` - zarządzanie ścieżkami
- [ ] Implementacja `src/core/types.py` - modele Pydantic

---

## FAZA 1: Dane Testowe

- [ ] Utworzenie `tests/fixtures/` struktury
- [ ] Implementacja `tests/fixtures/generate_fixtures.py`
- [ ] Wygenerowanie `masterdata_clean.xlsx` (1000 SKU)
- [ ] Wygenerowanie `masterdata_dirty.xlsx` (z błędami)
- [ ] Wygenerowanie `orders_clean.csv` (10000 linii)
- [ ] Wygenerowanie `orders_dirty.csv` (z błędami)
- [ ] Utworzenie `carriers.yml` - konfiguracja nośników
- [ ] Utworzenie `shifts_base.yml` - harmonogram zmian

---

## FAZA 2: Import Danych (Ingest)

- [ ] Implementacja `src/ingest/__init__.py`
- [ ] Implementacja `src/ingest/readers.py` - odczyt XLSX/CSV/TXT
- [ ] Implementacja `src/ingest/mapping.py` - Mapping Wizard
  - [ ] Auto-sugestie na podstawie nazw kolumn
  - [ ] Fuzzy matching
  - [ ] Manualne potwierdzenie mapowania
- [ ] Implementacja `src/ingest/units.py` - detekcja jednostek
  - [ ] Detekcja mm/cm/m
  - [ ] Detekcja kg/g
  - [ ] Konwersja do standardu (mm, kg)
- [ ] Implementacja `src/ingest/sku_normalize.py`
  - [ ] Normalizacja SKU (upper, strip, special chars)
  - [ ] Wykrywanie kolizji
- [ ] Implementacja `src/ingest/pipeline.py` - integracja
- [ ] Testy jednostkowe dla modułu ingest

---

## FAZA 3: Walidacja i Jakość Danych

- [ ] Implementacja `src/quality/__init__.py`
- [ ] Implementacja `src/quality/validators.py`
  - [ ] Reguła: NULL = missing
  - [ ] Reguła: 0 = missing (dla wymiarów, wagi, qty)
  - [ ] Reguła: negative = missing
- [ ] Implementacja `src/quality/dq_metrics.py`
  - [ ] Obliczanie coverage % (wymiary, waga, stock)
  - [ ] Zliczanie problemów
  - [ ] Data Quality Scorecard
- [ ] Implementacja `src/quality/dq_lists.py`
  - [ ] Lista MissingCritical
  - [ ] Lista SuspectOutliers (IQR)
  - [ ] Lista HighRiskBorderline
  - [ ] Lista Duplicates
  - [ ] Lista Conflicts
  - [ ] Lista SKU_Collisions
- [ ] Implementacja `src/quality/impute.py`
  - [ ] Imputacja medianą (global)
  - [ ] Flagowanie RAW vs ESTIMATED
- [ ] Implementacja `src/quality/pipeline.py` - integracja
- [ ] Testy jednostkowe dla modułu quality

---

## FAZA 4: Model Danych

- [ ] Implementacja `src/model/__init__.py`
- [ ] Implementacja `src/model/masterdata.py`
  - [ ] Konsolidacja duplikatów SKU
  - [ ] Obliczanie kubatury
  - [ ] Przygotowanie silver table
- [ ] Implementacja `src/model/orders.py`
  - [ ] Parsowanie timestamp
  - [ ] Konwersja qty do EA
  - [ ] Join z masterdata
  - [ ] Przygotowanie silver table
- [ ] Testy jednostkowe dla modułu model

---

## FAZA 5: Analityka Pojemnościowa

- [ ] Implementacja `src/analytics/__init__.py`
- [ ] Implementacja `src/analytics/duckdb_runner.py`
  - [ ] Połączenie z DuckDB
  - [ ] Rejestracja tabel Parquet
  - [ ] Wykonywanie queries
- [ ] Implementacja `src/analytics/capacity.py`
  - [ ] Generowanie 6 orientacji (permutacje)
  - [ ] Obsługa constraints (ANY, UPRIGHT_ONLY, FLAT_ONLY)
  - [ ] Sprawdzanie dopasowania do nośnika
  - [ ] Detekcja BORDERLINE (threshold 2mm)
  - [ ] Sprawdzanie limitu wagowego
  - [ ] Obliczanie N per carrier
  - [ ] Sizing maszyn z utilization
- [ ] Testy jednostkowe dla capacity

---

## FAZA 6: Analityka Wydajnościowa

- [ ] Implementacja `src/analytics/shifts.py`
  - [ ] Parsowanie YAML harmonogramu
  - [ ] Obsługa base schedule
  - [ ] Obsługa exceptions (date_overlay, range_overlay)
  - [ ] Przypisanie shift do timestamp
- [ ] Implementacja `src/analytics/performance.py`
  - [ ] KPI: lines/hour
  - [ ] KPI: orders/hour
  - [ ] KPI: units/hour
  - [ ] KPI: unique SKU/hour
  - [ ] KPI per zmiana z productive hours
  - [ ] Peak analysis (max, P90, P95)
  - [ ] Udział overlay w pracy
- [ ] Testy jednostkowe dla performance

---

## FAZA 7: Raportowanie

- [ ] Implementacja `src/reporting/__init__.py`
- [ ] Implementacja `src/reporting/csv_writer.py`
  - [ ] Separator ';'
  - [ ] Encoding UTF-8 BOM
  - [ ] Formatowanie liczb wg standardu
- [ ] Implementacja `src/reporting/main_report.py`
  - [ ] Format Key-Value (Section | Metric | Value)
  - [ ] Sekcje: RUN_INFO, DATA_QUALITY, CAPACITY, PERFORMANCE
- [ ] Implementacja `src/reporting/dq_reports.py`
  - [ ] DQ_Summary.csv
  - [ ] DQ_MissingCritical.csv
  - [ ] DQ_SuspectOutliers.csv
  - [ ] DQ_HighRiskBorderline.csv
  - [ ] DQ_Masterdata_Duplicates.csv
  - [ ] DQ_Masterdata_Conflicts.csv
  - [ ] DQ_SKU_Collisions.csv
- [ ] Implementacja `src/reporting/readme.py` - README.txt
- [ ] Implementacja `src/reporting/manifest.py` - Manifest.json z SHA256
- [ ] Implementacja `src/reporting/zip_export.py` - paczka ZIP
- [ ] Testy jednostkowe dla reporting

---

## FAZA 8: UI Streamlit

- [ ] Implementacja `src/ui/__init__.py`
- [ ] Implementacja `src/ui/app.py` - główna aplikacja
  - [ ] Konfiguracja page (title, layout)
  - [ ] Session state management
  - [ ] Nawigacja między zakładkami
- [ ] Implementacja `src/ui/components/sidebar.py`
  - [ ] Client name input
  - [ ] Utilization sliders (VLM, MiB)
  - [ ] Productive hours input
  - [ ] Borderline threshold input
  - [ ] Imputation toggle
- [ ] Implementacja `src/ui/components/mapping_wizard.py`
  - [ ] Tabela kolumn źródłowych
  - [ ] Auto-suggested mappings
  - [ ] Dropdown do ręcznego wyboru
  - [ ] Confidence indicator
  - [ ] Apply / Reset buttons
- [ ] Implementacja `src/ui/pages/import_page.py`
  - [ ] File upload (XLSX, CSV, TXT)
  - [ ] File type selection
  - [ ] Preview first N rows
  - [ ] Trigger mapping wizard
- [ ] Implementacja `src/ui/pages/validation_page.py`
  - [ ] Data Quality Scorecard (cards)
  - [ ] Coverage % bars
  - [ ] Listy problemów (expandable)
  - [ ] Imputacja button
  - [ ] Before/After comparison
- [ ] Implementacja `src/ui/pages/analysis_page.py`
  - [ ] Wybór nośników (multiselect)
  - [ ] Konfiguracja zmian
  - [ ] Run Analysis button
  - [ ] Progress bar
  - [ ] Results summary
- [ ] Implementacja `src/ui/pages/reports_page.py`
  - [ ] Lista raportów
  - [ ] Preview każdego raportu
  - [ ] Download individual CSV
  - [ ] Download ZIP button
- [ ] Testy manualne UI

---

## FAZA 9: Integracja i Testy

- [ ] Test integracyjny: full pipeline (Masterdata only)
- [ ] Test integracyjny: full pipeline (Masterdata + Orders)
- [ ] Test struktury katalogów runs/
- [ ] Test spójności danych między raportami
- [ ] Test wydajnościowy: 200k SKU
- [ ] Test wydajnościowy: 2M linii Orders
- [ ] Dokumentacja README.md
- [ ] Code review i refactoring
- [ ] Finalne testy

---

## Legenda

- `[ ]` - Do zrobienia
- `[x]` - Zrobione
- `[-]` - Pominięte / Nie dotyczy
