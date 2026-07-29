#!/bin/sh
# Run pending migrations before the app starts — this is the real
# production schema path (create_all in main.py is a dev-only fallback).
set -e

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
