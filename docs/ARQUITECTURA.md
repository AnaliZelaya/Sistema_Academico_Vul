# Arquitectura de Despliegue — Sistema Academico Vul

**Estructura actual:** todo el laboratorio vive en la rama `main`. La **V2 segura**
(`app.py`, raiz) y la **V1 vulnerable** (`v1/`) se despliegan juntas con
`docker compose up -d`; la rama `v1-insegura` conserva una copia aislada de la V1.

## 1. Topologia del laboratorio

```
                        Host (Docker Compose)
  ┌────────────────────────────────────────────────────────────────────────┐
  │  Red Docker: lab           Red Docker: web                             │
  │  ┌───────────────────┐    ┌────────────────────────────────────┐       │
  │  │ sistema_v1 :5001  │    │ sistema_nginx :80 / :443 (TLS)     │       │
  │  │  Flask dev debug  │    │   HTTP→HTTPS 301, HSTS, proxy_pass │       │
  │  │  SQLi/RCE/SSRF/XSS│    │   │                                 │       │
  │  │  uploads_v1       │    │   ▼                                 │       │
  │  └─────────┬─────────┘    │ sistema_v2 :5000 http (interno)     │       │
  │            │              │   Gunicorn (3 workers) + Flask      │       │
  │  sistema_sqlmap          │   + SQLite (db_v2) + uploads_v2      │       │
  │  (profile "attack",      └────────────────────────────────────┘        │
  │   on-demand, alcanza                                                  │
  │   http://v1:5001)                                                     │
  │                                                                        │
  │  Certs: ./certs (gitignored) · BDs versionadas: db/v1_academico.db    │
  │        y db/v2_academico.db (git)                                     │
  └────────────────────────────────────────────────────────────────────────┘
```

- **Red `web`** (aislada): `sistema_nginx` + `sistema_v2`. Nada externo toca la V2 directamente; solo Nginx expone `:80`/`:443`.
- **Red `lab`** (aislada): `sistema_v1` (expone `:5001` al host) + `sistema_sqlmap` (contenedor de ataque, solo con `--profile attack`).
- **sqlmap** se ejecuta on-demand: `docker compose run --rm sqlmap -u "http://v1:5001/login" ...`; la evidencia queda en `./docs/sqlmap_evidence` (montado en `/out`).

## 2. Stack tecnologico

| Componente | V1 (insegura) | V2 (segura) |
|---|---|---|
| Backend | Flask 3.0.3 + Werkzeug **3.0.1** (CVE-2024-34069) | Flask 3.1.3 + Gunicorn 23.0.0 (3 workers) |
| Servidor | Flask dev server (`debug=True`) | Gunicorn |
| Reverse proxy + TLS | - | Nginx 1.27 (alpine) |
| Certificados | - | OpenSSL (self-signed) · alt. Let's Encrypt |
| Base de datos | SQLite `academico.db` (texto plano) | SQLite `v2_academico.db` (bcrypt) |
| Orquestacion | Docker Compose (`Dockerfile.v1`) | Docker Compose (`Dockerfile`) |
| Ataque (lab) | - | sqlmap 1.10.7 (`Dockerfile.sqlmap`, perfil `attack`) |

## 3. Servicios de `docker-compose.yml`

| Servicio | Construye desde | Expuesto al host | Red | Persistencia |
|---|---|---|---|---|
| `v1` | `Dockerfile.v1` | `:5001` | `lab` | `uploads_v1` |
| `v2` | `Dockerfile` | solo interno | `web` | `db_v2`, `uploads_v2` |
| `nginx` | imagen `nginx:1.27-alpine` | `:80`, `:443` | `web` | `./certs` (bind) |
| `sqlmap` | `Dockerfile.sqlmap` | ninguno | `lab` | `./docs/sqlmap_evidence:/out` |

## 4. Flujo TLS

1. Cliente pide `http://...` → nginx responde `301` a `https://...`.
2. Cliente pide `https://...` → handshake TLS (self-signed `certs/cert.pem`; TLS 1.2/1.3).
3. nginx hace `proxy_pass http://v2:5000` (trafico interno HTTP, no expuesto).
4. nginx anade `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.

Alternativa sin nginx: la V2 puede servir HTTPS directo con `HTTPS=on` y `ssl_context`
(ver `docs/DESPLIEGUE.md`, seccion 2).

## 5. Seguridad en capas (V2)

- **Red**: V2 no expone puertos al host (solo nginx).
- **TLS**: terminacion en nginx, TLS 1.2/1.3, redirect y HSTS.
- **App**: bcrypt, CSRF (Flask-WTF), rate-limit + lockout, RBAC (`@admin_required`), queries parametrizadas, cookies `HttpOnly/SameSite/Secure`, error pages, uploads validados fuera del webroot.
- **Evidencia**: `docs/PENTEST.md`, `docs/SQLMAP_ATTACK.md`, `docs/sqlmap_evidence/`.

## 6. Bases de datos

`scripts/setup_dbs.py` genera ambas BDs versionadas en `db/`:

| Base | Contenido | Credenciales |
|---|---|---|
| `db/v1_academico.db` | passwords en **texto plano** | `admin/admin123`, `profesor/profesor` |
| `db/v2_academico.db` | passwords con **bcrypt** (cost 12) | `admin/admin123`, `profesor/profesor` |
