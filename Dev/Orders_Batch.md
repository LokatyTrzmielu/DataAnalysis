# Orders/Batch — instrukcja dla Claude Code

## Cel

Na podstawie danych wczytanych z plików Excel (eksporty WMS) wygenerować raport z rekomendowanymi wartościami do ręcznego wpisania w arkuszu **Dashboard** pliku `SolDimTool_V2_7_3.xlsm`, w sekcjach:

- **Order Information** → `Orders / Day`, `Orderlines / Order`
- **Station based** → `Orders/Batch` (5 pozycji), `Commonality` (5 pozycji)
- **Picking** → `Hours / Day`, `System Factor`

Aplikacja **nie modyfikuje** pliku SolDimTool. Wynikiem jest wyłącznie czytelny raport tekstowy / JSON z gotowymi wartościami.

---

## Dane wejściowe

Aplikacja wczytuje eksporty WMS — pliki Excel zawierające historię zleceń. Zakłada się, że aplikacja potrafi już je odczytać i znormalizować do ustrukturyzowanej postaci. Dla tego modułu potrzebne są następujące pola na poziomie wiersza (jedna linia zlecenia = jeden rekord):

| Pole               | Opis                                                        | Wymagane |
|--------------------|-------------------------------------------------------------|----------|
| `order_id`         | Identyfikator zlecenia                                      | ✓        |
| `order_date`       | Data zlecenia (`date` lub `datetime`)                       | ✓        |
| `order_time`       | Czas zlecenia (`time` lub część `datetime`) — jeśli dostępny | opcjonalne |
| `orderline_count`  | Liczba linii w zleceniu (lub 1 jeśli dane są na poziomie linii) | ✓  |
| `quantity`         | Liczba sztuk na linię                                       | opcjonalne |
| `sku`              | Indeks artykułu — do obliczenia commonality                 | opcjonalne |

Jeśli dane są na poziomie linii (jeden wiersz = jedna linia zlecenia), aplikacja grupuje po `order_id` w celu obliczenia `orderline_count`.

---

## Logika obliczeń

### 1. Orders / Day → komórka `C16`

```
orders_per_day = COUNT(distinct order_id) / COUNT(distinct order_date)
```

Użyj mediany dziennej liczby zleceń zamiast średniej, jeśli rozkład jest silnie prawoskośny (np. peak sezonowy). Zaokrąglij do pełnej liczby całkowitej.

**Raport powinien zawierać:**
- średnią dzienną
- medianę dzienną
- percentyl 90. (P90) — jako sygnał peak load
- rekomendowaną wartość (domyślnie: mediana; jeśli P90/mediana > 1,5 → zaproponuj P90 z komentarzem)

---

### 2. Orderlines / Order → komórka `C17`

```
ol_per_order = MEAN(orderline_count per order_id)
```

Zaokrąglij do 2 miejsc po przecinku. Raport zawiera również medianę i P90.

---

### 3. Hours / Day → komórka `A29`

#### Wykrywanie obecności czasu w danych

Sprawdź, czy kolumna `order_time` (lub część `datetime`) jest dostępna i zawiera zróżnicowane wartości godzinowe:

```python
has_time = (
    'order_time' in df.columns
    and df['order_time'].notna().sum() > 0.5 * len(df)          # >50% wierszy ma czas
    and df['order_time'].nunique() > 10                          # przynajmniej 10 różnych wartości
)
```

#### Jeśli `has_time = True` — wnioskowanie okna operacyjnego

1. Dla każdego dnia wyznacz `min_hour` i `max_hour` zleceń.
2. Oblicz medianę `max_hour - min_hour` jako `observed_window`.
3. Dodaj bufor operacyjny +0,5h (czas na otwarcie / zamknięcie zmiany).
4. Zaokrąglij w górę do pełnej godziny.

```
hours_per_day = ceil(median(max_hour - min_hour) + 0.5)
```

Ogranicz wynik do przedziału `[1, 24]`.

**Raport powinien zawierać:**
- wykryte okno operacyjne (min–max godzina ze wszystkich dni)
- medianę okna
- rekomendowaną wartość `Hours / Day`
- flagę `time_detected: true/false`

