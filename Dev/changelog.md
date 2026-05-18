# Changelog

Rejestr zmian w projekcie Datavisor.

## Format wpisów
```
### [YYYY-MM-DD HH:MM] - Typ zmiany
- Opis zmiany
- Branch/Commit: nazwa_brancha lub hash commita
```

---

### [2026-05-18] - Feature (feature/portable-static-serving) — wersja Portable Windows aplikacji

Branch: `feature/portable-static-serving` · commits `45be975` + `9d9ce89` (jeszcze nie zmergowany).

- **api/main.py**: warunkowy `StaticFiles` mount + SPA catchall pod `/{full_path:path}` gdy `frontend/dist/` istnieje. Guard wycina `api/`, `health`, `docs`, `redoc`, `openapi.json` z fallbacku — kierują do właściwych routerów / 404. Dev workflow (Vite :5173 + uvicorn :8000) bez zmian, bo bez zbudowanego dist mount się nie aktywuje.

- **Dev/Build-Portable.ps1**: skrypt buildujący paczkę portable do `D:\VS\Portable\Datavisor-Portable\`. Pobiera embeddable CPython 3.11.9 (~15 MB ZIP), bootstrapuje pip, instaluje 18 runtime depsów z hardcoded listy (sync z `pyproject.toml`, bez `asyncpg` bo portable jedzie tylko na SQLite), robocopy api/src/frontend\dist do `app/`, generuje `Start.bat`/`Stop.bat`/`README-PORTABLE.md`. Opcjonalny `-SmokeTest` flag.

- **Embedded Python `_pth` hack**: embeddable Python ignoruje `PYTHONPATH` i CWD — sys.path jest sztywno z `python311._pth`. Build dopisuje `..\..\app` (relatywnie do `runtime\python\`) żeby `python -m api.seed` i `uvicorn api.main:app` znajdowały moduły.

- **Start.bat**: ustawia absolutne `DATABASE_URL` (SQLite file w roocie paczki, slash-normalizowane), seeduje DB przy pierwszym starcie (`api.seed admin@local.app admin Admin` — 3 predefined carriers + admin), sprawdza wolny port 8000, uruchamia uvicorn ukryty w tle, czeka na `/health` (do 15 s), otwiera przeglądarkę. PID do `logs\server.pid`.

- **Smoke test PASS**: `/health` → 200 OK; `/` → SPA index.html; `/dashboard/foo` → SPA (deep-link); `/api/v1/runs` → 401 (router wygrywa z catchall). Embedded Python 3.11.9 zaimportował wszystkie ciężkie C-extensions: polars, duckdb, pyarrow, matplotlib, bcrypt, jose. Paczka **540 MB rozpakowana**, ~150 MB w ZIP (oszacowane).

- **Wykluczenia z paczki**: `Dev/`, `uploads/`, `tests/`, `tests_alan/`, `node_modules/`, `__pycache__`, `.git`, `.claude`, `.devcontainer`, `.playwright-mcp`, `datavisor.db` (z głównego dev), `data/datasets`.

- **Pliki nowe**: `Dev/Build-Portable.ps1`. Modified: `api/main.py`.

- **Co dalej**: spakować `Compress-Archive` do ZIP-a v0.1.0 i wysłać koledze. Każda nowa zmiana w aplikacji wymaga re-buildu paczki (`.\Dev\Build-Portable.ps1 -Force`).

---

### [2026-05-17] - Feature (feature/container-order-tool → main) — Container Order Calculator (Kardex VBM Box)

Merge: `b24a61f` · GitHub Issue: [#49](https://github.com/LokatyTrzmielu/DataAnalysis/issues/49). Branch usunięty po merge'u.

**Pełny tool przeszedł przez 17 iteracji w tym samym dniu** — od pierwszego szkieletu (drugi kafelek w Tools) do produkcyjnej funkcjonalności z historią obliczeń i rozbiciem zamówienia na bazy + ramki EasyClick. Szczegółowy changelog per-iteracja: `Dev/CONTAINER_ORDER_TOOL.md`.

- **Planer** (`src/analytics/container_planner.py`): bezstanowy algorytm dopasowujący SKU do wariantów Kardex VBM Box (48-wariant katalog = 12 footprintów × 4 wysokości 138/188/238/288 mm). Tryby: Auto (greedy set-cover, K wariantów), Guided (Simple/Standard/Full coverage), Manual. Cele optymalizacji: Min waste / Min bins / Max SKU coverage. Per-SKU candidates obliczane przez `_compute_fits` (geometric fit + weight cap + max_loc enforcement). Imputacja brakujących wymiarów medianą z datasetu (opt-in). 34/34 testów w `tests/test_container_planner.py`.

- **Base + Frame breakdown**: każdy fizyczny pojemnik = 1 baza 138 mm + N ramek EasyClick × 50 mm. `Variant.frames_per_bin = (tier - 138) // 50` (0/1/2/3 frames). `VariantSummary.total_frames_required` + `ContainerPlan.total_frames`. UI Summary tab, Excel arkusz „Order Summary", PDF tabela, CSV — nowe kolumny **Bases** i **Frames** z sumami w wierszu TOTAL.

- **History storage** (`api/models/container_order_plan.py`): nowy model `ContainerOrderPlan` (UUID PK, owner CASCADE, `source_run_id` SET NULL — usunięcie analizy NIE kasuje zachowanych planów, JSON snapshots params + plan, label, notes, timestamps). Auto-create przez `Base.metadata.create_all`. 5 endpointów `/plans` (POST save, GET list paginated, GET detail, PATCH rename/notes, DELETE) — wszystkie owner-only.

- **API** (`api/routers/container_order.py`, `api/schemas/container_order.py`): 9 endpointów pod `/api/v1/tools/container-order/` (catalog, eligible-analyses, calculate, export, plans CRUD). Owner-aware access przez `_get_accessible_run` (owner/public/shared). `EligibleAnalysis` schemat z MiB-specific metrykami (planned_sku, fit_pct dla nośnika MiB osobno od datasetu).

- **Excel / PDF / CSV generatory** (`api/excel_generator.py`, `api/pdf_generator.py`): 4-arkuszowy XLSX (Order Summary / SKU Assignment / Parameters / Orphans) z kolumnami Fit + Imputed + Bases + Frames i sumami w TOTAL; 2-stronicowy PDF z bar chartem; CSV jednoarkuszowy. „Generated by {name} <email>" zamiast Run ID. Fix empty-row-2 buga (`ws.cell` side-effect na `freeze_panes`).

- **Frontend** (Vue 3 + Pinia): 5-tabowa nawigacja `Analysis / Calculation / Summary / Export / History`. `SkuAssignmentTable.vue` z Excel-style filtrami w nagłówkach (▾ triggery, Teleport popovery żeby nie były clipowane przez `overflow-x:auto`) — filtry SKU search / Imputation status / ABC (z greyed-out dla klas niewybranych w Calculation) / Recommendation / Assignment. `VariantCard.vue` z SVG bin schematic (light/dark variants). `Bin3DPreview.vue` z Three.js sceną reagującą na `html.dark` przez MutationObserver. Loading indicators (page-icon pulse + button spinner). Save plan modal z `card-apple-elevated`. UI w całości po angielsku, en-GB date locale.

