import unittest
import os
import sys
import sqlite3
import jinja2

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from app import app, limiter

app.jinja_env.loader = jinja2.FileSystemLoader(os.path.join(ROOT_DIR, 'templates'))
app.static_folder = os.path.join(ROOT_DIR, 'static')
# El rate limit se evalua sobre un atributo fijado en init, no en app.config,
# por lo que se desactiva aqui para que los tests no se bloqueen entre si.
limiter.enabled = False


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['RATELIMIT_ENABLED'] = False
        self.app = app.test_client()
        self.db_path = os.path.join(ROOT_DIR, 'test_academico.db')

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

        import app as app_module
        self._orig_db = app_module.DB_PATH
        app_module.DB_PATH = self.db_path

    def tearDown(self):
        import app as app_module
        app_module.DB_PATH = self._orig_db
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def login(self):
        return self.app.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
        })
