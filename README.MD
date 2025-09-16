# RockMundo — Developer README (Updated 2025-09-09 21:40)

RockMundo is a modern, AI‑assisted music‑career simulation inspired by classic browser MMOs. Players form bands, write/record music, book gigs, tour, and climb the **World Pulse** charts while balancing skills, lifestyle, finances, and fandom.

This README gives you a **1‑file quickstart** for running a *testable* local build, a tour of the repo, and a checklist to validate the vertical slice.


## ⚡ Quick Start (Backend)

**Prereqs**: Python 3.11+ (Netlify builds run on 3.11), SQLite 3.39+, Node.js 20.11.1 (see `.nvmrc`), Rust/Cargo, Git, GNU gettext (`msgfmt`). (Static frontend pages can be served directly without Node.)
If you work on the frontend, ensure Node 20.11.1 is active; `nvm use` will read the repo's `.nvmrc`.

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
./scripts/migrate.sh        # apply Alembic migrations (skips ones already run)
python -m backend.scripts.seed_demo  # creates demo data: users, skills, genres, etc.

# 5) Run the API
uvicorn api:app --reload --port 8000
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

## 🏗️ Netlify/CI build setup

Netlify installs a Rust toolchain and expects Python 3.11. To mirror this environment locally:

```bash
# Install Rust (provides cargo)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
export PATH="$HOME/.cargo/bin:$PATH"  # make cargo/rustc available

# Use Python 3.11 as Netlify does
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Match Netlify's frontend build steps
nvm use                      # Node 20.11.1 from .nvmrc
npm ci --prefix frontend
npm run build --prefix frontend
```

These steps reproduce the `build.command` in `netlify.toml` so local builds behave like Netlify's CI pipeline.

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

## 🎮 Gameplay Features and Mechanics

- **Characters & Bands** — Manage roster creation, relationships, and shared resources through core routers like `routes/character.py`, `routes/band_routes.py`, and `routes/band_relationship_routes.py`.
  - `routes/character.py` exposes lifecycle CRUD, talent drafting, and lifestyle toggles; attribute spreads and personality tags here drive rehearsal efficiency, studio fatigue, and social conflicts across the sim.
  - `routes/band_routes.py` wires roster management, shared inventories, practice scheduling, and budget allocations; downstream systems (e.g., `routes/gig.py`, `routes/economy_routes.py`) read this data to determine payouts and skill checks.
  - `routes/band_relationship_routes.py` governs rivalries, alliances, and guest-spots; these modifiers flow into fan conversion rates and unlock collaborative songwriting hooks in `routes/songwriting_routes.py`.
- **Music Production** — Write, record, and release tracks via pipelines exposed in `routes/songwriting_routes.py`, `routes/production_routes.py`, and `routes/recording_routes.py`.
  - `routes/songwriting_routes.py` handles creative briefs, inspiration boosts, and co-write contracts; lyrical/melodic quality scores here influence subsequent recording difficulty and chart potential.
  - `routes/production_routes.py` coordinates studio bookings, mixing/mastering passes, and producer perks; production quality affects release hype, licensing offers, and expense ledgers managed by `routes/economy_routes.py`.
  - `routes/recording_routes.py` simulates session stamina, take tracking, and post-production edits; clean takes reduce fatigue penalties before tours and feed audio assets to `routes/media_routes.py` for previews.
- **Performance & Touring** — Book gigs, plan routes, and optimize setlists with `routes/gig.py`, `routes/tour_routes.py`, `routes/tour_planner_routes.py`, and `routes/setlist_routes.py`.
  - `routes/gig.py` negotiates venue contracts, deposits, and technical riders; success/failure updates cashflow streams, reputation, and fan momentum metrics.
  - `routes/tour_routes.py` and `routes/tour_planner_routes.py` simulate travel logistics, routing fatigue, lodging costs, and routing RNG events; these values feed into burnout systems and economic overhead.
  - `routes/setlist_routes.py` tunes song order, encore odds, and stage prop usage; setlist cohesion modifies performance XP, merch sales multipliers, and live recording unlocks back in production flows.
