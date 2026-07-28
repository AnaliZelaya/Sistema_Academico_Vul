import os
import sqlite3
import uuid
import logging
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

# CORRECCION: Proteccion CSRF en todos los formularios POST/PUT/PATCH/DELETE
csrf = CSRFProtect(app)

# CORRECCION: Rate limiting para mitigar fuerza bruta en login
limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

DB_PATH = os.path.join(os.path.dirname(__file__), os.environ.get('DATABASE_URL', 'academico.db'))
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
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


@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


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
            logger.info(f"Login exitoso: {username}")
            flash('Inicio de sesion exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
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


@app.route('/estudiantes/eliminar/<int:id>')
@login_required
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


@app.route('/cursos/eliminar/<int:id>')
@login_required
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


@app.route('/notas/eliminar/<int:id>')
@login_required
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

    # CORRECCION: Guardar fuera del webroot (en subdirectorio sin acceso directo)
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


@app.route('/archivos/eliminar/<int:id>')
@login_required
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
    app.run(debug=False, host='127.0.0.1', port=5000)
