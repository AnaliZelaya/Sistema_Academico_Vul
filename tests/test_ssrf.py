import unittest
from unittest.mock import patch

from werkzeug.exceptions import HTTPException

from app import _validar_url_ssrf
from test_base import BaseTestCase


class ValidarURLSSRFTest(BaseTestCase):
    def _bloqueada(self, url):
        with self.assertRaises(HTTPException) as ctx:
            _validar_url_ssrf(url)
        self.assertEqual(ctx.exception.code, 403, f'URL deberia ser SSRF bloqueada: {url}')

    def _rechazada(self, url):
        with self.assertRaises(HTTPException) as ctx:
            _validar_url_ssrf(url)
        self.assertEqual(ctx.exception.code, 400, f'URL deberia ser rechazada: {url}')

    def test_loopback_bloqueado(self):
        for url in ('http://127.0.0.1/', 'http://127.0.0.1:5000/login', 'http://[::1]/'):
            self._bloqueada(url)

    def test_redes_privadas_bloqueadas(self):
        for url in ('http://10.0.0.1/', 'http://172.16.0.1/', 'http://172.31.255.1/',
                    'http://192.168.1.1/', 'http://[fc00::1]/'):
            self._bloqueada(url)

    def test_metadata_y_link_local_bloqueados(self):
        self._bloqueada('http://169.254.169.254/latest/meta-data/')
        self._bloqueada('http://169.254.1.1/')

    def test_localhost_bloqueado(self):
        with patch('app.socket.getaddrinfo', return_value=[(2, 1, 6, '', ('127.0.0.1', 80))]):
            self._bloqueada('http://localhost/')

    def test_esquema_no_permitido(self):
        for url in ('file:///etc/passwd', 'ftp://ftp.example.com/', 'gopher://10.0.0.1/'):
            self._rechazada(url)

    def test_sin_esquema_o_host(self):
        self._rechazada('localhost/x')
        self._rechazada('http:///path')

    def test_puerto_invalido(self):
        self._rechazada('http://8.8.8.8:99999/')

    def test_ip_publica_permitida(self):
        for url in ('http://8.8.8.8/', 'http://1.1.1.1/'):
            _validar_url_ssrf(url)


class ImportarEndpointTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.login()

    def test_get_importar_form(self):
        resp = self.app.get('/importar')
        self.assertEqual(resp.status_code, 200)

    def test_post_url_privada_403(self):
        resp = self.app.post('/importar', data={'url': 'http://169.254.169.254/latest/meta-data/'})
        self.assertEqual(resp.status_code, 403)

    def test_post_loopback_403(self):
        resp = self.app.post('/importar', data={'url': 'http://127.0.0.1:5000/'})
        self.assertEqual(resp.status_code, 403)

    def test_post_file_400(self):
        resp = self.app.post('/importar', data={'url': 'file:///etc/passwd'})
        self.assertEqual(resp.status_code, 400)

    def test_post_url_publica_200(self):
        with patch('app._fetch_url', return_value=(200, b'<html>contenido ok</html>', 'http://8.8.8.8/')):
            resp = self.app.post('/importar', data={'url': 'http://8.8.8.8/'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'contenido ok', resp.data)

    def test_post_sin_csrf_rechazado(self):
        self.app.application.config['WTF_CSRF_ENABLED'] = True
        try:
            resp = self.app.post('/importar', data={'url': 'http://8.8.8.8/'})
            self.assertEqual(resp.status_code, 400)
        finally:
            self.app.application.config['WTF_CSRF_ENABLED'] = False

    def test_docente_no_accede(self):
        self.app.get('/logout')
        self.login_docente()
        resp = self.app.get('/importar')
        self.assertEqual(resp.status_code, 403)

    def test_sin_login_redirige(self):
        self.app.get('/logout')
        resp = self.app.get('/importar')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers.get('Location'))


if __name__ == '__main__':
    unittest.main()
