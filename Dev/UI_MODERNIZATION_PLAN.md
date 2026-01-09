# Plan modernizacji UI aplikacji Streamlit - DataAnalysis

## Podsumowanie
Kompletna przebudowa interfejsu aplikacji z jasnego motywu na ciemny (dark theme) inspirowany dashboardem n8n, z nową strukturą kodu i interaktywnymi wykresami Plotly.

## Docelowa struktura

### Zakładki (4)
```
[ Import ] [ Analiza pojemnościowa ] [ Analiza wydajnościowa ] [ Raporty ]
```

### Sidebar
- Logo/tytuł aplikacji
- Nazwa klienta
- Parametry analizy (productive hours, borderline threshold)
- Imputation settings
- Outlier validation settings
- Status importu (badges)

### Każda zakładka analityczna
- **Sekcja KPI** (góra) - karty z metrykami
- **Sekcja wykresów** (środek) - Plotly interaktywne
- **Sekcja tabel/logów** (dół) - dataframe + eksport

---

## Etap 1: Theme i struktura plików

**Status:** [x] Zrealizowany

### Cel
Utworzenie fundamentu: dark theme + struktura katalogów + moduł stylów.

### Pliki do utworzenia/modyfikacji

**`.streamlit/config.toml`** - aktualizacja:
```toml
[theme]
primaryColor = "#4CAF50"           # Zielony akcent
backgroundColor = "#121212"        # Główne tło
secondaryBackgroundColor = "#1E1E1E"  # Tło paneli
textColor = "#EAEAEA"              # Jasny tekst
font = "sans serif"
```

**`src/ui/theme.py`** - kolory i style CSS:
```python
# Paleta kolorów
COLORS = {
    "background": "#121212",
    "surface": "#1E1E1E",
    "surface_light": "#2A2A2A",
    "primary": "#4CAF50",      # Zielony - sukces
    "error": "#F44336",        # Czerwony - błędy
    "warning": "#FF9800",      # Pomarańczowy - Kardex/gabaryty
    "text": "#EAEAEA",
    "text_secondary": "#B0B0B0",
    "border": "#333333",
}

# Custom CSS dla komponentów
def get_custom_css() -> str: ...
```

**`src/ui/layout.py`** - komponenty layoutu:
```python
def render_kpi_card(title, value, delta=None, color="primary"): ...
def render_kpi_section(metrics: list[dict]): ...
def render_section_header(title, icon=None): ...
def render_card_container(content_func): ...
```

### Struktura katalogów
```
src/ui/
├── app.py              # Główny routing (do refaktoryzacji)
├── theme.py            # NOWY - kolory, CSS
├── layout.py           # NOWY - komponenty layoutu
├── components/         # (istniejący, pusty)
└── views/              # NOWY katalog
    ├── __init__.py
    ├── import_view.py
    ├── capacity_view.py
    ├── performance_view.py
    └── reports_view.py
```

### Weryfikacja
- [x] Uruchomić aplikację i sprawdzić czy dark theme się ładuje
- [x] Sprawdzić czy kolory są zgodne z wytycznymi

---

## Etap 2: Komponenty UI (layout.py)

**Status:** [x] Zrealizowany

### Cel
Zbudowanie reużywalnych komponentów UI w stylu n8n.

### Komponenty do zaimplementowania

**KPI Cards:**
```python
def render_kpi_card(
    title: str,
    value: str | int | float,
    delta: str | None = None,
    delta_color: str = "primary",
    icon: str | None = None,
    help_text: str | None = None
) -> None:
    """Renderuje kartę KPI z wartością i opcjonalną deltą."""
```

**Section containers:**
```python
def render_section(
    title: str,
    icon: str | None = None,
    expanded: bool = True
) -> contextmanager:
    """Context manager dla sekcji z nagłówkiem."""
```

**Status badges:**
```python
def render_status_badge(
    text: str,
    status: Literal["success", "warning", "error", "info"]
) -> None:
    """Renderuje badge statusu z odpowiednim kolorem."""
```

**Chart container:**
```python
def render_chart_container(
    title: str,
    chart_func: Callable,
    **chart_kwargs
) -> None:
    """Wrapper dla wykresów Plotly z nagłówkiem."""
```

