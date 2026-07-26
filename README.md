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
8. **CSRF** - Proteccion con tokens (preparado para Flask-WTF)
9. **Logging** - Registro de eventos de seguridad en `security.log`
10. **Validacion de entrada** - Longitudes maximas, tipos de datos, campos obligatorios

## DevSecOps

- **Bandit** (SAST): `bandit -r .`
- **Safety**: `safety check`
- **Tests automatizados**: `python -m pytest tests/`

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
python -m pytest tests/ -v
```

## Analisis de seguridad

```bash
# Instalar Bandit
pip install bandit

# Ejecutar SAST
bandit -r . -f json -o reporte_bandit.json

# Instalar Safety
pip install safety

# Verificar dependencias
safety check
```
