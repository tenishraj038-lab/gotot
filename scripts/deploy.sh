#!/bin/bash
set -e

echo "=== GoToT Production Start ==="

# Check for .env file
if [ ! -f backend/.env ]; then
    echo "ERROR: backend/.env not found. Copy from .env.production.template and configure."
    exit 1
fi

# Pull latest images
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull

# Start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Wait for health checks
echo "Waiting for services to become healthy..."
sleep 10

# Check health
HEALTH=$(docker compose exec backend curl -sf http://localhost:8000/health 2>/dev/null || echo '{"status":"unreachable"}')
echo "Backend health: $(echo $HEALTH | python3 -c 'import json,sys;print(json.load(sys.stdin).get("status","unknown"))')"

echo "GoToT is running."
echo "  Frontend: https://gotot.app"
echo "  Backend:  https://gotot.app/api"
echo "  Grafana:  https://gotot.app/grafana"
