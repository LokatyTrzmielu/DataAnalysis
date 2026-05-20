# Changelog

Rejestr zmian w projekcie Datavisor.

## Format wpisów
```
### [YYYY-MM-DD HH:MM] - Typ zmiany
- Opis zmiany
- Branch/Commit: nazwa_brancha lub hash commita
```

---

### [2026-05-20] - Feature (feature/help-extended-sections) — Help: grupowana nawigacja + przykłady obliczeń + 4 nowe sekcje

**Problem:** `HelpView.vue` miał ograniczoną szerokość (`max-width: 880px`), płaski 8-pozycyjny sidebar i opisywał tylko proces analizy. Brakowało: dokumentacji Datasets, Carriers, Tools › Data Preparation i Tools › Container Order; konkretnych liczb przy formułach (P90, Filling Rate, ABC, fit test); hierarchii w bocznym pasku porządkującej rosnącą listę sekcji.

**Co się zmienia (zmiana ogranicza się do jednego pliku — `frontend/src/views/HelpView.vue`):**
- **Sidebar — zwijane grupy z podsekcjami:** drzewo `navTree` (typ `NavNode { id, label, icon?, isGroup?, children? }`) zamiast płaskiej tablicy `sections`. Trzy grupy: Process (Import / Quality / Performance + 3 podsekcje / Capacity + 3 podsekcje / Reports), Data & Carriers (Datasets / Carriers), Tools (Data Preparation / Container Order). Overview, Sharing, Dashboard pozostają pojedynczymi pozycjami. Toggle przez kliknięcie nagłówka grupy; watcher na `activeSection` auto-rozszerza grupę zawierającą aktualną sekcję.
- **IntersectionObserver rozszerzony** o wszystkie podsekcje (id-y: `performance-kpi`, `performance-abc`, `performance-pareto`, `capacity-fit`, `capacity-loc`, `capacity-modes`). Rekurencyjny `collectAnchorIds` zbiera id-y do obserwacji.
- **Szerokość:** usunięty `max-width: 880px` z `.help-page` — strona korzysta z `max-w-[1400px]` z `App.vue`. Sidebar: 220 px, gap: 40 px. Sticky sidebar z `max-height: calc(100vh - 88px)` i własnym scrollem dla długich nawigacji.
- **Nowe komponenty stylistyczne:**
  - `.help-example-card` — zielona karta „EXAMPLE" z monospace pre-formatted body dla prostych wzorów (Coverage %, Filling Rate, P90).
  - `.help-steps-table` — siatka CSS-grid z zebra rows + wariantami `abc-grid` (5 kol.), `pareto-grid` (4 kol.), `fit-grid` (6 kol.), `prep-grid` (3 kol.) dla procesów wieloetapowych.
- **Przykładowe obliczenia z liczbami** dodane do Quality (Coverage 85.6 %, outlier 1200 mm > 840 mm, imputacja prefixu BOLT-M8), Performance (4.17 lines/order, P90 = 142 lines/h, ABC cuts at rank 142/418, top-10 = 31 %), Capacity (fit test 6 orientacji SKU 80×60×40 vs 100×70×50, Filling Rate 96.0 %, three-mode example).
- **Cztery nowe sekcje:** `#datasets` (workflow upload → inspect → map → save → use; kiedy używać vs Import bezpośredni), `#carriers` (pola, inner vs outer, przykład borderline_threshold), `#tool-data-prep` (merge N plików z różnymi nazwami kolumn; przykład 3 pliki × 5 000 wierszy → 14 982 unique SKU), `#tool-container-ord` (5-krokowa tabela: Best Fit → grupowanie → locations → konwersja → plan; tip o limicie 288 mm Kardex divider).
- **Inne:** Overview `flowSteps` rozszerzony z 5 do 7 (dodane Datasets + Carriers jako kroki 1–2). Access table w Sharing przeniesiona z inline-style do klasy `.help-access-table` (data-driven `v-for` po `accessRows`).

**Weryfikacja:** `npm run type-check` — clean dla `HelpView.vue` (dwa pre-existing TS errors w `PerformanceTab.vue` bez związku ze zmianą). Smoke test w przeglądarce na 1440 px, light + dark mode: layout 1400, auto-expand grupy po scrollu, manual toggle, aktywna podsekcja podświetlona, IntersectionObserver poprawnie śledzi `performance-pareto`, `capacity-fit`, `datasets` itp.

**Branch:** `feature/help-extended-sections`.

---

### [2026-05-20] - Feature (feature/dashboard-shifts-performance-kpi) — Dashboard: karty Shifts/day i Performance (lines/h)

**Problem:** Po dodaniu autodetekcji `shifts_per_day` + manual override (commit 5b4cec2) ta informacja była widoczna tylko w PerformanceTab, ale nie na głównym Dashboardzie. Nie było też szybkiego podglądu czy analiza performance była puszczona na całym pliku, czy na wybranych nośnikach (`data_scope`).

**Co się zmienia:**
- `frontend/src/views/DashboardView.vue`: w sekcji Orders dodane dwie nowe karty KPI **na pierwszej pozycji**:
  - **Shifts / day** — wartość z `perf.shifts_per_day` + podpis ze źródłem (`auto-detected` / `manual` / `from schedule`) z `perf.shifts_source`.
  - **Performance (lines/h)** — `perf.kpi.avg_lines_per_hour.toFixed(1)` + podpis ze zakresem analizy (`Entire file` lub `Carriers: <nazwy>`) na podstawie `perf.data_scope` i mapowania `capacity_result.carrier_stats[id].carrier_name`.
  - Dwa nowe computed-y: `shiftsSourceLabel`, `performanceScopeLabel`. Oba degradują się czysto dla starszych runów (brak `shifts_source` lub brak `data_scope` → fallback do `null` / `"Entire file"`).
- `frontend/src/api/runs.ts`: do interfejsu `PerformanceResult` dodane opcjonalne pola `productive_hours_per_shift?: number` oraz `data_scope?: { type: 'entire_file' | 'carriers'; carrier_ids: string[] }` — backend już je zapisywał (`api/routers/runs.py:1177-1181`), tylko typ TS się o tym nie wiedział.

**Brak zmian w:** backendzie (pola już istniały w `performance_result`), `PerformanceTab.vue`, schemach Pydantic, modelu `AnalysisRun`, żadnym innym widoku.

---

### [2026-05-20] - Refactor (refactor/container-order-simplify-ux) — Container Order: jeden przycisk + Advanced fold-out

**Problem:** Calculation tab miał 14 widocznych kontrolek (Mode/Goal/Preset dropdowny, 7 sliderów/togglów, manualny picker 48 wariantów). Trzyklasowa hierarchia `mode × goal × preset` była myląca; mało kto wiedział, kiedy „Auto + min_waste" działa inaczej niż „Guided + full_coverage". Tymczasem priorytety operacyjne są jasne i bezkonfliktowe: max Fill % → ~100% coverage → najmniej wariantów (niższy koszt zamówienia).

**Co się zmienia:**
- `src/analytics/container_planner.py`: `PlanParams.mode` defaultem `"guided"` (z `"auto"`), `PlanParams.guided_preset` defaultem `"full_coverage"` (z `"standard"`). Te wartości routują do istniejącego `_greedy_until_coverage`, który dokładnie realizuje priorytety usera.
- `api/schemas/container_order.py`: defaulty `PlanParamsRequest` zsynchronizowane z backendem.
- `frontend/src/api/containerOrder.ts`: `defaultParams()` zwraca `mode='guided'`, `guided_preset='full_coverage'`.
- `frontend/src/views/tools/ContainerOrderView.vue`: Calculation tab przebudowany — na górze widoczny tylko duży CTA „Calculate optimal plan →" + toggle „▸ Advanced". Wszystkie obecne kontrolki schowane w sekcji Advanced (collapsed by default) — bez utraty funkcjonalności.
- Nowy test `test_default_plan_params_route_to_full_coverage_greedy` w `tests/test_container_planner_params.py` — pinuje że `PlanParams()` bez argumentów produkuje plan z coverage ≥99% (lub orphany wyłącznie geometryczne) i ≤28 wariantów.
- `Dev/CONTAINER_ORDER_TOOL.md`: nowa sekcja „Domyślny przepływ" opisująca jeden-przycisk UX.

