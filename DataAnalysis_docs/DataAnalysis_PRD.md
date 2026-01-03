Product Requirements Document (PRD) - DataAnalysis
1. Podsumowanie produktu
- Nazwa: DataAnalysis
- Opis: Aplikacja do analizy danych operacyjnych i masterdata w kontekście projektów automatyzacji magazynowej.
- Cel: Umożliwienie szybkiej, lokalnej analizy pojemnościowej i wydajnościowej na dużych wolumenach danych (do 2 mln wierszy).
- Użytkownik docelowy: Konsultanci ds. intralogistyki, analitycy danych, projektanci systemów ASRS.
Aplikacja ma wspierać proces analizy danych w projektach automatyzacji magazynowej, obejmując:
•	Analizę pojemnościową SKU (gabaryty, waga, dopasowanie do nośników Kardex).
•	Analizę wydajnościową na podstawie danych historycznych zleceń (linie/h, piki, struktura zamówień).
•	Generowanie raportów w formacie CSV (opcjonalnie XLSX) oraz wizualizacji KPI.
2. Decyzje techniczne (MVP)
- Architektura: Local-first, modularna (ingest, walidacja, analityka, raportowanie, UI).
- Format danych: Parquet jako format roboczy, wejście XLSX/CSV/TXT.
- Silnik obliczeń: DuckDB (agregacje, joiny) + opcjonalnie Polars (transformacje).
- UI: Streamlit (lokalny, intuicyjny interfejs).
3. Wymagania funkcjonalne
Import danych:
•	Obsługa plików XLSX, CSV, TXT.
•	Mapping Wizard (interaktywny wybór kolumn + auto-sugestie).
•	Konwersja do formatu roboczego Parquet.
Walidacja danych:
•	Sprawdzenie braków, zer, błędnych typów.
•	Raport jakości danych (Data Quality Scorecard).
•	Imputacja braków medianą (RAW vs ESTIMATED).
Analiza pojemnościowa:
•	Obliczanie kubatury SKU.
•	Dopasowanie gabarytowe do nośników (6 orientacji + opcjonalne ograniczenia UPRIGHT_ONLY, FLAT_ONLY).
•	Uwzględnienie limitów wagowych.
•	Estymacja liczby sztuk na nośnik.
•	Sizing maszyn z parametrem utilization (np. VLM 0.75, MiB 0.68).
Analiza wydajnościowa:
•	KPI: lines/hour, orders/hour, units/hour, unique SKU/hour.
•	Obsługa harmonogramów zmian (base + overlay).
•	Uwzględnienie productive hours (np. 7h z 8h zmiany).
•	Raport piku (P90/P95).
Raportowanie:
•	Eksport CSV (raport główny + listy problematycznych SKU).
•	Sekcje: Data Quality, Capacity, Performance.
•	RAW vs ESTIMATED wyniki + udział imputacji.
UI/UX:
•	Streamlit (lokalnie, darmowo): 
o	Upload plików.
o	Mapping Wizard.
o	Konfiguracja zmian + overlay.
o	Parametry nośników + utilization.
o	Podgląd raportów + pobieranie ZIP.
4. Wymagania niefunkcjonalne
Wydajność: 
•	Obsługa do 2 mln wierszy ORDERS w <5 min analizy.
•	Format roboczy: Parquet.
•	Silnik obliczeń: DuckDB (agregacje) + Polars (transformacje).
Bezpieczeństwo: 
•	Lokalna praca (brak chmury).
•	Brak wrażliwych danych w logach.
Architektura: 
•	Modularna: ingest / validation / analytics / reporting / ui.
•	Możliwość migracji do serwera w przyszłości.
5. Interfejs użytkownika
- Layout: główny panel z zakładkami (Import, Walidacja, Analiza, Raporty).
- Sidebar: parametry analizy (utilization, harmonogram zmian, imputacja).
- Panele: podgląd danych, raporty, wykresy KPI.
6. Stack technologiczny
•	Backend: Python 3.11+, DuckDB, Polars. 
•	UI: Streamlit. 
•	Raporty: Pandas (tylko do eksportu CSV), opcjonalnie Plotly dla wykresów.
7. Ograniczenia i założenia
- Brak integracji z chmurą (wersja lokalna).
- Brak czasu zakończenia w Orders (analiza event-based).
- Obsługa do 2 mln wierszy ORDERS i 200k SKU.
- Wersja MVP bez obsługi API zewnętrznych.
8. Copy (teksty interfejsu)
- Przyciski: 'Wgraj plik', 'Uruchom analizę', 'Eksportuj raport'.
- Komunikaty: 'Analiza w toku...', 'Braki danych uzupełnione medianą (szacunek)'.
9. Pliki projektu
```
docs/
├── DataAnalysis_PRD       					 # Ten dokument
├── customers_shifts       					 # Harmonogram zmian zależny od dnia tygodnia — model i zasady
├── Struktura katalogów aplikacji       	 # Przykładowa struktura katalogów aplikacji
├── Struktura katalogów projektu			 # Przykładowa struktura katalogów projektu
├── Profil projektu							 # Przykładowa profil projektu
├── Format danych							 # Format danych przy obliczeniach
```
10. Parametry konfiguracyjne
•	0 = brak danych (wymiary, waga, ilości). 
•	Stock basis policy: AUTO (prefer MAX), z opcją RAW vs ESTIMATED. 
•	Imputation: median (global), flagi w raporcie.
•	Borderline threshold = 2 mm dla dopasowania gabarytowego. 
•	Constraints orientacji: ANY, UPRIGHT_ONLY, FLAT_ONLY. 
•	Utilization: VLM 0.70–0.80, MiB 0.60–0.75. 
•	Timestamp w Orders = moment realizacji/wysyłki (output throughput).
11. Struktura repozytorium
 Dataanalysis_repo/ 
├── core/ (modele, typy, utils) 
├── ingest/ (import i konwersja do Parquet) 
├── validation/ (reguły walidacji, raporty błędów) 
├── analytics/ (DuckDB/Polars, KPI, ABC) 
├── reporting/ (eksport CSV, generowanie raportów) 
├── ui/ (Streamlit interfejs) 
└── tests/ (testy jednostkowe)
12. Kolejność kroków implementacji
Krok 1: Import danych → konwersja do Parquet (staging). 
Krok 2: Walidacja danych (braki, duplikaty, dopasowanie SKU). 
Krok 3: Analityka (KPI wydajnościowe, analiza pojemnościowa). 
Krok 4: Raportowanie (CSV, opcjonalnie Parquet). 
Krok 5: UI w Streamlit (upload plików, konfiguracja parametrów, pasek postępu, eksport wyników).
13. Raporty
Data Quality: 
•	Coverage % dla wymiarów, wagi, ilości.
•	Listy: MissingCritical, SuspectOutliers, HighRiskBorderline.
Capacity: 
•	Fit status (FIT/BORDERLINE/NOT FIT).
•	N per carrier, limiting factor (gabaryt/waga).
•	Liczba maszyn (z utilization).
Performance: 
•	KPI godzinowe, zmianowe, overlay.
•	Piki (max, P95).
•	Udział overlay w pracy.
14. MVP – Zakres pierwszej wersji
•	Import + Mapping Wizard. 
•	Walidacja + imputacja medianą. 
•	Analiza pojemnościowa (EA, constraints, utilization). 
•	Analiza wydajnościowa (lines/hour, shifts, overlay). 
•	Raport CSV + ZIP z listami problematycznych SKU. 
•	UI w Streamlit.


