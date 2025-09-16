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

- **Career Loop Overview** — Follow the end-to-end band lifecycle managed by `routes/daily_loop_routes.py` and orchestrated through `routes/schedule_routes.py`, which tick rehearsals, releases, and tours on the in-game calendar.
  - *Core Scheduler Routes* — `routes/daily_loop_routes.py`, `routes/schedule_routes.py`, and `routes/ai_tour_scheduler_routes.py` post the activities generated by every other system onto the shared calendar so day, week, and season ticks remain in sync.
  - *Service & Automation Layer* — `services/schedule_service.py`, `services/scheduler_service.py`, and `services/lifestyle_scheduler.py` apply fatigue, cooldowns, and availability gates each rollover while cronable jobs such as `jobs/lifestyle_jobs.py`, `jobs/world_pulse_jobs.py`, and `jobs/random_events.py` keep long-running effects (sponsorship decay, chart updates, event timers) moving without player input.
  - *Admin & Live-Ops Hooks* — Operations staff tune pacing with `routes/admin_routes.py` feature toggles, adjust season cadence through `routes/admin_season_routes.py`, and inject headline beats via `routes/admin_events_routes.py`; their calls land in `services/admin_service.py` and `services/admin_audit_service.py` so every change is auditable against the live scheduler.
- **Characters & Bands** — Manage roster creation, relationships, and shared resources through core routers like `routes/character.py`, `routes/band_routes.py`, and `routes/band_relationship_routes.py`.
  - *Player-Facing Routes* — `routes/character.py` drafts and edits members, `routes/band_routes.py` allocates shared budgets/inventories, `routes/rehearsal_routes.py` + `routes/learning_routes.py` pace practice plans, and `routes/management_routes.py` applies manager directives that ripple into production and touring.
  - *Service Backbone* — `services/character_service.py`, `services/band_service.py`, `services/band_relationship_service.py`, and `services/rehearsal_service.py` coordinate stat growth, chemistry modifiers, and shared cooldowns while AI helpers (`services/ai_manager_service.py`, `services/npc_band_service.py`) keep rival crews evolving in parallel.
  - *Admin & Training Ops* — Mentorship tooling lives in `routes/admin_apprenticeship_routes.py`, `routes/admin_tutor_routes.py`, and `routes/admin_workshop_routes.py`; they call into `services/apprenticeship_admin_service.py`, `services/tutor_admin_service.py`, and `services/workshop_admin_service.py` so live-ops can open new lessons, audit rosters, or fast-track NPC hires without direct DB edits.
- **Music Production** — Write, record, and release tracks via pipelines exposed in `routes/songwriting_routes.py`, `routes/production_routes.py`, and `routes/recording_routes.py`.
  - *Player-Facing Routes* — `routes/songwriting_routes.py` spins up briefs/co-writes, `routes/production_routes.py` manages studio blocks and producer perks, `routes/recording_routes.py` resolves takes/editing fatigue, and release prep flows through `routes/album_routes.py`, `routes/indie_release_routes.py`, and `routes/distribution.py`.
  - *Service Backbone* — `services/songwriting_service.py`, `services/music_production_service.py`, `services/production_service.py`, `services/song_service.py`, and `services/song_remaster_service.py` score quality, persist mix states, and manage asset lifecycles, while `services/song_popularity_service.py` plus forecasting helpers (e.g., `services/song_popularity_forecast.py`) predict chart momentum before marketing spend goes out.
  - *Admin & Curriculum Tools* — Balance teams tweak content supply through `routes/admin_course_routes.py`, `routes/admin_book_routes.py`, and `routes/admin_song_popularity_routes.py`; these surface `services/course_admin_service.py`, `services/book_admin_service.py`, and `services/song_popularity_service.py` so studio lists, skill curricula, and chart weighting can be tuned between seasons.
