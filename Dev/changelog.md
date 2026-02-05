# Changelog

Rejestr zmian w projekcie DataAnalysis.

## Format wpisów
```
### [YYYY-MM-DD HH:MM] - Typ zmiany
- Opis zmiany
- Branch/Commit: nazwa_brancha lub hash commita
```

---

### [2026-02-05 13:00] - Refactor
- **Usunięcie zbędnej logiki "Exclusion settings"**:
  - Problem: Po uproszczeniu outlier detection do carrier-based, zostały artefakty starego systemu
  - "Detect outliers" button był redundantny - analiza robi to samo automatycznie
  - "Exclusion settings" checkbox był bezcelowy - outliers i tak pokazują się jako NOT_FIT
  - Rozwiązanie: Usunięto oba, outliers widoczne w wynikach pod "Does not fit any carrier"
- Zmiany w plikach:
  - `src/ui/views/capacity_view.py`: Usunięto `render_data_quality_settings()`, dodano uproszczone `render_analysis_settings()`
  - `src/ui/app.py`: Usunięto `capacity_dq_result` i `outlier_validation_enabled` z session_state
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
