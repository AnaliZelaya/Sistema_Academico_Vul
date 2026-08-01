DROP TABLE IF EXISTS notas;
DROP TABLE IF EXISTS archivos;
DROP TABLE IF EXISTS estudiantes;
DROP TABLE IF EXISTS cursos;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'admin'
);

CREATE TABLE estudiantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL,
    carrera TEXT NOT NULL,
    foto_url TEXT
);

CREATE TABLE cursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    codigo TEXT NOT NULL UNIQUE,
    creditos INTEGER NOT NULL
);

CREATE TABLE notas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id INTEGER NOT NULL,
    curso_id INTEGER NOT NULL,
    nota REAL NOT NULL,
    ciclo TEXT NOT NULL,
    observaciones TEXT,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id),
    FOREIGN KEY (curso_id) REFERENCES cursos(id)
);

CREATE TABLE archivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_original TEXT NOT NULL,
    nombre_guardado TEXT NOT NULL,
    ruta TEXT NOT NULL,
    subido_por INTEGER,
    curso_id INTEGER,
    FOREIGN KEY (subido_por) REFERENCES usuarios(id),
    FOREIGN KEY (curso_id) REFERENCES cursos(id)
);
