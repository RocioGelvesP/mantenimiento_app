from functools import wraps
from flask import abort, flash, redirect, url_for, request, send_file, after_this_request, Blueprint
from flask_login import current_user
import   os
import platform
import pdfkit
from models import Auditoria, db
from datetime import datetime

# ============================================================================
# FUNCIONES PARA GENERACIÓN DE PDFS CON REPORTLAB
# ============================================================================

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Table, TableStyle, Paragraph, Image, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from io import BytesIO
import os
import calendar
import os

# 1. Clase NumberedCanvas para paginación 'Página X de Y'
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        super().showPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 8)
        self.drawRightString(
            self._pagesize[0] - 40,  # Ajusta el margen derecho si lo necesitas
            20,                      # Ajusta la altura si lo necesitas
            f"Página {self._pageNumber} de {page_count}"
        )

def get_pdf_config():
	sistema = platform.system()
	if sistema == 'Windows':
		path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
	elif sistema == 'Linux':
		# Buscar wkhtmltopdf en múltiples ubicaciones comunes
		possible_paths = [
			'/usr/bin/wkhtmltopdf',
			'/usr/local/bin/wkhtmltopdf',
			'/opt/wkhtmltopdf/bin/wkhtmltopdf'
		]
		
		path_wkhtmltopdf = None
		for path in possible_paths:
			if os.path.exists(path):
				path_wkhtmltopdf = path
				break
		
		# Si no se encuentra en las rutas comunes, intentar usar 'which'
		if path_wkhtmltopdf is None:
			import subprocess
			try:
				result = subprocess.run(['which', 'wkhtmltopdf'], 
									   capture_output=True, text=True, timeout=5)
				if result.returncode == 0:
					path_wkhtmltopdf = result.stdout.strip()
			except (subprocess.TimeoutExpired, FileNotFoundError):
				pass
		
		if path_wkhtmltopdf is None:
			raise FileNotFoundError(f"No se encontró wkhtmltopdf en ninguna ubicación conocida")
	else:
		raise OSError(f"Sistema no compatible: {sistema}")

	return pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

def get_pdf_options(orientation='Portrait', page_size='A4', include_footer=True, custom_footer=None):
	"""
	Obtiene opciones optimizadas para PDF con paginación.
	
	Args:
		orientation: 'Portrait' o 'Landscape'
		page_size: Tamaño de página (A4, Letter, etc.)
		include_footer: Si incluir pie de página con paginación
		custom_footer: Texto personalizado para el pie de página
	"""
	options = {
		'page-size': page_size,
		'orientation': orientation,
		'margin-top': '0.5in',
		'margin-right': '0.5in',
		'margin-bottom': '0.75in',  # Más espacio para el pie de página
		'margin-left': '0.5in',
		'encoding': 'UTF-8',
		'no-outline': None,
		'enable-local-file-access': None,
		'disable-smart-shrinking': None,
		'print-media-type': None,
		'no-stop-slow-scripts': None,
		'javascript-delay': '1000',
		'load-error-handling': 'ignore',
		'load-media-error-handling': 'ignore'
	}
	
	if include_footer:
		if custom_footer:
			options['footer-center'] = custom_footer
		else:
			options['footer-center'] = 'Página [page] de [topage]'
		options['footer-font-size'] = '10'
		options['footer-spacing'] = '5'
		options['footer-line'] = None  # Línea separadora
	
	return options