**Brak zmian w:** algorytmach planera (`_greedy_until_coverage`, `_greedy_set_cover`, `_best_variant_for_sku`, `_evaluate_selection`, `_compute_fits`, `_locations_needed`), schemacie odpowiedzi (`ContainerPlanResponse`), pozostałych tabach (Summary/Export/History), eksportach (Excel/PDF/CSV), wizualizacjach (VariantCard/Bin3DPreview). Tryb Manual nadal istnieje — dostępny w Advanced przez przełącznik Mode.

---

### [2026-05-20] - Fix (fix/kardex-dividers-288mm-limit) — Container Order: limit Dividers/Frames do 288 mm

**Problem:** Katalog Kardex VBM Box generował 6 tierów wysokości (138/188/238/288/**338**/**388** mm), ale Kardex fizycznie nie oferuje Dividerów ani ramek EasyClick powyżej 288 mm. Tiery 338 i 388 były błędem dokumentacji wprowadzonym 2026-05-19 (vide wpis przy commicie z 72 wariantami) i należało je usunąć z całego narzędzia.

**Co się zmienia:**
- `src/analytics/container_planner.py`: `HEIGHT_TIERS_MM = (138, 188, 238, 288)` (z `(138, 188, 238, 288, 338, 388)`). Katalog: **72 → 48 wariantów** (12 footprintów × 4 tiery); auto-katalog: **42 → 28** (7 × 4). Maks. wnętrze komory: 360 → 260 mm. Maks. `frames_per_bin`: 5 → 3.
- Testy w `tests/test_container_planner.py` i `tests/test_container_planner_params.py` zaktualizowane (asercje liczby wariantów, lista tierów, mapa frames, mapa wolumenu, docstringi). Stary `test_height_tiers_include_338_and_388` zastąpiony przez `test_height_tiers_exclude_above_288`.
- `Dev/CONTAINER_ORDER_TOOL.md` zaktualizowany (sekcja "Wysokości", liczby wariantów, przykład kodu wariantu).

**Brak zmian w:** frontendzie (data-driven — czyta `bin_height_mm` z odpowiedzi API), eksportach (Excel/PDF/CSV — agregują po wariantach), schematach Pydantic, logice dopasowania SKU. SKU które wymagały tierów 338/388 staną się transparentnymi orphanami z `orphan_reason='no_fitting_variant'`.

---

### [2026-05-20] - Feature (main) — Performance: autodetekcja `shifts_per_day` + manualny override w UI

**Problem:** w UI zawsze widniało `(2 shifts/day)`, niezależnie czy dane pokrywały 8/16/24 godzin. KPI per-shift (`Avg/Shift`, `Med/Shift`, `Max/Shift`) były dzielone przez stały dzielnik 2 — przy faktycznych 3 zmianach metryki były zawyżone o ~50%. Powód: `PerformanceAnalyzer` był zawsze tworzony bez `shift_schedule`, więc kod schodził do `else: shifts_per_day = 2`.

**`src/analytics/performance.py`:**
- Nowy helper `_detect_shifts_per_day(datehour)` — heurystyka: aktywna godzina = ta z sumą lini ≥ 10% max-godziny (sumując po wszystkich dniach); `shifts = ceil(active_hours / 8)`, clamp `[1, 3]`, fallback `2` dla pustego inputu. Odporna na overlap zmian i dipy lunchowe (mierzy realnie aktywne godziny, nie span).
- `PerformanceAnalyzer.__init__` przyjmuje nowy `shifts_per_day_override: Optional[int] = None`.
- `analyze()` zmienia kolejność: liczy `hourly/daily/datehour` najpierw, potem wybiera `shifts_per_day` w hierarchii **override → schedule → detected**. Source jest raportowane jako `"manual" | "schedule" | "auto"`.
- `PerformanceAnalysisResult` ma nowe pola `detected_shifts_per_day: int` i `shifts_source: str`.

**`api/routers/runs.py` → `POST /runs/{id}/performance`:**
- Nowy parametr formularza `shifts_per_day_override: Optional[int] = Form(default=None)`, walidacja `{1, 2, 3}` z `422`.
- Wartość trafia do analyzera i jest persystowana per-run w `run.analysis_config["shifts_per_day_override"]` (przeżywa reload, share, ponowne otwarcie).
- Response (`performance_result`) zawiera nowe pola `detected_shifts_per_day`, `shifts_source`.

**`frontend/src/api/runs.ts`:**
- `PerformanceResult` ma opcjonalne `detected_shifts_per_day` i `shifts_source: 'auto' | 'manual' | 'schedule'`.
- `runsApi.runPerformance(..., shiftsPerDayOverride: number | null = null)` — dodaje `shifts_per_day_override` do FormData gdy nie-`null`.

**`frontend/src/components/analysis/PerformanceTab.vue`:**
- Nowa kontrolka radio "Shifts per day" w "Analysis settings" (Auto / 1 / 2 / 3 shifts). Etykieta pokazuje auto-detected value gdy dostępne (`pr.detected_shifts_per_day`). Wartość początkowa hydrowana z `props.run.analysis_config.shifts_per_day_override` — wybór przeżywa reload.
- Nagłówek "Throughput per Period" rozszerzony o suffix: `· auto-detected` lub `· manual` zależnie od `pr.shifts_source`.
- `doRunAnalysis` przekazuje `shiftsPerDayOverride.value` do API.

**`tests/test_analytics.py`:**
- Nowa klasa `TestShiftsAutodetection` (10 testów): 2-zmianowy profile (06–21), 24/7 → 3, single shift (08–15) → 1, pusta lista / same zera → fallback 2, peak overlap nie psuje wyniku, próg 10% odrzuca szumowe godziny, override wygrywa z heurystyką (`shifts_source == "manual"`, `detected_shifts_per_day` raportuje co heurystyka by sama wybrała), brak override + brak schedule → `shifts_source == "auto"`.
- Wszystkie 10 testów przechodzi. 2 pre-existing failsy w `_calculate_kpi` (niezwiązane — brakuje `order_date` w fixture) zostają.

**Note dot. semantyki PER HOUR vs override:**
- Kolumny `Avg/Hr`, `Med/Hr`, `Max/Hr` są liczone z obserwowanych `(date, hour)` bucketów (`_calculate_kpi` → `lines_values = [dh.lines for dh in datehour]`), **nie** z `day / (shifts × productive_hours)`. Zmiana `shifts_per_day` nie zmienia tych liczb — to zachowanie zamierzone (PER HOUR opisuje obserwacje, nie teoretyczny dzielnik).
- Doprecyzowanie w UI: nagłówki grup w "Throughput per Period" mają teraz `title` tooltips wyjaśniające źródło każdej sekcji. Grupa "Per Hour" ma dodatkowo ikonkę `ⓘ` i `cursor: help` (nowa klasa CSS `.perf-group-th-info`).

---

### [2026-05-19] - UX (main) — Performance: kategoryczna oś LpO + sekcje w Throughput per Period

