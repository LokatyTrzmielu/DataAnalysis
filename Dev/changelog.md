# Changelog

Rejestr zmian w projekcie DataAnalysis.

## Format wpisów
```
### [YYYY-MM-DD HH:MM] - Typ zmiany
- Opis zmiany
- Branch/Commit: nazwa_brancha lub hash commita
```

---

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
