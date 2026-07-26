import os
import sqlite3
from flask import (
    Flask, request, render_template, redirect,
    url_for, session, flash, send_from_directory,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)

# VULNERABILIDAD: Secret key hardcodeada y predecible
app.secret_key = '12345'

DB_PATH = os.path.join(os.path.dirname(__file__), 'academico.db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
        cursor.executescript(f.read())
    conn.commit()
    conn.close()


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()

        # VULNERABILIDAD: SQL Injection via concatenacion de strings
        query = "SELECT * FROM usuarios WHERE username='" + username + "' AND password='" + password + "'"
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['rol'] = user['rol']
            flash('Inicio de sesion exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas', 'danger')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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
def estudiantes():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    buscar = request.args.get('buscar', '')
    conn = get_db()
    cursor = conn.cursor()

    if buscar:
        # VULNERABILIDAD: SQL Injection en busqueda
        cursor.execute("SELECT * FROM estudiantes WHERE nombre LIKE '%" + buscar + "%' OR email LIKE '%" + buscar + "%'")
    else:
        cursor.execute("SELECT * FROM estudiantes")

    lista = cursor.fetchall()
    conn.close()
    return render_template('estudiantes.html', estudiantes=lista, buscar=buscar)


@app.route('/estudiantes/crear', methods=['POST'])
def crear_estudiante():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    email = request.form['email']
    carrera = request.form['carrera']

    conn = get_db()
    cursor = conn.cursor()
    # VULNERABILIDAD: SQL Injection en insercion
    cursor.execute(
        "INSERT INTO estudiantes (nombre, email, carrera) VALUES ('"
        + nombre + "', '" + email + "', '" + carrera + "')"
    )
    conn.commit()
    conn.close()
    flash('Estudiante creado exitosamente', 'success')
    return redirect(url_for('estudiantes'))


@app.route('/estudiantes/editar/<int:id>', methods=['POST'])
def editar_estudiante(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    email = request.form['email']
    carrera = request.form['carrera']

    conn = get_db()
    cursor = conn.cursor()
    # VULNERABILIDAD: SQL Injection en actualizacion
    cursor.execute(
        "UPDATE estudiantes SET nombre='" + nombre + "', email='" + email
        + "', carrera='" + carrera + "' WHERE id=" + str(id)
    )
    conn.commit()
    conn.close()
    flash('Estudiante actualizado', 'success')
    return redirect(url_for('estudiantes'))


@app.route('/estudiantes/eliminar/<int:id>')
def eliminar_estudiante(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notas WHERE estudiante_id=" + str(id))
    cursor.execute("DELETE FROM estudiantes WHERE id=" + str(id))
    conn.commit()
    conn.close()
    flash('Estudiante eliminado', 'success')
    return redirect(url_for('estudiantes'))


@app.route('/cursos')
def cursos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cursos")
    lista = cursor.fetchall()
    conn.close()
    return render_template('cursos.html', cursos=lista)


@app.route('/cursos/crear', methods=['POST'])
def crear_curso():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    codigo = request.form['codigo']
    creditos = request.form['creditos']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cursos (nombre, codigo, creditos) VALUES ('"
        + nombre + "', '" + codigo + "', " + creditos + ")"
    )
    conn.commit()
    conn.close()
    flash('Curso creado exitosamente', 'success')
    return redirect(url_for('cursos'))


@app.route('/cursos/editar/<int:id>', methods=['POST'])
def editar_curso(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    codigo = request.form['codigo']
    creditos = request.form['creditos']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE cursos SET nombre='" + nombre + "', codigo='" + codigo
        + "', creditos=" + creditos + " WHERE id=" + str(id)
    )
    conn.commit()
    conn.close()
    flash('Curso actualizado', 'success')
    return redirect(url_for('cursos'))


@app.route('/cursos/eliminar/<int:id>')
def eliminar_curso(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notas WHERE curso_id=" + str(id))
    cursor.execute("DELETE FROM cursos WHERE id=" + str(id))
    conn.commit()
    conn.close()
    flash('Curso eliminado', 'success')
    return redirect(url_for('cursos'))


@app.route('/notas')
def notas():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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
def crear_nota():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    estudiante_id = request.form['estudiante_id']
    curso_id = request.form['curso_id']
    nota = request.form['nota']
    ciclo = request.form['ciclo']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notas (estudiante_id, curso_id, nota, ciclo) VALUES ("
        + estudiante_id + ", " + curso_id + ", " + nota + ", '" + ciclo + "')"
    )
    conn.commit()
    conn.close()
    flash('Nota registrada exitosamente', 'success')
    return redirect(url_for('notas'))


@app.route('/notas/eliminar/<int:id>')
def eliminar_nota(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notas WHERE id=" + str(id))
    conn.commit()
    conn.close()
    flash('Nota eliminada', 'success')
    return redirect(url_for('notas'))


@app.route('/archivos')
def archivos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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


@app.route('/archivos/subir', methods=['POST'])
def subir_archivo():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'archivo' not in request.files:
        flash('No se selecciono archivo', 'danger')
        return redirect(url_for('archivos'))

    archivo = request.files['archivo']
    if archivo.filename == '':
        flash('No se selecciono archivo', 'danger')
        return redirect(url_for('archivos'))

    # VULNERABILIDAD: Sin validacion de tipo de archivo
    # VULNERABILIDAD: Sin validacion de tamano
    # VULNERABILIDAD: Se guarda con el nombre original (path traversal posible)
    filename = archivo.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    archivo.save(filepath)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO archivos (nombre_original, nombre_guardado, ruta, subido_por) VALUES ('"
        + filename + "', '" + filename + "', '" + filepath + "', "
        + str(session['user_id']) + ")"
    )
    conn.commit()
    conn.close()
    flash('Archivo subido exitosamente', 'success')
    return redirect(url_for('archivos'))


@app.route('/archivos/descargar/<filename>')
def descargar_archivo(filename):
    # VULNERABILIDAD: Path traversal - sin validacion del filename
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/archivos/eliminar/<int:id>')
def eliminar_archivo(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM archivos WHERE id=" + str(id))
    archivo = cursor.fetchone()

    if archivo:
        filepath = archivo['ruta']
        if os.path.exists(filepath):
            os.remove(filepath)
        cursor.execute("DELETE FROM archivos WHERE id=" + str(id))
        conn.commit()

    conn.close()
    flash('Archivo eliminado', 'success')
    return redirect(url_for('archivos'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesion cerrada', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_db()
    # VULNERABILIDAD: Debug mode activado en produccion
    app.run(debug=True, host='0.0.0.0', port=5000)
