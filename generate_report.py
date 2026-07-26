from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def set_cell_shading(cell, color):
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)


def add_paragraph(doc, text, style='Normal', bold=False, italic=False,
                  alignment=None, space_after=Pt(6), font_size=Pt(12),
                  first_line_indent=None):
    p = doc.add_paragraph(style=style)
    run = p.add_run(text)
    run.font.size = font_size
    run.font.name = 'Times New Roman'
    run.bold = bold
    run.italic = italic
    if alignment:
        p.alignment = alignment
    p.paragraph_format.space_after = space_after
    if first_line_indent:
        p.paragraph_format.first_line_indent = first_line_indent
    return p


def add_heading_apa(doc, text, level=1):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(12)
    run.font.name = 'Times New Roman'
    run.bold = True
    if level == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run.font.size = Pt(14)
    elif level == 2:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    return p


def add_code_block(doc, code, label=""):
    if label:
        p = doc.add_paragraph()
        run = p.add_run(label)
        run.font.size = Pt(10)
        run.font.name = 'Courier New'
        run.bold = True

    p = doc.add_paragraph()
    run = p.add_run(code)
    run.font.size = Pt(9)
    run.font.name = 'Courier New'
    pf = p.paragraph_format
    pf.left_indent = Cm(1.27)
    pf.space_before = Pt(3)
    pf.space_after = Pt(3)
    return p


