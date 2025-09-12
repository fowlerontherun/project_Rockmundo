#!/bin/sh
# Apply database migrations, skipping already-applied revisions.
# Alembic's upgrade command is idempotent and will only run new migrations.
set -e
cd "$(dirname "$0")/.."
# Apply migrations using the active Python interpreter
python -m alembic upgrade head
