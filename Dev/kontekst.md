# DataAnalysis - Kontekst Projektu

> Plik służy do zachowania kontekstu projektu przy przerwaniu sesji.

---

## Informacje Podstawowe

| Parametr | Wartość |
|----------|---------|
| Nazwa projektu | DataAnalysis |
| Katalog roboczy | `D:\VS\DataAnalysis` |
| Data rozpoczęcia | 2026-01-03 |
| Status | **MVP KOMPLETNE** |
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
└── ui/         # Streamlit app.py (monolityczny)

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

## Ostatnia Aktualizacja

**Data:** 2026-01-07
**Status:** MVP kompletne, dokumentacja uproszczona