#### Jeśli `has_time = False`

Nie da się wywnioskować okna. Zastosuj wartości domyślne i poinformuj użytkownika:

```
hours_per_day = 8    # typowa jednozmianowa operacja magazynowa
```

Raport zawiera ostrzeżenie: `"Brak danych czasowych — przyjęto domyślną wartość 8h. Zweryfikuj ręcznie."`

#### Tryb widoku (`A31`)

Komórka `A31` przyjmuje jedną z dwóch wartości tekstowych:

| Wartość w SolDimTool | Kiedy stosować                                              |
|----------------------|-------------------------------------------------------------|
| `hourly view`        | `hours_per_day ≤ 8` lub analiza godzinowa jest istotna     |
| `daily view`         | `hours_per_day > 8` lub dane bez czasu (domyślnie dzienny) |

Raport wskazuje rekomendowaną wartość i uzasadnienie.

---

### 4. System Factor → komórka `C29`

System Factor reprezentuje procentowe straty wydajności (przerwy, przestoje, zmiany). Wartość wpisywana jako ułamek dziesiętny (np. `0.10` = 10%).

Aplikacja **nie oblicza** System Factor z danych WMS (WMS nie rejestruje przestojów maszyny). Zawsze zwracaj wartość domyślną:

```
system_factor = 0.10
```

Raport zawiera notatkę: `"Wartość domyślna 10%. Dostosuj ręcznie na podstawie danych serwisowych maszyny."`

---

### 5. Orders/Batch (5 pozycji) → komórki `B21`–`B25`

Pięć pozycji reprezentuje różne scenariusze batch size do porównania w SolDimTool. Celem jest pokrycie sensownego zakresu: od pojedynczego zlecenia do realnego maksimum operacyjnego.

#### Algorytm doboru wartości

**Krok 1 — wyznacz `max_batch`**

```
max_batch = floor(orders_per_day / 4)
```

Racjonalnie: operator nie powinien kompletować batcha dłużej niż ~15 minut (1/4 godziny przy typowym tempie), co ogranicza liczbę zleceń w batchu.

Ogranicz: `max_batch = max(5, min(max_batch, 100))`

**Krok 2 — wygeneruj 5 punktów**

Użyj skali logarytmicznej (małe wartości dają największy przyrost wydajności):

```python
import math

def suggest_batch_sizes(max_batch: int) -> list[int]:
    raw = [
        1,
        max(2, round(max_batch * 0.10)),
        max(3, round(max_batch * 0.25)),
        max(4, round(max_batch * 0.50)),
        max_batch,
    ]
    # Usuń duplikaty, zachowaj kolejność rosnącą
    seen = []
    for v in raw:
        if v not in seen:
            seen.append(v)
    # Jeśli < 5 unikalnych — dopełnij interpolacją
    while len(seen) < 5:
        gaps = [(seen[i+1] - seen[i], i) for i in range(len(seen)-1)]
        _, idx = max(gaps)
        seen.insert(idx + 1, (seen[idx] + seen[idx+1]) // 2)
    return sorted(seen[:5])
```

**Przykład** dla `orders_per_day = 260` → `max_batch = 65`:

| Pozycja | Wartość | Komórka |
|---------|---------|---------|
| 1.      | 1       | `B21`   |
| 2.      | 7       | `B22`   |
| 3.      | 16      | `B23`   |
| 4.      | 33      | `B24`   |
| 5.      | 65      | `B25`   |

---

### 6. Commonality (5 pozycji) → komórki `C21`–`C25`

Commonality = odsetek linii zleceń wskazujących na ten sam nośnik/pozycję co poprzednia linia w batchu (efekt hit rate). Wartość wpisywana jako ułamek dziesiętny (`0.05` = 5%).

#### Jeśli kolumna `sku` jest dostępna — oblicz empirycznie

Dla każdej pary kolejnych linii w batchu (symulacja batch=10):

