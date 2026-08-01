# Matriz de Entrega — Sistema Academico Vul

Correlacion entre cada requisito de la tarea y el artefacto que lo satisface en el repositorio.

| # | Requisito de la tarea | Artefacto en el repo | Estado |
|---|---|---|---|
| 1 | Aplicacion vulnerable V1 (OWASP Top 10: RCE, SQLi, etc.) | `v1/app.py`, `v1/templates/`, `v1/schema.sql` (raiz `main`) + rama `v1-insegura`. 10/10 categorias OWASP explotables | ✅ |
| 2 | Sanitizar todo en una V2 | `app.py` (raiz), `templates/`, `schema.sql`, `requirements.txt` — 59 tests, 18/18 probes | ✅ |
| 3 | Arquitectura de despliegue con tecnologias usadas | `docs/ARQUITECTURA.md` (topologia `web`+`lab`, stack V1/V2, flujo TLS) | ✅ |
| 4 | Guia de levantar en local (Docker / VM / GNS3) | `docs/DESPLIEGUE.md` (quick-start Docker Compose, VM+systemd, GNS3, Let's Encrypt) | ✅ |
| 5 | V2 con SSL/TLS (openssl / free) para HTTPS | `nginx/nginx.conf` (TLS 1.2/1.3, redirect, HSTS), `scripts/generate_certs.sh/.ps1`, `HTTPS=on` directo | ✅ |
| 6 | SQLi automatizado con sqlmap descubriendo credenciales | `docs/SQLMAP_ATTACK.md` (ejecutado), `scripts/sqlmap_attack.sh/.ps1`, evidencia `docs/sqlmap_evidence/` (dump `admin/admin123`) | ✅ |
| 7 | Documentacion y guia de pruebas de penetracion | `docs/PENTEST.md`, `docs/GUIA_ATAQUES.md`, `v1/docs/PENTEST.md` | ✅ |
| 8 | Codigo de ambas versiones adjunto | V2 (raiz) + V1 (`v1/` en `main` y rama `v1-insegura`) | ✅ |
| 9 | Base de datos de ambas versiones adjunta | `db/v1_academico.db` (texto plano) y `db/v2_academico.db` (bcrypt), versionadas; `scripts/setup_dbs.py` las regenera | ✅ |
| 10 | Documento tecnico formal (ISO/IEC 15408) con evidencia por vulnerabilidad | `Trabajo_Seguridad_Informatica.docx` (regenerable con `generate_report.py`) | ✅ |

## Reproduccion rapida (checklist para el docente)

```bash
git clone https://github.com/AnaliZelaya/Sistema_Academico_Vul.git
cd Sistema_Academico_Vul

# 1. Certificados TLS (V2)
.\scripts\generate_certs.ps1            # Linux: ./scripts/generate_certs.sh

# 2. Levantar laboratorio: V1 (:5001) + V2/Nginx TLS (:443)
docker compose up -d --build

# 3. Verificar V2 (12 probes no destructivos -> PASS=18 FAIL=0)
.\scripts\verificar_v2.ps1 -Brute

# 4. sqlmap contra la V1 (dump de credenciales)
docker compose run --rm sqlmap -u "http://v1:5001/login" \
       --data="username=admin&password=x" \
       --batch --level=1 --risk=1 --threads=4 -T usuarios --dump --output-dir=/out

# 5. Tests de seguridad de la V2 (59/59)
pip install -r requirements-dev.txt
python -m pytest tests/ -q

# 6. Regenerar el documento tecnico
python generate_report.py   # -> Trabajo_Seguridad_Informatica.docx
```
