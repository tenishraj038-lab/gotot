#!/bin/bash
set -e

echo "=== GoToT Rollback ==="

# Get previous deployment tag
PREVIOUS=$(git tag | sort -V | tail -2 | head -1)
if [ -z "$PREVIOUS" ]; then
    PREVIOUS=$(git rev-list --max-parents=0 HEAD)
fi

echo "Rolling back to: $PREVIOUS"

git checkout "$PREVIOUS"

echo "Rebuilding and restarting services with previous version..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "Running database migrations for rollback..."
docker compose exec backend alembic downgrade -1 || echo "Downgrade skipped"

echo "Rollback to $PREVIOUS complete."
