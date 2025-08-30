#!/bin/sh
set -e
cd "$(dirname "$0")/.."
alembic upgrade head
exec uvicorn backend.api:app --host 0.0.0.0 --port 8000
