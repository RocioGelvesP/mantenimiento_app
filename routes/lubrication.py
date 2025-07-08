from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Equipo, Lubricacion, get_or_404
from forms import LubricacionForm
from utils import require_role, require_delete_permission, require_any_role
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import make_response
try:
    from weasyprint import HTML
except ImportError:
    HTML = None  # weasyprint no está instalado

lubrication_bp = Blueprint('lubrication', __name__)

def guardar_imagen_equipo(archivo, codigo_equipo):
    """Guardar imagen de lubricación del equipo"""
    if archivo and archivo.filename:
        # Validar tipo de archivo
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        if '.' not in archivo.filename or \
           archivo.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return None
        
        # Crear directorio si no existe
        upload_dir = os.path.join('static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{codigo_equipo}_lubricacion_{timestamp}_{secure_filename(archivo.filename)}"
        filepath = os.path.join(upload_dir, filename)
        
        try:
            archivo.save(filepath)
            return filename
        except Exception as e:
            print(f"Error guardando imagen: {e}")
            return None
    return None

@lubrication_bp.route('/lista')
@login_required
@require_any_role('super_admin', 'admin', 'supervisor')
def lista_cartas():
    """Mostrar lista general de todos los equipos con información de lubricación"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    filtro = request.args.get('filtro', 'todos')  # 'todos', 'con_cartas', 'sin_cartas'
    
    # Obtener estadísticas generales
    total_equipos = db.session.query(Equipo).count()
    equipos_con_cartas = db.session.query(Equipo).join(Lubricacion).distinct().count()
    total_cartas = db.session.query(Lubricacion).count()
    
    # Construir la consulta base
    query = db.session.query(
        Equipo,
        db.func.count(Lubricacion.id).label('total_cartas'),
        db.func.max(Lubricacion.numero).label('ultima_carta')
    ).outerjoin(
        Lubricacion, Equipo.codigo == Lubricacion.equipo_codigo
    ).group_by(
        Equipo.codigo, Equipo.nombre, Equipo.ubicacion
    )
    
    # Aplicar filtros
    if filtro == 'con_cartas':
        query = query.having(db.func.count(Lubricacion.id) > 0)
    elif filtro == 'sin_cartas':
        query = query.having(db.func.count(Lubricacion.id) == 0)
    
    # Ordenar y paginar
    equipos_con_lubricacion = query.order_by(
        Equipo.codigo
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('lubrication/lista_general.html', 
                         equipos=equipos_con_lubricacion,
                         total_equipos=total_equipos,
                         equipos_con_cartas=equipos_con_cartas,
                         total_cartas=total_cartas,
                         filtro_actual=filtro)

@lubrication_bp.route('/equipo/<codigo_equipo>', methods=['GET', 'POST'])
@login_required
@require_any_role('super_admin', 'admin', 'supervisor', 'tecnico')
def cartas_equipo(codigo_equipo):
    """Mostrar y editar en lote las cartas de lubricación de un equipo específico"""
    equipo = Equipo.query.filter_by(codigo=codigo_equipo).first()
    if not equipo:
        flash('Equipo no encontrado', 'error')
        return redirect(url_for('equipment.listar_equipos'))

    if request.method == 'POST' and (current_user.is_admin() or current_user.is_supervisor() or current_user.is_super_admin()):
        ids = request.form.getlist('id[]')
        mecanismos = request.form.getlist('mecanismo[]')
        cantidades = request.form.getlist('cantidad[]')
        tipos = request.form.getlist('tipo_lubricante[]')
        productos = request.form.getlist('producto[]')
        metodos = request.form.getlist('metodo_lubricacion[]')
        frecuencias = request.form.getlist('frecuencia_inspeccion[]')
        observaciones = request.form.getlist('observaciones[]')

        # Obtener todas las cartas actuales del equipo
        cartas_actuales = {str(lub.id): lub for lub in Lubricacion.query.filter_by(equipo_codigo=codigo_equipo).all()}
        ids_enviados = set()
        numero = 1
        for i in range(len(mecanismos)):
            id_lub = ids[i]
            if id_lub and id_lub in cartas_actuales:
                # Editar existente
                lub = cartas_actuales[id_lub]
                lub.numero = numero
                lub.mecanismo = mecanismos[i]
                lub.cantidad = cantidades[i]
                lub.tipo_lubricante = tipos[i]
                lub.producto = productos[i]
                lub.metodo_lubricacion = metodos[i]
                lub.frecuencia_inspeccion = frecuencias[i]
                lub.observaciones = observaciones[i]
                ids_enviados.add(id_lub)
            else:
                # Nueva carta
                nueva = Lubricacion(
                    equipo_codigo=codigo_equipo,
                    numero=numero,
                    mecanismo=mecanismos[i],
                    cantidad=cantidades[i],
                    tipo_lubricante=tipos[i],
                    producto=productos[i],
                    metodo_lubricacion=metodos[i],
                    frecuencia_inspeccion=frecuencias[i],
                    observaciones=observaciones[i]
                )
                db.session.add(nueva)
            numero += 1
        # Eliminar cartas que no están en el formulario
        for id_actual, carta in cartas_actuales.items():
            if id_actual not in ids_enviados and id_actual:
                db.session.delete(carta)
        db.session.commit()
        flash('Cambios guardados exitosamente', 'success')
        return redirect(url_for('lubrication.cartas_equipo', codigo_equipo=codigo_equipo))

    lubricaciones = Lubricacion.query.filter_by(equipo_codigo=codigo_equipo).order_by(Lubricacion.numero).all()
    return render_template('lubrication/cartas_equipo.html', 
                         equipo=equipo, 
                         lubricaciones=lubricaciones)

@lubrication_bp.route('/nueva/<codigo_equipo>', methods=['GET', 'POST'])
@login_required
@require_any_role('super_admin', 'admin', 'supervisor')
def nueva_carta(codigo_equipo):
    """Crear varias cartas de lubricación en lote"""
    equipo = Equipo.query.filter_by(codigo=codigo_equipo).first()
    if not equipo:
        flash('Equipo no encontrado', 'error')
        return redirect(url_for('equipment.listar_equipos'))

    form = LubricacionForm()
    if request.method == 'POST':
        mecanismos = request.form.getlist('mecanismo[]')
        cantidades = request.form.getlist('cantidad[]')
        tipos = request.form.getlist('tipo_lubricante[]')
        productos = request.form.getlist('producto[]')
        metodos = request.form.getlist('metodo_lubricacion[]')
        frecuencias = request.form.getlist('frecuencia_inspeccion[]')
        observaciones = request.form.getlist('observaciones[]')

        total = len(mecanismos)
        if total == 0:
            flash('Debe ingresar al menos una lubricación', 'error')
            return render_template('lubrication/nueva_carta.html', form=form, equipo=equipo)

        # Obtener el último número de carta para ese equipo
        last = db.session.query(db.func.max(Lubricacion.numero)).filter_by(equipo_codigo=codigo_equipo).scalar() or 0
        nuevas = []
        for i in range(total):
            nuevas.append(Lubricacion(
                equipo_codigo=codigo_equipo,
                numero=last + i + 1,
                mecanismo=mecanismos[i],
                cantidad=cantidades[i],
                tipo_lubricante=tipos[i],
                producto=productos[i],
                metodo_lubricacion=metodos[i],
                frecuencia_inspeccion=frecuencias[i],
                observaciones=observaciones[i] if observaciones else None
            ))
        db.session.add_all(nuevas)
        db.session.commit()
        flash(f'Se guardaron {total} cartas de lubricación exitosamente', 'success')
        return redirect(url_for('lubrication.cartas_equipo', codigo_equipo=codigo_equipo))

    return render_template('lubrication/nueva_carta.html', form=form, equipo=equipo)

@lubrication_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@require_any_role('super_admin', 'admin', 'supervisor')
def editar_carta(id):
    """Editar una carta de lubricación existente"""
    lubricacion = get_or_404(Lubricacion, id)
    equipo = Equipo.query.filter_by(codigo=lubricacion.equipo_codigo).first()
    
    form = LubricacionForm(obj=lubricacion)
    if form.validate_on_submit():
        lubricacion.numero = form.numero.data
        lubricacion.mecanismo = form.mecanismo.data
        lubricacion.cantidad = form.cantidad.data
        lubricacion.tipo_lubricante = form.tipo_lubricante.data
        lubricacion.producto = form.producto.data
        lubricacion.metodo_lubricacion = form.metodo_lubricacion.data
        lubricacion.frecuencia_inspeccion = form.frecuencia_inspeccion.data
        lubricacion.observaciones = form.observaciones.data
        
        db.session.commit()
        
        flash('Carta de lubricación actualizada exitosamente', 'success')
        return redirect(url_for('lubrication.cartas_equipo', codigo_equipo=lubricacion.equipo_codigo))
    
    return render_template('lubrication/editar_carta.html', 
                         form=form, 
                         lubricacion=lubricacion, 
                         equipo=equipo)

@lubrication_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@require_delete_permission()
def eliminar_carta(id):
    """Eliminar una carta de lubricación"""
    lubricacion = get_or_404(Lubricacion, id)
    equipo_codigo = lubricacion.equipo_codigo
    
    db.session.delete(lubricacion)
    db.session.commit()
    
    flash('Carta de lubricación eliminada exitosamente', 'success')
    return redirect(url_for('lubrication.cartas_equipo', codigo_equipo=equipo_codigo))

@lubrication_bp.route('/imprimir/<codigo_equipo>')
@login_required
@require_any_role('super_admin', 'admin', 'supervisor', 'tecnico')
def imprimir_cartas(codigo_equipo):
    """Imprimir las cartas de lubricación de un equipo"""
    equipo = Equipo.query.filter_by(codigo=codigo_equipo).first()
    if not equipo:
        flash('Equipo no encontrado', 'error')
        return redirect(url_for('equipment.listar_equipos'))
    
    lubricaciones = Lubricacion.query.filter_by(equipo_codigo=codigo_equipo).order_by(Lubricacion.numero).all()
    
    return render_template('lubrication/imprimir_cartas.html', 
                         equipo=equipo, 
                         lubricaciones=lubricaciones)

@lubrication_bp.route('/subir-imagen/<codigo_equipo>', methods=['POST'])
@login_required
@require_any_role('super_admin', 'admin', 'supervisor')
def subir_imagen(codigo_equipo):
    """Subir imagen de lubricación para un equipo"""
    equipo = Equipo.query.filter_by(codigo=codigo_equipo).first()
    if not equipo:
        flash('Equipo no encontrado', 'error')
        return redirect(url_for('equipment.listar_equipos'))
    
    if 'imagen' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('lubrication.cartas_equipo', codigo_equipo=codigo_equipo))
    
    archivo = request.files['imagen']
    if archivo.filename == '':
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('lubrication.cartas_equipo', codigo_equipo=codigo_equipo))
    
    # Guardar imagen
    imagen_filename = guardar_imagen_equipo(archivo, codigo_equipo)
    if imagen_filename:
        # Eliminar imagen anterior si existe
        if equipo.imagen_lubricacion:
            try:
                imagen_anterior = os.path.join('static', 'uploads', equipo.imagen_lubricacion)
                if os.path.exists(imagen_anterior):
                    os.remove(imagen_anterior)
            except:
                pass
        
        # Actualizar equipo con nueva imagen
        equipo.imagen_lubricacion = imagen_filename
        db.session.commit()
        
        flash('Imagen subida exitosamente', 'success')
    else:
        flash('Error al subir la imagen. Verifique el formato y tamaño del archivo', 'error')
    
    return redirect(url_for('lubrication.cartas_equipo', codigo_equipo=codigo_equipo))

@lubrication_bp.route('/pdf/<codigo_equipo>')
@login_required
@require_any_role('super_admin', 'admin', 'supervisor', 'tecnico')
def descargar_pdf_lubricacion(codigo_equipo):
    if HTML is None:
        flash('La funcionalidad de PDF requiere instalar weasyprint. Ejecute: pip install weasyprint', 'error')
        return redirect(url_for('lubrication.cartas_equipo', codigo_equipo=codigo_equipo))
    
    equipo = Equipo.query.filter_by(codigo=codigo_equipo).first()
    if not equipo:
        flash('Equipo no encontrado', 'error')
        return redirect(url_for('equipment.listar_equipos'))
    
    lubricaciones = Lubricacion.query.filter_by(equipo_codigo=codigo_equipo).order_by(Lubricacion.numero).all()
    fecha_actual = datetime.now().strftime('%d/%m/%Y')
    html = render_template('lubrication/cartas_equipo_pdf.html', equipo=equipo, lubricaciones=lubricaciones, fecha_actual=fecha_actual)
    pdf = HTML(string=html, base_url=request.url_root).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Carta_Lubricacion_{equipo.codigo}.pdf'
    return response 