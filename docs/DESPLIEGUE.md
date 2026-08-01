# Guia de Despliegue — Sistema Academico Vul

Guia para levantar la aplicacion en **Docker Compose** (principal), en una **VM con systemd** y en un escenario **GNS3**.

> **Despliegue por ramas:** este archivo describe la **V2 segura** (rama `feature/p3-tls`). La **V1 vulnerable** (rama `v1-insegura`) tiene su propio despliegue descrito en su rama.

Requisitos: Docker + Docker Compose, OpenSSL, Python 3.12 (solo para desarrollo local).

---

## 1. Despliegue con Docker Compose (principal)

### 1.1 Generar certificados

```bash
# Linux / macOS
./scripts/generate_certs.sh

# Windows PowerShell
.\scripts\generate_certs.ps1
```

Genera `certs/cert.pem` y `certs/key.pem` (self-signed, 365 dias). La carpeta `certs/` esta en `.gitignore`.

### 1.2 Configurar entorno

```bash
cp .env.example .env
```

Variables relevantes: `NGINX_HTTP_PORT`, `NGINX_HTTPS_PORT`, `GUNICORN_WORKERS`, `SECRET_KEY`.

### 1.3 Levantar el stack

```bash
docker compose up -d --build
```

| Servicio | URL |
|---|---|
| V2 (segura, TLS) | `https://localhost` (HTTP redirige a HTTPS) |

> La V1 vulnerable se levanta desde la rama `v1-insegura` (puerto expuesto distinto, p. ej. `:5001`).

### 1.4 Verificar TLS

```bash
# Redireccion HTTP -> HTTPS (debe responder 301)
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://localhost/

# Headers de seguridad via HTTPS (ignorando el certificado self-signed)
curl -k -s -D - -o /dev/null https://localhost/ | grep -iE "HTTP/|strict-transport|content-security"

# Certificado
openssl s_client -connect localhost:443 -showcerts < /dev/null 2>/dev/null | grep subject
```

### 1.5 Detener

```bash
docker compose down
docker compose down -v   # ademas elimina los volumenes (BD de V2 incluida)
```

---

## 2. HTTPS directo en la app V2 (sin nginx)

Alternativa para desarrollo local sin nginx: servir la app con `ssl_context`.

```bash
# Generar certs (o usar los ya generados para nginx)
./scripts/generate_certs.sh

export HTTPS=on
export SSL_CERT=certs/cert.pem
export SSL_KEY=certs/key.pem
python init_db.py
python app.py            # escucha en https://127.0.0.1:5000
```

Con `HTTPS=on`, `SESSION_COOKIE_SECURE` se activa automaticamente (requisito de cookie segura).

---

## 3. Despliegue en VM con systemd

Escenario: V2 + Gunicorn + Nginx instalados en una VM Linux.

### 3.1 Aplicacion

```bash
sudo apt update && sudo apt install -y python3-venv nginx openssl
git clone <repo>
cd Sistema_Academico_Vul
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python init_db.py
```

### 3.2 Certificados

Self-signed:

```bash
sudo mkdir -p /etc/nginx/certs
sudo openssl req -x509 -nodes -newkey rsa:2048 -keyout /etc/nginx/certs/key.pem \
  -out /etc/nginx/certs/cert.pem -days 365 \
  -subj "/C=PE/ST=Lima/L=Lima/O=Sistema Academico Vul/CN=localhost"
```

Alternativa Let's Encrypt (certificado real):

```bash
sudo apt install -y certbot python3-certbot-nginx
# apuntar el dominio a la VM y luego:
sudo certbot --nginx -d academico.example.com
```

### 3.3 Gunicorn como servicio

`/etc/systemd/system/sistema-v2.service`:

```ini
[Unit]
Description=Sistema Academico V2 (Gunicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/sistema_academico_vul
EnvironmentFile=/opt/sistema_academico_vul/.env
ExecStart=/opt/sistema_academico_vul/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 --access-logfile /var/log/sistema-v2.access --error-logfile /var/log/sistema-v2.error app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sistema-v2
sudo systemctl status sistema-v2
```

### 3.4 Nginx como reverse proxy

Configuracion equivalente a `nginx/nginx.conf` del repo (redirect + TLS + HSTS), apuntando a `127.0.0.1:5000`. Con Let's Encrypt, `certbot --nginx` genera esta configuracion automaticamente.

---

## 4. Escenario GNS3 (red realista)

Simula la topologia del laboratorio con equipos/maquinas reales.

1. **Dispositivos**:
   - Switch GNS3 (red de laboratorio, por ejemplo `10.0.0.0/24`).
   - **Kali Linux** (atacante) con `sqlmap`, `nmap`, `curl`, `Burp`.
   - **Servidor Ubuntu/Debian** con Docker (o la app V1/V2 directamente).

2. **Configuracion**:
   - Levantar la V2 en el servidor (secciones 1-3) desde la rama `feature/p3-tls`.
   - Levantar la V1 desde la rama `v1-insegura` (su propio compose; escucha en `0.0.0.0:5001`).
   - Desde Kali: `nmap -sV 10.0.0.X` para descubrir 5001 (v1) y 80/443 (v2).

3. **Ataque (P4)**:
   - Ejecutar `scripts/sqlmap_attack.sh` apuntando a `http://<v1-ip>:5001/login` (scripts en la rama `v1-insegura`).
   - Ejecutar pentest manual segun `docs/PENTEST.md`.

4. **Justificacion**: separar atacante (Kali) de victima (servidor) por una red conmutable permite validar el alcance real del compromiso (red interna, pivoteo, etc.) de forma cercana a un entorno de produccion.

---

## 5. Notas de seguridad

- Certificados self-signed son solo para el laboratorio; en produccion usar Let's Encrypt (seccion 3.2) o un CA comercial.
- Con terminacion TLS en nginx, la cookie de sesion no lleva `Secure` salvo que se active `HTTPS=on` en el contenedor V2 (ver seccion 2) — se recomienda para produccion.
- V1 y V2 se despliegan desde ramas separadas (`v1-insegura` y `feature/p3-tls`): cada rama contiene solo su aplicacion y su despliegue. Ningun servicio externo ve V2 directamente (solo via nginx).
