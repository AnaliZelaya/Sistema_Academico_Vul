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

## Ejecutar tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Los tests estan separados por vulnerabilidad: `test_sqli.py`, `test_auth.py`, `test_upload.py` (mas `test_base.py` con la configuracion compartida).

## Analisis de seguridad

```bash
pip install -r requirements-dev.txt

# SAST - excluye tests/ y static/ (ver bandit.yaml)
bandit -r . -c bandit.yaml

# Vulnerabilidades conocidas en dependencias
safety check -r requirements.txt
```

`safety check` actualmente reporta CVEs conocidos en las versiones pineadas de Flask, Werkzeug y python-dotenv (`requirements.txt`). Se documentan aqui como parte del pipeline en vez de subir de version sin validar el impacto en el resto de la app.
