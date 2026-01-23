# DataAnalysis - Lista Zadań

## Status Projektu

**MVP KOMPLETNE** | 122 testy | Wszystkie fazy ukończone

---

## Fazy Implementacji

| Faza | Nazwa | Zakres | Status |
|------|-------|--------|--------|
| 0 | Przygotowanie | config, formatting, paths, types | ✅ |
| 1 | Dane testowe | fixtures, CSV/XLSX generatory | ✅ |
| 2 | Import (Ingest) | readers, mapping, units, sku_normalize | ✅ |
| 3 | Jakość danych | validators, dq_metrics, dq_lists, impute | ✅ |
| 4 | Model danych | masterdata, orders processing | ✅ |
| 5 | Analiza pojemnościowa | capacity (6 orientacji, borderline) | ✅ |
| 6 | Analiza wydajnościowa | shifts, performance, KPI | ✅ |
| 7 | Raportowanie | csv_writer, reports, manifest, zip | ✅ |
| 8 | UI Streamlit | app.py (monolityczny) | ✅ |
| 9 | Testy | 122 testy jednostkowe + integracyjne | ✅ |
| 10 | Poprawki UI | outliers, borderline, tooltips | ✅ |
| 11 | System nośników | carriers.py, carriers.yml | ✅ |
| 12 | Code review | weryfikacja volume_m3, naprawa testów | ✅ |
| 13 | Modernizacja UI | dark theme, komponenty, Plotly | ✅ |
| 14 | Poprawki bugów | timestamp conversion, null handling | ✅ |
| 15 | UI Audit Priority 3 | render_bold_label, render_data_table, DEPRECATED | ✅ |
| 16 | UI Fixes - Sidebar & Titles | nawigacja, statusy, tytuły sekcji | ✅ |
| 17 | Naprawa Stock Volume | konwersja stock z przecinkami | ✅ |
| 18 | Priorytet nośników | ręczny priorytet w trybie Prioritized | ✅ |

---

## Modernizacja UI (Faza 13) - ZAKOŃCZONA

**Plan:** `Dev/UI_MODERNIZATION_PLAN.md`

| Etap | Zakres | Status |
|------|--------|--------|
| 1 | Dark theme + struktura | ✅ |
| 2 | Komponenty UI | ✅ |
| 3 | Refaktoryzacja app.py | ✅ |
| 4 | Import view | ✅ |
| 5 | Capacity view + Plotly | ✅ |
| 6 | Performance view + Plotly | ✅ |
| 7 | Reports view | ✅ |
| 8 | Finalizacja | ✅ |

---

## Poprawki Bugów (Faza 14) - ZAKOŃCZONA

| Problem | Rozwiązanie | Plik |
|---------|-------------|------|
| `'int' object has no attribute 'date'` | Konwersja Unix epoch → datetime | `pipeline.py:200-216` |
| `InvalidOperationError` na `.dt.weekday()` | Defensywna konwersja timestamp | `performance.py:123-136` |
| `NoneType - int` w heatmapie | Filtr null timestamps | `performance_view.py:324` |
| `use_container_width` deprecated | Zamiana na `width="stretch"` | 6 plików UI |

---

## Naprawa Stock Volume (Faza 17) - ZAKOŃCZONA

**Problem:** Po Capacity Analysis wartości Stock volume = 0

**Przyczyna:** W `pipeline.py` wartości stock z przecinkiem/kropką dziesiętną (np. "100,5") były konwertowane na NULL przy `cast(Int64)`, co skutkowało `stock_qty = 0`.

| Zmiana | Plik | Szczegóły |
|--------|------|-----------|
| Nowa konwersja stock | pipeline.py:119-136 | string → replace comma → float → round → int |
| Ostrzeżenie o NULL | pipeline.py:133-136 | Informacja gdy wartości nie mogą być przekonwertowane |

**Przepływ konwersji:**
```
"100,5" → "100.5" → 100.5 → 101.0 → 101
```

