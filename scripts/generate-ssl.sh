#!/bin/bash
set -e

SSL_DIR="/etc/nginx/ssl"
CERT_FILE="${SSL_DIR}/cert.pem"
KEY_FILE="${SSL_DIR}/key.pem"

if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "SSL certificates already exist at ${SSL_DIR}"
    exit 0
fi

mkdir -p "$SSL_DIR"

echo "Generating self-signed SSL certificates..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/C=US/ST=State/L=City/O=GoTot/CN=gotot.app" \
    -addext "subjectAltName=DNS:gotot.app,DNS:www.gotot.app,DNS:api.gotot.app,IP:0.0.0.0"

chmod 600 "$KEY_FILE"
echo "SSL certificates generated at ${SSL_DIR}"
