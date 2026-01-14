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

---

## Funkcje Wyłączone Tymczasowo

| Funkcja | Status | Lokalizacja |
|---------|--------|-------------|
| Utilization sliders | ⏸️ | `app.py:111-127` |
| Optional fields mapping | ⏸️ | `app.py:420-472` |

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
