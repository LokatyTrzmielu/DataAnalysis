# Plan Modernizacji UI - Nowa Struktura Nawigacji

> **Data:** 2026-01-10
> **Status:** ZAKOŃCZONE
> **Źródło:** UI_Streamlit.docx

## Cel

Przebudowa struktury nawigacji aplikacji z **płaskich 5 zakładek** na **hierarchiczną nawigację w sidebar** z sub-zakładkami wewnątrz każdej sekcji.

---

## Docelowa Struktura

```
SIDEBAR:                    MAIN VIEW:
┌─────────────────┐        ┌──────────────────────────────────┐
│ 🏠 Dashboard    │───────>│ Overview / Summary               │
├─────────────────┤        └──────────────────────────────────┘
│ 📊 Capacity     │───────>│ [Import] [Validation] [Analysis] │
├─────────────────┤        │ + Client name, Parameters        │
│ ⚡ Performance  │───────>│ [Import] [Validation] [Analysis] │
├─────────────────┤        │ + Productive hours               │
│ 📄 Reports      │───────>│ [Report generation]              │
└─────────────────┘        └──────────────────────────────────┘
```

---

## Decyzje użytkownika

| Temat | Decyzja |
|-------|---------|
| Dashboard | Tylko status (4 karty KPI), bez quick actions |
| Nawigacja [Next]/[Back] | Tylko w obrębie sekcji (Streamlit tabs zapewniają nawigację) |

---

## Etapy implementacji

### Etap 1: Refaktoryzacja nawigacji w app.py
**Status:** [x] ZAKOŃCZONE

- [x] Dodanie zmiennych session_state: `active_section`, `active_subtab`
- [x] Nowa funkcja `render_sidebar_navigation()` (zintegrowana w `render_sidebar()`)
- [x] Nowa funkcja `render_main_content()`
- [x] Funkcje sekcji: `_render_dashboard()`, `_render_capacity_section()`, `_render_performance_section()`, `_render_reports_section()`

### Etap 2: Podział widoków na sub-moduły
**Status:** [x] ZAKOŃCZONE (uproszczone)

**Implementacja:** Zamiast tworzenia nowych katalogów, wykorzystano istniejące funkcje:
- `render_masterdata_import()` - dla Capacity Import
- `render_orders_import()` - dla Performance Import
- `render_validation_view()` - dla Validation w obu sekcjach
- `render_capacity_view()` - dla Capacity Analysis
- `render_performance_view()` - dla Performance Analysis

- [x] Aktualizacja `__init__.py` - eksport `render_masterdata_import`, `render_orders_import`

### Etap 3: Dashboard view
**Status:** [x] ZAKOŃCZONE

- [x] Dashboard zaimplementowany w `_render_dashboard()` w `app.py`
- [x] 4 karty KPI: Masterdata, Orders, Capacity Analysis, Performance Analysis
- [x] Używa `render_kpi_card()` z `layout.py`

### Etap 4: Przyciski nawigacyjne [Next]/[Back]
**Status:** [x] ZAKOŃCZONE

- [x] Dodanie `render_navigation_buttons()` do `layout.py`
- [x] Streamlit tabs zapewniają nawigację między sub-zakładkami

### Etap 5: Przeniesienie parametrów do sekcji
**Status:** [x] ZAKOŃCZONE

- [x] `_render_capacity_settings()` - Client name, Borderline threshold, Imputation, Outlier validation
- [x] `_render_performance_settings()` - Productive hours / shift

### Etap 6: Finalizacja i testy
**Status:** [x] ZAKOŃCZONE

- [x] Import test: `python -c "from src.ui.app import main"`
- [x] Wszystkie 122 testy przechodzą: `python -m pytest tests/ -v`

---

## Pliki zmodyfikowane

| Plik | Akcja | Status |
|------|-------|--------|
| `src/ui/app.py` | Refaktoryzacja nawigacji, Dashboard, sekcje | [x] |
| `src/ui/layout.py` | Dodanie `render_navigation_buttons()` | [x] |
| `src/ui/views/__init__.py` | Eksport `render_masterdata_import`, `render_orders_import` | [x] |

---

## Weryfikacja

```bash
# Uruchomienie aplikacji
streamlit run src/ui/app.py

# Testy
python -m pytest tests/ -v
```

**Wyniki:**
- [x] Import działa bez błędów
- [x] 122/122 testów przechodzi
- [x] Sidebar navigation działa (Dashboard/Capacity/Performance/Reports)
- [x] Sub-zakładki działają w każdej sekcji
- [x] Parametry pokazują się tylko w odpowiedniej sekcji
- [x] Dashboard pokazuje status wszystkich sekcji

---

## Historia zmian

| Data | Etap | Status | Uwagi |
|------|------|--------|-------|
| 2026-01-10 | Plan | Utworzony | Zatwierdzony przez użytkownika |
| 2026-01-10 | Etap 1-6 | ZAKOŃCZONE | Pełna implementacja nawigacji sidebar |
