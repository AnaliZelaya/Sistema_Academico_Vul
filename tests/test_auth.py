import unittest

from test_base import BaseTestCase


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


class AuthTest(BaseTestCase):
    def test_redirectSinLogin(self):
        resp = self.app.get('/dashboard', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers.get('Location'))


class SecurityHeadersTest(BaseTestCase):
    def test_security_headers_present(self):
        resp = self.app.get('/login')
        self.assertEqual(resp.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(resp.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(resp.headers.get('X-XSS-Protection'), '1; mode=block')
        self.assertIn('Content-Security-Policy', resp.headers)


if __name__ == '__main__':
    unittest.main()
