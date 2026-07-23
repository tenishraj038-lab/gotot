#!/bin/bash
set -e

DOMAIN=${DOMAIN:-gotot.app}
EMAIL=${SSL_EMAIL:-admin@gotot.app}
SSL_DIR=${SSL_DIR:-/etc/nginx/ssl}

# Check for existing certificate
if [ -f "$SSL_DIR/live/$DOMAIN/fullchain.pem" ]; then
    echo "Existing certificate found for $DOMAIN, renewing if needed..."
    certbot renew --quiet
    exit 0
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update -qq && apt-get install -y -qq certbot python3-certbot-nginx
fi

# Stop nginx temporarily to free port 80
echo "Stopping nginx to obtain certificate..."
docker stop gotot-nginx-1 2>/dev/null || true

# Obtain certificate
echo "Obtaining SSL certificate for $DOMAIN..."
certbot certonly --standalone \
    --domains "$DOMAIN" \
    --domains "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive

# Copy to nginx ssl directory
mkdir -p "$SSL_DIR"
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/cert.pem"
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/key.pem"
chmod 600 "$SSL_DIR/key.pem"

# Restart nginx
echo "Restarting nginx..."
docker start gotot-nginx-1 2>/dev/null || true
docker exec gotot-nginx-1 nginx -s reload 2>/dev/null || true

echo "SSL certificate obtained and installed for $DOMAIN"

# Setup auto-renewal
echo "0 3 * * * root /usr/bin/certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $SSL_DIR/cert.pem && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $SSL_DIR/key.pem && docker exec gotot-nginx-1 nginx -s reload" > /etc/cron.d/certbot-renew
chmod 644 /etc/cron.d/certbot-renew

echo "Auto-renewal configured (daily at 3 AM)"
