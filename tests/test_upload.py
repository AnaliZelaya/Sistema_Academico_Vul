import unittest
import io
import os
import sqlite3

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

    def test_upload_magic_bytes_no_coinciden(self):
        data = {
            'archivo': (io.BytesIO(b'<script>alert(1)</script>'), 'malicioso.pdf'),
        }
        resp = self.app.post('/archivos/subir', data=data,
                             content_type='multipart/form-data',
                             follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'El contenido no corresponde al tipo de archivo', resp.data)

    def test_upload_magic_bytes_png_falso_rechazado(self):
        data = {
            'archivo': (io.BytesIO(b'%PDF-1.4 fingido como imagen'), 'falso.png'),
        }
        resp = self.app.post('/archivos/subir', data=data,
                             content_type='multipart/form-data',
                             follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'El contenido no corresponde al tipo de archivo', resp.data)

    def test_upload_pdf_con_firma_valida_aceptado(self):
        data = {
            'archivo': (io.BytesIO(b'%PDF-1.4\n1 0 obj\n<<>>\nendobj'), 'doc.pdf'),
        }
        resp = self.app.post('/archivos/subir', data=data,
                             content_type='multipart/form-data',
                             follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Archivo subido exitosamente', resp.data)


class UploadWebrootTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.login()

    def test_archivo_no_servible_desde_static(self):
        data = {
            'archivo': (io.BytesIO(b'%PDF-1.4 contenido webroot'), 'webroot.pdf'),
        }
        resp = self.app.post('/archivos/subir', data=data,
                             content_type='multipart/form-data',
                             follow_redirects=True)
        self.assertIn(b'Archivo subido exitosamente', resp.data)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT nombre_guardado FROM archivos ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        guardado = row['nombre_guardado']
        upload_folder = self.app.application.config['UPLOAD_FOLDER']

        try:
            resp = self.app.get(f'/static/uploads/{guardado}')
            self.assertEqual(resp.status_code, 404,
                             'El archivo no debe ser accesible via /static/uploads/')
            resp = self.app.get(f'/archivos/descargar/{guardado}')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.content_type.split(';')[0], 'application/pdf')
            resp.close()
        finally:
            ruta = os.path.join(upload_folder, guardado)
            if os.path.exists(ruta):
                os.remove(ruta)


if __name__ == '__main__':
    unittest.main()
