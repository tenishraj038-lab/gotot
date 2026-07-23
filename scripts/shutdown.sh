#!/bin/bash
set -e

echo "=== GoToT Stop ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
echo "All services stopped."
