# Changelog

Rejestr zmian w projekcie DataAnalysis.

## Format wpisów
```
### [YYYY-MM-DD HH:MM] - Typ zmiany
- Opis zmiany
- Branch/Commit: nazwa_brancha lub hash commita
```

---

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
