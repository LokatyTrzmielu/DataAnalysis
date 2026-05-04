# Datavisor

Aplikacja do analizy danych magazynowych — pojemnościowa i wydajnościowa.

## Funkcjonalności

- Import danych Masterdata i Orders (XLSX, CSV, TXT)
- Mapping Wizard z auto-sugestiami kolumn
- Walidacja i Data Quality Scorecard
- Imputacja brakujących wartości (mediana)
- Analiza pojemnościowa (dopasowanie SKU do nośników)
- Analiza wydajnościowa (KPI, peaks, P90/P95)
- Eksport raportów do ZIP/PDF

## Uruchomienie (development)

**Backend (FastAPI):**
```bash
uvicorn api.main:app --reload
```

**Frontend (Vue 3 + Vite):**
```bash
cd frontend && npm run dev
```

## Testy

```bash
python -m pytest tests/ -v
```

## Stack technologiczny

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Frontend:** Vue 3, Vite, TypeScript, Pinia
- **Dane:** Polars, DuckDB, DuckDB persistence
- **Auth:** JWT (python-jose)
- **Raporty:** ReportLab (PDF), openpyxl
