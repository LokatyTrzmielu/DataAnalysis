# Plan Implementacji DataAnalysis

## Podsumowanie

| Parametr | Wartość |
|----------|---------|
| Stack | Python 3.11+, DuckDB, Polars, Streamlit, Pydantic |
| Architektura | Backend-first, monolityczny UI |
| Status | **Wszystkie fazy ukończone** |

---

## Moduły

| Moduł | Pliki | Opis |
|-------|-------|------|
| `src/core/` | config, formatting, paths, types, carriers | Konfiguracja, typy Pydantic |
| `src/ingest/` | readers, mapping, units, sku_normalize, pipeline, cleaning | Import XLSX/CSV, Mapping Wizard |
| `src/quality/` | validators, dq_metrics, dq_lists, impute, pipeline | Walidacja, DQ scorecard, imputacja |
| `src/model/` | masterdata, orders | Przetwarzanie danych |
| `src/analytics/` | duckdb_runner, capacity, shifts, performance | Analiza pojemnościowa i wydajnościowa |
| `src/reporting/` | csv_writer, main_report, dq_reports, readme, manifest, zip | Raporty CSV, ZIP |
| `src/ui/` | app.py, theme.py, layout.py, views/ | Streamlit UI (modernizacja w toku) |

---

## Status Faz

| Faza | Nazwa | Status |
|------|-------|--------|
| 0 | Przygotowanie projektu | ✅ |
| 1 | Dane testowe | ✅ |
| 2 | Import danych (Ingest) | ✅ |
| 3 | Walidacja i jakość danych | ✅ |
| 4 | Model danych | ✅ |
| 5 | Analityka pojemnościowa | ✅ |
| 6 | Analityka wydajnościowa | ✅ |
| 7 | Raportowanie | ✅ |
| 8 | UI Streamlit | ✅ |
| 9 | Testy integracyjne | ✅ |
| 10 | Poprawki UI i walidacji | ✅ |
| 11 | System nośników | ✅ |
| 12 | Code review i weryfikacja | ✅ |
| 13 | Modernizacja UI | ✅ |
| 14 | Paleta kolorów i przyciski statusu | ✅ |
| 15 | Restrukturyzacja nawigacji | ✅ |
| 16 | UI Audit Priority 3 | ✅ |
| 17 | Performance module (date/time import, analytics, UI) | ✅ |
| 18 | Validation split (Capacity/Performance) | ✅ |
| 19 | Performance Validation UI/UX fixes | ✅ |

---

## Modernizacja UI

**Szczegółowy plan:** `Dev/UI_MODERNIZATION_PLAN.md`

| Etap | Zakres | Status |
|------|--------|--------|
| 1 | Dark theme + struktura plików | ✅ |
| 2 | Komponenty UI (layout.py) | ✅ |
| 3 | Refaktoryzacja app.py na views | ✅ |
| 4 | Import view restyling | ✅ |
| 5 | Capacity view + Plotly | ✅ |
| 6 | Performance view + Plotly | ✅ |
| 7 | Reports view | ✅ |
| 8 | Finalizacja i testy | ✅ |

---

## Paleta Kolorów i Przyciski Statusu

**Szczegółowy plan:** `Dev/UI_COLOR_BUTTONS_PLAN.md`

**Zmiany:**
- Nowa paleta kawowo-brązowa (coffee-bean, graphite, burnt-caramel)
- 7 typów statusu z ikonami SVG (pending, in_progress, submitted, in_review, success, failed, expired)
- Nowe funkcje: `render_status_button()`, `render_status_buttons_inline()`
- Zachowana wsteczna kompatybilność ze starymi `.status-badge`

---

## Restrukturyzacja Nawigacji

**Szczegółowy plan:** `Dev/UI_NAVIGATION_PLAN.md`

**Phase 1:** Nawigacja sidebar
- 4 sekcje: Dashboard, Capacity, Performance, Reports
- Sub-zakładki: Import | Validation | Analysis
- Dashboard z 4 kartami KPI

**Phase 2:** Styling & Consistency
- Settings przeniesione z sidebar do zakładek Validation
- Sidebar bez bullet points (hover rust-brown, selected dim-grey)
- Usunięto wszystkie emoji z UI
- Standardowe headers: `st.header()` / `st.subheader()`

---

**Nowe pliki (Etap 1):**
- `src/ui/theme.py` - COLORS, get_custom_css(), apply_theme()
- `src/ui/layout.py` - render_kpi_card(), render_section(), render_status_badge()
- `src/ui/views/__init__.py` - katalog na widoki zakładek

**Rozszerzenia (Etap 2):**
- `theme.py` - hover effects, responsywność CSS, message boxes, scrollbar
- `layout.py` - render_message_box(), render_table_container(), render_empty_state(), render_progress_section()
- `views/components_demo.py` - strona demo wszystkich komponentów
- `run_components_demo.py` - skrypt uruchamiający demo

**Refaktoryzacja (Etap 3):**
- Rozbicie `app.py` z 1838 linii na ~280 linii
- Moduły widoków: import_view.py, validation_view.py, capacity_view.py, performance_view.py, reports_view.py
- 5 zakładek: Import | Validation | Capacity | Performance | Reports

**Import view restyling (Etap 4):**
- Dark theme dla statusów pól (rgba backgrounds)
- `render_section_header()` dla nagłówków (📦 Masterdata, 📋 Orders, 🔗 Column mapping)
- `render_status_badge()` dla statusu importu
- `render_error_box()` dla błędów duplikacji
- Stylizowane mapping summary (auto=zielony, manual=niebieski)

---

## System Nośników

**Plik konfiguracji:** `src/core/carriers.yml`

3 predefiniowane nośniki:
- Nosnik 1: 600×400×220mm (wew. 570×370×200), max 35kg
- Nosnik 2: 640×440×238mm (wew. 610×410×210), max 35kg
- Nosnik 3: 3650×864×200mm, max 440kg

**Progi outlierów** (`src/core/config.py`):
```
length/width: 10-2000mm | height: 5-1500mm | weight: 0.01-200kg
```

---

## Funkcje Wyłączone

| Funkcja | Lokalizacja | Plan powrotu |
|---------|-------------|--------------|
| Utilization sliders | `app.py:111-127` | Zdefiniować wpływ na sizing maszyn |
| Optional fields | `app.py:420-472` | Określić potrzebne pola opcjonalne |

---

## Decyzje Architektoniczne

| Decyzja | Uzasadnienie |
|---------|--------------|
| Polars zamiast Pandas | Wydajność na dużych zbiorach |
| DuckDB dla agregacji | SQL bez ładowania do RAM |
| Pydantic dla typów | Type safety + walidacja |
| Monolityczny UI | Szybszy development |

---

## Kluczowe Formuły

| Metryka | Formuła |
|---------|---------|
| volume_m3 | `(L×W×H) / 10⁹` |
| stock_volume_m3 | `volume_m3 × stock_qty` |
| Fit check | 6 orientacji + borderline 2mm |