- **Bug fixy dotychczasowe odsłonięte przy okazji**: strict ABC/Machine filtering gdy istnieją dane Performance (SKU bez metadanych nie wymykają się przez filtr, jeśli user jawnie wybrał klasę/Machine); `max_locations_per_sku` realnie egzekwowane (SKU które wymagają więcej lokalizacji niż cap trafiają do orphans zamiast cicho overstuffować); chip BORDERLINE w tabeli SKU (`fit_status` plumb'owany przez `Assignment`); audyt dark mode + caption 3D solid bg.

- **Pliki nowe**: `api/models/container_order_plan.py`, `api/excel_generator.py`, `api/routers/container_order.py`, `api/schemas/container_order.py`, `frontend/src/api/containerOrder.ts`, `frontend/src/components/Bin3DPreview.vue`, `frontend/src/components/SkuAssignmentTable.vue`, `frontend/src/components/VariantCard.vue`, `frontend/src/stores/containerOrder.ts`, `frontend/src/views/tools/ContainerOrderView.vue`, `src/analytics/container_planner.py`, `tests/test_container_planner.py`, `Dev/CONTAINER_ORDER_TOOL.md`. Modified: `api/models/__init__.py`, `api/pdf_generator.py`.

- **Pozostawione na v2**: sharing zapisanych planów między userami, mixed-cell konstrukcje (PDF flyer wspomina o 100+ układach), inne nośniki niż MiB 640×440, multi-warehouse, wycena persystowana serwer-side.

---

### [2026-05-16] - Feature (feature/time-saved-counter) — Time-saved counter per user

- **Backend: TimeSavingEvent model + service** (`api/models/time_saving_event.py`, `api/services/time_saving.py`): nowa tabela `time_saving_events` (per-user FK, event_type, manual_seconds, scale_value, run_id, context JSON, indeksy na user_id+created_at); `TIME_SAVING_RULES` z bazowymi estymacjami czasu manualnego (15min import masterdata, 30min DQ, 45min capacity, 40min performance + 25min Pareto, 45min PDF, 25min ZIP) + skalowanie z liczbą wierszy/SKU/carrier/wykresów/CSV; `calculate_manual_seconds()` pure-function; `record_event()` failsafe (try/except + rollback)

- **Backend: endpoint `GET /api/v1/users/me/time-savings`** (`api/routers/time_saving.py`): zwraca `total_seconds`, `total_events` i `breakdown` (per event_type, label, count, seconds, sortowane DESC po seconds); strict per-user isolation przez `Depends(get_current_user)`

- **Backend: integracja w istniejących endpointach** (`api/routers/datasets.py`, `runs.py`, `reports.py`): wywołania `record_event` po imporcie datasetu (masterdata/orders), po Quality, Capacity, Performance, po eksporcie ZIP i PDF; każde wewnątrz try/except — błąd telemetrii nigdy nie psuje samej analizy

- **Backend: backfill CLI** (`api/scripts/backfill_time_savings.py`): jednorazowy skrypt `python -m api.scripts.backfill_time_savings`; iteruje po `AnalysisRun`, tworzy historyczne eventy dla nie-NULL `quality_result/capacity_result/performance_result` (timestamp z `updated_at`); idempotentny — sprawdza istnienie eventu po (run_id, event_type)

- **Frontend: `TimeSavedCard.vue` w Settings** (`frontend/src/views/SettingsView.vue`, `frontend/src/components/settings/TimeSavedCard.vue`, `frontend/src/api/timeSavings.ts`): nowa karta między Account a Change password; duży licznik `⏱ Xh Ymin` + count operacji + tabela breakdown per typ (label / count / time); loading + empty + error states; helper `formatDuration()` formatuje sekundy w postaci `Xh Ymin`

- **Testy** (`tests/test_time_saving.py`): 23 testy obejmujące `calculate_manual_seconds` (różne event_types, skalowanie, edge cases), persystencję `record_event` + agregację `get_summary_for_user`, izolację per-user, endpoint (401 bez tokenu, empty summary, seeded events, isolation między userami), failsafe (unknown event_type, błąd commitu)

- **Średnie wartości manualnej pracy** (estymacje analityka logistyki w Excel/SQL):
  - Masterdata import 3000 SKU ≈ 30 min · Orders import 50k linii ≈ 3h 40min
  - Quality 5000 rows ≈ 45 min · Capacity 3000 SKU × 5 carriers ≈ 1h 40min
  - Performance 50k linii + Pareto ≈ 1h 55min · PDF (5 charts) ≈ 1h 10min · ZIP (8 CSV) ≈ 41 min

- **Poprawka skalowania Performance** (`api/services/time_saving.py`, `api/scripts/backfill_time_savings.py`): podczas weryfikacji backfill dla Admina (3 analizy z 236k–975k linii) początkowe `per_1000_lines = 4 min` dawało nierealistyczne 65h dla pojedynczego runu (manualna analiza w SQL skaluje się sub-liniowo). Zmiana: `per_1000_lines: 1 min` + nowe pole `max_seconds: 6h` jako rozsądny ceiling per event (`calculate_manual_seconds` aplikuje cap jeśli reguła go specyfikuje). Backfill scripts naprawiony — `carriers_analyzed` w `capacity_result` to lista, więc używamy `len(...)`. Test `test_performance_caps_huge_datasets` waliduje cap dla 1M linii. Po poprawce Admin (3 historyczne analizy) widzi realistyczne ~27h 18min zamiast wcześniejszych ~141h.

---

### [2026-05-15] - Feature + Fix (main) — ABC Pareto & Performance carrier filter + SKU Pareto UX fixes

- **Feature: ABC Pareto — carrier filter** (`PerformanceTab.vue`): nowy dropdown "Filter by carrier" w sekcji SKU Pareto; lista carriers pochodzi z `capacity_result.carrier_stats`; filtr zawęża tabelę i wykresy do SKU przypisanych do wybranego nośnika; opcja "All carriers" resetuje filtr

- **Feature: Performance — data scope by carrier** (`api/routers/runs.py`, `PerformanceTab.vue`): nowy filtr "Data scope" w nagłówku Performance; całościowa analiza lub ograniczona do wybranego nośnika (tylko SKU przypisane w capacity_result); pełne tłumaczenie EN (usunięto ostatnie polskie stringi z zakładki Performance)

- **Feature: PDF — Productive Hours & Data Scope** (`api/pdf_generator.py`, `api/routers/runs.py`): nowa tabela info w raporcie PDF Performance (sekcja Capacity); wiersze: "Productive hours / shift" i "Data scope" (nazwa nośnika lub "Entire file"); `data_scope` i `productive_hours_per_shift` serializowane w `performance_result`

- **Fix: SKU Pareto carrier filter** — wyłączanie opcji niedostępnych poza aktualnym zakresem danych z tooltipem "Not in current data scope"

- **Fix: SKU Pareto — column widths + tooltip position** — stałe szerokości kolumn (nie rozciągają się); tooltip pozycjonowany do lewej (zapobiega overflowowi poza ekran)

- **Fix: SKU Pareto filters — gray out with no data** — opcje dropdownów (Fit Status, Recommendation) wyszarzone gdy brak danych dla danej opcji w aktualnym filtrze

---

### [2026-05-15] - Feature (feature/carrier-priority-drag-drop) — Drag & Drop Priority dla nośników w Capacity Analysis

- **Priorytety per-run**: kolejność nośników w trybie Prioritized ustalana przez drag & drop w Capacity Analysis (nie w zakładce Carriers)
- **Frontend** (`CapacityTab.vue`): lista z uchwytem drag & drop pojawia się gdy tryb = Prioritized; kolejność od góry do dołu = priorytet 1, 2, 3…; synchronizacja z CarrierMultiSelect (dodanie/usunięcie nośnika aktualizuje listę)
- **Backend** (`api/routers/runs.py`): gdy `prioritization_mode=True` i `carrier_ids` podane, pozycja w liście = priorytet (index 0 → priority 1); fallback na DB priority gdy brak explicit carrier_ids
- **Brak zmian w DB**: pole `priority` na modelu Carrier pozostaje jako fallback dla wywołań API

---

### [2026-05-15] - Feature (main) — PDF: Carrier Settings + BORDERLINE threshold

- **Carrier Settings** (nowa sekcja w PDF przed Carrier Breakdown): tabela z nazwą carriера, wymiarami wewnętrznymi (L/W/H mm) i max wagą (kg); wyświetla wyłącznie carriers uczestniczące w analizie (wyklucza "NONE")
- **BORDERLINE z progiem**: wiersz BORDERLINE w tabeli Capacity Analysis pokazuje teraz wartość progu w nawiasie, np. `BORDERLINE (2mm)`; fallback do `BORDERLINE` dla starych wyników bez tej wartości
- **Backend** (`api/routers/runs.py`): `capacity_result` rozszerzony o `borderline_threshold_mm` i `carrier_settings` (słownik: carrier_id → name/dims/max_weight)
- **PDF generator** (`api/pdf_generator.py`): nowa sekcja Carrier Settings z tabelą, dynamiczny label BORDERLINE

---

### [2026-05-15] - Feature (main) — Fit Status w SKU Pareto (join z capacity)

- **Kolumna "Fit Status"** w tabeli SKU Pareto: FIT (zielony), Borderline (pomarańczowy), NOT FIT (czerwony), N/A (szary)
- **Źródło danych**: join `capacity_result.rows` × `sku_pareto` na SKU w warstwie API; best-fit = max(FIT > BORDERLINE > NOT_FIT) across all carriers
- **Filtr**: dropdown rozszerzony o opcje FIT / Borderline / NOT FIT
- **Export CSV**: kolumna `fit_status` w eksporcie z przycisku i w ZIP Reports
- **Backend** (`api/routers/runs.py`): budowanie `_sku_fit_map` przed serializacją; pole `fit_status` w każdym wierszu `sku_pareto`; działa gdy capacity nie była uruchomiona (fit_status = null)
- **Reports** (`api/routers/reports.py`): `fit_status` dodane do `REPORT_COLUMNS["SKU_Pareto"]`
- **Frontend types** (`frontend/src/api/runs.ts`): pole `fit_status: string | null` w `PerformanceSKUPareto`
- **Frontend UI** (`frontend/src/components/analysis/PerformanceTab.vue`): `fitStatusClass()`, `fitStatusLabel()`, kolumna tabeli, filtr, CSS `.badge-nf`

---

### [2026-05-15] - Feature (main) — Rekomendacja maszynowa w SKU Pareto

- **Kolumna "Rekomendacja"** w tabeli SKU Pareto: domyślnie klasa A = "Maszyna", B/C = "Poza maszyną"
- **Klikalne wiersze w Pareto Concentration**: kliknięcie ustawia własny próg top-N (np. top 200 SKU); wiersz podświetlony; kliknięcie ponownie = reset do ABC
- **Baner informacyjny** nad tabelą SKU Pareto: informuje o aktywnym progu (klasa A domyślny lub top-N custom)
- **Filtr rozszerzony** w dropdownie: dodano opcje "Maszyna" i "Poza maszyną" (filtrują wg aktywnego progu)
- **Export CSV** SKU Pareto zawiera kolumnę `recommendation`; Reports ZIP też (automatycznie przez dict keys)
- **Backend** (`src/analytics/performance.py`): pole `recommendation` w dataclass `SKUFrequency`; przypisanie w `_calculate_sku_pareto()`
- **API** (`api/routers/runs.py`): serializacja `recommendation` w `sku_pareto`
- **Reports** (`api/routers/reports.py`): `recommendation` dodane do `REPORT_COLUMNS["SKU_Pareto"]`
- **Frontend types** (`frontend/src/api/runs.ts`): pole `recommendation: string` w `PerformanceSKUPareto`
- **Frontend UI** (`frontend/src/components/analysis/PerformanceTab.vue`): `customTopN` ref, `rowRecommendation()`, `setCustomTopN()`, baner, kolumna, klikalne wiersze

---

### [2026-05-13] - Feature (main) — Pareto Concentration Table w ABC Classification

- **Nowa tabela Pareto Concentration** w zakładce Performance (sekcja ABC):
  - Pokazuje koncentrację aktywności w pasmach Top-N SKU (10, 20, ..., 100, 200, ..., total)
  - Kolumny: MovedSKU, CumulatedSKU%, Lines/Day, Lines%, Cumul.Lines%, Pieces/Day, Pieces%, Cumul.Pieces%
  - "Lines/Day" i "Pieces/Day" = średnia dzienna (total / liczba dni analizy)
  - Wiersz "Total" podsumowuje całość
  - Przycisk "Export CSV" bezpośrednio z tabeli
  - **Backend** (`src/analytics/performance.py`): nowy dataclass `ParetoBandRow`, metoda `_calculate_pareto_bands()`, pole `pareto_bands` w `PerformanceAnalysisResult`
  - **API** (`api/routers/runs.py`): serializacja `pareto_bands` w odpowiedzi performance
  - **Reports CSV** (`api/routers/reports.py`): nowy typ raportu `"Pareto_Bands"`, endpoint CSV + ZIP
  - **Reports tab** (`frontend/src/components/analysis/ReportsTab.vue`): przycisk "Pareto Bands"
  - **PDF** (`api/pdf_generator.py`): tabela Pareto Concentration w sekcji Performance Analysis (po Per Shift, przed wykresami)
  - **Frontend types** (`frontend/src/api/runs.ts`): interfejs `PerformanceParetoBand`, pole opcjonalne w `PerformanceResult`

---

### [2026-05-12] - Fix (main) — seria 4 commitów: polskie CSV, Orders Validation, Performance

- **Fix: CSV upload failure dla polskich plików (cp1250)**:
  - **Root cause**: `detect_separator()` używał hardcoded `encoding="utf-8-sig"` → `UnicodeDecodeError` na plikach cp1250; `detect_encoding()` próbkował tylko 4096 bajtów → polskie znaki po tej granicy powodowały fałszywe wykrycie utf-8
  - **Fix** (`src/ingest/readers.py`): `detect_encoding()` próbkuje 512 KB; `detect_separator()` używa `detect_encoding()` i `errors="replace"`; `_read_csv()` zawsze pre-dekoduje plik przez Python (obsługa wszystkich kodowań), przekazuje UTF-8 bajty do Polars
  - Commit: `bbbaba9`

- **Fix: Orders Validation pusta po imporcie Orders**:
  - **Root cause**: `OrdersIngestPipeline.run()` nie czyścił kolumny `quantity` → została jako Utf8; `OrdersValidator._check_quantity_anomalies()` wywołał `qty.eq(0)` na Utf8 → `InvalidOperationError`; cichy `except Exception` w `runs.py` łapał błąd → `orders_validation_result = None` → zakładka Validation nic nie pokazywała
  - **Fix 1** (`src/ingest/pipeline.py`): dodano `clean_numeric_column(pl.col("quantity")).cast(pl.Float64)` po `apply_mapping()` — analogicznie jak `MasterdataIngestPipeline` robi dla `stock`
  - **Fix 2** (`src/analytics/orders_validation.py`): defensywny `clean_numeric_column` na początku `_check_quantity_anomalies()` zamiast bezpośredniego `cast(Float64)`
  - **Fix 3** (`api/routers/runs.py`): dodano `logger.exception()` do obu cichych `except Exception` dla orders validation
  - Commit: `d65675a`

- **Fix: 100% Quantity Null w Validation przy danych z przecinkiem**:
  - **Root cause**: defensywny `cast(pl.Float64, strict=False)` w `_check_quantity_anomalies()` konwertował europejskie liczby ("1,5", "2,3") na `null` — Polars nie parsuje formatu z przecinkiem dziesiętnym bezpośrednio jako Float64
  - **Fix** (`src/analytics/orders_validation.py`): zastąpiono bezpośredni cast przez `clean_numeric_column()` via `with_columns` — "1,5" → 1.5, "1.500,00" → 1500.0
  - Commit: `6708449`

- **Fix: Performance 500 gdy orders nie mają kolumny order_id / order_date**:
  - **Root cause**: `PerformanceAnalyzer.analyze()` używa `order_id`, `order_date`, `quantity` w wielu miejscach; gdy CSV użytkownika nie mapuje `order_id` → `ColumnNotFoundError` → HTTP 500
  - **Fix 1** (`api/routers/runs.py`, endpoint `run_performance`): pre-processing `orders_df` przed `analyzer.analyze()`: syntetyczny `order_id` (indeks wiersza) gdy brak, `order_date` z `timestamp` gdy brak, `clean_numeric_column` na `quantity` lub domyślnie 1.0; `analyze()` owinięty w try/except → HTTP 422 na błąd
  - **Fix 2** (`src/analytics/performance.py`, metoda `analyze()`): analogiczne defensywne sprawdzenia po filtrze null timestamps
  - Commit: `5d21145`

---

### [2026-05-06] - Feature: Zastąpienie Duplicate przyciskiem Notes w RunsView (main)

- **`frontend/src/views/RunsView.vue`** — usunięto przycisk Duplicate i funkcję `onDuplicate`; dodano przycisk Notes (ikona dokumentu z liniami) z rozwijającym się textarea poniżej wiersza; zapis z debouncingiem 500 ms przez `runStore.patchRun`; ikona świeci na niebiesko gdy notatka jest zapisana lub pole otwarte (ten sam wzorzec co DashboardView)

---

### [2026-05-06] - Fix: Dashboard — brak Avg Dimensions/Weight i nieprawidłowa liczba Carriers (main)

- **Bug fix: `api/routers/runs.py`** — dodano `avg_length_mm`, `avg_width_mm`, `avg_height_mm`, `avg_weight_kg` do słownika zapisywanego jako `capacity_result` w bazie (były obliczane przez `CapacityAnalyzer`, ale nie serializowane → null na Dashboardzie)
- **Bug fix: `src/analytics/capacity.py`** — usunięto dołączanie `"NONE"` do `carriers_analyzed_ids`; "NONE" to wirtualny marker SKU niepasujących do żadnego nośnika, a nie prawdziwy carrier — jego obecność zawyżała licznik "Carriers selected" o 1; `carrier_stats["NONE"]` nadal istnieje w statystykach

---

### [2026-05-06] - Feature + Fix (main) — seria commitów

- **Feature: Rozszerzone KPI na Dashboardzie i lista analiz w sidebarze** (commit `9d7308a`):
  - Dashboard przeprojektowany: layout dwukolumnowy — KPI po lewej (flex:1), lista analiz sticky po prawej (270px)
  - Pełny zestaw KPI pogrupowany wg etapu: Masterdata (Total SKU, Quality Score), Capacity (Fit %, Fit, Not Fit, Avg Dimensions, Avg Weight, Carriers selected), SKU Cross-validation (obie strony z licznikiem i %), Orders (wiersze, dni, SKU, hourly flag, zamówienia, linie, metryki avg, pieces/line)
  - Każda karta pokazuje placeholder specyficzny dla etapu gdy krok nie był uruchomiony

- **Feature: Cache RunDetail w Pinia store** (commit `98a7610`):
  - `frontend/src/stores/run.ts` — in-memory Map do cache'owania fetched RunDetail; unikanie ponownego pobierania dużych wyników analizy przy przełączaniu analiz na Dashboardzie
  - `RunView.vue` — force-refreshuje cache po uruchomieniu analizy

- **Feature: Formularz edycji nośnika w CarriersView** (commit `98a7610`):
  - `frontend/src/views/CarriersView.vue` — ten sam formularz do tworzenia i edycji; tryb "Edit carrier" z przyciskiem Cancel; Carrier ID readonly w trybie edycji
  - `frontend/src/stores/carriers.ts` — nowa akcja `updateCarrier`
  - Rename nagłówka tabeli Capacity: "Units" → "Locations"

- **Feature: Multi-select bulk delete w RunsView** (commit `9d34a28`):
  - `frontend/src/views/RunsView.vue` — checkbox na każdym wierszu; selection bar z Select-all, licznik, Delete selected (z inline confirm), Clear
  - Bulk delete równoległy via `Promise.all`; czyści selekcję po powodzeniu; per-row delete usuwa ID z aktywnej selekcji
  - Fix dark mode: ikony duplicate/delete `@mouseleave` hardcoded `rgba(0,0,0,0.32)` → `var(--app-placeholder)`; `@mouseover` `rgba(0,0,0,0.02)` → `var(--table-row-hover)`

- **Fix: Dataset file deleted on run delete** (commit `a1a13dc`):
  - `api/routers/runs.py` — przy DELETE run plik datasetu nie był usuwany gdy run był powiązany z datasetem zamiast bezpośrednim plikiem

- **Fix: Carrier selection restoring correct state after tab switch** (commit `48e5d87`):
  - `frontend/src/components/analysis/CapacityTab.vue` — przywraca tylko carriers używane w analizie (z `carriers_analyzed`), z wykluczeniem pseudo-carrier NONE

- **Fix: Avg Dimensions card overflow gdy dimension values są null** (commit `bc87e85`):
  - `frontend/src/views/DashboardView.vue` — guard przed null `avg_*_mm` w `capacity_result`; bez sprawdzenia template literal produkował `"undefined×undefined×undefined mm"` (truthy) rozciągający kartę

- **Fix: Autofocus na input name w New Analysis modal** (commit `787a11f`):
  - `frontend/src/components/analysis/NewRunModal.vue` — HTML `autofocus` nie uruchamia się na dynamicznie montowanych komponentach; rozwiązanie: `onMounted + ref.focus()`

- **Rename: Units → Pieces w Performance tab i PDF** (commit `20dce22`):
  - `frontend/src/components/analysis/PerformanceTab.vue` — KPI label "Avg Units/Order" → "Avg Pieces/Order"; tabela throughput "Units" → "Pieces"
  - `api/pdf_generator.py` — KPI label "Total Units" → "Total Pieces"

---

### [2026-05-06] - Fix (fix/validation-outlier-detection) — 2 bugi

- **Fix: SKU cross-validation nie pokazuje się po wgraniu Masterdata po Orders**:
  - **Root cause**: `orders_validation_result` jest obliczany w momencie importu Zleceń. Gdy w tym momencie Masterdata nie istnieje → `sku_xval_available: False`. Późniejszy import Masterdata nigdy nie odświeżał tego wyniku.
  - **Fix** (`api/routers/runs.py`): Dodano helper `_load_orders_df(run)` do re-ładowania df zleceń (obsługuje `.duckdb` dataset i surowy plik Excel). W endpointach `run_quality` i `masterdata_from_dataset` — po przetworzeniu Masterdata, jeśli `sku_xval_available == False` i orders już załadowane, re-run `OrdersValidator().validate(..., masterdata_df=md_df)` i nadpisanie `orders_validation_result`.
  - Dotyczy obu ścieżek: wgranie pliku (`/quality`) i wybór z Datasets (`/masterdata/from-dataset`).



- **Fix: Validation – Suspect outliers zawsze 0, braki maskowane przez imputację**:
  - **Root cause 1**: `pipeline.py` budował DQ lists z `df_imputed` (po imputacji) — zera/NULL/negatives były już uzupełnione medianą, więc `missing_critical` wychodziło 0
  - **Root cause 2**: `build_validation_lists()` w `dq_lists.py` zwracał `suspect_outliers=[]` — nigdy nie sprawdzał ekstremalnych wartości (np. 9999mm, 9999kg)
  - **Fix 1** (`pipeline.py` linia 113): `build_validation_lists(df_imputed)` → `build_validation_lists(df_validated)` — DQ lists budowane z danych przed imputacją
  - **Fix 2** (`dq_lists.py`): dodano metodę `_find_static_threshold_outliers()` używającą `OUTLIER_THRESHOLDS` z configu; wywołana w `build_validation_lists()` zamiast pustej listy
  - Statyczne progi: length≤3650mm, width≤864mm, height≤500mm, weight≤500kg — wartości powyżej → `suspect_outlier`
  - Testy: dodano `test_find_static_threshold_outliers` i `test_build_validation_lists_detects_outliers`; 32/32 pass

---

### [2026-05-05] - Fix + Feature (main) — commit `9faa516`

- **Fix: Performance analysis 500 gdy orders z Datasetu**:
  - `api/routers/runs.py` — endpoint `/performance` zawsze uruchamiał `OrdersIngestPipeline.run()` na `orders_path`; gdy orders załadowane z Datasetu, ścieżka wskazywała na `.duckdb` → pipeline crash
  - Naprawa: pattern identyczny jak w `/capacity` (linia 350) — sprawdzenie `orders_path.suffix == ".duckdb"` i load przez `DataStore().load()` zamiast pipeline
  - Pliki: `api/routers/runs.py:802-809`

- **Feature: Original filename tracking w runach**:
  - Nowe pola DB i ORM: `masterdata_original_filename`, `orders_original_filename` w `AnalysisRun`
  - Migration w `api/main.py` (lifespan ALTER TABLE) + schema SQLAlchemy + Pydantic `RunResponse` + TypeScript `RunDetail`
  - Ustawiane w 4 miejscach: `inspect_masterdata`, `masterdata_from_dataset`, `inspect_orders`, `orders_from_dataset`
  - `ImportTab.vue` — `mdFileName` i `ordersFileName` computed oparte teraz na `original_filename` zamiast parsowania ścieżki na dysku (usuwa problem z pełnymi ścieżkami serwera pokazywanymi użytkownikowi)
  - `ReportsTab.vue` — nowa karta "Source files" pokazująca nazwy wgranych plików masterdata i orders

- **Feature: Analysis running indicator w navbarze**:
  - Nowy store `frontend/src/stores/analysis.ts` — globalny stan `isAnalyzing` (start/stop)
  - `AppTopNav.vue` — animowana ikona emoji (🏃/💨/🚀/🔥) w navbarze podczas trwania analizy; cykl co 500ms z losowym wyborem; `Transition` fade-in/out; czyszczenie `setInterval` na `onUnmounted`
  - `CapacityTab.vue`, `ImportTab.vue` (6 operacji) — `analysis.start()` / `analysis.stop()` wokół wszystkich długich operacji API

- **Dane testowe: generator zleceń TechMag_SA**:
  - `tests_alan/generate_orders_client.py` — skrypt generujący 6 miesięcznych plików XLSX (`Zlecenia_2025_01..06`) w folderze `tests_alan/TechMag_SA/`
  - 800 unikalnych SKU (alfanumeryczne), sezonowość miesięczna, 6 typów zleceń, 1–7 linii/zlecenie
  - Łącznie ~61 500 wierszy zleceń w 6 plikach

- Branch: `main`

---

### [2026-05-05] - Feature (main)

- **Datasets — mapowanie kolumn przy imporcie**:
  - Nowy endpoint `POST /api/v1/datasets/inspect` — inspekcja pliku bez persystencji; zwraca kolumny, auto-sugestie mapowania, preview 5 wierszy i definicję schematu
  - Modyfikacja `POST /api/v1/datasets/import` — przyjmuje opcjonalny parametr `mapping_json` (JSON z mapowaniem target_field → source_column)
  - Nowe schematy: `DatasetColumnSuggestion`, `DatasetInspectResponse` w `api/schemas/dataset.py`
  - `DatasetsView.vue` — 2-krokowy wizard: Upload (wybór pliku + typ → inspect) → Mapping (dropdowny Required/Optional, preview tabeli, walidacja duplikatów i brakujących pól)
  - Frontend API: nowe typy `DatasetColumnSuggestion`, `DatasetInspectResponse`; nowa metoda `inspect()`; rozszerzony `import()` o opcjonalne `mapping`
  - Wsteczna kompatybilność zachowana — `mapping_json` jest opcjonalny

---

### [2026-05-04] - Feature + Fix + Refactor (main)

- **Datasets — warstwa persystencji plików masterdata/orders**:
  - Nowy model `Dataset` w DB z deduplikacją opartą na SHA-256
  - `api/routers/datasets.py` — endpointy: list, upload, delete, download
  - `frontend/src/views/DatasetsView.vue` — nowa strona Datasets z tabelą, notatkami, akcją delete
  - Możliwość re-importu tego samego pliku między sesjami; ulepszony komunikat błędu dla duplikatów nazw runów
  - Dataset selection w zakładce Import — wybieranie wcześniej załadowanego pliku zamiast ponownego uploadu
  - Fix 500 → 422 gdy plik masterdata brakuje na dysku

- **Tools tab z modułem Data Preparation**:
  - Nowa zakładka "Tools" w `RunView` z podmodułem Data Preparation
  - `frontend/src/components/analysis/ToolsTab.vue` (nowy komponent)

- **Fix: Dark mode — seria poprawek**:
  - Data Preparation view (tła, kolory tekstu, granice)
  - Datasets import form and list
  - ImportTab (Masterdata & Orders)
  - Select dropdown background; ujednolicenie kolorów empty state; usunięcie `line_id`
  - QualityTab dark mode

- **Refactor: Usunięcie Streamlit (PR #40)**:
  - Usunięto cały kod Streamlit — jedyny stack to FastAPI + Vue 3/Vite
  - Commit: `75a82bc`

- **Fix: Dashboard query performance (PR #41)**:
  - Partial select z DB zamiast pełnych obiektów + indeksy bazy danych
  - Usunięto martwe skany Polars, single-pass ABC dla Dashboard KPIs
  - Commit: `2a358d8`, `48c6504`

- **Feature: Toast notifications dla akcji (PR #42)**:
  - Powiadomienia toast dla: Notes, Delete, Share, Duplicate, Change password
  - Commit: `cd07e33`

- **Pliki testowe i generator dużych danych**:
  - Dodano `tests_alan/` — przykładowe pliki masterdata/orders do testów manualnych
  - Skrypt generujący duże zestawy danych (stress testing)

- Branch: `main`

---

### [2026-05-03] - Feature + Fix (main)

- **Performance — Throughput per Period KPIs**:
  - Nowa tabela "Throughput per Period" w zakładce Performance pokazująca avg/median/max dla zamówień, linii i sztuk per dzień, zmianę i godzinę
  - `src/analytics/performance.py` — `_median()` helper, 21 nowych pól w `PerformanceKPI` (9 per-day, 9 per-shift, 3 median per-hour), zaktualizowany `_calculate_kpi(shifts_per_day)`, przeniesiony blok `shifts_per_day` przed wywołanie KPI
  - `api/routers/runs.py` — serializacja wszystkich nowych pól KPI + `shifts_per_day` w `performance_result`
  - `frontend/src/api/runs.ts` — rozszerzony interfejs `PerformanceKPI` o 23 pola, `shifts_per_day` w `PerformanceResult`
  - `frontend/src/components/analysis/PerformanceTab.vue` — siatka KPI zaktualizowana (usunięto `Avg Lines/Hour` i `Peak Lines/Hour`, dodano `Avg Units/Order` i `P95 Lines/Hour`), nowa karta z tabelą throughput (kolumny per-hour ukryte gdy brak danych godzinowych)

- **Fix: runtime crash na starych wynikach Performance**:
  - Stare rekordy `performance_result` w DB nie zawierały nowych pól KPI → `undefined.toFixed()` TypeError zamrażał cały komponent Vue
  - `frontend/src/components/analysis/PerformanceTab.vue` — dodano `?? 0` fallback do każdego odwołania do nowych pól, np. `(pr.kpi.avg_units_per_order ?? 0).toFixed(1)`

- **Fix: brakujące powiadomienie "Analysis complete" w Performance**:
  - `PerformanceTab.vue` nie miał `useNotificationsStore` ani wywołania `notify.push()` wzorem `CapacityTab.vue`
  - `frontend/src/components/analysis/PerformanceTab.vue` — dodano import `useNotificationsStore`, instancję `notify`, wywołanie `notify.push({ type: 'success', title: 'Analysis complete' })` po `emit('refreshed')`

- **Feature: przełącznik Light/Dark mode w navbarze**:
  - `frontend/src/stores/theme.ts` — inicjalizacja uwzględnia `prefers-color-scheme` jako fallback gdy brak `localStorage`
  - `frontend/src/components/layout/AppTopNav.vue` — przycisk toggle z ikoną słońca (dark→light) / księżyca (light→dark), klasa CSS `.nav-theme-toggle` (28×28px, `border-radius: 6px`, hover effects)

- **Fix: usunięcie Dark Mode toggle z Settings**:
  - Sekcja "Appearance" w Settings stała się zbędna po dodaniu toggle do nawigacji
  - `frontend/src/views/SettingsView.vue` — usunięto sekcję Appearance, usunięto import `useThemeStore` i instancję `theme`

- Branch: `main`

---

### [2026-04-20] - Feature (main)
- **Order Line Distribution KPIs w sekcji Performance**:
  - Nowy wiersz kart KPI pokazujący rozkład liczby linii na zamówienie: 1, 2, 3, 4, 5, 6–10, 11–20, >20
  - `src/analytics/performance.py` — nowe pole `order_line_distribution` w `PerformanceKPIResult`
  - `src/ui/views/performance_results.py` — wyświetlanie drugiego wiersza KPI cards
- **Fix:** `getattr` fallback w `performance_results.py` — stare sesje bez `order_line_distribution` nie crashują po deployu
- **Fix:** zmiana `group_by/agg(pl.len())` → `value_counts()` (bardziej niezawodne na Streamlit Cloud)
- Branch: `main`

---

### [2026-04-20] - Feature (New_UI)
- **Apple Design System — pełna wymiana warstwy prezentacyjnej**:
  - `frontend/src/assets/main.css` — design tokens (`@theme`), globalne klasy (`btn-apple-primary`, `btn-apple-dark`, `btn-apple-pill`, `input-apple`, `input-apple-sm`, `label-apple`, `card-apple`, `card-apple-elevated`, `card-apple-list`)
  - `frontend/src/assets/base.css` — wyczyszczony (zastąpiony przez main.css)
  - `frontend/src/App.vue` — layout sidebar → block + sticky top nav, max-w-[980px], `route.meta.fullscreen` dla loginu
  - `frontend/src/components/layout/AppTopNav.vue` — **nowy komponent** — szklana nawigacja (rgba(0,0,0,0.82) + backdrop-filter), 48px, sticky
  - `frontend/src/router/index.ts` — `meta: { fullscreen: true }` dla `/login`
  - `frontend/src/components/shared/ToastContainer.vue` — toast `top: 60px` (clearance od 48px nava)
  - `frontend/src/views/LoginView.vue` — fullscreen centered, `card-apple-elevated`, max-w 380px
  - `frontend/src/views/DashboardView.vue` — Apple dashboard z pipeline steps, KPI cards, recent list
  - `frontend/src/views/RunsView.vue` — `card-apple-list`, `input-apple-sm`, `btn-apple-primary`
  - `frontend/src/views/RunView.vue` — underline tabs (border-bottom 2px #0071e3), `btn-apple-pill` akcje
  - `frontend/src/views/CarriersView.vue` — `card-apple`, `card-apple-list`, `input-apple-sm`
  - `frontend/src/views/SettingsView.vue` — `card-apple` sekcje, `input-apple`
  - `frontend/src/components/shared/AppToast.vue` — glassmorphism, dot status (●), bez colored border
  - `frontend/src/components/shared/StatusBadge.vue` — Apple rgba palette + dodanie `orders_ingested`
  - `frontend/src/components/shared/KpiCard.vue` — `card-apple`, 12px label, 28px value
  - `frontend/src/components/shared/HelpTip.vue` — `#1d1d1f` tooltip background
  - `frontend/src/components/analysis/NewRunModal.vue` — `card-apple-elevated`, `input-apple`
  - `frontend/src/components/analysis/NotesModal.vue` — `card-apple-elevated`
  - `frontend/src/components/analysis/ShareModal.vue` — `card-apple-elevated`, `input-apple`
  - `frontend/src/components/analysis/ReportsTab.vue` — `card-apple`, `btn-apple-dark`, `btn-apple-pill`
  - `frontend/src/components/analysis/ImportTab.vue` — `card-apple`, `btn-apple-primary`
  - `frontend/src/components/analysis/QualityTab.vue` — `card-apple-list`, `card-apple`, weekday bars Apple Blue
  - `frontend/src/components/analysis/CapacityTab.vue` — `card-apple`, Apple Blue Plotly charts, Apple system colors dla FIT/BORDERLINE/NOT_FIT
  - `frontend/src/components/analysis/PerformanceTab.vue` — `card-apple`, `#0071e3` Plotly bar charts, Apple heatmap
  - `frontend/index.html` — title "Vite App" → "Datavisor"
- Branch: `New_UI`

---

### [2026-04-19] - Feature (feature/fastapi-vue3-migration)
- **Sharing, notatki, ustawienia, walidacja zamówień — duży commit migracji**:
  - **Run sharing:** model `RunShare`, endpoint `POST /runs/{id}/share`, `ShareModal.vue`
  - **Notatki do runów:** `NotesModal.vue`, endpoint `PATCH /runs/{id}/notes`
  - **SettingsView:** nowy widok ustawień (`/settings`) z `AppSidebar.vue`
  - **Orders Validation:** nowy moduł `src/analytics/orders_validation.py` (277 linii) z testami
  - **API:** rozszerzone routery `runs.py`, `auth.py`, `reports.py` o share/notes/settings
  - **UI:** przeprojektowane `ImportTab`, `PerformanceTab`, `QualityTab`, `CapacityTab`, `DashboardView`, `RunsView`, `RunView`, `LoginView`
  - Nowe schematy: `RunShare`, `RunNotes`, rozszerzone `schemas/auth.py`
  - `pyproject.toml` — nowe zależności
- **Fix:** Excel scientific notation dla długich kodów SKU w eksporcie CSV z `CapacityTab`
- **Fix:** ZIP download — odpowiedź in-memory `Response` zamiast `FileResponse`; lepsze komunikaty błędów w `ReportsTab`
- **Fix:** `NameError` — zmiana typu zwracanego z `FileResponse` na `Response` w `download_zip`
- Branch: `feature/fastapi-vue3-migration`

---

### [2026-04-01] - Merge (feature/fastapi-vue3-migration → main)
- **PR #31 — scalenie migracji FastAPI+Vue3 do main**
  - Połączono branch `feature/fastapi-vue3-migration` z `main`
  - Rozwiązano konflikty w dokumentach `Dev/`
  - Dodano `.vite/` do `.gitignore` frontendu
- Branch: merge

---

### [2026-03-30] - Fix + Feature (feature/fastapi-vue3-migration)
- **Fix: błąd auto-detekcji jednostki wymiarów ×10**:
  - `src/ingest/units.py` — zaostrzenie progu detekcji CM: tylko gdy `median < 10` i `max < 50`, inaczej domyślnie mm
  - Wcześniej wartości dziesiątek/setek mm były błędnie mnożone ×10
- **Fix: błąd 422 w capacity analysis po załadowaniu zapisanego runu**:
  - `api/routers/runs.py` — `run_capacity` rekonstruuje `masterdata_mapping` przed uruchomieniem pipeline, gdy nazwy kolumn nie pasują do domyślnych schematu
- **Feature: selektor jednostki wymiarów w imporcie Masterdata (Streamlit)**:
  - `src/ui/views/import_view.py` — nowy selectbox `mm/cm/auto`, analogiczny do selektora jednostki wagi
  - Pozwala ręcznie wymusić `mm` gdy auto-detekcja błędnie interpretuje małe wartości jako cm
- **Fix: session_nav AttributeError po czyszczeniu cache Streamlit**:
  - Guard w callbacku `_on_nav_change` przed brakującym kluczem `session_nav`
- **Fix: SKU Pareto CSV — formatowanie `cumulative_pct` jako string procentowy**:
  - `api/routers/reports.py` — zapobieganie błędnej interpretacji kolumny przez Excel jako datę
- **Feature: ABC class cross-filter w zakładce Capacity (Vue3 frontend)**:
  - `frontend/src/components/analysis/CapacityTab.vue` — tabela cross-stats (unikalne SKU per klasa ABC vs FIT/BORDERLINE/NOT_FIT), filtr dropdown ABC, kolumna ABC w tabeli wyników i eksporcie CSV
  - Działa gdy dostępny jest wynik Performance Analysis dla tego samego runu
- **Feature: ABC class cross-filter w widoku Capacity (Streamlit)**:
  - `src/ui/views/capacity_view.py` — tabela cross-stats, filtr dropdownem, kolumna ABC w dataframe i CSV
- Branch: `feature/fastapi-vue3-migration`

---

### [2026-02-25] - Minor (feature/fastapi-vue3-migration)
- **Zmiana nazwy aplikacji z DataAnalysis na Datavisor**:
  - Zaktualizowano nazwę we wszystkich plikach kodu i dokumentacji (12 plików)
  - `api/main.py` — tytuł API
  - `api/database.py` — nazwa pliku bazy danych (`datavisor.db`)
  - `api/pdf_generator.py` — stopka raportu PDF
  - `frontend/src/App.vue` — navbar
  - `frontend/src/views/LoginView.vue` — nagłówek strony logowania
  - `pyproject.toml` — nazwa pakietu, autor, skrypt CLI (`datavisor`)
  - `src/__init__.py`, `src/core/config.py`, `src/core/types.py`, `src/ui/app.py` — docstringi
  - `src/reporting/readme.py` — nagłówek i stopka paczki raportów
  - `README.md` — nagłówek główny
- Branch: `feature/fastapi-vue3-migration`

---

### [2026-02-25] - Minor (main)
- **Per Day stats dla trybu bez danych godzinowych (Performance)**:
  - Problem: sekcja "Detailed Statistics" ukrywała tabele Orders/Order Lines/Pieces gdy plik nie zawierał kolumny czasu (`has_hourly_data = False`)
  - Przyczyna: warunek `if result.has_hourly_data and result.daily_metrics:` pomijał przypadek bez godzin
  - Rozwiązanie: dodano gałąź `elif result.daily_metrics:` wyświetlającą 3 tabele (Orders, Order Lines, Pieces) z kolumnami **Avg / Median / Min / Max** i wierszem "Per Day"
  - Przeniesiono pomocniczą funkcję `_fmt()` przed oba bloki `if/elif`
- Plik: `src/ui/views/performance_results.py`
- Branch: main (minor)

---

### [2026-02-20] - Minor (main)
- **Analiza frameworków UI — ocena alternatyw dla Streamlit**:
  - Zidentyfikowano 4 główne problemy z obecnym Streamlit: brak kontroli layoutu, ograniczone custom komponenty, powolne reruns, walka z CSS
  - Potwierdzenie problemu: `theme.py` ma 1179 linii (masowe CSS injektowanie)
  - Udokumentowano 3 alternatywy: Dash, FastAPI+Vue 3, Reflex — z oceną wysiłku migracji, kontroli UI, dojrzałości
  - Rekomendacja: Dash (100% Python, dojrzały, natywny Plotly) lub FastAPI+Vue (maksymalna swoboda)
- Utworzono `Dev/FRAMEWORK_MIGRATION_ANALYSIS.md` z pełną analizą i tabelami porównawczymi
- Pliki: `Dev/FRAMEWORK_MIGRATION_ANALYSIS.md` (nowy)
- Branch: main (minor — dokumentacja)

### [2026-02-19] - Feature (feature/ux-redesign)
- **UX Redesign — uproszczenie Capacity Validation UI**:
  - Zamiana progress barów walidacji na karty "Key Findings" i tabelę pokrycia danych
  - Uproszczenie Capacity Validation: usunięcie settings expandera, przycisku re-run, dodanie KPI cards
  - Zastąpienie `st.metric()` bloków w Orders Validation summary przez `render_kpi_section()` KPI cards
  - Usunięcie redundantnego nagłówka z Dashboard Executive Summary
  - Przeprojektowanie przycisków zakładek jako złote pill buttons; usunięcie wskaźników statusu
- **Drobne czyszczenie UI Capacity Validation**:
  - Usunięcie blue forward-guidance box ("Validation complete — proceed to the Analysis tab…")
  - Usunięcie noty "Outlier and Borderline detection has been moved to Capacity Analysis…"
  - Usunięcie zbędnego separatora `---` na końcu sekcji Validation help
- Pliki: `src/ui/views/capacity_validation_view.py`, `src/ui/views/performance_validation_view.py`, `src/ui/app.py`, `src/ui/theme.py`, `src/ui/layout.py`, `src/ui/views/dashboard_view.py`
- Branch: `feature/ux-redesign`

### [2026-02-17] - Minor
- **Zmiana na jasny motyw (Light Theme)**:
  - Zamiana ciemnego motywu (dark theme) na jasny (light theme) z zachowaniem złotego akcentu (`#c9a227`)
  - Nowe tła: beżowy `#f0ede8` (sidebar), prawie-biały `#faf9f6` (main), biały `#ffffff` (karty)
  - Nowy tekst: ciemny brąz `#2d2926` (główny), ciepły szary `#6b6560` (drugorzędny)
  - STATUS_COLORS: ciemniejsze warianty dla lepszego kontrastu na jasnym tle
  - Dostosowanie ~20 hardcoded `rgba()` w CSS (opacity 0.15→0.10, cienie 0.3→0.08)
  - Checkmark w pipeline indicator: zmiana koloru na biały
  - File uploader hover: jasny overlay `rgba(232, 217, 160, 0.2)`
  - Rename `apply_plotly_dark_theme()` → `apply_plotly_theme()` (6 plików)
- Pliki: `src/ui/theme.py`, `.streamlit/config.toml`, `src/ui/layout.py`, `src/ui/__init__.py`, `src/ui/views/capacity_view.py`, `src/ui/views/performance_view.py`, `src/ui/views/components_demo.py`
- Branch: main (minor)

### [2026-02-16] - Minor
- **Podmiana palety kolorów na ciepłą neutralną ze złotym akcentem**:
  - Zamiana kawowo-brązowej palety (coffee-bean `#20100e`, burnt-caramel `#b7622c`) na ciepłą neutralną (`#463f3a` base) ze złotym akcentem (`#c9a227`)
  - Nowe tła: `#2d2926` / `#463f3a` / `#544c46` / `#635b54`
  - Nowe akcenty: złoty `#c9a227` / `#a8861f` / `#6b5a2a`
  - Nowy tekst: kremowa biel `#f4f3ee`, jasny beż `#bcb8b1`
  - Zaktualizowano hardcoded `rgba()` w CSS (info-box, warning-box, file uploader hover)
  - STATUS_COLORS bez zmian (kolory funkcyjne)
- Plik: `src/ui/theme.py`
- Branch: main (minor)

### [2026-02-16] - Refactor
- **Ujednolicenie obsługi formatów numerycznych w pipeline**:
  - Nowy moduł `src/ingest/cleaning.py` z uniwersalną funkcją `clean_numeric_column()`
  - Obsługuje: europejski przecinek dziesiętny (`1,5`), notację naukową (`1,0E+0`), kropki jako separatory tysięcy (`1.234,56`)
  - Zastosowano w `pipeline.py` (kolumna `stock`) zamiast inline kodu
  - Zastosowano w `units.py` (wymiary `length/width/height` i `weight`) — wcześniej wartości jak `"1,5"` cicho stawały się `null`
  - 9 nowych testów w `test_ingest.py` pokrywających edge cases
- Branch: `feature/numeric-cleaning`

### [2026-02-12 20:00] - Feature
- **Eksport interaktywnych wykresów jako standalone HTML**:
  - Dodano przycisk "Download interactive HTML" pod każdym wykresem w zakładkach Analysis
  - Performance Analysis: 7 wykresów (throughput, daily activity, heatmap, weekly trend, day-of-week, SKU pareto, order structure)
  - Capacity Analysis: 3 wykresy (dimensions distribution, carrier fit, weight distribution)
  - Pliki HTML otwierają się w przeglądarce z pełną interaktywnością (zoom, hover, pan)
  - Wykorzystano wbudowany Plotly `fig.to_html()` z CDN — brak nowych zależności
- Pliki: `src/ui/layout.py`, `src/ui/views/performance_view.py`, `src/ui/views/capacity_view.py`
- Branch: feature/performance

### [2026-02-12 18:00] - Fix
- **Smart date gaps detection in Validation tab**:
  1. Infer working weekdays from data (weekdays appearing in >=20% of weeks)
  2. Classify missing dates into "workday gaps" (unexpected) vs "non-working days" (expected)
  3. Show breakdown: workday gaps as warning, non-working days as info
  4. Display detected working days pattern (e.g., "Mon, Tue, Wed, Thu, Fri")
  5. Show workday gaps table with date + weekday name
  6. Context rows now show only relevant columns (order_date, timestamp, sku, quantity) instead of full DataFrame
- Root cause: algorithm treated all calendar days as expected, so weekends (84 days) showed as "missing"
- File: `src/ui/views/performance_validation_view.py`

### [2026-02-12 17:30] - Fix
- **Per Shift calculation fixed** — was showing same values as Per Day
  1. Added `shifts_per_day` field to `PerformanceAnalysisResult`
  2. Compute from weekly schedule (max shifts on any working day) instead of counting shift types
  3. Use `result.shifts_per_day` in view instead of `len(result.shift_performance)`
- Root cause: `shift_performance` grouped by shift TYPE (BASE/OVERLAY), not by shift count
- Files: `src/analytics/performance.py`, `src/ui/views/performance_view.py`

### [2026-02-10 15:00] - Fix
- **Performance Validation View — UI/UX fixes after user testing**:
  1. Orders data summary: split 5 cramped columns into 2 rows of 3 columns
  2. Expandable tables (Missing SKUs, Quantity anomalies): show all imported columns instead of hardcoded 3
  3. Statistical outliers: replaced technical `(mean=X, std=Y)` with user-friendly message + caption explaining 3-sigma rule
  4. Working pattern profile: fixed N/A values — shifts defaults to 1 when `max_hour == min_hour`, fallback computes weekday from `order_date` if `weekday` column missing
- File: `src/ui/views/performance_validation_view.py`
- Branch: feature/performance

### [2026-02-10 14:00] - Feature
- **Performance Validation View — full implementation**:
  - Expanded Orders data summary: 5 metrics (added Unique SKUs, Unique days)
  - New section: Missing SKUs — detects null, empty, "N/A", "-", whitespace-only SKU values
  - New section: Date gaps — finds missing calendar dates between min/max order_date
  - New section: Quantity anomalies — null/zero, negative, and statistical outliers (>mean+3σ)
  - New section: Working pattern profile — active days/week, hours range, estimated shifts (only with hourly data)
  - Removed placeholder "under development" message
  - Pattern: main render function + private `_render_*` helpers (matches capacity validation style)
- File: `src/ui/views/performance_validation_view.py`
- Branch: feature/performance

### [2026-02-10 12:00] - Refactor
- **Rozdzielenie Capacity Validation i Performance Validation**:
  - Problem: `_render_performance_validation()` wywoływała `render_validation_view()` przeznaczoną dla Masterdata, co było błędne dla danych Orders
  - Rozwiązanie: Dwie niezależne walidacje:
    - `capacity_validation_view.py` z `render_capacity_validation_view()` - istniejąca logika Masterdata (bez zmian)
    - `performance_validation_view.py` z `render_performance_validation_view()` - nowy widok dla Orders (placeholder z podstawowymi statystykami)
  - Usunięto stary `validation_view.py`
- Zmiany w plikach:
  - `src/ui/views/validation_view.py` → usunięty
  - `src/ui/views/capacity_validation_view.py` → nowy (rename z validation_view.py)
  - `src/ui/views/performance_validation_view.py` → nowy (placeholder Orders validation)
  - `src/ui/views/__init__.py` → zaktualizowane importy
  - `src/ui/app.py` → zaktualizowane importy i wywołania
- Weryfikacja: 143 testy przechodzą
- Branch: feature/performance

### [2026-02-05 13:30] - Fix
- **Naprawa generowania raportów po uproszczeniu outlier detection**:
  - Problem: ZipExporter.export() wymagał `capacity_dq_result` który został usunięty
  - Raporty DQ_SuspectOutliers i DQ_HighRiskBorderline potrzebują szczegółów (field, value, details)
  - Rozwiązanie: DQListBuilder uruchamiany automatycznie podczas capacity analysis
  - `capacity_dq_result` przywrócony w session_state (generowany, nie konfigurowany przez UI)
- **Lekcja:** Przy refaktoringu sprawdzać moduły eksportu/raportowania!
- Branch: feature/capacity-location-metrics

### [2026-02-05 13:00] - Refactor
- **Usunięcie zbędnej logiki "Exclusion settings"**:
  - Problem: Po uproszczeniu outlier detection do carrier-based, zostały artefakty starego systemu
  - "Detect outliers" button był redundantny - analiza robi to samo automatycznie
  - "Exclusion settings" checkbox był bezcelowy - outliers i tak pokazują się jako NOT_FIT
  - Rozwiązanie: Usunięto oba, outliers widoczne w wynikach pod "Does not fit any carrier"
- Zmiany w plikach:
  - `src/ui/views/capacity_view.py`: Usunięto `render_data_quality_settings()`, dodano uproszczone `render_analysis_settings()`
  - `src/ui/app.py`: Usunięto `outlier_validation_enabled` z session_state
- Branch: feature/capacity-location-metrics

### [2026-02-05 12:00] - Refactor
- **Uproszczenie outlier detection - tylko rotation-aware z wagą**:
  - **Problem:** SKU 151×112×1225mm oznaczany jako outlier mimo że mieści się w nośniku po rotacji
  - **Stara logika:** Dwa mechanizmy: static thresholds + rotation-aware (konfliktujące)
  - **Nowa logika:** Outlier = SKU który nie mieści się w ŻADNYM aktywnym nośniku pod względem:
    - Wymiarów (z rotacją) - 6 możliwych orientacji
    - Wagi - musi być ≤ max_weight_kg nośnika
  - **Zero konfiguracji thresholds** - nośniki definiują limity
- Zmiany w plikach:
  - `src/core/dimension_checker.py`: Rozszerzenie `can_fit_any_carrier()` o parametr `weight_kg`
  - `src/quality/dq_lists.py`: Usunięcie `outlier_thresholds`, uproszczenie `_find_suspect_outliers()` do tylko rotation+weight check
  - `src/ui/views/capacity_view.py`: Usunięcie UI "Static thresholds", uproszczone wywołanie DQListBuilder
  - `src/ui/app.py`: Usunięcie inicjalizacji outlier threshold values z session_state
  - `tests/test_quality.py`: Zaktualizowane testy dla nowej logiki
- Korzyści:
  - Prostota - jeden spójny mechanizm zamiast dwóch
  - Poprawność - SKU które mieszczą się po rotacji nie są flagowane jako outliers
  - Pełna kontrola przez nośniki - dodanie wagi do sprawdzenia
- Branch: feature/capacity-location-metrics

### [2026-02-04 17:00] - Feature
- Ulepszenie obliczeń pojemności zgodnie z metodologią arkusza Excel:
  - **Nowa metryka: `locations_required`** - ile lokalizacji/nośników potrzeba dla danego SKU
    - Formuła: `ceil(stock_qty / units_per_carrier)`
  - **Nowa metryka: `filling_rate`** - współczynnik wypełnienia przestrzeni (0-1)
    - Formuła: `(stock_qty × sku_volume) / (locations_required × carrier_volume)`
    - Bliski 1.0 = optymalne wykorzystanie, < 0.5 = marnowanie miejsca
  - **Nowy tryb: "Best Fit"** - automatyczny wybór optymalnej lokalizacji
    - SKU przypisywany do nośnika z najwyższym filling rate
    - Minimalizacja marnowanej przestrzeni
- Zmiany w plikach:
  - `src/core/types.py`: Rozszerzenie `CarrierFitResult` o pola: `locations_required`, `filling_rate`, `stored_volume_L`, `carrier_volume_L`
  - `src/analytics/capacity.py`: Nowa metoda `_calculate_location_metrics()`, rozszerzenie `CarrierStats` o `total_locations_required` i `avg_filling_rate`, obsługa trybu `best_fit_mode`
  - `src/ui/views/capacity_view.py`: Nowy tryb analizy "Best Fit", nowe kolumny w tabeli wyników ("Locations Req.", "Filling Rate (%)"), rozszerzone statystyki per carrier
- Weryfikacja: Test jednostkowy potwierdza zgodność obliczeń z arkuszem Excel (SKU 100×80×60mm, stock 500szt → 14 lokalizacji, filling rate 71.4%)
- Branch: feature/capacity-location-metrics

### [2026-02-04 15:30] - Fix
- Poprawa kontrastu file uploadera:
  - Zmiana border z `1px dashed` na `2px dashed` z kolorem `accent_muted` (#5e3123)
  - Dodanie efektu hover z kolorem `accent` (#b7622c) i jaśniejszym tłem
- Konfiguracja motywu sidebara w `.streamlit/config.toml`:
  - Zachowana sekcja `[theme.sidebar]` z oficjalnie wspieranymi opcjami
  - Ostrzeżenia konsoli "Invalid color passed for widgetBackgroundColor..." to znany wewnętrzny problem Streamlit (zdeprecjonowane opcje, PR #10332), nie wpływają na funkcjonalność
- Pliki: `.streamlit/config.toml`, `src/ui/theme.py`
- Branch: main (fix)

### [2026-02-04 12:00] - Refactor
- Naprawa 110 błędów pyright type errors w całym codebase:
  - `src/core/types.py`: ShiftConfig akceptuje `str | time` dla start/end
  - `src/ingest/units.py`: `Sequence[float]` zamiast `list[float]` (covariance)
  - `src/ingest/sku_normalize.py`: `normalize_sku()` akceptuje `str | None`
  - `src/ingest/readers.py`: Poprawiony `max()` key, type narrowing dla file_type
  - `src/ingest/mapping_history.py`: Null guard dla `_cache`
  - `src/analytics/capacity.py`: Explicit ORIENTATIONS type, assert dla best_orientation, sorted key
  - `src/analytics/performance.py`: Bezpieczne wyciąganie dat z timestamp, int cast
  - `src/analytics/shifts.py`: Konwersja str→time dla ShiftInstance
  - `src/quality/dq_metrics.py`: int cast dla zero_count, negative_count, valid_count
  - `src/quality/dq_lists.py`: Null guard dla carriers
  - `src/quality/impute.py`: Bezpieczna konwersja do float z polars scalars
  - `src/model/orders.py`: Optional datetime dla date_from/date_to
  - `src/ui/views/performance_view.py`: Inicjalizacja zmiennych, explicit WeeklySchedule
- Dodano `pyrightconfig.json` z exclude dla `DataAnalysis_docs/`
- Wynik: 110 błędów → 0 błędów, wszystkie testy przechodzą (126 passed)
- Branch: refactor/move-outlier-detection-to-capacity → main
- Commit: c0073a8

### [2026-02-02 18:00] - Refactor
- Przeniesienie Outlier/Borderline detection z Validation do Capacity Analysis:
  - **Problem architektoniczny:** Validation używał carrierów z Capacity Analysis, co łamało zasadę niezależności kroków
  - **Błędny komunikat:** "max dimension 2740mm > max carrier axis 3650mm" był matematycznie fałszywy
  - **Rozwiązanie:** Outliers i Borderline są teraz wykrywane w Capacity Analysis z użyciem aktywnych carrierów
- Zmiany w plikach:
  - `src/quality/dq_lists.py`: Dodano `build_validation_lists()` i `build_capacity_lists()`
  - `src/quality/pipeline.py`: Usunięto parametry outlier/carriers, używa `build_validation_lists()`
  - `src/quality/validators.py`: Usunięto logikę outlier validation
  - `src/ui/views/validation_view.py`: Uproszczono - pokazuje tylko Missing/Duplicates/Conflicts
  - `src/ui/views/capacity_view.py`: Dodano sekcję "Data Quality Settings" z outlier/borderline detection
  - `src/ui/app.py`: Przeniesiono outlier settings, dodano `capacity_dq_result`
- Korzyści:
  - Czysta separacja - Validation nie zależy od carrierów
  - Logiczny przepływ - Outliers wykrywane w kontekście rzeczywistych carrierów
  - Rotation-aware check ma sens tylko z carrierami
- Branch: refactor/move-outlier-detection-to-capacity
- Issue: #8

### [2026-02-02 16:30] - Fix
- Naprawa wyświetlania Outliers count - pokazywanie unikalnych SKU zamiast wpisów:
  - Problem: Count pokazywał 22142 przy 17238 rekordach (każdy SKU może mieć wiele wpisów outlier)
  - Przyczyna: `len(dq.suspect_outliers)` liczył wpisy (items), nie unikalne SKU
  - Rozwiązanie: Zmiana na `len({item.sku for item in dq.suspect_outliers})`
- Pliki: src/ui/views/validation_view.py:144, src/ui/views/capacity_view.py:311
- Branch: main (minor fix)

### [2026-02-02 16:00] - Fix
- Naprawa ignorowania statycznych progów outlier dla wymiarów gdy skonfigurowane są carriery:
  - Problem: Zmiana progów (np. Width max = 1mm) nie miała efektu przy aktywnych carrierach
  - Przyczyna: Logika `if/else` pomijała static thresholds dla dimension_fields gdy carriers istniały
  - Rozwiązanie: Zmiana logiki na **ZAWSZE static thresholds + opcjonalnie rotation-aware**
  - Teraz static thresholds zawsze działają, a rotation-aware jest dodatkowym sprawdzeniem
- Pliki: src/quality/dq_lists.py:127-159, src/quality/validators.py:251-283
- Branch: main (minor fix)

### [2026-02-02 15:00] - Fix
- Naprawa wyświetlania Borderline count w Validation view:
  - Zmiana domyślnej wartości `borderline_threshold` z 0 na 2.0 w session_state.get()
  - Niespójność powodowała pokazywanie 0 borderline issues mimo wykrycia
  - Teraz zgodna z wartościami domyślnymi w capacity_view.py (2.0) i app.py (2.0)
- Weryfikacja przepływu outlier validation → capacity analysis:
  - Rotation-aware detection działa poprawnie (6 rotacji)
  - Outlier SKUs są poprawnie wykluczane z capacity analysis
  - Quality Score penalty (0.5/issue, max 30) działa poprawnie
- Plik: src/ui/views/validation_view.py:150
- Branch: main (minor)

### [2026-02-02 13:30] - Feature
- Rozszerzenie Pipeline Sidebar o status "in_progress" (pulsujące niebieskie kółko):
  - CAPACITY: Masterdata (mapping...), Validation (configuring...), Analysis (configuring...)
  - PERFORMANCE: Orders (mapping...), Validation (configuring...), Analysis (configuring...)
  - Warunki in_progress:
    - Masterdata/Orders: gdy `mapping_step == "mapping"` (użytkownik mapuje kolumny)
    - Validation: gdy użytkownik jest w zakładce Validation i nie ma jeszcze wyniku
    - Analysis: gdy użytkownik jest w zakładce Analysis i nie ma jeszcze wyniku
  - Dodano tracking aktywnej zakładki: `capacity_active_tab`, `performance_active_tab`
- Pliki: src/ui/app.py
- Branch: main (minor)

### [2026-02-02 11:45] - Feature
- Sidebar Status Pipeline - hierarchiczny widok statusu w sidebarze z wizualną timeline:
  - CAPACITY: Masterdata → Validation → Analysis
  - PERFORMANCE: Orders → Validation → Analysis
  - Wskaźniki statusu: zielone wypełnione (success), żółte puste (pending), pulsujące niebieskie (in_progress)
  - Pionowe linie łączące (zielone gdy krok powyżej ukończony)
  - Szczegóły kroków (np. "1,234 SKU loaded", "complete", "pending")
- Pliki: src/ui/theme.py (CSS ~60 linii), src/ui/layout.py (3 funkcje), src/ui/app.py (status functions + sidebar update)
- Branch: main (minor)

### [2026-02-02 10:15] - Minor
- Aktualizacja progów walidacji outlierów w sekcji Capacity - Validation:
  - Width max: 3650mm → 864mm
  - Height max: 3650mm → 500mm
- Naprawa validation_view.py - użycie OUTLIER_THRESHOLDS z config jako fallback zamiast zahardkodowanych wartości
- Pliki: src/core/config.py, src/ui/views/validation_view.py
- Commit: 0bbd52b

### [2026-02-01 15:30] - Refactor
- Poprawki layoutu sekcji Import (Column Mapping):
  - Data preview: expander na górze z ograniczoną szerokością (max 600px)
  - Progress bar: ograniczona szerokość (max 400px)
  - Column mapping: nowy dwukolumnowy layout (60% mapping / 40% summary)
  - Mapping summary: zawsze widoczne w prawej kolumnie (bez expandera)
  - Unmapped columns: zawsze widoczne pod Mapping summary (bez expandera)
  - Status kolumn (Done/Missing): węższe kolumny statusu [1:3] zamiast [1:4]
  - Weight unit dropdown: ograniczona szerokość (2/5 kontenera)
  - Przyciski: Back po lewej, Import wyrównany do prawej
- Pliki: src/ui/views/import_view.py, src/ui/theme.py
- Branch: refactor/desktop-layout-constraints

### [2026-02-01 14:30] - Refactor
- Dodanie ograniczeń szerokości layoutu aplikacji (Desktop Layout Constraints)
  - Główny kontener: max-width 1400px, wycentrowany
  - Komponenty formularzy: file uploader (600px), selectbox (400px), number input (200px), text input (400px)
  - Przyciski: naturalna szerokość z min-width 120px
  - Wykresy i tabele: 100% szerokości kontenera
  - Responsywność: pełna szerokość poniżej 1500px, komponenty 100% poniżej 768px
- Branch: refactor/desktop-layout-constraints

### [2026-02-01 12:00] - Minor
- Utworzenie pliku changelog.md do rejestrowania zmian w projekcie
- Dodanie zasady #9 do CLAUDE.md (Session Type First - ustalanie typu sesji na początku pracy)
- Branch/Commit: main
