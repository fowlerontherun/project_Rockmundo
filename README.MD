# RockMundo — Developer README (Updated 2025-09-09 21:40)

RockMundo is a modern, AI‑assisted music‑career simulation inspired by classic browser MMOs. Players form bands, write/record music, book gigs, tour, and climb the **World Pulse** charts while balancing skills, lifestyle, finances, and fandom.

This README gives you a **1‑file quickstart** for running a *testable* local build, a tour of the repo, and a checklist to validate the vertical slice.


## ⚡ Quick Start (Backend)

**Prereqs**: Python 3.11+, SQLite 3.39+, Node.js 18+, Git, GNU gettext (`msgfmt`). (Static frontend pages can be served directly without Node.)
If you work on the frontend, ensure Node 18 is active, e.g. with `nvm use 18`.

```bash
# 1) Create venv + install deps

python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) Compile translation catalogs (generates `.mo` files for deployment)
python scripts/compile_translations.py  # requires msgfmt; missing it triggers a runtime error (see backend/utils/i18n.py)

# 3) Configure environment
cp .env.example .env
# If you plan to maintain a separate storage config:
cp .env.example .env.storage
mkdir -p var/storage                      # create storage dir
# ensure the runtime user can write to it
chmod -R 775 var/storage                  # adjust UID/GID as needed
# 4) Initialize DB (migrations + seeds)
./backend/scripts/migrate.sh        # apply Alembic migrations (skips ones already run)
# 3) Initialize DB (migrations + seeds)
./scripts/migrate.sh        # apply Alembic migrations (skips ones already run)
python -m backend.scripts.seed_demo  # creates demo data: users, skills, genres, etc.

# 5) Run the API
uvicorn backend.api:app --reload --port 8000
```

> When running via Docker, mount `var/storage` and ensure it is owned by the
> container user so attachments can be written:
>
> ```bash
> docker run -v "$(pwd)/var/storage:/app/var/storage" rockmundo
> # inside the container: chown -R app:app /app/var/storage
> ```

Open:
- **Swagger / OpenAPI** → http://localhost:8000/docs
- **Front-end static pages (served by FastAPI)** → http://localhost:8000/frontend/login.html

> The API mounts `frontend/pages` at `/frontend` for convenient local testing.

## Demo Credentials

- Email: demo@rockmundo.test
- Password: demo123

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
live3d/                    # 3D performance rendering prototype
tests/
  ...                             # ~50+ pytest suites (realtime, lifestyle, charts, etc.)
docs/ TDD_with_diagrams.md        # high-level design notes/diagrams
assets/ images/                   # branding & UI assets
```

---

## 🔐 Auth & RBAC

- JWT-based sessions with RBAC guards on sensitive routes.
- Login flow routes are under `backend/auth/routes.py` and `backend/routes/*` where guarded.
- For local testing, the seed script creates a demo user (see **Demo Credentials** above).

---

## 🗄️ Data, Migrations & Seeds

- Run migrations with `scripts/migrate.sh` – it skips revisions already applied.
- `make db-reset` removes `rockmundo.db` and re-applies migrations for a clean slate.
- Full-text search (FTS5) and **World Pulse** (daily/weekly charts) are included.
- `backend/scripts/seed_demo.py` seeds minimum data (skills, genres, equipment, etc.) and creates test users and bands for smoke tests.

---

## 📡 Realtime

- WebSocket hub for jam sessions and notifications (`tests/realtime/*` cover gateway basics).
- SSE/WS are optional for the MVP vertical slice; the static pages fall back to polling where applicable.
- The realtime routers mount only when `ROCKMUNDO_REALTIME_BACKEND` is *not* set to `disabled`.
  - `ROCKMUNDO_REALTIME_BACKEND=memory` (default) keeps an in-process hub for local dev.
  - `ROCKMUNDO_REALTIME_BACKEND=redis` enables Redis pub/sub.
  - `ROCKMUNDO_REALTIME_BACKEND=disabled` skips the WebSocket routes so the frontend's polling fallback is used.

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
 - Storage defaults to the local filesystem. Attachments live under `var/storage/mail/attachments`, which is created on startup. To try S3 instead, set `STORAGE_BACKEND=s3` in your env file (e.g. `.env` or `.env.storage`) and provide your bucket details.

---

## 📝 License

MIT (see LICENSE if present in repo root).

---

## 📌 Outstanding Work (High-level)

For a detailed, testable MVP checklist, see `OUTSTANDING_WORK.md` included in this ZIP.
