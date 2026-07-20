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
  command -v docker >/dev/null 2>&1 || err "Docker not found."
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
    warn "Using legacy docker-compose (v1). Install Docker Compose v2 for better performance."
  else
    err "docker compose not found."
  fi
}

check_env() {
  if [ ! -f "$ROOT_DIR/backend/.env" ]; then
    if [ -f "$ROOT_DIR/backend/.env.example" ]; then
      warn "backend/.env not found, creating from .env.example"
      cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
      log "Created backend/.env - edit with your production secrets"
    else
      err "backend/.env.example not found. Create backend/.env manually."
    fi
  fi
}

generate_ssl() {
  if [ ! -f "$ROOT_DIR/nginx/ssl/cert.pem" ] || [ ! -f "$ROOT_DIR/nginx/ssl/key.pem" ]; then
    log "Generating self-signed SSL certificates..."
    mkdir -p "$ROOT_DIR/nginx/ssl"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout "$ROOT_DIR/nginx/ssl/key.pem" \
      -out "$ROOT_DIR/nginx/ssl/cert.pem" \
      -subj "/C=US/ST=State/L=City/O=GoTot/CN=gotot.app" \
      -addext "subjectAltName=DNS:gotot.app,DNS:www.gotot.app,IP:0.0.0.0" 2>/dev/null
    chmod 600 "$ROOT_DIR/nginx/ssl/key.pem"
    log "SSL certificates generated"
  fi
}

start_production() {
  check_deps
  check_env
  generate_ssl

  log "Building and starting all services..."
  cd "$ROOT_DIR"

  ${COMPOSE_CMD} build --parallel
  ${COMPOSE_CMD} up -d

  log "GoTot is running!"
  echo ""
  echo "  Frontend:  https://localhost"
  echo "  Backend:   http://localhost:8000"
  echo "  Docs:      http://localhost:8000/docs"
  echo "  Prometheus: http://localhost:9090"
  echo ""
  warn "For production deployment:"
  warn "  1. Set SECRET_KEY to a random 64-char string in backend/.env"
  warn "  2. Set RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET in backend/.env"
  warn "  3. Replace SSL certs with real certificates in nginx/ssl/"
  warn "  4. Set POSTGRES_PASSWORD env var (override docker-compose default)"
  warn "  5. Set REDIS_REQUIREPASS for Redis authentication"
  echo ""
  log "Run ./run.sh logs to see service logs"
}

start_backup() {
  check_deps
  mkdir -p "$ROOT_DIR/backups"
  log "Running database backup..."
  cd "$ROOT_DIR"
  docker run --rm --network gotot_default \
    -e PGHOST=postgres -e PGPORT=5432 \
    -e POSTGRES_USER=${POSTGRES_USER:-gotot} \
    -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-gotot_pass} \
    -e POSTGRES_DB=${POSTGRES_DB:-gotot} \
    -v "$ROOT_DIR/backups:/backups" \
    postgres:16-alpine /bin/sh -c \
    'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "/backups/gotot_$(date +%Y%m%d_%H%M%S).sql.gz"'
  log "Backup completed"
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
  ${COMPOSE_CMD} logs -f
}

start_stop() {
  cd "$ROOT_DIR"
  ${COMPOSE_CMD} down
  log "All services stopped"
}

start_clean() {
  cd "$ROOT_DIR"
  ${COMPOSE_CMD} down -v
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
  backup)
    start_backup
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
    echo "  backup      Run one-time database backup"
    ;;
esac
