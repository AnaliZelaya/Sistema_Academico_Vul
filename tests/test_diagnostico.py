import unittest
from unittest.mock import patch

from test_base import BaseTestCase


class DiagnosticoTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.login()

    def test_get_diagnostico_form(self):
        resp = self.app.get('/diagnostico')
        self.assertEqual(resp.status_code, 200)

    def test_comando_no_permitido_bloqueado(self):
        for comando in ('; id', '| whoami', 'whoami', 'uname', 'ping -c 1 127.0.0.1',
                        'rm -rf /', 'fecha; cat /etc/passwd'):
            resp = self.app.post('/diagnostico', data={'comando': comando})
            self.assertEqual(resp.status_code, 200, comando)
            self.assertIn(b'Comando no permitido', resp.data, comando)

    def test_comando_permitido_ejecuta_allowlist_sin_shell(self):
        fake = type('R', (), {'stdout': 'host-test\n', 'returncode': 0})()
        with patch('app.subprocess.run', return_value=fake) as mock_run:
            resp = self.app.post('/diagnostico', data={'comando': 'hostname'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'host-test', resp.data)
        self.assertEqual(mock_run.call_args.args[0], ['hostname'])
        self.assertFalse(mock_run.call_args.kwargs['shell'])
        self.assertEqual(mock_run.call_args.kwargs['timeout'], 10)

    def test_docente_no_accede(self):
        self.app.get('/logout')
        self.login_docente()
        resp = self.app.get('/diagnostico')
        self.assertEqual(resp.status_code, 403)

    def test_sin_login_redirige(self):
        self.app.get('/logout')
        resp = self.app.get('/diagnostico')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers.get('Location'))

    def test_post_sin_csrf_rechazado(self):
        self.app.application.config['WTF_CSRF_ENABLED'] = True
        try:
            resp = self.app.post('/diagnostico', data={'comando': 'hostname'})
            self.assertEqual(resp.status_code, 400)
        finally:
            self.app.application.config['WTF_CSRF_ENABLED'] = False


if __name__ == '__main__':
    unittest.main()
