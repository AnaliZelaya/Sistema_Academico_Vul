import unittest
import os
import sys
import sqlite3
import io
import jinja2

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from app import app, init_db, get_db

# Forzar el Jinja loader para que apunte a la carpeta de templates correcta
app.jinja_env.loader = jinja2.FileSystemLoader(os.path.join(ROOT_DIR, 'templates'))
app.static_folder = os.path.join(ROOT_DIR, 'static')


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        self.db_path = os.path.join(ROOT_DIR, 'test_academico.db')

        # Crear BD de prueba
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        with open(os.path.join(ROOT_DIR, 'schema.sql'), 'r') as f:
            conn.executescript(f.read())

        import bcrypt
        admin_pass = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
            ('admin', admin_pass, 'admin'),
        )
        conn.commit()
        conn.close()

        # Parchear DB_PATH para tests
        import app as app_module
        self._orig_db = app_module.DB_PATH
        app_module.DB_PATH = self.db_path

    def tearDown(self):
        import app as app_module
        app_module.DB_PATH = self._orig_db
        if os.path.exists(self.db_path):
            os.remove(self.db_path)


class LoginTest(BaseTestCase):
    def test_login_correcto(self):
        resp = self.app.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Dashboard', resp.data)

    def test_login_incorrecto(self):
        resp = self.app.post('/login', data={
            'username': 'admin',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Credenciales incorrectas', resp.data)


class SQLInjectionTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.app.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
        })

    def test_sqli_busqueda_inyectada(self):
        payload = "' OR '1'='1"
        resp = self.app.get(f'/estudiantes?buscar={payload}')
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b'Maria Garcia', resp.data)
        self.assertNotIn(b'Carlos Lopez', resp.data)

    def test_sqli_union_attack(self):
        payload = "' UNION SELECT 1,2,3,4--"
        resp = self.app.get(f'/estudiantes?buscar={payload}')
        self.assertEqual(resp.status_code, 200)


class UploadTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.app.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
        })

    def test_upload_extension_no_permitida(self):
        data = {
            'archivo': (io.BytesIO(b'malware content'), 'virus.exe'),
        }
        resp = self.app.post('/archivos/subir', data=data,
                             content_type='multipart/form-data',
                             follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Tipo de archivo no permitido', resp.data)

    def test_upload_svg_no_permitido(self):
        data = {
            'archivo': (io.BytesIO(b'<svg>xss</svg>'), 'xss.svg'),
        }
        resp = self.app.post('/archivos/subir', data=data,
                             content_type='multipart/form-data',
                             follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Tipo de archivo no permitido', resp.data)


class SecurityHeadersTest(BaseTestCase):
    def test_security_headers_present(self):
        resp = self.app.get('/login')
        self.assertEqual(resp.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(resp.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(resp.headers.get('X-XSS-Protection'), '1; mode=block')
        self.assertIn('Content-Security-Policy', resp.headers)


class AuthTest(BaseTestCase):
    def test_redirectSinLogin(self):
        resp = self.app.get('/dashboard', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers.get('Location'))


if __name__ == '__main__':
    unittest.main()