---

## UI Fixes - Sidebar & Titles (Faza 16) - ZAKOŃCZONA

**Zmiany:**

| Zmiana | Plik | Szczegóły |
|--------|------|-----------|
| Aktywna zakładka nawigacji | theme.py | Dodano obramowanie 2px accent (#b7622c) dla wybranego elementu |
| Usunięcie border ze statusów | theme.py | Dodano selektory dla .stAlertContainer z border: none |
| Nazwa aplikacji | app.py:130 | "DataAnalysis" → "Data Analysis" |
| Tytuł Capacity | app.py:220 | Dodano st.header("Capacity") |
| Tytuł Performance | app.py:348 | Dodano st.header("Performance") |

**CSS Selektory dla nawigacji:**
- `label:has(input:checked)` - nowoczesny CSS
- `label[aria-checked="true"]` - fallback ARIA
- `label[data-checked="true"]` - fallback legacy

---

## UI Audit Priority 3 (Faza 15) - ZAKOŃCZONA

**Nowe komponenty w layout.py:**
- `render_bold_label(text, icon, size)` - stylizowane etykiety bold
- `render_data_table(df, height, title)` - wrapper dla dataframe

**Zmiany w plikach:**
| Plik | Zakres zmian |
|------|--------------|
| capacity_view.py | 8 zamian bold labels na render_bold_label() |
| validation_view.py | 2 zamiany st.write("**...**") |
| performance_view.py | 2 zamiany st.markdown("**...**") |
| app.py | 1 zamiana (Outlier validation) |
| reports_view.py | 2 zamiany bold labels |
| layout.py | Dodano DEPRECATED do legacy status functions |
| reports_view.py | Usunięto nieużywane legacy imports |

---

## Funkcje Wyłączone Tymczasowo

| Funkcja | Status | Lokalizacja |
|---------|--------|-------------|
| Utilization sliders | ⏸️ | `app.py:111-127` |
| Optional fields mapping | ⏸️ | `app.py:420-472` |

---

## Priorytet Nośników (Faza 18) - ZAKOŃCZONA

**Cel:** Ręczne ustawienie priorytetu nośników w trybie "Prioritized"

**Zmiany:**

| Plik | Zmiana |
|------|--------|
| `types.py` | Dodano pole `priority: Optional[int]` do `CarrierConfig` |
| `carriers.py` | Obsługa priority przy zapisie custom carriers |
| `capacity.py` | Filtrowanie i sortowanie po priority w trybie Prioritized |
| `carriers.yml` | Dodano priority: 1, 2, 3 do predefined carriers |
| `capacity_view.py` | Zaktualizowany komunikat informacyjny |

**Logika:**
- `priority: 1` = najwyższy priorytet (pierwszy w kolejności)
- `priority: None` = nośnik pomijany w trybie Prioritized
- W trybie Independent priorytet nie ma wpływu

**Przepływ danych:**
```
carriers.yml: priority: 1, 2, 3 lub brak
    ↓
CarrierConfig.priority = 1, 2, 3 lub None
    ↓
capacity.py (prioritization_mode=True):
    1. Filter: carriers where priority is not None
    2. Sort: by priority ascending (1 first, 2 second, ...)
    3. Assign SKU to first fitting carrier
```

---

## Możliwe Przyszłe Rozszerzenia

- [ ] Testy wydajnościowe (200k SKU, 2M orders)
- [ ] Eksport do Excel z formatowaniem
- [x] Dashboard z wykresami (Plotly) → Faza 13
- [ ] Przywrócenie utilization sliders
- [ ] Rozszerzenie optional fields

---

## Legenda

| Symbol | Znaczenie |
|--------|-----------|
| ✅ | Ukończone |
| ⏳ | W trakcie realizacji |
| ⏸️ | Wyłączone tymczasowo |
| [ ] | Do zrobienia (przyszłość) |
