#!/bin/sh
set -e

./scripts/migrate.sh
python -m backend.scripts.seed_demo

exec "$@"
