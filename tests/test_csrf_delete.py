import unittest
import sqlite3

from test_base import BaseTestCase


class CSRFDeleteTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.login()

    def test_delete_por_get_rechazado(self):
        resp = self.app.get('/estudiantes/eliminar/1', follow_redirects=False)
        self.assertEqual(resp.status_code, 405)

        resp = self.app.get('/cursos/eliminar/1', follow_redirects=False)
        self.assertEqual(resp.status_code, 405)

        resp = self.app.get('/notas/eliminar/1', follow_redirects=False)
        self.assertEqual(resp.status_code, 405)

        resp = self.app.get('/archivos/eliminar/1', follow_redirects=False)
        self.assertEqual(resp.status_code, 405)

    def test_delete_por_post_sin_csrf_rechazado(self):
        self.app.application.config['WTF_CSRF_ENABLED'] = True
        try:
            resp = self.app.post('/estudiantes/eliminar/1', follow_redirects=False)
            self.assertEqual(resp.status_code, 400)
        finally:
            self.app.application.config['WTF_CSRF_ENABLED'] = False

    def test_delete_por_post_elimina_registro(self):
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


if __name__ == '__main__':
    unittest.main()
