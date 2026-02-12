# DataAnalysis - Kontekst Projektu

> Plik służy do zachowania kontekstu projektu przy przerwaniu sesji.

---

## Informacje Podstawowe

| Parametr | Wartość |
|----------|---------|
| Nazwa projektu | DataAnalysis |
| Katalog roboczy | `D:\VS\DataAnalysis` |
| Data rozpoczęcia | 2026-01-03 |
| Status | **MVP KOMPLETNE** - Modernizacja UI + nawigacja sidebar |
| Testy | 143 (wszystkie przechodzą) |

---

## Cel Projektu

Lokalna aplikacja do analizy danych magazynowych:
- **Analiza pojemnościowa** - dopasowanie SKU do nośników Kardex (6 orientacji, borderline)
- **Analiza wydajnościowa** - KPI (lines/h, orders/h), harmonogram zmian, peak analysis
- **Raportowanie** - CSV + ZIP z manifestem SHA256

---

## Stack Technologiczny

| Technologia | Zastosowanie |
|-------------|--------------|
| Python 3.11+ | Język programowania |
| Polars | Transformacje danych |
| DuckDB | Agregacje SQL |
| Streamlit | UI lokalne |
| Plotly | Interaktywne wykresy |
| Pydantic | Typy i walidacja |

---

## Struktura Projektu

```
src/
├── core/       # Konfiguracja, typy, formatowanie, carriers
├── ingest/     # Import danych, Mapping Wizard
├── quality/    # Walidacja, DQ metrics, imputacja
├── model/      # Masterdata, Orders processing
├── analytics/  # DuckDB, capacity, performance
├── reporting/  # Raporty CSV, manifest, ZIP
└── ui/         # Streamlit UI
    ├── app.py      # Główna aplikacja (sidebar nav, ~420 linii)
    ├── theme.py    # Dark theme, paleta kolorów, CSS, sidebar styling
    ├── layout.py   # Komponenty UI (KPI cards, badges, sekcje)
    └── views/      # Widoki zakładek
        ├── import_view.py                # Import danych z mapowaniem
        ├── capacity_validation_view.py   # Walidacja Masterdata
        ├── performance_validation_view.py # Walidacja Orders (placeholder)
        ├── capacity_view.py              # Analiza pojemnościowa
        ├── performance_view.py           # Analiza wydajnościowa
        ├── reports_view.py               # Raporty i eksport
        └── components_demo.py            # Demo komponentów UI

# Nawigacja UI (sidebar)
SIDEBAR:                    MAIN VIEW:
├─ Dashboard         ───>   Status overview (4 KPI cards)
├─ Capacity          ───>   [Import] [Validation] [Analysis]
├─ Performance       ───>   [Import] [Validation] [Analysis]
└─ Reports           ───>   Report generation

tests/          # 143 testy jednostkowe + integracyjne
runs/           # Wyniki analiz per klient
```

---

## Kluczowe Koncepty

### Analiza Pojemnościowa
- **Fit check**: 6 orientacji, constraints (ANY/UPRIGHT_ONLY/FLAT_ONLY)
- **Borderline**: threshold 2mm
- **volume_m3**: `(L×W×H) / 10⁹` - objętość jednostki
- **stock_volume_m3**: `volume_m3 × stock_qty` - objętość magazynowa

### Data Quality
- `0` = missing (dla wymiarów, wagi, qty)
- Imputacja: mediana globalna
- Flagi: RAW vs ESTIMATED

---

## Uruchomienie

```bash
# Aplikacja
streamlit run src/ui/app.py

# Testy
python -m pytest tests/ -v
```

---

## Funkcje Wyłączone Tymczasowo

| Funkcja | Lokalizacja | Powód |
|---------|-------------|-------|
| Utilization sliders | `app.py:111-127` | Wymaga integracji z analizą |
| Optional fields | `app.py:420-472` | Uproszczenie UI |

---

## Modernizacja UI (zakończona)

**Plan:** `Dev/UI_MODERNIZATION_PLAN.md`

| Etap | Nazwa | Status |
|------|-------|--------|
| 1 | Theme i struktura plików | ✅ |
| 2 | Komponenty UI (layout.py) | ✅ |
| 3 | Refaktoryzacja app.py | ✅ |
| 4 | Import view (restyling) | ✅ |
| 5 | Capacity view (KPI + wykresy Plotly) | ✅ |
| 6 | Performance view (KPI + wykresy Plotly) | ✅ |
| 7 | Reports view (KPI + styled cards + preview) | ✅ |
| 8 | Finalizacja i testy | ✅ |

