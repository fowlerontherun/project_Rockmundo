#!/bin/sh
set -e
cd "$(dirname "$0")/.."

# Re-run in nix-shell if not already in one
if [ -z "$IN_NIX_SHELL" ]; then
  exec nix-shell shell.nix --run "sh $0"
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  python3.11 -m venv venv
  ./venv/bin/pip install -r requirements.txt
fi

# Apply database migrations before starting the server.  The migration script
# skips revisions that have already been applied, so startup remains fast after
# the initial run.
./scripts/migrate.sh
exec env PYTHONPATH=.:backend ./venv/bin/python3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000