def create_report():
    doc = Document()

    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 2.0

    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    # === PORTADA ===
    for _ in range(6):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('Analisis de Seguridad en una Aplicacion Web Academica:\nDe Vulnerabilidades a Practicas SecDevOps')
    run.font.size = Pt(14)
    run.font.name = 'Times New Roman'
    run.bold = True

    doc.add_paragraph()
    add_paragraph(doc, 'Anali Zelaya Albornoz', alignment=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    add_paragraph(doc, 'Universidad Nacional Abierta y a Distancia - UNAD', alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_paragraph(doc, 'Escuela de Ciencias Sociales, Artes y Humanidades - ECSAH', alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_paragraph(doc, 'Programa de Ingenieria de Sistemas', alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_paragraph(doc, 'Seguridad Informatica', alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_paragraph(doc, '2026', alignment=WD_ALIGN_PARAGRAPH.CENTER)

    doc.add_page_break()

    # === RESUMEN ===
    add_heading_apa(doc, 'Resumen', level=1)
    add_paragraph(doc,
        'El presente informe documenta el desarrollo de una aplicacion web academica basica '
        'construida en dos versiones: una primera version deliberadamente insegura y una segunda '
        'version corregida aplicando practicas de Secure Development Operations (SecDevOps). '
        'La aplicacion incluye funcionalidades de autenticacion, CRUD de estudiantes, cursos y '
        'notas, y subida de archivos. Se identificaron y documentaron cuatro vulnerabilidades '
        'principales: SQL Injection, autenticacion rota, Cross-Site Scripting (XSS) y subida '
        'de archivos insegura. La segunda version corrige estas vulnerabilidades mediante queries '
        'parametrizadas, hashing con bcrypt, validacion de entrada, headers de seguridad y '
        'tests automatizados. El proyecto demuestra la importancia de integrar la seguridad '
        'en cada fase del ciclo de vida del desarrollo de software.',
        first_line_indent=Cm(1.27))

    p = doc.add_paragraph()
    run = p.add_run('Palabras clave: ')
    run.bold = True
    run.font.size = Pt(12)
    run.font.name = 'Times New Roman'
    run2 = p.add_run('Seguridad informatica, SQL Injection, XSS, SecDevOps, aplicaciones web')
    run2.font.size = Pt(12)
    run2.font.name = 'Times New Roman'

    doc.add_page_break()

    # === ABSTRACT ===
    add_heading_apa(doc, 'Abstract', level=1)
    add_paragraph(doc,
        'This report documents the development of a basic academic web application built in '
        'two versions: a first deliberately insecure version and a second corrected version '
        'applying Secure Development Operations (SecDevOps) practices. The application includes '
        'authentication functionality, CRUD operations for students, courses, and grades, and '
        'file upload. Four main vulnerabilities were identified and documented: SQL Injection, '
        'broken authentication, Cross-Site Scripting (XSS), and insecure file upload. The '
        'second version corrects these vulnerabilities through parameterized queries, bcrypt '
        'hashing, input validation, security headers, and automated tests. The project '
        'demonstrates the importance of integrating security throughout the software '
        'development lifecycle.',
        first_line_indent=Cm(1.27))

    p = doc.add_paragraph()
    run = p.add_run('Keywords: ')
    run.bold = True
    run.font.size = Pt(12)
    run.font.name = 'Times New Roman'
    run2 = p.add_run('cybersecurity, SQL Injection, XSS, SecDevOps, web applications')
    run2.font.size = Pt(12)
    run2.font.name = 'Times New Roman'

    doc.add_page_break()

    # === TABLA DE CONTENIDO ===
    add_heading_apa(doc, 'Tabla de Contenido', level=1)
    toc_items = [
        ('Resumen', '2'), ('Abstract', '3'), ('Introduccion', '5'),
        ('Justificacion', '5'), ('Objetivos', '6'),
        ('1. Descripcion de la Aplicacion', '7'),
        ('1.1 Stack Tecnologico', '7'), ('1.2 Modelo de Datos', '7'),
        ('1.3 Funcionalidades', '8'),
        ('2. Version 1: Analisis de Vulnerabilidades', '9'),
        ('2.1 SQL Injection', '9'), ('2.2 Autenticacion Rota', '10'),
        ('2.3 Cross-Site Scripting (XSS)', '11'),
        ('2.4 Subida de Archivos Insegura', '12'),
        ('3. Version 2: Soluciones con SecDevOps', '13'),
        ('3.1 Correccion de SQL Injection', '13'),
        ('3.2 Mejora de Autenticacion', '14'),
        ('3.3 Prevencion de XSS', '15'),
        ('3.4 Seguridad en Subida de Archivos', '16'),
        ('3.5 Medidas Adicionales', '17'),
        ('3.6 Herramientas DevSecOps', '18'),
        ('4. Comparativa V1 vs V2', '19'),
        ('Conclusiones', '20'), ('Referencias', '21'),
    ]
    for item, page in toc_items:
        p = doc.add_paragraph()
        run = p.add_run(f'{item}')
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'
        p.paragraph_format.space_after = Pt(2)

    doc.add_page_break()

    # === INTRODUCCION ===
    add_heading_apa(doc, 'Introduccion', level=1)
    add_paragraph(doc,
        'En el contexto actual de constante transformacion digital, la seguridad informatica '
        'se ha convertido en un factor critico para el desarrollo de aplicaciones web. Las '
        'vulnerabilidades en las aplicaciones representan una de las principales amenazas para '
        'las organizaciones, ya que pueden ser explotadas para robar datos, comprometer '
        'sistemas o alterar la integridad de la informacion.',
        first_line_indent=Cm(1.27))
    add_paragraph(doc,
        'El presente proyecto tiene como proposito desarrollar una aplicacion web academica '
        'basica que permita demostrar, de manera practica, las diferencias entre una aplicacion '
        'con problemas de seguridad y una construida bajo principios de Secure Development '
        'Operations (SecDevOps). La aplicacion incluye funcionalidades fundamentales como '
        'autenticacion de usuarios, operaciones CRUD sobre estudiantes, cursos y notas, y '
        'gestion de archivos.',
        first_line_indent=Cm(1.27))
    add_paragraph(doc,
        'El enfoque metodologico consiste en construir primero una version deliberadamente '
        'insegura (V1) que contenga vulnerabilidades comunes, y posteriormente una version '
        'corregida (V2) que demuestre las soluciones adecuadas. Ambas versiones estan '
        'documentadas en el repositorio de codigo fuente y acompanadas de tests automatizados '
        'que verifican la presencia de vulnerabilidades en V1 y su correccion en V2.',
        first_line_indent=Cm(1.27))

    # === JUSTIFICACION ===
    add_heading_apa(doc, 'Justificacion', level=1)
    add_paragraph(doc,
        'La eleccion de este tema responde a la necesidad de comprender con mayor profundidad '
        'como las vulnerabilidades de seguridad impactan en las aplicaciones web. Segun OWASP '
        '(Open Web Application Security Project), las diez vulnerabilidades mas criticas '
        'incluyen SQL Injection, Cross-Site Scripting y problemas de autenticacion, todas las '
        'cuales estan presentes en la version 1 de esta aplicacion.',
        first_line_indent=Cm(1.27))
    add_paragraph(doc,
        'La practica de SecDevOps representa una evolucion del paradigma DevOps que integra '
        'la seguridad en todas las fases del ciclo de vida del desarrollo de software. Su '
        'adopcion permite detectar y corregir vulnerabilidades desde las etapas tempranas del '
        'desarrollo, reduciendo significativamente los costos y riesgos asociados.',
        first_line_indent=Cm(1.27))
    add_paragraph(doc,
        'Este proyecto es relevante porque permite al estudiante experimentar de manera directa '
        'tanto las vulnerabilidades como sus soluciones, fortaleciendo su comprension sobre '
        'seguridad en el desarrollo de software y preparandolo para enfrentar desafios reales '
        'en el ambito profesional.',
        first_line_indent=Cm(1.27))

    # === OBJETIVOS ===
    add_heading_apa(doc, 'Objetivos', level=1)
    add_heading_apa(doc, 'Objetivo General', level=2)
    add_paragraph(doc,
        'Desarrollar una aplicacion web academica que permita demostrar las diferencias '
        'entre una aplicacion con vulnerabilidades de seguridad y una construida con practicas '
        'SecDevOps, documentando los problemas encontrados y las soluciones aplicadas.',
        first_line_indent=Cm(1.27))

    add_heading_apa(doc, 'Objetivos Especificos', level=2)
    objectives = [
        'Implementar una aplicacion web con funcionalidades de autenticacion, CRUD y subida de archivos.',
        'Identificar y documentar vulnerabilidades de seguridad comunes en la version 1 de la aplicacion.',
        'Corregir las vulnerabilidades encontradas aplicando practicas de seguridad en la version 2.',
        'Implementar tests automatizados que verifiquen la seguridad de la aplicacion.',
        'Documentar el proceso de desarrollo seguro en un informe tecnico estructurado.',
    ]
    for obj in objectives:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(obj)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    doc.add_page_break()

    # === 1. DESCRIPCION DE LA APLICACION ===
    add_heading_apa(doc, '1. Descripcion de la Aplicacion', level=1)
    add_heading_apa(doc, '1.1 Stack Tecnologico', level=2)
    add_paragraph(doc,
        'La aplicacion fue desarrollada utilizando las siguientes tecnologias:',
        first_line_indent=Cm(1.27))

    # Tabla de stack
    table = doc.add_table(rows=7, cols=2)
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ['Componente', 'Tecnologia']
    data = [
        ('Backend', 'Python 3.12 + Flask 3.0.3'),
        ('Base de datos', 'SQLite'),
        ('Frontend', 'HTML5 + Bootstrap 5 + Jinja2'),
        ('Seguridad V2', 'bcrypt, python-dotenv'),
        ('Testing', 'pytest'),
        ('Control de versiones', 'Git (ramas main y v1-insegura)'),
    ]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(11)
                run.font.name = 'Times New Roman'
    for row_idx, (comp, tech) in enumerate(data, 1):
        table.rows[row_idx].cells[0].text = comp
        table.rows[row_idx].cells[1].text = tech
        for cell in table.rows[row_idx].cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(11)
                    run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    run = p.add_run('Tabla 1. Stack tecnologico de la aplicacion')
    run.font.size = Pt(10)
    run.italic = True
    run.font.name = 'Times New Roman'
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_heading_apa(doc, '1.2 Modelo de Datos', level=2)
    add_paragraph(doc,
        'La base de datos SQLite contiene cinco tablas principales:',
        first_line_indent=Cm(1.27))

    table2 = doc.add_table(rows=6, cols=3)
    table2.style = 'Light Grid Accent 1'
    table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(['Tabla', 'Campos Principales', 'Relacion']):
        cell = table2.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(10)
                run.font.name = 'Times New Roman'

    tables_data = [
        ('usuarios', 'id, username, password, rol', 'Autenticacion'),
        ('estudiantes', 'id, nombre, email, carrera', 'CRUD principal'),
        ('cursos', 'id, nombre, codigo, creditos', 'CRUD principal'),
        ('notas', 'id, estudiante_id, curso_id, nota, ciclo', 'FK a estudiantes y cursos'),
        ('archivos', 'id, nombre_original, nombre_guardado, ruta, subido_por', 'FK a usuarios'),
    ]
    for row_idx, (tbl, campos, rel) in enumerate(tables_data, 1):
        table2.rows[row_idx].cells[0].text = tbl
        table2.rows[row_idx].cells[1].text = campos
        table2.rows[row_idx].cells[2].text = rel
        for cell in table2.rows[row_idx].cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(10)
                    run.font.name = 'Times New Roman'

    add_heading_apa(doc, '1.3 Funcionalidades', level=2)
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

    doc.add_page_break()

    # === 2. VERSION 1: VULNERABILIDADES ===
    add_heading_apa(doc, '2. Version 1: Analisis de Vulnerabilidades', level=1)
    add_paragraph(doc,
        'La version 1 de la aplicacion fue construida deliberadamente con multiples '
        'vulnerabilidades de seguridad. A continuacion se analizan las cuatro vulnerabilidades '
        'principales identificadas.',
        first_line_indent=Cm(1.27))

    # 2.1 SQL Injection
    add_heading_apa(doc, '2.1 SQL Injection', level=2)
    add_paragraph(doc,
        'La vulnerabilidad de SQL Injection se presenta cuando los datos proporcionados por '
        'el usuario se concatenan directamente en las consultas SQL sin sanitizar. Esto permite '
        'a un atacante manipular la consulta para acceder, modificar o eliminar datos.',
        first_line_indent=Cm(1.27))

    add_paragraph(doc, 'Vulnerabilidad en la ruta de login (V1):', bold=True)
    add_code_block(doc,
        '# VULNERABILIDAD: SQL Injection via concatenacion de strings\n'
        'query = ("SELECT * FROM usuarios WHERE username=\'" + username\n'
        "          + \"' AND password='\" + password + \"'\")\n"
        'cursor.execute(query)',
        'app.py (V1)')

    add_paragraph(doc,
        'Con un payload como `admin\' OR \'1\'=\'1`, un atacante puede evadir la autenticacion '
        'y acceder al sistema sin credenciales validas. La misma vulnerabilidad se presenta '
        'en la busqueda de estudiantes y en todas las operaciones CRUD.',
        first_line_indent=Cm(1.27))

    # 2.2 Autenticacion Rota
    add_heading_apa(doc, '2.2 Autenticacion Rota', level=2)
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

    add_paragraph(doc,
        'Estas debilidades permiten ataques de fuerza bruta similares a los demostrados '
        'en la Unidad III del curso utilizando herramientas como Hydra, donde se explotan '
        'credenciales debiles o por defecto para obtener acceso no autorizado.',
        first_line_indent=Cm(1.27))

    # 2.3 XSS
    add_heading_apa(doc, '2.3 Cross-Site Scripting (XSS)', level=2)
    add_paragraph(doc,
        'El Cross-Site Scripting (XSS) es una vulnerabilidad que permite a un atacante '
        'inyectar codigo JavaScript malicioso en las paginas web vistas por otros usuarios. '
        'En la version 1, los campos de entrada como nombre de estudiante no estan sanitizados, '
        'permitiendo XSS almacenado.',
        first_line_indent=Cm(1.27))

    add_paragraph(doc,
        'Si un atacante ingresa un nombre como `<script>alert("XSS")</script>`, este se '
        'almacena en la base de datos y se renderiza directamente en el navegador de cualquier '
        'usuario que consulte la lista de estudiantes, ejecutando el codigo malicioso.',
        first_line_indent=Cm(1.27))

    # 2.4 Upload Inseguro
    add_heading_apa(doc, '2.4 Subida de Archivos Insegura', level=2)
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

    doc.add_page_break()

    # === 3. VERSION 2: SOLUCIONES ===
    add_heading_apa(doc, '3. Version 2: Soluciones con SecDevOps', level=1)
    add_paragraph(doc,
        'La version 2 corrige todas las vulnerabilidades identificadas en la version 1 '
        'e incorpora practicas de seguridad en todo el ciclo de desarrollo.',
        first_line_indent=Cm(1.27))

    # 3.1 SQL Injection fix
    add_heading_apa(doc, '3.1 Correccion de SQL Injection', level=2)
    add_paragraph(doc,
        'Todas las consultas SQL fueron modificadas para usar queries parametrizadas con '
        'el caracter `?` como marcador de posicion. Esto garantiza que los datos del usuario '
        'nunca se interpreten como parte de la consulta SQL.',
        first_line_indent=Cm(1.27))

    add_paragraph(doc, 'Codigo corregido (V2):', bold=True)
    add_code_block(doc,
        '# CORRECCION: Query parametrizada\n'
        "cursor.execute(\n"
        "    \"SELECT * FROM usuarios WHERE username = ?\",\n"
        "    (username,),\n"
        ")",
        'app.py (V2)')

    add_paragraph(doc,
        'Esta correccion se aplico en todas las rutas de la aplicacion: login, busqueda '
        'de estudiantes, creacion, actualizacion y eliminacion de registros.',
        first_line_indent=Cm(1.27))

    # 3.2 Auth fix
    add_heading_apa(doc, '3.2 Mejora de Autenticacion', level=2)
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

    # 3.3 XSS fix
    add_heading_apa(doc, '3.3 Prevencion de XSS', level=2)
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

    # 3.4 Upload fix
    add_heading_apa(doc, '3.4 Seguridad en Subida de Archivos', level=2)
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

    # 3.5 Medidas adicionales
    add_heading_apa(doc, '3.5 Medidas Adicionales', level=2)
    add_paragraph(doc,
        'Ademas de las correcciones a las cuatro vulnerabilidades principales, se implementaron '
        'las siguientes medidas de seguridad:',
        first_line_indent=Cm(1.27))

    additional = [
        'Schema de base de datos mejorado con constraints CHECK y UNIQUE.',
        'Foreign keys con ON DELETE CASCADE para mantener integridad referencial.',
        'Validacion de tipos de datos en el backend (int, float) antes de INSERT.',
        'Logging centralizado de eventos de seguridad en security.log.',
        'Eliminacion de archivos temporales de测试 durante tearDown.',
    ]
    for item in additional:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(item)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    # 3.6 Herramientas DevSecOps
    add_heading_apa(doc, '3.6 Herramientas DevSecOps', level=2)
    add_paragraph(doc,
        'Se integran las siguientes herramientas en el pipeline de desarrollo:',
        first_line_indent=Cm(1.27))

    tools_table = doc.add_table(rows=4, cols=3)
    tools_table.style = 'Light Grid Accent 1'
    tools_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(['Herramienta', 'Tipo', 'Funcion']):
        cell = tools_table.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(10)
                run.font.name = 'Times New Roman'

    tools_data = [
        ('Bandit', 'SAST', 'Analisis estatico de codigo Python para detectar vulnerabilidades'),
        ('Safety', 'SCA', 'Verificacion de dependencias contra vulnerabilidades conocidas'),
        ('pytest', 'Testing', 'Tests automatizados que verifican correcciones de seguridad'),
    ]
    for row_idx, (tool, tipo, func) in enumerate(tools_data, 1):
        tools_table.rows[row_idx].cells[0].text = tool
        tools_table.rows[row_idx].cells[1].text = tipo
        tools_table.rows[row_idx].cells[2].text = func
        for cell in tools_table.rows[row_idx].cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(10)
                    run.font.name = 'Times New Roman'

    doc.add_page_break()

    # === 4. COMPARATIVA ===
    add_heading_apa(doc, '4. Comparativa Version 1 vs Version 2', level=1)

    comp_table = doc.add_table(rows=9, cols=3)
    comp_table.style = 'Light Grid Accent 1'
    comp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(['Aspecto', 'Version 1 (Insegura)', 'Version 2 (Segura)']):
        cell = comp_table.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(10)
                run.font.name = 'Times New Roman'

    comp_data = [
        ('SQL Queries', 'Concatenacion de strings', 'Queries parametrizadas (?)'),
        ('Passwords', 'Texto plano', 'bcrypt hashing'),
        ('Secret Key', 'Hardcodeada ("12345")', 'Variable de entorno (.env)'),
        ('XSS', 'Sin sanitizacion', 'Auto-escaping Jinja2 + CSP'),
        ('File Upload', 'Sin validacion', 'Whitelist + UUID + validacion MIME'),
        ('Headers', 'Ninguno', 'CSP, HSTS, X-Frame-Options'),
        ('Debug Mode', 'Activado', 'Desactivado'),
        ('Tests', 'Ninguno', '8 tests automatizados'),
    ]
    for row_idx, (aspect, v1, v2) in enumerate(comp_data, 1):
        comp_table.rows[row_idx].cells[0].text = aspect
        comp_table.rows[row_idx].cells[1].text = v1
        comp_table.rows[row_idx].cells[2].text = v2
        for cell in comp_table.rows[row_idx].cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(10)
                    run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    run = p.add_run('Tabla 2. Comparativa de seguridad entre Version 1 y Version 2')
    run.font.size = Pt(10)
    run.italic = True
    run.font.name = 'Times New Roman'
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()

    # === CONCLUSIONES ===
    add_heading_apa(doc, 'Conclusiones', level=1)
    conclusions = [
        'La construccion deliberada de una aplicacion insegura permite comprender de manera '
        'practica como funcionan las vulnerabilidades mas comunes en aplicaciones web. La '
        'experiencia de ver SQL Injection, XSS y problemas de autenticacion en codigo real '
        'fortalece la comprension teorica adquirida en el curso.',
        'Las queries parametrizadas son la solucion efectiva y sencilla contra SQL Injection. '
        'Su implementacion no afecta el rendimiento de la aplicacion y elimina completamente '
        'esta categoria de vulnerabilidad.',
        'El hashing de passwords con algoritmos como bcrypt es fundamental para la proteccion '
        'de credenciales. A diferencia del texto plano, un hash con salt fuerza a los atacantes '
        'a realizar fuerza bruta sobre cada hash individualmente.',
        'La integracion de la seguridad en el ciclo de desarrollo (SecDevOps) es mas efectiva '
        'que tratar de agregar seguridad al final del desarrollo. Herramientas como Bandit '
        'y Safety permiten detectar problemas automaticamente.',
        'Los tests automatizados de seguridad son esenciales para verificar que las '
        'correcciones funcionan correctamente y para prevenir regresiones en futuras '
        'versiones del codigo.',
    ]
    for c in conclusions:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(c)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    doc.add_page_break()

    # === REFERENCIAS ===
    add_heading_apa(doc, 'Referencias', level=1)
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

    doc.save('Informe_Tecnico_Seguridad_Informatica.docx')
    print('Informe generado: Informe_Tecnico_Seguridad_Informatica.docx')


if __name__ == '__main__':
    create_report()
