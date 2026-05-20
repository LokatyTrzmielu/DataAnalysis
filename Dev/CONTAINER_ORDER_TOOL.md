# Container Order Tool — Kardex VBM Box

Drugi kafelek w **Tools**. Generuje listę zamówieniową pojemników (warianty + ilości)
dla SKU z ukończonej analizy, wykorzystując nośnik MiB 640×440.

Plan implementacyjny: `C:\Users\roszc\.claude\plans\zapoznaj-si-z-cryptic-blanket.md`.

## Co robi narzędzie

Bierze:
- ukończoną analizę (status `capacity_done` lub `performance_done`),
- która zawiera nośnik MiB 640×440 (`carrier_id == "2"` w `capacity_result.carriers_analyzed`).

Daje:
- listę wariantów pojemników (footprint × wysokość) i liczbę sztuk każdego,
- przypisanie SKU → wariant,
- listę SKU bez przypisania ("orphans"),
- eksport Excel (4 arkusze) / PDF (2 strony) / CSV.

## Źródło prawdy dla katalogu

Plik PDF `Dev/Calculators/Flyer_PL_Kardex-VBM-Box.pdf` (Kardex VBM Box flyer) + uściślenia od użytkownika z 2026-05-19:

- Pojemnik bazowy: **640 × 440 × 138 mm** (zewn.), wnętrze **611 × 411 × 110 mm**, ok. 27.6 L, gross max 35 kg.
- Waga pustego pojemnika (tare): **2.35 kg** → użyteczna nośność stocka per bin = **32.65 kg**.
  (Założenie: ramki EasyClick traktujemy jako 0 kg do czasu uzyskania danych z Kardex.)
- Dno bina pochłania **28 mm** wysokości (`bin_height − interior_height`).
- System EasyClick: każda ramka dodaje **+50 mm** w pełni użytecznej wysokości wnętrza.
- Wysokości: 138 / 188 / 238 / 288 mm → wnętrze 110 / 160 / 210 / 260 mm.
- Dividery i ramki EasyClick istnieją tylko do 288 mm — wyższych konfiguracji Kardex nie oferuje (potwierdzone 2026-05-20). Wcześniejszy zapis o tierach 338 / 388 był błędem dokumentacji.

## Katalog wariantów

12 footprintów × 4 wysokości = **48 wariantów (pełny katalog, tryb Manual)**.
7 footprintów oznaczonych jako "auto" → **28 wariantów (tryby Auto i Guided)**.

Wymiary komór (długość × szerokość, integer floor z `611/n` i `411/n`):

| Footprint   | Komora (L×W) | Komór | Auto |
|-------------|--------------|------:|:----:|
| `1/1`       | 611 × 411    |  1    | ✓ |
| `1/2L`      | 305 × 411    |  2    | ✓ |
| `1/2W`      | 611 × 205    |  2    | ✓ |
| `1/3W`      | 611 × 137    |  3    | ✓ |
| `1/3L`      | 203 × 411    |  3    |   |
| `1/4`       | 305 × 205    |  4    | ✓ |
| `1/6_3x2`   | 203 × 205    |  6    | ✓ |
| `1/6_2x3`   | 305 × 137    |  6    |   |
| `1/8`       | 305 × 102    |  8    |   |
| `1/12_3x4`  | 203 × 102    | 12    | ✓ |
| `1/12_6x2`  | 101 × 205    | 12    |   |
| `1/24`      | 101 × 102    | 24    |   |

Waga maksymalna na komorę = `32.65 kg × (pole_komory / pole_wnętrza_bin)` — czyli proporcjonalny cap nakłada się na **netto** stockową nośność, nie brutto.

Po obliczeniu planu `VariantSummary.bin_gross_weight_kg` raportuje średnie **brutto** (stock per bin + tare 2.35 kg) — pozwala zweryfikować, że 35-kg cap jest respektowany w eksportach.

Wewnętrzna wysokość komory = `bin_height_mm − 28` (utracone na dno).

Kody wariantów: `{footprint}-{bin_height_mm}` — np. `1/4-188`, `1/24-288`.

## Test 6 orientacji SKU (2026-05-19)

Wcześniej `_sku_fits_variant` testował tylko **2 orientacje** (rotacja w płaszczyźnie poziomej, wysokość SKU zawsze pionowo). Capacity analysis sprawdza **6 orientacji** (wszystkie permutacje L/W/H → X/Y/Z). Od 2026-05-19 Container Order również testuje 6 orientacji, respektując ograniczenie z masterdata:

| `orientation_constraint` | Dozwolone orientacje | Liczba |
|---|---|---:|
| `ANY` (domyślnie) | wszystkie permutacje (L,W,H) → (cell_X, cell_Y, cell_Z) | 6 |
| `UPRIGHT_ONLY` | tylko te z H na osi Z (cell_height) — "ta strona do góry" | 2 |
| `FLAT_ONLY` | tylko te z L lub W na osi Z — SKU musi leżeć płasko | 4 |

Pole `orientation_constraint` żyje w `MasterdataRow` (`src/core/types.py:81-84`) i jest forwardowane przez `capacity_result.rows` do planner'a. Starsze runy bez tego pola domyślnie używają `ANY` (= 6 orientacji), co jest najszerszym i najbezpieczniejszym domyślnym zachowaniem.

Praktyczna konsekwencja: SKU typu "kabel/profil/blacha" (long-and-thin), które wcześniej stawały się orphan-ami, teraz znajdują wariant przez lay-flat orientation. Sztywne "ta strona do góry" SKU (zaznaczone w masterdata) nadal respektują swoje ograniczenie.

Wybrana orientacja używana jest **wewnętrznie** do decyzji o dopasowaniu — nie pojawia się w SKU table ani exportach (decyzja użytkownika 2026-05-19).

## Filtrowanie SKU vs. capacity NOT_FIT (2026-05-19)

Wcześniejsza wersja `_filter_skus` cicho odrzucała SKU oznaczone w analizie Capacity jako `NOT_FIT`. Capacity testuje wymiary przeciwko **jednemu** zestawowi `inner_*_mm` carriera MiB z `carriers.yml`, a VBM Box ma sześć tierów wysokości — SKU "nie pasujące" do standardowego tieru mogłyby pasować do wyższego. Od 2026-05-19:

- `_filter_skus` przepuszcza wszystkie wiersze (FIT, BORDERLINE, NOT_FIT) do `_compute_fits`.
- Decyzję o "fitness" podejmuje per-wariant check (`_sku_fits_variant` + `_locations_needed`) wobec rzeczywistych wymiarów komór wariantów.
- SKU, które nie pasują do żadnego wariantu w katalogu, lądują jako transparent orphans z `orphan_reason="no_fitting_variant"`.
- Toggle `include_borderline` zachowuje swoje znaczenie (FIT vs BORDERLINE), nie dotyczy NOT_FIT.

