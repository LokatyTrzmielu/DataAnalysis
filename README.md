# DataAnalysis

Aplikacja do analizy danych magazynowych - pojemnościowa i wydajnościowa.

## Funkcjonalności

- Import danych Masterdata i Orders (XLSX, CSV, TXT)
- Mapping Wizard z auto-sugestiami kolumn
- Walidacja i Data Quality Scorecard
- Imputacja brakujących wartości (mediana)
- Analiza pojemnościowa (dopasowanie SKU do nośników)
- Analiza wydajnościowa (KPI, peaks, P90/P95)
- Eksport raportów do ZIP

## Uruchomienie

```bash
streamlit run src/ui/app.py
```

## Stack technologiczny

- Python 3.11+
- Polars (transformacje danych)
- DuckDB (agregacje SQL)
- Streamlit (UI)
- Pydantic (walidacja typów)
