#!/usr/bin/env bash
# =============================================================================
# verificar_v2.sh — reproduce los 12 probes no destructivos contra la V2
# (https://localhost). Mismo procedimiento documentado en docs/PENTEST.md 7.1.
#
# Uso:
#   ./scripts/verificar_v2.sh [BASE_URL]
#   BASE_URL por defecto: https://localhost  (certificado autofirmado -> curl -k)
#
# Notas:
#   - No escribe datos: CSRF/405/403 detienen la request antes de tocar la BD.
#   - Requiere la V2 desplegada (docker compose up -d).
#   - El probe 12 (fuerza bruta) solo corre con BRUTE=1, porque el rate-limit
#     es por IP y bloquea /login durante ~1 min para todos.
# =============================================================================
set -uo pipefail

BASE="${1:-https://localhost}"
BRUTE="${BRUTE:-0}"
PASS=0; FAIL=0
CJ=$(mktemp); CJD=$(mktemp)
trap 'rm -f "$CJ" "$CJD" /tmp/payload_v2.html' EXIT

check() { # $1 nombre  $2 regex esperada  $3 actual
  if echo "$3" | grep -qE "$2"; then
    echo "OK   $1 ($3)"; PASS=$((PASS+1))
  else
    echo "FAIL $1 (esperado ~$2, actual: $3)"; FAIL=$((FAIL+1))
  fi
}

get_token() { # $1 url  -> valor de csrf_token
  curl -ks -b "$CJ" -c "$CJ" "$1" | grep -oP 'name="csrf_token" value="\K[^"]+' | head -1
}

echo "== V2 verificacion: $BASE =="

