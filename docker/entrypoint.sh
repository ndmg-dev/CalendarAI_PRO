#!/bin/bash
set -e

echo "=== CalendAI PRO ==="
echo "Running database migrations..."
alembic upgrade head 2>/dev/null || echo "No migrations to run (or Alembic not configured yet)"

echo "Starting application..."
exec "$@"
