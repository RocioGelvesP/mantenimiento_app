from functools import wraps
from flask import abort, flash, redirect, url_for, request, send_file, after_this_request
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

    # Anchos personalizados para el encabezado (suma = 764)
    col_widths_header = [98, 222, 244, 120, 80]  # Ajusta para que sumen 764

    # Dibuja el borde exterior
    canvas.rect(x, y - height, sum(col_widths_header), height)

    # Líneas verticales
    for i in range(1, 5):
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
    canvas.setFont('Helvetica-Bold', 11)
    center_x = x + sum(col_widths_header[:1]) + col_widths_header[1] / 2
    center_y = y - height / 2
    canvas.drawCentredString(center_x, center_y + 6, "INR INVERSIONES")
    canvas.drawCentredString(center_x, center_y - 8, "REINOSO Y CIA. LTDA.")

    # 3. Título (columna 3)
    canvas.setFont('Helvetica-Bold', 10)
    center_x2 = x + sum(col_widths_header[:2]) + col_widths_header[2] / 2
    canvas.drawCentredString(center_x2, center_y, "CONTROL DE ACTIVIDADES DE MANTENIMIENTO")

    # 4. Mes (columna 4)
    canvas.setFont('Helvetica-Bold', 13)
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    mes_actual = meses[datetime.now().month - 1]
    center_x3 = x + sum(col_widths_header[:3]) + col_widths_header[3] / 2
    canvas.drawCentredString(center_x3, center_y, mes_actual)

    # 5. Código/Edición (columna 5)
    cuadro_x = x + sum(col_widths_header[:4])
    cuadro_w = col_widths_header[4]
    row_h = height / 4
    for i, (txt, font) in enumerate([
        ("Código", 'Helvetica-Bold'),
        ("71-MT-43", 'Helvetica'),
        ("Edición", 'Helvetica-Bold'),
        ("4/Jul/2025", 'Helvetica')
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
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))
    info_data = [
        ['Campo', 'Valor', 'Campo', 'Valor'],
        ['Código', str(equipo.codigo) if equipo.codigo else '', 'Marca', str(equipo.marca) if equipo.marca else ''],
        ['Nombre', str(equipo.nombre) if equipo.nombre else '', 'Modelo', str(equipo.modelo) if equipo.modelo else ''],
        ['Ubicación', str(equipo.ubicacion) if equipo.ubicacion else '', 'Serie', str(equipo.serie) if equipo.serie else ''],
        ['Estado', str(equipo.estado_eq) if equipo.estado_eq else '', 'Fecha Ingreso', equipo.fecha_ingreso.strftime('%d/%m/%Y') if equipo.fecha_ingreso else ''],
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
    elements.append(Spacer(1, 15))
    if mantenimientos:
        elements.append(Paragraph("Mantenimientos Realizados", title_style))
        elements.append(Spacer(1, 10))
        headers = ['F. Inicio', 'F. Fin', 'Tiempo', 'Tipo', 'Servicio', 'Técnico', 'Repuestos', 'Herramientas', 'Observaciones', 'C. Rep.', 'C. Herr.', 'C. MDO', 'Costo Total']
        data = [headers]
        for mtto in mantenimientos:
            costo_total = (mtto.costo_rep or 0) + (mtto.costo_herram or 0) + (mtto.costo_mdo or 0)
            row = [
                mtto.hora_inicial.strftime('%d/%m/%Y %H:%M') if mtto.hora_inicial else '',
                mtto.hora_final.strftime('%d/%m/%Y %H:%M') if mtto.hora_final else '',
                str(mtto.tiempo_gastado) if mtto.tiempo_gastado else '',
                str(mtto.tipo_mantenimiento) if mtto.tipo_mantenimiento else '',
                str(mtto.servicio) if mtto.servicio else '',
                str(mtto.tecnico_realizador or mtto.tecnico_asignado) if mtto.tecnico_realizador or mtto.tecnico_asignado else '',
                str(mtto.repuestos) if mtto.repuestos else '',
                str(mtto.herramientas) if mtto.herramientas else '',
                str(mtto.observaciones) if mtto.observaciones else '',
                f"${mtto.costo_rep:,.2f}" if mtto.costo_rep else '$0.00',
                f"${mtto.costo_herram:,.2f}" if mtto.costo_herram else '$0.00',
                f"${mtto.costo_mdo:,.2f}" if mtto.costo_mdo else '$0.00',
                f"${costo_total:,.2f}"
            ]
            data.append(row)
        maint_table = Table(data, repeatRows=1)
        maint_style = TableStyle([
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
        maint_table.setStyle(maint_style)
        elements.append(maint_table)
    else:
        elements.append(Paragraph("No hay mantenimientos realizados registrados.", styles['Normal']))
    from reportlab.platypus import PageTemplate, Frame
    encabezado_height = 55
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - encabezado_height, id='normal')
    doc.addPageTemplates([PageTemplate(id='all', frames=frame, onPage=encabezado_y_footer)])
    doc.build(elements)
    buffer.seek(0)
    return buffer

def create_reportlab_pdf_equipment_technical_sheet(equipo, motores, title="Ficha Técnica de Equipos y Máquinas"):
    """
    Crea un PDF de ficha técnica de equipo usando ReportLab.
    
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
    
    # Datos Generales
    elements.append(Paragraph("Datos Generales", section_style))
    
    general_data = [
        ['Campo', 'Valor', 'Campo', 'Valor'],
        ['Código', str(equipo.codigo) if equipo.codigo else '', 'Nombre', str(equipo.nombre) if equipo.nombre else ''],
        ['Fecha Ingreso', equipo.fecha_ingreso.strftime('%d/%m/%Y') if equipo.fecha_ingreso else '', 'Tipo Equipo', str(equipo.tipo_eq) if equipo.tipo_eq else ''],
        ['Ubicación', str(equipo.ubicacion) if equipo.ubicacion else '', 'Marca', str(equipo.marca) if equipo.marca else ''],
        ['Referencia', str(equipo.referencia) if equipo.referencia else '', 'Serie', str(equipo.serie) if equipo.serie else ''],
        ['Color', str(equipo.color) if equipo.color else '', 'Estado', str(equipo.estado_eq) if equipo.estado_eq else ''],
    ]
    
    general_table = Table(general_data, repeatRows=1)
    general_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
    ])
    
    general_table.setStyle(general_style)
    elements.append(general_table)
    elements.append(Spacer(1, 15))
    
    # Dimensiones
    elements.append(Paragraph("Dimensiones", section_style))
    
    dimensiones_data = [
        ['Altura', 'Largo', 'Ancho', 'Peso'],
        [str(equipo.altura) if equipo.altura else '', str(equipo.largo) if equipo.largo else '', 
         str(equipo.ancho) if equipo.ancho else '', str(equipo.peso) if equipo.peso else '']
    ]
    
    dim_table = Table(dimensiones_data, repeatRows=1)
    dim_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
    ])
    
    dim_table.setStyle(dim_style)
    elements.append(dim_table)
    elements.append(Spacer(1, 15))
    
    # Información Energética
    elements.append(Paragraph("Información Energética", section_style))
    
    energia_data = [
        ['Tipo de Energía', 'Corriente', 'Potencia Instalada', 'Voltaje'],
        [str(equipo.tipo_energia) if equipo.tipo_energia else '', str(equipo.corriente) if equipo.corriente else '',
         str(equipo.potencia_instalada) if equipo.potencia_instalada else '', str(equipo.voltaje) if equipo.voltaje else '']
    ]
    
    energia_table = Table(energia_data, repeatRows=1)
    energia_table.setStyle(dim_style)  # Reutilizar el mismo estilo
    elements.append(energia_table)
    elements.append(Spacer(1, 15))
    
    # Información de Motores
    if motores:
        elements.append(Paragraph("Información Motores", section_style))
        
        motores_headers = ['N°', 'Nombre Motor', 'Descripción', 'Tipo', 'Dirección de Rotación', 
                          'RPM', 'Eficiencia', 'Corriente', 'Potencia Instalada', 'Voltaje']
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
        
        motores_table = Table(motores_data, repeatRows=1)
        motores_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
        ])
        
        motores_table.setStyle(motores_style)
        elements.append(motores_table)
        elements.append(Spacer(1, 15))
    
    # Información de Consumo
    elements.append(Paragraph("Información de Consumo", section_style))
    
    consumo_data = [
        ['Tipo Refrigerante', 'Tipo Lubricante', 'Tipo Combustible'],
        [str(equipo.tipo_refrigerante) if equipo.tipo_refrigerante else '',
         str(equipo.tipo_lubricante) if equipo.tipo_lubricante else '',
         str(equipo.tipo_combustible) if equipo.tipo_combustible else '']
    ]
    
    consumo_table = Table(consumo_data, repeatRows=1)
    consumo_table.setStyle(dim_style)  # Reutilizar el mismo estilo
    elements.append(consumo_table)
    elements.append(Spacer(1, 10))
    
    # Repuestos
    if equipo.repuestos:
        repuestos_text = f"Repuestos: {equipo.repuestos}"
        elements.append(Paragraph(repuestos_text, styles['Normal']))
        elements.append(Spacer(1, 15))
    
    # Documentación
    elements.append(Paragraph("Documentación", section_style))
    
    doc_data = [
        ['Ficha Técnica', 'Hoja de Vida', 'Preoperacional', 'Plan de Mantenimiento'],
        ['Sí' if equipo.ficha_tecnica else 'No', 'Sí' if equipo.hoja_vida else 'No',
         'Sí' if equipo.preoperacional else 'No', 'Sí' if equipo.plan_mantenimiento else 'No']
    ]
    
    doc_table = Table(doc_data, repeatRows=1)
    doc_table.setStyle(dim_style)  # Reutilizar el mismo estilo
    elements.append(doc_table)
    elements.append(Spacer(1, 15))
    
    # Observaciones
    if equipo.observaciones:
        elements.append(Paragraph("Observaciones", section_style))
        elements.append(Paragraph(str(equipo.observaciones), styles['Normal']))
    
    # Construir el documento
    doc.build(elements, onFirstPage=draw_encabezado, onLaterPages=draw_encabezado)
    
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
    elements.append(Paragraph("Información del Equipo", section_style))
    
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
        elements.append(Paragraph("Cartas de Lubricación", section_style))
        
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
