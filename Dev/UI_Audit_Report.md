# UI Consistency Audit Report — DataAnalysis

**Data audytu:** 2026-01-13
**Pliki audytowane:** 8 (theme.py, layout.py, app.py, capacity_view.py, import_view.py, validation_view.py, performance_view.py, reports_view.py)
**Łączna liczba linii:** ~3,500

---

## Podsumowanie wykonawcze

| Kategoria | Problemów | Krytycznych | Wysokich | Średnich | Niskich |
|-----------|-----------|-------------|----------|----------|---------|
| Typografia | 15 | 0 | 3 | 10 | 2 |
| Layout/Spacing | 18 | 0 | 5 | 10 | 3 |
| Kolorystyka | 2 | 0 | 1 | 1 | 0 |
| Komponenty | 12 | 1 | 4 | 5 | 2 |
| **RAZEM** | **47** | **1** | **13** | **26** | **7** |

**Infrastruktura:** Aplikacja posiada dobrze zaprojektowany system tematu (`theme.py` - 678 linii, 13 kolorów + 7 statusów) oraz bibliotekę komponentów (`layout.py` - 494 linii, 16+ funkcji). Problem polega na **niespójnym wykorzystaniu** tych narzędzi w plikach widoków.

---

## 1. Typografia

### Problem T-001: Niespójne nagłówki sekcji (WYSOKI)
**Problem:** Mieszane użycie `st.subheader()`, `st.markdown("**...**")` i `render_section_header()`

**Lokalizacja:**
| Plik | Linie | Aktualnie | Powinno być |
|------|-------|-----------|-------------|
| capacity_view.py | 371, 528, 546, 639 | `st.subheader()` | `render_section_header()` |
| performance_view.py | 200, 228, 392 | `st.subheader()` | `render_section_header()` |
| validation_view.py | 95, 113 | `st.subheader()` | `render_section_header()` |
| import_view.py | 119, 259, 427 | `st.subheader()` | `render_section_header()` |

**Dlaczego niespójne:** `theme.py` definiuje klasę `.section-header` z określonym stylem (1.1rem, border-bottom), ale `st.subheader()` nie używa tego stylu.

**Propozycja:** Zamienić wszystkie `st.subheader()` na `render_section_header()` z odpowiednimi ikonami.

---

### Problem T-002: Etykiety jako bold markdown (ŚREDNI)
**Problem:** Użycie `st.markdown("**tekst**")` zamiast dedykowanego komponentu

**Lokalizacja:**
| Plik | Linie | Tekst |
|------|-------|-------|
| capacity_view.py | 20 | `"**Add new carrier:**"` |
| capacity_view.py | 23 | `"**Internal dimensions (mm):**"` |
| capacity_view.py | 140 | `"**Defined carriers:**"` |
| capacity_view.py | 145-155 | Nagłówki tabeli (`**Active**`, `**Carrier**`, etc.) |
| performance_view.py | 29 | `"**Shift configuration:**"` |
| performance_view.py | 41 | `"**Enter schedule parameters:**"` |
| validation_view.py | 99, 106 | `"**Before/After imputation:**"` |
| app.py | 290 | `"**Outlier validation**"` |
| reports_view.py | 424 | `"**Data coverage after imputation:**"` |

**Propozycja:** Utworzyć funkcję `render_bold_label(text)` w `layout.py` z jednolitym stylem.

---

### Problem T-003: Nagłówki tabel bez stylu (ŚREDNI)
**Problem:** Nagłówki tabel w `capacity_view.py:143-156` używają surowego `st.markdown("**...**")`

**Lokalizacja:** `capacity_view.py:143-156`

**Propozycja:** Utworzyć komponent `render_table_header()` lub użyć CSS dla nagłówków tabel.

---

## 2. Layout i Spacing

### Problem L-001: Dividers jako st.markdown("---") (WYSOKI)
**Problem:** Ręczne tworzenie dividerów zamiast użycia `render_divider()`

**Lokalizacja:**
| Plik | Linie |
|------|-------|
| app.py | 130, 150, 336, 389 |
| capacity_view.py | 236, 249, 621, 626, 631, 636 |
| performance_view.py | 187, 192, 197 |
| validation_view.py | 92 |
| reports_view.py | 123, 128, 133, 423 |

**Łącznie:** 18 wystąpień

**Propozycja:** Zamienić wszystkie `st.markdown("---")` na `render_divider()`.

---

### Problem L-002: Spacery jako st.markdown("") (ŚREDNI)
**Problem:** Użycie pustego markdown zamiast `render_spacer()`

