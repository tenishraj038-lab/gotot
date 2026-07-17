#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head || echo "Migration failed (non-fatal, continuing)"

echo "Starting GoTot API server..."
exec "$@"