### CSS do dodania w theme.py
- Styl kart KPI (tło #1E1E1E, border-radius 8px, box-shadow)
- Styl nagłówków sekcji
- Styl tabel (ciemne tło, jasny tekst)
- Hover effects

### Weryfikacja
- [x] Utworzyć testową stronę z przykładowymi komponentami
- [x] Sprawdzić responsywność (4 kolumny → 2 kolumny)

---

## Etap 3: Refaktoryzacja app.py

**Status:** [x] Zrealizowany

### Cel
Rozbicie monolitu 1838 linii na moduły.

### Pliki do wyekstrahowania

**`src/ui/views/import_view.py`:**
- `render_import_tab()` → `render_import_view()`
- `render_masterdata_import()`
- `render_orders_import()`
- `render_mapping_ui()`
- `render_mapping_status()`
- Funkcje pomocnicze mapowania

**`src/ui/views/capacity_view.py`:**
- `render_analysis_tab()` (część pojemnościowa) → `render_capacity_view()`
- `render_carrier_form()`
- `render_carriers_table()`
- NOWE: sekcja KPI pojemnościowych
- NOWE: wykresy Plotly (histogram gabarytów, dopasowanie do nośników)

**`src/ui/views/performance_view.py`:**
- `render_analysis_tab()` (część wydajnościowa) → `render_performance_view()`
- Shift configuration
- NOWE: sekcja KPI wydajnościowych
- NOWE: wykresy Plotly (linie/h, heatmapa godzinowa)

**`src/ui/views/reports_view.py`:**
- `render_reports_tab()` → `render_reports_view()`
- `generate_individual_report()`

**`src/ui/app.py`** (nowy, uproszczony):
```python
def main():
    init_session_state()
    apply_custom_css()  # z theme.py
    render_sidebar()
    render_tabs()  # 4 zakładki

def render_tabs():
    tabs = st.tabs(["📁 Import", "📊 Pojemnościowa", "⚡ Wydajnościowa", "📄 Raporty"])
    with tabs[0]: render_import_view()
    with tabs[1]: render_capacity_view()
    with tabs[2]: render_performance_view()
    with tabs[3]: render_reports_view()
```

### Weryfikacja
- [x] Aplikacja działa identycznie jak przed refaktoryzacją
- [x] Testy przechodzą
- [x] Każdy view jest importowalny osobno

### Dodatkowe zmiany
- Utworzono `validation_view.py` - wydzielona zakładka walidacji
- Nowa struktura 5 zakładek: Import | Validation | Capacity | Performance | Reports
- `app.py` zredukowane z 1838 do ~280 linii

---

## Etap 4: Zakładka Import (restyling)

**Status:** [x] Zrealizowany

### Cel
Dostosowanie zakładki Import do nowego stylu.

### Zmiany
1. **Header sekcji** - użycie `render_section_header("Masterdata", "📦")`
2. **Status mapping** - nowe badge'y (`render_status_badge`)
3. **Progress bar** - stylizacja na zielono
4. **Expanders** - ciemne tło (#1E1E1E)
5. **Buttons** - primary button w zielonym kolorze
6. **Data preview** - ciemna tabela

### Kolorystyka statusów
- ✅ Mapped → zielony badge
- ⚠️ Missing → czerwony badge
- ℹ️ Info → szary badge

### Weryfikacja
- [x] Import Masterdata działa
- [x] Import Orders działa
- [x] Mapping UI jest czytelny w dark mode

### Szczegóły implementacji
- `_get_field_status_html()` - zaktualizowane do dark theme (rgba backgrounds)
- `render_section_header()` - zastąpiło `st.subheader()` w całym module
- `render_status_badge()` - używane dla statusu ukończonego importu
- `render_error_box()` - dla błędów duplikacji kolumn
- Mapping summary - stylizowane z kolorami auto/manual
- Główny header - stylowany z ikoną 📁

---

## Etap 5: Zakładka Analiza pojemnościowa

**Status:** [x] Zrealizowany

### Cel
Nowy widok z KPI, wykresami i tabelą.

### Sekcja KPI (góra)
4 karty w rzędzie:
1. **Liczba SKU** - total SKU w analizie
2. **% dopasowania** - średni % fit do nośników
3. **Średnie gabaryty** - średnie L×W×H w mm
4. **Średnia waga** - średnia waga w kg

### Sekcja wykresów (środek)
Layout: 2 kolumny

**Wykres 1: Histogram gabarytów**
- Plotly histogram
- 3 serie: Length, Width, Height
- Bins: automatyczne lub 20
- Kolory: pomarańczowy gradient

**Wykres 2: Dopasowanie do nośników**
- Plotly bar chart (poziomy lub pionowy)
- Dla każdego nośnika: FIT / BORDERLINE / NOT_FIT
- Kolory: zielony / pomarańczowy / czerwony

**Wykres 3: Rozkład wag**
- Plotly histogram
- Kolor: pomarańczowy

### Sekcja tabeli (dół)
- Tabela wynikowa z kolumnami: SKU, L, W, H, Weight, Carrier, Status
- Filtrowanie po statusie (FIT/BORDERLINE/NOT_FIT)
- Eksport CSV

### Elementy do zachowania
- Carrier management (tabela nośników, formularz dodawania)
- Exclusion settings (outliers, borderline)
- Analysis mode (Independent/Prioritized)

### Weryfikacja
- [x] KPI wyświetlają poprawne wartości
- [x] Wykresy są interaktywne (hover, zoom)
- [x] Eksport działa

### Szczegóły implementacji
- `_render_capacity_kpi()` - sekcja z 4 kartami KPI używając `render_kpi_section()`
- `_render_dimensions_histogram()` - histogram Plotly dla L/W/H z overlay
- `_render_carrier_fit_chart()` - stacked bar chart dla FIT/BORDERLINE/NOT_FIT per carrier
- `_render_weight_histogram()` - histogram wag z Plotly Express
- `_render_capacity_charts()` - kontener dla wszystkich wykresów (2 kolumny + pełna szerokość)
- `_render_capacity_table()` - tabela z filtrowaniem po statusie i carrier, eksport CSV
- Dodano `plotly>=5.18.0` do zależności w `pyproject.toml`
- Wszystkie wykresy używają `apply_plotly_dark_theme()` dla spójności z dark mode

---

## Etap 6: Zakładka Analiza wydajnościowa

**Status:** [x] Zrealizowany

### Cel
Nowy widok z KPI wydajnościowymi i wykresami czasowymi.

### Sekcja KPI (góra)
4 karty w rzędzie:
1. **Linie/h (avg)** - średnia liczba linii na godzinę
2. **Peak hour** - szczytowa godzina
3. **Liczba zamówień** - total orders
4. **Śr. pozycji/zamówienie** - average lines per order

### Sekcja wykresów (środek)

**Wykres 1: Linie/h w czasie**
- Plotly line chart
- Oś X: data/godzina
- Oś Y: liczba linii
- Kolor: zielony

**Wykres 2: Heatmapa godzinowa**
- Plotly heatmap
- Oś X: godzina (0-23)
- Oś Y: dzień tygodnia
- Kolor: skala zielona

**Wykres 3: Struktura zamówień**
- Plotly histogram lub pie chart
- Rozkład liczby pozycji na zamówienie

### Sekcja konfiguracji
- Shift configuration (zachować obecną logikę)
- Productive hours slider

### Weryfikacja
- [x] KPI wydajnościowe są poprawne
- [x] Wykresy czasowe działają
- [x] Heatmapa jest czytelna

### Szczegóły implementacji
- `_render_performance_kpi()` - sekcja z 4 kartami KPI (Avg Lines/h, Peak Hour, Total Orders, Avg Lines/Order)
- `_render_daily_lines_chart()` - line chart Plotly z 2 osiami Y (lines i orders)
- `_render_hourly_heatmap()` - heatmapa aktywności (dzień tygodnia × godzina)
- `_render_order_structure_chart()` - histogram lines per order
- `_render_performance_charts()` - kontener dla wykresów (2 kolumny + pełna szerokość)
- Zachowano shift configuration (Default/Custom/YAML/None)
- Wszystkie wykresy używają `apply_plotly_dark_theme()`

---

## Etap 7: Zakładka Raporty

**Status:** [ ] Do zrobienia

### Cel
Uporządkowanie sekcji raportów w nowym stylu.

### Layout
**Lista raportów** - karty lub accordion:
- Każdy raport: nazwa, opis, przycisk Download
- Grupowanie: Summary, Data Quality, Capacity, Performance

**Bulk download:**
- Przycisk "Generuj wszystkie (ZIP)"
- Progress bar podczas generowania

**Preview sekcja:**
- Podgląd danych (expanders jak obecnie)
- Stylizacja na ciemnym tle

### Weryfikacja
- [ ] Wszystkie raporty się generują
- [ ] ZIP działa
- [ ] Preview jest czytelny

---

## Etap 8: Finalizacja i testy

**Status:** [ ] Do zrobienia

### Cel
Dopracowanie detali, testy, dokumentacja.

### Zadania
1. **Responsywność** - test na różnych szerokościach
2. **Accessibility** - kontrast kolorów
3. **Performance** - czas ładowania wykresów
4. **Edge cases** - puste dane, błędy
5. **Dokumentacja** - aktualizacja README

### Testy manualne
- [ ] Import Masterdata
- [ ] Import Orders
- [ ] Mapping UI
- [ ] Validation
- [ ] Capacity analysis (Independent)
- [ ] Capacity analysis (Prioritized)
- [ ] Performance analysis
- [ ] All reports generation
- [ ] ZIP download

---

## Pliki krytyczne do modyfikacji

| Plik | Akcja | Etap |
|------|-------|------|
| `.streamlit/config.toml` | Modyfikacja | 1 |
| `src/ui/theme.py` | Nowy | 1 |
| `src/ui/layout.py` | Nowy | 2 |
| `src/ui/views/__init__.py` | Nowy | 3 |
| `src/ui/views/import_view.py` | Nowy | 3, 4 |
| `src/ui/views/capacity_view.py` | Nowy | 3, 5 |
| `src/ui/views/performance_view.py` | Nowy | 3, 6 |
| `src/ui/views/reports_view.py` | Nowy | 3, 7 |
| `src/ui/app.py` | Refaktoryzacja | 3 |
| `pyproject.toml` | Dodanie plotly | 5 |

---

## Zależności do dodania

```toml
# pyproject.toml
dependencies = [
    # ... existing
    "plotly>=5.18.0",
]
```

---

## Paleta kolorów (referencja)

| Nazwa | Hex | Użycie |
|-------|-----|--------|
| Background | #121212 | Główne tło |
| Surface | #1E1E1E | Tło kart/paneli |
| Surface Light | #2A2A2A | Hover, secondary |
| Primary (Green) | #4CAF50 | Sukces, pozytywne KPI |
| Error (Red) | #F44336 | Błędy, alerty |
| Warning (Orange) | #FF9800 | Kardex, gabaryty |
| Text | #EAEAEA | Główny tekst |
| Text Secondary | #B0B0B0 | Opisy, podpisy |
| Border | #333333 | Obramowania |

---

## Historia zmian

| Data | Etap | Status | Uwagi |
|------|------|--------|-------|
| 2026-01-08 | Plan | Utworzony | Zatwierdzony przez użytkownika |
| 2026-01-08 | Etap 1 | Zrealizowany | Dark theme + struktura plików |
| 2026-01-08 | Etap 2 | Zrealizowany | Komponenty UI, CSS responsywny, strona demo |
| 2026-01-08 | Etap 3 | Zrealizowany | Refaktoryzacja app.py, 5 modułów widoków, 5 zakładek |
| 2026-01-08 | Etap 4 | Zrealizowany | Import view restyling - dark theme statusy, section headers, badges |
| 2026-01-09 | Etap 5 | Zrealizowany | Capacity view - KPI cards, 3 wykresy Plotly, tabela z filtrowaniem i eksportem CSV |
| 2026-01-09 | Etap 6 | Zrealizowany | Performance view - KPI cards, daily line chart, hourly heatmap, order structure histogram |