## Decyzje projektowe (z dyskusji z użytkownikiem)

1. **ABC Pareto = filtr + wizualizacja, nie modyfikator matematyki.**
   Stock jest już w masterdata; mnożenie ABC×N to podwójne liczenie. ABC steruje
   *kogo planujemy* (np. tylko A+B do VBM), nie *ile pojemników na SKU*.

2. **Analiza pozostaje generyczna.** Sub-layouty są specyfiką VBM Box → należą do
   narzędzia, nie do `capacity_result`. Żadna modyfikacja analizy nie była konieczna.

3. **`stock_current` jako baza planowania.** Szanujemy decyzje klienta z masterdata.
   Dla porównania scenariuszy avg/max → osobna analiza.

4. **3D z dzielnikami** (three.js, parametryczne) — bez kostek SKU w środku.

5. **Trzy tryby**: Auto (domyślny) / Guided / Manual.

## Architektura

### Backend

```
src/analytics/container_planner.py     ← algorytm, katalog (CATALOG_AUTO / CATALOG_FULL)
api/schemas/container_order.py         ← Pydantic (PlanParamsRequest, ContainerPlanResponse, …)
api/routers/container_order.py         ← 4 endpoint'y pod /api/v1/tools/container-order
api/excel_generator.py                 ← openpyxl, 4-sheet Excel
api/pdf_generator.py                   ← rozszerzony o generate_container_order_pdf
```

#### Endpoint'y

| Method | Path                                                    | Opis |
|--------|---------------------------------------------------------|------|
| GET    | `/api/v1/tools/container-order/catalog`                 | pełny katalog 48 wariantów + lista kodów auto |
| GET    | `/api/v1/tools/container-order/eligible-analyses`       | analizy z carrier "2", dla zalogowanego usera |
| POST   | `/api/v1/tools/container-order/calculate/{run_id}`      | oblicza `ContainerPlanResponse` z `PlanParamsRequest` |
| POST   | `/api/v1/tools/container-order/export/{run_id}`         | xlsx / pdf / csv blob |

### Frontend

```
frontend/src/api/containerOrder.ts                 ← klient axios
frontend/src/stores/containerOrder.ts              ← Pinia store
frontend/src/components/VariantCard.vue            ← top-down SVG kafelek wariantu
frontend/src/components/Bin3DPreview.vue           ← three.js, base + frames + dividers
frontend/src/components/SkuAssignmentTable.vue     ← paginowana tabela 100/stronę
frontend/src/views/tools/ContainerOrderView.vue    ← 5-stepowy wizard
frontend/src/views/ToolsView.vue                   ← aktywacja 2. kafelka (linie 32-50)
frontend/src/router/index.ts                       ← trasa /tools/container-order
```

## Algorytm `plan_containers`

1. **Filtr SKU**:
   - tylko wiersze `capacity_result.rows` z `carrier_id == "2"`,
   - tylko `fit_status ∈ {FIT, BORDERLINE}` (jeśli `include_borderline`),
   - filtr ABC (jeśli `performance_result.sku_pareto` dostępne),
   - filtr `recommendation == "Machine"` (jeśli włączony i SKU znany perfowi).

2. **Per SKU**: dla każdego wariantu z aktywnego katalogu sprawdź czy się mieści
   (dwie orientacje: L×W i W×L) i czy waga ≤ `max_weight_kg_per_cell`.
   Policz wymagane lokacje:
   `ceil(stock_volume_L × multiplier / cell_volume_L / fill_rate)`,
   ograniczone do `[min_loc, max_loc]`.

3. **Set cover (tryb Auto)**: greedy — w każdym kroku dodaj wariant, którego
   marginalna poprawa względem celu (min_waste / min_bins / max_coverage) jest
   największa. Stop przy `auto_max_variants`.

4. **Tryb Guided**:
   - `simple` → 3 footprinty (1/1, 1/4, 1/6_3x2) × 2 wysokości (188, 288) = 6 wariantów.
   - `standard` → greedy z 8 wariantami, cel `min_waste`.
   - `full_coverage` → greedy do osiągnięcia 99% coverage lub 28 wariantów.

5. **Tryb Manual**: użyj tylko `manual_variant_codes` przekazanych z UI.

6. Każdy SKU → najlepszy z wybranych wariantów per cel (tiebreak: wyższe wypełnienie).
   Niedopasowane SKU → `orphans` (zawsze widoczne w UI + osobny arkusz w Excelu).

## Konwencje wykorzystane z istniejącego kodu

- Tokeny CSS: `var(--app-text)`, `var(--app-text-sec)`, `var(--app-surface)`, `var(--app-border)`, `var(--table-header-bg)`, `var(--table-divider)`.
- Klasy Apple: `card-apple`, `btn-apple-primary`, `btn-apple-pill`, `input-apple-sm`, `label-apple`, `toggle-switch`.
- Wzorzec wizard: 1:1 z `DataPreparationView.vue` (single `ref<Step>` + `<div v-if>`).
- Notifications: `useNotificationsStore().push({ type, title, message })`.
- HTTP: axios via `frontend/src/api/client.ts` (Bearer token z auth store).
- Auth na endpointach: `Depends(get_current_user)` + dostęp przez owner / public / shared.

## Test plan (per CLAUDE.md pkt 9)

### Backend (zielone)
```bash
python -m pytest tests/test_container_planner.py -v
```
20/20 testów przechodzi (katalog, fit, filtry, set-cover, integralność planu).

### Manual E2E
1. `uvicorn api.main:app --reload` + `npm run dev` w `frontend/`.
2. Login → `/tools` — drugi kafelek "Container Order" jest aktywny.
3. Wybierz analizę z carrier MiB → karta podświetlona → "Użyj tej analizy".
4. Krok 2: dostosuj suwaki, wybierz tryb, kliknij "Oblicz plan".
5. Krok 3: kliknij kafelek wariantu → 3D obraca się myszą. Tabela SKU paginuje.
6. Krok 4: licznik pojemników, tabela podsumowania.
7. Krok 5: pobierz `.xlsx` → otwórz w Excelu → sprawdź 4 arkusze.
8. Dark mode: przełącz w Settings — wszystkie elementy używają `var(--app-*)`.

### Regression
Sprawdź, że pierwszy kafelek (Data Preparation) nadal działa — to ten sam plik
`ToolsView.vue`, tylko placeholder #1 został zamieniony.

## Co zostawiono na v2

- **Mieszane konstrukcje** (różne komory w jednym binie — PDF mówi "ponad 100 układów"). v1 = jednolite.
- **Wycena** persystowana na backendzie (v1 = `localStorage`).
- **Inne nośniki niż MiB 640×440** (v1 = tylko ten pojemnik).
- **Multi-warehouse** w jednym zamówieniu.
- **Sharing zapisanych planów** między userami (mirror `RunShare` pattern).

## Changelog

### 2026-05-17 — historia + rozbicie na bazy/ramki

