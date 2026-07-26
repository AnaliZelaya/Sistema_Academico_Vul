# Sistema Academico Vul - Version 1 (Insegura)

Sistema academico basico con multiples vulnerabilidades de seguridad deliberadas.

## Funcionalidades

- Inicio de sesion
- CRUD de Estudiantes
- CRUD de Cursos
- CRUD de Notas
- Subida y gestion de archivos

## Credenciales de prueba

- **Admin:** admin / admin123
- **Docente:** profesor / profesor

## Vulnerabilidades incluidas (V1)

1. **SQL Injection** - Concatenacion de strings en queries
2. **Autenticacion rota** - Passwords en texto plano, sin rate-limit
3. **XSS Almacenado** - Entrada sin sanitizar renderizada directo
4. **Subida de archivos insegura** - Sin validacion de tipo/tamaño
5. **Secret hardcodeado** - app.secret_key = '12345'
6. **Debug mode activado** - En produccion

## Ejecucion

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

La app estara disponible en http://localhost:5000
