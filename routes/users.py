from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User
from forms import UsuarioForm, EliminarForm
from utils import require_role, get_usuarios_filtrados_por_rol, require_delete_permission, require_any_role

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@usuarios_bp.route('/listar', methods=['GET'])
@login_required
@require_any_role('super_admin', 'admin')
def listar_usuarios():
    usuarios = get_usuarios_filtrados_por_rol()
    form_eliminar = EliminarForm()
    return render_template('usuarios/listar_usuarios.html', usuarios=usuarios, form_eliminar=form_eliminar)

@usuarios_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@require_any_role('super_admin', 'admin')
def nuevo_usuario():
    form = UsuarioForm()
    if form.validate_on_submit():
        name = form.name.data   
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = form.role.data
        is_active = form.is_active.data
        usuario_existente = User.query.filter_by(username=username).first()
        if usuario_existente:
            flash("El nombre de usuario ya está registrado. Intenta con otro.", "danger")
            return redirect(url_for('usuarios.nuevo_usuario'))
        nuevo_usuario = User(
            name=name,
            username=username,
            email=email,
            password=generate_password_hash(password),
            role=role,
            is_active=is_active
        )
        db.session.add(nuevo_usuario)
        try:
            db.session.commit()
            flash("Usuario creado con éxito", "success")
            return redirect(url_for('usuarios.listar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear usuario: {str(e)}", "danger")
            return redirect(url_for('usuarios.nuevo_usuario'))
    return render_template('usuarios/nuevo_usuario.html', form=form)

@usuarios_bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@require_any_role('super_admin', 'admin')
def editar_usuario(id):
    usuario = db.session.get(User, id)
    if not usuario:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('usuarios.listar_usuarios'))
    form = UsuarioForm(obj=usuario)
    if form.validate_on_submit():
        usuario.name = form.name.data
        usuario.username = form.username.data
        usuario.email = form.email.data
        usuario.role = form.role.data
        usuario.is_active = form.is_active.data
        if form.password.data:
            usuario.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('usuarios.listar_usuarios'))
    return render_template('usuarios/editar_usuario.html', form=form, usuario=usuario)

    
        # ELIMINAR USUARIOS
@usuarios_bp.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
@require_delete_permission()
def eliminar_usuario(id):
    usuario = db.session.get(User, id)
    if not usuario:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('usuarios.listar_usuarios'))

    try:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuario eliminado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar usuario: {str(e)}", "danger")

    return redirect(url_for('usuarios.listar_usuarios'))

@usuarios_bp.route('/', methods=['GET'])
@login_required
@require_any_role('super_admin', 'admin')
def lista_usuarios():
    usuarios = get_usuarios_filtrados_por_rol()
    return render_template('usuarios/listar_usuarios.html', usuarios=usuarios)