**Lokalizacja:**
| Plik | Linie |
|------|-------|
| capacity_view.py | 397 | `st.markdown("")` |
| capacity_view.py | 601-603 | `st.markdown("")` (x2) |

**Propozycja:** Zamienić na `render_spacer()` z odpowiednią wysokością.

---

### Problem L-003: Niespójne nazewnictwo kolumn (ŚREDNI)
**Problem:** Mieszane style nazewnictwa zmiennych kolumn

**Wzorce:**
- `col1, col2, col3` - używane w: app.py, import_view.py, performance_view.py (częściowo)
- `col_a, col_b, col_c` - używane w: capacity_view.py:670, 714, 734
- `col_filter, col_carrier, col_export` - używane w: capacity_view.py:556
- `btn_col1, btn_col2, btn_col3` - używane w: import_view.py:335, 495

**Propozycja:** Standaryzować na `col1, col2, col3` dla prostych układów.

---

### Problem L-004: Brak standardowych proporcji kolumn (NISKI)
**Problem:** Różne proporcje kolumn dla podobnych układów

**Przykłady:**
- Navigation buttons: `[1, 2, 1]` - OK, używane konsekwentnie
- Filters: `[2, 2, 1]` vs `[4, 1]` - niespójne

**Propozycja:** Udokumentować standardowe wzorce proporcji.

---

## 3. Kolorystyka

### Problem C-001: Inline colors zamiast COLORS dict (WYSOKI)
**Problem:** Użycie Streamlit inline color `:blue[...]` zamiast `COLORS`

**Lokalizacja:** `capacity_view.py:184-187`
```python
if is_predefined:
    st.markdown(":blue[Predef.]")  # ← Hardcoded
else:
    st.markdown(":green[Custom]")  # ← Hardcoded
```

**Propozycja:** Użyć `render_status_button()` lub HTML z `COLORS`.

---

### Problem C-002: Hardcoded colors w components_demo.py (NISKI)
**Problem:** Użycie `"#000"`, `"#fff"` zamiast `COLORS`

**Lokalizacja:** `components_demo.py:289, 304`

**Propozycja:** Zastąpić wartościami z `COLORS` dict.

---

## 4. Komponenty

### Problem K-001: Dual Status System (KRYTYCZNY)
**Problem:** Współistnieją dwa systemy statusów bez jasnej strategii migracji

**Systemy:**
1. **Legacy 4-type** (layout.py:107-133):
   - Typy: `success, warning, error, info`
   - Funkcja: `render_status_badge()`
   - CSS: `.status-badge`

2. **Modern 7-type** (layout.py:137-176):
   - Typy: `pending, in_progress, submitted, in_review, success, failed, expired`
   - Funkcja: `render_status_button()`
   - CSS: `.status-btn`

**Użycie w plikach:**
| Plik | Legacy | Modern |
|------|--------|--------|
| reports_view.py | TAK (import) | TAK (import i użycie) |
| import_view.py | NIE | TAK |
| components_demo.py | TAK | TAK |

**Propozycja:**
1. Dodać komentarz `# DEPRECATED` do legacy funkcji
2. Zmigrować wszystkie użycia do 7-type system
3. Usunąć legacy po pełnej migracji

---

### Problem K-002: Przyciski bez type="primary" (WYSOKI)
**Problem:** Główne przyciski akcji nie mają `type="primary"`

**Lokalizacja:**
| Plik | Linia | Przycisk |
|------|-------|----------|
| validation_view.py | 16 | `st.button("Run validation"...)` |
| capacity_view.py | 292 | `st.button("Run capacity analysis"...)` |
| performance_view.py | 94 | `st.button("Run performance analysis")` |

**Propozycja:** Dodać `type="primary"` do wszystkich głównych akcji.

---

### Problem K-003: Niespójny help text w st.metric() (ŚREDNI)
**Problem:** Niektóre metryki mają help text, inne nie

**Lokalizacja:**
| Plik | Z help | Bez help |
|------|--------|----------|
| validation_view.py | 76-84 (Quality Score) | 86-90 (Records, Valid, Imputed) |
| performance_view.py | - | 204-210 (wszystkie 6 metryk) |
| reports_view.py | - | 427-467 (Dimensions, Weight) |
| capacity_view.py | 672-764 (wszystkie) | - |

**Wzorzec dobry:** `capacity_view.py` - wszystkie metryki mają help text.

**Propozycja:** Dodać help text do wszystkich st.metric() wywołań.

---

### Problem K-004: Niespójne st.dataframe() height (ŚREDNI)
**Problem:** Różne wysokości dataframe w różnych widokach