```python
def estimate_commonality(df, batch_size=10, sample_batches=500):
    """
    Losowo próbkuje batche z danych i sprawdza, ile kolejnych linii
    ma ten sam SKU co poprzednia linia w batchu.
    """
    hits = []
    orders = df['order_id'].unique()
    for _ in range(sample_batches):
        sampled = np.random.choice(orders, size=min(batch_size, len(orders)), replace=False)
        lines = df[df['order_id'].isin(sampled)]['sku'].tolist()
        if len(lines) < 2:
            continue
        batch_hits = sum(1 for i in range(1, len(lines)) if lines[i] == lines[i-1])
        hits.append(batch_hits / (len(lines) - 1))
    return round(np.mean(hits), 3) if hits else 0.0

base_commonality = estimate_commonality(df)
```

Wygeneruj 5 wartości jako siatkę wokół `base_commonality`:

```python
def commonality_range(base: float) -> list[float]:
    lo = max(0.0, base - 0.05)
    hi = min(0.25, base + 0.10)
    step = (hi - lo) / 4
    return [round(lo + i * step, 2) for i in range(5)]
```

#### Jeśli `sku` niedostępne

Użyj wartości domyślnych i zaznacz w raporcie:

```
[0.00, 0.05, 0.10, 0.15, 0.20]
```

Nota w raporcie: `"Brak kolumny SKU — użyto domyślnego zakresu 0–20%. Dostosuj na podstawie wiedzy o asortymencie."`

---

## Format raportu wyjściowego

Raport generowany jest jako blok tekstowy (lub opcjonalnie JSON) gotowy do odczytu przez użytkownika. Każda wartość zawiera: rekomendację, uzasadnienie i komórkę docelową w SolDimTool.

### Przykład raportu (format tekstowy)

```
╔══════════════════════════════════════════════════════════════╗
║         SolDimTool v2.7.3 — Dashboard Input Report          ║
║         Źródło: export_wms_2025_Q1.xlsx                      ║
╚══════════════════════════════════════════════════════════════╝

── ORDER INFORMATION ─────────────────────────────────────────

  Orders / Day            komórka C16
  ─────────────────────────────────────
  Średnia dzienna:        247,3
  Mediana dzienna:        260,0
  Percentyl 90. (P90):   318,0
  ► Rekomendacja:         260        ← wpisz w C16

  Orderlines / Order      komórka C17
  ─────────────────────────────────────
  Średnia:                2,31
  Mediana:                2,00
  Percentyl 90.:          4,00
  ► Rekomendacja:         2,30       ← wpisz w C17

── STATION BASED ─────────────────────────────────────────────

  Orders/Batch (5 pozycji)            komórki B21–B25
  ─────────────────────────────────────────────────────
  max_batch = floor(260 / 4) = 65
  ┌──────┬─────────┬──────────┐
  │ Poz. │ Wartość │ Komórka  │
  ├──────┼─────────┼──────────┤
  │  1.  │       1 │   B21    │
  │  2.  │       7 │   B22    │
  │  3.  │      16 │   B23    │
  │  4.  │      33 │   B24    │
  │  5.  │      65 │   B25    │
  └──────┴─────────┴──────────┘

  Commonality (5 pozycji)             komórki C21–C25
  ─────────────────────────────────────────────────────
  Oszacowanie empiryczne (SKU): 0,04
  ┌──────┬──────────┬──────────┐
  │ Poz. │ Wartość  │ Komórka  │
  ├──────┼──────────┼──────────┤
  │  1.  │    0,00  │   C21    │
  │  2.  │    0,02  │   C22    │
  │  3.  │    0,05  │   C23    │
  │  4.  │    0,09  │   C24    │
  │  5.  │    0,14  │   C25    │
  └──────┴──────────┴──────────┘

── PICKING ───────────────────────────────────────────────────

  Hours / Day             komórka A29
  ─────────────────────────────────────
  Wykryto dane czasowe:   TAK
  Okno operacyjne:        06:12 – 14:47 (typowy dzień)
  Mediana okna:           8,3h
  ► Rekomendacja:         9          ← wpisz w A29

  Adjusting View          komórka A31
  ─────────────────────────────────────
  ► Rekomendacja:         daily view ← wpisz w A31
  Uzasadnienie:           Hours/Day > 8

  System Factor           komórka C29
  ─────────────────────────────────────
  ► Rekomendacja:         0,10       ← wpisz w C29
  ⚠  Wartość domyślna. Dostosuj na podstawie danych serwisowych maszyny.

══════════════════════════════════════════════════════════════
  Ostrzeżenia: brak
  Wygenerowano: 2025-04-14 09:32:11
══════════════════════════════════════════════════════════════
```

