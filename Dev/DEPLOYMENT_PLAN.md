# Plan wdrożenia DataVisor do sieci

> Data: 2026-05-02  
> Status: **Draft — do przeglądu**

---

## Context

Aplikacja jest narzędziem wewnętrznym (kilka–kilkanaście osób), budżet do ~20 USD/miesiąc. Cele:
- Szybka analiza danych (Excel → SQL → wyniki)
- Historia wykonanych analiz
- Baza użytkowników z autoryzacją
- Wdrożenie FastAPI + Vue 3 (najpierw skończyć Vue 3, potem deploy)

**Dobra wiadomość**: Aplikacja ma już zaimplementowane ~80% potrzebnej infrastruktury:
- `api/models/user.py` — model użytkowników ✓
- `api/models/analysis_run.py` — historia analiz ✓
- `api/routers/auth.py` — JWT auth ✓
- `api/database.py` — konfiguracja PostgreSQL ✓
- Migracje Alembic ✓

Do zrobienia to głównie **deployment config + dokończenie Vue 3**.

---

## Stos technologiczny (0–10 USD/miesiąc)

| Warstwa | Narzędzie | Koszt | Uzasadnienie |
|---------|-----------|-------|--------------|
| **Frontend** | Vercel (Vue 3 static) | **$0** | Free tier, CDN, auto-deploy z GitHub |
| **Backend API** | Fly.io (FastAPI + Uvicorn) | **$0–3** | Free tier: 3 VM × 256MB, cold start ~1s |
| **Baza danych** | Supabase (PostgreSQL) | **$0** | Free: 500MB, 50k req/dzień |
| **Pliki tymcz.** | Fly.io volumes (lokalnie) | **$0** | Excel parsowany → kasowany, bez S3 |
| **SSL/DNS** | Cloudflare | **$0** | Free tier, własna domena |

**Łączny koszt: ~$0–5/miesiąc** przy lekkim użytkowaniu wewnętrznym.

> Alternatywa: **Railway** ($5–15/mies.) — prostsze zarządzanie all-in-one, ale droższe.

---

## Architektura produkcyjna

```
Użytkownik
    │
    ▼
Cloudflare DNS + SSL
    │
    ├─── app.datavisor.com ──► Vercel (Vue 3 SPA)
    │                              │
    │                              │ API calls
    │                              ▼
    └─── api.datavisor.com ──► Fly.io (FastAPI)
                                    │
                         ┌──────────┼──────────┐
                         ▼          ▼           ▼
                    Supabase    Fly Volume   Fly Volume
                  (PostgreSQL)  (tmp files)  (/reports)
```

---

## Przepływ danych: Excel → SQL (performance)

Obecny przepływ (problematyczny dla prod):
```
Excel upload → Polars in-memory → st.session_state → znika przy odświeżeniu
```

Docelowy przepływ (produkcja):
```
1. Użytkownik uploaduje Excel (multipart/form-data)
2. FastAPI: NamedTemporaryFile → Polars czyta → DataFrame gotowy
3. Polars/DuckDB: analiza → wyniki jako dict
4. PostgreSQL: INSERT INTO analysis_runs (results JSON, metadata)
5. Plik tymczasowy: usunięty (os.unlink)
6. Frontend: poll /runs/{id}/status → wyświetla wyniki
```

**Klucz do szybkości**: Polars + DuckDB są już w kodzie. Baza SQL przechowuje tylko *wyniki*, nie surowe dane. Nie potrzeba konwersji Excel → tabelę PostgreSQL.

---

## Fazy implementacji

### Faza 1: Deployment config (2–3 godz.)

Nowe pliki do stworzenia:
- `Dockerfile` — FastAPI + Uvicorn, Python 3.12-slim
- `fly.toml` — konfiguracja Fly.io (shared-cpu-1x, auto-stop)
- `.env.production` — zmienne środowiskowe (gitignored)

Zmienne środowiskowe (Fly.io secrets):
```
DATABASE_URL=postgresql+asyncpg://...supabase...
SECRET_KEY=<random 32 chars>
ALLOWED_ORIGINS=https://app.datavisor.com
```

---

### Faza 2: Supabase PostgreSQL (30 min.)

