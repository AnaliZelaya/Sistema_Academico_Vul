import os
import sqlite3
import uuid
import logging
import time
import ipaddress
import socket
import subprocess  # nosec B404 - solo se usa con allowlist fija y shell=False (ver /diagnostico)
import urllib.error
import urllib.parse
import urllib.request
from functools import wraps

import bcrypt
from dotenv import load_dotenv
from flask import (
    Flask, request, render_template, redirect,
    url_for, session, flash, send_from_directory, abort,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32).hex())

@app.route('/static/uploads/<path:filename>')
def static_uploads_blocked(filename):
    abort(404)


# CORRECCION: Hardening de la cookie de sesion
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('HTTPS', 'off').lower() == 'on'

# CORRECCION: Proteccion CSRF en todos los formularios POST/PUT/PATCH/DELETE
csrf = CSRFProtect(app)
# CORRECCION: Desactivar WTF_CSRF_SSL_STRICT (chequeo de Referer de Flask-WTF).
# Con HTTPS activo y SameSite=Lax, la validacion del token sincronizador ya
# protege contra CSRF; el chequeo de Referer rompe clientes legimitimos que no
# envian Referer (curl, Burp Suite, scripts, API clients usados en las guias).
app.config['WTF_CSRF_SSL_STRICT'] = False

# CORRECCION: Rate limiting para mitigar fuerza bruta en login
limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

DB_PATH = os.path.join(os.path.dirname(__file__), os.environ.get('DATABASE_URL', 'academico.db'))
# CORRECCION: Uploads fuera del webroot (A08) - static/uploads era servible
# directamente por Flask (/static/uploads/<file>). Ahora se guardan en uploads/
# en la raiz del proyecto y solo se sirven via /archivos/descargar (as_attachment).
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), os.environ.get('UPLOAD_FOLDER', 'uploads'))
MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'xlsx', 'txt', 'csv'}
ALLOWED_MIMETYPES = {
    'application/pdf', 'image/png', 'image/jpeg', 'image/gif',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain', 'text/csv',
}

