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
| `src/ingest/` | readers, mapping, units, sku_normalize, pipeline | Import XLSX/CSV, Mapping Wizard |
| `src/quality/` | validators, dq_metrics, dq_lists, impute, pipeline | Walidacja, DQ scorecard, imputacja |
| `src/model/` | masterdata, orders | Przetwarzanie danych |
| `src/analytics/` | duckdb_runner, capacity, shifts, performance | Analiza pojemnościowa i wydajnościowa |
| `src/reporting/` | csv_writer, main_report, dq_reports, readme, manifest, zip | Raporty CSV, ZIP |
| `src/ui/` | app.py | Streamlit (monolityczny) |

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
