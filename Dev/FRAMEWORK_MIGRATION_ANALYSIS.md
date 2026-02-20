# Analiza frameworków UI — alternatywy dla Streamlit

**Data:** 2026-02-20
**Kontekst:** Ocena ograniczeń Streamlit i potencjalnych alternatyw

---

## Zidentyfikowane problemy ze Streamlit

Na podstawie przeglądu kodu zidentyfikowano 4 główne problemy:

1. **Layout — brak kontroli** — niemożliwość precyzyjnego pozycjonowania, brak sticky headers, floating panels itp.
2. **Custom komponenty** — brak komponentów których potrzebuje app (zaawansowane tabele, drag-and-drop)
3. **Rerun — powolne odświeżanie** — każda interakcja rerenderuje całą stronę
4. **CSS walka** — każda zmiana wyglądu wymaga hacków i jest krucha

**Dowody w kodzie:**
- `src/ui/theme.py` — **1179 linii** CSS injektowanego przez `st.markdown(unsafe_allow_html=True)`
- Własny system komponentów w `layout.py` obchodzący limity Streamlit
- Ciągłe commity naprawiające UI (tab spacing, button styling, toolbar icons)

---

## Stan obecnego backendu

Backend jest **dobrze zaprojektowany** i niezależny od warstwy UI:

```
src/core/        ← typy Pydantic, konfiguracja
src/ingest/      ← import, mapping wizard
src/quality/     ← walidacja, DQ metrics
src/model/       ← modele danych
src/analytics/   ← capacity, performance (Polars + DuckDB)
src/reporting/   ← generowanie raportów CSV/ZIP
```

Migracja UI nie wymaga zmiany backendu — to czysta wymiana warstwy prezentacji.

---

## Ocena alternatyw

### Opcja A: Dash (Plotly)
**Najszybsza ścieżka migracji**

| | |
|---|---|
| **Wysiłek migracji** | Średni — rewrite UI, backend bez zmian |
| **Kontrola UI** | Dobra — prawdziwy CSS Flexbox/Grid |
| **Integracja Plotly** | Natywna (ten sam ekosystem) |
| **Python-only** | ✅ Tak |
| **Dojrzałość** | ✅ Dojrzały, duża społeczność |

```python
# Callbacks zamiast reruns — tylko to co potrzeba się odświeża
@app.callback(Output("chart", "figure"), Input("btn", "n_clicks"))
def update_chart(n):
    return generate_figure()
```

**Zalety:** Natywna integracja Plotly, prawdziwy layout CSS, callbacks > reruns, DataTable, dcc.Upload
**Wady:** Bardziej verbose niż Streamlit, duże przepisanie UI

---

### Opcja B: FastAPI + Vue 3
**Pełna kontrola, maksymalna swoboda**

Backend (Pydantic, analytics, reporting) jest **gotowy na FastAPI** — potrzeba tylko nowej warstwy API:

```
src/api/          ← nowe (FastAPI endpoints)
src/analytics/    ← bez zmian
src/model/        ← bez zmian
src/reporting/    ← bez zmian
frontend/         ← Vue 3 + Plotly.js / ECharts
```

| | |
|---|---|
| **Wysiłek migracji** | Duży |
| **Kontrola UI** | Pełna — absolutna wolność |
| **Integracja Plotly** | Manualna (Plotly.js) |
| **Python-only** | ❌ Wymaga Vue/JS |
| **Dojrzałość** | ✅ Bardzo dojrzały |

**Zalety:** Absolutna wolność UI, backend może obsługiwać wiele klientów przez API, prawdziwy responsive design
**Wady:** Wymaga znajomości Vue/JS, największy wysiłek

---

### Opcja C: Reflex
**Nowoczesne podejście Python → React**

```python
class State(rx.State):
    data: list[dict] = []

    async def load_analysis(self):
        self.data = await run_analysis()

def page():
    return rx.data_table(data=State.data)
```

| | |
|---|---|
| **Wysiłek migracji** | Średni-duży |
| **Kontrola UI** | Pełna (React pod spodem) |
| **Python-only** | ✅ Tak |
| **Dojrzałość** | ⚠️ Młody projekt (2023) |

**Zalety:** Pełna moc React w Pythonie, prawdziwy state management
**Wady:** Młody projekt, API jeszcze ewoluuje, mniejsza społeczność

---

## Porównanie zbiorcze

| Kryterium | Streamlit (teraz) | Dash | FastAPI+Vue | Reflex |
|---|---|---|---|---|
| Wysiłek migracji | — | Średni | Duży | Średni-duży |
| Kontrola UI | ❌ Słaba | ✅ Dobra | ✅ Pełna | ✅ Pełna |
| Python-only | ✅ | ✅ | ❌ | ✅ |
| Plotly integracja | ✅ | ✅ Natywna | Manualna | Manualna |
| Dojrzałość | ✅ | ✅ | ✅ | ⚠️ |
| Rerun problem | ❌ Tak | ✅ Brak | ✅ Brak | ✅ Brak |
| CSS kontrola | ❌ Hacki | ✅ Normalna | ✅ Pełna | ✅ Pełna |

---

## Rekomendacja

**Jeśli 100% Python** → **Dash** — najbezpieczniejszy wybór, dojrzały, natywny Plotly, rozwiązuje wszystkie 4 problemy

**Jeśli dostępna wiedza JS** → **FastAPI + Vue 3** — największa swoboda długoterminowo, backend jest już gotowy

---

## Następne kroki (do decyzji)

- [ ] Proof-of-concept: zmapować `capacity_view.py` na Dash żeby zobaczyć jak to wygląda konkretnie
- [ ] Ocenić znajomość Vue/JS w zespole
- [ ] Zdecydować o priorytetach: szybkość migracji vs długoterminowa swoboda