**`frontend/src/components/analysis/PerformanceTab.vue`:**
- Lines per Order Distribution Chart: wymuszony `xaxis.type: 'category'` + `categoryorder: 'array'` z `categoryarray` z bin labels. Powód: Plotly auto-parsował pierwsze 5 kubełków (`"1".."5"`) jako liczby i wyrzucał kategoryczne (`"6–10"`, `"11–20"`, …) — w efekcie wykres pokazywał tylko 5 słupków zamiast pełnego zestawu z kart KPI.
- Throughput per Period: dodany dodatkowy wiersz nagłówkowy "Per Day / Per Shift / Per Hour" (`colspan=3`) oraz pionowe separatory (`border-right` na ostatniej kolumnie każdej sekcji) zarówno w nagłówku, jak i w każdym wierszu (Orders/Lines/Pieces). Separator po Max/Shift renderuje się tylko gdy `has_hourly_data` (żeby nie wisiał na krawędzi tabeli). Kolumny `Avg/Day` … `Max/Hr` wyśrodkowane (`text-center`); kolumna `Metric` zostaje wyrównana do lewej.
- Dodane klasy CSS: `.perf-section-end` (pionowy separator) i `.perf-group-th` (drobny nagłówek grupy, uppercase, letter-spacing).

---

### [2026-05-19] - UX (fix/mapping-stock-bug) — Performance: etykiety wartości, hover dnia tygodnia, więcej kubełków LpO

**`frontend/src/components/analysis/PerformanceTab.vue`:**
- Wszystkie wykresy słupkowe (Daily Activity, Hourly Throughput, Weekly Trend, Day-of-Week Profile, Lines per Order Distribution) mają teraz stałe etykiety wartości nad słupkami (`textposition: 'outside'`, `cliponaxis: false`, drobny `textfont`). Górny margines podniesiony do 24 px, żeby etykiety się mieściły.
- Daily Activity: hover zmieniony z `data + lines` na `dzień tygodnia + lines` (`hovertemplate` z `customdata`). Data nadal widoczna na osi X, więc duplikacja w tooltipie była zbędna.

**`api/routers/runs.py`:**
- `lines_per_order_dist`: ostatni kubełek `21+` zastąpiony serią `21–30`, `31–40`, `41–50`, `51–60`, `61+`. Wykres i karty KPI używają tego samego źródła, więc liczba słupków = liczbie kart (12 zamiast 8).

---

### [2026-05-19] - Fix (fix/mapping-stock-bug) — Kolumna `stock` nie była mapowana na pole `stock`

**Root cause:** w `MASTERDATA_SCHEMA["sku"]["aliases"]` był alias `"stock_code"`. Algorytm `_find_best_match` (`src/ingest/mapping.py:297`) przetwarzał pola po kolei i dla pola `sku` partial-matchem łapał kolumnę `stock` (`"stock"` zawiera się w `"stock_code"` → score 0.5 ≥ 0.4 próg). Kolumna `stock` była konsumowana przez `sku`, więc pole `stock` zostawało w `missing_required`.

**Fix algorytmu — `src/ingest/mapping.py`:**
- Nowa metoda `_find_exact_match()` — szuka kolumny której znormalizowana nazwa równa się dokładnie aliasowi.
- `auto_map()` rozbity na trzy kroki: history → exact-match pass przez wszystkie pola → partial-match pass dla nieprzypisanych. Exact match dla `stock` → `stock` ląduje przed partial matchem dla `sku`.
- Usunięto alias `"stock_code"` z pola sku (defense in depth — pozostałe code-aliasy `item_code`, `product_code`, `part_code` pokrywają realne przypadki).

**Rozszerzenie słowników PL/EN w `MASTERDATA_SCHEMA` i `ORDERS_SCHEMA`:**
- **sku (masterdata + orders):** + `nazwa`, `nazwa_produktu`, `nazwa_towaru`, `indeks_handlowy`, `indeks_materialu`, `indeks_wewnetrzny`, `kod_wewnetrzny`, `kod_kreskowy`, `model`, `model_no`, `model_number`, `wariant`, `vendor_code`, `supplier_code`, `sap_code`, `iso_code`, `asin`, `manufacturer_code`, `materialnumber`, `articleno`, `artno`, `matnr`, `gtin`, `upc`, …
- **length/width/height:** + literówki (`lenght`), warianty osi (`bok_a`/`bok_b`/`bok_c`, `wymiar_a`/`b`/`c`), prefiksy (`outer_`, `pack_`, `box_`, `carton_`, `case_`), `karton_dlugosc`, `karton_szerokosc`, `karton_wysokosc`, `dlugosc_opakowania`, jednostki imperial (`length_inch`, `width_in`), `thickness`, `grubosc`, …
- **weight:** + `unit_weight_kg`, `unit_mass`, `wagajedn`, `waga_jedn`, `ciezar_jednostkowy`, `peso`, `pack_weight`, `box_weight`, `carton_weight`, `weight_lbs`, `weight_oz`, …
- **stock:** + `stan_mag`, `stany`, `stany_magazynowe`, `stan_aktualny`, `dostepnosc`, `do_wydania`, `wolne`, `wolny_stan`, `liczba_szt`, `liczba_sztuk`, `ilosc_w_mag`, `ilosc_w_magazynie`, `qty_on_hand`, `oh_qty`, `quantity_on_hand`, `quantity_in_stock`, `in_stock`, `current_stock`, `actual_stock`, `wms_stock`, `warehouse_stock`, `free_stock`, …
- **order_id:** + `numer_dokumentu`, `nr_dokumentu`, `dokumenty`, `pickorder`, `pick_id`, `wave`, `wave_id`, `wz`, `wz_nr`, `nr_wz`, `delivery`, `delivery_no`, `shipment`, `shipment_id`, `ship_no`, `release_id`, `zlecenie`, `nr_zlecenia`, `wydanie`, `wydanie_zewnetrzne`, `transakcja`, …
- **quantity:** + `ilosc_zamowiona`, `ilosc_skompletowana`, `ilosc_wydana`, `ilosc_dostarczona`, `qty_ordered`, `qty_shipped`, `picked_qty`, `delivered_qty`, `liczba_sztuk`, `wydane`, `skompletowane`, `each`, …
- **date:** + `data_utworzenia`, `data_zlozenia`, `data_zalozenia`, `data_dokumentu`, `data_kompletacji`, `data_wydania`, `data_transakcji`, `data_pickingu`, `data_zlecenia`, `dzien`, `creation_date`, `order_dt`, `dt`, `due_date`, `business_date`, …
- **time:** + `czas_zamowienia`, `godzina_zamowienia`, `godz`, `czas_realizacji`, `pick_time`, `creation_time`, `transaction_time`, …

**Testy regresyjne — `tests/test_ingest.py`:**
- `test_stock_column_not_stolen_by_sku_alias` — column `stock` ze schematem bez exact sku alias musi trafić na pole stock.
- `test_exact_match_wins_over_partial` — `stock`/`length`/`weight` zachowują dokładne dopasowanie nawet gdy sku nie ma exact matcha.
- Wszystkie 58 testów `test_ingest.py` przechodzi. 4 pre-existing fails na main (`test_analytics.py`, `test_api.py`) nie są związane z mapowaniem.

---

### [2026-05-19] - Feature (feature/dashboard-sidebar) — Sidebar przypięty do lewej krawędzi viewportu

Iteracja na poprzednim commitie: Sidebar przeniesiony z pozycji `sticky` wewnątrz kontenera `max-w-[1400px]` na `position: fixed` przy lewej krawędzi okna. Pełna wysokość ekranu pod nawigacją (top: 48 px → bottom: 100vh).

**`frontend/src/components/layout/DashboardSidebar.vue`:**
- `position: sticky; top: 12px` → `position: fixed; left: 0; top: 48px; height: calc(100vh - 48px); z-index: 50`.
- Usunięte: `border-radius: 12px`, `box-shadow` (sidebar dotyka krawędzi viewportu). Dodane: `border-right: 1px solid var(--app-border)` jako delikatny separator + subtelny cień 1 px po prawej (`box-shadow: rgba(0,0,0,0.04) 1px 0 3px`).
- Sidebar eksponuje swoją bieżącą szerokość przez CSS variable `--app-sidebar-w` na `document.documentElement` (264 px / 56 px). Wartość aktualizuje się przy zmianie `collapsed`, zapisuje przy `onMounted` i czyści w `onBeforeUnmount` (gdy użytkownik nawiguje poza Dashboard).
- Lista (`.sidebar-list`) bez zmian — flex `flex:1; overflow-y:auto; min-height:0` naturalnie wypełnia pełną wysokość.

