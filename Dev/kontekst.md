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

**Faza:** MVP ZAIMPLEMENTOWANE
**Ostatnia ukończona faza:** FAZA 8 - UI Streamlit
**Następna faza:** FAZA 9 - Testy integracyjne

**Postęp:** ~95% MVP ukończone

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
| `src/ui/` | ✅ Kompletny | monolityczny app.py |
| `tests/fixtures/` | ✅ Kompletny | generate_fixtures, dane testowe |

---

## Decyzje Projektowe

| Decyzja | Wybór | Powód |
|---------|-------|-------|
| Lokalizacja kodu | Nowy katalog `src/` | Czysta architektura |
| Kolejność implementacji | Backend-first | Logika przed UI |
| Zakres MVP | Pełne MVP z PRD | Wszystkie funkcje |
| Dane testowe | Syntetyczne + rzeczywiste | MD_Kardex_gotowy.xlsx |
| Architektura UI | Monolityczny app.py | Szybszy development |
| Testy jednostkowe | Pominięte | Priorytet na MVP |

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

---

## Jak Kontynuować Po Przerwie

1. Przeczytaj ten plik (`Dev/kontekst.md`)
2. Sprawdź aktualny stan w `Dev/task.md`
3. Przeczytaj szczegóły fazy w `Dev/plan.md`
4. Kontynuuj od następnego nieukończonego zadania

**Uruchomienie aplikacji:**
```bash
streamlit run src/ui/app.py
```

---

## Pozostałe Zadania (FAZA 9)

- [ ] Testy manualne UI
- [ ] Test integracyjny full pipeline
- [ ] Testy wydajnościowe (opcjonalnie)
- [ ] Code review i refactoring (opcjonalnie)

---

## Ostatnia Aktualizacja

**Data:** 2026-01-03
**Przez:** Claude Code
**Zmiany:** Aktualizacja statusu po implementacji FAZ 0-8
