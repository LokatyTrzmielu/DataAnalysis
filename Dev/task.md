# DataAnalysis - Lista Zadań

## Status Projektu

**MVP KOMPLETNE** | 152 testy | Wszystkie fazy ukończone

---

## Fazy Implementacji

| Faza | Nazwa | Zakres | Status |
|------|-------|--------|--------|
| 0 | Przygotowanie | config, formatting, paths, types | ✅ |
| 1 | Dane testowe | fixtures, CSV/XLSX generatory | ✅ |
| 2 | Import (Ingest) | readers, mapping, units, sku_normalize | ✅ |
| 3 | Jakość danych | validators, dq_metrics, dq_lists, impute | ✅ |
| 4 | Model danych | masterdata, orders processing | ✅ |
| 5 | Analiza pojemnościowa | capacity (6 orientacji, borderline) | ✅ |
| 6 | Analiza wydajnościowa | shifts, performance, KPI | ✅ |
| 7 | Raportowanie | csv_writer, reports, manifest, zip | ✅ |
| 8 | UI Streamlit | app.py (monolityczny) | ✅ |
| 9 | Testy | 122 testy jednostkowe + integracyjne | ✅ |
| 10 | Poprawki UI | outliers, borderline, tooltips | ✅ |
| 11 | System nośników | carriers.py, carriers.yml | ✅ |
| 12 | Code review | weryfikacja volume_m3, naprawa testów | ✅ |
| 13 | Modernizacja UI | dark theme, komponenty, Plotly | ✅ |
| 14 | Poprawki bugów | timestamp conversion, null handling | ✅ |
| 15 | UI Audit Priority 3 | render_bold_label, render_data_table, DEPRECATED | ✅ |
| 16 | UI Fixes - Sidebar & Titles | nawigacja, statusy, tytuły sekcji | ✅ |
| 17 | Naprawa Stock Volume | konwersja stock z przecinkami | ✅ |
| 18 | Priorytet nośników | ręczny priorytet w trybie Prioritized | ✅ |
| 19 | Import string columns | obsługa kolumn stringowych przy imporcie | ✅ |
| 20 | Performance module | date/time import, analytics, UI charts | ✅ |
| 21 | Validation split | rozdzielenie Capacity/Performance validation | ✅ |
| 22 | Performance Validation UI/UX | poprawki layoutu, kolumn, outliers, working pattern | ✅ |
| 23 | Units→Pieces & Throughput | rename labels, 18 nowych metryk throughput | ✅ |
| 24 | Numeric cleaning | uniwersalna clean_numeric_column() | ✅ |

---

## Modernizacja UI (Faza 13) - ZAKOŃCZONA

**Plan:** `Dev/UI_MODERNIZATION_PLAN.md`

| Etap | Zakres | Status |
|------|--------|--------|
| 1 | Dark theme + struktura | ✅ |
| 2 | Komponenty UI | ✅ |
| 3 | Refaktoryzacja app.py | ✅ |
| 4 | Import view | ✅ |
| 5 | Capacity view + Plotly | ✅ |
| 6 | Performance view + Plotly | ✅ |
| 7 | Reports view | ✅ |
| 8 | Finalizacja | ✅ |

---

## Poprawki Bugów (Faza 14) - ZAKOŃCZONA

| Problem | Rozwiązanie | Plik |
|---------|-------------|------|
| `'int' object has no attribute 'date'` | Konwersja Unix epoch → datetime | `pipeline.py:200-216` |
| `InvalidOperationError` na `.dt.weekday()` | Defensywna konwersja timestamp | `performance.py:123-136` |
| `NoneType - int` w heatmapie | Filtr null timestamps | `performance_view.py:324` |
| `use_container_width` deprecated | Zamiana na `width="stretch"` | 6 plików UI |

---

## Naprawa Stock Volume (Faza 17) - ZAKOŃCZONA

**Problem:** Po Capacity Analysis wartości Stock volume = 0

**Przyczyna:** W `pipeline.py` wartości stock z przecinkiem/kropką dziesiętną (np. "100,5") były konwertowane na NULL przy `cast(Int64)`, co skutkowało `stock_qty = 0`.

| Zmiana | Plik | Szczegóły |
|--------|------|-----------|
| Nowa konwersja stock | pipeline.py:119-136 | string → replace comma → float → round → int |
| Ostrzeżenie o NULL | pipeline.py:133-136 | Informacja gdy wartości nie mogą być przekonwertowane |

**Przepływ konwersji:**
```
"100,5" → "100.5" → 100.5 → 101.0 → 101
```

