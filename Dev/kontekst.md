# DataAnalysis - Kontekst Projektu

> Ten plik służy do zachowania kontekstu projektu przy przerwaniu sesji lub kompaktowaniu kontekstu.

---

## Informacje Podstawowe

**Nazwa projektu:** DataAnalysis
**Katalog roboczy:** `D:\VS\DataAnalysis`
**Data rozpoczęcia:** 2026-01-03

---

## Cel Projektu

Aplikacja do analizy danych operacyjnych i masterdata w kontekście projektów automatyzacji magazynowej:
- Analiza pojemnościowa SKU (gabaryty, waga, dopasowanie do nośników Kardex)
- Analiza wydajnościowa (linie/h, piki, struktura zamówień)
- Generowanie raportów CSV + ZIP

---

## Stack Technologiczny

| Technologia | Zastosowanie |
|-------------|--------------|
| Python 3.11+ | Język programowania |
| Polars | Transformacje danych (wydajność) |
| DuckDB | Agregacje SQL |
| Streamlit | UI lokalne |
| Parquet | Format roboczy |
| Pydantic | Typy i walidacja |

---

## Struktura Projektu

```
D:\VS\DataAnalysis\
├── Dev/                    # Pliki deweloperskie (plan, task, kontekst)
├── DataAnalysis_docs/      # Dokumentacja PRD i referencje
├── src/                    # Kod źródłowy aplikacji
│   ├── core/               # Konfiguracja, typy, formatowanie
│   ├── ingest/             # Import danych, Mapping Wizard
│   ├── quality/            # Walidacja, DQ, imputacja
│   ├── model/              # Przetwarzanie Masterdata/Orders
│   ├── analytics/          # DuckDB, capacity, performance
│   ├── reporting/          # Raporty CSV, ZIP
│   └── ui/                 # Streamlit
├── tests/                  # Testy + fixtures
├── runs/                   # Wyniki analiz per klient
└── pyproject.toml
```

---

## Kluczowe Dokumenty Referencyjne

1. **`DataAnalysis_docs/DataAnalysis_PRD.md`** - główne wymagania funkcjonalne
2. **`DataAnalysis_docs/customers_shifts.yml`** - model harmonogramu zmian
3. **`DataAnalysis_docs/Format danych.txt`** - formatowanie liczb w CSV
4. **`DataAnalysis_docs/Profil projektu.txt`** - konfiguracja DQ i imputacji
5. **`Dev/plan.md`** - szczegółowy plan implementacji
6. **`Dev/task.md`** - lista zadań z checkboxami

---

## Aktualny Stan Projektu

**Faza:** MVP KOMPLETNE
**Ostatnia ukończona faza:** FAZA 9 - Testy integracyjne
**Status:** Wszystkie fazy zakończone

**Postęp:** 100% MVP ukończone

---

## Zaimplementowane Moduły

| Moduł | Status | Uwagi |
|-------|--------|-------|
| `src/core/` | ✅ Kompletny | config, formatting, paths, types |
| `src/ingest/` | ✅ Kompletny | readers, mapping, units, pipeline |
| `src/quality/` | ✅ Kompletny | validators, metrics, lists, impute |
| `src/model/` | ✅ Kompletny | masterdata, orders |
| `src/analytics/` | ✅ Kompletny | capacity, shifts, performance, duckdb |
| `src/reporting/` | ✅ Kompletny | csv_writer, reports, manifest, zip |
| `src/ui/` | ✅ Kompletny | monolityczny app.py z pełnym UI |
| `tests/fixtures/` | ✅ Kompletny | generate_fixtures, dane testowe (clean + dirty) |
| `tests/` | ✅ Kompletny | 119 testów jednostkowych (ingest, quality, model, analytics, reporting) |

---

## Decyzje Projektowe

| Decyzja | Wybór | Powód |
|---------|-------|-------|
| Lokalizacja kodu | Nowy katalog `src/` | Czysta architektura |
| Kolejność implementacji | Backend-first | Logika przed UI |
| Zakres MVP | Pełne MVP z PRD | Wszystkie funkcje |
| Dane testowe | Syntetyczne + rzeczywiste | MD_Kardex_gotowy.xlsx |
| Architektura UI | Monolityczny app.py | Szybszy development |
| Testy jednostkowe | Zaimplementowane | 119 testów dla wszystkich modułów |

---

## Kluczowe Koncepty Biznesowe

### Analiza Pojemnościowa
- **Fit check**: dopasowanie SKU do nośnika (6 orientacji)
- **Constraints**: ANY, UPRIGHT_ONLY, FLAT_ONLY
- **Borderline threshold**: 2mm marginesu
- **N per carrier**: ile sztuk mieści się na nośniku
- **Utilization**: VLM 0.70-0.80, MiB 0.60-0.75

### Analiza Wydajnościowa
- **KPI**: lines/h, orders/h, units/h, unique SKU/h
- **Harmonogram zmian**: base + overlay (z YAML)
- **Productive hours**: efektywny czas pracy (np. 7h z 8h)
- **Peak analysis**: max, P90, P95

### Data Quality
- **0 = missing** (dla wymiarów, wagi, ilości)
- **Imputacja**: mediana globalna
- **Flagi**: RAW vs ESTIMATED

---

## Notatki z Sesji

### Sesja 2026-01-03 (inicjalna)
- Przeanalizowano PRD i dokumentację
- Utworzono plan implementacji (9 faz)
- Użytkownik wybrał: backend-first, nowy katalog src/, pełne MVP
- Utworzono folder Dev z plikami: plan.md, task.md, kontekst.md