- **Performance & Touring** — Book gigs, plan routes, and optimize setlists with `routes/gig.py`, `routes/tour_routes.py`, `routes/tour_planner_routes.py`, and `routes/setlist_routes.py`.
  - *Player-Facing Routes* — `routes/gig.py` handles contracts/payouts, `routes/tour_routes.py` and `routes/tour_planner_routes.py` generate itineraries, `routes/setlist_routes.py` tweaks set cohesion, while `routes/tour_logistics_routes.py`, `routes/transport_routes.py`, `routes/ai_tour_scheduler_routes.py`, and `routes/ticketing_routes.py` keep freight, travel, automation, and attendance forecasts aligned.
  - *Service Backbone* — `services/gig_service.py`, `services/tour_service.py`, `services/tour_logistics_service.py`, `services/transport_service.py`, `services/ticketing_service.py`, and `services/setlist_service.py` compute stamina costs, crew wages, routing penalties, and ticket curves; `services/ai_tour_manager_service.py` mirrors these calculations for NPC competitors.
  - *Admin & Venue Ops* — Live-ops manage calendars via `routes/admin_book_routes.py` and `routes/admin_venue_routes.py`, schedule headline events through `routes/admin_events_routes.py`, and audit outcomes with `routes/admin_analytics_routes.py`; under the hood `services/book_admin_service.py`, `services/venue_service.py`, `services/venue_availability.py`, and `services/admin_analytics_service.py` enforce capacity rules, blackout windows, and reporting.
- **Economy & Commerce** — Handle cashflow, merchandising, and trading using `routes/economy_routes.py`, `routes/banking_routes.py`, `routes/merch_routes.py`, and `routes/marketplace_routes.py`.
  - *Player-Facing Routes* — `routes/economy_routes.py` reconciles ledgers/royalties, `routes/banking_routes.py` handles credit lines, `routes/merch_routes.py` and `routes/gear_routes.py` run storefronts, while `routes/payment_routes.py`, `routes/shipping_routes.py`, and `routes/trade_routes.py` close purchase loops and peer swaps.
  - *Service Backbone* — `services/economy_service.py`, `services/bank_service.py`, `services/merch_service.py`, `services/gear_service.py`, `services/payment_service.py`, `services/shipping_service.py`, and `services/trade_route_service.py` maintain tax rules, risk bands, fulfillment delays, and escrow releases. Background workers like `jobs/royalty_clearing_job.py` and `jobs/sponsor_reconciliation_job.py` move payouts into player wallets on schedule.
  - *Admin & Compliance Ops* — `routes/admin_economy_routes.py`, `routes/admin_business_routes.py`, `routes/admin_shop_event_routes.py`, and `routes/admin_city_shop_routes.py` feed into `services/economy_admin_service.py`, `services/admin_audit_service.py`, and `services/city_shop_service.py` so finance teams can tweak multipliers, run flash sales, or freeze suspicious accounts.
- **Fan Engagement & Media** — Grow audiences and publicity through `routes/fan_club_routes.py`, `routes/fan_interaction_routes.py`, `routes/media_routes.py`, and `routes/promotion_routes.py`.
  - *Player-Facing Routes* — `routes/fan_club_routes.py` builds tier programs, `routes/fan_interaction_routes.py` resolves meetups and reactive choices, `routes/media_routes.py` and `routes/media_publicity_routes.py` schedule press, while `routes/promotion_routes.py`, `routes/media_exposure_routes.py`, `routes/radio_routes.py`, `routes/stream_routes.py`, and `routes/fan_logistics_routes.py` govern campaign reach and event fulfillment.
  - *Service Backbone* — `services/fan_club_service.py`, `services/fan_interaction_service.py`, `services/fan_insight_service.py`, `services/media_service.py`, `services/media_event_service.py`, and `services/social_media_training_service.py` calculate sentiment arcs, convert fans into spenders, and record media cooldowns. Alerting hooks in `services/notifications_service.py` broadcast spikes to other systems.
  - *Admin & Moderation Ops* — Reputation teams moderate via `routes/admin_media_moderation_routes.py` and `routes/admin_events_routes.py`; the calls are executed by `services/media_moderation_service.py` and `services/admin_notifications_service.py` so media storms, bans, or limited-time showcases can be launched or defused quickly.
- **Progression & Competition** — Track achievements, leaderboards, and seasonal play using `routes/achievement_routes.py`, `routes/world_pulse_routes.py`, `routes/chart_routes.py`, and `routes/tournament_routes.py`.
  - *Player-Facing Routes* — `routes/achievement_routes.py` dispenses badges/XP, `routes/world_pulse_routes.py` exposes global standings, `routes/chart_routes.py` forecasts genre trends, while `routes/tournament_routes.py`, `routes/quest_routes.py`, `routes/replay_routes.py`, and `routes/legacy_routes.py` run events, narrative arcs, and prestige resets.
  - *Service Backbone* — `services/achievement_service.py`, `services/world_pulse_service.py`, `services/chart_service.py`, `services/tournament_service.py`, `services/quest_service.py`, and `services/legacy_service.py` compute score differentials, apply buffs/debuffs, and gate unlock trees. Automation flows through `jobs/world_pulse_jobs.py` and `jobs/random_events.py` to refresh ladders and trigger special quests.
  - *Admin & Balance Ops* — Seasonal knobs live in `routes/admin_season_routes.py`, `routes/admin_song_popularity_routes.py`, `routes/admin_xp_routes.py`, `routes/admin_xp_event_routes.py`, `routes/admin_xp_item_routes.py`, and `routes/karma_admin_routes.py`; they persist through `services/xp_admin_service.py`, `services/song_popularity_service.py`, `services/quest_admin_service.py`, and `services/admin_analytics_service.py` to ensure every bracket change is tracked.
