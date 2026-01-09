# Plan: Moduł Storage Planning (VBM/VLM) - Opcja Zaawansowana

> **Status:** Do doprecyzowania
> **Źródło:** Analiza pliku `D:\VS\Inspiration\Calculators\01_calc_stock.xlsx`
> **Data:** 2026-01-08

## Wybrane parametry

| Parametr | Wartość |
|----------|---------|
| **Opcja** | C: Zaawansowana - pełne planowanie magazynu |
| **Priorytetyzacja** | VBM przed VLM (mniejszy system ma pierwszeństwo) |
| **Eksport** | Jeden plik CSV z kolumną `system` (VBM/VLM/UNFIT) |
| **Pojemność systemów** | Konfigurowalna przez użytkownika w UI |
| **Analiza kosztów** | Nie |
| **Symulacje** | Tak - what-if scenarios |

---

## Kontekst z Excela

### Dane źródłowe (01_calc_stock.xlsx):
| Element | Wartość |
|---------|---------|
| VBM (Vertical Buffer Module) | HU: 370×570×200mm, max 35kg, 100m³, 8m wysokości |
| VLM (Vertical Lift Module) | Tray: 3650×864×200mm, max 500kg, 45m³, 10m wysokości |
| Wynik | Klasyfikacja SKU: "does it fit VBM/VLM?" |
| Arkusze | Masterdata (17,239), VBM (13,295), VLM (16,524), 714 SKUs (nie pasują) |

### Co już ma aplikacja:
- System nośników (CarrierConfig) w `src/core/carriers.py`
- CapacityAnalyzer - dopasowanie SKU do nośników (6 orientacji)
- Statusy fit: FIT, BORDERLINE, NOT_FIT
- Stałe VLM/MIB zdefiniowane ale nieużywane aktywnie

---

## Architektura rozwiązania

### Nowe pliki do utworzenia:
```
src/
├── core/
│   └── storage_systems.py      # NOWY - konfiguracja VBM/VLM
├── analytics/
│   └── storage_planner.py      # NOWY - główna logika
├── reporting/
│   └── storage_reports.py      # NOWY - eksport CSV
└── ui/views/
    └── storage_view.py         # NOWY - zakładka UI
```

### Pliki do modyfikacji:
```
src/
├── core/
│   └── types.py                # Nowe typy Pydantic
└── ui/
    └── app.py                  # Dodanie zakładki "📦 Storage"
```

---

## Szczegółowy plan implementacji

### Faza 1: Model danych i konfiguracja systemów

**Plik: `src/core/storage_systems.py`**
```python
@dataclass
class StorageSystem:
    system_id: str              # "VBM" | "VLM"
    name: str
    # Wymiary HU/Tray (mm)
    inner_length_mm: float
    inner_width_mm: float
    inner_height_mm: float
    max_weight_kg: float
    # Pojemność modułu
    module_capacity_m3: float   # np. VBM: 100m³, VLM: 45m³
    module_height_m: float      # np. VBM: 8m, VLM: 10m
    priority: int               # 1=VBM (wyższy), 2=VLM

# Domyślne wartości z Excela:
DEFAULT_SYSTEMS = [
    StorageSystem("VBM", "Vertical Buffer Module",
                  370, 570, 200, 35, 100.0, 8.0, priority=1),
    StorageSystem("VLM", "Vertical Lift Module",
                  3650, 864, 200, 500, 45.0, 10.0, priority=2),
]
```

**Plik: `src/core/types.py` - nowe typy**
```python
class StorageAllocation(BaseModel):
    sku: str
    system: Literal["VBM", "VLM", "UNFIT"]
    fit_status: Literal["FIT", "BORDERLINE", "NOT_FIT"]
    volume_m3: float
    stock_qty: int
    stock_volume_m3: float
    reason: str | None  # dlaczego nie pasuje

class StoragePlanningResult(BaseModel):
    allocations: list[StorageAllocation]
    summary: StorageSummary
    capacity_plan: CapacityPlan
    simulation_results: list[SimulationResult] | None

class StorageSummary(BaseModel):
    vbm_sku_count: int
    vbm_volume_m3: float
    vlm_sku_count: int
    vlm_volume_m3: float
    unfit_sku_count: int
    unfit_volume_m3: float
    total_sku_count: int
    total_volume_m3: float

class CapacityPlan(BaseModel):
    vbm_modules_needed: int
    vlm_modules_needed: int
    vbm_utilization_pct: float
    vlm_utilization_pct: float

class SimulationResult(BaseModel):
    scenario_name: str
    stock_multiplier: float  # np. 1.2 = +20% stock
    vbm_modules_needed: int
    vlm_modules_needed: int
    unfit_increase: int
```

---

### Faza 2: Logika Storage Planner

**Plik: `src/analytics/storage_planner.py`**

Klasa `StoragePlanner`:

1. **`allocate_skus(masterdata, systems)`**
   - Iteracja po SKU
   - Próba dopasowania do VBM (priorytet 1)
   - Jeśli nie pasuje → próba VLM (priorytet 2)
   - Jeśli nie pasuje → UNFIT z powodem
   - Sprawdzanie 6 orientacji (L×W×H permutacje)
   - Sprawdzanie wagi

