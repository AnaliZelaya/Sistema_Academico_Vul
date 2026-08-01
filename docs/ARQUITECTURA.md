# Arquitectura de Despliegue — Sistema Academico Vul

**Despliegue por ramas:** la V2 segura se despliega desde `feature/p3-tls` (este repo/rama); la V1 vulnerable se despliega desde la rama `v1-insegura`. Cada rama contiene solo su propia aplicacion y su despliegue.

## 1. Topologia del laboratorio

```
                    Host (Docker Compose)
  ┌───────────────────────────────────────────────────────────────────┐
  │  Kali Linux (atacante)                                            │
  │    sqlmap / curl / nmap / Burp / Metasploit                       │
  │    │                                                              │
  │    │  red del laboratorio (bridge / GNS3)                         │
  │    ▼                                                              │
  │  Rama feature/p3-tls  ── V2 segura (este archivo)                 │
  │  ┌────────────────────────────────────────────┐                   │
  │  │  Red Docker: web                           │                   │
  │  │                                            │                   │
  │  │  nginx :80/:443 TLS                        │                   │
  │  │    HTTP→HTTPS 301, HSTS, proxy_pass        │                   │
  │  │    │                                        │                   │
  │  │    ▼                                        │                   │
  │  │  v2-segura :5000 http (interno)             │                   │
  │  │    Gunicorn (3 workers) + Flask + SQLite    │                   │
  │  └────────────────────────────────────────────┘                   │
  │                                                                    │
  │  Rama v1-insegura ── V1 vulnerable (lab)                          │
  │  ┌────────────────────────────────────────────┐                   │
  │  │  Red Docker: lab                           │                   │
  │  │  v1-insegura :5001 http (expuesto)         │                   │
  │  │    Flask dev (debug) + SQLite + uploads    │                   │
  │  │  sqlmap (perfil attack) → http://v1:5000   │                   │
  │  └────────────────────────────────────────────┘                   │
  │                                                                    │
  │  Volumenes (V2): db_v2, uploads_v2 · Certs: ./certs (gitignored)  │
  └───────────────────────────────────────────────────────────────────┘
```

## 2. Stack tecnologico (V2)

| Componente | Tecnologia | Version |
|---|---|---|
| App V2 | Python + Flask | Python 3.12 · Flask 3.1.3 |
| Servidor WSGI | Gunicorn | 23.0.0 (3 workers) |
| Reverse proxy + TLS | Nginx | 1.27 (alpine) |
| Certificados | OpenSSL (self-signed) | 3.x · alt. Let's Encrypt |
| Base de datos | SQLite | 3.x |
| Orquestacion | Docker / Docker Compose | Compose 2 |

> La V1 usa Flask dev server (debug) y su propio stack, descrito en la rama `v1-insegura`.

## 3. Servicios de esta rama (`docker-compose.yml`)

| Servicio | Construye desde | Expuesto al host | Red |
|---|---|---|---|
| `v2` | `Dockerfile` (Gunicorn) | solo interno | `web` |
| `nginx` | imagen `nginx:1.27-alpine` | `:80`, `:443` | `web` |

- **Red `web`**: aislada para produccion. Solo `nginx` y `v2`. Nada externo toca a V2 directamente.
- **Volumenes**: `db_v2` → `/app/db` (persistencia de `v2_academico.db`); `uploads_v2` → `/app/uploads` (uploads fuera del webroot); `./certs` → `/etc/nginx/certs` (bind mount).

## 4. Flujo TLS

1. Cliente pide `http://...` → nginx responde `301` a `https://...`.
2. Cliente pide `https://...` → handshake TLS (self-signed `certs/cert.pem`).
3. nginx hace `proxy_pass http://v2:5000` (trafico interno HTTP, no expuesto).
4. nginx anade `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, etc.

Nota: la app V2 tambien emite HSTS en su `after_request`; se duplica con el de nginx (mismo valor, inofensivo).

## 5. Seguridad en capas (V2)

- **Red**: V2 no expone puertos al host (solo nginx).
- **TLS**: terminacion en nginx, TLS 1.2/1.3, redirect y HSTS.
- **App**: bcrypt, CSRF, rate-limit, RBAC (`@admin_required`), queries parametrizadas, cookies `HttpOnly/SameSite`, error pages.
- **Cookie `Secure`**: con terminacion TLS en nginx, `HTTPS=off` en el contenedor; para forzar `Secure`, poner `HTTPS=on` (requiere montar certs en el contenedor V2) o revisar DESPLIEGUE.md.

## 6. Estado y pendientes

- V2 endurecida (P2) completa: RBAC, deletes POST+CSRF, cookies seguras, error pages, `HTTPS=on`, tests (`test_rbac`, `test_csrf_delete`, `test_errors`, `test_ssrf`, `test_cookies`, `test_diagnostico`, `test_lockout`, `test_upload`, `test_sqli`, `test_auth`, `test_base`).
- Despliegue P3 de V2 con Nginx/TLS en esta rama; lab de V1 + sqlmap en la rama `v1-insegura`.
