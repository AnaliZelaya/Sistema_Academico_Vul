# Sistema Academico Vul - Version 1 (Insegura)

Sistema academico basico con multiples vulnerabilidades de seguridad deliberadas,
cubriendo las 10 categorias de OWASP Top 10 2021. Objetivo de pentest manual y
sqlmap automatizado.

## Funcionalidades

- Inicio de sesion
- CRUD de Estudiantes (+ importar foto de perfil desde URL)
- CRUD de Cursos (+ importar silabo desde URL)
- CRUD de Notas (+ observaciones)
- Subida y gestion de archivos
- Diagnostico de red (ping a un host)
- Panel de usuarios (admin)

## Credenciales de prueba

- **Admin:** admin / admin123
- **Docente:** profesor / profesor

## Vulnerabilidades incluidas (V1) — mapeo OWASP Top 10 2021

| # | Categoria | Vector |
|---|---|---|
| A01 | Broken Access Control | `/admin/usuarios` y los `eliminar_*` solo verifican sesion, nunca el rol. El nav oculta estas opciones a `docente`, pero el backend las sigue permitiendo por URL directa. |
| A02 | Cryptographic Failures | Passwords en texto plano, `secret_key='12345'` (permite forjar cookies de sesion). |
| A03 | Injection | SQLi por concatenacion en login, busqueda y todos los CRUD. RCE (command injection) en `/diagnostico`. RCE encadenado via subida de archivo con `filename="../app.py"` (secure_filename importado pero no usado) + reloader de Werkzeug. |
| A04 | Insecure Design | Sin rate-limit ni lockout de login, credenciales por defecto. |
| A05 | Security Misconfiguration | `debug=True`, sin headers de seguridad, errores SQL expuestos en el traceback. |
| A06 | Vulnerable & Outdated Components | `Werkzeug==3.0.1`, vulnerable a **CVE-2024-34069** (PIN del debugger interactivo insuficientemente aleatorio, corregido en 3.0.3). |
| A07 | Identification & Auth Failures | Sin regeneracion/invalidacion de sesion, sin rate-limit, secret predecible. |
| A08 | Software and Data Integrity Failures | Subida sin validar tipo/tamano; `.html` malicioso servido directo desde `static/uploads` (XSS almacenado real). |
| A09 | Logging & Monitoring Failures | Sin logging: logins fallidos, subidas y acciones admin no dejan rastro. |
| A10 | SSRF | `/estudiantes/importar-foto` y `/cursos/importar-silabo` descargan cualquier URL sin allowlist. |

XSS almacenado adicional: campo `observaciones` de `notas`, renderizado con `|safe`.

## Ejecucion

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

Puerto configurable via variable de entorno `PORT` (por defecto `5001`).
La app estara disponible en http://localhost:5001
