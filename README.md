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

## Testy

```bash
python -m pytest tests/ -v
```

## Stack technologiczny

- Python 3.11+
- Polars (transformacje danych)
- DuckDB (agregacje SQL)
- Streamlit (UI)
- Plotly (interaktywne wykresy)
- Pydantic (walidacja typów)

---

## Architektura UI

### Struktura plików

```
src/ui/
├── app.py              # Główna aplikacja, routing zakładek
├── theme.py            # Dark theme, paleta kolorów, CSS
├── layout.py           # Reużywalne komponenty UI
└── views/              # Widoki zakładek
    ├── import_view.py      # Import danych + mapping
    ├── validation_view.py  # Walidacja jakości danych
    ├── capacity_view.py    # Analiza pojemnościowa
    ├── performance_view.py # Analiza wydajnościowa
    └── reports_view.py     # Generowanie raportów
```

### Zakładki aplikacji

| Zakładka | Opis |
|----------|------|
| **Import** | Upload plików, mapping kolumn, preview danych |
| **Validation** | Walidacja jakości, imputacja, wykrywanie problemów |
| **Capacity** | Zarządzanie nośnikami, analiza dopasowania SKU |
| **Performance** | Konfiguracja zmian, analiza wydajnościowa |
| **Reports** | Generowanie raportów, eksport ZIP |

### Dark Theme

Aplikacja używa ciemnego motywu inspirowanego n8n:

| Element | Kolor |
|---------|-------|
| Background | `#121212` |
| Surface | `#1E1E1E` |
| Primary (sukces) | `#4CAF50` |
| Error | `#F44336` |
| Warning | `#FF9800` |
| Info | `#2196F3` |
| Text | `#EAEAEA` |

### Komponenty UI (layout.py)

| Komponent | Opis |
|-----------|------|
| `render_kpi_card()` | Karta KPI z wartością i deltą |
| `render_kpi_section()` | Rząd kart KPI (4 kolumny) |
| `render_section_header()` | Nagłówek sekcji z ikoną |
| `render_status_badge()` | Badge statusu (success/warning/error/info) |
| `render_message_box()` | Stylizowane info/warning/error box |
| `apply_plotly_dark_theme()` | Aplikowanie dark theme do wykresów Plotly |

### Responsywność

CSS zawiera breakpoints:
- **Desktop** (>768px): 4 kolumny KPI
- **Tablet** (768px): 2 kolumny KPI
- **Mobile** (480px): 1 kolumna KPI

### Accessibility

- Kontrast tekst/tło: **12.6:1** (WCAG AAA)
- Wszystkie kolory akcentowe spełniają **WCAG AA**
- Hover effects na interaktywnych elementach