**`frontend/src/router/index.ts`:**
- Dashboard route (`/`) dostaje `meta: { hasSidebar: true }`, dzięki czemu App.vue wie, kiedy zarezerwować lewy padding na sidebar.

**`frontend/src/App.vue`:**
- `<main>` używa `computed` `mainClass` / `mainStyle` zamiast inline class.
- Dla `route.meta.hasSidebar`: klasa `pr-6 py-8` (bez `mx-auto max-w-[1400px]`), inline style `padding-left: calc(var(--app-sidebar-w, 264px) + 24px)` z `transition: padding-left 0.25s ease`. Padding podąża za szerokością sidebaru w czasie animacji collapse/expand.
- Dla pozostałych route'ów: zachowane stare zachowanie (`mx-auto max-w-[1400px] px-6 py-8`).

**`frontend/src/views/DashboardView.vue`:**
- Usunięty zewnętrzny wrapper `display:flex; gap:24px` (sidebar jest teraz poza document flow). DashboardView renderuje tylko `<DashboardSidebar>` + zawartość bez dodatkowej kolumny.

**Skutek wizualny:**
- Sidebar pełnej wysokości (od dolnej krawędzi `AppTopNav` do dołu viewportu).
- Dashboard zyskuje przestrzeń: brak ograniczenia `max-w-[1400px]` — siatki KPI rozciągają się na pełną dostępną szerokość (minus sidebar i prawy margines).
- Z‑index: AppTopNav (100) > Sidebar (50), brak nakładania (sidebar startuje pod nawigacją).
- Smooth transition `padding-left` w głównej kolumnie + `width` w sidebarze, oba 0.25s.

**Weryfikacja:**
- `npx vue-tsc --noEmit` → exit 0.
- `npm run build` → ✓ built in 21 s, bez nowych ostrzeżeń.

---

### [2026-05-19] - Feature (feature/dashboard-sidebar) — Dashboard: zwijany Sidebar z listą analiz

Reorganizacja głównego ekranu Dashboard tak, by wybór analizy i przycisk „New Analysis" znalazły się w jednym, stałym miejscu po lewej stronie, a kolumna KPI odzyskała szerokość.

**Nowy plik `frontend/src/components/layout/DashboardSidebar.vue`:**
- Sticky, samodzielny aside; szerokość 264 px (rozwinięty) / 56 px (zwinięty), `transition: width 0.25s ease`.
- Header: pełnoszerokościowy przycisk „+ New Analysis" (rozwinięty) / okrągły niebieski guzik z ikoną „+" (zwinięty), pod nim chevron collapse/expand.
- Lista rozwinięta: identyczne wiersze jak dawna prawa kolumna (`client_name`, `StatusBadge`, data, ikonka Notes z rozwijanym `<textarea>` + debounced `runStore.patchRun`). Klik → emit `select`. Double‑click → emit `open(id, tab)`.
- Lista zwinięta: kolorowe awatary 32 px (1. litera client_name, kolor z hashu nazwy → paleta Apple), zaznaczenie przez 2 px ring `#0071e3`, tooltip `client_name · data`. Notes ukryte.
- Persistencja stanu collapsed w `localStorage['dashboard.sidebar.collapsed']`.

**`frontend/src/views/DashboardView.vue`:**
- **Usunięto** 3 kafle Quick actions u góry (New Analysis / History / Carriers) — Historia i Carriers są w `AppTopNav`, „New Analysis" przeniesione do sidebaru.
- **Usunięto** prawą kolumnę „Recent analyses" (310 px) wraz z lokalną obsługą `showModal`, `openNotesId`, `dashboardNotesTimer`, `toggleNotes`, `onDashboardNotesInput`, `selectRun`, `formatDate`, `tabFromStatus` — wszystko przeniesione do sidebaru.
- Layout: nadrzędny `display:flex; gap:24px; align-items:flex-start`; sidebar po lewej, główna kolumna `flex:1; min-width:0`.
- `latestRun` z lokalnego `ref` → `computed(() => runStore.currentRun)` (single source of truth). `selectedId` to `runStore.currentRun?.id`.
- Selekcja w sidebarze → emit `select` → `runStore.fetchRun(id)` → KPI grids reagują automatycznie.
- Modal „New Analysis" otwiera się z sidebaru; emit `created(id)` → `router.push('/runs/' + id)`.

**Poszerzone siatki KPI** (odzyskana szerokość po usunięciu prawej kolumny):
- Capacity: `grid-cols-2 sm:grid-cols-3` → `grid-cols-2 sm:grid-cols-3 lg:grid-cols-6` (6 kafli w 1 wierszu przy `lg`+).
- Orders: `grid-cols-2 sm:grid-cols-4` → `grid-cols-2 sm:grid-cols-4 lg:grid-cols-6`.
- Masterdata (2 kafle) i SKU Cross‑validation — bez zmian.

**Decyzje projektowe** (potwierdzone z użytkownikiem przed wdrożeniem):
- Zakres: tylko Dashboard (sidebar nie wchodzi do `App.vue` / globalnej nawigacji).
- Tryb zwinięty: wąski pasek ikon (~56 px), nie pełne ukrycie.
- Szerokość strony: globalny `max-w-[1400px]` w `App.vue` zostaje bez zmian.

**Weryfikacja:**
- `npx vue-tsc --noEmit` → exit 0.
- `npm run build` → ✓ built in 22.7 s, brak nowych ostrzeżeń (pre-existujące chunk-size dla `RunView` / `ContainerOrderView` bez zmian).

**Out of scope:**
- Globalny sidebar na wszystkich widokach, mobile drawer, drag-to-resize, pinowanie/reordering analiz.

---

### [2026-05-19] - Fix (main) — Container Order: 6-orientation SKU fit check (matches Capacity)

User asked whether the planner tests all 6 SKU orientations. It didn't — `_sku_fits_variant` only checked 2 (horizontal rotation, height pinned to vertical). Long-and-thin SKUs (cables, profiles, sheets) that would fit when laid flat were silently orphaned.

**`src/analytics/container_planner.py`:**
- New `ORIENTATIONS` tuple (mirrors `capacity.py`) — all 6 permutations of `(L, W, H) → (cell_X, cell_Y, cell_Z)`.
- New `_allowed_orientations(constraint)` filters by per-SKU constraint: `UPRIGHT_ONLY` → 2 orientations (H on Z); `FLAT_ONLY` → 4 orientations (H off Z); `ANY` / `None` → all 6.
- `_sku_fits_variant` rewritten to iterate over allowed orientations and return `True` if any fits. Height vs `cell_height_mm` is no longer a hard pre-filter — a tall SKU that's short on another axis now passes via lay-flat.
- `_compute_fits` reads `row.get("orientation_constraint") or "ANY"` and threads it through.

**`src/analytics/capacity.py`:**
- Forwards `orientation_constraint` (the input DataFrame value, default `ANY`) into every emitted result row dict, both in the FIT/BORDERLINE path and the NOT_FIT marker row.
- Added `orientation_constraint: pl.Utf8` to the explicit DataFrame schema so the column survives serialisation.
- No change to fit logic — Capacity already does 6 orientations.

**Backwards compatibility:**
- Older `capacity_result` blobs without the new column → planner defaults to `"ANY"` → 6-orientation check → strict superset of previous behaviour. Nothing that previously fit becomes an orphan; some previously-orphaned SKUs now find variants.
- `orientation_constraint` not surfaced in API schema, frontend types, or exports — internal decision only.

