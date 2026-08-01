#!/usr/bin/env bash
# Genera certificados TLS auto-firmados para el laboratorio (V2 / nginx).
# Alternativa de produccion: Let's Encrypt (ver docs/DESPLIEGUE.md).
set -euo pipefail

unset OPENSSL_CONF

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="$(dirname "$SCRIPT_DIR")/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -days 365 \
  -subj "/C=PE/ST=Lima/L=Lima/O=Sistema Academico Vul/OU=Lab Seguridad/CN=localhost"

echo "Certificados generados en $CERT_DIR (cert.pem + key.pem)"
