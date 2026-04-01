# FastAPI + Vue 3 Migration — Status (Datavisor)

**Branch:** `feature/fastapi-vue3-migration`
**Date:** 2026-02-25

---

## Phases completed

### Phase 1 ✅ FastAPI PoC (stateless endpoint)
- `api/main.py` — app factory, CORS, lifespan
- `api/routers/analyze.py` — stateless `POST /api/v1/analyze/capacity`
- `api/schemas/analysis.py` — `CapacityResponse` serializing Polars DataFrame

**Verification:** `curl -F "file=@test.xlsx" http://localhost:8000/api/v1/analyze/capacity` → full `CapacityAnalysisResult` JSON ✅

---

### Phase 2 ✅ Database + persistence
| File | Purpose |
|------|---------|
| `api/database.py` | Async SQLAlchemy engine, SQLite (dev) / PostgreSQL (prod) |
| `api/models/user.py` | User ORM (UUID PK, email, bcrypt hash) |
| `api/models/analysis_run.py` | AnalysisRun ORM (JSONB for results) |
| `api/models/carrier.py` | Carrier ORM (migrated from YAML) |
| `api/models/upload_staging.py` | Temp upload staging (TTL) |
| `api/dependencies.py` | `get_db()`, `get_current_user()` (JWT) |
| `api/routers/auth.py` | `POST /login`, `GET /me` |
| `api/routers/runs.py` | CRUD runs, `POST /{id}/capacity`, `POST /{id}/quality` |
| `api/routers/carriers.py` | GET/POST/PATCH/DELETE carriers |
| `api/routers/reports.py` | `GET /{id}/reports/zip` streaming response |
| `api/seed.py` | CLI: init DB + seed users + seed carriers from YAML |

**Verification:** Login → create run → POST /quality → POST /capacity → GET /runs/{id} → result persisted ✅

---

### Phase 3 ✅ Auth + Vue 3 frontend
**Stack:** Vue 3 + TypeScript + Vite + Tailwind CSS v4 + Pinia + Vue Router 4 + Axios

| Layer | Files |
|-------|-------|
| API client | `src/api/client.ts` (Axios + JWT interceptor) |
| API wrappers | `src/api/auth.ts`, `runs.ts`, `carriers.ts` |
| Stores | `src/stores/auth.ts`, `run.ts`, `carriers.ts` |
| Router | `src/router/index.ts` — auth guard, 5 routes |
| Views | `LoginView`, `DashboardView`, `RunsView`, `RunView` (5 tabs), `CarriersView` |
| Components | `ImportTab`, `QualityTab`, `CapacityTab`, `ReportsTab`, `NewRunModal`, `KpiCard`, `StatusBadge` |

**Verification:** `npm run build` → build succeeds, 0 TypeScript errors ✅

---

### Phase 4 ✅ PDF reports (reportlab)
- `api/pdf_generator.py` — A4 PDF with KPI summary + carrier breakdown table (reportlab, pure-Python)
- `GET /api/v1/runs/{id}/reports/pdf` → `Response(content=pdf_bytes, media_type="application/pdf")`
- Frontend: PDF download button in `ReportsTab.vue`

Note: Used `reportlab` instead of `weasyprint` — WeasyPrint requires GTK on Windows.
On Render.com (Linux) WeasyPrint works and can be added as upgrade later.

### Phase 5 ✅ Full feature parity (Fazy A–E) — 2026-02-24

#### Faza A — Column Mapping Wizard (ImportTab)
- `POST /api/v1/runs/{id}/masterdata/inspect` — saves file, returns columns + auto-suggestions + 5 preview rows
- `run_quality` now accepts `mapping_json: Form` — parses to `MappingResult` before ingest
- `ImportTab.vue` rewritten as 3-step wizard: Upload → Map → Done
- New schemas: `ColumnSuggestion`, `MappingInspectResponse`
- New API calls: `inspectMasterdata`, `runQualityWithMapping`

#### Faza B — Performance Pipeline
- `POST /api/v1/runs/{id}/orders/inspect` — orders file upload + column suggestions
- `POST /api/v1/runs/{id}/orders/ingest` — ingest with mapping, saves stats to `analysis_config`
- `POST /api/v1/runs/{id}/performance` — `PerformanceAnalyzer.analyze()`, saves full result to `run.performance_result`
- New `PerformanceTab.vue` — full 3-section wizard: orders upload → settings (productive hours slider) → results (KPI grid + Daily Activity chart + Hourly Heatmap + SKU Pareto table)
- `RunView.vue` — replaced "coming soon" with `<PerformanceTab />`

#### Faza C — Capacity UX
- `borderline_threshold: float = Form(default=2.0)` added to `run_capacity` endpoint
- `CapacityTab.vue` — radio group (Independent/Prioritized/Best Fit), borderline slider, 3 Plotly charts (Carrier Fit stacked bar, Dimensions Distribution histogram, Weight Distribution histogram), SKU table with status/carrier filters + CSV export button

#### Faza D — CSV Reports
- `run_quality` now stores full DQ detail lists: `missing_critical`, `suspect_outliers`, `high_risk_borderline`, `duplicates`, `conflicts`
- `GET /api/v1/runs/{id}/reports/csv/{report_name}` — whitelist of 8 reports (DQ_Summary, DQ_MissingCritical, DQ_SuspectOutliers, DQ_HighRiskBorderline, DQ_Duplicates, DQ_Conflicts, Capacity_Results, SKU_Pareto)
- `ReportsTab.vue` — DQ CSV buttons (dimmed if no quality_result) + Analysis CSV buttons (dimmed if no results)

#### Faza E — Dashboard KPIs
- `DashboardView.vue` — fetches full latest run on mount, shows 5-step pipeline status indicator + KPI summary (Quality Score, Fit%, Total Lines, Avg Lines/Hour)

### Phase 6 🔜 Sharing + advanced features
Not started.

---

## Running locally

```bash
# Backend
python -m api.seed admin@example.com password123 Admin  # jednorazowy setup (tworzy datavisor.db)
uvicorn api.main:app --port 8000

# Frontend (separate terminal)
cd frontend && npm run dev
# → http://localhost:5173 (proxied to :8000)
```

## API docs
Visit `http://localhost:8000/docs` for interactive Swagger UI.

---

## Tests
All 191 tests pass. Backend (`src/`) is untouched.
```
pytest tests/ -q → 191 passed
```
