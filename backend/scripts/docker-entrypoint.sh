#!/bin/sh
set -e

./backend/scripts/migrate.sh
python -m backend.scripts.seed_demo

exec "$@"