### Opcjonalny format JSON

```json
{
  "source_file": "export_wms_2025_Q1.xlsx",
  "generated_at": "2025-04-14T09:32:11",
  "warnings": [],
  "dashboard": {
    "C16": { "value": 260,   "label": "Orders / Day",        "basis": "mediana dzienna" },
    "C17": { "value": 2.30,  "label": "Orderlines / Order",  "basis": "średnia" },
    "B21": { "value": 1,     "label": "Orders/Batch 1." },
    "B22": { "value": 7,     "label": "Orders/Batch 2." },
    "B23": { "value": 16,    "label": "Orders/Batch 3." },
    "B24": { "value": 33,    "label": "Orders/Batch 4." },
    "B25": { "value": 65,    "label": "Orders/Batch 5." },
    "C21": { "value": 0.00,  "label": "Commonality 1." },
    "C22": { "value": 0.02,  "label": "Commonality 2." },
    "C23": { "value": 0.05,  "label": "Commonality 3." },
    "C24": { "value": 0.09,  "label": "Commonality 4." },
    "C25": { "value": 0.14,  "label": "Commonality 5." },
    "A29": { "value": 9,     "label": "Hours / Day",         "time_detected": true },
    "A31": { "value": "daily view", "label": "Adjusting View" },
    "C29": { "value": 0.10,  "label": "System Factor",       "default": true }
  }
}
```

---

## Ostrzeżenia i walidacja

Przed wygenerowaniem raportu sprawdź i dołącz do sekcji `warnings`:

| Warunek                                          | Komunikat                                                                                   |
|--------------------------------------------------|---------------------------------------------------------------------------------------------|
| `orders_per_day < 10`                            | `"Bardzo mała liczba zleceń — zweryfikuj zakres dat danych."`                              |
| `ol_per_order > 50`                              | `"Wysoka liczba linii/zlecenie — sprawdź czy dane nie są na poziomie linii zamiast zleceń."` |
| `ol_per_order < 1`                               | `"Liczba linii/zlecenie < 1 — błąd agregacji lub niekompletne dane."`                       |
| `P90 / median_orders > 2.0`                      | `"Silna sezonowość (P90/mediana > 2×) — rozważ użycie P90 zamiast mediany dla C16."`       |
| `has_time = False`                               | `"Brak danych czasowych — Hours/Day ustawione na domyślne 8h."`                             |
| `hours_per_day > 16`                             | `"Wykryte okno operacyjne > 16h — możliwe dane z wielu zmian lub błąd w danych czasowych."` |
| `sku` niedostępne                                | `"Brak kolumny SKU — Commonality oparte na wartościach domyślnych."`                        |
| `max_batch < 5`                                  | `"Bardzo mała liczba zleceń dziennie — zakres batch size może być niereprezentacyjny."`     |

---

## Ograniczenia i założenia

- Aplikacja zakłada, że dane WMS obejmują **co najmniej 10 dni roboczych** — przy mniejszej próbie wyniki mogą być niestabilne.
- `System Factor` jest zawsze domyślny (`0.10`) — WMS nie rejestruje przestojów maszyny.
- Komórka `C31` (Hit rate: ON/OFF) **nie jest ustawiana** przez ten moduł — zależy od konfiguracji maszyny, nie od danych zamówieniowych.
- Komórki konfiguracji stacji (share of order load, VLM/Station, Picker/Station itp.) są poza zakresem tego modułu.
- Wartości `Commonality` są symetrycznym zakresem wokół estymatora empirycznego — użytkownik może dostosować ręcznie.
