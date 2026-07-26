from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def add_paragraph(doc, text, bold=False, italic=False, alignment=None,
                  space_after=Pt(6), font_size=Pt(12), first_line_indent=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = font_size
    run.font.name = 'Times New Roman'
    run.bold = bold
    run.italic = italic
    if alignment:
        p.alignment = alignment
    p.paragraph_format.space_after = space_after
    p.paragraph_format.line_spacing = 1.5
    if first_line_indent:
        p.paragraph_format.first_line_indent = first_line_indent
    return p


def add_heading_apa(doc, text, level=1):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.bold = True
    if level == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run.font.size = Pt(14)
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(12)
    elif level == 2:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run.font.size = Pt(12)
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
    elif level == 3:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run.font.size = Pt(12)
        run.italic = True
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    return p


def add_code_block(doc, code, label=""):
    if label:
        p = doc.add_paragraph()
        run = p.add_run(label)
        run.font.size = Pt(10)
        run.font.name = 'Courier New'
        run.bold = True
        p.paragraph_format.line_spacing = 1.0

    for line in code.split('\n'):
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.size = Pt(9)
        run.font.name = 'Courier New'
        pf = p.paragraph_format
        pf.left_indent = Cm(1.27)
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing = 1.0
    return p


def add_figure_label(doc, label):
    p = doc.add_paragraph()
    run = p.add_run(label)
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'
    run.italic = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(12)
    return p


def add_table_label(doc, label):
    p = doc.add_paragraph()
    run = p.add_run(label)
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'
    run.italic = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(12)
    return p


def add_note(doc, text):
    p = doc.add_paragraph()
    run = p.add_run('Nota. ')
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'
    run.italic = True
    run2 = p.add_run(text)
    run2.font.size = Pt(10)
    run2.font.name = 'Times New Roman'
    run2.italic = True
    p.paragraph_format.space_after = Pt(12)
    return p


def create_table(doc, headers, data):
    table = doc.add_table(rows=1 + len(data), cols=len(headers))
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(11)
                run.font.name = 'Times New Roman'

    for row_idx, row_data in enumerate(data, 1):
        for col_idx, val in enumerate(row_data):
            table.rows[row_idx].cells[col_idx].text = val
            for paragraph in table.rows[row_idx].cells[col_idx].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(11)
                    run.font.name = 'Times New Roman'

    return table


def create_report():
    doc = Document()

    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.5

    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    # ================================================================
    # PORTADA
    # ================================================================
    for _ in range(3):
        doc.add_paragraph()

    add_paragraph(doc, 'UNIVERSIDAD NACIONAL AGRARIA DE LA SELVA',
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(14))
    add_paragraph(doc, 'FACULTAD DE INGENIERIA EN INFORMATICA Y SISTEMAS',
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12))
    add_paragraph(doc, 'ESCUELA PROFESIONAL DE INGENIERIA EN INFORMATICA Y SISTEMAS',
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(11))

    doc.add_paragraph()
    doc.add_paragraph()

    add_paragraph(doc,
        'Analisis de Seguridad en una Aplicacion Web Academica:\n'
        'De Vulnerabilidades a Practicas SecDevOps',
        bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(14))

    doc.add_paragraph()
    doc.add_paragraph()

    add_paragraph(doc, 'Alumno: Zelaya Albornoz, Anali Amy',
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12))
    doc.add_paragraph()
    add_paragraph(doc, 'IS040704B: Seguridad Informatica',
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12))
    add_paragraph(doc, 'Docente: Mg. Ramos Estela, Juan',
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12))
    add_paragraph(doc, 'Semestre: 2026 - I',
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12))
    add_paragraph(doc, 'Tingo Maria - Peru',
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12))

    doc.add_page_break()

    # ================================================================
    # INDICE DE FIGURAS
    # ================================================================
    add_heading_apa(doc, 'Indice de figuras', level=1)
    figuras = [
        ('Figura 1', 'Estructura del repositorio Git con ramas V1 y V2'),
        ('Figura 2', 'Modelo de datos - Diagrama de tablas'),
        ('Figura 3', 'V1 - SQL Injection en busqueda de estudiantes'),
        ('Figura 4', 'V1 - Passwords en texto plano en la BD'),
        ('Figura 5', 'V1 - Archivos subidos sin validacion'),
        ('Figura 6', 'V2 - Queries parametrizadas corregidas'),
        ('Figura 7', 'V2 - Hashing de passwords con bcrypt'),
        ('Figura 8', 'V2 - Headers de seguridad configurados'),
        ('Figura 9', 'V2 - Validacion de archivos con whitelist'),
        ('Figura 10', 'Resultados de tests automatizados (8/8 passing)'),
        ('Figura 11', 'Comparativa de seguridad V1 vs V2'),
    ]
    for num, desc in figuras:
        p = doc.add_paragraph()
        run = p.add_run(f'{num} {desc}')
        run.font.size = Pt(11)
        run.font.name = 'Times New Roman'
        p.paragraph_format.space_after = Pt(2)

    doc.add_page_break()

    # ================================================================
    # CONTENIDO - DESARROLLO
    # ================================================================
    add_heading_apa(doc, 'Contenido', level=1)

    # --- 1. Descripcion de la Aplicacion ---
    add_heading_apa(doc, '1. Descripcion de la Aplicacion', level=2)

    add_paragraph(doc,
        'La aplicacion desarrollada es un Sistema Academico basico que permite gestionar '
        'estudiantes, cursos, notas y archivos. Fue construida en dos versiones para '
        'demostrar la diferencia entre una aplicacion insegura y una desarrollada con '
        'practicas de seguridad.',
        first_line_indent=Cm(1.27))

    add_heading_apa(doc, '1.1 Stack Tecnologico', level=3)
    add_paragraph(doc, 'La aplicacion fue desarrollada con las siguientes tecnologias:',
                  first_line_indent=Cm(1.27))

    create_table(doc,
        ['Componente', 'Tecnologia'],
        [
            ('Backend', 'Python 3.12 + Flask 3.0.3'),
            ('Base de datos', 'SQLite'),
            ('Frontend', 'HTML5 + Bootstrap 5 + Jinja2'),
            ('Seguridad V2', 'bcrypt, python-dotenv'),
            ('Testing', 'pytest'),
            ('Control de versiones', 'Git (ramas main y v1-insegura)'),
        ])
    add_table_label(doc, 'Tabla 1. Stack tecnologico de la aplicacion')

    add_heading_apa(doc, '1.2 Modelo de Datos', level=3)
    add_paragraph(doc,
        'La base de datos SQLite contiene cinco tablas principales:',
        first_line_indent=Cm(1.27))

    create_table(doc,
        ['Tabla', 'Campos Principales', 'Relacion'],
        [
            ('usuarios', 'id, username, password, rol', 'Autenticacion'),
            ('estudiantes', 'id, nombre, email, carrera', 'CRUD principal'),
            ('cursos', 'id, nombre, codigo, creditos', 'CRUD principal'),
            ('notas', 'id, estudiante_id, curso_id, nota, ciclo', 'FK estudiantes/cursos'),
            ('archivos', 'id, nombre_original, nombre_guardado, ruta', 'FK a usuarios'),
        ])
    add_table_label(doc, 'Tabla 2. Modelo de datos de la aplicacion')

    add_figure_label(doc, 'Figura 2. Modelo de datos - Diagrama de tablas')

    add_heading_apa(doc, '1.3 Funcionalidades', level=3)
    funcs = [
        'Inicio de sesion con autenticacion de usuarios.',
        'Dashboard con estadisticas generales del sistema.',
        'CRUD completo de estudiantes (crear, leer, actualizar, eliminar).',
        'CRUD completo de cursos.',
        'CRUD de notas con asignacion a estudiantes y cursos.',
        'Subida, listado, descarga y eliminacion de archivos.',
    ]
    for f in funcs:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(f)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    add_heading_apa(doc, '1.4 Estructura del Repositorio', level=3)
    add_paragraph(doc,
        'El proyecto utiliza dos ramas en Git para separar las versiones:',
        first_line_indent=Cm(1.27))

    add_code_block(doc,
        '* main (V2 - segura, practicas SecDevOps)\n'
        '|\n'
        '└── v1-insegura (V1 - con vulnerabilidades deliberadas)')

    add_figure_label(doc, 'Figura 1. Estructura del repositorio Git con ramas V1 y V2')

    doc.add_page_break()

    # --- 2. Version 1: Analisis de Vulnerabilidades ---
    add_heading_apa(doc, '2. Version 1: Analisis de Vulnerabilidades', level=2)

    add_paragraph(doc,
        'La version 1 de la aplicacion fue construida deliberadamente con multiples '
        'vulnerabilidades de seguridad. A continuacion se analizan las cuatro '
        'vulnerabilidades principales identificadas.',
        first_line_indent=Cm(1.27))

    # 2.1 SQL Injection
    add_heading_apa(doc, '2.1 SQL Injection', level=3)

    add_paragraph(doc,
        'La vulnerabilidad de SQL Injection se presenta cuando los datos del usuario '
        'se concatenan directamente en las consultas SQL sin sanitizar. Esto permite '
        'a un atacante manipular la consulta para acceder, modificar o eliminar datos.',
        first_line_indent=Cm(1.27))

    add_paragraph(doc, 'Codigo vulnerable en la ruta de login (V1):', bold=True)
    add_code_block(doc,
        '# VULNERABILIDAD: SQL Injection via concatenacion de strings\n'
        'query = ("SELECT * FROM usuarios WHERE username=\'" + username\n'
        "          + \"' AND password='\" + password + \"'\")\n"
        'cursor.execute(query)',
        'app.py (V1)')

    add_figure_label(doc, 'Figura 3. SQL Injection en busqueda de estudiantes')

    add_paragraph(doc,
        'Con un payload como admin\' OR \'1\'=\'1, un atacante puede evadir la '
        'autenticacion y acceder al sistema sin credenciales validas. La misma '
        'vulnerabilidad se presenta en la busqueda de estudiantes y en todas las '
        'operaciones CRUD.',
        first_line_indent=Cm(1.27))

    # 2.2 Autenticacion Rota
    add_heading_apa(doc, '2.2 Autenticacion Rota', level=3)

    add_paragraph(doc,
        'La version 1 presenta multiples problemas en el sistema de autenticacion:',
        first_line_indent=Cm(1.27))

    auth_issues = [
        'Passwords almacenados en texto plano en la base de datos.',
        'Credenciales hardcodeadas en el codigo fuente (admin/admin123).',
        'Sin mecanismo de rate limiting contra ataques de fuerza bruta.',
        'Secret key de Flask hardcodeada y predecible (app.secret_key = "12345").',
        'Debug mode activado en produccion, exponiendo informacion sensible.',
    ]
    for issue in auth_issues:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(issue)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    add_figure_label(doc, 'Figura 4. Passwords en texto plano en la BD')

    add_paragraph(doc,
        'Estas debilidades permiten ataques de fuerza bruta similares a los '
        'demostrados en la Unidad III del curso utilizando herramientas como Hydra, '
        'donde se explotan credenciales debiles o por defecto para obtener acceso '
        'no autorizado.',
        first_line_indent=Cm(1.27))

    # 2.3 XSS
    add_heading_apa(doc, '2.3 Cross-Site Scripting (XSS)', level=3)

    add_paragraph(doc,
        'El Cross-Site Scripting (XSS) es una vulnerabilidad que permite a un '
        'atacante inyectar codigo JavaScript malicioso en las paginas web vistas '
        'por otros usuarios. En la version 1, los campos de entrada como nombre '
        'de estudiante no estan sanitizados, permitiendo XSS almacenado.',
        first_line_indent=Cm(1.27))

    add_paragraph(doc,
        'Si un atacante ingresa un nombre como <script>alert("XSS")</script>, '
        'este se almacena en la base de datos y se renderiza directamente en el '
        'navegador de cualquier usuario que consulte la lista de estudiantes, '
        'ejecutando el codigo malicioso.',
        first_line_indent=Cm(1.27))

    # 2.4 Upload Inseguro
    add_heading_apa(doc, '2.4 Subida de Archivos Insegura', level=3)

    add_paragraph(doc,
        'La version 1 permite subir cualquier tipo de archivo sin validacion alguna. '
        'Esto representa multiples riesgos:',
        first_line_indent=Cm(1.27))

    upload_issues = [
        'Sin validacion de extension: archivos ejecutables (.exe, .php) pueden subirse.',
        'Sin validacion de tamano: archivos de gigabytes pueden agotar el espacio del servidor.',
        'Nombre original preservado: permite path traversal y sobreescritura de archivos.',
        'Archivos guardados en directorio web-accessible: acceso directo desde el navegador.',
    ]
    for issue in upload_issues:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(issue)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    add_figure_label(doc, 'Figura 5. Archivos subidos sin validacion')

    doc.add_page_break()

    # --- 3. Version 2: Soluciones con SecDevOps ---
    add_heading_apa(doc, '3. Version 2: Soluciones con SecDevOps', level=2)

    add_paragraph(doc,
        'La version 2 corrige todas las vulnerabilidades identificadas en la version 1 '
        'e incorpora practicas de seguridad en todo el ciclo de desarrollo.',
        first_line_indent=Cm(1.27))

    # 3.1 SQL Injection fix
    add_heading_apa(doc, '3.1 Correccion de SQL Injection', level=3)

    add_paragraph(doc,
        'Todas las consultas SQL fueron modificadas para usar queries parametrizadas '
        'con el caracter ? como marcador de posicion. Esto garantiza que los datos del '
        'usuario nunca se interpreten como parte de la consulta SQL.',
        first_line_indent=Cm(1.27))

    add_paragraph(doc, 'Codigo corregido (V2):', bold=True)
    add_code_block(doc,
        '# CORRECCION: Query parametrizada\n'
        "cursor.execute(\n"
        "    \"SELECT * FROM usuarios WHERE username = ?\",\n"
        "    (username,),\n"
        ")",
        'app.py (V2)')

    add_figure_label(doc, 'Figura 6. Queries parametrizadas corregidas')

    add_paragraph(doc,
        'Esta correccion se aplico en todas las rutas de la aplicacion: login, '
        'busqueda de estudiantes, creacion, actualizacion y eliminacion de registros.',
        first_line_indent=Cm(1.27))

    # 3.2 Auth fix
    add_heading_apa(doc, '3.2 Mejora de Autenticacion', level=3)

    add_paragraph(doc,
        'El sistema de autenticacion fue completamente refactorizado:',
        first_line_indent=Cm(1.27))

    auth_fixes = [
        'Passwords hasheados con bcrypt: algoritmo de hash adaptativo con salt automatico.',
        'Secret key en variable de entorno (.env): evita exponer credenciales en el codigo.',
        'Debug mode desactivado: previene la exposicion de informacion sensible.',
        'Logging de eventos de seguridad: registro de intentos de login exitosos y fallidos.',
        'Decorador login_required: protege todas las rutas que requieren autenticacion.',
    ]
    for fix in auth_fixes:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(fix)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    add_paragraph(doc, 'Codigo de verificacion de password (V2):', bold=True)
    add_code_block(doc,
        '# CORRECCION: Verificacion segura con bcrypt\n'
        "if user and bcrypt.checkpw(password, user['password'].encode()):\n"
        "    session['user_id'] = user['id']\n"
        "    logger.info(f\"Login exitoso: {username}\")",
        'app.py (V2)')

    add_figure_label(doc, 'Figura 7. Hashing de passwords con bcrypt')

    # 3.3 XSS fix
    add_heading_apa(doc, '3.3 Prevencion de XSS', level=3)

    add_paragraph(doc,
        'La proteccion contra XSS se logro mediante multiples capas:',
        first_line_indent=Cm(1.27))

    xss_fixes = [
        'Auto-escaping de Jinja2: todas las variables se escapan automaticamente en los templates.',
        'Validacion de entrada: campos con longitud maxima y tipos de datos definidos.',
        'Content Security Policy (CSP): headers que restringen la ejecucion de scripts.',
        'X-XSS-Protection: header del navegador que activa el filtro de XSS.',
    ]
    for fix in xss_fixes:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(fix)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    add_paragraph(doc, 'Headers de seguridad (V2):', bold=True)
    add_code_block(doc,
        "@app.after_request\n"
        "def set_security_headers(response):\n"
        "    response.headers['X-Content-Type-Options'] = 'nosniff'\n"
        "    response.headers['X-Frame-Options'] = 'DENY'\n"
        "    response.headers['X-XSS-Protection'] = '1; mode=block'\n"
        "    response.headers['Content-Security-Policy'] = (\n"
        "        \"default-src 'self'; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net\"\n"
        "    )\n"
        "    response.headers['Strict-Transport-Security'] = (\n"
        "        'max-age=31536000; includeSubDomains'\n"
        "    )\n"
        "    return response",
        'app.py (V2)')

    add_figure_label(doc, 'Figura 8. Headers de seguridad configurados')

    # 3.4 Upload fix
    add_heading_apa(doc, '3.4 Seguridad en Subida de Archivos', level=3)

    add_paragraph(doc,
        'La gestion de archivos fue reforzada con las siguientes medidas:',
        first_line_indent=Cm(1.27))

    upload_fixes = [
        'Whitelist de extensiones: solo se permiten tipos especificos (pdf, png, jpg, etc.).',
        'Validacion de tipo MIME: verifica que el tipo de archivo coincida con la extension.',
        'Renombrado con UUID: los archivos se guardan con nombres aleatorios para evitar conflictos.',
        'Nombre seguro: uso de secure_filename() de Werkzeug para prevenir path traversal.',
        'Tamano maximo: limite de 5MB configurado via MAX_CONTENT_LENGTH.',
    ]
    for fix in upload_fixes:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(fix)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    add_figure_label(doc, 'Figura 9. Validacion de archivos con whitelist')

    # 3.5 Herramientas DevSecOps
    add_heading_apa(doc, '3.5 Herramientas DevSecOps', level=3)

    add_paragraph(doc,
        'Se integran las siguientes herramientas en el pipeline de desarrollo:',
        first_line_indent=Cm(1.27))

    create_table(doc,
        ['Herramienta', 'Tipo', 'Funcion'],
        [
            ('Bandit', 'SAST', 'Analisis estatico de codigo Python'),
            ('Safety', 'SCA', 'Verificacion de dependencias'),
            ('pytest', 'Testing', 'Tests automatizados de seguridad'),
        ])
    add_table_label(doc, 'Tabla 3. Herramientas DevSecOps integradas')

    # 3.6 Tests automatizados
    add_heading_apa(doc, '3.6 Tests Automatizados', level=3)

    add_paragraph(doc,
        'Se implementaron 8 tests automatizados que verifican las correcciones '
        'de seguridad en la version 2:',
        first_line_indent=Cm(1.27))

    create_table(doc,
        ['Test', 'Verificacion'],
        [
            ('test_login_correcto', 'Login exitoso con credenciales validas'),
            ('test_login_incorrecto', 'Rechazo con credenciales invalidas'),
            ('test_sqli_busqueda_inyectada', 'SQL Injection no funciona en busqueda'),
            ('test_sqli_union_attack', 'UNION injection no funciona'),
            ('test_upload_extension_no_permitida', 'Archivos .exe son rechazados'),
            ('test_upload_svg_no_permitido', 'Archivos .svg son rechazados'),
            ('test_security_headers_present', 'Headers de seguridad presentes'),
            ('test_redirectSinLogin', 'Redireccion al login sin sesion'),
        ])
    add_table_label(doc, 'Tabla 4. Tests automatizados de seguridad')

    add_figure_label(doc, 'Figura 10. Resultados de tests automatizados (8/8 passing)')

    doc.add_page_break()

    # --- 4. Comparativa ---
    add_heading_apa(doc, '4. Comparativa Version 1 vs Version 2', level=2)

    add_paragraph(doc,
        'La siguiente tabla resume las diferencias de seguridad entre ambas versiones:',
        first_line_indent=Cm(1.27))

    create_table(doc,
        ['Aspecto', 'Version 1 (Insegura)', 'Version 2 (Segura)'],
        [
            ('SQL Queries', 'Concatenacion de strings', 'Queries parametrizadas (?)'),
            ('Passwords', 'Texto plano', 'bcrypt hashing'),
            ('Secret Key', 'Hardcodeada ("12345")', 'Variable de entorno (.env)'),
            ('XSS', 'Sin sanitizacion', 'Auto-escaping Jinja2 + CSP'),
            ('File Upload', 'Sin validacion', 'Whitelist + UUID + validacion MIME'),
            ('Headers', 'Ninguno', 'CSP, HSTS, X-Frame-Options'),
            ('Debug Mode', 'Activado', 'Desactivado'),
            ('Tests', 'Ninguno', '8 tests automatizados'),
        ])
    add_table_label(doc, 'Tabla 5. Comparativa de seguridad entre Version 1 y Version 2')

    add_figure_label(doc, 'Figura 11. Comparativa de seguridad V1 vs V2')

    add_note(doc,
        'Los resultados muestran que la version 2 elimina las vulnerabilidades '
        'principales mediante la aplicacion de practicas de seguridad en el '
        'ciclo de desarrollo.')

    doc.add_page_break()

    # ================================================================
    # CONCLUSIONES
    # ================================================================
    add_heading_apa(doc, 'Conclusiones', level=1)

    conclusions = [
        'La construccion deliberada de una aplicacion insegura permite comprender '
        'de manera practica como funcionan las vulnerabilidades mas comunes en '
        'aplicaciones web. La experiencia de ver SQL Injection, XSS y problemas '
        'de autenticacion en codigo real fortalece la comprension teorica adquirida '
        'en el curso.',

        'Las queries parametrizadas son la solucion efectiva y sencilla contra '
        'SQL Injection. Su implementacion no afecta el rendimiento de la aplicacion '
        'y elimina completamente esta categoria de vulnerabilidad.',

        'El hashing de passwords con algoritmos como bcrypt es fundamental para '
        'la proteccion de credenciales. A diferencia del texto plano, un hash con '
        'salt fuerza a los atacantes a realizar fuerza bruta sobre cada hash '
        'individualmente.',

        'La integracion de la seguridad en el ciclo de desarrollo (SecDevOps) es '
        'mas efectiva que tratar de agregar seguridad al final del desarrollo. '
        'Herramientas como Bandit y Safety permiten detectar problemas '
        'automaticamente.',

        'Los tests automatizados de seguridad son esenciales para verificar que '
        'las correcciones funcionan correctamente y para prevenir regresiones en '
        'futuras versiones del codigo.',
    ]
    for c in conclusions:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(c)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    doc.add_page_break()

    # ================================================================
    # REFERENCIAS BIBLIOGRAFICAS
    # ================================================================
    add_heading_apa(doc, 'Referencias bibliograficas', level=1)

    references = [
        'OWASP. (2021). OWASP Top Ten. https://owasp.org/www-project-top-ten/',
        'Flask. (2024). Welcome to Flask. https://flask.palletsprojects.com/',
        'bcrypt. (2024). Password Hashing. https://pypi.org/project/bcrypt/',
        'OWASP. (2023). SQL Injection Prevention Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html',
        'OWASP. (2023). Cross-Site Scripting Prevention Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Scripting_Prevention_Cheat_Sheet.html',
        'OWASP. (2023). File Upload Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html',
        'Bandit. (2024). Bandit is a tool designed to find common issues in Python code. https://bandit.readthedocs.io/',
        'NIST. (2023). National Vulnerability Database. https://nvd.nist.gov/',
        'Microsoft. (2023). Secure Development Lifecycle. https://www.microsoft.com/en-us/securityengineering/sdl',
    ]
    for ref in references:
        p = doc.add_paragraph()
        run = p.add_run(ref)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'
        p.paragraph_format.left_indent = Cm(1.27)
        p.paragraph_format.first_line_indent = Cm(-1.27)
        p.paragraph_format.space_after = Pt(6)

    doc.save('Trabajo_Seguridad_Informatica.docx')
    print('Informe generado: Trabajo_Seguridad_Informatica.docx')


if __name__ == '__main__':
    create_report()
