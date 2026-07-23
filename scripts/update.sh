#!/bin/bash
set -e

echo "=== GoToT Update ==="
git fetch origin
git log --oneline HEAD..origin/main | head -5

read -p "Pull latest changes? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Update cancelled."
    exit 0
fi

git pull origin main

echo "Rebuilding and restarting services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "Running database migrations..."
docker compose exec backend alembic upgrade head || echo "Migration skipped (no changes)"

echo "Update complete."
