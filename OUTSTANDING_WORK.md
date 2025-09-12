# RockMundo — Outstanding Work for a Testable MVP

This list is focused on getting a **clickable, end‑to‑end vertical slice** working on a single laptop with local SQLite and the static frontend pages served by FastAPI.

> Definition of “testable”: a non‑developer can sign in, create/select an avatar, create a band, book a gig, perform, see outcomes (XP, fans, cash), and browse simple dashboards — all using UI pages under `/frontend/*` with minimal manual steps.

---

## A. Must‑Have (Blockers)

- [ ] **Auth flow wiring (frontend ⇄ backend):**  
  - Ensure `login.html` posts to the right JWT endpoint and stores the token.  
  - Provide a tiny `auth.js` helper (get/set token, attach `Authorization: Bearer <jwt>` on `fetch`).  
  - Show logged‑in user state in navbar/profile.

- [ ] **Seeded demo user & data verified:**  
  - `backend/scripts/seed_demo.py` must create: 1 demo user, 1 avatar, 1 demo band, a handful of venues, and a day’s schedule window.  
  - Document demo credentials in README (or print them at seed completion).

- [ ] **Band creation + avatar selection UI:**  
  - Make `profile.html` and/or `band_dashboard.html` actually POST to `band_routes` and avatar endpoints.  
  - Surface validation errors inline.

- [ ] **Gig booking & performance (no stubs):**  
  - Replace simulated values in `routes/gig.py` (fame/skill/solo checks) with real services or queries.  
  - Implement capacity/date/time conflict checks and simple payout formula (guarantee + ticket split).  
  - Persist performance result (xp deltas, fans gained, cash). Show a simple “Gig Result” panel.

- [ ] **Economy write‑path:**  
  - Ensure basic money ledger updates on gig completion.  
  - Display current balance and last 5 transactions on `band_dashboard.html`.

- [ ] **Notifications / toasts:**  
  - When a booking is confirmed or a gig is performed, show a toast and list it in `/notifications`.

---

## B. Nice‑to‑Have for MVP polish

- [ ] **World Pulse snapshot**: nightly/daily job run triggerable via admin route; show top 10 on `popularity_dashboard.html`.
- [ ] **FTS search**: simple search box for messages/music using `mail_fts` if present.
- [ ] **Realtime (optional)**: WS connection for jam room or notifications; otherwise polling is fine.

---

## C. Tech Hygiene

- [ ] **.env sanity**: document all flags in `.env.example` with defaults.
- [ ] **DB migrations runner**: confirm startup applies SQL migrations idempotently; add a `make db-reset` convenience target (optional).  
- [ ] **CORS**: allow `http://localhost:*` in dev.  
- [ ] **Storage**: default to `local` provider; verify attachments folder exists on startup.

---

## D. Test Plan (manual)

1. **Login** with seeded user.  
2. **Create/select** avatar → **Create/select** band.  
3. **Book** a gig → visible on **schedule**.  
4. **Perform** gig → results UI shows money/XP/fans.  
5. **Dashboard** shows updated balances & popularity.  
6. **World Pulse** page shows snapshot (if job run).  
7. **Notifications** list includes recent actions.

---

## E. Known Spots to Touch in Code

- `backend/routes/gig.py` — replace simulated fame/skill/solo checks.  
- `backend/services/*` — confirm `band_service`, `avatar_service`, `economy_service` write paths used by gig completion.  
- `frontend/pages/*` — ensure pages call the correct endpoints; add minimal JS `fetch` helpers.  
- `backend/scripts/seed_demo.py` — ensure richer demo content (venues, bands).

---

## F. Later (Not needed for MVP)

- 3D live performance engine (separate module).  
- Marketplace skins with S3 storage + payments.  
- Full mail + attachments UI.  
- Advanced AI managers (tour manager, PR manager), complex scheduling constraints.  
- Multi‑region charts and royalty jobs pipeline hardening.

---

### Deliverable

Once all **A‑blockers** are complete, the repo should boot with `uvicorn`, seed data, and allow a user to complete the vertical slice using only `/frontend/*` pages and the exposed JSON API.
