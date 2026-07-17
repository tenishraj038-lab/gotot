#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

check_deps() {
  command -v docker >/dev/null 2>&1 || err "Docker not found. Install: https://docs.docker.com/get-docker/"
  command -v docker compose >/dev/null 2>&1 || warn "docker compose not found, trying docker-compose..."
}

check_env() {
  if [ ! -f "$ROOT_DIR/backend/.env" ]; then
    warn "backend/.env not found, creating from .env.example"
    cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
    log "Created backend/.env - edit with your production secrets"
  fi
}

start_production() {
  check_deps
  check_env

  log "Building and starting all services..."
  cd "$ROOT_DIR"

  docker compose build --parallel
  docker compose up -d

  log "GoTot is running!"
  echo ""
  echo "  Frontend:  http://localhost:3000"
  echo "  Backend:   http://localhost:8000"
  echo "  Docs:      http://localhost:8000/docs"
  echo "  Prometheus: http://localhost:9090"
  echo ""
  warn "For production:"
  warn "  1. Set SECRET_KEY in backend/.env to a random 64-char string"
  warn "  2. Set RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET in backend/.env"
  warn "  3. Configure SSL certs in nginx/ssl/"
  warn "  4. Set NEXT_PUBLIC_API_URL=/api in frontend/.env.production"
  echo ""
  log "Run ./run.sh logs to see service logs"
}

start_backend_dev() {
  log "Starting backend in dev mode..."
  cd "$ROOT_DIR/backend"
  export ENVIRONMENT=development
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

start_frontend_dev() {
  log "Starting frontend in dev mode..."
  cd "$ROOT_DIR/frontend"
  npm run dev
}

start_logs() {
  cd "$ROOT_DIR"
  docker compose logs -f
}

start_stop() {
  cd "$ROOT_DIR"
  docker compose down
  log "All services stopped"
}

start_clean() {
  cd "$ROOT_DIR"
  docker compose down -v
  log "All services stopped and volumes removed"
}

start_migration() {
  cd "$ROOT_DIR/backend"
  source .venv/bin/activate 2>/dev/null || true
  alembic upgrade head
}

case "${1:-production}" in
  production)
    start_production
    ;;
  dev)
    echo "Starting in dev mode..."
    echo "  Run './run.sh backend' in one terminal"
    echo "  Run './run.sh frontend' in another"
    echo "  Requires PostgreSQL and Redis running locally"
    ;;
  backend)
    start_backend_dev
    ;;
  frontend)
    start_frontend_dev
    ;;
  logs)
    start_logs
    ;;
  stop)
    start_stop
    ;;
  clean)
    start_clean
    ;;
  migrate)
    start_migration
    ;;
  *)
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  production  Start all services with Docker Compose (default)"
    echo "  dev         Start backend + frontend in dev mode"
    echo "  backend     Start only backend dev server"
    echo "  frontend    Start only frontend dev server"
    echo "  logs        Follow Docker Compose logs"
    echo "  stop        Stop all Docker Compose services"
    echo "  clean       Stop and remove Docker volumes"
    echo "  migrate     Run Alembic migrations"
    ;;
esac
