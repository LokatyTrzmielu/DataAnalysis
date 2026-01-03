# DataAnalysis - Lista Zadań

## FAZA 0: Przygotowanie Projektu ✅

- [x] Utworzenie struktury katalogów (`src/`, `tests/`, `runs/`)
- [x] Utworzenie `pyproject.toml` z zależnościami
- [x] Implementacja `src/core/__init__.py`
- [x] Implementacja `src/core/config.py` - stałe konfiguracyjne
- [x] Implementacja `src/core/formatting.py` - formatowanie liczb
- [x] Implementacja `src/core/paths.py` - zarządzanie ścieżkami
- [x] Implementacja `src/core/types.py` - modele Pydantic

---

## FAZA 1: Dane Testowe ✅

- [x] Utworzenie `tests/fixtures/` struktury
- [x] Implementacja `tests/fixtures/generate_fixtures.py`
- [x] Wygenerowanie `masterdata_clean.csv` (dane testowe)
- [x] Wygenerowanie `masterdata_dirty.csv` (z błędami)
- [x] Wygenerowanie `orders_clean.csv` (dane testowe)
- [x] Wygenerowanie `orders_dirty.csv` (z błędami jakościowymi)
- [x] Utworzenie `carriers.yml` - konfiguracja nośników
- [x] Utworzenie `shifts_base.yml` - harmonogram zmian
- [x] Dodano `MD_Kardex_gotowy.xlsx` - rzeczywiste dane testowe

---

## FAZA 2: Import Danych (Ingest) ✅

- [x] Implementacja `src/ingest/__init__.py`
- [x] Implementacja `src/ingest/readers.py` - odczyt XLSX/CSV/TXT
- [x] Implementacja `src/ingest/mapping.py` - Mapping Wizard
  - [x] Auto-sugestie na podstawie nazw kolumn
  - [x] Fuzzy matching
  - [x] Manualne potwierdzenie mapowania
- [x] Implementacja `src/ingest/units.py` - detekcja jednostek
  - [x] Detekcja mm/cm/m
  - [x] Detekcja kg/g
  - [x] Konwersja do standardu (mm, kg)
- [x] Implementacja `src/ingest/sku_normalize.py`
  - [x] Normalizacja SKU (upper, strip, special chars)
  - [x] Wykrywanie kolizji
- [x] Implementacja `src/ingest/pipeline.py` - integracja
- [x] Testy jednostkowe dla modułu ingest (tests/test_ingest.py)

---

## FAZA 3: Walidacja i Jakość Danych ✅

- [x] Implementacja `src/quality/__init__.py`
- [x] Implementacja `src/quality/validators.py`
  - [x] Reguła: NULL = missing
  - [x] Reguła: 0 = missing (dla wymiarów, wagi, qty)
  - [x] Reguła: negative = missing
- [x] Implementacja `src/quality/dq_metrics.py`
  - [x] Obliczanie coverage % (wymiary, waga, stock)
  - [x] Zliczanie problemów
  - [x] Data Quality Scorecard
- [x] Implementacja `src/quality/dq_lists.py`
  - [x] Lista MissingCritical
  - [x] Lista SuspectOutliers (IQR)
  - [x] Lista HighRiskBorderline
  - [x] Lista Duplicates
  - [x] Lista Conflicts
  - [x] Lista SKU_Collisions
- [x] Implementacja `src/quality/impute.py`
  - [x] Imputacja medianą (global)
  - [x] Flagowanie RAW vs ESTIMATED
- [x] Implementacja `src/quality/pipeline.py` - integracja
- [x] Testy jednostkowe dla modułu quality (tests/test_quality.py)

---

## FAZA 4: Model Danych ✅

- [x] Implementacja `src/model/__init__.py`
- [x] Implementacja `src/model/masterdata.py`
  - [x] Konsolidacja duplikatów SKU
  - [x] Obliczanie kubatury
  - [x] Przygotowanie silver table
- [x] Implementacja `src/model/orders.py`
  - [x] Parsowanie timestamp
  - [x] Konwersja qty do EA
  - [x] Join z masterdata
  - [x] Przygotowanie silver table
- [x] Testy jednostkowe dla modułu model (tests/test_model.py)

---

## FAZA 5: Analityka Pojemnościowa ✅

- [x] Implementacja `src/analytics/__init__.py`
- [x] Implementacja `src/analytics/duckdb_runner.py`
  - [x] Połączenie z DuckDB
  - [x] Rejestracja tabel Parquet
  - [x] Wykonywanie queries
- [x] Implementacja `src/analytics/capacity.py`
  - [x] Generowanie 6 orientacji (permutacje)
  - [x] Obsługa constraints (ANY, UPRIGHT_ONLY, FLAT_ONLY)
  - [x] Sprawdzanie dopasowania do nośnika
  - [x] Detekcja BORDERLINE (threshold 2mm)
  - [x] Sprawdzanie limitu wagowego
  - [x] Obliczanie N per carrier
  - [x] Sizing maszyn z utilization
