# Plan: Aktualizacja Palety Kolorów i Przycisków Statusu UI

> Data: 2026-01-09

## Cel
Modernizacja UI aplikacji DataAnalysis:
1. Wdrożenie ciepłej, kawowo-brązowej palety kolorów
2. Zastąpienie istniejących `.status-badge` nowymi `.status-btn` z 7 typami statusu i ikonami

---

## 1. Paleta Kolorów

### Historia zmian
- **2026-01-10:** Paleta kawowo-brązowa (coffee-bean, burnt-caramel)
- **2026-02-16:** Podmiana na ciepłą neutralną ze złotym akcentem

### Aktualna paleta (2026-02-16)
| Nazwa | Hex | Rola UI |
|-------|-----|---------|
| dark neutral | `#2d2926` | Sidebar, deepest bg |
| warm brown | `#463f3a` | Główne tło aplikacji |
| elevated | `#544c46` | Karty, inputy |
| light neutral | `#635b54` | Hover, bordery |
| gold | `#c9a227` | Główny akcent |
| dark gold | `#a8861f` | Hover przycisków |
| muted gold | `#6b5a2a` | Subtelne bordery |
| cream white | `#f4f3ee` | Tekst główny |
| light beige | `#bcb8b1` | Tekst drugorzędny |

### Aktualny słownik COLORS w `theme.py`

```python
COLORS = {
    # === TŁA ===
    "background": "#2d2926",       # ciemniejszy wariant - sidebar, deepest bg
    "surface": "#463f3a",          # główne tło aplikacji
    "surface_elevated": "#544c46", # karty, inputy
    "surface_light": "#635b54",    # hover, subtelne wyróżnienia

    # === AKCENTY ===
    "accent": "#c9a227",           # złoty - główny akcent
    "accent_dark": "#a8861f",      # ciemniejsze złoto - hover
    "accent_muted": "#6b5a2a",     # stonowane złoto - subtelne bordery

    # === FUNKCJONALNE ===
    "primary": "#4CAF50",          # zielony sukces (bez zmian)
    "error": "#E57373",            # czerwony błąd (bez zmian)
    "warning": "#c9a227",          # złoty (= accent)
    "info": "#8a817c",             # ciepły szary

    # === TEKST ===
    "text": "#f4f3ee",             # kremowa biel
    "text_secondary": "#bcb8b1",   # jasny beż

    # === BORDERY ===
    "border": "#635b54",           # ciepły szary border
}
```

---

## 2. Nowe Przyciski Statusu (7 typów)

Zastępują stare `.status-badge` (4 typy: success/warning/error/info).

| Status | Kolor | Ikona SVG |
|--------|-------|-----------|
| **pending** | `#FFB74D` żółty | Triangle warning |
| **in_progress** | `#64B5F6` niebieski | Dashed circle (rotating) |
| **submitted** | `#BA68C8` fioletowy | Paper plane (send) |
| **in_review** | `#FF8A65` pomarańczowy | Circular arrows |
| **success** | `#81C784` zielony | Checkmark circle |
| **failed** | `#E57373` czerwony | X circle |
| **expired** | `#90A4AE` szary | Clock |

### Styl CSS
```css
.status-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 500;
    border: 1px solid;
    background-color: rgba(COLOR, 0.15);
    border-color: rgba(COLOR, 0.4);
    color: COLOR;
}
```

---

## 3. Pliki do Modyfikacji

### 3.1 `src/ui/theme.py` (główny plik)
**Linie do zmiany:**
- `3-15`: Słownik COLORS - całkowita wymiana
- `79-106`: CSS `.status-badge` → `.status-btn` (7 typów)
- `128-140`: CSS `.stButton` - nowe kolory przycisków
- `186-189`: Progress bar - `#b7622c`
- `237-245`: Hover effects `.status-btn`
- `280-333`: Message boxes - nowe kolory rgba
- `376-393`: Scrollbar - ciepłe kolory
- `397`: Spinner - `#b7622c`

**Dodać:**
- Słownik `STATUS_COLORS` z 7 typami
- Słownik `STATUS_ICONS` z SVG