def require_role(role):
    """
    Decorador para requerir un rol específico.
    Uso: @require_role('admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if not current_user.has_role(role):
                flash('No tienes permisos para acceder a esta función.', 'error')
                return redirect(url_for('home_bp.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_any_role(*roles):
    """
    Decorador para requerir cualquiera de los roles especificados.
    Uso: @require_any_role('admin', 'supervisor')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if not any(current_user.has_role(role) for role in roles):
                flash('No tienes permisos para acceder a esta función.', 'error')
                return redirect(url_for('home_bp.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_delete_permission():
    """
    Decorador para requerir permisos de eliminación (solo super_admin).
    Uso: @require_delete_permission()
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if not current_user.can_delete():
                flash('No tienes permisos para eliminar registros. Solo el Super Administrador puede realizar esta acción.', 'error')
                return redirect(url_for('home_bp.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def can_edit_mantenimiento(user, mantenimiento):
    """
    Verifica si el usuario actual puede editar un mantenimiento específico.
    Los técnicos solo pueden editar mantenimientos asignados a ellos.
    """
    if not user.is_authenticated:
        return False
    
    # Super admin, admin y supervisor pueden editar todos los mantenimientos
    if user.is_super_admin() or user.is_admin() or user.is_supervisor():
        return True
    
    # Técnicos solo pueden editar mantenimientos asignados a ellos
    if user.is_tecnico():
        return (mantenimiento.tecnico_asignado == user.username or 
                mantenimiento.tecnico_realizador == user.username)
    
    return False

def can_view_mantenimiento(user, mantenimiento):
    """
    Verifica si el usuario actual puede ver un mantenimiento específico.
    Los técnicos solo pueden ver mantenimientos asignados a ellos.
    """
    if not user.is_authenticated:
        return False
    
    # Super admin, admin y supervisor pueden ver todos los mantenimientos
    if user.is_super_admin() or user.is_admin() or user.is_supervisor():
        return True
    
    # Técnicos solo pueden ver mantenimientos asignados a ellos
    if user.is_tecnico():
        return (mantenimiento.tecnico_asignado == user.username or 
                mantenimiento.tecnico_realizador == user.username)
    
    return False

def get_mantenimientos_filtrados_por_rol():
    """
    Retorna una consulta filtrada de mantenimientos según el rol del usuario.
    """
    from models import Programado
    
    if current_user.is_super_admin() or current_user.is_admin() or current_user.is_supervisor():
        # Super admin, admin y supervisor ven todos los mantenimientos
        return Programado.query
    
    elif current_user.is_tecnico():
        # Técnicos solo ven mantenimientos asignados a ellos
        return Programado.query.filter(
            (Programado.tecnico_asignado == current_user.username) |
            (Programado.tecnico_realizador == current_user.username)
        )
    
    else:
        # Usuarios regulares no ven ningún mantenimiento
        return Programado.query.filter(Programado.id == 0)  # Query vacía

def get_usuarios_filtrados_por_rol():
    """
    Retorna una lista de usuarios según el rol del usuario actual.
    """
    from models import User
    
    if current_user.is_super_admin():
        # Super admin ve todos los usuarios
        return User.query.all()
    
    elif current_user.is_admin():
        # Admin ve todos los usuarios excepto super_admin
        return User.query.filter(User.role != 'super_admin').all()
    
    elif current_user.is_supervisor():
        # Supervisor ve técnicos y usuarios regulares
        return User.query.filter(User.role.in_(['tecnico', 'user'])).all()
    
    else:
        # Técnicos y usuarios regulares no ven otros usuarios
        return []

def get_equipos_filtrados_por_rol():
    """
    Retorna una consulta filtrada de equipos según el rol del usuario.
    """
    from models import Equipo
    
    if current_user.is_super_admin() or current_user.is_admin() or current_user.is_supervisor():
        # Super admin, admin y supervisor ven todos los equipos
        return Equipo.query
    
    elif current_user.is_tecnico():
        # Técnicos ven equipos que tienen mantenimientos asignados a ellos
        from models import Programado
        mantenimientos_asignados = Programado.query.filter(
            (Programado.tecnico_asignado == current_user.username) |
            (Programado.tecnico_realizador == current_user.username)
        ).with_entities(Programado.codigo).distinct()
        
        codigos_equipos = [m.codigo for m in mantenimientos_asignados]
        return Equipo.query.filter(Equipo.codigo.in_(codigos_equipos))
    
    else:
        # Usuarios regulares no ven equipos
        return Equipo.query.filter(Equipo.codigo == '')  # Query vacía 

def registrar_auditoria(modulo, accion, tabla=None, descripcion='', datos_anteriores=None, datos_nuevos=None):
    auditoria = Auditoria(
        usuario=getattr(current_user, 'username', 'anónimo'),
        fecha=datetime.utcnow(),
        ip=request.remote_addr,
        modulo=modulo,
        accion=accion,
        tabla=tabla,
        descripcion=descripcion,
        datos_anteriores=str(datos_anteriores) if datos_anteriores else None,
        datos_nuevos=str(datos_nuevos) if datos_nuevos else None
    )
    db.session.add(auditoria)
    db.session.commit() 

def add_footer(canvas, doc):
    """
    Función para agregar pie de página con paginación "Página X de Y".
    """
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    # Dibujar la paginación centrada
    canvas.drawCentredString(
        doc.pagesize[0] / 2,  # Centro de la página
        doc.bottomMargin / 2,  # Cerca del borde inferior
        f"Página {canvas._pageNumber}"
    )
    canvas.restoreState()

def draw_encabezado(canvas, doc):
    canvas.saveState()
    x = doc.leftMargin
    y = doc.pagesize[1] - doc.topMargin
    height = 55  # Igual que encabezado_height
    # Anchos personalizados para el encabezado (4 columnas que ocupan todo el ancho)
    col_widths_header = [doc.width*0.15, doc.width*0.35, doc.width*0.40, doc.width*0.10]  # Código/edición pequeña
    # Dibuja el borde exterior
    canvas.rect(x, y - height, sum(col_widths_header), height)
    # Líneas verticales
    for i in range(1, 4):
        canvas.line(x + sum(col_widths_header[:i]), y - height, x + sum(col_widths_header[:i]), y)
    # --- Contenido de cada bloque ---
    # 1. Logo (columna 1)
    logo_path = os.path.join(os.getcwd(), 'static', 'logo.png')
    if os.path.exists(logo_path):
        logo_w, logo_h = 55, 35
        logo_x = x + (col_widths_header[0] / 2) - (logo_w / 2)
        logo_y = y - (height / 2) - (logo_h / 2)
        canvas.drawImage(logo_path, logo_x, logo_y, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
    # 2. Empresa (columna 2)
    canvas.setFont('Helvetica-Bold', 12)
    center_x = x + sum(col_widths_header[:1]) + col_widths_header[1] / 2
    center_y = y - height / 2
    canvas.drawCentredString(center_x, center_y + 6, "INR INVERSIONES")
    canvas.drawCentredString(center_x, center_y - 8, "REINOSO Y CIA. LTDA.")
    # 3. Título (columna 3)
    canvas.setFont('Helvetica-Bold', 10)
    center_x2 = x + sum(col_widths_header[:2]) + col_widths_header[2] / 2
    canvas.drawCentredString(center_x2, center_y, "HOJA DE VIDA")
    # 4. Código/Edición (columna 4) - ahora es la última columna
    cuadro_x = x + sum(col_widths_header[:3])
    cuadro_w = col_widths_header[3]
    row_h = height / 4
    for i, (txt, font) in enumerate([
        ("Código", 'Helvetica-Bold'),
        ("71-MT-72", 'Helvetica'),
        ("Edición", 'Helvetica-Bold'),
        ("17/Jul/2025", 'Helvetica')
    ]):
        canvas.setFont(font, 8)
        center_x4 = cuadro_x + cuadro_w / 2
        sub_top = y - i * row_h
        sub_bot = y - (i + 1) * row_h
        center_y4 = (sub_top + sub_bot) / 2 - 2
        canvas.drawCentredString(center_x4, center_y4, txt)
    # Líneas horizontales internas del bloque derecho
    for i in range(1, 4):
        canvas.line(cuadro_x, y - i * row_h, cuadro_x + cuadro_w, y - i * row_h)
    # NO dibujar paginación aquí
    canvas.restoreState()

def draw_encabezado_ficha_tecnica(canvas, doc):
    canvas.saveState()
    x = doc.leftMargin
    y = doc.pagesize[1] - doc.topMargin
    height = 55

    # Anchos de las 4 columnas (ajustados según la imagen)
    # Primera y cuarta más estrechas, segunda y tercera más anchas
    col_widths = [doc.width*0.15, doc.width*0.35, doc.width*0.35, doc.width*0.15]

    # Dibuja el borde exterior
    canvas.rect(x, y - height, doc.width, height)

    # Líneas verticales separadoras (3 líneas para 4 columnas)
    current_x = x
    for i in range(3):
        current_x += col_widths[i]
        canvas.line(current_x, y - height, current_x, y)

    # Columna 1: Logo
    logo_path = os.path.join(os.getcwd(), 'static', 'logo.png')
    if os.path.exists(logo_path):
        logo_x = x + (col_widths[0] / 2) - 25
        logo_y = y - height/2 - 20
        canvas.drawImage(logo_path, logo_x, logo_y, width=50, height=40, mask='auto')

    # Columna 2: Texto de empresa
    canvas.setFont('Helvetica-Bold', 12)
    center_x2 = x + col_widths[0] + col_widths[1]/2
    center_y = y - height/2
    canvas.drawCentredString(center_x2, center_y + 5, "INR INVERSIONES")
    canvas.drawCentredString(center_x2, center_y - 5, "REINOSO Y CIA. LTDA.")

    # Columna 3: Título principal
    canvas.setFont('Helvetica-Bold', 10)
    center_x3 = x + col_widths[0] + col_widths[1] + col_widths[2]/2
    canvas.drawCentredString(center_x3, center_y, "FICHA TÉCNICA DE EQUIPOS")

    # Columna 4: Código y Edición (dividido en 4 espacios verticales)
    cuadro_x = x + col_widths[0] + col_widths[1] + col_widths[2]
    cuadro_w = col_widths[3]
    row_h = height / 4  # 4 filas
    
    # Líneas horizontales internas del bloque derecho
    for i in range(1, 4):
        canvas.line(cuadro_x, y - i * row_h, cuadro_x + cuadro_w, y - i * row_h)
    
    # Contenido del bloque derecho - centrado horizontal y vertical
    center_x4 = cuadro_x + cuadro_w / 2
    
    # Fila 1: "Código"
    canvas.setFont('Helvetica-Bold', 8)
    canvas.drawCentredString(center_x4, y - row_h/2 - 5, "Código")
    
    # Fila 2: "71-MT-56"
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(center_x4, y - row_h - row_h/2 - 5, "71-MT-56")
    
    # Fila 3: "Edición"
    canvas.setFont('Helvetica-Bold', 8)
    canvas.drawCentredString(center_x4, y - 2*row_h - row_h/2 - 5, "Edición")
    
    # Fila 4: "5/Jul/2025"
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(center_x4, y - 3*row_h - row_h/2 - 5, "5/Jul/2025")

    canvas.restoreState()

# Utilidad para reemplazar el marcador por el total real de páginas
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas as rl_canvas
from io import BytesIO

def agregar_total_paginas(input_pdf_path, output_pdf_path, pagesize):
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas as rl_canvas
    from io import BytesIO

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    total = len(reader.pages)
    for i, page in enumerate(reader.pages, 1):
        packet = BytesIO()
        can = rl_canvas.Canvas(packet, pagesize=pagesize)
        # --- DIBUJAR ENCABEZADO ---
        # Simular un objeto doc para pasar a draw_encabezado
        class DummyDoc:
            def __init__(self, pagesize):
                self.pagesize = pagesize
                self.leftMargin = 10 * mm
                self.rightMargin = 10 * mm
                self.topMargin = 20 * mm
                self.bottomMargin = 30 * mm
                self.width = pagesize[0] - self.leftMargin - self.rightMargin
                self.height = pagesize[1] - self.topMargin - self.bottomMargin
        dummy_doc = DummyDoc(pagesize)
        draw_encabezado(can, dummy_doc)
        # --- DIBUJAR PAGINACIÓN ---
        try:
            can.setFont("DejaVuSans-Bold", 10)
        except:
            can.setFont("Helvetica-Bold", 10)
        can.drawCentredString(
            pagesize[0] / 2,  # Centro de la página
            30,               # Más cerca del borde inferior
            f"Página {i} de {total}"
        )
        can.save()
        packet.seek(0)
        from PyPDF2 import PdfReader as RLReader
        overlay = RLReader(packet)
        page.merge_page(overlay.pages[0])
        writer.add_page(page)
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

# USO:
# 1. Genera el PDF con el marcador (por ejemplo, usando BytesIO y guardando en un archivo temporal)
# 2. Llama a agregar_total_paginas para crear el PDF final con la paginación correcta


# --- LISTA DE MANTENIMIENTOS ---
def create_reportlab_pdf_maintenance_report(mantenimientos, title="Control de Actividades de Mantenimiento", orientation='landscape', include_footer=True):
    buffer = BytesIO()
    if orientation == 'landscape':
        pagesize = landscape(A4)
    else:
        pagesize = A4
    doc = SimpleDocTemplate(buffer, pagesize=pagesize, rightMargin=10*mm, leftMargin=10*mm, topMargin=20*mm, bottomMargin=30*mm)
    styles = getSampleStyleSheet()
    elements = []
    headers = ['N°', 'Fec./Hor. Inic.', 'Fec./Hor. Fin', 'Código', 'Ubicación', 'Tipo', 'Técnico', 'Actividad', 'Observaciones', 'Recibido por']
    data = [headers]
    for i, mtto in enumerate(mantenimientos, 1):
        row = [
            str(i),
            Paragraph(str(mtto.hora_inicial) if mtto.hora_inicial else '', ParagraphStyle('fecha_ini', fontSize=8, alignment=TA_CENTER, leading=10)),
            Paragraph(str(mtto.hora_final) if mtto.hora_final else '', ParagraphStyle('fecha_fin', fontSize=8, alignment=TA_CENTER, leading=10)),
            str(mtto.codigo) if mtto.codigo else '',
            str(mtto.ubicacion) if mtto.ubicacion else '',
            str(mtto.tipo_mantenimiento) if mtto.tipo_mantenimiento else '',
            str(mtto.tecnico_asignado_display) if hasattr(mtto, 'tecnico_asignado_display') and mtto.tecnico_asignado_display else '',
            Paragraph(str(mtto.servicio) if mtto.servicio else '', ParagraphStyle('actividad', fontSize=8, alignment=TA_LEFT, leading=10)),
            Paragraph(str(mtto.observaciones) if mtto.observaciones else '', ParagraphStyle('obs', fontSize=8, alignment=TA_LEFT, leading=10)),
            str(mtto.recibido_por) if mtto.recibido_por else ''
        ]
        data.append(row)
    col_widths = [24, 68, 68, 50, 104, 52, 67, 125, 120, 80]
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('ALIGN', (0, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (6, -1), 'CENTER'),
        ('ALIGN', (7, 1), (7, -1), 'LEFT'),
        ('ALIGN', (8, 1), (8, -1), 'LEFT'),
        ('ALIGN', (9, 1), (9, -1), 'CENTER'),
    ])
    table.setStyle(table_style)
    elements.append(table)
    from reportlab.platypus import PageTemplate, Frame
    encabezado_height = 55
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - encabezado_height, id='normal')
    doc.addPageTemplates([PageTemplate(id='all', frames=frame, onPage=encabezado_y_footer)])
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- DETALLE DE MANTENIMIENTO ---
def create_reportlab_pdf_maintenance_detail(mantenimiento, title="Control de Actividades de Mantenimiento"):
    buffer = BytesIO()
    pagesize = landscape(A4)
    doc = SimpleDocTemplate(buffer, pagesize=pagesize, rightMargin=10*mm, leftMargin=10*mm, topMargin=20*mm, bottomMargin=30*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Bold')
    elements = []
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))
    info_data = [
        ['Campo', 'Valor'],
        ['ID', str(mantenimiento.id)],
        ['Código', str(mantenimiento.codigo) if mantenimiento.codigo else ''],
        ['Nombre', str(mantenimiento.nombre) if mantenimiento.nombre else ''],
        ['Fecha Programada', mantenimiento.fecha_prog.strftime('%d/%m/%Y') if mantenimiento.fecha_prog else ''],
        ['Hora', str(mantenimiento.hora) if mantenimiento.hora else ''],
        ['Servicio', str(mantenimiento.servicio) if mantenimiento.servicio else ''],
        ['Tipo Mantenimiento', str(mantenimiento.tipo_mantenimiento) if mantenimiento.tipo_mantenimiento else ''],
        ['Estado', str(mantenimiento.estado_inicial) if mantenimiento.estado_inicial else ''],
        ['Técnico Asignado', str(mantenimiento.tecnico_asignado_display) if hasattr(mantenimiento, 'tecnico_asignado_display') and mantenimiento.tecnico_asignado_display else ''],
        ['Ubicación', str(mantenimiento.ubicacion) if mantenimiento.ubicacion else ''],
        ['Observaciones', str(mantenimiento.observaciones) if mantenimiento.observaciones else '']
    ]
    info_table = Table(info_data, repeatRows=1)
    info_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
    ])
    info_table.setStyle(info_style)
    elements.append(info_table)
    from reportlab.platypus import PageTemplate, Frame
    encabezado_height = 55
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - encabezado_height, id='normal')
    doc.addPageTemplates([PageTemplate(id='all', frames=frame, onPage=encabezado_y_footer)])
    doc.build(elements)
    buffer.seek(0)
    return buffer 

# --- HISTORIAL DE CAMBIOS ---
def create_reportlab_pdf_historial(historial, mantenimiento_id, title="Historial de Cambios del Mantenimiento"):
    buffer = BytesIO()
    pagesize = landscape(A4)
    doc = SimpleDocTemplate(buffer, pagesize=pagesize, rightMargin=10*mm, leftMargin=10*mm, topMargin=20*mm, bottomMargin=30*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Bold')
    elements = []
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))
    if historial and historial[0].mantenimiento:
        info_text = f"Código: {historial[0].mantenimiento.codigo}<br/>Nombre: {historial[0].mantenimiento.nombre}"
        info_para = Paragraph(info_text, styles['Normal'])
        elements.append(info_para)
        elements.append(Spacer(1, 10))
    headers = ['Fecha', 'Usuario', 'Campo', 'Valor Anterior', 'Valor Nuevo', 'Acción']
    data = [headers]
    for h in historial:
        row = [
            h.fecha.strftime('%d/%m/%Y %H:%M') if h.fecha else '',
            str(h.usuario) if h.usuario else '',
            str(h.campo) if h.campo else '',
            str(h.valor_anterior) if h.valor_anterior else '',
            str(h.valor_nuevo) if h.valor_nuevo else '',
            str(h.accion) if h.accion else ''
        ]
        data.append(row)
    if data:
        table = Table(data, repeatRows=1)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ])
        table.setStyle(table_style)
        elements.append(table)
    from reportlab.platypus import PageTemplate, Frame
    encabezado_height = 55
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - encabezado_height, id='normal')
    doc.addPageTemplates([PageTemplate(id='all', frames=frame, onPage=encabezado_y_footer)])
    doc.build(elements)
    buffer.seek(0)
    return buffer 

# --- HOJA DE VIDA DE EQUIPO ---
def create_reportlab_pdf_equipment_life_sheet(equipo, mantenimientos, title="Hoja de Vida de Equipos"):
    buffer = BytesIO()
    pagesize = landscape(A4)
    doc = SimpleDocTemplate(buffer, pagesize=pagesize, rightMargin=10*mm, leftMargin=10*mm, topMargin=20*mm, bottomMargin=30*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Bold')
    elements = []
    # Quitar el título principal ya que está en el encabezado
    # elements.append(Paragraph(title, title_style))
    # elements.append(Spacer(1, 10))
    
    # Sección de información del equipo con imagen
    info_section = []
    
    # Imagen del equipo (lado izquierdo)
    if equipo.imagen:
        try:
            if equipo.imagen.startswith('uploads/'):
                imagen_path = os.path.join(os.getcwd(), 'static', equipo.imagen)
            else:
                imagen_path = os.path.join(os.getcwd(), 'static', 'uploads', equipo.imagen)
            
            if os.path.exists(imagen_path):
                img = Image(imagen_path)
                img._restrictSize(120, 120)  # Tamaño fijo para la imagen
                info_section.append(img)
            else:
                # Placeholder si no hay imagen
                info_section.append(Paragraph("Sin imagen", styles['Normal']))
        except Exception as e:
            info_section.append(Paragraph("Error al cargar imagen", styles['Normal']))
    else:
        info_section.append(Paragraph("Sin imagen", styles['Normal']))
    
    # Información del equipo (lado derecho) - organizada en 3 columnas con texto flexible
    equipo_info = [
        [
            Paragraph('Código:', ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=9, alignment=TA_LEFT)),
            Paragraph(str(equipo.codigo) if equipo.codigo else '', ParagraphStyle('value', fontName='Helvetica', fontSize=9, alignment=TA_LEFT)),
            Paragraph('Marca:', ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=9, alignment=TA_LEFT)),
            Paragraph(str(equipo.marca) if equipo.marca else '', ParagraphStyle('value', fontName='Helvetica', fontSize=9, alignment=TA_LEFT)),
            Paragraph('Serie:', ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=9, alignment=TA_LEFT)),
            Paragraph(str(equipo.serie) if equipo.serie else '', ParagraphStyle('value', fontName='Helvetica', fontSize=9, alignment=TA_LEFT))
        ],
        [
            Paragraph('Nombre:', ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=9, alignment=TA_LEFT)),
            Paragraph(str(equipo.nombre) if equipo.nombre else '', ParagraphStyle('value', fontName='Helvetica', fontSize=9, alignment=TA_LEFT)),
            Paragraph('Modelo:', ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=9, alignment=TA_LEFT)),
            Paragraph(str(equipo.modelo) if equipo.modelo else '', ParagraphStyle('value', fontName='Helvetica', fontSize=9, alignment=TA_LEFT)),
            Paragraph('Estado:', ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=9, alignment=TA_LEFT)),
            Paragraph(str(equipo.estado_eq) if equipo.estado_eq else '', ParagraphStyle('value', fontName='Helvetica', fontSize=9, alignment=TA_LEFT))
        ],
        [
            Paragraph('Ubicación:', ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=9, alignment=TA_LEFT)),
            Paragraph(str(equipo.ubicacion) if equipo.ubicacion else '', ParagraphStyle('value', fontName='Helvetica', fontSize=9, alignment=TA_LEFT)),
            Paragraph('Fecha Ingreso:', ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=9, alignment=TA_LEFT)),
            Paragraph(equipo.fecha_ingreso.strftime('%d/%m/%Y') if equipo.fecha_ingreso else '', ParagraphStyle('value', fontName='Helvetica', fontSize=9, alignment=TA_LEFT)),
            '', ''
        ]
    ]
    info_table = Table(equipo_info, colWidths=[70, 150, 80, 120, 80, 120])
    info_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        # Sin bordes para un formato más limpio
        ('GRID', (0, 0), (-1, -1), 0, colors.white),
    ])
    info_table.setStyle(info_style)
    # Crear tabla principal: imagen (columna 1) + info_table (columna 2)
    main_layout = Table([[info_section[0], info_table]], colWidths=[150, 570])
    main_layout.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),   # Imagen alineada a la izquierda
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),   # Info a la izquierda
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),  # Sin padding izquierdo en la imagen
        ('RIGHTPADDING', (0, 0), (0, 0), 0), # Sin padding derecho en la imagen
        ('LEFTPADDING', (1, 0), (1, 0), 15), # Padding izquierdo en la info
        ('RIGHTPADDING', (1, 0), (1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        # Sin bordes para un formato más limpio
        ('GRID', (0, 0), (-1, -1), 0, colors.white),
    ]))
    elements.append(main_layout)
    elements.append(Spacer(1, 15))
    
    # Sección de mantenimientos realizados
    if mantenimientos:
        # Crear título con fondo gris claro
        title_with_bg = Paragraph(
            "Mantenimientos Realizados",
            ParagraphStyle(
                'TitleWithBackground',
                parent=title_style,
                fontSize=12,  # Reducir el tamaño de la fuente
                alignment=TA_CENTER,  # Centrar el texto
                backColor=colors.lightgrey,
                leftIndent=0,
                rightIndent=0,
                spaceBefore=0,
                spaceAfter=0,
                paddingTop=8,
                paddingBottom=8,
                paddingLeft=10,
                paddingRight=10
            )
        )
        # Crear tabla de una sola celda para que ocupe todo el ancho
        title_table = Table([[title_with_bg]], colWidths=[doc.width])
        title_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 0),
            ('TOPPADDING', (0, 0), (0, 0), 0),
            ('BOTTOMPADDING', (0, 0), (0, 0), 0),
            ('GRID', (0, 0), (0, 0), 0, colors.white),  # Sin bordes
        ]))
        elements.append(title_table)
        elements.append(Spacer(1, 10))
        
        # Tabla de mantenimientos más compacta
        headers = ['Fech./Hor. Inic.', 'Fec./Hor. Fin', 'Tiempo', 'Tipo', 'Actividad', 'Técnico', 'Repuestos', 'Herramientas', 'Observaciones', 'C. Rep.', 'C. Herr.', 'C. MDO', 'Costo Total']
        data = [headers]
        
        # Calcular totales
        total_costo_rep = 0
        total_costo_herram = 0
        total_costo_mdo = 0
        total_general = 0
        
        for mtto in mantenimientos:
            costo_total = (mtto.costo_rep or 0) + (mtto.costo_herram or 0) + (mtto.costo_mdo or 0)
            total_costo_rep += mtto.costo_rep or 0
            total_costo_herram += mtto.costo_herram or 0
            total_costo_mdo += mtto.costo_mdo or 0
            total_general += costo_total
            
            row = [
                Paragraph(mtto.hora_inicial.strftime('%d/%m/%Y %H:%M') if mtto.hora_inicial else '', ParagraphStyle('fecha', fontSize=7, leading=9)),
                Paragraph(mtto.hora_final.strftime('%d/%m/%Y %H:%M') if mtto.hora_final else '', ParagraphStyle('fecha', fontSize=7, leading=9)),
                str(mtto.tiempo_gastado) if mtto.tiempo_gastado else '',
                str(mtto.tipo_mantenimiento) if mtto.tipo_mantenimiento else '',
                Paragraph(str(mtto.servicio) if mtto.servicio else '', ParagraphStyle('servicio', fontSize=7, leading=9)),
                str(mtto.tecnico_realizador or mtto.tecnico_asignado) if mtto.tecnico_realizador or mtto.tecnico_asignado else '',
                str(mtto.repuestos) if mtto.repuestos else '',
                str(mtto.herramientas) if mtto.herramientas else '',
                Paragraph(str(mtto.observaciones) if mtto.observaciones else '', ParagraphStyle('obs', fontSize=7, leading=9)),
                f"${mtto.costo_rep:,.2f}" if mtto.costo_rep else '$0.00',
                f"${mtto.costo_herram:,.2f}" if mtto.costo_herram else '$0.00',
                f"${mtto.costo_mdo:,.2f}" if mtto.costo_mdo else '$0.00',
                f"${costo_total:,.2f}"
            ]
            data.append(row)
        
        # Agregar fila de totales
        totales_row = ['', '', '', '', '', 'Totales:', '', '', '', 
                      f"${total_costo_rep:,.2f}", f"${total_costo_herram:,.2f}", 
                      f"${total_costo_mdo:,.2f}", f"${total_general:,.2f}"]
        data.append(totales_row)
        
        maint_table = Table(data, repeatRows=1, hAlign='LEFT')
        maint_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),  # Filas de datos
            ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
            # Centrar columnas específicas (0, 1, 2, 3, 5)
            ('ALIGN', (0, 1), (0, -2), 'CENTER'),   # Columna 1: Fech./Hor. Inic.
            ('ALIGN', (1, 1), (1, -2), 'CENTER'),   # Columna 2: Fec./Hor. Fin
            ('ALIGN', (2, 1), (2, -2), 'CENTER'), # Columna 3: Tiempo
            ('ALIGN', (3, 1), (3, -2), 'CENTER'), # Columna 4: Tipo
            ('ALIGN', (5, 1), (5, -2), 'CENTER'), # Columna 6: Técnico
            # Alinear columnas de costos a la derecha
            ('ALIGN', (9, 1), (9, -2), 'RIGHT'),   # Columna 9: C. Rep.
            ('ALIGN', (10, 1), (10, -2), 'RIGHT'), # Columna 10: C. Herr.
            ('ALIGN', (11, 1), (11, -2), 'RIGHT'), # Columna 11: C. MDO
            ('ALIGN', (12, 1), (12, -2), 'RIGHT'), # Columna 12: Costo Total
            # Fila de totales - alineación específica
            ('BACKGROUND', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 9),
            ('ALIGN', (0, -1), (5, -1), 'LEFT'),    # Columnas 0-5 alineadas a la izquierda
            ('ALIGN', (9, -1), (12, -1), 'RIGHT'),  # Columnas de costos (9-12) alineadas a la derecha
        ])
        maint_table.setStyle(maint_style)
        elements.append(maint_table)
        elements.append(Spacer(1, 15))
        
        # Sección de estadísticas
        # Crear título con fondo gris claro (igual que mantenimientos)
        stats_title_with_bg = Paragraph(
            "Estadísticas",
            ParagraphStyle(
                'StatsTitleWithBackground',
                parent=title_style,
                fontSize=12,  # Reducir el tamaño de la fuente
                alignment=TA_CENTER,  # Centrar el texto
                backColor=colors.lightgrey,
                leftIndent=0,
                rightIndent=0,
                spaceBefore=0,
                spaceAfter=0,
                paddingTop=8,
                paddingBottom=8,
                paddingLeft=10,
                paddingRight=10
            )
        )
        # Crear tabla de una sola celda para que ocupe todo el ancho
        stats_title_table = Table([[stats_title_with_bg]], colWidths=[doc.width])
        stats_title_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 0),
            ('TOPPADDING', (0, 0), (0, 0), 0),
            ('BOTTOMPADDING', (0, 0), (0, 0), 0),
            ('GRID', (0, 0), (0, 0), 0, colors.white),  # Sin bordes
        ]))
        elements.append(stats_title_table)
        elements.append(Spacer(1, 10))
        
        # Calcular estadísticas
        total_programados = len(mantenimientos)
        total_completados = len([m for m in mantenimientos if m.hora_final])
        total_pendientes = total_programados - total_completados
        porcentaje_completado = (total_completados / total_programados * 100) if total_programados > 0 else 0
        
        stats_data = [
            ['Total Mttos Prog.', 'Total Pendientes', 'Total Completados', 'Prog. Vs Comp.'],
            [str(total_programados), str(total_pendientes), str(total_completados), f"{porcentaje_completado:.0f}%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[doc.width/4, doc.width/4, doc.width/4, doc.width/4])
        stats_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.7, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ])
        stats_table.setStyle(stats_style)
        elements.append(stats_table)
    else:
        elements.append(Paragraph("No hay mantenimientos realizados registrados.", styles['Normal']))
    
    from reportlab.platypus import PageTemplate, Frame
    encabezado_height = 55
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - encabezado_height, id='normal')
    doc.addPageTemplates([PageTemplate(id='all', frames=frame, onPage=encabezado_y_footer)])
    doc.build(elements)
    buffer.seek(0)
    return buffer

def create_reportlab_pdf_equipment_technical_sheet(equipo, motores, title="FICHA TÉCNICA DE EQUIPOS"):
    """
    Crea un PDF de ficha técnica de equipo usando ReportLab con el formato específico.
    
    Args:
        equipo: Objeto Equipo
        motores: Lista de objetos MotorEquipo
        title: Título del reporte
    
    Returns:
        BytesIO object con el PDF
    """
    buffer = BytesIO()
    pagesize = A4  # Portrait para ficha técnica
    
    doc = SimpleDocTemplate(buffer, pagesize=pagesize, 
                           rightMargin=10*mm, leftMargin=10*mm,
                           topMargin=15*mm, bottomMargin=30*mm)
    
    styles = getSampleStyleSheet()
    
    # Estilo para títulos de sección con barra gris
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=11,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        textColor=colors.white,
        backColor=colors.grey,
        leftIndent=0,
        rightIndent=0,
        spaceBefore=4
    )
    
    elements = []
    
    # Sección de identificación - Registro Nuevo y Actualización
    registro_text = f"Registro Nuevo {'Sí' if equipo.registro_nuevo else 'No'}"
    actualizacion_text = f"Actualización {'Sí' if equipo.actualizacion else 'No'}"
    
    # Crear tabla con dos columnas para alinear el texto
    ident_text_data = [[registro_text, actualizacion_text]]
    ident_text_table = Table(ident_text_data, colWidths=[200, 200])
    ident_text_style = TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Registro Nuevo a la izquierda
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'), # Actualización a la derecha
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('GRID', (0, 0), (-1, -1), 0, colors.white),  # Sin bordes
    ])
    ident_text_table.setStyle(ident_text_style)
    elements.append(ident_text_table)
    elements.append(Spacer(1, 5))
    
    # Tabla de Código y Nombre del Equipo
    equipo_data = [
        ['Código Equipo', 'Nombre Equipo'],
        [str(equipo.codigo) if equipo.codigo else '', str(equipo.nombre) if equipo.nombre else '']
    ]
    
    # Calcular el ancho total para que coincida con el encabezado
    total_width = doc.width
    equipo_table = Table(equipo_data, colWidths=[total_width/2, total_width/2])
    equipo_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Primera fila completa (encabezados) en negrita
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),      # Segunda fila (valores) normal
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    
    equipo_table.setStyle(equipo_style)
    elements.append(equipo_table)
    elements.append(Spacer(1, 10))
    
    # Imagen del equipo - Usar el campo imagen del equipo
    if equipo.imagen:
        try:
            # Construir la ruta correcta para la imagen
            if equipo.imagen.startswith('uploads/'):
                imagen_path = os.path.join(os.getcwd(), 'static', equipo.imagen)
            else:
                imagen_path = os.path.join(os.getcwd(), 'static', 'uploads', equipo.imagen)
            print(f"Buscando imagen en: {imagen_path}")
            if os.path.exists(imagen_path):
                print(f"✅ Imagen encontrada: {imagen_path}")
                # Crear la imagen con ancho máximo igual al de la tabla (doc.width)
                max_width = doc.width
                max_height = 180  # Altura máxima sugerida
                img = Image(imagen_path)
                img._restrictSize(max_width, max_height)
                img.hAlign = 'CENTER'
                # Crear tabla de una celda para centrar la imagen y que ocupe todo el ancho
                img_table = Table([[img]], colWidths=[max_width])
                img_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(img_table)
                elements.append(Spacer(1, 5))
            else:
                print(f"❌ No se encontró la imagen en: {imagen_path}")
                static_uploads = os.path.join(os.getcwd(), 'static', 'uploads')
                if os.path.exists(static_uploads):
                    archivos = os.listdir(static_uploads)
                    archivos_similares = [f for f in archivos if equipo.codigo in f]
                    if archivos_similares:
                        print(f"🔍 Archivos similares encontrados en uploads/: {archivos_similares}")
        except Exception as e:
            print(f"❌ Error al cargar imagen: {e}")
    else:
        print("El equipo no tiene imagen asignada")
    

    
    # Datos Generales
    datos_generales_header = Table([["Datos Generales"]], colWidths=[doc.width])
    datos_generales_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    datos_generales_header.setStyle(datos_generales_header_style)
    elements.append(datos_generales_header)
    
    general_data = [
        ['Fecha Ingreso', 'Tipo Equipo', 'Ubicación', 'Marca'],
        [str(equipo.fecha_ingreso) if equipo.fecha_ingreso else '', str(equipo.tipo_eq) if equipo.tipo_eq else '', 
         str(equipo.ubicacion) if equipo.ubicacion else '', str(equipo.marca) if equipo.marca else ''],
        ['Referencia', 'Serie', 'Color', 'Estado'],
        [str(equipo.referencia) if equipo.referencia else '', str(equipo.serie) if equipo.serie else '', 
         str(equipo.color) if equipo.color else '', str(equipo.estado_eq) if equipo.estado_eq else '']
    ]
    
    general_table = Table(general_data, colWidths=[doc.width/4, doc.width/4, doc.width/4, doc.width/4])
    general_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),           # Todo centrado
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Primera fila (etiquetas) en negrita
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),       # Segunda fila (valores) en texto normal
        ('FONTSIZE', (0, 1), (-1, 1), 8),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),  # Tercera fila (etiquetas) en negrita
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica'),       # Cuarta fila (valores) en texto normal
        ('FONTSIZE', (0, 3), (-1, 3), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    
    general_table.setStyle(general_style)
    elements.append(general_table)
    elements.append(Spacer(1, 5))
    
    # Dimensiones
    dimensiones_header = Table([["Dimensiones"]], colWidths=[doc.width])
    dimensiones_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    dimensiones_header.setStyle(dimensiones_header_style)
    elements.append(dimensiones_header)
    
    dimensiones_data = [
        ['Altura', 'Largo', 'Ancho', 'Peso'],
        [str(equipo.altura) if equipo.altura else 'N.A', str(equipo.largo) if equipo.largo else 'N.A', 
         str(equipo.ancho) if equipo.ancho else 'N.A', str(equipo.peso) if equipo.peso else 'N.A']
    ]
    
    dim_table = Table(dimensiones_data, colWidths=[doc.width/4, doc.width/4, doc.width/4, doc.width/4])
    dim_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),           # Todo centrado
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Primera fila (títulos) en negrita
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),      # Segunda fila (valores) en texto normal
        ('FONTSIZE', (0, 1), (-1, 1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    
    dim_table.setStyle(dim_style)
    elements.append(dim_table)
    elements.append(Spacer(1, 5))
    
    # Información Energética
    energia_header = Table([["Información Energética"]], colWidths=[doc.width])
    energia_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    energia_header.setStyle(energia_header_style)
    elements.append(energia_header)
    
    energia_data = [
        ['Tipo de Energía', 'Corriente', 'Potencia Instalada', 'Voltaje'],
        [str(equipo.tipo_energia) if equipo.tipo_energia else '', str(equipo.corriente) if equipo.corriente else '',
         str(equipo.potencia) if equipo.potencia else '', str(equipo.voltaje) if equipo.voltaje else '']
    ]
    
    energia_table = Table(energia_data, colWidths=[doc.width/4, doc.width/4, doc.width/4, doc.width/4])
    energia_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),           # Todo centrado
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Primera fila (títulos) en negrita
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),      # Segunda fila (valores) en texto normal
        ('FONTSIZE', (0, 1), (-1, 1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    energia_table.setStyle(energia_style)
    elements.append(energia_table)
    elements.append(Spacer(1, 5))
    
    # Información de Motores
    motores_header = Table([["Información Motores"]], colWidths=[doc.width])
    motores_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    motores_header.setStyle(motores_header_style)
    elements.append(motores_header)
    # NO Spacer aquí para que la tabla quede pegada
    if motores:
        motores_headers = ['N°', 'Nom. Motor', 'Descripción', 'Tipo', 'Energía',
                          'RPM', 'Eficiencia', 'Corriente', 'Potencia', 'Voltaje']
        motores_data = [motores_headers]
        for i, motor in enumerate(motores, 1):
            row = [
                str(i),
                str(motor.nomb_Motor) if motor.nomb_Motor else '',
                str(motor.descrip_Motor) if motor.descrip_Motor else '',
                str(motor.tipo_Motor) if motor.tipo_Motor else '',
                str(motor.rotacion) if motor.rotacion else '',
                str(motor.rpm_Motor) if motor.rpm_Motor else '',
                str(motor.eficiencia) if motor.eficiencia else '',
                str(motor.corriente_Motor) if motor.corriente_Motor else '',
                str(motor.potencia_Motor) if motor.potencia_Motor else '',
                str(motor.voltaje_Motor) if motor.voltaje_Motor else ''
            ]
            motores_data.append(row)
        # Definir ancho reducido para la columna 'N°' y repartir el resto
        ancho_n = doc.width * 0.05  # 5% del ancho total para 'N°'
        ancho_otros = (doc.width - ancho_n) / 9  # El resto para las otras 9 columnas
        motores_col_widths = [ancho_n] + [ancho_otros] * 9
        motores_table = Table(motores_data, colWidths=motores_col_widths)
        motores_style = TableStyle([
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Encabezados centrados
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),   # Resto de filas a la izquierda
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Primera fila (títulos) en negrita
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),     # Resto de filas en texto normal
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ])
        motores_table.setStyle(motores_style)
        elements.append(motores_table)
        elements.append(Spacer(1, 10))
    
    # Información de Consumo
    consumo_header = Table([["Información de Consumo"]], colWidths=[doc.width])
    consumo_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    consumo_header.setStyle(consumo_header_style)
    elements.append(consumo_header)
    
    consumo_data = [
        ['Tipo Refrigerante', 'Tipo Lubricante', 'Tipo Combustible'],
        [str(equipo.tipo_refrig) if equipo.tipo_refrig else 'N.A', str(equipo.tipo_lub) if equipo.tipo_lub else 'N.A',
         str(equipo.tipo_comb) if equipo.tipo_comb else 'N.A']
    ]
    consumo_table = Table(consumo_data, colWidths=[doc.width/3, doc.width/3, doc.width/3])
    consumo_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),           # Todo centrado
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Primera fila (títulos) en negrita
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),      # Segunda fila (valores) en texto normal
        ('FONTSIZE', (0, 1), (-1, 1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    consumo_table.setStyle(consumo_style)
    elements.append(consumo_table)
    elements.append(Spacer(1, 5))
    
    # Repuestos
    repuestos_data = [['Repuestos', str(equipo.repuestos) if equipo.repuestos else '']]
    repuestos_table = Table(repuestos_data, colWidths=[doc.width * 0.15, doc.width * 0.85])
    repuestos_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),  # Primera columna (título) en negrita
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),       # Segunda columna (valor) en texto normal
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    repuestos_table.setStyle(repuestos_style)
    elements.append(repuestos_table)
    elements.append(Spacer(1, 5))
    
    # Historial de Mantenimientos
    historial_header = Table([["Historial de Mantenimientos"]], colWidths=[doc.width])
    historial_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    historial_header.setStyle(historial_header_style)
    elements.append(historial_header)
    hist_text = str(equipo.hist_mtto) if equipo.hist_mtto else "El historial del mantenimiento realizado queda en el formato 'registro de mantenimiento de infraestructura' y se anexa a la hoja de vida"
    hist_data = [[hist_text]]
    hist_table = Table(hist_data, colWidths=[doc.width])
    hist_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, 0), 8),
        ('GRID', (0, 0), (0, 0), 0.5, colors.black),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 4),
        ('RIGHTPADDING', (0, 0), (0, 0), 4),
        ('TOPPADDING', (0, 0), (0, 0), 2),
        ('BOTTOMPADDING', (0, 0), (0, 0), 2),
    ]))
    elements.append(hist_table)
    elements.append(Spacer(1, 5))
    
    # Función de la Máquina
    funcion_header = Table([["Función de la Máquina"]], colWidths=[doc.width])
    funcion_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    funcion_header.setStyle(funcion_header_style)
    elements.append(funcion_header)
    func_text = str(equipo.funcion_maq) if equipo.funcion_maq else "Una bomba de agua, es un dispositivo que se utiliza para bombear agua de un lugar a otro, sin importar el fluido."
    func_data = [[func_text]]
    func_table = Table(func_data, colWidths=[doc.width])
    func_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, 0), 8),
        ('GRID', (0, 0), (0, 0), 0.5, colors.black),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 4),
        ('RIGHTPADDING', (0, 0), (0, 0), 4),
        ('TOPPADDING', (0, 0), (0, 0), 2),
        ('BOTTOMPADDING', (0, 0), (0, 0), 2),
    ]))
    elements.append(func_table)
    elements.append(Spacer(1, 5))
    
    # Checklists
    checklists_header = Table([["Documentos"]], colWidths=[doc.width])
    checklists_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    checklists_header.setStyle(checklists_header_style)
    elements.append(checklists_header)
    
    checklist_data = [
        ['Ficha Técnica', 'Hoja de Vida', 'Preoperacional', 'Plan de Mantenimiento', 'Inspección de Seguridad'],
        ['Sí' if equipo.ficha_tecnica else 'No', 'Sí' if equipo.hoja_vida else 'No',
         'Sí' if equipo.preoperacional else 'No', 'Sí' if equipo.plan_mantenimiento else 'No',
         'Sí' if equipo.inspeccion_seguridad else 'No'],
        ['Procedimientos de Oper.', 'Manuales', 'Certificaciones', 'Registro de MTTOS', ''],
        ['Sí' if equipo.procedimientos_operacion else 'No', 'Sí' if equipo.manual_usuario else 'No',
         'Sí' if equipo.certificaciones else 'No', 'Sí' if equipo.registro_mantenimientos else 'No', '']
    ]
    
    checklist_table = Table(checklist_data, colWidths=[doc.width/5, doc.width/5, doc.width/5, doc.width/5, doc.width/5])
    checklist_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),           # Todo centrado
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Primera fila (títulos) en negrita
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),      # Segunda fila (valores) en texto normal
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'), # Tercera fila (títulos) en negrita
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica'),      # Cuarta fila (valores) en texto normal
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    
    checklist_table.setStyle(checklist_style)
    elements.append(checklist_table)
    elements.append(Spacer(1, 10))
    
    # Manuales
    manuales_header = Table([["Manuales"]], colWidths=[doc.width])
    manuales_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    manuales_header.setStyle(manuales_header_style)
    elements.append(manuales_header)
    
    manuales_data = [
        ['Operación', 'Eléctrico', 'Mecánicos', 'Partes'],
        [
            'Sí' if getattr(equipo, 'manual_operacion', False) else 'No',
            'Sí' if getattr(equipo, 'manual_electrico', False) else 'No',
            'Sí' if getattr(equipo, 'manual_mecanicos', False) else 'No',
            'Sí' if getattr(equipo, 'manual_partes', False) else 'No'
        ]
    ]
    
    manuales_table = Table(manuales_data, colWidths=[doc.width/4, doc.width/4, doc.width/4, doc.width/4])
    manuales_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),           # Todo centrado
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Primera fila (títulos) en negrita
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),      # Segunda fila (valores) en texto normal
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ])
    manuales_table.setStyle(manuales_style)
    elements.append(manuales_table)
    elements.append(Spacer(1, 5))

     # Observaciones
    observaciones_header = Table([["Observaciones"]], colWidths=[doc.width])
    observaciones_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    observaciones_header.setStyle(observaciones_header_style)
    elements.append(observaciones_header)
    observaciones_data = [[str(equipo.observaciones) if equipo.observaciones else '']]
    observaciones_table = Table(observaciones_data, colWidths=[doc.width])
    observaciones_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, 0), 8),
        ('GRID', (0, 0), (0, 0), 0.5, colors.black),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 4),
        ('RIGHTPADDING', (0, 0), (0, 0), 4),
        ('TOPPADDING', (0, 0), (0, 0), 2),
        ('BOTTOMPADDING', (0, 0), (0, 0), 2),
    ]))
    elements.append(observaciones_table)
    elements.append(Spacer(1, 5))
    
    # Construir el documento con encabezado personalizado
    from reportlab.platypus import PageTemplate, Frame
    encabezado_height = 55
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - encabezado_height, id='normal')
    doc.addPageTemplates([PageTemplate(id='all', frames=frame, onPage=encabezado_y_footer_ficha_tecnica)])
    
    doc.build(elements)
    buffer.seek(0)
    return buffer 

def create_reportlab_pdf_lubrication_sheet(equipo, lubricaciones, title="Carta de Lubricación"):
    """
    Crea un PDF de carta de lubricación usando ReportLab.
    
    Args:
        equipo: Objeto Equipo
        lubricaciones: Lista de objetos Lubricacion
        title: Título del reporte
    
    Returns:
        BytesIO object con el PDF
    """
    buffer = BytesIO()
    pagesize = A4  # Portrait para carta de lubricación
    
    doc = SimpleDocTemplate(buffer, pagesize=pagesize, 
                           rightMargin=10*mm, leftMargin=10*mm,
                           topMargin=10*mm, bottomMargin=30*mm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        textColor=colors.grey
    )
    
    elements = []
    
    # Título
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))
    
    # Información del equipo
    info_equipo_header = Table([["Información del Equipo"]], colWidths=[doc.width])
    info_equipo_header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ])
    info_equipo_header.setStyle(info_equipo_header_style)
    elements.append(info_equipo_header)
    
    equipo_data = [
        ['Campo', 'Valor'],
        ['Código', str(equipo.codigo) if equipo.codigo else ''],
        ['Nombre', str(equipo.nombre) if equipo.nombre else ''],
        ['Ubicación', str(equipo.ubicacion) if equipo.ubicacion else ''],
        ['Marca', str(equipo.marca) if equipo.marca else ''],
        ['Modelo', str(equipo.modelo) if equipo.modelo else ''],
        ['Serie', str(equipo.serie) if equipo.serie else '']
    ]
    
    equipo_table = Table(equipo_data, repeatRows=1)
    equipo_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
    ])
    
    equipo_table.setStyle(equipo_style)
    elements.append(equipo_table)
    elements.append(Spacer(1, 15))
    
    # Cartas de lubricación
    if lubricaciones:
        cartas_lubricacion_header = Table([["Cartas de Lubricación"]], colWidths=[doc.width])
        cartas_lubricacion_header_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
        cartas_lubricacion_header.setStyle(cartas_lubricacion_header_style)
        elements.append(cartas_lubricacion_header)
        
        # Preparar datos de la tabla
        headers = ['N°', 'Mecanismo', 'Cant.', 'Tipo Lubricación', 'Producto', 
                  'Método Lubricación', 'Frecuencia Inspección', 'Observaciones']
        data = [headers]
        
        # Agregar datos de lubricaciones
        for lub in lubricaciones:
            row = [
                str(lub.numero) if lub.numero else '',
                str(lub.mecanismo) if lub.mecanismo else '',
                str(lub.cantidad) if lub.cantidad else '',
                str(lub.tipo_lubricante) if lub.tipo_lubricante else '',
                str(lub.producto) if lub.producto else '',
                str(lub.metodo_lubricacion) if lub.metodo_lubricacion else '',
                str(lub.frecuencia_inspeccion) if lub.frecuencia_inspeccion else '',
                str(lub.observaciones) if lub.observaciones else ''
            ]
            data.append(row)
        
        # Crear tabla de lubricaciones
        lub_table = Table(data, repeatRows=1)
        lub_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
        ])
        
        lub_table.setStyle(lub_style)
        elements.append(lub_table)
    else:
        elements.append(Paragraph("No hay cartas de lubricación registradas para este equipo.", styles['Normal']))
    
    # Construir el documento
    doc.build(elements, onFirstPage=draw_encabezado, onLaterPages=draw_encabezado)
    
    buffer.seek(0)
    return buffer 

# Ejemplo completo de uso para paginación 'Página X de Y' en tu reporte
# 1. Genera el PDF con el marcador '__TOTAL__' en el pie de página
# 2. Guarda el PDF en un archivo temporal
# 3. Llama a agregar_total_paginas para crear el PDF final con la paginación correcta

import tempfile

def generar_pdf_con_paginacion(mantenimientos, orientation='landscape', output_pdf_path='reporte_final.pdf'):
    """
    Genera un PDF con paginación 'Página X de Y' usando marcador y PyPDF2.
    - mantenimientos: lista de objetos de mantenimiento
    - orientation: 'landscape' o 'portrait'
    - output_pdf_path: ruta del PDF final
    """
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate
    from io import BytesIO
    import tempfile

    # 1. Genera el PDF con el marcador
    buffer = BytesIO()
    pagesize = landscape(A4) if orientation == 'landscape' else A4
    doc = SimpleDocTemplate(buffer, pagesize=pagesize, rightMargin=10*mm, leftMargin=10*mm, topMargin=20*mm, bottomMargin=15*mm)
    elements = []
    # Aquí deberías agregar tu tabla y demás elementos a 'elements'
    # Por ejemplo:
    # elements.append(mi_tabla)
    doc.build(elements)

    # 2. Guarda el PDF en un archivo temporal
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_pdf.write(buffer.getvalue())
    temp_pdf.close()
    temp_pdf_path = temp_pdf.name

    # 3. Llama a agregar_total_paginas para crear el PDF final
    agregar_total_paginas(temp_pdf_path, output_pdf_path, pagesize=pagesize)
    # Ahora 'output_pdf_path' tiene la paginación correcta
    return output_pdf_path

# USO:
# output_pdf = generar_pdf_con_paginacion(mantenimientos)
# print(f"PDF generado: {output_pdf}")

import os
from flask import send_file, after_this_request
from reportlab.lib.pagesizes import landscape, A4

def generar_y_enviar_pdf_mantenimiento(mantenimientos):
    """
    Genera el PDF de mantenimientos con encabezado y paginación "Página X de Y" en todas las páginas.
    """
    # Generar PDF base con encabezado y paginación básica
    buffer = create_reportlab_pdf_maintenance_report(mantenimientos, orientation='landscape')
    
    # Usar la función que agrega paginación total y envía el archivo
    nombre_archivo = f'mantenimientos_programados_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    return generar_y_enviar_pdf_con_paginacion(buffer, nombre_archivo)

# USO EN FLASK:
# @app.route('/descargar_reporte')
# def descargar_reporte():
#     return generar_y_enviar_pdf_mantenimiento(mantenimientos)

# --- FUNCIÓN SIMPLIFICADA PARA PAGINACIÓN ---
def add_pagination_footer(canvas, doc):
    """
    Función para agregar paginación "Página X de Y" en el pie de página.
    """
    canvas.saveState()
    # No dibujar nada aquí, solo reservar el espacio
    # La paginación final se agregará con PyPDF2
    canvas.restoreState()

# --- FUNCIÓN PARA ENCABEZADO Y PIE DE PÁGINA EN TODOS LOS PDF ---
def encabezado_y_footer(canvas, doc):
    draw_encabezado(canvas, doc)
    add_pagination_footer(canvas, doc)

# --- FUNCIÓN PARA ENCABEZADO Y PIE DE PÁGINA ESPECÍFICA PARA FICHA TÉCNICA ---
def encabezado_y_footer_ficha_tecnica(canvas, doc):
    draw_encabezado_ficha_tecnica(canvas, doc)
    add_pagination_footer(canvas, doc)

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas as rl_canvas
from io import BytesIO

def agregar_paginacion_final(input_pdf_path, output_pdf_path):
    """
    Agrega la paginación 'Página X de Y' en el pie de página de cada página del PDF.
    input_pdf_path: ruta del PDF base (sin paginación final)
    output_pdf_path: ruta del PDF final con paginación
    """
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    total = len(reader.pages)
    for i, page in enumerate(reader.pages, 1):
        packet = BytesIO()
        can = rl_canvas.Canvas(packet, pagesize=page.mediabox[2:])
        can.setFont("Helvetica", 8)
        can.drawCentredString(
            float(page.mediabox[2]) / 2,
            20,
            f"Página {i} de {total}"
        )
        can.save()
        packet.seek(0)
        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        writer.add_page(page)
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

# Ejemplo de uso:
# 1. Genera el PDF base (sin paginación final) y guárdalo en 'temp.pdf'
# 2. Llama a agregar_paginacion_final('temp.pdf', 'reporte_final.pdf')
# 3. Envía 'reporte_final.pdf' al usuario

import tempfile
import os
from flask import send_file, after_this_request

def generar_y_enviar_pdf_con_paginacion(buffer, nombre_archivo="reporte.pdf"):
    """
    Genera un PDF base (en buffer), agrega paginación 'Página X de Y' y lo envía al usuario.
    Limpia los archivos temporales automáticamente.
    """
    # 1. Guarda el PDF base en un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_base:
        temp_base.write(buffer.getvalue())
        temp_base_path = temp_base.name
    # 2. Crea el PDF final con paginación
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_final:
        temp_final_path = temp_final.name
    agregar_paginacion_final(temp_base_path, temp_final_path)
    # 3. Limpia los archivos temporales después de enviar
    @after_this_request
    def cleanup(response):
        try:
            os.remove(temp_base_path)
            os.remove(temp_final_path)
        except Exception as e:
            print(f"Error eliminando archivos temporales: {e}")
        return response
    # 4. Envía el PDF final al usuario
    return send_file(temp_final_path, as_attachment=True, download_name=nombre_archivo, mimetype='application/pdf')

# Ejemplo de uso en una ruta Flask:
# buffer = create_reportlab_pdf_maintenance_report(mantenimientos)
# return generar_y_enviar_pdf_con_paginacion(buffer, nombre_archivo="mantenimientos_programados.pdf")

import tempfile
from flask import send_file, after_this_request

def generar_y_enviar_pdf_ficha_tecnica(equipo, motores, nombre_archivo="ficha_tecnica.pdf"):
    """
    Genera el PDF de ficha técnica con paginación 'Página X de Y' y lo envía al usuario.
    """
    # 1. Genera el PDF base en memoria
    buffer = create_reportlab_pdf_equipment_technical_sheet(equipo, motores)
    # 2. Guarda el PDF base en un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_base:
        temp_base.write(buffer.getvalue())
        temp_base_path = temp_base.name
    # 3. Crea el PDF final con paginación
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_final:
        temp_final_path = temp_final.name
    agregar_paginacion_final(temp_base_path, temp_final_path)
    # 4. Limpia los archivos temporales después de enviar
    @after_this_request
    def cleanup(response):
        import os
        try:
            os.remove(temp_base_path)
            os.remove(temp_final_path)
        except Exception as e:
            print(f"Error eliminando archivos temporales: {e}")
        return response
    # 5. Envía el PDF final al usuario
    return send_file(temp_final_path, as_attachment=True, download_name=nombre_archivo, mimetype='application/pdf')
