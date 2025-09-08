
# RockMundo Backend

## Overview
RockMundo is a modern music industry simulation game inspired by the depth of legacy titles like Popmundo, rebuilt with a fully featured, modular backend in Python/FastAPI. This backend powers a persistent, multiplayer world where players can create and manage avatars, form bands, record and distribute music, tour globally, and interact with a dynamic, AI-driven simulation.

This document outlines the current state of implemented features, the roadmap for future development, and the architecture that ties it all together.

## Feature Summary
- **Core Platform & API:** FastAPI services with role-based access, migrations, and OpenAPI docs.
- **Player & Avatar System:** Customizable avatars with cosmetic skins and expressive emotes.
- **Bands, Collaborations & Gigs:** Tools for managing bands, collaborations, and gig history.
- **Music Content: Songs, Albums, EPs:** Create and digitally distribute music under business rules.
- **Streaming, Sales, Charts & Royalties:** Track plays, sales, charts, and royalty earnings.
- **Progression & Skills:** Skill progression with random events and a daily scheduler.
- **Lifestyle & Event Engine:** Lifestyle stats and random events influence player performance.
- **NPCs & World Simulation:** AI-controlled bands generate gigs and releases to populate the world.
- **Community & Governance:** Karma, elections, and moderation tools support community life.
- **Venues, Sponsors & Ads:** Venue sponsorships and ad revenue systems.
- **Transport, Touring & Logistics:** AI tour scheduling and fan logistics planning.
- **Admin & Ops:** Admin analytics, routes, and audit logging.
- **Media & Promotion:** Media exposure systems and podcast scaffolding.
- **Docs, Wiki & Onboarding:** Large-scale name generator and documentation seeds.

## Game Loops
- **Login Streaks:** Daily logins build streaks that grant increasing rewards.
- **Rotating Challenges:** Challenges rotate each day to provide fresh tasks and bonuses.
- **Weekly Milestones:** Weekly goals reset to deliver larger rewards.
- **Tiered Rewards:** Completion of loops advances players through tiered reward tracks.

---

## Implemented Features

### 1) Core Platform & API
- FastAPI routes and services scaffolding across all major domains (auth, bands, charts, distribution, streaming, transport, admin, lifestyle, NPCs, events, sponsorships, etc.)
- Database migrations and seed data for initial world setup.
- Role-based access control (RBAC) groundwork with role/permission checks in place.
- OpenAPI documentation via FastAPI.

### 2) Player & Avatar System
- Avatar models, routes, and schemas for player creation and customization.
- Cosmetic skin system (models/routes/schemas) with support for future 3D designer integration.
- Emote models for expressive interactions.

### 3) Bands, Collaborations & Gigs
- Band management with collaboration support for joint songs/albums.
- Gig and live performance tracking.
- Festival history and promotion mechanics.

### 4) Music Content: Songs, Albums, EPs
- Song and album creation with business rule enforcement (e.g., EP max song count).
- Digital distribution endpoints for releasing music.

### 5) Streaming, Sales, Charts & Royalties
- Streaming models and services for tracking plays.
- Sales models/routes for digital and vinyl formats.
- Global chart system with fame and promotion modifiers.
- Royalties framework.

### 6) Progression & Skills
- Base skill system with progression and XP gains.
- Random event system (injury, illness, burnout) affecting skills.
- Daily scheduler for timed events.

### 7) Lifestyle & Event Engine
- Lifestyle models and services (sleep, drinking, stress) influencing skills.
- Random lifestyle events impacting player stats.
- Notification routes for communicating events to players.

### 8) NPCs & World Simulation
- NPC bands to populate the world and simulate activity.
- AI-controlled gigs and releases.

### 9) Community & Governance
- Karma tracking and admin moderation tools.
- Election and community role systems.

### 10) Venues, Sponsors & Ads
- Venue sponsorship management (naming, logos, website links).
- CPM and fixed-fee ad revenue models.

### 11) Transport, Touring & Logistics
- AI tour scheduler and transport optimizer.
- Fan logistics engine for interactive tour planning.

### 12) Admin & Ops
- Admin routes and analytics services.
- Audit logging for admin actions.

### 13) Media & Promotion
- Media exposure and promotion systems.
- Podcast scaffolding.

### 14) Docs, Wiki & Onboarding
- Large-scale name generator with thousands of first/last name combinations.
- Documentation seeds for internal/external usage.

---

## Roadmap (Next Steps)

### Immediate Priorities
1. Centralize RBAC & permissions.
2. Finalize royalties and sponsor revenue system.
3. Implement daily baseline XP and lifestyle-linked progression.
4. Launch interactive tour planner UI.
5. Build real-time admin dashboard.
6. Ship 3D avatar designer + skin marketplace.

### Feature Expansions
- Country-specific charts and leaderboards.
- Advanced NPC simulation with seasonal and random events.
- Community-driven festivals and genre trends.
- Player-submitted cosmetic moderation workflows.
- Daily game loop with login streaks, rotating challenges, weekly item drops, and tiered rewards (see docs/daily_game_loop.md).

---

## Technical Stack
- **Language:** Python 3.x
- **Framework:** FastAPI
- **Database:** SQLite (migrations included)
- **ORM:** SQLAlchemy / Pydantic models
- **Auth:** Role-based (JWT-ready)
- **Architecture:** Modular services, routes, and models
- **Deployment:** Uvicorn / Docker-ready

---

## Setup Instructions
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy the example environment and adjust as needed: `cp .env.example .env`
4. Apply migrations: `alembic upgrade head`
5. Seed the database with demo data: `python backend/scripts/seed_demo.py`
6. Run the server: `uvicorn backend.main:app --reload`
7. Access the API docs at `http://localhost:8000/docs`

## Monitoring & Alerts

For operational insight, the backend exposes an admin metrics endpoint and
WebSocket channels:

- `GET /admin/monitoring/metrics` returns CPU usage, memory consumption, and the
  number of active admin sessions.
- `WS /admin/realtime/ws` streams real-time alerts. Clients subscribe to
  topics such as `economy` or `moderation` after connecting.

These endpoints power the admin dashboard widget under
`frontend/src/admin/dashboard/`.

## Learning & Burnout Mechanics

Skill progression uses level-gated learning methods. Higher tiers grant more experience but carry greater burnout risk.

| Level Range | Learning Method Category | XP Rate | Burnout Risk |
|-------------|-------------------------|---------|--------------|
| 1-3         | Books / YouTube          | 1.0x    | Low          |
| 4-7         | University / Apprenticeships / Bandmates | 1.5x | Medium |
| 8-10        | Tutors / Masterclasses   | 2.0x    | High         |

Burnout increases with continuous practice:

| Practice Hours | XP Modifier | Burnout Gain |
|----------------|------------|--------------|
| 0-1            | 0.5x       | 0%           |
| 2-4            | 1.0x       | 5%           |
| 5-6            | 1.2x       | 15%          |
| 7+             | 1.5x       | 30%          |

See [docs/learning_methods.md](docs/learning_methods.md) for detailed progression rules and meta-modifiers.

## Testing
Run the test suite from the project root:

```bash
pytest
```

The tests will automatically create a temporary SQLite database and seed sample data. Coverage information is printed after the run.

---

## Contributing
We welcome contributions via pull requests. Please ensure all new features include:
- Models (SQLAlchemy + Pydantic)
- Routes with proper HTTP methods
- Service layer for business logic
- Unit tests
- OpenAPI annotations

---

© 2025 RockMundo
