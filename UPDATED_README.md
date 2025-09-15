# RockMundo — Developer README (Updated 2025-09-09 21:40)

RockMundo is a modern, AI‑assisted music‑career simulation inspired by classic browser MMOs. Players form bands, write/record music, book gigs, tour, and climb the **World Pulse** charts while balancing skills, lifestyle, finances, and fandom.

This README gives you a **1‑file quickstart** for running a *testable* local build, a tour of the repo, and a checklist to validate the vertical slice.

---

## ⚡ Quick Start (Backend)

**Prereqs**: Python 3.11+, SQLite 3.39+, Git. (Frontend dev uses Node.js 18; HTML pages can be served directly without Node.)
If you plan to work on the frontend, run `nvm use 18` to match the required Node version.

```bash
# 1) Create venv + install deps
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) Configure environment
cp .env.example .env
# If you plan to store attachments locally:
cp .env.example .env.storage

# 3) Initialize DB (migrations + seeds)
# Migrations are SQL files in backend/migrations/sql/*.sql
./scripts/migrate.sh                 # apply Alembic migrations (skips ones already run)
python -m backend.scripts.seed_demo  # creates demo data: users, skills, genres, etc.

# 4) Run the API
uvicorn api:app --reload --port 8000
```

Open:
- **Swagger / OpenAPI** → http://localhost:8000/docs
- **Front-end static pages (served by FastAPI)** → http://localhost:8000/frontend/login.html

> The API mounts `frontend/pages` at `/frontend` for convenient local testing.

### Required environment variables

The application expects these keys in your `.env` file:

- `ROCKMUNDO_DB_PATH` – path to the SQLite database file.
- `ROCKMUNDO_JWT_SECRET` – secret used to sign JWTs.
- `ROCKMUNDO_JWT_ISS` – issuer claim for JWT tokens.
- `ROCKMUNDO_JWT_AUD` – audience claim for JWT tokens.
- `ROCKMUNDO_JWT_ALG` – algorithm used to sign tokens.
- `ROCKMUNDO_ACCESS_TTL_MIN` – access token lifetime in minutes.
- `ROCKMUNDO_REFRESH_TTL_DAYS` – refresh token lifetime in days.
- `DISCORD_WEBHOOK_URL` – optional webhook for ops notifications.
- `ROCKMUNDO_RATE_LIMIT_REQUESTS_PER_MIN` – requests allowed per minute.
- `ROCKMUNDO_RATE_LIMIT_STORAGE` – rate limit backend (`memory` or `redis`).
- `ROCKMUNDO_RATE_LIMIT_REDIS_URL` – Redis URL if using redis for rate limiting.
- `ROCKMUNDO_CORS_ALLOWED_ORIGINS` – comma-separated list of allowed origins.
- `ROCKMUNDO_REALTIME_BACKEND` – backend for realtime features.
- `ROCKMUNDO_REALTIME_REDIS_URL` – Redis URL if realtime backend is `redis`.

If using `.env.storage` for uploads, set:

- `STORAGE_BACKEND` – storage backend (`local` or `s3`).
- `STORAGE_LOCAL_ROOT` – directory for local file storage.
- `STORAGE_PUBLIC_BASE_URL` – public URL base for uploaded files.
- `S3_BUCKET`, `S3_REGION`, `S3_ENDPOINT_URL`, `S3_FORCE_PATH_STYLE`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` – S3/MinIO settings.

---

## 🌐 Frontend (static pages)

The current frontend is a set of **static HTML pages + JS** under `frontend/pages` and `frontend/components`. These are mounted by the backend for local dev. You can also open them via a simple static server if you prefer:

```bash
# Option A: use backend mount (recommended) → http://localhost:8000/frontend/login.html
# Option B: serve statically (example using Python)
cd frontend && python -m http.server 5173
```

Key entry pages for the vertical slice:
- `frontend/pages/login.html`
- `frontend/pages/profile.html`
- `frontend/pages/band_dashboard.html`
- `frontend/pages/gig_booking.html`
- `frontend/pages/schedule.html`
- `frontend/pages/popularity_dashboard.html`

These pages call backend JSON endpoints with `fetch()`; ensure your `.env` points the frontend to `http://localhost:8000` if you change ports.

---

## 🧱 Repository Layout

```
backend/
  api.py, main.py                 # FastAPI app entry
  auth/                           # JWT, RBAC, MFA hooks, dependencies
  core/                           # config, scheduler, logging/observability, rate limiting
  middleware/                     # Observability, Locale, RateLimit, Admin MFA
  routes/                         # ~170+ route modules (player, bands, gigs, music, admin/*, etc.)
  services/                       # ~160+ service modules (business logic)
  migrations/sql/*.sql            # 30+ SQLite migrations (charts, royalties, FTS, etc.)
  seeds/                          # genre, lifestyle, stage equipment, weather...
  scripts/seed_demo.py            # demo data seeding script
  storage/                        # base, local, s3 adapters
  realtime/                       # WebSocket/SSE gateway helpers + tests
frontend/
  pages/*.html                    # static testable pages
  components/*.js / *.vue         # widgets (notifications, schedule, player, charts, etc.)
tests/
  ...                             # ~50+ pytest suites (realtime, lifestyle, charts, etc.)
docs/ TDD_with_diagrams.md        # high-level design notes/diagrams
assets/ images/                   # branding & UI assets
```

---

## 🔐 Auth & RBAC

- JWT-based sessions with RBAC guards on sensitive routes.
- Login flow routes are under `backend/auth/routes.py` and `backend/routes/*` where guarded.
- For local testing, the seed script creates a demo user; check the console output and `.env` for default credentials/secret.

---

## 🗄️ Data, Migrations & Seeds

- Migrations live in `backend/migrations/sql`. They are applied in-order by the startup DB initializer.
- Full-text search (FTS5) and **World Pulse** (daily/weekly charts) are included.
- `backend/scripts/seed_demo.py` seeds minimum data (skills, genres, equipment, etc.) and creates test users and bands for smoke tests.

---

## 📡 Realtime

- WebSocket hub for jam sessions and notifications (`tests/realtime/*` cover gateway basics).
- SSE/WS are optional for the MVP vertical slice; the static pages fall back to polling where applicable.

---

## 🧪 Tests

```bash
pytest -q
```

Note: Some suites exercise optional features (audio mixing, streaming). If your workstation lacks those deps, skip marks like `-m "not slow"`.

---

## 🧭 Minimal Playable Vertical Slice (what to try)

1) **Sign in** at `/frontend/login.html` (seeded user).  
2) **Create/Select avatar** and **create a band**.  
3) **Book a small gig** using `/gigs/book` then **perform** it.  
4) Check **XP / skills progression**, **fandom/popularity**, and **cashflow** on profile and dashboards.  
5) Explore **World Pulse** snapshots and basic **inbox/notifications**.

If any step fails, consult the **Outstanding work** checklist below.

---

## 🧰 Dev Tips

- Logs are JSON-formatted with request IDs; see `backend/core/logging.py`.
- Admin/ops endpoints surface health checks, WAL status, counts, and job triggers.
- Storage defaults to local disk; S3 adapter is scaffolded (enable via `.env.storage`).

---

## 📝 License

MIT (see LICENSE if present in repo root).

---

## 📌 Outstanding Work (High-level)

For a detailed, testable MVP checklist, see `OUTSTANDING_WORK.md` included in this ZIP.