### 3.2 `src/ui/layout.py`
**Linie do zmiany:**
- `107-120`: `render_status_badge()` → `render_status_button()` (nowa sygnatura)
- `123-133`: `render_status_badges_inline()` → `render_status_buttons_inline()`
- `168-191`: `get_plotly_layout_defaults()` - nowe kolory
- `365-380`: `get_status_color()` - rozszerzyć o 7 typów

### 3.3 `src/ui/__init__.py`
**Linie 9-10, 25-26:** Zaktualizować eksporty nazw funkcji

### 3.4 `src/ui/views/import_view.py`
**Linie do zmiany:**
- `13`: Import nowej funkcji
- `401`: `render_status_badge("✓ X SKU imported", "success")` → `render_status_button("X SKU imported", "success")`
- `551`: `render_status_badge("✓ X lines imported", "success")` → `render_status_button("X lines imported", "success")`

### 3.5 `src/ui/views/reports_view.py`
**Linie do zmiany:**
- `13-14`: Import nowych funkcji
- `459`: `render_status_badges_inline()` → `render_status_buttons_inline()`

### 3.6 `src/ui/views/components_demo.py`
**Linie do zmiany:**
- `24-25`: Importy
- `131-145`: Sekcja demo - pokazać wszystkie 7 typów statusu

### 3.7 `.streamlit/config.toml`
```toml
[theme]
primaryColor = "#b7622c"
backgroundColor = "#20100e"
secondaryBackgroundColor = "#323232"
textColor = "#F5F0E8"
```

---

## 4. Mapowanie Starych Statusów na Nowe

| Stary status | Nowy status | Użycie |
|--------------|-------------|--------|
| `success` | `success` | Import zakończony, walidacja OK |
| `warning` | `pending` lub `in_review` | Oczekujące, do przeglądu |
| `error` | `failed` | Błędy, niepowodzenia |
| `info` | `in_progress` lub `submitted` | Informacyjne, w trakcie |

---

## 5. Ikony SVG (inline)

```python
STATUS_ICONS = {
    "pending": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>',
    "in_progress": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="4 2"><circle cx="12" cy="12" r="10"/></svg>',
    "submitted": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>',
    "in_review": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>',
    "success": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>',
    "failed": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
    "expired": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
}
```

---

## 6. Kolejność Implementacji

1. **theme.py** - COLORS + STATUS_COLORS + STATUS_ICONS + CSS
2. **config.toml** - Streamlit theme
3. **layout.py** - Nowe funkcje `render_status_button()`
4. **__init__.py** - Eksporty
5. **import_view.py** - Użycie nowych statusów
6. **reports_view.py** - Użycie nowych statusów
7. **components_demo.py** - Demo 7 typów
8. **Testy** - `pytest tests/ -v`

---

## 7. Weryfikacja

```bash
# Uruchomienie aplikacji
streamlit run src/ui/app.py

# Testy automatyczne
python -m pytest tests/ -v
```

**Checklist:**
- [x] Wszystkie zakładki wyświetlają się poprawnie
- [x] Kontrast tekstu czytelny
- [x] Przyciski statusu pokazują ikony
- [x] Wykresy Plotly mają ciepłe kolory
- [x] Hover effects działają
- [x] 122 testy przechodzą

---

## 8. Status Implementacji

**Data zakończenia:** 2026-01-10

**Zmiany wykonane:**
1. `theme.py` - Nowa paleta COLORS, STATUS_COLORS, STATUS_ICONS + CSS dla .status-btn
2. `config.toml` - Zaktualizowane kolory Streamlit
3. `layout.py` - Nowe funkcje render_status_button(), render_status_buttons_inline(), zaktualizowane get_status_color()
4. `__init__.py` - Eksporty nowych funkcji i słowników
5. `import_view.py` - Użycie render_status_button() dla importu
6. `reports_view.py` - Użycie render_status_buttons_inline() dla capacity preview
7. `components_demo.py` - Demo wszystkich 7 typów statusu + paleta kolorów
8. `theme.py` - Dodane obramowanie espresso (`#5e3123`) dla aktywnej zakładki w sidebarze (2026-01-10)