# 1. TLS: HTTP redirige a HTTPS; HTTPS responde (login 302)
R=$(curl -s -o /dev/null -w "%{http_code}->%{redirect_url}" http://localhost/)
check "1 HTTP->HTTPS (301)" "^301" "$R"
R=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE/")
check "1b HTTPS responde (302)" "^302" "$R"

# 2. Headers de seguridad
H=$(curl -k -s -D - -o /dev/null "$BASE/")
for h in "strict-transport-security" "content-security-policy" "x-frame-options" "x-content-type-options"; do
  if echo "$H" | grep -qi "$h"; then echo "OK   2 header $h"; PASS=$((PASS+1)); else echo "FAIL 2 header $h"; FAIL=$((FAIL+1)); fi
done

# 3. SQLi en login: payload no crea sesion (200 en login, sin redirect)
TOK=$(get_token "$BASE/login")
R=$(curl -k -s -b "$CJ" -c "$CJ" -o /dev/null -w "%{http_code}" -X POST "$BASE/login" \
     --data-urlencode "username=admin' OR '1'='1' --" --data-urlencode "password=x" \
     --data-urlencode "csrf_token=$TOK")
check "3 SQLi login sin bypass (200)" "^200" "$R"

# Login admin real (para probes con sesion)
TOK=$(get_token "$BASE/login")
curl -k -s -b "$CJ" -c "$CJ" -o /dev/null -X POST "$BASE/login" \
     --data-urlencode "username=admin" --data-urlencode "password=admin123" \
     --data-urlencode "csrf_token=$TOK"

# 4. CSRF: POST sin token -> 400 (no escribe)
R=$(curl -k -s -b "$CJ" -c "$CJ" -o /dev/null -w "%{http_code}" -X POST "$BASE/estudiantes/crear" \
     --data-urlencode "nombre=HACK" --data-urlencode "email=hack@x.com" --data-urlencode "carrera=X")
check "4 CSRF sin token (400)" "^400" "$R"

# 5. Delete por GET -> 405
R=$(curl -k -s -b "$CJ" -c "$CJ" -o /dev/null -w "%{http_code}" "$BASE/estudiantes/eliminar/1")
check "5 GET delete (405)" "^405" "$R"

# 6. Ruta inexistente -> 404 personalizado (sin trazas)
R=$(curl -k -s -b "$CJ" -c "$CJ" -o /dev/null -w "%{http_code}" "$BASE/no-existe-xyz")
check "6 404 personalizado" "^404" "$R"

# 7. RCE: comando no permitido -> mensaje, sin salida
TOK=$(get_token "$BASE/diagnostico")
R=$(curl -k -s -b "$CJ" -c "$CJ" -X POST "$BASE/diagnostico" \
     --data-urlencode "comando=whoami" --data-urlencode "csrf_token=$TOK" | grep -ci "no permitido")
check "7 RCE bloqueado (mensaje)" "^[1-9]" "$R"

# 8. SSRF: metadata / loopback / RFC1918 -> 403
for u in "http://169.254.169.254/latest/meta-data/" "http://localhost/" "http://192.168.1.1/"; do
  TOK=$(get_token "$BASE/importar")
  R=$(curl -k -s -b "$CJ" -c "$CJ" -o /dev/null -w "%{http_code}" -X POST "$BASE/importar" \
       --data-urlencode "url=$u" --data-urlencode "csrf_token=$TOK")
  check "8 SSRF $(echo $u | sed 's#http://##') (403)" "^403" "$R"
done

# 9. SQLi UNION en busqueda -> 0 filas, sin hashes bcrypt
R=$(curl -k -s -b "$CJ" -c "$CJ" --get \
     --data-urlencode "buscar=x' UNION SELECT username,password,rol,'x' FROM usuarios --" \
     "$BASE/estudiantes" | grep -c '2b\$12')
check "9 UNION sin fuga (0 hashes)" "^0" "$R"

# 10. Upload .html malicioso -> rechazado
printf '<script>alert(1)</script>' > /tmp/payload_v2.html
TOK=$(get_token "$BASE/archivos")
R=$(curl -k -s -b "$CJ" -c "$CJ" -L -F "archivo=@/tmp/payload_v2.html;type=text/html" \
     -F "csrf_token=$TOK" "$BASE/archivos/subir" | grep -ci "no permitido")
check "10 upload html bloqueado" "^[1-9]" "$R"

# 11. RBAC: docente no puede /importar ni /diagnostico -> 403
TOK=$(curl -ks -c "$CJD" "$BASE/login" | grep -oP 'name="csrf_token" value="\K[^"]+' | head -1)
curl -k -s -b "$CJD" -c "$CJD" -o /dev/null -X POST "$BASE/login" \
     --data-urlencode "username=profesor" --data-urlencode "password=profesor" \
     --data-urlencode "csrf_token=$TOK"
for p in "/importar" "/diagnostico"; do
  R=$(curl -k -s -b "$CJD" -c "$CJD" -o /dev/null -w "%{http_code}" "$BASE$p")
  check "11 docente $p (403)" "^403" "$R"
done

# 12. Fuerza bruta (opcional): 6 POSTs -> el 6o devuelve 429 (rate-limit)
if [ "$BRUTE" = "1" ]; then
  CJB=$(mktemp); trap 'rm -f "$CJB"' EXIT
  for i in 1 2 3 4 5 6; do
    TOK=$(curl -ks -c "$CJB" "$BASE/login" | grep -oP 'name="csrf_token" value="\K[^"]+' | head -1)
    R=$(curl -k -s -b "$CJB" -c "$CJB" -o /dev/null -w "%{http_code}" -X POST "$BASE/login" \
         --data-urlencode "username=fuerzabruta" --data-urlencode "password=wrong" \
         --data-urlencode "csrf_token=$TOK")
    echo "    intento $i -> $R"
  done
  check "12 brute force (429)" "^429" "$R"
  echo "  -> el rate-limit queda activo ~1 min por IP; 'docker compose restart v2' lo limpia"
else
  echo "OK  12 brute force omitido (ejecutar con BRUTE=1)"
fi

echo
echo "== RESUMEN: PASS=$PASS FAIL=$FAIL =="
[ "$FAIL" = "0" ]
