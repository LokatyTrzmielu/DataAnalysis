# UI_Audit_Prompt_For_Claude.md

**Wytyczne do przeprowadzenia pełnego audytu UI aplikacji Streamlit**

---

## 1. Zakres audytu

### 1.1. Typografia

Zweryfikuj:

* spójność rozmiarów nagłówków (H1/H2/H3) w powtarzalnych sekcjach,
* jednolitość akapitów ([`st.write`](https://st.write), [`st.markdown`](https://st.markdown)) — rozmiar fontu, odstępy, grubość,
* spójność typografii w komponentach (KPI, wykresy, tabele),
* brak przypadkowych różnic w wielkości tekstu między sekcjami.

### 1.2. Layout i spacing

Sprawdź:

* spójność marginesów i paddingów w [`st.container`](https://st.container)`()`, [`st.columns`](https://st.columns)`()` i panelach,
* czy nie występują „rozjechane” elementy layoutu,
* czy odstępy między sekcjami są jednolite,
* czy powtarzalne sekcje mają identyczną strukturę i proporcje.

### 1.3. Kolorystyka

Przeanalizuj:

* spójność kolorów tła, paneli, tekstu i akcentów,
* czy nie występują przypadkowe odcienie (np. #1E1E1E vs #1F1F1F),
* czy kolory akcentów są używane konsekwentnie:
  * zielony → pozytywne KPI,
  * czerwony → błędy,
  * pomarańczowy → gabaryty/Kardex,
* czy kontrast tekstu jest wystarczający na ciemnym tle.

### 1.4. Komponenty Streamlit

Sprawdź:

* spójność stylu [`st.metric`](https://st.metric)`()` (kolory, rozmiary, ikonografia),
* spójność wykresów (kolory, grubość linii, tła),
* spójność tabel ([`st.dataframe`](https://st.dataframe)) — nagłówki, szerokości kolumn, kolory,
* spójność przycisków ([`st.button`](https://st.button), `st.download_button`).

### 1.5. Powtarzalne sekcje

Zweryfikuj, czy sekcje takie jak:

* KPI,
* wykresy,
* tabele,
* panele informacyjne,

mają identyczne:

* spacing,
* style ramek,
* kolory tła,
* zaokrąglenia rogów,
* cienie.

---

## 2. Oczekiwany sposób pracy

### 2.1. Analiza kodu

Przejdź przez wszystkie pliki aplikacji i zidentyfikuj miejsca generujące UI.

### 2.2. Raportowanie problemów

Każdy problem opisz w formacie:

* **Problem:**
* **Lokalizacja w kodzie:**
* **Dlaczego to jest niespójne:**
* **Propozycja poprawy:**

### 2.3. Refaktoryzacja

Zaproponuj:

* wyodrębnienie stylów do [`theme.py`](https://theme.py),
* stworzenie komponentów UI (np. `render_kpi_box()`),
* ujednolicenie spacingu i kolorów,
* wprowadzenie zmiennych stylu (np. `PRIMARY_BG = "#1E1E1E"`).

---

## 3. Format końcowego raportu

Zwróć raport w strukturze:
UI Consistency Audit — Wyniki
1. Typografia
- Problem 1: ...
- Problem 2: ...
2. Layout i spacing
- Problem 1: ...
- Problem 2: ...
3. Kolorystyka
- Problem 1: ...
- Problem 2: ...
4. Komponenty
- Problem 1: ...
- Problem 2: ...
5. Rekomendacje refaktoryzacji
- ...
6. Lista zmian do wdrożenia
- ...