- **Economy & Commerce** — Handle cashflow, merchandising, and trading using `routes/economy_routes.py`, `routes/banking_routes.py`, `routes/merch_routes.py`, and `routes/marketplace_routes.py`.
  - `routes/economy_routes.py` centralizes budget snapshots, royalty claims, and expense auditing; financial health gates investment options and risk checks for expansion features.
  - `routes/banking_routes.py` provides loans, savings yields, and escrow for contracts; interest schedules affect weekly balance sheets and unlock credit-locked gear in `routes/marketplace_routes.py`.
  - `routes/merch_routes.py` manages SKU creation, inventory flow, and per-gig pop-up shops; merch performance loops back into fan affinity tiers and influences `routes/fan_club_routes.py` perks.
  - `routes/marketplace_routes.py` surfaces gear auctions, staff hiring, and licensing deals; acquisitions here add modifiers to production quality and touring resilience stats.
- **Fan Engagement & Media** — Grow audiences and publicity through `routes/fan_club_routes.py`, `routes/fan_interaction_routes.py`, `routes/media_routes.py`, and `routes/promotion_routes.py`.
  - `routes/fan_club_routes.py` spins up membership tiers, loyalty rewards, and retention challenges; success unlocks steady revenue streams and protects against popularity decay.
  - `routes/fan_interaction_routes.py` covers meet-and-greets, AMA sessions, and reactive responses to events; engagement responses alter sentiment which in turn boosts chart multipliers and touring attendance.
  - `routes/media_routes.py` coordinates press kits, interviews, and broadcast slots; coverage affects hype curves before releases and the sponsorship tiers exposed by `routes/economy_routes.py`.
  - `routes/promotion_routes.py` orchestrates marketing campaigns, social boosts, and influencer partnerships; campaign ROI metrics decide whether virality events trigger and unlock collaborative quests.
- **Progression & Competition** — Track achievements, leaderboards, and seasonal play using `routes/achievement_routes.py`, `routes/world_pulse_routes.py`, `routes/chart_routes.py`, and `routes/tournament_routes.py`.
  - `routes/achievement_routes.py` awards milestone XP, trait badges, and unlock tokens; these rewards open advanced contracts and narrative arcs in other systems.
  - `routes/world_pulse_routes.py` simulates global chart ticks, weekly resets, and territory bonuses; standings provide buffs/debuffs to touring demand and media interest.
  - `routes/chart_routes.py` publishes genre charts, breakout lists, and predictive analytics; chart placements boost royalty calculations and determine NPC rival behavior.
  - `routes/tournament_routes.py` runs bracketed events, streaming showcases, and prize payouts; competitive ranking grants exclusive merch recipes and tour venues.
- **Administrative & Modding** — Configure live ops tooling and extensions through `routes/admin_routes.py`, `routes/admin_monitoring_routes.py`, `routes/admin_modding_routes.py`, and `routes/modding_routes.py`.
  - `routes/admin_routes.py` controls feature flags, player sanctions, and live event scheduling; these toggles maintain server balance and shape seasonal metas.
  - `routes/admin_monitoring_routes.py` surfaces KPIs, job queues, and anomaly alerts; telemetry guides balance patches that ripple across economy, progression, and touring payouts.
  - `routes/admin_modding_routes.py` plus `routes/modding_routes.py` enable content injection, scripting hooks, and asset validation; curated mods add new venues, instruments, or stories without breaking persistence.
- **Realtime Communication** — Coordinate live jams, chat, and alerts via `routes/jam_ws.py`, `routes/chat_routes.py`, and `routes/notifications_ws.py`.
  - `routes/jam_ws.py` powers low-latency rehearsal lobbies with tempo sync, allowing collaborative skill gains and unlocking improv challenges.
  - `routes/chat_routes.py` bridges asynchronous inbox, DM, and group channels; social cohesion scores influence member retention and unlock co-op quests.
  - `routes/notifications_ws.py` streams alerts for tour incidents, chart updates, and mod actions; timely feedback loops keep players reactive to shifting conditions.
- **World & Environment** — Simulate locations, weather, and special events using `routes/venue_routes.py`, `routes/weather_routes.py`, `routes/city_routes.py`, and `routes/event_routes.py`.
  - `routes/venue_routes.py` catalogs capacities, acoustics, and resident perks; venue traits modify gig success probabilities and staging costs.
  - `routes/weather_routes.py` models forecasts, severe events, and travel delays; weather penalties cascade into touring fatigue and emergency expense spikes.
  - `routes/city_routes.py` manages population tastes, economy tiers, and cultural trends; city profiles steer fan acquisition rates and sponsor availability.
  - `routes/event_routes.py` schedules festivals, storyline beats, and holidays; global events create limited-time buffs, exclusive merch windows, and cross-system narrative triggers.

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
