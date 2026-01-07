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
  - [x] Ręczne wprowadzenie wymiarów nośnika (W/L/H w mm, waga w kg)
  - [x] Opcjonalne ID i nazwa nośnika (auto-generowane)
  - [x] Konfiguracja zmian (wybór harmonogramu)
  - [x] Własny harmonogram zmian (dni/godziny/zmiany)
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

## FAZA 10: Poprawki UI i Walidacji (2026-01-06) ✅

### Import
- [x] Przesunięcie przycisku "Import Masterdata" do prawej krawędzi
- [x] Naprawa etykiety "(manual)" w podsumowaniu mapowania
  - Zachowanie statusu is_auto z oryginalnego mapowania
  - Oznaczanie jako "manual" tylko przy zmianie przez użytkownika
- [x] Wykrywanie duplikatów kolumn w mapowaniu
  - Komunikat błędu z listą zduplikowanych mapowań
  - Blokada przycisku Import przy duplikatach
- [x] Wybór jednostki wagi przy imporcie (Auto-detect / Grams / Kilograms)
  - Przydatne gdy auto-detekcja zawodzi dla lekkich przedmiotów

### Walidacja
- [x] Sekcja pomocy walidacji ("Validation help")
  - Opisy: Missing Critical, Outliers, Borderline, Duplicates, Conflicts
  - Info o wykluczaniu outliers/borderline z analizy
- [x] Konfigurowalne progi outlierów w sidebarze
  - Checkbox włączania/wyłączania walidacji outlierów
  - Pola min/max dla wymiarów (mm) i wagi (kg)
  - Integracja z pipeline'em jakości danych
- [x] Poprawione liczniki Outliers/Borderline (pokazuje 0 gdy walidacja wyłączona)
- [x] Weryfikacja jednostki wagi (kg) - potwierdzone że system używa kg

### Analiza pojemnościowa
- [x] Wykluczanie Outliers i Borderline SKU z analizy pojemnościowej
  - Automatyczne filtrowanie przed analizą
  - Komunikat "Excluded from analysis: X SKU (outliers/borderline)"
- [x] Tooltips do wszystkich metryk pojemnościowych
  - FIT, BORDERLINE, NOT FIT, Fit %, Volume - wyjaśnienia działania
- [x] Nowa metryka "Stock volume (m³)"
  - Suma objętości jednostkowej × zapas dla wszystkich pasujących SKU
  - Dodane pole stock_volume_m3 do CarrierStats
- [x] Przebudowa widoku tabeli nośników
  - Kompaktowy format 2-wierszowy zamiast 7-kolumnowego
  - Separator między nośnikami

---

## FAZA 11: System Nośników i Refaktoryzacja (2026-01-07) ✅

### System nośników
- [x] Utworzenie `src/core/carriers.py` - moduł CarrierService
  - [x] Klasa CarrierService z metodami load_all_carriers() i save_custom_carriers()
  - [x] Domyślne nośniki hardcoded jako fallback
  - [x] Helper function load_carriers()
- [x] Utworzenie `src/core/carriers.yml` - konfiguracja nośników
  - [x] Sekcja `carriers` dla predefiniowanych nośników
  - [x] Sekcja `custom_carriers` dla zapisanych przez użytkownika
  - [x] 3 predefiniowane nośniki (600x400x220, 640x440x238, 3650x864x200)
- [x] Rozszerzenie `src/core/types.py` - pole is_predefined w CarrierConfig

### Zunifikowane progi outlierów
- [x] Dodanie `OUTLIER_THRESHOLDS` do `src/core/config.py`
  - [x] Progi dla length_mm, width_mm, height_mm, weight_kg, stock_qty
  - [x] Centralne źródło prawdy dla walidacji
- [x] Aktualizacja `src/quality/validators.py` - użycie OUTLIER_THRESHOLDS
- [x] Aktualizacja `src/quality/dq_lists.py` - użycie OUTLIER_THRESHOLDS

### Refaktoryzacja UI
- [x] Uproszczenie layoutu w `src/ui/app.py`
- [x] Integracja CarrierService z interfejsem analizy pojemnościowej
- [x] Poprawki wyświetlania i interakcji

---

## Funkcje Tymczasowo Wyłączone ⏸️

> Zakomentowane w kodzie - do przyszłego rozwinięcia

### Utilization Sliders
- [-] Slidery VLM (0.70-0.80) i MiB (0.60-0.75) w sidebarze
- **Lokalizacja:** `src/ui/app.py` linie 111-127
- **Plan powrotu:**
  - [ ] Zdefiniować wpływ utilization na sizing maszyn
  - [ ] Określić współczynniki per typ nośnika
  - [ ] Zintegrować z analizą pojemnościową
  - [ ] Odkomentować i podłączyć logikę

### Optional Fields (Masterdata Mapping)
- [-] Sekcja mapowania opcjonalnych pól (np. stock)
- **Lokalizacja:** `src/ui/app.py` linie 420-472
- **Plan powrotu:**
  - [ ] Określić potrzebne pola opcjonalne
  - [ ] Zaprojektować UX prezentacji
  - [ ] Rozważyć wpływ na analizę (stock × volume)
  - [ ] Odkomentować i dostosować UI

---

## Legenda

- `[ ]` - Do zrobienia
- `[x]` - Zrobione
- `[-]` - Pominięte / Nie dotyczy
- `⏸️` - Tymczasowo wyłączone (zakomentowane)
