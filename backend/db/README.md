# Database Migrations

This package contains lightweight SQL migrations for the SQLite database
used by Rockmundo.  Migrations are stored in the `migrations/` directory
and executed in filename order by `apply_migrations`.

## New schema additions

- **Lifestyle:** Added `appearance_score`, `exercise_minutes`, and
  `last_exercise` columns for tracking player wellbeing.
- **Drug system:** Introduced `drug_categories`, `drugs`, and
  `addictions` tables to model substances and player dependencies.
