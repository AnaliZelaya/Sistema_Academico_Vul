import unittest
import time

import app as app_module
from test_base import BaseTestCase


class LockoutTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        app_module._intentos_fallidos.clear()
        app_module._bloqueos.clear()

    def tearDown(self):
        app_module._intentos_fallidos.clear()
        app_module._bloqueos.clear()
        super().tearDown()

    def test_bloqueo_tras_5_fallos(self):
        for _ in range(5):
            self.app.post('/login', data={'username': 'admin', 'password': 'mala'})
        resp = self.app.post('/login', data={'username': 'admin', 'password': 'admin123'})
        self.assertIn(b'Cuenta bloqueada temporalmente', resp.data)
        self.assertNotIn(b'Inicio de sesion exitoso', resp.data)

    def test_bloqueo_no_afecta_a_otro_usuario(self):
        for _ in range(5):
            self.app.post('/login', data={'username': 'admin', 'password': 'mala'})
        resp = self.app.post('/login', data={'username': 'profesor', 'password': 'profesor'},
                             follow_redirects=True)
        self.assertIn(b'Inicio de sesion exitoso', resp.data)

    def test_login_exitoso_limpia_intentos(self):
        for _ in range(4):
            self.app.post('/login', data={'username': 'admin', 'password': 'mala'})
        resp = self.app.post('/login', data={'username': 'admin', 'password': 'admin123'},
                             follow_redirects=True)
        self.assertIn(b'Inicio de sesion exitoso', resp.data)
        self.assertNotIn('admin', app_module._intentos_fallidos)
        self.assertNotIn('admin', app_module._bloqueos)

    def test_bloqueo_expirado_permite_login(self):
        app_module._bloqueos['admin'] = time.time() - 1
        resp = self.app.post('/login', data={'username': 'admin', 'password': 'admin123'},
                             follow_redirects=True)
        self.assertIn(b'Inicio de sesion exitoso', resp.data)


if __name__ == '__main__':
    unittest.main()
