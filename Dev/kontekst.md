# DataAnalysis - Kontekst Projektu

> Plik służy do zachowania kontekstu projektu przy przerwaniu sesji.

---

## Informacje Podstawowe

| Parametr | Wartość |
|----------|---------|
| Nazwa projektu | DataAnalysis |
| Katalog roboczy | `D:\VS\DataAnalysis` |
| Data rozpoczęcia | 2026-01-03 |
| Status | **MVP KOMPLETNE** - Modernizacja UI w toku |
| Testy | 122 (wszystkie przechodzą) |

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
    ├── app.py      # Główna aplikacja (zrefaktoryzowana, ~280 linii)
    ├── theme.py    # Dark theme, paleta kolorów, CSS
    ├── layout.py   # Komponenty UI (KPI cards, badges, sekcje)
    └── views/      # Widoki zakładek
        ├── import_view.py      # Import danych z mapowaniem
        ├── validation_view.py  # Walidacja i jakość danych
        ├── capacity_view.py    # Analiza pojemnościowa
        ├── performance_view.py # Analiza wydajnościowa
        ├── reports_view.py     # Raporty i eksport
        └── components_demo.py  # Demo komponentów UI

tests/          # 122 testy jednostkowe + integracyjne
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

## Modernizacja UI (w toku)

**Plan:** `Dev/UI_MODERNIZATION_PLAN.md`

| Etap | Nazwa | Status |
|------|-------|--------|
| 1 | Theme i struktura plików | ✅ |
| 2 | Komponenty UI (layout.py) | ✅ |
| 3 | Refaktoryzacja app.py | ✅ |
| 4-7 | Widoki zakładek (restyling) | ⏳ |
| 8 | Finalizacja i testy | ⏳ |

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

---

## Ostatnia Aktualizacja

**Data:** 2026-01-08
**Status:** MVP kompletne, modernizacja UI - Etap 3 ukończony
