# Sistema Academico Vul - Version 2 (Segura)

Sistema academico basico construido con practicas SecDevOps, corrigiendo las vulnerabilidades de la V1.

## Funcionalidades

- Inicio de sesion seguro (bcrypt + rate limiting)
- CRUD de Estudiantes
- CRUD de Cursos
- CRUD de Notas
- Subida y gestion de archivos (validada)

## Credenciales de prueba

- **Admin:** admin / admin123
- **Docente:** profesor / profesor

## Correcciones de seguridad aplicadas (V2)

1. **SQL Injection** - Queries parametrizadas con `?` en todas las queries
2. **Autenticacion rota** - Passwords hasheados con bcrypt, rate limiting, sin hardcodeo
3. **XSS Almacenado** - Auto-escaping de Jinja2 + validacion de entrada + CSP headers
4. **Subida de archivos insegura** - Validacion MIME + extension + tamano + renombrado UUID
5. **Secret seguro** - Variable de entorno `.env` (no hardcodeado)
6. **Debug mode** - Desactivado en produccion
7. **Headers de seguridad** - CSP, X-Frame-Options, HSTS, X-XSS-Protection
8. **CSRF** - Tokens CSRF con Flask-WTF (`CSRFProtect`) en todos los formularios POST
9. **Logging** - Registro de eventos de seguridad en `security.log`
10. **Validacion de entrada** - Longitudes maximas, tipos de datos, campos obligatorios
11. **Rate limiting** - Flask-Limiter, 5 intentos por minuto en `/login`
12. **RBAC (Control de acceso)** - Decorador `@admin_required`: `docente` solo lectura + subir/descargar archivos; `admin` CRUD completo. UI oculta acciones no autorizadas
13. **Deletes por POST + CSRF** - Las eliminaciones ya no usan GET (ahora devuelven 405); usan formularios POST con token CSRF
14. **Cookies de sesion seguras** - `HttpOnly`, `SameSite=Lax`, `Secure` (cuando HTTPS esta activo)
15. **HTTPS/TLS** - Soporte opcional via `HTTPS=on` con certificados en `certs/` (auto-firmados con OpenSSL)
16. **Paginas de error personalizadas** - 400, 403, 404 y 500 sin exponer trazas del servidor

## DevSecOps

- **Bandit** (SAST): `bandit -r . -c bandit.yaml`
- **Safety** (dependencias): `safety check -r requirements.txt`
- **Tests automatizados**: `python -m pytest tests/` (o `python -m unittest discover -s tests`)

Herramientas de desarrollo en `requirements-dev.txt` (no se instalan en produccion).

## Ejecucion

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env con un SECRET_KEY seguro
python init_db.py
python app.py
```

La app estara disponible en http://localhost:5000

### HTTPS/TLS (opcional)

```bash
# 1. Generar certificados auto-firmados en certs/
openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"

# 2. Activar HTTPS en .env
#    HTTPS=on
#    SSL_CERT=certs/cert.pem
#    SSL_KEY=certs/key.pem

# 3. Ejecutar
python app.py
```

La app quedara disponible en https://localhost:5000 (los certificados son de laboratorio; en produccion usar Let's Encrypt u otro CA confiable).

## Ejecutar tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Los tests estan separados por vulnerabilidad:
`test_sqli.py`, `test_auth.py`, `test_upload.py`, `test_rbac.py`, `test_csrf_delete.py`,
`test_errors.py`, `test_cookies.py` (mas `test_base.py` con la configuracion compartida).
Total: **29 tests**.

## Analisis de seguridad

```bash
pip install -r requirements-dev.txt

# SAST - excluye tests/ y static/ (ver bandit.yaml)
bandit -r . -c bandit.yaml

# Vulnerabilidades conocidas en dependencias
safety check -r requirements.txt
```

`bandit` no reporta hallazgos y `safety check` no reporta CVEs en las versiones pineadas
de `requirements.txt` (flask 3.1.3, werkzeug 3.1.8, python-dotenv 1.2.2).