**Lokalizacja:**
| Plik | Linie | Height |
|------|-------|--------|
| capacity_view.py | 594-598 | `height=400` |
| import_view.py | 309, 402, 478, 552 | auto (brak) |
| components_demo.py | 235 | auto (brak) |

**Propozycja:** Standaryzować na `height=400` dla tabel z więcej niż ~10 wierszy.

---

### Problem K-005: Expanders bez ikon (ŚREDNI)
**Problem:** Niespójne użycie ikon w expanderach

**Lokalizacja:**
| Plik | Z ikoną | Bez ikony |
|------|---------|-----------|
| reports_view.py | 390, 434, 472 (emoji) | - |
| import_view.py | - | 220, 237, 306, 401, 474, 551 |
| capacity_view.py | - | 59, 239, 272, 652, 669, 713, 733 |
| app.py | - | 251, 371 |
| validation_view.py | - | 141 |

**Wzorzec dobry:** `reports_view.py` używa emoji ikon.

**Propozycja:** Dodać ikony do wszystkich expanderów dla spójności.

---

### Problem K-006: Mieszane expanded defaults (NISKI)
**Problem:** Niespójne domyślne stany expanderów

**Lokalizacja:** `capacity_view.py` - niektóre `expanded=True`, inne `expanded=False`, niektóre warunkowe.

**Propozycja:** Udokumentować zasady kiedy expander powinien być domyślnie rozwinięty.

---

## 5. Rekomendacje refaktoryzacji

### Priorytet 1: Quick Wins (5-10 minut każdy)
1. ✅ **ZREALIZOWANE (2026-01-13)** Zamień `st.markdown("---")` na `render_divider()` (19 miejsc - 4 w app.py, 6 w capacity_view.py, 3 w performance_view.py, 1 w validation_view.py, 5 w reports_view.py)
2. ✅ **ZREALIZOWANE (2026-01-13)** Zamień `st.markdown("")` na `render_spacer()` (3 miejsca w capacity_view.py)
3. ✅ **ZREALIZOWANE (2026-01-13)** Dodaj `type="primary"` do 3 przycisków akcji (validation_view.py, capacity_view.py, performance_view.py)
4. ✅ **ZREALIZOWANE (2026-01-13)** Napraw inline colors w capacity_view.py:184-187 → render_status_button()

### Priorytet 2: Standaryzacja komponentów (30-60 minut)
1. ✅ **ZREALIZOWANE (2026-01-13)** Zamień `st.subheader()` na `render_section_header()` z ikonami (12 miejsc: 4 w capacity_view.py, 3 w import_view.py, 3 w performance_view.py, 2 w validation_view.py)
2. ✅ **ZREALIZOWANE (2026-01-13)** Dodaj help text do wszystkich `st.metric()` wywołań (12 metryk: 3 w validation_view.py, 6 w performance_view.py, 3 w reports_view.py)
3. ✅ **ZREALIZOWANE (2026-01-13)** Standaryzuj nazewnictwo kolumn na `col1, col2, col3` (capacity_view.py - 3 miejsca)
4. ✅ **ZREALIZOWANE (2026-01-13)** Dodaj ikony do wszystkich expanderów (14 expanderów: 2 w app.py, 6 w capacity_view.py, 5 w import_view.py, 1 w validation_view.py)

### Priorytet 3: Nowe komponenty (1-2 godziny)
1. ✅ **ZREALIZOWANE (2026-01-14)** Utwórz `render_bold_label(text, icon=None)` w layout.py
2. ✅ **ZREALIZOWANE (2026-01-14)** Utwórz `render_data_table(df, height=400)` wrapper
3. ✅ **ZREALIZOWANE (2026-01-14)** Zamień `st.markdown("**...**")` na `render_bold_label()` w 5 plikach (app.py, capacity_view.py, validation_view.py, performance_view.py, reports_view.py)

### Priorytet 4: System statusów (2-3 godziny)
1. ✅ **ZREALIZOWANE (2026-01-14)** Dodaj `# DEPRECATED - use render_status_button()` do legacy funkcji
2. ✅ **ZREALIZOWANE (2026-01-14)** Usunięto nieużywane legacy imports z reports_view.py
3. ✅ Legacy functions zachowane w layout.py i __init__.py dla wstecznej kompatybilności
4. ✅ components_demo.py używa legacy functions celowo (demonstracja systemu)

---

## 6. Lista zmian do wdrożenia

### app.py
- [x] L130, L150, L336, L389: `st.markdown("---")` → `render_divider()` ✅ DONE
- [x] L251, L371: Dodaj ikony do expanderów ✅ DONE (2026-01-13)
- [x] L290: `st.markdown("**Outlier validation**")` → `render_bold_label("Outlier validation", "⚠️")` ✅ DONE (2026-01-14)

