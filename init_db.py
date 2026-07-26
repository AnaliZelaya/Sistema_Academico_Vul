import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'academico.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
        cursor.executescript(f.read())

    import bcrypt
    admin_pass = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
    prof_pass = bcrypt.hashpw('profesor'.encode(), bcrypt.gensalt()).decode()

    cursor.execute(
        "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
        ('admin', admin_pass, 'admin'),
    )
    cursor.execute(
        "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
        ('profesor', prof_pass, 'docente'),
    )

    estudiantes = [
        ('Maria Garcia', 'maria.garcia@unas.edu.pe', 'Ingenieria de Sistemas'),
        ('Carlos Lopez', 'carlos.lopez@unas.edu.pe', 'Ingenieria Informatica'),
        ('Ana Martinez', 'ana.martinez@unas.edu.pe', 'Ingenieria de Software'),
        ('Pedro Sanchez', 'pedro.sanchez@unas.edu.pe', 'Ciencias de la Computacion'),
        ('Laura Fernandez', 'laura.fernandez@unas.edu.pe', 'Ingenieria de Sistemas'),
        ('Diego Ramirez', 'diego.ramirez@unas.edu.pe', 'Ingenieria Informatica'),
        ('Sofia Torres', 'sofia.torres@unas.edu.pe', 'Ingenieria de Software'),
        ('Luis Mendoza', 'luis.mendoza@unas.edu.pe', 'Ciencias de la Computacion'),
        ('Camila Rios', 'camila.rios@unas.edu.pe', 'Redes y Telecomunicaciones'),
        ('Andres Vega', 'andres.vega@unas.edu.pe', 'Ingenieria de Sistemas'),
        ('Valeria Castro', 'valeria.castro@unas.edu.pe', 'Ingenieria Informatica'),
        ('Jorge Paredes', 'jorge.paredes@unas.edu.pe', 'Ingenieria de Software'),
        ('Luciana Huaman', 'luciana.huaman@unas.edu.pe', 'Ciencias de la Computacion'),
        ('Raul Guerrero', 'raul.guerrero@unas.edu.pe', 'Redes y Telecomunicaciones'),
        ('Fernanda Silva', 'fernanda.silva@unas.edu.pe', 'Ingenieria de Sistemas'),
        ('Ricardo Tello', 'ricardo.tello@unas.edu.pe', 'Ingenieria Informatica'),
        ('Gabriela Pineda', 'gabriela.pineda@unas.edu.pe', 'Ingenieria de Software'),
        ('Hector Delgado', 'hector.delgado@unas.edu.pe', 'Ciencias de la Computacion'),
        ('Isabel Quispe', 'isabel.quispe@unas.edu.pe', 'Redes y Telecomunicaciones'),
        ('Migangel Yalico', 'migangel.yalico@unas.edu.pe', 'Ingenieria de Sistemas'),
    ]
    cursor.executemany(
        "INSERT INTO estudiantes (nombre, email, carrera) VALUES (?, ?, ?)",
        estudiantes,
    )

    cursos = [
        ('Seguridad Informatica', 'SEG301', 4),
        ('Base de Datos', 'BD201', 3),
        ('Redes de Computadoras', 'RED301', 4),
        ('Ingenieria de Software', 'IS202', 3),
        ('Sistemas Operativos', 'SO301', 4),
        ('Inteligencia Artificial', 'IA401', 4),
        ('Programacion Web', 'PW301', 3),
        ('Matematica Discreta', 'MD101', 3),
    ]
    cursor.executemany(
        "INSERT INTO cursos (nombre, codigo, creditos) VALUES (?, ?, ?)",
        cursos,
    )

    notas = [
        (1, 1, 18.5, '2026-I'),
        (1, 2, 16.0, '2026-I'),
        (1, 5, 17.5, '2026-I'),
        (2, 1, 14.5, '2026-I'),
        (2, 3, 17.0, '2026-I'),
        (2, 7, 12.0, '2026-I'),
        (3, 1, 19.0, '2026-I'),
        (3, 4, 15.5, '2026-I'),
        (3, 6, 18.0, '2026-I'),
        (4, 2, 13.0, '2026-I'),
        (4, 5, 16.5, '2026-I'),
        (4, 8, 11.0, '2026-I'),
        (5, 3, 18.0, '2026-I'),
        (5, 5, 14.0, '2026-I'),
        (5, 7, 19.5, '2026-I'),
        (6, 1, 20.0, '2026-I'),
        (6, 4, 17.0, '2026-I'),
        (6, 8, 15.0, '2026-I'),
        (7, 2, 8.5, '2026-I'),
        (7, 6, 10.0, '2026-I'),
        (8, 3, 12.5, '2026-I'),
        (8, 7, 14.0, '2026-I'),
        (9, 1, 16.5, '2026-I'),
        (9, 5, 13.5, '2026-I'),
        (10, 4, 7.0, '2026-I'),
        (10, 8, 9.5, '2026-I'),
        (11, 2, 18.0, '2026-I'),
        (11, 6, 16.0, '2026-I'),
        (12, 3, 15.0, '2026-I'),
        (12, 7, 17.5, '2026-I'),
        (13, 1, 11.0, '2026-I'),
        (13, 8, 14.0, '2026-I'),
        (14, 5, 19.0, '2026-I'),
        (14, 6, 18.5, '2026-I'),
        (15, 4, 13.0, '2026-I'),
        (15, 7, 15.5, '2026-I'),
        (16, 2, 20.0, '2026-I'),
        (16, 3, 18.0, '2026-I'),
        (17, 1, 9.0, '2026-I'),
        (17, 6, 12.0, '2026-I'),
        (18, 8, 16.0, '2026-I'),
        (18, 5, 14.5, '2026-I'),
        (19, 3, 17.0, '2026-I'),
        (19, 4, 15.0, '2026-I'),
        (20, 1, 18.5, '2026-I'),
        (20, 2, 17.0, '2026-I'),
        (20, 7, 16.0, '2026-I'),
    ]
    cursor.executemany(
        "INSERT INTO notas (estudiante_id, curso_id, nota, ciclo) VALUES (?, ?, ?, ?)",
        notas,
    )

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")
    print("Usuarios creados: admin/admin123, profesor/profesor")
    print(f"Estudiantes: {len(estudiantes)}")
    print(f"Cursos: {len(cursos)}")
    print(f"Notas: {len(notas)}")


if __name__ == '__main__':
    init_db()
