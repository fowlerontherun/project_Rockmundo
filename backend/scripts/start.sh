#!/bin/sh
set -e
cd "$(dirname "$0")/.."
# Apply database migrations before starting the server.  The migration script
# skips revisions that have already been applied, so startup remains fast after
# the initial run.
./scripts/migrate.sh
exec uvicorn backend.api:app --host 0.0.0.0 --port 8000