**Tests** in `tests/test_container_planner_params.py` (+5 new, 99 passed total):
- `test_long_thin_sku_fits_via_lay_flat_orientation` — SKU 100×100×400 fits 1/2L-138 (305×411×110) via lay-flat (height → cell Y axis).
- `test_upright_only_constraint_blocks_lay_flat` — same SKU with `UPRIGHT_ONLY` orphans correctly (h=400 > 360 = max cell height).
- `test_flat_only_constraint_forces_lay_flat` — SKU that fits upright but also flat; constraint filters to flat-only orientations.
- `test_orientation_constraint_missing_defaults_to_any` — older row (no key) behaves identically to explicit `ANY`.
- `test_height_no_longer_hard_pre_filter` — tall SKU that fits in `max_coverage` auto mode via lay-flat across the catalog.

**Docs:**
- `Dev/CONTAINER_ORDER_TOOL.md` — new *"Test 6 orientacji SKU"* section with the constraint table.
- `Dev/CONTAINER_ORDER_PARAMS_AUDIT.md` — new *"Geometric fit check (orientations)"* row.

---

### [2026-05-19] - Fix (main) — Container Order: geometry/weight model + NOT_FIT pass-through + params_echo clarity

User clarified the Kardex VBM Box spec and reported two transparency issues. Fixed in one pass:

**Catalog geometry (`src/analytics/container_planner.py`):**
- Interior: 611 × 411 (was 617 × 408 — too long, too narrow).
- Floor loss: 28 mm (was 10 mm). Interior heights now 110 / 160 / 210 / 260 / 310 / 360 mm.
- Height tiers extended: `(138, 188, 238, 288, 338, 388)` — dividers + frames now go all six tiers (previous "dividers stop at 288" turned out to be over-conservative). Catalog: 48 → **72 variants**; auto subset: 28 → **42**.
- `FOOTPRINTS` cell L/W rebuilt as integer floor of `611/n` and `411/n` (1/1 = 611×411, 1/4 = 305×205, 1/24 = 101×102, etc.).

**Weight model:**
- New constants: `BIN_GROSS_MAX_KG = 35.0`, `BIN_TARE_KG = 2.35`, `BIN_NET_MAX_KG = 32.65`. Per-cell proportional cap is now computed on the **net** 32.65 kg of usable stock weight, not gross. By induction this keeps the gross bin weight (stock + tare) ≤ 35 kg.
- `BIN_MAX_WEIGHT_KG` kept as deprecated alias that resolves to `BIN_NET_MAX_KG` for external callers.
- New `VariantSummary.bin_gross_weight_kg` field — avg full bin weight including tare. Mirrored in `api/schemas/container_order.py` and `frontend/src/api/containerOrder.ts` for the SKU table and exports.
- Frames assumed weightless (documented in `Dev/CONTAINER_ORDER_TOOL.md`) pending Kardex data.