- **Administrative & Modding** — Configure live ops tooling and extensions through `routes/admin_routes.py`, `routes/admin_monitoring_routes.py`, `routes/admin_modding_routes.py`, and `routes/modding_routes.py`.
  - *Control Plane Routes* — `routes/admin_routes.py`, `routes/admin_monitoring_routes.py`, `routes/admin_audit_routes.py`, `routes/admin_notifications_routes.py`, and `routes/admin_analytics_routes.py` expose feature flags, ban tools, telemetry dashboards, and alert dispatch so operators can react to real-time issues.
  - *Service Backbone* — `services/admin_service.py`, `services/admin_audit_service.py`, `services/admin_notifications_service.py`, and `services/admin_analytics_service.py` centralize RBAC enforcement, change logging, and broadcast pipelines; `services/mod_marketplace_service.py` powers both creator uploads and moderator workflows.
  - *Modding & Toolchain* — `routes/admin_modding_routes.py` + `routes/modding_routes.py` work with `realtime/admin_gateway.py` and `realtime/social_gateway.py` to review submissions, while asset validation and publishing happen in `services/mod_marketplace_service.py` so curated mods roll out safely.
- **Realtime Communication** — Coordinate live jams, chat, and alerts via `routes/jam_ws.py`, `routes/chat_routes.py`, and `routes/notifications_ws.py`.
  - *Player-Facing Routes* — `routes/jam_ws.py` syncs session tempo, `routes/chat_routes.py` spans inbox/DM/group messaging, `routes/notifications_ws.py` pushes broadcast alerts, and REST fallbacks in `routes/notification_routes.py`, `routes/notifications_routes.py`, and `routes/support_slot_routes.py` ensure parity for players without persistent WS connections.
  - *Service Backbone* — `services/jam_service.py`, `services/chat_service.py`, `services/notifications_service.py`, and `services/support_service.py` maintain presence data, session history, and queue prioritization while the gateway implementations (`realtime/gateway.py`, `realtime/jam_gateway.py`, `realtime/dialogue_gateway.py`, `realtime/social_gateway.py`) handle fan-out.
  - *Admin & Safety Ops* — `routes/admin_notifications_routes.py` and `realtime/admin_gateway.py` let moderators broadcast PSAs, silence abusive rooms, or escalate incidents; the actions are persisted through `services/admin_notifications_service.py` for audit and replay.
- **World & Environment** — Simulate locations, weather, and special events using `routes/venue_routes.py`, `routes/weather_routes.py`, `routes/city_routes.py`, and `routes/event_routes.py`.
  - *Player-Facing Routes* — `routes/venue_routes.py` defines capacities/perks, `routes/weather_routes.py` injects climate modifiers, `routes/city_routes.py` surfaces regional demand sliders, and `routes/event_routes.py` plus `routes/festival_builder_routes.py`, `routes/random_event_routes.py`, and `routes/transport_routes.py` orchestrate festivals, surprise challenges, and travel costs.
  - *Service Backbone* — `services/venue_service.py`, `services/venue_availability.py`, `services/venue_sponsorships_service.py`, `services/weather_service.py`, `services/city_service.py`, `services/event_service.py`, and `services/random_event_service.py` apply localized multipliers, rotate inventories, and schedule background happenings. Logistics hooks in `services/transport_service.py` mirror those changes for touring systems.
  - *Admin & World-Building Ops* — City and venue tuning flows through `routes/admin_city_shop_routes.py`, `routes/admin_venue_routes.py`, and `routes/admin_events_routes.py`, backed by `services/city_shop_service.py`, `services/venue_service.py`, and `services/admin_notifications_service.py`; narrative teams also rely on `jobs/random_events.py` to preview and QA surprise world states before they go live.

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
