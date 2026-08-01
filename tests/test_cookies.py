import unittest

from test_base import BaseTestCase


class CookieFlagsTest(BaseTestCase):
    def test_cookie_httponly_y_samesite(self):
        resp = self.app.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
        }, follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        cookie = resp.headers.get('Set-Cookie', '')
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Lax', cookie)

    def test_cookie_secure_cuando_https_activado(self):
        self.app.application.config['SESSION_COOKIE_SECURE'] = True
        try:
            resp = self.app.post('/login', data={
                'username': 'admin',
                'password': 'admin123',
            }, follow_redirects=False)
            cookie = resp.headers.get('Set-Cookie', '')
            self.assertIn('Secure', cookie)
        finally:
            self.app.application.config['SESSION_COOKIE_SECURE'] = False

    def test_cookie_no_secure_sin_https(self):
        resp = self.app.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
        }, follow_redirects=False)
        cookie = resp.headers.get('Set-Cookie', '')
        self.assertNotIn('Secure', cookie)


if __name__ == '__main__':
    unittest.main()
