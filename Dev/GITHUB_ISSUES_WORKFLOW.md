# GitHub Issues Workflow

## Status: ✅ Aktywny

Workflow skonfigurowany 2026-02-01.

---

## Zasady tworzenia Issues

### Format Issue (minimalny)

```markdown
**Tytuł:** [typ] Krótki opis zadania

**Body:**
Opis co ma zostać zrobione (1-3 zdania)
```

### Labels (podstawowe)

| Label | Kolor | Użycie |
|-------|-------|--------|
| `feature` | 🟢 #0E8A16 | Nowa funkcjonalność |
| `bug` | 🔴 #D73A4A | Naprawa błędu |
| `refactor` | 🔵 #0366D6 | Refaktoryzacja kodu |

### Konwencja tytułów

```
[feature] Dodaj eksport do CSV
[bug] Błąd przy ładowaniu danych z API
[refactor] Wydziel logikę filtrowania do osobnego modułu
```

---

## Workflow współpracy

1. **Ty opisujesz** - co chcesz zrobić (nawet w jednym zdaniu)
2. **Ja doprecyzowuję** - zadaję pytania jeśli potrzeba
3. **Ja tworzę Issue** - używając `gh issue create`
4. **Ty akceptujesz** - lub prosisz o zmiany

---

## Powiązanie z branchami

Po utworzeniu Issue, tworzę branch zgodnie z CLAUDE.md:
- `feature/nazwa` dla feature
- `fix/nazwa` dla bug
- `refactor/nazwa` dla refactor

---

## Komendy GitHub CLI

### Tworzenie labels (jednorazowo)

```bash
gh label create "feature" --color "0E8A16" --description "Nowa funkcjonalność"
gh label create "bug" --color "D73A4A" --description "Naprawa błędu"
gh label create "refactor" --color "0366D6" --description "Refaktoryzacja kodu"
```

### Operacje na Issues

```bash
# Tworzenie issue
gh issue create --title "[feature] Dodaj filtrowanie po dacie" \
  --body "Umożliwić użytkownikowi filtrowanie danych po zakresie dat" \
  --label "feature"

# Lista otwartych issues
gh issue list --state open

# Zamknięcie issue po zakończeniu pracy
gh issue close <number>

# Podgląd konkretnego issue
gh issue view <number>
```

---

## Kiedy tworzymy Issue?

- ✅ Każda nowa funkcjonalność
- ✅ Każdy zgłoszony bug
- ✅ Planowany refactoring
- ❌ Drobne poprawki (typo, formatowanie) - bezpośrednio na main

