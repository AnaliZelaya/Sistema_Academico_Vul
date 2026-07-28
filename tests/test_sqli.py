import unittest

from test_base import BaseTestCase


class SQLInjectionTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.login()

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


if __name__ == '__main__':
    unittest.main()