---

## UI Fixes - Sidebar & Titles (Faza 16) - ZAKOŃCZONA

**Zmiany:**

| Zmiana | Plik | Szczegóły |
|--------|------|-----------|
| Aktywna zakładka nawigacji | theme.py | Dodano obramowanie 2px accent (#b7622c) dla wybranego elementu |
| Usunięcie border ze statusów | theme.py | Dodano selektory dla .stAlertContainer z border: none |
| Nazwa aplikacji | app.py:130 | "DataAnalysis" → "Data Analysis" |
| Tytuł Capacity | app.py:220 | Dodano st.header("Capacity") |
| Tytuł Performance | app.py:348 | Dodano st.header("Performance") |

**CSS Selektory dla nawigacji:**
- `label:has(input:checked)` - nowoczesny CSS
- `label[aria-checked="true"]` - fallback ARIA
- `label[data-checked="true"]` - fallback legacy

---

## UI Audit Priority 3 (Faza 15) - ZAKOŃCZONA

**Nowe komponenty w layout.py:**
- `render_bold_label(text, icon, size)` - stylizowane etykiety bold
- `render_data_table(df, height, title)` - wrapper dla dataframe

**Zmiany w plikach:**
| Plik | Zakres zmian |
|------|--------------|
| capacity_view.py | 8 zamian bold labels na render_bold_label() |
| validation_view.py | 2 zamiany st.write("**...**") |
| performance_view.py | 2 zamiany st.markdown("**...**") |
| app.py | 1 zamiana (Outlier validation) |
| reports_view.py | 2 zamiany bold labels |
| layout.py | Dodano DEPRECATED do legacy status functions |
| reports_view.py | Usunięto nieużywane legacy imports |

---

## Funkcje Wyłączone Tymczasowo

| Funkcja | Status | Lokalizacja |
|---------|--------|-------------|
| Utilization sliders | ⏸️ | `app.py:111-127` |
| Optional fields mapping | ⏸️ | `app.py:420-472` |

---

## Priorytet Nośników (Faza 18) - ZAKOŃCZONA

**Cel:** Ręczne ustawienie priorytetu nośników w trybie "Prioritized"

**Zmiany:**

| Plik | Zmiana |
|------|--------|
| `types.py` | Dodano pole `priority: Optional[int]` do `CarrierConfig` |
| `carriers.py` | Obsługa priority przy zapisie custom carriers |
| `capacity.py` | Filtrowanie i sortowanie po priority w trybie Prioritized |
| `carriers.yml` | Dodano priority: 1, 2, 3 do predefined carriers |
| `app.py` | Ładowanie priority do session state przy starcie |
| `capacity_view.py` | Kolumna Priority w tabeli nośników z edycją |
| `capacity_view.py` | Zaktualizowane komunikaty i etykiety |

**UI - Tabela nośników:**
- Nowa kolumna "Priority" z number_input
- Wartość 0 = brak priorytetu (excluded from Prioritized)
- Wartość 1-99 = priorytet (1 = pierwszy w kolejności)

**Logika:**
- `priority: 1` = najwyższy priorytet (pierwszy w kolejności)
- `priority: 0` lub `None` = nośnik pomijany w trybie Prioritized
- W trybie Independent priorytet nie ma wpływu

**Przepływ danych:**
```
UI: Priority input (0=excluded, 1-99=priority)
    ↓
session_state.custom_carriers[i]["priority"] = int lub None
    ↓
capacity.py (prioritization_mode=True):
    1. Filter: carriers where priority is not None
    2. Sort: by priority ascending (1 first, 2 second, ...)
    3. Assign SKU to first fitting carrier
```

**UWAGA:** Po aktualizacji kodu należy zrestartować aplikację Streamlit,
aby załadować nośniki z polem priority.

---

## Import String Columns (Faza 19) - ZAKOŃCZONA

**Problem:** Błędy konwersji gdy kolumny wymiarów, wag lub stock w pliku źródłowym były typu string.

**Rozwiązanie:** Defensywne castowanie `cast(pl.Float64, strict=False)` przed operacjami numerycznymi.

| Plik | Zmiana |
|------|--------|
| `units.py:248` | Cast przy auto-detect length unit |
| `units.py:286` | Cast przy auto-detect weight unit |
| `units.py:257-261` | Cast przy konwersji L/W/H do mm |
| `units.py:293` | Cast przy konwersji weight do kg |
| `pipeline.py:120-123` | Cast stock do Int64 |

**Parametr `strict=False`** powoduje, że nieparsowalne wartości stają się `null` zamiast wyrzucać błąd.

---

## Rozdzielenie Validation (Faza 21) - ZAKOŃCZONA

**Problem:** `_render_performance_validation()` wywoływała `render_validation_view()` przeznaczoną dla Masterdata - Orders mają inny schemat danych.

**Rozwiązanie:** Dwa niezależne widoki walidacji:

| Plik | Funkcja | Zakres |
|------|---------|--------|
| `capacity_validation_view.py` | `render_capacity_validation_view()` | Walidacja Masterdata (quality pipeline, coverage, issues) |
| `performance_validation_view.py` | `render_performance_validation_view()` | Walidacja Orders (summary, missing SKUs, date gaps, quantity anomalies, working pattern) |

---

## Performance Validation UI/UX (Faza 22) - ZAKOŃCZONA

**Problem:** Po implementacji widoku Performance Validation, testy użytkownika wykazały 5 problemów UI/UX.

**Poprawki:**

| # | Problem | Rozwiązanie |
|---|---------|-------------|
| 1 | 5 kolumn summary zbyt ciasnych | Podział na 2 rzędy po 3 kolumny |
| 2 | Expandable tables pokazywały 3 hardcoded kolumny | Wyświetlanie wszystkich kolumn z importowanego pliku |
| 3 | Outliers: "mean=X, std=Y" niezrozumiałe | User-friendly message + caption wyjaśniający 3-sigma |
| 4 | Working pattern: wartości "N/A" | Fallback: shifts=1 gdy max==min hour, weekday z order_date |
| 5 | Date gaps: 1 kolumna missing_date | Dodanie weekday + wierszy z sąsiednich dni (pełne kolumny) |

**Plik:** `src/ui/views/performance_validation_view.py`

---

## Rename Units→Pieces & Detailed Throughput (Faza 23) - ZAKOŃCZONA

**Zmiany:**

| # | Zmiana | Pliki |
|---|--------|-------|
| 1 | Rename "Total Units" → "Total Pieces" | performance_view.py, reports_view.py, main_report.py |
| 2 | Rename "Avg Units/*" → "Avg Pieces/*" | performance_view.py, main_report.py |
| 3 | 18 nowych metryk throughput (3 grupy × 3 okresy × avg/max) | performance_view.py |

**Nowy layout Detailed Statistics:**
- Wiersz z 4 metrykami summary (Total Lines, Orders, Pieces, SKU)
- Ratio metrics (Avg Lines/Order, Avg Pieces/Line, percentyle)
- 3 tabele throughput: Orders, Order Lines, Pieces
  - Każda z wierszami: Per Hour, Per Shift, Per Day
  - Kolumny: Avg, Max

**Źródła danych:**
- Per Hour: z istniejących pól KPI (avg_*_per_hour, peak_*_per_hour)
- Per Day: obliczone z `result.daily_metrics` (mean/max)
- Per Shift: Per Day / shifts_per_day

---

## Ujednolicenie Numeric Cleaning (Faza 24) - ZAKOŃCZONA

**Problem:** Europejskie formaty numeryczne (przecinek dziesiętny, notacja naukowa `1,0E+0`) obsługiwane tylko dla `stock`. Kolumny wymiarów i wagi cicho konwertowały takie wartości na `null`.

**Rozwiązanie:** Uniwersalna funkcja `clean_numeric_column()` w nowym module `src/ingest/cleaning.py`.

| Plik | Zmiana |
|------|--------|
| `src/ingest/cleaning.py` | **NOWY** — `clean_numeric_column()` |
| `src/ingest/pipeline.py` | Import + użycie w stock (zastąpienie inline kodu) |
| `src/ingest/units.py` | Import + użycie w dimensions i weight (sample + conversion) |
| `tests/test_ingest.py` | 9 nowych testów edge cases |

**GitHub Issue:** #26
**Branch:** `feature/numeric-cleaning`

---

## Możliwe Przyszłe Rozszerzenia

- [ ] Testy wydajnościowe (200k SKU, 2M orders)
- [ ] Eksport do Excel z formatowaniem
- [x] Dashboard z wykresami (Plotly) → Faza 13
- [ ] Przywrócenie utilization sliders
- [ ] Rozszerzenie optional fields

---

## Legenda

| Symbol | Znaczenie |
|--------|-----------|
| ✅ | Ukończone |
| ⏳ | W trakcie realizacji |
| ⏸️ | Wyłączone tymczasowo |
| [ ] | Do zrobienia (przyszłość) |
