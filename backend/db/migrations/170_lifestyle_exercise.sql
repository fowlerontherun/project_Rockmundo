-- File: backend/db/migrations/170_lifestyle_exercise.sql
BEGIN;

ALTER TABLE lifestyle ADD COLUMN appearance_score REAL DEFAULT 50.0;
ALTER TABLE lifestyle ADD COLUMN exercise_minutes REAL DEFAULT 0.0;
ALTER TABLE lifestyle ADD COLUMN last_exercise TEXT;

COMMIT;
