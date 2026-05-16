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

Plik PDF `Dev/Calculators/Flyer_PL_Kardex-VBM-Box.pdf` (Kardex VBM Box flyer):

- Pojemnik bazowy: **640 × 440 × 138 mm**, 27.6 L, max 35 kg.
- Wnętrze użytkowe: ~617 × 408 mm.
- System EasyClick: frames podnoszą bin co +50 mm.
- Wysokości: 138 / 188 / 238 / 288 / 338 / 388 mm.
  **Dividery działają tylko do 288 mm** → narzędzie używa 4 wysokości: 138/188/238/288.
- Modułowość: komory są wielokrotnościami 103 mm wzdłuż i 102 mm wszerz.

## Katalog wariantów

12 footprintów × 4 wysokości = **48 wariantów (pełny katalog, tryb Manual)**.
7 z nich oznaczono jako "auto" → **28 wariantów (tryby Auto i Guided)**.

Wymiary komór (długość × szerokość, w mm):

| Footprint   | Komora (L×W) | Komór | Auto |
|-------------|--------------|------:|:----:|
| `1/1`       | 617 × 408    |  1    | ✓ |
| `1/2L`      | 309 × 408    |  2    | ✓ |
| `1/2W`      | 617 × 204    |  2    | ✓ |
| `1/3W`      | 617 × 136    |  3    | ✓ |
| `1/3L`      | 206 × 408    |  3    |   |
| `1/4`       | 309 × 204    |  4    | ✓ |
| `1/6_3x2`   | 206 × 204    |  6    | ✓ |
| `1/6_2x3`   | 309 × 136    |  6    |   |
| `1/8`       | 309 × 102    |  8    |   |
| `1/12_3x4`  | 206 × 102    | 12    | ✓ |
| `1/12_6x2`  | 103 × 204    | 12    |   |
| `1/24`      | 103 × 102    | 24    |   |

Waga maksymalna na komorę = `35 kg × (pole_komory / pole_użytkowe_bin)`.
Wewnętrzna wysokość komory = `tier - 10 mm` (utracone na dno).

Kody wariantów: `{footprint}-{bin_height_mm}` — np. `1/4-188`, `1/24-138`.

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
- **Persystencja zamówień** w DB (`ContainerOrder` model + historia per klient).
- **Wycena** persystowana na backendzie (v1 = `localStorage`).
- **Inne nośniki niż MiB 640×440** (v1 = tylko ten pojemnik).
- **Multi-warehouse** w jednym zamówieniu.