**Część A — Bases + Frames w zamówieniu.** Kardex VBM Box to system EasyClick: każdy fizyczny pojemnik = 1 baza 138 mm + N ramek 50 mm. Catalog narzędzia używa tier'ów 138/188/238/288 → odpowiednio 0/1/2/3 ramek. Dotąd narzędzie pokazywało tylko sumaryczną liczbę pojemników, ale magazyn potrzebuje wiedzieć ile baz i ile ramek osobno (to oddzielne SKU u dostawcy).

Zmiany w planerze: `Variant.frames_per_bin` obliczane w `_build_catalog()` z formuły `(tier - 138) // 50`. `VariantSummary` zyskuje pola `frames_per_bin` i `total_frames_required = bins_required × frames_per_bin`. `ContainerPlan.total_frames` agreguje wszystkie warianty. Stałe `BASE_BIN_HEIGHT_MM = 138`, `FRAME_INCREMENT_MM = 50` w `container_planner.py`. Liczba baz = liczba pojemników (1 baza per bin), nie wprowadzam osobnego pola.

UI: tabela podsumowania w Summary tab ma teraz 9 kolumn (dodane **Bases** i **Frames** zaraz po „Bins") z sumami w wierszu TOTAL. Excel arkusz „Order Summary" — 11 kolumn z analogicznym TOTAL. PDF tabela „Order summary" — 11 kolumn, `colWidths` rebalans. CSV w `_generate_summary_csv` — dodane kolumny `bases` i `frames`.

3 nowe testy planera (`test_variant_frames_per_bin_derived_from_height`, `test_variant_summary_carries_frames_per_bin_and_total`, `test_container_plan_aggregates_total_frames_across_variants`) — łącznie 34/34 zielone.

**Część B — Historia obliczeń (explicit save).** Nowy model `ContainerOrderPlan` (`api/models/container_order_plan.py`) z polami: `id`, `owner_id` (FK users CASCADE), `source_run_id` (FK analysis_runs SET NULL — usunięcie analizy NIE kasuje zapisanych planów), `label`, `client_name`, `params` JSON, `plan` JSON, `notes`, `created_at`, `updated_at`. Rejestracja w `api/models/__init__.py` — `Base.metadata.create_all` w `api/main.py` automatycznie tworzy tabelę.

5 nowych endpointów w `api/routers/container_order.py`:
- `POST /plans` — zapisuje snapshot (frontend wysyła params + plan z store).
- `GET /plans?page&page_size` — paginowana lista własnych planów, sortowana DESC po `created_at`. Każdy item ma `source_run_available: bool` (czy źródłowa analiza wciąż istnieje).
- `GET /plans/{id}` — pełny detail z params + plan.
- `PATCH /plans/{id}` — rename / update notes.
- `DELETE /plans/{id}` — owner-only.

Helper `_get_owned_saved_plan` analogicznie do istniejącego `_get_accessible_run`. Schematy: `SavedPlanCreate`, `SavedPlanResponse` (lekka pozycja listy z KPI), `SavedPlanDetail` (z params + plan), `SavedPlanPatch`, `SavedPlanListResponse`.

UI: nowa **piąta zakładka „History"** w tab nav (zawsze enabled). Lista kart z labelem, mode-chip, datą, KPI strip (`bins · frames · coverage · SKUs`), trzema akcjami (Load / Rename / Delete) i banerem „source missing" gdy źródłowa analiza jest skasowana. Paginacja „Load more" (page_size=20). Empty state z instrukcją.

**„Save plan"** button w Calculation tab obok „Next →" — widoczny tylko gdy `store.plan` istnieje i nie był jeszcze zapisany w sesji (`currentSavedId` flag). Klik → modal `card-apple-elevated` (380 px) z labelem (prefilled `{client_name} — {today en-GB}`) i opcjonalnymi notes. Enter zapisuje, Esc zamyka.

**Load flow**: klik „Load" w History → `store.loadSavedPlan(id)` → przywraca params + plan + próbuje znaleźć `currentRun` w `eligible` (jeśli analiza wciąż istnieje); jeśli nie → `currentRun = null` i flaga `sourceMissing = true`. UI w Calculation tab pokazuje warning panel + disabluje „Calculate plan →" (eksport nadal działa).

Store w `containerOrder.ts` rozszerzony o `savedPlans / savedPlansTotal / savedPlansLoading / savedPlansError / currentSavedId / sourceMissing` plus akcje `listSavedPlans / savePlan / loadSavedPlan / renameSavedPlan / deleteSavedPlan`.

Scoped CSS: `.history-card` (pochodna `.run-card`), `.kpi-strip`, `.history-actions`, `.mode-chip` (z dark variantem), `.save-modal-overlay` + `.save-modal` (reuse `card-apple-elevated`), `.empty-history`. Chip `.chip-imputed` przeniesiony do scoped CSS żeby był też dostępny w History (jako „source missing" badge).

`vue-tsc --noEmit` → exit 0. 34/34 testów planera. Wszystkie nowe endpointy (`/plans`, GET/POST/PATCH/DELETE) zarejestrowane w app.

Pliki: `src/analytics/container_planner.py`, `api/schemas/container_order.py`, `api/routers/container_order.py`, `api/models/container_order_plan.py` (NEW), `api/models/__init__.py`, `api/excel_generator.py`, `api/pdf_generator.py`, `frontend/src/api/containerOrder.ts`, `frontend/src/stores/containerOrder.ts`, `frontend/src/views/tools/ContainerOrderView.vue`, `tests/test_container_planner.py`.

### 2026-05-17 — czytelny zakres SKU dla analiz z >1 nośnikami

**Problem:** karta wyboru analizy (Krok 1) pokazywała globalne `SKU` i `FIT%` z całego datasetu. Gdy analiza miała 2 nośniki (np. MiB + większa paleta), SKU pasujące tylko do drugiego nośnika wliczały się w FIT%, sugerując że narzędzie planuje na większym zbiorze niż w rzeczywistości. Backend planera filtrował poprawnie (`_select_capacity_rows` w `container_planner.py`), bug był wyłącznie w UI.

**Zmiana:**
- `EligibleAnalysis` (schema + TS interface) dostał pola `mib_fit_count`, `mib_borderline_count`, `mib_not_fit_count`, `mib_fit_pct`, `mib_planned_sku`, `carriers_analyzed` — odczytywane z `capacity_result.carrier_stats["2"]`.
- Karta w Kroku 1: wyróżnia liczbę SKU planowanych dla MiB (z procentem), poniżej kontekst (z ilu SKU w datasecie, ile nośników w analizie). Brak FIT-ów MiB → warning + zablokowany przycisk.
- Nagłówek Kroku 2: dopisana linia "Planowanie obejmie N SKU pasujące do MiB 640×440 (FIT + BORDERLINE)".
- Notka w Kroku 1: wprost mówi, że SKU pasujące tylko do innych nośników nie wchodzą do planu.

Pliki: `api/schemas/container_order.py`, `api/routers/container_order.py`, `frontend/src/api/containerOrder.ts`, `frontend/src/views/tools/ContainerOrderView.vue`.

### 2026-05-17 — szerszy widok, stabilne kolumny, Load more dla SKU

- Usunięto inline `max-width:1100px` z `card-apple` w `ContainerOrderView.vue` → tool używa teraz pełnej szerokości `max-w-[1400px]` zdefiniowanej w `App.vue` (tak samo jak `CarriersView`).
- Krok 3 (Przegląd): outer grid zmieniony z `lg:grid-cols-2` na `lg:grid-cols-3` z `lg:col-span-2` dla siatki wariantów; wewnętrzna siatka przeszła z `grid-cols-2` na `grid-cols-2 sm:grid-cols-3`. Efekt: 3 karty wariantów w rzędzie obok podglądu 3D na szerokich ekranach.
- Obie tabele (`SkuAssignmentTable` oraz tabela podsumowania w Kroku 4) dostały `table-layout:fixed` + `<colgroup>` z procentowymi szerokościami kolumn, plus `cell-truncate` (ellipsis) dla długich wartości SKU/Rekom/Wariant. Filtry nie powodują już przeskoków kolumn.
- `SkuAssignmentTable`: paginacja prev/next zastąpiona przyciskiem **„Załaduj więcej"**. `pageSize` = 20. Licznik pozostałych SKU pokazany w przycisku; counter w nagłówku tabeli mówi „Pokazano X z Y SKU (filtr) · Z łącznie". Zmiana filtra (search/ABC/status) resetuje widoczny zakres do 20 wierszy.

Pliki: `frontend/src/views/tools/ContainerOrderView.vue`, `frontend/src/components/SkuAssignmentTable.vue`.

### 2026-05-17 — fix toggle + max_locations_per_sku faktycznie egzekwowane

**Toggle „Tylko SKU Machine"**: w `ContainerOrderView.vue` używał `<label class="toggle-switch"><input type="checkbox"><span class="toggle-slider"></span></label>`, ale CSS `.toggle-switch` w `main.css:282-308` projektowany jest dla `<button class="toggle-switch" :class="{'is-on': value}">` ze stylem `::after` jako kółko thumb. Efekt: natywny checkbox renderował się NA tle pigułki z dodatkowym białym kółkiem. Fix: zamiana na `<button type="button" class="toggle-switch" :class="{'is-on': only_machine}" @click="toggle">` — działa zgodnie z CSS i jest spójne z resztą aplikacji.

**`max_locations_per_sku` faktycznie egzekwowane**: bug w `src/analytics/container_planner.py:_locations_needed`. Stary kod `return min(n, max_loc)` cicho cap'ował liczbę lokalizacji, nawet gdy realny popyt był większy — w efekcie:
1. SKU „mieścił się" w mniejszej liczbie lokalizacji niż fizycznie potrzebne,
2. `fill_pct` przekraczało 100%,
3. Cel `min_waste` perwersyjnie preferował te przesycone warianty (najwyższy fill),
4. SKU nigdy nie trafiał do `orphans`, więc użytkownik nie wiedział że cap nie jest egzekwowany.

Naprawa: `_locations_needed` zwraca `0` gdy `n_required > max_loc`. `_compute_fits` już teraz pomija wariant gdy `locs <= 0`, więc wariant odpada z kandydatów danego SKU. Jeśli żaden wariant nie zmieści SKU pod ustalonym capem → SKU staje się orphanem (z poprawnym ostrzeżeniem w Kroku 3 i arkuszem „Orphans" w eksporcie).

**Pozostałe parametry zweryfikowane bez zmian**: `abc_classes`, `only_machine`, `include_borderline`, `stock_multiplier`, `location_fill_rate`, `min_locations_per_sku`, `mode`, `auto_max_variants`, `auto_goal`, `guided_preset`, `manual_variant_codes` — wszystkie poprawnie threadują przez planera (audit zapisany w komentarzu do commita).

**Testy**: dodane `test_locations_needed_returns_zero_when_demand_exceeds_max_loc`, `test_locations_needed_keeps_variant_when_within_max_loc`, `test_max_locations_per_sku_orphans_when_no_variant_fits_under_cap`, `test_max_locations_per_sku_picks_larger_variant_when_smaller_one_exceeds_cap`, `test_fill_pct_never_exceeds_100`. Łącznie 25/25 testów planera przechodzi.

Pliki: `src/analytics/container_planner.py`, `tests/test_container_planner.py`, `frontend/src/views/tools/ContainerOrderView.vue`.

### 2026-05-17 — pełne tłumaczenie UI Container Order na angielski

Wszystkie user-facing teksty narzędzia przeszły z polskiego na angielski. Backend (Excel/PDF generators) był już od początku po angielsku, więc zmiany są wyłącznie po stronie frontu.

**`ContainerOrderView.vue`**:
- Zakładki: `Analiza/Obliczenia/Podsumowanie/Eksport` → `Analysis/Calculation/Summary/Export`.
- `disabledReason` przepisane: „First pick an analysis with SKUs that fit MiB.", „First click 'Calculate plan →' in the Calculation tab.".
- Krok Analysis: „Select a completed analysis", lista kart pokazuje „To plan (MiB 640×440): N SKUs · X% fit in MiB" + „of M SKUs in dataset · K carriers in analysis", warning „0 SKUs fit in MiB 640×440 — the tool cannot generate an order.", przycisk „Use this analysis →".
- Krok Calculation: nagłówek „Plan calculation", podtytuł „Analysis: … · N SKUs fitting MiB 640×440 (FIT + BORDERLINE)". Sekcje parametrów: „ABC classes", toggle „Only Machine"/„Impute missing", suwaki „Stock buffer"/„Fill rate"/„Max variants", „Mode" pills, dropdown „Goal" (Minimum waste / Minimum bins / Max SKU coverage), „Preset" (Simple / Standard / Full coverage), „Min loc."/„Max loc.", manual picker „Pick variants (48 available)" + przyciski „+ Auto 28 / + All 48 / Clear". Przycisk akcji `Calculating…` / `Calculate plan →`.
- Sekcja wyników: „Planning results", „Selected N variants · coverage X% (A / B SKUs)", „Selected variants (click to view 3D)", „Bin 3D preview", warning „N unassigned SKUs — none of the selected variants fits them. Consider increasing the number of variants or switching to Manual mode.", „SKU table" jako tytuł tabeli, przycisk „Next →".
- Placeholder: „Adjust the parameters above and click 'Calculate plan →' to see the planning results."
- Krok Summary: „Order summary", hero „Total bins to order", kontekst „N variants · coverage X% · avg fill Y%". Tabela: `Variant / Footprint / Height mm / SKUs / Locations / Bins / Fill`, wiersz TOTAL po angielsku. Stopka „N SKUs were not assigned — listed in 'Orphans' sheet of the export.", przycisk „Go to export →".
- Krok Export: „Export the order", podtytuł „Choose a format. Excel contains 4 sheets … PDF — a 2-page summary.", opisy kafelków `multi-sheet Excel` / `2-page report` / `single sheet`, stan `Generating…`, przyciski „↺ New order" + „← Back to Tools".
- Toasty: „Calculation failed" / „File generated" / „Export failed" + komunikat fallback „Please try again."
- `formatDate` używa locale `en-GB` zamiast `pl-PL` — daty w formacie `4 May 2026`.

**`SkuAssignmentTable.vue`**:
- Counter: „Showing X of Y SKUs (filtered) · Z imputed total".
- Headery filtrowalne: `SKU / Dimensions mm / ABC / Recom. / Variant`, niefiltrowalne `Weight kg / Locations / Fill`.
- Tooltipy triggerów `▾`: „Filter by SKU / imputation status / ABC class / recommendation / assignment" z aktywnymi wariantami „SKU filter: …", „ABC filter: …" itd.
- Popovery: tytuły „Filter SKU / Imputation status / ABC class / Recommendation / Assignment", opcje „All / Only A/B/C / Imputed only / Not imputed only / Machine / Non-machine / Assigned / Unassigned", hint dla niedostępnych klas „(not selected in Calculation tab)", przyciski „Clear / Close".
- Komórka Variant gdy orphan: `missing dimensions` / `no variant`.
- Tooltipy chipów: „This SKU fits MiB with a small margin only (BORDERLINE from the Capacity analysis).", „Dimensions imputed with the median from the dataset.".
- Empty: „No SKUs match the filters.", „No SKUs with imputed dimensions in this plan.", „No SKUs in this plan.".
- Load more / Collapse: „Load all (N remaining)" / „Collapse to 20 rows".

**`Bin3DPreview.vue`**: empty state „Pick a variant on the left to see the 3D preview.", caption „— N cells, A×B×C mm".

Niedotknięte: chip etykiety `imputed` / `borderline` (i tak ang.), kody wariantów (`1/4-188` itd.), nazwy plików eksportu (`container_order_*`).

`vue-tsc --noEmit` → exit 0. 31/31 testów planera nadal zielone.

Pliki: `frontend/src/views/tools/ContainerOrderView.vue`, `frontend/src/components/SkuAssignmentTable.vue`, `frontend/src/components/Bin3DPreview.vue`.

### 2026-05-17 — flaga Borderline, fix empty row 2 w Excelu, suma Total locations, Run ID → Generated by

**Flaga Borderline w tabeli + eksportach**:
- `Assignment` rozszerzone o `fit_status: str | None` (`"FIT"` / `"BORDERLINE"`), propagowane z `capacity_result.rows[i].fit_status` przez `_SkuFit` do `_plan_from_selection` (oba branches: assigned i orphan).
- `AssignmentRow` (Pydantic + TS) lustrzanie dostały nowe pole.
- UI: chip `.chip-borderline` (pomarańczowy, scoped CSS z dark variantami: light `#ffedd5/#9a3412`, dark `rgba(249,115,22,0.22)/#fdba74`) obok SKU w głównej tabeli, gdy `fit_status === 'BORDERLINE'`. Razem z istniejącym chipem `imputed` daje czytelne flagowanie dwóch różnych zagrożeń.
- Excel: nowa kolumna **Fit** w arkuszu „SKU Assignment" (między SKU a Variant), dodatkowo kolumna **Imputed** (Yes/pusta) — by ułatwić filtrowanie/sortowanie po obu flagach jednocześnie. „Orphans" też dostał kolumnę Fit.

**Excel: empty row 2 — naprawiony**:
- Root cause: w `_style_header` wywołanie `ws.freeze_panes = ws.cell(row=row + 1, column=1)`. `ws.cell(...)` **tworzy** komórkę A2 jako side-effect, co rozszerza `ws.max_row` do 2. Kolejny `ws.append([...])` ląduje wtedy w wierszu 3, zostawiając wiersz 2 pusty. Excel widząc pusty wiersz nie traktuje wiersza 1 jako nagłówka przy auto-sort.
- Naprawa: `ws.freeze_panes = f"A{row + 1}"` (string reference — nie wywołuje `ws.cell()`, nie tworzy komórki).

**Suma `Total locations` w wierszu TOTAL Order Summary**:
- Excel: dopisany `ws.cell(row=total_row, column=7, value=total_locations)` gdzie `total_locations = sum(s.total_locations for s in plan.summaries)`.
- PDF: w `generate_container_order_pdf` w wierszu TOTAL tabeli Order Summary dopisana wartość `total_locations`.

**Run ID → Generated by**:
- `generate_order_xlsx(plan, params, run, user=None)` i `generate_container_order_pdf(plan, params, run, user=None)` dostały opcjonalny parametr `user`.
- Router `container_order.export_plan` przekazuje `current_user`.
- Excel `_sheet_parameters`: wiersz „Run ID" zamieniony na „Generated by" z formatem `"{name} <{email}>"` (fallback do samego name lub email, lub `—` jeśli brak).
- PDF: identyczna zamiana w sekcji Parameters used.

31/31 testów planera dalej zielone. `vue-tsc --noEmit` → exit 0.

Pliki: `src/analytics/container_planner.py`, `api/schemas/container_order.py`, `api/routers/container_order.py`, `api/excel_generator.py`, `api/pdf_generator.py`, `frontend/src/api/containerOrder.ts`, `frontend/src/components/SkuAssignmentTable.vue`.

### 2026-05-17 — strict filtering Performance + potwierdzenie konsolidacji binów

**Strict filtering w `_filter_skus`**: poprzednia logika `if abc_set is not None and meta is not None` pomijała filtr ABC dla SKU bez metadanych Performance (`sku_pareto`). Analogicznie dla `only_machine`. Efekt: gdy użytkownik wybierał konkretne klasy ABC + only Machine, w wynikach pojawiały się SKU z `"—"` w obu kolumnach (ABC i Rekom.) — nie spełniały jawnie zadanego warunku, ale „wymykały się" przez lukę w filtrze.

Naprawa: filtry działają teraz w dwóch trybach zależnie od dostępności danych Performance:
- **Strict** (perf data istnieje → `abc` dict niepusty): SKU bez wpisu w `sku_pareto` jest WYKLUCZANY gdy użytkownik wybrał specyficzny ABC lub `only_machine`. Aktywne wybory traktowane są jako jawne ograniczenie — SKU bez metadanych nie może być zaufany że je spełnia.
- **Lenient** (perf data brak → `abc` dict pusty): filtry ABC i `only_machine` są pomijane. Użytkownik nie sklasyfikował jeszcze SKU; powinien móc planować z samej Capacity. Zachowanie zgodne z istniejącym testem `test_no_performance_data_skips_abc_filter`.

**Potwierdzona konsolidacja 6 SKU → 1 bin**: nowy test `test_six_small_skus_share_one_six_cell_bin` weryfikuje że 6 małych SKU przypisanych do wariantu o `locations_per_bin=6` (np. `1/6_3x2-138`) konsumuje 6 lokalizacji łącznie i zamawia tylko **1 fizyczny pojemnik** (ceil(6/6)=1). Mechanika w `_plan_from_selection`: per-SKU lokalizacje są sumowane w `locs_per_variant[v_code]`, a potem dla każdego wariantu `bins = math.ceil(locs / v.locations_per_bin)`. Ta sumacja jest matematycznym sercem oszczędności na pojemnikach — wiele SKU dzieli cells w tym samym binie.

Łącznie 31/31 testów planera.

Pliki: `src/analytics/container_planner.py`, `tests/test_container_planner.py`.

### 2026-05-17 — polerowanie: usunięta tabela imputed, fix overflow kart, czytelny caption 3D, loading indicators

**Usunięta dodatkowa tabela imputed-only** — filtr „Status: Tylko Imputed" w głównej tabeli daje ten sam wynik. Skasowane: drugi `<SkuAssignmentTable mode="imputed-only">` oraz computed `hasImputedAssignments`.

**Fix overflow VariantCard przy >6 wariantach**: bug był w inline `style="min-height:62px"` na elemencie `<svg>` — przy ścieśnionych wierszach grida (3+ rzędów po 107 px każdy) SVG nie mógł się skurczyć poniżej 62 px, a tekst pod nim (wymiary + counter) był wypychany poza krawędź karty. Naprawa:
- Usunięte inline `min-height:62px` z SVG.
- `.variant-card > svg { flex: 1 1 0; min-height: 0; max-height: 100% }` — SVG kurczy się do tego co zostaje po nagłówku i counterach.
- `.variant-card { overflow: hidden }` — defensywny clip gdyby coś dalej się wylewało.
- `.variant-card > p { flex: 0 0 auto; white-space: nowrap; overflow: hidden; text-overflow: ellipsis }` — paragrafy nie zawijają, jak nie mieszczą się wszerz → wielokropek.
- `.variant-grid`: `height:320px` zmienione na `min-height:320px; max-height:480px` — pełne wypełnienie przy 2 rzędach, łagodny wzrost do 4 rzędów (140 px na rząd), scroll powyżej.

**Caption 3D w dark — definitywny fix**: dwie poprzednie próby (translucent overlay) zostawiały problem czytelności. Tym razem chip ma SOLIDNE kolory:
- Light: `bg:#ffffff; color:#1d1d1f`.
- Dark: `bg:#1d1d1f; color:#f5f5f7`.
- Secondary span (`.caption-secondary`) używa `opacity: 0.7` zamiast osobnego `color`, więc dziedziczy kolor z kontenera — nie ma ryzyka że jakaś reguła `color` nie zaaplikuje się do span w którymś z trybów.

**Loading indicators**:
- Ikona narzędzia (6-komorowy bin, ta sama co na kafelku w Tools) dodana w breadcrumb obok tytułu „Container Order — Kardex VBM Box". Klasa `.page-icon` z `color:#0071e3` (accent). Podczas `store.loading` pulsuje (`animation: page-icon-pulse 1s ease-in-out infinite` — `opacity 1↔0.4` + `scale 1↔0.9`).
- Wewnątrz przycisku „Oblicz plan →": gdy `store.loading`, pokazuje się `<svg class="calc-spinner">` (otwarte kółko z `stroke-dasharray`) wirujący z `animation: calc-spinner-rotate 0.85s linear infinite`. Tekst zmienia się na „Obliczanie…".

Pliki: `frontend/src/views/tools/ContainerOrderView.vue`, `frontend/src/components/VariantCard.vue`, `frontend/src/components/Bin3DPreview.vue`.

### 2026-05-17 — scalenie Parametrów i Przeglądu w zakładkę „Obliczenia"

Zakładka „Parametry" usunięta z nawigacji; jej zawartość przeniesiona na górę zakładki „Przegląd" przemianowanej na **Obliczenia**. Workflow zakładek skrócony z 5 do 4: `Analiza / Obliczenia / Podsumowanie / Eksport`.

W zakładce Obliczenia:
1. Nagłówek z nazwą analizy + liczbą SKU pasujących do MiB.
2. **Kompaktowy blok parametrów** (zawsze widoczny) — 3 poziome rzędy:
   - Rząd 1: ABC checkboxy + toggle „Tylko Machine" + toggle „Imputuj braki" (inline, tooltip jako podpowiedź).
   - Rząd 2: Suwaki — Bufor zapasu, Wypełnienie, Maks. wariantów (ostatni tylko w trybie auto).
   - Rząd 3: Tryb pills + dropdown Cel/Preset (mode-conditional) + Min/Max lok. (numeric inputs) + przycisk **Oblicz plan →** (right-aligned).
   - Rząd 4 (warunkowy, tylko w trybie manual): pełna szerokość, lista 48 wariantów z checkboxami + skróty Auto/Wszystkie/Wyczyść.
3. **Wyniki planowania** — pokazują się dopiero gdy `store.plan` istnieje. Nagłówek z liczbą wariantów i pokryciem, dalej grid wariantów + 3D, ostrzeżenie orphans, główna tabela SKU, dedykowana tabela imputed (warunkowo), przycisk „Dalej →" do Podsumowania.
4. **Placeholder** gdy nie ma jeszcze planu: dashed-border box z instrukcją „Dostosuj parametry powyżej i kliknij Oblicz plan →".

Klucze stanu:
- Type `Step` skrócony do `'select-run' | 'review' | 'summary' | 'export'`.
- `tabs` computed: 4 wpisy (label `Obliczenia` zamiast `Parametry` + `Przegląd`).
- `goToParams()` przekierowuje teraz wprost na `review`.

CSS:
- Nowe klasy `.params-compact` (wrapper z border+padding), `.params-row` (flex wrap z `gap:14px 22px`), `.param-cell` (column, `min-width:0`), `.param-cell.toggle-inline` (row z gap), `.param-cell.slider-cell` (`flex:1 1 200px; max-width:320px`), `.param-cell.calc-cell` (`margin-left:auto` dla przycisku Oblicz), `.param-label` (uppercase 11px, secondary, ze wsparciem `.param-value` w środku dla aktualnej wartości suwaka), `.empty-plan-hint` (dashed-border placeholder).
- Stare `.param-section`, `.section-label`, `.toggle-row`, `.toggle-title`, `.toggle-hint` usunięte (nieużywane po refaktorze).

Pliki: `frontend/src/views/tools/ContainerOrderView.vue`.

### 2026-05-17 — fix caption 3D w dark + uporządkowane parametry w 4 sekcjach

**Caption 3D w dark mode**: poprzednia próba `rgba(40,40,42,0.96)` była nadal zbyt jasna względem ciemnej sceny `0x1c1c1e`. Zmiana na klasyczny chip overlay (jak napisy w filmie):
- bg: `rgba(0,0,0,0.78)` — niemal czarne, mocno tłumi
- border: `rgba(255,255,255,0.18)` — subtelny jasny obrys dla czytelności krawędzi
- Tekst rozdzielony na `.caption-primary` (białe, font-weight 600 — kod wariantu) i `.caption-secondary` (`rgba(255,255,255,0.72)` — wymiary)

W light mode caption pozostaje na `rgba(255,255,255,0.92)` z borderem `var(--app-border)`.

**Reorganizacja Kroku 2 — 4 sekcje z nagłówkami**:
1. **Filtry SKU** — checkboxy ABC.
2. **Przełączniki** — Tylko Machine + Imputuj brakujące wymiary, każdy w `.toggle-row` (lewa strona: tytuł + krótka podpowiedź, prawa: toggle).
3. **Suwaki** — Bufor zapasu, Wypełnienie lokalizacji, Maks. liczba wariantów (ostatni tylko w trybie `auto`, zajmuje pełną szerokość).
4. **Tryb i akcje** — pills trybu (auto/guided/manual), mode-specific dropdown (Goal / Preset / variant checkboxes), Min/Max lokacji (numerics), przycisk **Oblicz plan →**.

Sekcje wizualnie rozdzielone `border-bottom: 1px solid var(--app-border)` (ostatnia bez bordera), nagłówki w stylu `.section-label` (uppercase 11px, secondary color, letter-spacing 0.4px). Każda sekcja ma `padding: 14px 0 18px`.

Pliki: `frontend/src/components/Bin3DPreview.vue`, `frontend/src/views/tools/ContainerOrderView.vue`.

### 2026-05-17 — Excel-style filtry w nagłówkach + dedykowana tabela imputed + caption fix

**Caption 3D w dark mode**: poprzedni `:global(html.dark) .bin3d-caption` ustawiał `background:rgba(31,41,55,0.92)` (niebieskawy) + `color:#e5e7eb` na surowo. Teraz caption ma `color:var(--app-text)` w light i `background:rgba(40,40,42,0.96)` w dark (zharmonizowane z `--app-surface`) plus `border:1px solid var(--app-border)`. Caption czyta się jako element UI, nie świecąca plamka nad sceną.

**Filtry w nagłówkach (Excel-style)**: cały top-bar z `<select>`ami zniknął. Każdy filtrowalny header (SKU, Wymiary mm, ABC, Rekom., Wariant) ma:
- Ikonkę `▾` (trigger) tuż przy etykiecie — sygnalizuje że kolumna jest filtrowalna.
- Aktywny filtr podświetla label kolumny + trigger na akcent `#0071e3` (font-weight 600/700).
- Klik → popover z opcjami radio (lub input dla SKU search). Popover ma `Wyczyść` i `Zamknij`.
- `Esc` zamyka popover.
- Klik gdziekolwiek poza popoverem zamyka (document-level click handler).

Popover **teleportowany do `<body>`** (`<Teleport>`), pozycjonowany via `getBoundingClientRect()` triggera + `position:fixed`. Powód: wrapper tabeli ma `overflow-x:auto`, a per spec CSS to wymusza `overflow-y:auto`, więc popover wewnątrz tabeli byłby clipowany. Teleport omija problem. Pozycja przelicza się przy scroll i resize.

Filtrowalne kolumny: SKU (search), Wymiary mm (status imputacji — tylko w mode='all'), ABC (z grayed-out dla klas niewybranych w Kroku 2), Rekom. (Machine/Non-machine), Wariant (Przypisanie). Pozostałe kolumny (Waga, Lokacji, Wypeł.) bez ▾.

**Dedykowana tabela dla SKU imputed**: drugi `<SkuAssignmentTable mode="imputed-only">` pod główną tabelą w Kroku 3. Pojawia się tylko gdy `hasImputedAssignments` (przynajmniej jedno SKU z `dimensions_imputed=true`). Pre-filtruje wewnętrznie na imputowane, ukrywa trigger „Wymiary mm" (bezcelowy gdy wszystko już imputed), zachowuje filtry ABC/Rekom./Wariant. Tytuł „SKU z imputowanymi wymiarami" pomaga audytowi imputacji.

Nowe propsy `SkuAssignmentTable`:
- `mode?: 'all' | 'imputed-only'` (default `'all'`)
- `title?: string` (renderowany jako nagłówek nad tabelą)
- `selectedAbcClasses?: string[]` (już było)

Pliki: `frontend/src/components/SkuAssignmentTable.vue` (pełny refactor), `frontend/src/components/Bin3DPreview.vue`, `frontend/src/views/tools/ContainerOrderView.vue`.

### 2026-05-17 — audit dark mode + 3 nowe filtry tabeli SKU

**Audit kolorów Light/Dark**:
- Chip „imputed": twardo kodowane `bg:#fef3c7` + `color:#92400e` wyglądały jak biała plama na ciemnej karcie. Wyniesione do scoped klasy `.chip-imputed` z `:global(html.dark)` overrideami (`bg:rgba(245,158,11,0.2); color:#fcd34d`).
- ABC chipy: usunięte inline `abcChipStyle()`, w zamian klasy `.abc-A` / `.abc-B` / `.abc-C` z dark variantami (zielony/żółty/szary translucent na dark).
- Warning text `#92400e` (w „0 SKU pasuje do MiB", w panelu orphans Krok 3, w stopce Krok 4): wszędzie zamienione na klasę `.warning-text` z dark variantem `#fcd34d`.
- Panel orphans (`background:rgba(245,158,11,0.1)`): klasa `.warning-panel` z lekko zwiększoną krytą i bardziej widocznym borderem w dark.
- `VariantCard` SVG: bin background `fill="#f3f4f6"` → klasa `.bin-bg`/`.bin-cell` w scoped CSS, z dark variantami (bin tło `#2c2c2e`, komórki `rgba(0,113,227,0.28)`).
- `Bin3DPreview`: scene.background dynamicznie (helper `currentSceneBg()` zwraca `0xf3f4f6` lub `0x1c1c1e`). MutationObserver na `<html class>` aktualizuje scenę bez konieczności remountu komponentu, więc przełączenie motywu w Settings natychmiast odświeża podgląd 3D.

Pozostałe wartości (`#0071e3`, `#ff3b30`, `#ef4444`, kolory tier-chipów w VariantCard) zostawione — działają poprawnie w obu trybach.

**3 nowe filtry w tabeli SKU**:
- **Status** (imputacja): „wszystkie / Tylko Imputed / Tylko Not imputed".
- **ABC**: opcje klas niewybranych w Kroku 2 są wyłączone (`<option :disabled>`) z etykietą „tylko X (niewybrane)" i wyszarzeniem. Watcher resetuje filtr na pusty gdy użytkownik dotnie parametrów ABC w Kroku 2 i wybrana wcześniej klasa nie jest już dostępna.
- **Rekomendacja**: „wszystkie / Machine / Non-machine".
- Stary filtr assigned/orphan przemianowany na **Przypisanie** (żeby zwolnić etykietę „Status" dla imputacji) — zachowuje pełną funkcjonalność.

Komponent `SkuAssignmentTable` dostał nowy prop `selectedAbcClasses?: string[]`. `ContainerOrderView` przekazuje `store.params.abc_classes`. Wszystkie filtry resetują widoczność do 20 wierszy przy zmianie (spójnie z search'em).

Pliki: `frontend/src/components/SkuAssignmentTable.vue`, `frontend/src/components/VariantCard.vue`, `frontend/src/components/Bin3DPreview.vue`, `frontend/src/views/tools/ContainerOrderView.vue`.

### 2026-05-17 — toggle restyle, równa wysokość kart wariantów, imputacja brakujących wymiarów

**Toggle (scoped CSS)**: `.toggle-switch` w `ContainerOrderView.vue` zmniejszony 51×31 → 34×20, kolor `is-on` zmieniony z iOS-green (`#34c759`) na Apple-blue (`#0071e3`) zgodnie z resztą akcentów aplikacji.

**Równa wysokość kart wariantów**: lewa kolumna w Kroku 3 (siatka kart) wcześniej była niższa niż prawa (`Bin3DPreview` ma stały `height: 320px`), tworząc pustą przestrzeń pod 2 rzędami kart. Nowa klasa `.variant-grid` ma `height: 320px` + `grid-auto-rows: minmax(120px, 1fr)`, a `VariantCard` zmienił `display: block` → `flex column; height: 100%`. Karty rozciągają się równo wypełniając całą wysokość okna podglądu. Wystającą zawartość obsługuje `overflow-y: auto`.

**Imputacja brakujących wymiarów**: zidentyfikowano realny bug w przepływie danych — `runs.py:299-336` zapisuje statystyki z `QualityPipeline`, ale **imputowany DataFrame nie jest persystowany**. Capacity czyta surowy `df` z dysku (`runs.py:439`), więc SKU z `length_mm=0`/`width_mm=0`/etc. przechodzą geometryczne sprawdzenie `0 ≤ cell_*` i pasują do każdego wariantu. W trybie `min_waste` wygrywa najmniejszy wariant (sztucznie wysoki `fill_pct`).

Naprawa per-tool, bez zmian w globalnym data flow: planer sam wykrywa braki i imputuje medianą w czasie planowania. Nowy parametr `PlanParams.impute_missing_dimensions: bool = True`:
- **ON (domyślnie)**: braki w `length_mm`/`width_mm`/`height_mm`/`weight_kg` (`<= 0` lub `null`) są zastępowane medianą obliczoną z pozostałych wierszy MiB tego datasetu. SKU dostaje flagę `dimensions_imputed=True` i chip „imputed" w tabeli (`bg:#fef3c7;color:#92400e`, tooltip „Wymiary uzupełnione medianą z datasetu.").
- **OFF**: SKU z brakami trafia bezpośrednio do `orphans` z `orphan_reason = "missing_dimensions"`. W tabeli SKU w kolumnie Wariant pokazuje się „brak wymiarów" zamiast generic „brak wariantu".

Toggle dodany w Kroku 2 obok „Tylko SKU Machine" (z tooltipiem). `Assignment` ma teraz pola `dimensions_imputed: bool` i `orphan_reason: str | None` (propagowane przez `AssignmentRow` schema → TS interface → UI).

Bonus: helper `_dataset_medians()` poprawnie pomija zerowe wartości przy liczeniu mediany (nie zaniża), a `_compute_fits` używa imputowanych wartości spójnie zarówno przy candidacie wariantów, jak i w wyjściowym `Assignment` (UI widzi te liczby, które rzeczywiście karmiły matcher).

**Testy**: dodane `test_imputation_off_orphans_sku_with_missing_dimensions`, `test_imputation_on_uses_dataset_median_for_missing_dimensions`, `test_imputation_on_orphans_when_no_dataset_median_available`, `test_dataset_medians_helper_skips_zero_values`. Łącznie 29/29 testów planera.

Pliki: `src/analytics/container_planner.py`, `tests/test_container_planner.py`, `api/schemas/container_order.py`, `api/routers/container_order.py`, `frontend/src/api/containerOrder.ts`, `frontend/src/views/tools/ContainerOrderView.vue`, `frontend/src/components/VariantCard.vue`, `frontend/src/components/SkuAssignmentTable.vue`.

### 2026-05-17 — zakładki zamiast kroków, fix hovera, lepszy Load more

- **Zakładki w stylu Analizy**: usunięto zewnętrzny wrapper `<div class="card-apple">` (zastąpiony `<div class="pt-6">`) oraz step indicator (przerywniki `1. ›  2. ›  …`). Pojawia się pasek zakładek `tool-tab-nav` / `tool-tab-btn` (klasy lokalne w scoped CSS, identyczny wygląd jak `run-tab-nav` w `RunView.vue`). Pięć zakładek: Analiza / Parametry / Przegląd / Podsumowanie / Eksport. Zakładki 2–5 są `disabled` (opacity 0.45, `cursor:not-allowed`, tooltip wyjaśnia dlaczego) dopóki nie spełnione warunki:
  - Parametry: wymaga wybranej analizy z `mib_planned_sku > 0`.
  - Przegląd / Podsumowanie / Eksport: wymaga `store.plan`.
- **Usunięte przyciski „← Wróć"** ze wszystkich kroków — nawigację zapewniają teraz zakładki. Przyciski akcji w prawym dolnym rogu („Użyj tej analizy →", „Oblicz plan →", „Dalej →", „Przejdź do eksportu →") zostały — uzupełniają linearny workflow.
- **Fix hovera**: globalna reguła `.card-apple:hover` w `main.css:254-260` dodawała box-shadow + zmianę tła w dark mode, co podświetlało cały obszar kroku przy najechaniu kursorem. Usunięcie wrappera `card-apple` z poziomu narzędzia rozwiązuje problem bez zmian w globalnych stylach. Kafelki eksportu (xlsx/pdf/csv) zachowują `card-apple` (klikalne, hover ma sens).
- **Load more**: zamiast inkrementu o 20, przycisk teraz wczytuje **wszystko** za jednym kliknięciem; gdy widać wszystkie wiersze, przycisk zmienia się na **„Zwiń do 20 wierszy"**. Zmiana filtra (search / ABC / status) resetuje widok do 20 wierszy.

Pliki: `frontend/src/views/tools/ContainerOrderView.vue`, `frontend/src/components/SkuAssignmentTable.vue`.