- [x] Testy jednostkowe dla capacity (tests/test_analytics.py)

---

## FAZA 6: Analityka Wydajnościowa ✅

- [x] Implementacja `src/analytics/shifts.py`
  - [x] Parsowanie YAML harmonogramu
  - [x] Obsługa base schedule
  - [x] Obsługa exceptions (date_overlay, range_overlay)
  - [x] Przypisanie shift do timestamp
- [x] Implementacja `src/analytics/performance.py`
  - [x] KPI: lines/hour
  - [x] KPI: orders/hour
  - [x] KPI: units/hour
  - [x] KPI: unique SKU/hour
  - [x] KPI per zmiana z productive hours
  - [x] Peak analysis (max, P90, P95)
  - [x] Udział overlay w pracy
- [x] Testy jednostkowe dla performance (tests/test_analytics.py)

---

## FAZA 7: Raportowanie ✅

- [x] Implementacja `src/reporting/__init__.py`
- [x] Implementacja `src/reporting/csv_writer.py`
  - [x] Separator ';'
  - [x] Encoding UTF-8 BOM
  - [x] Formatowanie liczb wg standardu
- [x] Implementacja `src/reporting/main_report.py`
  - [x] Format Key-Value (Section | Metric | Value)
  - [x] Sekcje: RUN_INFO, DATA_QUALITY, CAPACITY, PERFORMANCE
- [x] Implementacja `src/reporting/dq_reports.py`
  - [x] DQ_Summary.csv
  - [x] DQ_MissingCritical.csv
  - [x] DQ_SuspectOutliers.csv
  - [x] DQ_HighRiskBorderline.csv
  - [x] DQ_Masterdata_Duplicates.csv
  - [x] DQ_Masterdata_Conflicts.csv
  - [x] DQ_SKU_Collisions.csv
- [x] Implementacja `src/reporting/readme.py` - README.txt
- [x] Implementacja `src/reporting/manifest.py` - Manifest.json z SHA256
- [x] Implementacja `src/reporting/zip_export.py` - paczka ZIP
- [x] Testy jednostkowe dla reporting (tests/test_reporting.py)

---

## FAZA 8: UI Streamlit ✅

> **Uwaga:** UI zaimplementowane w monolitycznym pliku `app.py` zamiast osobnych komponentów.

- [x] Implementacja `src/ui/__init__.py`
- [x] Implementacja `src/ui/app.py` - główna aplikacja (monolityczna)
  - [x] Konfiguracja page (title, layout)
  - [x] Session state management
  - [x] Nawigacja między zakładkami (tabs)
- [x] Sidebar (w app.py: `render_sidebar()`)
  - [x] Client name input
  - [x] Utilization sliders (VLM, MiB)
  - [x] Productive hours input
  - [x] Borderline threshold input
  - [x] Imputation toggle
- [x] Mapping Wizard (w app.py: `render_mapping_ui()`)
  - [x] Tabela kolumn źródłowych
  - [x] Auto-suggested mappings
  - [x] Dropdown do ręcznego wyboru
  - [x] Confidence indicator
  - [x] Apply / Reset buttons (Back/Import)
- [x] Import Page (w app.py: `render_import_tab()`)
  - [x] File upload (XLSX, CSV, TXT)
  - [-] File type selection - auto-detected
  - [x] Preview first N rows
  - [x] Trigger mapping wizard
- [x] Validation Page (w app.py: `render_validation_tab()`)
  - [x] Data Quality Scorecard (metrics)
  - [x] Coverage % bars (progress)
  - [x] Listy problemów (warnings)
  - [x] Imputacja button
  - [x] Before/After comparison
- [x] Analysis Page (w app.py: `render_analysis_tab()`)
  - [x] Wybór nośników (multiselect)
  - [x] Konfiguracja zmian (wybór harmonogramu)
  - [x] Run Analysis button
  - [x] Progress bar (spinner)
  - [x] Results summary (metrics)
- [x] Reports Page (w app.py: `render_reports_tab()`)
  - [x] Lista raportów z opisami
  - [x] Preview każdego raportu (podgląd)
  - [x] Download individual CSV (przyciski pobierania)
  - [x] Download ZIP button
- [x] Testy manualne UI

---

## FAZA 9: Integracja i Testy ✅

- [x] Test integracyjny: full pipeline (Masterdata only)
- [x] Test integracyjny: full pipeline (Masterdata + Orders)
- [x] Test struktury katalogów runs/
- [x] Test spójności danych między raportami
- [-] Test wydajnościowy: 200k SKU - pominięte (brak danych)
- [-] Test wydajnościowy: 2M linii Orders - pominięte (brak danych)
- [x] Dokumentacja README.md
- [x] Code review i refactoring
- [x] Finalne testy

---

## Legenda

- `[ ]` - Do zrobienia
- `[x]` - Zrobione
- `[-]` - Pominięte / Nie dotyczy
