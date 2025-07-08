from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import Company, db, get_or_404
from forms import CompanyForm
from utils import require_any_role, require_delete_permission

companies_bp = Blueprint('companies', __name__)

@companies_bp.route('/companies')
@login_required
@require_any_role('super_admin', 'admin', 'supervisor')
def lista():
    companies = Company.query.all()
    return render_template('companies/lista.html', companies=companies)

@companies_bp.route('/companies/nueva', methods=['GET', 'POST'])
@login_required
@require_any_role('super_admin', 'admin', 'supervisor')
def nueva():
    form = CompanyForm()
    if form.validate_on_submit():
        company = Company(
            nombre=form.nombre.data,
            nit=form.nit.data,
            tipo_empresa=form.tipo_empresa.data,
            direccion=form.direccion.data,
            telefono=form.telefono.data,
            email=form.email.data,
            contacto=form.contacto.data,
            activo=form.activo.data
        )
        db.session.add(company)
        db.session.commit()
        flash('Empresa creada exitosamente', 'success')
        return redirect(url_for('companies.lista'))
    return render_template('companies/nueva.html', form=form, modo_edicion=False)

@companies_bp.route('/companies/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@require_any_role('super_admin', 'admin', 'supervisor')
def editar(id):
    company = get_or_404(Company, id)
    form = CompanyForm(obj=company)
    if form.validate_on_submit():
        company.nombre = form.nombre.data
        company.nit = form.nit.data
        company.tipo_empresa = form.tipo_empresa.data
        company.direccion = form.direccion.data
        company.telefono = form.telefono.data
        company.email = form.email.data
        company.contacto = form.contacto.data
        company.activo = form.activo.data
        db.session.commit()
        flash('Empresa actualizada exitosamente', 'success')
        return redirect(url_for('companies.lista'))
    return render_template('companies/nueva.html', form=form, modo_edicion=True)

@companies_bp.route('/companies/eliminar/<int:id>', methods=['POST'])
@login_required
@require_delete_permission()
def eliminar(id):
    company = get_or_404(Company, id)
    
    # Verificar si hay equipos asociados
    if company.equipos:
        flash('No se puede eliminar la empresa porque tiene equipos asociados', 'error')
        return redirect(url_for('companies.lista'))
    
    # Verificar si hay mantenimientos asociados
    if company.mantenimientos:
        flash('No se puede eliminar la empresa porque tiene mantenimientos asociados', 'error')
        return redirect(url_for('companies.lista'))
    
    try:
        db.session.delete(company)
        db.session.commit()
        flash('Empresa eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la empresa: {str(e)}', 'error')
    
    return redirect(url_for('companies.lista')) 