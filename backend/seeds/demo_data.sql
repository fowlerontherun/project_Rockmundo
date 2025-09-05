-- File: backend/seeds/demo_data.sql
-- Minimal demo data for local testing. Run after running migrations.

BEGIN;

INSERT INTO venues (name, city, country, capacity) VALUES
  ('Brixton Academy', 'London', 'UK', 4900),
  ('Barrowland Ballroom', 'Glasgow', 'UK', 1900),
  ('Paradiso', 'Amsterdam', 'NL', 1500);

-- Assume a band with id=1 exists in your users/bands table, or adjust as needed.
INSERT INTO tours (band_id, name, status) VALUES
  (1, 'UK Weekender', 'draft');

-- Two pending stops for tour 1
INSERT INTO tour_stops (tour_id, venue_id, date_start, date_end, order_index, status, notes, is_recorded) VALUES
  (1, 1, date('now', '+7 day'), date('now', '+7 day'), 0, 'pending', 'Opening night', 0),
  (1, 2, date('now', '+9 day'), date('now', '+9 day'), 1, 'pending', 'Second show', 0);

-- A sample notification for user 1
INSERT INTO notifications (user_id, type, title, body) VALUES
  (1, 'system', 'Welcome to RockMundo', 'Your account was created.');

COMMIT;
