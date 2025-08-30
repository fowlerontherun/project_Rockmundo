-- File: backend/migrations/007b_unique_active_sponsorship_per_venue.sql
CREATE UNIQUE INDEX IF NOT EXISTS ux_current_sponsor_per_venue
ON venue_sponsorships(venue_id)
WHERE is_active = 1 AND date(start_date) <= date('now') AND (end_date IS NULL OR date(end_date) >= date('now'));
