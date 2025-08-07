# 🎸 RockMundo Development Wiki

Welcome to **RockMundo** – a next-generation, community-driven band simulation game inspired by Popmundo but rebuilt for the modern age. This page tracks all current and upcoming features across the development cycle.

---

## 🧭 Vision

RockMundo is a persistent multiplayer music sim where players:

- Form and manage bands
- Train skills and unlock hidden talents
- Write, release, and promote songs and albums
- Go on tours and collaborate with other bands
- Customize 3D avatars and skins
- Influence the game world through elections and karma

---

## ✅ Features Already Built

### 👤 Characters & Avatars
- Unique auto-generated names (no duplicates)
- 3D avatar creator with cosmetic-only skins
- Skins system supports:
  - Clothing
  - Instruments
  - Vehicles
- Player-submitted skins with revenue sharing

### 🎸 Band & Music
- Band creation and full management
- Song & Album system:
  - Support for EPs (up to 4 songs)
  - Full albums
  - Track collaboration between bands (50/50 royalties)
- Streaming + Sales:
  - Digital sales
  - Vinyl sales
  - Streaming platforms
- Royalty earnings system

### 📊 Charts
- Global performance charts:
  - Combined (sales + streams)
  - Digital-only
  - Vinyl-only
  - Streaming-only

### 🧠 AI/NPC Layer
- NPC characters simulate real player loops
- Capped progression so players can outgrow them
- Random event-based NPC interactions (e.g. skill boosts)

### 🛠 Admin Tools
- In-game admin panel with UI to:
  - Reset world
  - Adjust game balance
  - Modify or create locations, items, skills
  - Manage NPCs, skins, venues

---

## 🔜 Features Planned for **Beta Launch**

### 🧠 Skills & Learning
- 40 base skills (e.g., Singing, Electric Guitar, Sound Mixing)
- Sub-skill unlocks (e.g., mastering Electric Guitar unlocks Lead Guitar)
- Genre-based skill trees
- Hidden skill unlocks via combinations
- Practice, online lessons, and tutorials (no books)

### 💸 Economy & Progression
- Daily login rewards
  - Streak bonuses
  - Monthly perfect streak bonus

### 🤝 Social & Community
- Band alliances & rivalries (impact fans and press)
- Mentorship 2.0 (optional, gamified)
- Karma system
  - Rewards helpful behavior
  - Restricts toxic players from events/features
- NPC elections for:
  - Label heads
  - Venue managers
  - Genre council chairs

---

## 🚀 Planned for **Full Release**

### 🚐 Touring & Transport
- Visual route planner UI
- Transport system with:
  - Vans, buses, trucks, planes, ferries
  - Upgrades (e.g., merch shop, sleeping pods)
- Logistics simulation (fuel, customs, crew fatigue)
- AI tour manager system (optimize route, venues)
- Fan logistics:
  - Fan petitions for tour stops
  - Affect popularity and fame

### 📡 Publicity & Media
- In-game video/audio podcast system
- Support for player-made promotion content
- Live gigs with visual control
- Music video-style shows

### 🌎 World Systems
- Career hubs ("Majors"):
  - Musicians, Producers, Promoters
  - Each with rankings, shared perks, elections
- Community Events:
  - Genre shifts
  - Festivals
  - Peace Week (karma-based)
- World Pulse Dashboard:
  - Live trends, top cities, genre surges, karma metrics

---

## 🗺 Roadmap Overview

| Milestone        | Status     | Notes |
|------------------|------------|-------|
| Core Backend      | ✅ Done      | SQLite DB, APIs, Admin Tools |
| Core Frontend     | ⚙️ In Dev    | UI files scaffolded |
| Character & Bands | ✅ Done      | Stable |
| Skins & Inventory | ✅ Done      | Supports cosmetics |
| Charts & Earnings | ✅ Done      | Working data model |
| Beta Systems      | 🔜 Building  | Skills, Karma, Login rewards |
| Touring Engine    | 🔜 Planned   | Map + Logistics |
| Public Media Layer| 🚀 Planned   | Post-beta |

---

## 🧩 Tech Stack

- **Backend:** FastAPI + SQLite (async-ready)
- **Frontend:** React (planned) + Vite
- **Avatar Engine:** Custom 3D avatar designer
- **Agents:** Multi-agent orchestration system using GPT-4o

---

## 🧠 Want to Contribute?

RockMundo is being developed in modular stages with agent-based assistance. Join the project or suggest features by submitting issues or feature requests.

---