**NOT_FIT pass-through (the user's bug report):**
- `_filter_skus` no longer silently drops `NOT_FIT` rows. The upstream Capacity analysis tests against a single MiB inner-dimension set (`carriers.yml` `inner_height_mm: 210`) but VBM Box has six height tiers — a SKU between 211–360 mm tall used to vanish at the filter. Now passes through to the per-variant check; SKUs that don't fit any variant in the catalog become **transparent orphans** with `orphan_reason="no_fitting_variant"`.
- `include_borderline` keeps its meaning: OFF drops BORDERLINE-classified rows; ON includes them alongside FIT and NOT_FIT.

**`params_echo` clarity in `ContainerOrderView.vue`:**
- Replaced the flat `paramsEchoDisplay` with two computed groups: **"Active in this calculation"** + **"Stored from a previous mode — not used in this calculation"**. Mode-conditional keys route based on the current `mode`: `auto_max_variants` (auto), `guided_preset` (guided), `manual_variant_codes` (manual). Everything else is always active. The unused group is muted with an amber left border.

**Tests:**
- Recalibrated 5 existing tests (catalog size 48 → 72, auto 28 → 42, tier list, weight cap 35 → 32.65, 1/6 proportional cap 5.8 → 5.4 kg).
- 8 new tests in `tests/test_container_planner_params.py`: interior dims, tier extension, volume table cross-check, tare reduces cell cap, gross bin weight surfacing, NOT_FIT-with-fitting-variant pass-through, NOT_FIT-with-no-variant transparent orphan, `include_borderline` semantic preservation.
- Full suite: **94 passed** (40 planner + 26 param + 28 time-saving).

**Docs:**
- `Dev/CONTAINER_ORDER_TOOL.md` rewritten spec section to match the new geometry, weight model, and NOT_FIT handling.
- `Dev/CONTAINER_ORDER_PARAMS_AUDIT.md` `include_borderline` row marked ✅, new row for the removed NOT_FIT gate.

---

### [2026-05-18] - Feature (main) — Container Order: parameter audit + UI gap fixes + regression tests

User reported that flipping scenarios in the Calculation tab didn't change the result. A full audit found three legitimate "looks broken but isn't" causes; each is now visible to the user.

**Verification artefact:** `Dev/CONTAINER_ORDER_PARAMS_AUDIT.md` — per-parameter table with file:line for every consumption site, plus a *"What looks broken but isn't"* explainer for the three ⚠ rows.

**UI fixes in `frontend/src/views/tools/ContainerOrderView.vue`:**
- **`include_borderline` toggle** — added in row 1 next to *Only Machine* / *Impute missing*. The parameter was wired correctly in `_filter_skus` (`container_planner.py:315`) but had no UI control; the store always sent the default `true`. Defaults to ON.
- **Inert-mode hint** — under the ABC checkboxes and inline next to *Only Machine*, shown when `currentRun.has_performance === false`. Explains that both filters are silently no-ops without Performance data (lenient-mode branch at `container_planner.py:317`).
- **`params_echo` reveal** — collapsible *"Parameters actually used by the planner"* fold-out under the Planning results summary. Renders `plan.params_echo` as a 2-column key/value grid so the user can verify what the backend actually acted on. Helpful when an inert combination silently skipped a filter.
- New CSS: `.hint-inert`, `.params-echo`, `.params-echo-grid` — amber-coloured hint copy and monospace echo table.

**Regression coverage in `tests/test_container_planner_params.py` (new, 18 tests):**
- One *effect* test per parameter (13 tests) — proves the planner output actually changes when the parameter changes.
- Three *documented no-op* tests pinning the inert combinations: `auto_max_variants` outside `mode="auto"`; `abc_classes` without performance data; `only_machine` without performance data. If anyone "fixes" these branches later, the no-op tests will flag the change for review.
- The `guided_preset` test uses a homogeneous two-SKU fixture so `full_coverage`'s early-stop beats `standard`'s k=8 ceiling — proving the two presets route to different algorithms even though they share a catalog.

**No backend behaviour changed.** Every parameter was already wired correctly *for the cases it applies to*; the fix was making the cases visible.

Full suite: 86 passed (40 planner + 18 new + 28 time-saving).

---

### [2026-05-18] - Fix (main) — Container Order PDF: column widths + procurement on one page

- **Order summary** column widths re-balanced to the actual rendered text width at 9 pt Helvetica (verified via `reportlab.pdfbase.pdfmetrics.stringWidth`). New widths: Variant 2.5 → fits `1/12_3x4-288`; Footprint 3.4 (Paragraph cell, wraps if a label still overflows); Cell (mm) 2.4 → fits `617×408×128`; Locs/bin 1.8; SKU 1.2; Locations 2.1; Bins 1.3; Avg fill 1.9. Total 16.6 cm vs 17.0 cm A4-portrait usable — small breathing room kept on purpose.
- Horizontal padding tightened from 5 → 4 pt and explicit MIDDLE vertical alignment added so wrapped footprint cells line up with the single-line numeric cells.
- **Procurement breakdown** now wraps its heading + table in `KeepTogether`, so ReportLab forces a page break before it if the current page can't fit the whole element. Eliminates the half-on-page-1, half-on-page-2 splits the user was seeing.

---

### [2026-05-18] - Feature (main) — Container Order SKU table: add Bins + Pcs/location

- `Assignment` (planner) and `AssignmentRow` (Pydantic + TS) gained `pcs_per_location: int`. Formula: `ceil(stock_qty / locations)` where `stock_qty = stock_volume_L / unit_volume_L` — the operationally meaningful number of pieces planned per allocated cell. Zero for orphans (no variant) or rows with missing dimensions.
- Planner (`_plan_from_selection`) now derives `unit_vol_L` once and reuses it for both `pcs_per_location` and the per-variant weight sum (was computed twice before).
- Frontend `SkuAssignmentTable.vue` — new columns inserted right after **Variant** (Pcs/loc) and right after **Locations** (Bins). Colgroup widths rebalanced to 10 cols; orphans render "—" in Pcs/loc.
- Excel export `_sheet_sku_assignment` — `Pcs/location` column inserted after Variant, blank string for orphans so spreadsheet sorts cleanly.
- 2 new planner tests: the user's worked example (1520 pcs / 152 locations = 10 pcs/loc) is now an explicit invariant + orphans must read 0.

---

### [2026-05-18] - Fix (main) — Container Order PDF: split cramped "Order summary" into two tables

- 12-column "Order summary" in `api/pdf_generator.py` :: `generate_container_order_pdf` was too dense on A4 portrait — column headers were truncating and rows wrapped unpredictably. Replaced with two tables, each with its own TOTAL row:
  1. **Order summary** — Variant, Footprint, Cell (mm), Locs/bin, SKU, Locations, Bins, Avg fill.
  2. **Procurement breakdown** — Variant, Bins, Bases, Frames, Dividers.
- Dropped the standalone `Height` column (height is encoded in the variant code, e.g. `1/4-188`, and present in the Excel sheet).
- Font bumped 8 → 9 pt, padding 4 → 5 px now that each table has room to breathe.
- Smoke-tested via in-process render: 41 KB PDF, no ReportLab errors.

---

### [2026-05-18] - Feature (fix/capacity-csv-carrier-name) — Time saved: cover Container Order + Data Preparation

**New event types in `api/services/time_saving.py`:**

- `container_order_run` — recorded on every `POST /tools/container-order/calculate/{run_id}`. Estimate: **60 min base + 25 min / 1 000 SKUs + 3 min / variant**, capped at 8 h. Manual equivalent: hand-building the 48-variant Kardex VBM catalog and VLOOKUP-mapping each SKU to a best-fit footprint × height. Context: `sku_count`, `variant_count`.
- `container_order_exported` — recorded on every `POST /tools/container-order/export/{run_id}`. Estimate: **20 min base + 10 min / sheet** (xlsx 4, pdf 2, csv 1). Context: `sheet_count`.
- `data_preparation_merge` — recorded on every `POST /tools/data-preparation/merge`. Estimate: **25 min base + 5 min / file + 3 min / 1 000 merged rows**. Manual equivalent: opening N spreadsheets, aligning headers, concat + dedup in Excel / Power Query. Context: `file_count`, `row_count`.

**Service plumbing:**

- `calculate_manual_seconds` learned three new scale knobs: `variant_count`, `file_count`, `sheet_count`. Same opt-in pattern as the existing `per_*` keys — rules without them are unaffected.
- `_pick_scale_value` now considers the new keys when persisting a representative scale_value for later inspection.
- `EVENT_LABELS` gained user-facing labels for the three new events ("Container Order — plan calculation" etc.).

**Routers:**

- `api/routers/container_order.py`: `calculate_plan` records the run event after the plan is computed (uses `plan.total_sku_planned` + `len(plan.summaries)`); `export_plan` records the export event with the format's sheet count.
- `api/routers/tools.py`: `merge_files` records the merge event right after the dataset is committed, using the file count and merged row count.

**UI:**

- `frontend/src/components/settings/TimeSavedCard.vue` — the "How time is estimated" popover now lists Data Preparation, Container Order — plan calculation (with 8 h cap note), Container Order — export, and the previously-missing Data quality Excel export line.

**Tests:**

- `tests/test_time_saving.py` — 4 new unit tests covering both base+scale arithmetic and the 8 h cap on `container_order_run`. Full file: 28 passed.

**Why this entry sits on `fix/capacity-csv-carrier-name`:** the user asked to bundle the time-saving extension with the in-flight Container Order weight-enforcement work and ship in one push.

---

### [2026-05-18] - Fix (fix/capacity-csv-carrier-name) — Container Order: bin-weight enforcement + Dividers column

**Bin-total weight cap is now enforced via stacking-aware per-cell weight check (`src/analytics/container_planner.py`):**

- Existing per-unit weight check at `_sku_fits_variant` rejected SKUs whose single-unit weight exceeded `max_weight_kg_per_cell` (proportional cap: `35 kg × cell_area / usable_bin_area`). But many lightweight units could still stack in a cell and exceed the proportional cap — silently breaking the 35 kg bin limit.
- `_locations_needed()` now optionally takes `unit_vol_L` and `unit_weight_kg`. When both are provided, it computes `n_weight = ceil(total_stock_weight / max_weight_kg_per_cell)` and uses `max(n_vol, n_weight)`. By induction every cell respects its proportional cap ⇒ every physical bin stays under 35 kg.
- `_compute_fits()` passes the new args through; signature defaults preserve backwards compatibility with any external callers.
- New tests: `test_locations_needed_bumps_when_stacking_exceeds_weight_cap`, `test_locations_needed_unchanged_when_weight_within_cap`, `test_plan_bin_total_weight_stays_under_cap`.

**Dividers column added across Summary + every export:**

- `VariantSummary` (and `VariantSummaryRow` schema) gained `dividers_required` (= `bins_required × locations_per_bin`) and `total_weight_kg` (Σ of `stock_qty × unit_weight` across SKUs assigned to the variant).
- `_plan_from_selection()` accumulates per-variant weight as assignments are processed; uses `stock_volume_L / unit_vol_L` as the unit count.
- Frontend `ContainerOrderView.vue`: new "Dividers" column between Frames and Fill; TOTAL row uses a `totalDividers` computed property. Small caption under the hero counter clarifies the bin weight cap and points to xlsx/csv for the per-variant total weight.
- Exports:
  - CSV (`_generate_summary_csv`): `dividers` + `total_weight_kg` columns appended; TOTAL row sums both.
  - Excel (`_sheet_order_summary`): new "Dividers" and "Total weight (kg)" columns; TOTAL row updated.
  - PDF (`generate_container_order_pdf`): new "Dividers" column; total_weight intentionally omitted to keep the table within A4 portrait width (column widths trimmed; total now 14.9 cm). Excel/CSV remain the authoritative per-variant weight source.
- New test: `test_variant_summary_dividers_required_equals_bins_times_locations`.

---

### [2026-05-18] - Fix (fix/capacity-csv-carrier-name) — Capacity_Results CSV: carrier_id → carrier_name

W `api/routers/reports.py` kolumna `carrier_id` w eksporcie *Capacity_Results* (single CSV + ZIP bundle) zastąpiona przez `carrier_name` zawierającą czytelną nazwę nośnika. Nowy helper `_capacity_rows_with_carrier_name()` mapuje ID → nazwę używając `carrier_settings` zapisanego w `capacity_result` (fallback do `carrier_stats.carrier_name` dla starszych runów). Specjalny marker `"NONE"` (SKU nie pasuje do żadnego nośnika) renderuje się jako *"Does not fit any carrier"*. Kolejność kolumn zachowana — `carrier_name` pojawia się w miejscu starego `carrier_id`. Frontend Capacity Tab eksport (`CapacityTab.vue::exportCsv`) ma już obie kolumny, nieruszony.

---

### [2026-05-18] - Fix (fix/pdf-rename-units-to-pieces) — PDF: "Units" → "Pieces"

W `api/pdf_generator.py` 10 user-facing labelek w sekcjach *Totals / Hourly Throughput / Daily / Per Shift* przemianowanych z `Units` na `Pieces` (np. *Avg Pieces / Order*, *Peak Pieces / Hour*, *Max Pieces / Shift*). Klucze KPI (`total_units`, `avg_units_per_hour` itp.) i import `reportlab.lib.units` nietknięte — to wewnętrzne identyfikatory danych. Spójność z istniejącymi już Pieces w sekcji *Pareto Concentration* (Pieces/Day, Cumul.Pieces%).

---

### [2026-05-18] - Fix (fix/dq-value-and-full-csv) — backfill DQ value, pełne CSV qty, animacja czołgu na Reports

**Value column dla istniejących runów (`api/routers/reports.py` + `api/routers/runs.py`):**

- Poprzednia poprawka populowała `value` w `quality_result` tylko dla nowych runów. Istniejące runy nadal pokazywały pustą kolumnę `value` w arkuszu *MD - Suspect Outliers* (i innych MD - *).
- Dodany helper `_quality_result_needs_value_backfill()` wykrywa stare wpisy bez `value`. `_maybe_backfill_quality_result()` przeładowuje masterdata przez nowy `_load_masterdata_df()` (mirror `_load_orders_df` — dataset .duckdb lub raw plik z user-confirmed mapping) i re-runuje `QualityPipeline`, zapisując świeżą `quality_result` do DB.
- Backfill odpalany jest w trzech miejscach: `/reports/xlsx`, `/reports/csv/DQ_*`. Po pierwszym pobraniu Excel/CSV stara run dostaje swoje `value` zapisane na stałe.

**Pełne listy CSV — usunięcie 100-row cap dla qty issues (`src/analytics/orders_validation.py` + `api/routers/reports.py`):**

- `OrdersValidator._check_quantity_anomalies()` nadal zapisuje **sampled preview** (max 100 wierszy) do JSON-a `orders_validation_result` (żeby kolumna nie puchła).
- Nowy module-level helper **`compute_qty_issue_rows(df, issue, limit=None)`** wykonuje ten sam filtr (null / zero / negative / outlier ≥ mean+3σ) na świeżym orders DataFrame **bez żadnego cap**.
- CSV endpointy `/reports/csv/Orders_QtyNull|Zero|Negative|Outliers` przeładowują orders df i wywołują `compute_qty_issue_rows` bez limitu — eksport zawiera teraz wszystkie dotknięte wiersze. Fallback do JSON-owego preview, jeśli przeładowanie się nie uda.
- Masterdata DQ CSV są pełne od początku (`DQListBuilder` nie ma cap-a) — backfill wystarczy żeby `value` pojawiło się dla starszych runów.
- Nowe testy: `TestComputeQtyIssueRows::test_returns_all_zero_rows_no_cap` (250 wierszy bez przycinania), `test_limit_honoured`, `test_outlier_threshold_matches_validator`.

**Animacja czołgu podczas eksportów (`frontend/src/components/analysis/ReportsTab.vue`):**

- Wszystkie cztery handlery downloadu (ZIP / PDF / Excel / per-CSV) wywołują teraz `useAnalysisStore.start()` przed requestem i `stop()` w bloku `finally`, dokładnie jak `CapacityTab` / `ImportTab`.
- Ikona czołgu w `AppTopNav` (`nav-tank` z klasą `is-shooting`) animuje się przez cały czas pracy backendu — szczególnie ważne dla backfillów Quality Pipeline / OrdersValidator, które mogą trwać kilka sekund.

**Tests**: `tests/test_orders_validation.py` (31) + `tests/test_quality.py` (32) green.

**Branch**: `fix/dq-value-and-full-csv` (jeszcze nie zmergowany).

---

### [2026-05-18] - Fix (fix/dq-excel-and-orders-csv) — Excel value column, gap consistency, qty backfill, Orders CSVs

**Excel (`api/dq_excel_generator.py` + `api/routers/runs.py`):**

- Kolumna **value** w arkuszach MD - * była pusta — `runs.py` serializował tylko `{sku, field, details}`, gubiąc `value` z `DQListItem`. Oba miejsca persistujące `quality_result` (`/quality` + `/masterdata/from-dataset`) zapisują teraz `value`. Dla istniejących runów wartość będzie pusta do następnego Quality Check.
- **Trzy arkusze Summary scalone w jeden** — `Summary` zawiera teraz trzy sekcje (Info / Masterdata / Orders) jako pasy nagłówkowe, zamiast oddzielnych zakładek.

**Spójność Date Gaps (`src/analytics/orders_validation.py`):**

- `gap_list` było wcześniej przycinane do 20 najdłuższych przerw (sort by days desc → `[:20]`), przez co Summary pokazywał `gap_count=40` a arkusz `Orders - Date Gaps` miał tylko 20 wierszy. **Cap usunięty** — pełna lista przerw trafia do JSON-a i Excel.
- Dodane pole **`total_gap_days`** (suma dni przerw) i pokazane w sekcji Orders w Summary, żeby od razu odróżnić *liczbę przerw* od *liczby dni w przerwach*.

**Qty Outliers — brakujące wiersze dla starszych runów (`api/routers/reports.py`):**

- Run z `qty_outlier_count=5486` ale pustym `qty_outlier_rows` (bo `orders_validation_result` powstał zanim feature wylądował) — endpoint `/reports/xlsx` wykrywa teraz brak nowych pól (`qty_*_rows`, `total_gap_days`) i **automatycznie re-runuje** `OrdersValidator` na bieżącym orders df, zapisując świeży wynik do DB.
- Helper `_maybe_backfill_orders_validation()` szanuje gate cross-validation (masterdata bez `masterdata_mapping` i bez `quality_result` → bez auto-mappingu).

**Reports tab — 5 CSV per sekcja (`frontend/src/components/analysis/ReportsTab.vue` + `api/routers/reports.py`):**

- **Masterdata Issues**: usunięty przycisk *DQ Summary*. Zostaje 5 przycisków: Missing Critical / Suspect Outliers / High Risk Borderline / Duplicates / Conflicts.
- **Orders Issues**: tekst podsumowania zastąpiony **5 przyciskami CSV** (jak Masterdata): Date Gaps / Qty Null / Qty Zero / Qty Negative / Qty Outliers. Backend dostał 5 nowych typów raportów w `CSV_REPORTS` + `_ORDERS_REPORT_TO_FIELD`, kolumny `order_id, sku, order_date, order_hour, quantity`.
- CSV endpointy dla orders qty również wywołują backfill, jeśli pole `qty_*_rows` jest puste a count > 0.

**Tests**: `tests/test_orders_validation.py` (28) + `tests/test_quality.py` (32) green.

**Branch**: `fix/dq-excel-and-orders-csv` (jeszcze nie zmergowany).

---

### [2026-05-18] - Fix (fix/reports-excel-and-cross-validation) — SKU cross-validation gate + rozbudowa Excel DQ

**Bug fix: `src/analytics/orders_validation.py` `_check_sku_crossvalidation`**

- Cross-validation SKU (Orders ↔ Masterdata) odpalała się również, gdy plik Masterdata został wgrany, ale **Quality Check nie został jeszcze wykonany** — `OrdersValidator` ładował wtedy masterdata przez `MasterdataIngestPipeline` z heurystycznym auto-mappingiem kolumn, co potrafiło błędnie wskazać kolumnę typu `Material` jako SKU i wygenerować bezsensowne listy Unknown/Inactive SKUs (widoczne także w pliku Excel).
- Fallback do auto-detekcji został **usunięty**. Cross-validation rusza wyłącznie gdy spełniony jest jeden z dwóch warunków:
  1. caller dostarczył już załadowany `masterdata_df` (np. dataset z potwierdzonym mappingiem), albo
  2. caller przekazał `masterdata_path` **wraz z** jawnym `masterdata_mapping` (czyli użytkownik przeszedł przez Quality Check i potwierdził mapowanie).
- W przeciwnym wypadku zwracane jest `sku_xval_available=False` z zerowymi listami — UI i Excel pokazują wtedy „N/A" zamiast halucynacji.
- Test regresyjny: `tests/test_orders_validation.py::test_path_without_mapping_skips_cross_validation` + `test_explicit_masterdata_df_enables_cross_validation`.

**Excel DQ — rozbudowa (`api/dq_excel_generator.py`, `src/analytics/orders_validation.py`):**

- Pojedynczy arkusz `Summary` zastąpiony trzema zakładkami:
  - **Info** — meta (Generated by, Client, Run ID, źródła plików, status Quality Check / Orders validation).
  - **Summary - Masterdata** — KPI sekcji masterdata (gdy `quality_result` istnieje).
  - **Summary - Orders** — KPI sekcji orders (gdy `orders_validation_result` istnieje).
- Dodane zakładki **per-issue dla Orders**: `Orders - Qty Null`, `Orders - Qty Zero`, `Orders - Qty Negative`, `Orders - Qty Outliers` (każda zawiera kolumny `order_id`, `sku`, `order_date`, `order_hour`, `quantity` z dotkniętymi wierszami, z notką o truncacji do 100 wierszy).
- `OrdersValidator._check_quantity_anomalies` zwraca teraz dodatkowo `qty_null_rows`, `qty_zero_rows`, `qty_negative_rows`, `qty_outlier_rows` (po max 100 wierszy każda) — pole jest backwards-compat, starsze runy z pustym JSONem dają puste listy.
- Test regresyjny: `tests/test_orders_validation.py::test_sample_rows_collected_per_issue`.

**Branch**: `fix/reports-excel-and-cross-validation` (jeszcze nie zmergowany).

---

### [2026-05-18] - Feature (feature/portable-static-serving) — Reports: split DQ + Excel + PDF Performance-only + Generated by

**Frontend (`frontend/src/components/analysis/ReportsTab.vue`, `frontend/src/api/runs.ts`):**

- Sekcja **Data Quality CSV reports** rozbita na dwie karty: **Masterdata Issues** (6 dotychczasowych CSV) i **Orders Issues** (skrócony przegląd licznikowy: gap_count, missing_sku_count, qty anomalies, unknown/inactive SKUs).
- Dodano przycisk **Download Excel** obok ZIP/PDF — wywołuje nowy endpoint `GET /api/v1/runs/{id}/reports/xlsx`.
- Przycisk **Download PDF** odblokowany również dla runów z samym performance_result (wcześniej wymagał capacity_result). `disabled` = `!(capacity_result || performance_result)`.
- Hint pod przyciskami zaktualizowany: ZIP nadal wymaga capacity; PDF działa dla capacity / performance / obu; Excel pokrywa DQ.

**Backend (`api/pdf_generator.py`, `api/routers/reports.py`, `api/dq_excel_generator.py` *nowy*, `api/services/time_saving.py`):**

- `generate_capacity_pdf(...)` akceptuje teraz `capacity_data: dict | None`. Sekcja Capacity (KPI + carrier settings + carrier breakdown + capacity charts) jest pomijana, gdy `capacity_data is None`. Tytuł nagłówka dobiera się dynamicznie: *Capacity & Performance Report* / *Capacity Report* / *Performance Report*.
- Pasek metadanych w PDF: zamiast `Run ID: <uuid>` jest teraz `Generated by: <name> <email>`. PDF generator dostał parametr `user`, a `download_pdf` przekazuje `current_user`.
- W trybie performance-only PDF startuje od razu od nagłówka *Performance Analysis* bez wymuszonego `PageBreak` (uniknięcie pustej strony 1).
- Gate w `GET /api/v1/runs/{id}/reports/pdf` poluzowany: 422 tylko gdy brak zarówno capacity, jak i performance results.
- Nowy generator `api/dq_excel_generator.py` (openpyxl, wzorowany na `excel_generator.py` dla Container Order). Jeden workbook z arkuszami:
  - `Summary` — dane runa + KPI Masterdata + KPI Orders;
  - `MD - Missing Critical`, `MD - Suspect Outliers`, `MD - Borderline`, `MD - Duplicates`, `MD - Conflicts` (gdy istnieje `quality_result`);
  - `Orders - Date Gaps`, `Orders - Unknown SKUs`, `Orders - Inactive SKUs` (gdy istnieje `orders_validation_result`).
- Nowy endpoint `GET /api/v1/runs/{id}/reports/xlsx` zwraca tego xlsx. Wymaga przynajmniej jednego z: `quality_result`, `orders_validation_result`.
- `TIME_SAVING_RULES`/`EVENT_LABELS` rozszerzone o `report_exported_xlsx` (25 min/eksport).

**Branch**: `feature/portable-static-serving` (jeszcze nie zmergowany).

---

### [2026-05-18] - Feature (feature/portable-static-serving) — wersja Portable Windows aplikacji

Branch: `feature/portable-static-serving` · commits `45be975`, `9d9ce89`, `1e198a2`, `13756e4`, `33e332f`, `7d24d67` (jeszcze nie zmergowany).

**Dodano w iteracji 2 (po pierwszym smoke teście u użytkownika):**

- **Fix `13756e4`**: Start.bat health-probe `localhost` → `127.0.0.1` (+ `TimeoutSec` 1→2). Na Windowsie z domyślnym `hosts`, `localhost` rozwiązuje się najpierw na IPv6 (`::1`), uvicorn nasłuchuje tylko na IPv4 — `Invoke-WebRequest -TimeoutSec 1` nie zdąży zfailować i przełączyć się. Skutek był taki, że Start.bat krzyczał "serwer nie wystartowal" mimo że uvicorn działał poprawnie. Przeglądarki radzą sobie z fallbackiem, dlatego app był dostępny od razu.

- **Fix `33e332f`**: 4 błędy TypeScriptowe wyłapane przez pierwsze faktyczne `vue-tsc --build` (Vite dev je pomijał, więc nigdy nie wypłynęły). Wszystkie zachowawcze: brakujący type import `PerformanceParetoBand` w `PerformanceTab.vue`, guard na `undefined` w `DatasetsView.duplicateColumns.includes()`, hoist+early-return z `selectedFiles.value[0]` w `DataPreparationView.doInspect()`. Build vite v7 + tsc strict przechodzi czysto, output zawiera świeży chunk `ContainerOrderView` (550 KB) który nigdy nie był dotąd w `dist/`.

- **Feature `7d24d67`**: flaga `-CodeOnly` w `Dev/Build-Portable.ps1`. Pomija download Pythona, get-pip i `pip install` (sekcje 2-6), robi tylko robocopy `api`/`src`/`frontend\dist` do `app/` + regenerację `Start.bat`/`Stop.bat`/README. Workflow iteracyjny: `npm run build; .\Dev\Build-Portable.ps1 -CodeOnly` (~20 s zamiast ~10 min, bez network I/O). Wymaga że paczka już istnieje (sprawdza obecność `runtime\python\python.exe`, w przeciwnym razie rzuca błąd z hintem żeby uruchomić pełny build z `-Force`).

**Iteracja 1 (wcześniej tego dnia):**

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
