import os
import unittest
import io
import sqlite3

from test_base import BaseTestCase


class DocenteRBACTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.login_docente()

    def test_docente_ve_listados(self):
        for ruta in ('/dashboard', '/estudiantes', '/cursos', '/notas', '/archivos'):
            resp = self.app.get(ruta)
            self.assertEqual(resp.status_code, 200, f'{ruta} deberia ser accesible para docente')

    def test_docente_no_puede_crear_estudiante(self):
        resp = self.app.post('/estudiantes/crear', data={
            'nombre': 'X', 'email': 'x@x.com', 'carrera': 'Informatica',
        }, follow_redirects=False)
        self.assertEqual(resp.status_code, 403)

    def test_docente_no_puede_editar_estudiante(self):
        resp = self.app.post('/estudiantes/editar/1', data={
            'nombre': 'X', 'email': 'x@x.com', 'carrera': 'Informatica',
        }, follow_redirects=False)
        self.assertEqual(resp.status_code, 403)

    def test_docente_no_puede_eliminar_estudiante(self):
        resp = self.app.post('/estudiantes/eliminar/1', follow_redirects=False)
        self.assertEqual(resp.status_code, 403)

    def test_docente_no_puede_crear_curso(self):
        resp = self.app.post('/cursos/crear', data={
            'nombre': 'X', 'codigo': 'X1', 'creditos': '3',
        }, follow_redirects=False)
        self.assertEqual(resp.status_code, 403)

    def test_docente_no_puede_crear_nota(self):
        resp = self.app.post('/notas/crear', data={
            'estudiante_id': '1', 'curso_id': '1', 'nota': '15', 'ciclo': '2026-I',
        }, follow_redirects=False)
        self.assertEqual(resp.status_code, 403)

    def test_docente_no_puede_eliminar_archivo(self):
        resp = self.app.post('/archivos/eliminar/1', follow_redirects=False)
        self.assertEqual(resp.status_code, 403)

    def test_docente_puede_subir_archivo(self):
        antes = set(os.listdir(self.app.application.config['UPLOAD_FOLDER']))
        try:
            data = {'archivo': (io.BytesIO(b'contenido de prueba'), 'prueba_docente.txt')}
            resp = self.app.post('/archivos/subir', data=data,
                                 content_type='multipart/form-data', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Archivo subido exitosamente', resp.data)
        finally:
            despues = set(os.listdir(self.app.application.config['UPLOAD_FOLDER']))
            for nuevo in despues - antes:
                os.remove(os.path.join(self.app.application.config['UPLOAD_FOLDER'], nuevo))


class AdminRBACTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.login()

    def test_admin_puede_crear_estudiante(self):
        resp = self.app.post('/estudiantes/crear', data={
            'nombre': 'Nuevo Estudiante', 'email': 'nuevo@universidad.edu', 'carrera': 'Informatica',
        }, follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

    def test_admin_puede_eliminar_estudiante(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM estudiantes")
        antes = cursor.fetchone()['total']
        conn.close()

        resp = self.app.post('/estudiantes/eliminar/1', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM estudiantes")
        despues = cursor.fetchone()['total']
        conn.close()
        self.assertEqual(despues, antes - 1)


class SinLoginRBACTest(BaseTestCase):
    def test_accion_admin_sin_login_redirige(self):
        resp = self.app.post('/estudiantes/crear', data={
            'nombre': 'X', 'email': 'x@x.com', 'carrera': 'Informatica',
        }, follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers.get('Location'))


if __name__ == '__main__':
    unittest.main()
