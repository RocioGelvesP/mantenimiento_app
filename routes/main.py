from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from models import db, Auditoria
from utils import require_any_role
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('home_bp.index'))

@main_bp.route('/auditoria')
@login_required
@require_any_role('super_admin', 'admin')
def auditoria():
    # Obtener parámetros de filtro
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    usuario = request.args.get('usuario')
    accion = request.args.get('accion')
    tabla = request.args.get('tabla')
    
    # Construir consulta base
    query = Auditoria.query
    
    # Aplicar filtros
    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            query = query.filter(Auditoria.fecha >= fecha_inicio_dt)
        except ValueError:
            pass
    
    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Auditoria.fecha < fecha_fin_dt)
        except ValueError:
            pass
    
    if usuario:
        query = query.filter(Auditoria.usuario.ilike(f'%{usuario}%'))
    
    if accion:
        query = query.filter(Auditoria.accion == accion)
    
    if tabla:
        query = query.filter(Auditoria.tabla == tabla)
    
    # Ordenar por fecha más reciente
    registros = query.order_by(Auditoria.fecha.desc()).limit(1000).all()
    
    # Obtener listas únicas para los filtros
    usuarios_unicos = db.session.query(Auditoria.usuario).distinct().all()
    acciones_unicas = db.session.query(Auditoria.accion).distinct().all()
    tablas_unicas = db.session.query(Auditoria.tabla).distinct().all()
    
    return render_template('auditoria/lista.html', 
                         registros=registros,
                         usuarios_unicos=[u[0] for u in usuarios_unicos if u[0]],
                         acciones_unicas=[a[0] for a in acciones_unicas if a[0]],
                         tablas_unicas=[t[0] for t in tablas_unicas if t[0]])
