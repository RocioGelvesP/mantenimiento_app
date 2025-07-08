from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
import   os
import platform
import pdfkit
from models import Auditoria, db
from datetime import datetime

def get_pdf_config():
	sistema = platform.system()
	if sistema == 'Windows':
		path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
	elif sistema == 'Linux':
		path_wkhtmltopdf = '/usr/bin/wkhtmltopdf'
	else:
		raise OSError(f"Sistema no compatible: {sistema}")
	if not os.path.exists(path_wkhtmltopdf):
		raise FileNotFoundError(f"No se encontró wkhtmltopdf en: {path_wkhtmltopdf}")

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
