import unittest

from test_base import BaseTestCase


class ErrorPagesTest(BaseTestCase):
    def test_404_pagina_personalizada(self):
        resp = self.app.get('/ruta-que-no-existe')
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b'404', resp.data)
        self.assertIn(b'no existe', resp.data)

    def test_403_pagina_personalizada(self):
        self.login_docente()
        resp = self.app.post('/estudiantes/crear', data={
            'nombre': 'X', 'email': 'x@x.com', 'carrera': 'Informatica',
        })
        self.assertEqual(resp.status_code, 403)
        self.assertIn(b'Acceso denegado', resp.data)

    def test_400_pagina_personalizada_csrf(self):
        self.login()
        self.app.application.config['WTF_CSRF_ENABLED'] = True
        try:
            resp = self.app.post('/estudiantes/crear', data={
                'nombre': 'X', 'email': 'x@x.com', 'carrera': 'Informatica',
            })
            self.assertEqual(resp.status_code, 400)
            self.assertIn(b'400', resp.data)
        finally:
            self.app.application.config['WTF_CSRF_ENABLED'] = False

    def test_500_pagina_personalizada(self):
        self.login()
        import app as app_module
        orig = app_module.get_db
        orig_testing = self.app.application.config.get('TESTING')
        orig_propagate = self.app.application.config.get('PROPAGATE_EXCEPTIONS')

        def boom():
            raise RuntimeError('error de prueba')

        app_module.get_db = boom
        self.app.application.config['TESTING'] = False
        self.app.application.config['PROPAGATE_EXCEPTIONS'] = False
        try:
            resp = self.app.get('/dashboard')
            self.assertEqual(resp.status_code, 500)
            self.assertIn(b'500', resp.data)
        finally:
            app_module.get_db = orig
            self.app.application.config['TESTING'] = orig_testing
            self.app.application.config['PROPAGATE_EXCEPTIONS'] = orig_propagate


if __name__ == '__main__':
    unittest.main()