### capacity_view.py
- [x] L20, L23, L140, L145-155: Zamień `st.markdown("**...**")` na `render_bold_label()` ✅ DONE (2026-01-14)
- [x] L184-187: Zamień `:blue[Predef.]`/`:green[Custom]` na `render_status_button()` ✅ DONE (2026-01-13)
- [x] L236, L249, L621, L626, L631, L636: `st.markdown("---")` → `render_divider()` ✅ DONE
- [x] L292: Dodaj `type="primary"` do przycisku ✅ DONE (2026-01-13)
- [x] L371, L528, L546, L639: `st.subheader()` → `render_section_header()` ✅ DONE (2026-01-13)
- [x] L397, L601-603: `st.markdown("")` → `render_spacer()` ✅ DONE (2026-01-13)
- [x] L670, L714, L734: Zmień `col_a, col_b, col_c` na `col1, col2, col3` ✅ DONE (2026-01-13)
- [x] Dodaj ikony do expanderów (6 miejsc) ✅ DONE (2026-01-13)

### import_view.py
- [x] L119, L259, L427: `st.subheader()` → `render_section_header()` ✅ DONE (2026-01-13)
- [x] L220, L237, L306, L401, L474, L551: Dodaj ikony do expanderów ✅ DONE (2026-01-13)

### validation_view.py
- [x] L16: Dodaj `type="primary"` do przycisku "Run validation" ✅ DONE (2026-01-13)
- [x] L86-90: Dodaj help text do metryk ✅ DONE (2026-01-13)
- [x] L92: `st.markdown("---")` → `render_divider()` ✅ DONE
- [x] L95, L113: `st.subheader()` → `render_section_header()` ✅ DONE (2026-01-13)
- [x] L141: Dodaj ikonę do expandera ✅ DONE (2026-01-13)
- [x] L99, L106: Zamień `st.write("**...**")` na `render_bold_label()` ✅ DONE (2026-01-14)

### performance_view.py
- [x] L29, L41: Zamień `st.markdown("**...**")` na `render_bold_label()` ✅ DONE (2026-01-14)
- [x] L94: Dodaj `type="primary"` do przycisku ✅ DONE (2026-01-13)
- [x] L187, L192, L197: `st.markdown("---")` → `render_divider()` ✅ DONE
- [x] L200, L228, L392: `st.subheader()` → `render_section_header()` ✅ DONE (2026-01-13)
- [x] L204-210: Dodaj help text do metryk ✅ DONE (2026-01-13)

### reports_view.py
- [x] L10-17: Usunięto nieużywane legacy imports ✅ DONE (2026-01-14)
- [x] L123, L128, L133, L423, L451: `st.markdown("---")` → `render_divider()` ✅ DONE (5 miejsc)
- [x] L427, L429, L467: Dodaj help text do metryk ✅ DONE (2026-01-13)
- [x] L425, L461: Zamień `st.markdown("**...**")` na `render_bold_label()` ✅ DONE (2026-01-14)

### layout.py (nowe komponenty)
- [x] Dodaj `render_bold_label(text: str, icon: str | None = None)` ✅ DONE (2026-01-14)
- [x] Dodaj `render_data_table(df, height=400)` wrapper ✅ DONE (2026-01-14)
- [x] Dodaj komentarz `# DEPRECATED` do `render_status_badge()` i `render_status_badges_inline()` ✅ DONE (2026-01-14)

---

## 7. Dobre praktyki zidentyfikowane

Następujące wzorce powinny być **zachowane i propagowane**:

1. **reports_view.py** - prawidłowe użycie `render_section_header()` z ikonami
2. **reports_view.py** - expanders z emoji ikonami (390, 434, 472)
3. **capacity_view.py:672-764** - wszystkie `st.metric()` z help text
4. **import_view.py** - prawidłowe użycie `render_status_button()` i `render_spacer()`
5. **layout.py:436-493** - `render_navigation_buttons()` jako wzorzec reużywalnego komponentu

---

## Weryfikacja po wdrożeniu

1. Uruchom aplikację: `streamlit run src/ui/app.py`
2. Sprawdź każdy widok:
   - Dashboard
   - Capacity → Import, Validation, Analysis
   - Performance → Import, Validation, Analysis
   - Reports
3. Zweryfikuj:
   - Dividers mają jednolity styl
   - Sekcje mają ikony
   - Przyciski głównych akcji są wyróżnione
   - Metryki mają tooltips
4. Przetestuj responsywność (resize okna do 768px i 480px)
