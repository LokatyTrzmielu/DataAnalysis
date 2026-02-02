# Changelog

Rejestr zmian w projekcie DataAnalysis.

## Format wpisów
```
### [YYYY-MM-DD HH:MM] - Typ zmiany
- Opis zmiany
- Branch/Commit: nazwa_brancha lub hash commita
```

---

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