logging.basicConfig(
    filename='security.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)


# CORRECCION: Lockout de cuenta tras intentos fallidos (A04) - complementa el
# rate limiting por IP con un bloqueo por usuario durante BLOQUEO_SEGUNDOS.
MAX_INTENTOS_LOGIN = 5
BLOQUEO_SEGUNDOS = 10 * 60
_intentos_fallidos = {}
_bloqueos = {}


def _usuario_bloqueado(username):
    fin = _bloqueos.get(username, 0)
    if fin and fin > time.time():
        return True
    if fin and fin <= time.time():
        _bloqueos.pop(username, None)
        _intentos_fallidos.pop(username, None)
    return False


# CORRECCION: Validacion de magic bytes (A08) - la firma real del archivo debe
# corresponder a su extension. txt/csv no tienen firma estandar (se validan
# solo por extension y MIME, documentado en el README).
MAGIC_BYTES = {
    'pdf': b'%PDF',
    'png': b'\x89PNG\r\n\x1a\n',
    'jpg': b'\xff\xd8\xff',
    'jpeg': b'\xff\xd8\xff',
    'gif': b'GIF8',
    'docx': b'PK\x03\x04',
    'xlsx': b'PK\x03\x04',
}


def _validar_magic_bytes(ext, head):
    firma = MAGIC_BYTES.get(ext)
    if firma is None:
        return True
    return head.startswith(firma)


# CORRECCION: Proteccion SSRF (A10). Solo http/https hacia IPs publicas;
# se bloquean loopback, RFC1918, link-local (incluye 169.254.169.254 metadata),
# ULA IPv6, IPv4-mapped, multicast, reservadas y sin especificar.
MAX_IMPORT_BYTES = 10 * 1024


def _validar_url_ssrf(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        abort(400)
    hostname = parsed.hostname
    if not hostname:
        abort(400)
    try:
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    except ValueError:
        abort(400)
    try:
        infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        abort(400)
    ips = {info[4][0] for info in infos}
    for ip in ips:
        try:
            addr = ipaddress.ip_address(ip.split('%')[0])
        except ValueError:
            abort(400)
        if (addr.is_loopback or addr.is_private or addr.is_link_local
                or addr.is_multicast or addr.is_reserved or addr.is_unspecified):
            logger.warning(f"SSRF bloqueado: {url} -> IP no publica {ip}")
            abort(403)


class _SinRedirecciones(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        logger.warning(f"SSRF: redireccion bloqueada hacia {newurl}")
        return None


def _fetch_url(url, timeout=5):
    # urllib se usa deliberadamente: la proteccion SSRF se aplica antes en
    # _validar_url_ssrf (resolucion DNS + solo IPs publicas) y las
    # redirecciones se bloquean para impedir bypass hacia redes internas.
    opener = urllib.request.build_opener(_SinRedirecciones)
    with opener.open(url, timeout=timeout) as resp:
        status = resp.status
        contenido = resp.read(MAX_IMPORT_BYTES)
        final_url = resp.geturl()
    return status, contenido, final_url


# CORRECCION: Comandos de diagnostico con allowlist y shell=False (A03).
# Solo argv fijo, sin argumentos del usuario -> no hay inyeccion de comandos.
ALLOWED_COMMANDS = {
    'fecha': ['date', '+%Y-%m-%d %H:%M:%S'],
    'hostname': ['hostname'],
    'sistema': ['uname', '-a'],
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
        cursor.executescript(f.read())

    admin_pass = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
    prof_pass = bcrypt.hashpw('profesor'.encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "INSERT OR IGNORE INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
        ('admin', admin_pass, 'admin'),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
        ('profesor', prof_pass, 'docente'),
    )

    estudiantes = [
        ('Maria Garcia', 'maria.garcia@universidad.edu', 'Ingenieria de Sistemas'),
        ('Carlos Lopez', 'carlos.lopez@universidad.edu', 'Informatica'),
        ('Ana Martinez', 'ana.martinez@universidad.edu', 'Ingenieria de Software'),
        ('Pedro Sanchez', 'pedro.sanchez@universidad.edu', 'Ciencias de la Computacion'),
        ('Laura Fernandez', 'laura.fernandez@universidad.edu', 'Ingenieria de Sistemas'),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO estudiantes (nombre, email, carrera) VALUES (?, ?, ?)",
        estudiantes,
    )

    cursos = [
        ('Seguridad Informatica', 'SEG301', 4),
        ('Base de Datos', 'BD201', 3),
        ('Redes de Computadoras', 'RED301', 4),
        ('Ingenieria de Software', 'IS202', 3),
        ('Sistemas Operativos', 'SO301', 4),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO cursos (nombre, codigo, creditos) VALUES (?, ?, ?)",
        cursos,
    )

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debe iniciar sesion', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# CORRECCION: Control de acceso basado en roles (A01 - Broken Access Control)
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debe iniciar sesion', 'warning')
            return redirect(url_for('login'))
        if session.get('rol') != 'admin':
            logger.warning(f"Acceso denegado (403): rol {session.get('rol')} intento acceder a {request.path}")
            abort(403)
        return f(*args, **kwargs)
    return decorated


@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


# CORRECCION: Paginas de error personalizadas (A05 - no exponer trazas)
@app.errorhandler(400)
def error_400(e):
    return render_template('errors/400.html'), 400


@app.errorhandler(403)
def error_403(e):
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def error_404(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def error_500(e):
    return render_template('errors/500.html'), 500


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').encode()

        if not username or not password:
            flash('Ingrese usuario y contrasena', 'danger')
            return render_template('login.html')

        # CORRECCION: Lockout tras demasiados intentos fallidos (A04)
        if _usuario_bloqueado(username):
            logger.warning(f"Login bloqueado (lockout): {username}")
            flash('Cuenta bloqueada temporalmente por demasiados intentos fallidos', 'danger')
            return render_template('login.html')

        conn = get_db()
        cursor = conn.cursor()
        # CORRECCION: Query parametrizada - sin concatenacion de strings
        cursor.execute(
            "SELECT * FROM usuarios WHERE username = ?",
            (username,),
        )
        user = cursor.fetchone()
        conn.close()

        # CORRECCION: Verificacion segura con bcrypt
        if user and bcrypt.checkpw(password, user['password'].encode()):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['rol'] = user['rol']
            _intentos_fallidos.pop(username, None)
            _bloqueos.pop(username, None)
            logger.info(f"Login exitoso: {username}")
            flash('Inicio de sesion exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            _intentos_fallidos[username] = _intentos_fallidos.get(username, 0) + 1
            if _intentos_fallidos[username] >= MAX_INTENTOS_LOGIN:
                _bloqueos[username] = time.time() + BLOQUEO_SEGUNDOS
                logger.warning(f"Cuenta bloqueada tras {MAX_INTENTOS_LOGIN} intentos fallidos: {username}")
            logger.warning(f"Login fallido: {username}")
            flash('Credenciales incorrectas', 'danger')

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM estudiantes")
    total_estudiantes = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM cursos")
    total_cursos = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM notas")
    total_notas = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM archivos")
    total_archivos = cursor.fetchone()['total']
    conn.close()

    return render_template(
        'dashboard.html',
        total_estudiantes=total_estudiantes,
        total_cursos=total_cursos,
        total_notas=total_notas,
        total_archivos=total_archivos,
    )


@app.route('/estudiantes')
@login_required
def estudiantes():
    buscar = request.args.get('buscar', '').strip()
    conn = get_db()
    cursor = conn.cursor()

    if buscar:
        # CORRECCION: Query parametrizada con LIKE seguro
        cursor.execute(
            "SELECT * FROM estudiantes WHERE nombre LIKE ? OR email LIKE ?",
            (f'%{buscar}%', f'%{buscar}%'),
        )
    else:
        cursor.execute("SELECT * FROM estudiantes")

    lista = cursor.fetchall()
    conn.close()
    return render_template('estudiantes.html', estudiantes=lista, buscar=buscar)


@app.route('/estudiantes/crear', methods=['POST'])
@login_required
@admin_required
def crear_estudiante():
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    carrera = request.form.get('carrera', '').strip()

    if not nombre or not email or not carrera:
        flash('Todos los campos son obligatorios', 'danger')
        return redirect(url_for('estudiantes'))

    conn = get_db()
    cursor = conn.cursor()
    # CORRECCION: Query parametrizada
    cursor.execute(
        "INSERT INTO estudiantes (nombre, email, carrera) VALUES (?, ?, ?)",
        (nombre, email, carrera),
    )
    conn.commit()
    conn.close()
    logger.info(f"Estudiante creado: {nombre}")
    flash('Estudiante creado exitosamente', 'success')
    return redirect(url_for('estudiantes'))


@app.route('/estudiantes/editar/<int:id>', methods=['POST'])
@login_required
@admin_required
def editar_estudiante(id):
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    carrera = request.form.get('carrera', '').strip()

    if not nombre or not email or not carrera:
        flash('Todos los campos son obligatorios', 'danger')
        return redirect(url_for('estudiantes'))

    conn = get_db()
    cursor = conn.cursor()
    # CORRECCION: Query parametrizada
    cursor.execute(
        "UPDATE estudiantes SET nombre = ?, email = ?, carrera = ? WHERE id = ?",
        (nombre, email, carrera, id),
    )
    conn.commit()
    conn.close()
    logger.info(f"Estudiante actualizado: ID {id}")
    flash('Estudiante actualizado', 'success')
    return redirect(url_for('estudiantes'))


@app.route('/estudiantes/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_estudiante(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notas WHERE estudiante_id = ?", (id,))
    cursor.execute("DELETE FROM estudiantes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    logger.info(f"Estudiante eliminado: ID {id}")
    flash('Estudiante eliminado', 'success')
    return redirect(url_for('estudiantes'))


@app.route('/cursos')
@login_required
def cursos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cursos")
    lista = cursor.fetchall()
    conn.close()
    return render_template('cursos.html', cursos=lista)


@app.route('/cursos/crear', methods=['POST'])
@login_required
@admin_required
def crear_curso():
    nombre = request.form.get('nombre', '').strip()
    codigo = request.form.get('codigo', '').strip()
    creditos = request.form.get('creditos', '').strip()

    if not nombre or not codigo or not creditos:
        flash('Todos los campos son obligatorios', 'danger')
        return redirect(url_for('cursos'))

    try:
        creditos = int(creditos)
    except ValueError:
        flash('Creditos debe ser un numero', 'danger')
        return redirect(url_for('cursos'))

    conn = get_db()
    cursor = conn.cursor()
    # CORRECCION: Query parametrizada
    cursor.execute(
        "INSERT INTO cursos (nombre, codigo, creditos) VALUES (?, ?, ?)",
        (nombre, codigo, creditos),
    )
    conn.commit()
    conn.close()
    logger.info(f"Curso creado: {codigo}")
    flash('Curso creado exitosamente', 'success')
    return redirect(url_for('cursos'))


@app.route('/cursos/editar/<int:id>', methods=['POST'])
@login_required
@admin_required
def editar_curso(id):
    nombre = request.form.get('nombre', '').strip()
    codigo = request.form.get('codigo', '').strip()
    creditos = request.form.get('creditos', '').strip()

    if not nombre or not codigo or not creditos:
        flash('Todos los campos son obligatorios', 'danger')
        return redirect(url_for('cursos'))

    try:
        creditos = int(creditos)
    except ValueError:
        flash('Creditos debe ser un numero', 'danger')
        return redirect(url_for('cursos'))

    conn = get_db()
    cursor = conn.cursor()
    # CORRECCION: Query parametrizada
    cursor.execute(
        "UPDATE cursos SET nombre = ?, codigo = ?, creditos = ? WHERE id = ?",
        (nombre, codigo, creditos, id),
    )
    conn.commit()
    conn.close()
    logger.info(f"Curso actualizado: ID {id}")
    flash('Curso actualizado', 'success')
    return redirect(url_for('cursos'))


@app.route('/cursos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_curso(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notas WHERE curso_id = ?", (id,))
    cursor.execute("DELETE FROM cursos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    logger.info(f"Curso eliminado: ID {id}")
    flash('Curso eliminado', 'success')
    return redirect(url_for('cursos'))


@app.route('/notas')
@login_required
def notas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.id, n.nota, n.ciclo,
               e.nombre as estudiante_nombre,
               c.nombre as curso_nombre, c.codigo as curso_codigo
        FROM notas n
        JOIN estudiantes e ON n.estudiante_id = e.id
        JOIN cursos c ON n.curso_id = c.id
        ORDER BY e.nombre, c.nombre
    """)
    lista = cursor.fetchall()

    cursor.execute("SELECT * FROM estudiantes")
    estudiantes = cursor.fetchall()
    cursor.execute("SELECT * FROM cursos")
    cursos = cursor.fetchall()
    conn.close()

    return render_template(
        'notas.html', notas=lista,
        estudiantes=estudiantes, cursos=cursos,
    )


@app.route('/notas/crear', methods=['POST'])
@login_required
@admin_required
def crear_nota():
    estudiante_id = request.form.get('estudiante_id', '').strip()
    curso_id = request.form.get('curso_id', '').strip()
    nota = request.form.get('nota', '').strip()
    ciclo = request.form.get('ciclo', '').strip()

    if not estudiante_id or not curso_id or not nota or not ciclo:
        flash('Todos los campos son obligatorios', 'danger')
        return redirect(url_for('notas'))

    try:
        estudiante_id = int(estudiante_id)
        curso_id = int(curso_id)
        nota = float(nota)
    except ValueError:
        flash('Datos invalidos', 'danger')
        return redirect(url_for('notas'))

    if nota < 0 or nota > 20:
        flash('La nota debe estar entre 0 y 20', 'danger')
        return redirect(url_for('notas'))

    conn = get_db()
    cursor = conn.cursor()
    # CORRECCION: Query parametrizada
    cursor.execute(
        "INSERT INTO notas (estudiante_id, curso_id, nota, ciclo) VALUES (?, ?, ?, ?)",
        (estudiante_id, curso_id, nota, ciclo),
    )
    conn.commit()
    conn.close()
    logger.info(f"Nota registrada: Estudiante {estudiante_id}, Curso {curso_id}")
    flash('Nota registrada exitosamente', 'success')
    return redirect(url_for('notas'))


@app.route('/notas/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_nota(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    logger.info(f"Nota eliminada: ID {id}")
    flash('Nota eliminada', 'success')
    return redirect(url_for('notas'))


@app.route('/archivos')
@login_required
def archivos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, u.username as subido_por_nombre
        FROM archivos a
        LEFT JOIN usuarios u ON a.subido_por = u.id
        ORDER BY a.id DESC
    """)
    lista = cursor.fetchall()
    conn.close()
    return render_template('archivos.html', archivos=lista)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/archivos/subir', methods=['POST'])
@login_required
def subir_archivo():
    if 'archivo' not in request.files:
        flash('No se selecciono archivo', 'danger')
        return redirect(url_for('archivos'))

    archivo = request.files['archivo']
    if archivo.filename == '':
        flash('No se selecciono archivo', 'danger')
        return redirect(url_for('archivos'))

    # CORRECCION: Validacion de tipo de archivo por extension
    if not allowed_file(archivo.filename):
        flash('Tipo de archivo no permitido', 'danger')
        logger.warning(f"Intento de subida de archivo no permitido: {archivo.filename}")
        return redirect(url_for('archivos'))

    # CORRECCION: Validacion de tipo MIME (solo si el browser envia uno especifico)
    if archivo.content_type and archivo.content_type not in ALLOWED_MIMETYPES and archivo.content_type != 'application/octet-stream':
        flash('Tipo MIME no permitido', 'danger')
        logger.warning(f"Intento de subida con MIME no permitido: {archivo.content_type}")
        return redirect(url_for('archivos'))

    # CORRECCION: Nombre seguro + renombrado con UUID
    original_filename = secure_filename(archivo.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    safe_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    # CORRECCION: Validacion de magic bytes - la firma real debe coincidir
    # con la extension (impide disfrazar contenido malicioso como PDF/PNG/etc.)
    archivo.stream.seek(0)
    head = archivo.stream.read(16)
    archivo.stream.seek(0)
    if not _validar_magic_bytes(ext, head):
        flash('El contenido no corresponde al tipo de archivo', 'danger')
        logger.warning(f"Intento de subida con magic bytes invalidos: {archivo.filename}")
        return redirect(url_for('archivos'))

    # CORRECCION: Guardar fuera del webroot (en directorio sin acceso directo)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    archivo.save(filepath)

    conn = get_db()
    cursor = conn.cursor()
    # CORRECCION: Query parametrizada
    cursor.execute(
        "INSERT INTO archivos (nombre_original, nombre_guardado, ruta, subido_por) VALUES (?, ?, ?, ?)",
        (original_filename, safe_filename, filepath, session['user_id']),
    )
    conn.commit()
    conn.close()
    logger.info(f"Archivo subido: {original_filename} -> {safe_filename}")
    flash('Archivo subido exitosamente', 'success')
    return redirect(url_for('archivos'))


@app.route('/archivos/descargar/<filename>')
@login_required
def descargar_archivo(filename):
    # CORRECCION: Validacion del nombre de archivo
    safe_name = secure_filename(filename)
    if safe_name != filename:
        logger.warning(f"Intento de path traversal: {filename}")
        abort(403)

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        abort(404)

    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_name, as_attachment=True)


@app.route('/archivos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_archivo(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM archivos WHERE id = ?", (id,))
    archivo = cursor.fetchone()

    if archivo:
        filepath = archivo['ruta']
        if os.path.exists(filepath):
            os.remove(filepath)
        cursor.execute("DELETE FROM archivos WHERE id = ?", (id,))
        conn.commit()
        logger.info(f"Archivo eliminado: ID {id}")

    conn.close()
    flash('Archivo eliminado', 'success')
    return redirect(url_for('archivos'))


@app.route('/importar', methods=['GET', 'POST'])
@login_required
@admin_required
def importar():
    resultado = None
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        if not url:
            flash('Ingrese una URL', 'danger')
            return render_template('importar.html')

        _validar_url_ssrf(url)

        try:
            status, contenido, final_url = _fetch_url(url)
        except urllib.error.HTTPError as e:
            if 300 <= e.code < 400:
                logger.warning(f"SSRF: redireccion bloqueada hacia {url}")
                flash('Redirecciones no permitidas', 'danger')
            else:
                flash(f'Error HTTP {e.code}', 'danger')
            return render_template('importar.html')
        except (urllib.error.URLError, socket.timeout, ValueError, TimeoutError) as e:
            logger.warning(f"Importacion fallida {url}: {e}")
            flash('No se pudo obtener el contenido de la URL', 'danger')
            return render_template('importar.html')

        texto = contenido.decode('utf-8', errors='replace')
        resultado = {'status': status, 'url': final_url, 'preview': texto[:500]}
        logger.info(f"Importacion exitosa: {url}")

    return render_template('importar.html', resultado=resultado)


@app.route('/diagnostico', methods=['GET', 'POST'])
@login_required
@admin_required
def diagnostico():
    salida = None
    error = None
    if request.method == 'POST':
        comando = request.form.get('comando', '').strip()
        if comando not in ALLOWED_COMMANDS:
            logger.warning(f"RCE bloqueado: comando no permitido '{comando}'")
            flash('Comando no permitido (solo: fecha, hostname, sistema)', 'danger')
            return render_template('diagnostico.html')
        try:
            # La entrada es una allowlist fija (argv sin argumentos del usuario)
            # y se ejecuta con shell=False, por lo que no hay inyeccion posible.
            resultado = subprocess.run(ALLOWED_COMMANDS[comando], shell=False,  # nosec B603
                                       capture_output=True, text=True, timeout=10)
            salida = resultado.stdout.strip()
            logger.info(f"Diagnostico ejecutado: {comando}")
        except Exception as e:
            logger.warning(f"Diagnostico fallo ({comando}): {e}")
            error = str(e)
    return render_template('diagnostico.html', salida=salida, error=error)


@app.route('/logout')
def logout():
    username = session.get('username', 'desconocido')
    session.clear()
    logger.info(f"Logout: {username}")
    flash('Sesion cerrada', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_db()
    # CORRECCION: Debug mode desactivado, host restringido
    # CORRECCION: Soporte HTTPS/TLS (A02) - certs generados por scripts/generate_certs.*
    https_enabled = os.environ.get('HTTPS', 'off').lower() == 'on'
    ssl_cert = os.environ.get('SSL_CERT', os.path.join(os.path.dirname(__file__), 'certs', 'cert.pem'))
    ssl_key = os.environ.get('SSL_KEY', os.path.join(os.path.dirname(__file__), 'certs', 'key.pem'))
    if https_enabled:
        app.run(debug=False, host='127.0.0.1', port=5000, ssl_context=(ssl_cert, ssl_key))
    else:
        app.run(debug=False, host='127.0.0.1', port=5000)
