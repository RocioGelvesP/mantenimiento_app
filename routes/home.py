from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Equipo, Programado
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func
from collections import Counter
from utils import get_mantenimientos_filtrados_por_rol

home_bp = Blueprint('home_bp', __name__)

@home_bp.route('/')
@login_required
def index():
    # Contar equipos
    total_equipos = Equipo.query.count()
    
    # Obtener consulta base filtrada por rol
    query_base = get_mantenimientos_filtrados_por_rol()
    
    # Contar mantenimientos por estado final
    mantenimientos_completados = query_base.filter_by(estado_final='Completado').count()
    mantenimientos_cancelados = query_base.filter_by(estado_final='Cancelado').count()
    
    # Contar mantenimientos activos (sin estado final)
    mantenimientos_activos = query_base.filter_by(estado_final=None).count()
    
    # Total de mantenimientos
    total_mantenimientos = mantenimientos_completados + mantenimientos_cancelados + mantenimientos_activos
    
    # Calcular porcentajes (evitar división por cero)
    def porcentaje(valor):
        return round((valor / total_mantenimientos) * 100, 1) if total_mantenimientos > 0 else 0

    porcentaje_completados = porcentaje(mantenimientos_completados)
    porcentaje_cancelados = porcentaje(mantenimientos_cancelados)
    porcentaje_activos = porcentaje(mantenimientos_activos)

    # Mantenimientos próximos a vencer (15 días) y vencidos
    hoy = datetime.now().date()
    en_15_dias = hoy + timedelta(days=15)
    proximos = query_base.filter(
        Programado.fecha_prog >= hoy,
        Programado.fecha_prog <= en_15_dias,
        func.lower(func.trim(Programado.estado_inicial)).in_(['programado', 'asignado'])
    ).count()
    vencidos = query_base.filter(
        or_(
            and_(Programado.fecha_prog < hoy, func.lower(func.trim(Programado.estado_inicial)) == 'programado'),
            func.lower(func.trim(Programado.estado_inicial)) == 'vencido'
        )
    ).count()

    porcentaje_proximos = round((proximos / total_mantenimientos) * 100, 1) if total_mantenimientos > 0 else 0
    porcentaje_vencidos = round((vencidos / total_mantenimientos) * 100, 1) if total_mantenimientos > 0 else 0

    fecha_inicio_proximos = hoy.strftime('%Y-%m-%d')
    fecha_fin_proximos = en_15_dias.strftime('%Y-%m-%d')

    # Obtener mantenimientos completados recientemente (últimos 7 días)
    mantenimientos_completados_recientes = []
    if current_user.is_admin() or current_user.is_supervisor():
        fecha_limite = datetime.now() - timedelta(days=7)
        mantenimientos_completados_recientes = query_base.filter(
            Programado.estado_final == 'Completado',
            Programado.hora_final >= fecha_limite
        ).order_by(Programado.hora_final.desc()).limit(12).all()

    return render_template('home/index.html',
        total_equipos=total_equipos,
        mantenimientos_completados=mantenimientos_completados,
        mantenimientos_cancelados=mantenimientos_cancelados,
        mantenimientos_activos=mantenimientos_activos,
        porcentaje_completados=porcentaje_completados,
        porcentaje_cancelados=porcentaje_cancelados,
        porcentaje_activos=porcentaje_activos,
        proximos=proximos,
        vencidos=vencidos,
        porcentaje_proximos=porcentaje_proximos,
        porcentaje_vencidos=porcentaje_vencidos,
        fecha_inicio_proximos=fecha_inicio_proximos,
        fecha_fin_proximos=fecha_fin_proximos,
        mantenimientos_completados_recientes=mantenimientos_completados_recientes,
        current_user=current_user
    )