2. **`calculate_capacity_plan(allocations, systems)`**
   - Suma objętości per system
   - Obliczenie: `modules_needed = ceil(total_volume / (module_capacity * utilization))`
   - Default utilization: VBM=0.68, VLM=0.75 (z config.py)

3. **`run_simulation(masterdata, systems, scenarios)`**
   - Scenariusze: stock +10%, +20%, +50%
   - Dla każdego: przeliczenie alokacji i capacity plan
   - Zwrot delta vs baseline

---

### Faza 3: Raportowanie

**Plik: `src/reporting/storage_reports.py`**

1. **`generate_allocation_report(result) -> DataFrame`**
   - Kolumny: sku, system, fit_status, volume_m3, stock_qty, stock_volume_m3, reason
   - Jeden plik CSV z kolumną `system`

2. **`generate_summary_report(result) -> dict`**
   - KPI do wyświetlenia w UI
   - Format key-value dla main_report

3. **`generate_capacity_report(result) -> DataFrame`**
   - Ile modułów per system
   - Utilization %

---

### Faza 4: UI - Zakładka Storage

**Plik: `src/ui/views/storage_view.py`**

Layout:
```
┌─────────────────────────────────────────────────────────────────┐
│ 📦 Storage Planning                                             │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ VBM SKUs    │ │ VLM SKUs    │ │ Unfit SKUs  │ │ Total Vol.  │ │
│ │   13,295    │ │   3,229     │ │     714     │ │  5,468 m³   │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ ⚙️ System Configuration                                         │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ VBM: 370×570×200mm, 35kg, 100m³ capacity    [Edit]        │   │
│ │ VLM: 3650×864×200mm, 500kg, 45m³ capacity   [Edit]        │   │
│ └───────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ 📊 Capacity Planning                                            │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ VBM Modules needed: 15  (utilization: 64%)                │   │
│ │ VLM Modules needed: 66  (utilization: 72%)                │   │
│ └───────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ 🔮 What-If Simulations                                          │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Scenario          │ VBM Mod │ VLM Mod │ Unfit Δ           │   │
│ │ Baseline          │    15   │    66   │     -             │   │
│ │ Stock +20%        │    18   │    79   │   +52             │   │
│ │ Stock +50%        │    23   │    99   │  +187             │   │
│ │ [+ Add scenario]                                          │   │
│ └───────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ 📥 [Download Allocation Report]  [Download Capacity Plan]       │
└─────────────────────────────────────────────────────────────────┘
```

Funkcjonalności:
1. **KPI Cards** - podsumowanie alokacji
2. **Konfiguracja systemów** - edycja parametrów VBM/VLM
3. **Capacity Planning** - ile modułów potrzeba
4. **Symulacje** - slider dla stock multiplier + wyniki
5. **Eksport** - przycisk pobierania CSV

---

### Faza 5: Integracja z app.py

**Plik: `src/ui/app.py`**

Dodanie nowej zakładki między "Capacity" a "Performance":
```python
tabs = st.tabs([
    "📥 Import",
    "✓ Validation",
    "📦 Capacity",
    "📦 Storage",    # NOWA
    "📈 Performance",
    "📄 Reports"
])
```

---

## Kolejność implementacji

1. **`src/core/storage_systems.py`** - model StorageSystem
2. **`src/core/types.py`** - nowe typy Pydantic
3. **`src/analytics/storage_planner.py`** - główna logika
4. **`src/reporting/storage_reports.py`** - eksport CSV
5. **`src/ui/views/storage_view.py`** - widok UI
6. **`src/ui/app.py`** - integracja zakładki

---

## Weryfikacja

### Testy jednostkowe:
- [ ] Test alokacji: SKU pasujące do VBM nie trafiają do VLM
- [ ] Test priorytetyzacji: SKU pasujące do obu → przypisane do VBM
- [ ] Test UNFIT: zbyt duże SKU mają reason
- [ ] Test capacity: obliczenia modułów

### Testy integracyjne:
- [ ] Import danych z Excela (Masterdata)
- [ ] Porównanie wyników z arkuszami VBM/VLM/714 SKUs
- [ ] Eksport CSV i weryfikacja formatu

### Testy UI:
- [ ] `streamlit run src/ui/app.py`
- [ ] Edycja parametrów systemów
- [ ] Symulacje what-if
- [ ] Pobieranie raportów

### Oczekiwane wyniki (z Excela):
| System | SKU Count | Objętość |
|--------|-----------|----------|
| VBM    | 13,295    | 968 m³   |
| VLM    | 3,229*    | 2,973 m³ |
| UNFIT  | 714       | -        |

*Uwaga: VLM w Excelu ma 16,524 bo nie ma priorytetyzacji - z priorytetem VBM będzie mniej

---

## Do doprecyzowania

- [ ] Szczegóły algorytmu priorytetyzacji
- [ ] Dokładne scenariusze symulacji
- [ ] Integracja z istniejącym systemem nośników (carriers.py)
- [ ] Czy VBM/VLM to osobne systemy czy rozszerzenie carriers?
