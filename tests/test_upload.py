import unittest
import io

from test_base import BaseTestCase


class UploadTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.login()

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


if __name__ == '__main__':
    unittest.main()
