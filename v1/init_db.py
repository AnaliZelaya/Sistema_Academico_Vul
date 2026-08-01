import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'academico.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
        cursor.executescript(f.read())

    # Usuario admin inseguro: password en texto plano
    cursor.execute(
        "INSERT INTO usuarios (username, password, rol) VALUES ('admin', 'admin123', 'admin')"
    )
    cursor.execute(
        "INSERT INTO usuarios (username, password, rol) VALUES ('profesor', 'profesor', 'docente')"
    )

    # Estudiantes de prueba
    estudiantes = [
        ('Maria Garcia', 'maria.garcia@universidad.edu', 'Ingenieria de Sistemas'),
        ('Carlos Lopez', 'carlos.lopez@universidad.edu', 'Informatica'),
        ('Ana Martinez', 'ana.martinez@universidad.edu', 'Ingenieria de Software'),
        ('Pedro Sanchez', 'pedro.sanchez@universidad.edu', 'Ciencias de la Computacion'),
        ('Laura Fernandez', 'laura.fernandez@universidad.edu', 'Ingenieria de Sistemas'),
    ]
    cursor.executemany(
        "INSERT INTO estudiantes (nombre, email, carrera) VALUES (?, ?, ?)",
        estudiantes,
    )

    # Cursos de prueba
    cursos = [
        ('Seguridad Informatica', 'SEG301', 4),
        ('Base de Datos', 'BD201', 3),
        ('Redes de Computadoras', 'RED301', 4),
        ('Ingenieria de Software', 'IS202', 3),
        ('Sistemas Operativos', 'SO301', 4),
    ]
    cursor.executemany(
        "INSERT INTO cursos (nombre, codigo, creditos) VALUES (?, ?, ?)",
        cursos,
    )

    # Notas de prueba
    notas = [
        (1, 1, 18.5, '2026-I'),
        (1, 2, 16.0, '2026-I'),
        (2, 1, 14.5, '2026-I'),
        (2, 3, 17.0, '2026-I'),
        (3, 1, 19.0, '2026-I'),
        (3, 4, 15.5, '2026-I'),
        (4, 2, 13.0, '2026-I'),
        (4, 5, 16.5, '2026-I'),
        (5, 3, 18.0, '2026-I'),
        (5, 5, 14.0, '2026-I'),
    ]
    cursor.executemany(
        "INSERT INTO notas (estudiante_id, curso_id, nota, ciclo) VALUES (?, ?, ?, ?)",
        notas,
    )

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")
    print("Usuarios creados: admin/admin123, profesor/profesor")


if __name__ == '__main__':
    init_db()
