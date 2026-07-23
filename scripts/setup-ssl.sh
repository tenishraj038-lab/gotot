#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOMAIN="${1:-}"
EMAIL="${2:-admin@goto.app}"

if [ -z "$DOMAIN" ]; then
  echo "Usage: $0 <domain> [email]"
  echo "Example: $0 gotot.app admin@gotot.app"
  exit 1
fi

CERT_DIR="$ROOT_DIR/../nginx/ssl"
mkdir -p "$CERT_DIR"

# Check if certbot is available
if command -v certbot >/dev/null 2>&1; then
  log "certbot found, requesting certificates for $DOMAIN..."

  # Stop nginx temporarily (we use standalone mode)
  docker compose -f "$ROOT_DIR/../docker-compose.prod.yml" stop nginx 2>/dev/null || true

  certbot certonly --standalone \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive

  # Symlink certificates to nginx/ssl/
  ln -sf "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_DIR/cert.pem"
  ln -sf "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$CERT_DIR/key.pem"

  log "Certificates obtained and linked to $CERT_DIR/"
  log "Restarting nginx..."
  docker compose -f "$ROOT_DIR/../docker-compose.prod.yml" up -d nginx
else
  err "certbot not installed. Install: sudo apt install certbot"
fi

# Setup auto-renewal cron
CRON_JOB="0 3 * * * certbot renew --quiet && docker compose -f $ROOT_DIR/../docker-compose.prod.yml restart nginx"
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
  (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
  log "Auto-renewal cron job added (runs daily at 3am)"
fi

log "Let's Encrypt setup complete for $DOMAIN"