**Zmiany Etapu 1:**
- Dark theme (#121212, #1E1E1E, #4CAF50)
- `theme.py` - paleta kolorów, CSS
- `layout.py` - komponenty KPI, badges, sekcje
- `views/` - katalog na widoki

**Zmiany Etapu 2:**
- Rozszerzone CSS - hover effects, responsywność (4→2→1 kolumny)
- Message boxes (info/warning/error/success)
- Nowe komponenty: table_container, metric_row, divider, spacer, empty_state, progress_section
- Strona demo: `views/components_demo.py`
- Skrypt testowy: `run_components_demo.py`

**Zmiany Etapu 3:**
- Rozbicie monolitu app.py (1838 → ~280 linii)
- Nowe moduły widoków:
  - `import_view.py` - import + mapowanie kolumn
  - `validation_view.py` - walidacja danych
  - `capacity_view.py` - nośniki + analiza pojemnościowa
  - `performance_view.py` - zmiany + analiza wydajnościowa
  - `reports_view.py` - generowanie raportów
- Nowa struktura 5 zakładek: Import | Validation | Capacity | Performance | Reports
- Aplikowanie dark theme w main()

**Zmiany Etapu 4:**
- Import view dostosowany do dark theme
- `_get_field_status_html()` - rgba backgrounds (zielony/czerwony dla status pól)
- `render_section_header()` - nagłówki Masterdata 📦, Orders 📋, Column mapping 🔗
- `render_status_badge()` - status ukończonego importu (✓ X SKU imported)
- `render_error_box()` - stylizowane błędy duplikacji kolumn
- Mapping summary - kolory auto (zielony) / manual (niebieski)
- Główny header - stylowany z ikoną 📁

**Zmiany Etapu 5:**
- Dodano Plotly do zależności (`plotly>=5.18.0`)
- Capacity view z nowymi sekcjami:
  - **KPI Section**: 4 karty (SKU Count, Avg Fit %, Avg Dimensions, Avg Weight)
  - **Charts Section**:
    - Histogram gabarytów (L/W/H overlay)
    - Stacked bar chart FIT/BORDERLINE/NOT_FIT per carrier
    - Histogram wag
  - **Results Table**: filtry status + carrier, eksport CSV
- Wykresy Plotly z dark theme (`apply_plotly_dark_theme()`)
- Zachowano istniejące elementy: Carrier management, Exclusion settings, Analysis mode

**Zmiany Etapu 6:**
- Performance view z nowymi sekcjami:
  - **KPI Section**: 4 karty (Avg Lines/h, Peak Hour, Total Orders, Avg Lines/Order)
  - **Charts Section**:
    - Daily activity line chart (2 osie Y: lines + orders)
    - Hourly heatmap (dzień tygodnia × godzina)
    - Order structure histogram (lines per order)
- Wykresy Plotly z dark theme
- Zachowano istniejące elementy: Shift configuration (Default/Custom/YAML/None)

**Zmiany Etapu 7:**
- Reports view z nowymi sekcjami:
  - **KPI Section**: 4 karty (Total Reports, Data Sources, DQ Reports, Analysis Reports)
  - **Report Categories**: stylizowane karty pogrupowane per kategoria
  - **Bulk Download**: przycisk ZIP z progress bar (20% → 40% → 80% → 100%)
  - **Data Preview**: expanders ze styled metrics dla DQ, Capacity, Performance
- Nowe funkcje: `_render_reports_kpi()`, `_render_report_categories()`, `_render_category_section()`, `_render_report_card()`, `_render_bulk_download()`, `_generate_zip_package()`, `_render_data_preview()`, `_render_quality_preview()`, `_render_capacity_preview()`, `_render_performance_preview()`
- Nowe style CSS: `.report-category-header`, `.report-card`, `.preview-metric`

**Zmiany Etapu 8:**
- Finalizacja i testy:
  - **Testy**: 122 testy jednostkowe i integracyjne - wszystkie przechodzą
  - **Responsywność**: breakpoints CSS 768px (2 kolumny), 480px (1 kolumna)
  - **Accessibility**: kontrast kolorów WCAG AAA (12.6:1 dla tekstu głównego)
  - **Edge cases**: obsługa pustych danych i błędów w każdym widoku
  - **Dokumentacja**: README.md zaktualizowane z sekcją "Architektura UI"

---

## Poprawki (2026-01-09)

### Konwersja Timestamp w Pipeline
- **Problem:** Błąd `'int' object has no attribute 'date'` przy analizie wydajnościowej
- **Przyczyna:** Pipeline konwertował tylko stringowe timestampy, nie obsługiwał Unix epoch (int)
- **Rozwiązanie:** `pipeline.py:200-216` - dodano konwersję `pl.from_epoch()` dla typów Int64/Int32/UInt64/UInt32
- **Dodatkowe zabezpieczenie:** `performance.py:123-136` - defensywna konwersja przed użyciem `.date()`

### Null Timestamps w Heatmapie
- **Problem:** `TypeError: unsupported operand type(s) for -: 'NoneType' and 'int'`
- **Przyczyna:** Null timestamps dawały None przy `.dt.weekday()`
- **Rozwiązanie:** `performance_view.py:324` - filtr `pl.col("timestamp").is_not_null()` przed agregacją

### Deprecation Warning Streamlit
- **Problem:** `use_container_width` deprecated po 2025-12-31
- **Rozwiązanie:** Zamiana `use_container_width=True` na `width="stretch"` w 6 plikach:
  - `layout.py`, `capacity_view.py`, `reports_view.py`
  - `performance_view.py`, `components_demo.py`, `import_view.py`

---

## Aktualizacja Palety Kolorów i Przycisków (2026-01-10)

### Nowa Paleta Kawowo-Brązowa
**Plan:** `Dev/UI_COLOR_BUTTONS_PLAN.md`

| Kolor | Hex | Rola |
|-------|-----|------|
| coffee-bean | `#20100e` | Główne tło |
| graphite | `#323232` | Powierzchnie |
| dim-grey | `#5f605b` | Hover states |
| espresso | `#5e3123` | Bordery |
| rust-brown | `#923b1b` | Hover przycisków |
| burnt-caramel | `#b7622c` | Główny akcent |

### Nowe Przyciski Statusu (7 typów)
| Status | Kolor | Ikona |
|--------|-------|-------|
| pending | `#FFB74D` żółty | Triangle warning |
| in_progress | `#64B5F6` niebieski | Dashed circle |
| submitted | `#BA68C8` fioletowy | Paper plane |
| in_review | `#FF8A65` pomarańczowy | Circular arrows |
| success | `#81C784` zielony | Checkmark circle |
| failed | `#E57373` czerwony | X circle |
| expired | `#90A4AE` szary | Clock |

### Zmienione Pliki
- `src/ui/theme.py` - COLORS, STATUS_COLORS, STATUS_ICONS, CSS `.status-btn`
- `.streamlit/config.toml` - nowe kolory Streamlit theme
- `src/ui/layout.py` - `render_status_button()`, `render_status_buttons_inline()`, `get_status_color()`
- `src/ui/__init__.py` - eksporty nowych funkcji
- `src/ui/views/import_view.py` - użycie `render_status_button()`
- `src/ui/views/reports_view.py` - użycie `render_status_buttons_inline()`
- `src/ui/views/components_demo.py` - demo 7 typów statusu

---

## Restrukturyzacja Nawigacji (2026-01-10)

**Plan:** `Dev/UI_NAVIGATION_PLAN.md`

### Phase 1: Nawigacja Sidebar
- Zamiana 5 płaskich zakładek na hierarchiczną nawigację sidebar
- 4 sekcje w sidebar: Dashboard, Capacity, Performance, Reports
- Sub-zakładki w sekcjach: Import | Validation | Analysis
- Dashboard z 4 kartami KPI statusu

### Phase 2: Styling & Consistency
| Zmiana | Szczegóły |
|--------|-----------|
| Settings w Validation | Przeniesiono z sidebar do zakładek Validation |
| Sidebar styling | Bez bullet points, hover rust-brown, selected dim-grey |
| Emoji removal | Usunięto emoji z tabs, headers, sekcji |
| Header standardization | `st.header()` / `st.subheader()` zamiast custom HTML |

### Zmienione pliki (Phase 2)
- `src/ui/app.py` - nawigacja, settings w validation tabs, bez emoji
- `src/ui/theme.py` - CSS dla sidebar navigation styling
- `src/ui/views/import_view.py` - bez emoji, st.subheader
- `src/ui/views/capacity_view.py` - bez emoji, st.subheader
- `src/ui/views/performance_view.py` - bez emoji, st.subheader

---

## Poprawki Import Masterdata (2026-01-23)

### Obsługa Kolumn Stringowych

**Problem:** Błędy konwersji gdy kolumny wymiarów, wag lub stock były typu string zamiast numeric.

**Rozwiązanie:** Dodano defensywne castowanie do Float64/Int64 we wszystkich operacjach na danych numerycznych.

| Plik | Zmiana |
|------|--------|
| `units.py:248,286` | Cast do Float64 przy auto-detect jednostek (sample) |
| `units.py:257-261` | Cast do Float64 przy konwersji wymiarów (L/W/H) |
| `units.py:293` | Cast do Float64 przy konwersji wagi |
| `pipeline.py:120-123` | Cast stock do Int64 przed rename |

**Wzorzec:**
```python
# Przed:
pl.col("length") * factor
# Po:
pl.col("length").cast(pl.Float64, strict=False) * factor
```

---

## Ostatnia Aktualizacja

**Data:** 2026-02-10
**Status:** MVP kompletne, **modernizacja UI zakończona** + nawigacja sidebar + performance module + validation split
