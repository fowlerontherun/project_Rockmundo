# World Pulse Snapshot Demo

This project includes a lightweight World Pulse dashboard that can display the
current top genres. The snapshot data is generated on demand and stored in the
`genre_pulse_snapshots` table.

## Triggering a Snapshot

Use the admin endpoint to compute today's snapshot and store the top ten
results:

```bash
curl -X POST http://localhost:8000/api/world-pulse/snapshot
```

The response contains the snapshot date and the ten highest scoring genres.

## Viewing the Snapshot

Open `frontend/pages/popularity_dashboard.html` in a browser and click
**Refresh Snapshot**. The page requests `/api/world-pulse/ranked` with today's
date and renders the top ten genres along with a simple trend indicator.

This flow is suitable for demos or manual testing and avoids the need for a
background scheduler.
