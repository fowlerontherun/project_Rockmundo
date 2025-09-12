# Database Migrations

This package contains lightweight SQL migrations for the SQLite database
used by Rockmundo.  Migrations are stored in the `migrations/` directory
and executed in filename order by `apply_migrations`.

## Deprecation notice

The synchronous database helpers located in ``backend/utils/db.py`` (such as
``get_conn`` and ``cached_query``) are deprecated.  New development should use
the asynchronous interfaces instead.

## New schema additions

- **Lifestyle:** Added `appearance_score`, `exercise_minutes`, and
  `last_exercise` columns for tracking player wellbeing.
- **Drug system:** Drugs are represented using the existing
  `item_categories` and `items` tables rather than dedicated drug tables.