1. Utwórz projekt na supabase.com (free tier)
2. Skopiuj `DATABASE_URL` (connection pooling mode)
3. Ustaw `fly secrets set DATABASE_URL=...`
4. Uruchom migracje: `alembic upgrade head`
5. Seed admin: `python -m api.seed admin@firma.com haslo Admin`

---

### Faza 3: Fly.io deployment (1 godz.)

```bash
winget install flyctl
fly auth login
fly launch --no-deploy
fly secrets set DATABASE_URL="..." SECRET_KEY="..."
fly deploy
fly status && fly logs
```

---

### Faza 4: Vue 3 na Vercel (30 min.)

1. Push `frontend/` na GitHub
2. Vercel → "New Project" → auto-detect Vue 3
3. Env var: `VITE_API_URL=https://api.datavisor.com`
4. Każdy push do `main` = auto-deploy

---

### Faza 5: Dokończenie Vue 3 frontend (główna praca)

Brakujące ekrany (priorytet):

| Ekran | Priorytet | Endpoint |
|-------|-----------|----------|
| Login/Register | P0 | `POST /auth/token`, `POST /auth/register` |
| Historia analiz | P0 | `GET /runs`, `GET /runs/{id}` |
| Import pliku + analiza | P0 | `POST /analyze` |
| Zarządzanie carrier'ami | P1 | `GET/POST/DELETE /carriers` |
| Eksport raportów | P1 | `GET /reports/{run_id}` |

---

### Faza 6: Historia analiz + użytkownicy

Model `analysis_run.py` już istnieje. Potrzebna integracja w UI:
- **Lista analiz** → tabela z datą, typem, statusem, notatkami
- **Szczegóły analizy** → wyniki capacity/performance
- **Udostępnianie** → `run_share.py` już istnieje, wymaga UI
- **Panel admin** → zarządzanie użytkownikami (endpoint do dodania)

---

## Kolejność działań

```
Tydzień 1: Infrastruktura
  □ Konto Supabase → baza PostgreSQL
  □ Konto Fly.io → Dockerfile + deploy FastAPI
  □ Test: GET /health → {"status": "ok"}
  □ Migracje Alembic na prod
  □ Konto Vercel → deploy Vue 3 (nawet bez wszystkich ekranów)

Tydzień 2: Vue 3 ekrany krytyczne
  □ Strona logowania (Auth store, JWT w localStorage)
  □ Strona importu pliku → POST /analyze
  □ Historia analiz → GET /runs

Tydzień 3: Pełna funkcjonalność
  □ Wyniki capacity + performance
  □ Eksport PDF/CSV
  □ Panel administratora
```

---

## Pliki krytyczne do modyfikacji

| Plik | Zmiana |
|------|--------|
| `api/main.py` | Dodać CORS dla domeny produkcyjnej |
| `api/routers/auth.py` | Sprawdzić endpoint rejestracji |
| `api/database.py` | Upewnić się, że asyncpg działa z Supabase URL |
| `Dockerfile` | Nowy plik |
| `fly.toml` | Nowy plik |
| `frontend/.env.production` | `VITE_API_URL=https://api.datavisor.com` |

---

## Weryfikacja end-to-end

```bash
# Backend health
curl https://api.datavisor.com/health

# Rejestracja
curl -X POST https://api.datavisor.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@firma.com", "password": "test123", "name": "Test"}'

# Logowanie
curl -X POST https://api.datavisor.com/auth/token \
  -d "username=test@firma.com&password=test123"

# Analiza (z tokenem)
curl -X POST https://api.datavisor.com/analyze \
  -H "Authorization: Bearer <token>" \
  -F "file=@masterdata.xlsx" -F "analysis_type=capacity"

# Historia
curl https://api.datavisor.com/runs -H "Authorization: Bearer <token>"
```

---

## Uwagi

- **Cold start Fly.io**: ~1s przy auto-stop. Akceptowalne dla narzędzia wewnętrznego.
- **Supabase free limits**: 500MB DB + 2GB bandwidth/mies. Wystarczy dla kilkunastu użytkowników.
- **Skalowanie w przyszłości**: Railway ($15/mies.) lub Hetzner VPS (€5/mies.) jako prosty upgrade.
- **Własna domena**: Cloudflare DNS → darmowy SSL.
