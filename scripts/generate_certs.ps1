# Genera certificados TLS auto-firmados para el laboratorio (V2 / nginx).
# Alternativa de produccion: Let's Encrypt (ver docs/DESPLIEGUE.md).
$ErrorActionPreference = "Stop"

Remove-Item Env:OPENSSL_CONF -ErrorAction SilentlyContinue

$CERT_DIR = Join-Path (Split-Path -Parent $PSScriptRoot) "certs"
New-Item -ItemType Directory -Force -Path $CERT_DIR | Out-Null

openssl req -x509 -nodes -newkey rsa:2048 `
  -keyout (Join-Path $CERT_DIR "key.pem") `
  -out (Join-Path $CERT_DIR "cert.pem") `
  -days 365 `
  -subj "/C=PE/ST=Lima/L=Lima/O=Sistema Academico Vul/OU=Lab Seguridad/CN=localhost"

Write-Host "Certificados generados en $CERT_DIR (cert.pem + key.pem)"