### Sesja 2026-01-03 (implementacja)
- Zaimplementowano FAZY 0-8 (cały backend + UI)
- Wszystkie moduły core, ingest, quality, model, analytics, reporting
- UI Streamlit jako monolityczny app.py (nie oddzielne pliki)
- Dodano dane testowe: syntetyczne CSV + rzeczywisty plik MD_Kardex_gotowy.xlsx
- Pominięto testy jednostkowe (priorytet MVP)
- Zaimplementowano Mapping Wizard z auto-sugestiami i manualnym wyborem kolumn
- Aplikacja gotowa do testów manualnych

### Sesja 2026-01-03 (testy integracyjne)
- Utworzono plik `tests/test_integration.py` z 4 testami:
  1. Test full pipeline Masterdata only - PASSED
  2. Test full pipeline Masterdata + Orders - PASSED
  3. Test struktury katalogów runs/ - PASSED
  4. Test spójności danych między raportami - PASSED
- Naprawiono błąd w `src/analytics/capacity.py` (schema typów dla Polars DataFrame)
- Wszystkie testy przechodzą pomyślnie (4/4)
- Code review: kod jest poprawny i czytelny
- MVP KOMPLETNE - projekt gotowy do użycia

### Sesja 2026-01-03 (testy jednostkowe + rozszerzenia UI)
- Ukończono wszystkie pominięte zadania z task.md:
  1. **Generator orders_dirty.csv** - dodano funkcję z typowymi błędami jakościowymi
  2. **Testy jednostkowe** - 119 testów dla wszystkich modułów:
     - `tests/test_ingest.py` - 41 testów (FileReader, MappingWizard, UnitDetector, SKUNormalizer)
     - `tests/test_quality.py` - 27 testów (MasterdataValidator, DQMetrics, DQLists, Imputer)
     - `tests/test_model.py` - 13 testów (MasterdataProcessor, OrdersProcessor)
     - `tests/test_analytics.py` - 21 testów (CapacityAnalyzer, ShiftSchedule, PerformanceAnalyzer)
     - `tests/test_reporting.py` - 13 testów (CSVWriter, DQReportGenerator)
  3. **Rozszerzenia UI** (`src/ui/app.py`):
     - Borderline threshold input (slider 0.5-10mm)
     - Wybór nośników (multiselect: TRAY_S, TRAY_M, TRAY_L, TRAY_XL)
     - Konfiguracja zmian (Domyślny/Z pliku YAML/Brak)
     - Lista raportów z opisami
     - Download individual CSV (przyciski pobierania dla każdego raportu)
- Wszystkie 119 testów przechodzą pomyślnie
- Zaktualizowano task.md - wszystkie zadania ukończone

### Sesja 2026-01-04 (ulepszenia UX - ręczne wprowadzanie danych)
- **Analiza pojemnościowa - uproszczony formularz nośnika:**
  - Wymiary (szerokość, długość, wysokość) na pierwszym planie
  - Wartości w mm jako liczby całkowite (bez przecinka)
  - Waga w kg widoczna od razu
  - ID i nazwa nośnika są opcjonalne (auto-generowane jeśli puste)
  - Auto-generacja ID: `CARRIER_WxLxH` (np. `CARRIER_400x600x200`)
  - Auto-generacja nazwy: `Nosnik WxLxHmm` (np. `Nosnik 400x600x200mm`)
- **Analiza wydajnościowa - własny harmonogram zmian:**
  - Nowa opcja "Własny harmonogram" w dropdown
  - Ręczne wprowadzenie: dni w tygodniu (1-7), godziny dziennie (1-24), zmiany dziennie (1-4)
  - Automatyczne wyliczenie godzin na zmianę
  - Podsumowanie: "Godzin na zmiane: Xh | Lacznie zmian/tydzien: Y"
  - Harmonogram generowany automatycznie (start od 6:00, przypisanie do dni Pn-Nd)

---

## Jak Kontynuować Po Przerwie

1. Przeczytaj ten plik (`Dev/kontekst.md`)
2. Sprawdź aktualny stan w `Dev/task.md`
3. Przeczytaj szczegóły fazy w `Dev/plan.md`

**Uruchomienie aplikacji:**
```bash
streamlit run src/ui/app.py
```

**Uruchomienie testów:**
```bash
python -m pytest tests/ -v
```

**Szybkie uruchomienie testów (bez verbose):**
```bash
python -m pytest tests/
```

---

## Projekt Zakończony

Wszystkie zadania z FAZY 0-9 zostały ukończone. MVP jest kompletne i gotowe do użycia.
Dodatkowo zaimplementowano wszystkie wcześniej pominięte zadania (testy jednostkowe, rozszerzenia UI).

**Możliwe przyszłe rozszerzenia:**
- Testy wydajnościowe z dużymi zbiorami danych (200k SKU, 2M orders)
- ~~Dodanie własnych nośników przez użytkownika (custom carriers)~~ ✅ ZAIMPLEMENTOWANE
- ~~Własny harmonogram zmian~~ ✅ ZAIMPLEMENTOWANE
- Eksport wyników do Excel z formatowaniem
- Dashboard z wykresami (Plotly)

---

## Ostatnia Aktualizacja

**Data:** 2026-01-04
**Przez:** Claude Code
**Zmiany:** Ulepszenia UX - uproszczony formularz nośnika (wymiary na pierwszym planie, opcjonalne ID/nazwa), własny harmonogram zmian (ręczne wprowadzenie dni/godzin/zmian)
