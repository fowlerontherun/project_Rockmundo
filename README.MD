
# RockMundo Backend

## Overview
RockMundo is a modern music industry simulation game inspired by the depth of legacy titles like Popmundo, rebuilt with a fully featured, modular backend in Python/FastAPI. This backend powers a persistent, multiplayer world where players can create and manage avatars, form bands, record and distribute music, tour globally, and interact with a dynamic, AI-driven simulation.

This document outlines the current state of implemented features, the roadmap for future development, and the architecture that ties it all together.

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
3. Apply migrations: `alembic upgrade head`
4. Seed the database with initial data.
5. Run the server: `uvicorn main:app --reload`
6. Access the API docs at `http://localhost:8000/docs`

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
