from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField, FloatField, TextAreaField, TimeField, EmailField, BooleanField, SelectMultipleField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Optional, Length, Email, NumberRange, ValidationError
from wtforms.fields import DateTimeField
import re
from flask_wtf.file import FileField, FileAllowed

def validate_password_strength(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError('La contraseña debe tener al menos 8 caracteres')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('La contraseña debe contener al menos una letra mayúscula')
    if not re.search(r'[a-z]', password):
        raise ValidationError('La contraseña debe contener al menos una letra minúscula')
    if not re.search(r'\d', password):
        raise ValidationError('La contraseña debe contener al menos un número')

def validate_equipo_sin_preventivo(form, field):
    """Validar que el equipo no tenga un mantenimiento preventivo con la misma combinación de servicio y frecuencia para el año actual"""
    from datetime import datetime
    from models import Programado
    from flask import request

    # Si el tipo de mantenimiento no es preventivo, no aplicar esta validación
    if not form.tipo_mantenimiento.data or form.tipo_mantenimiento.data != 'Preventivo':
        return

    # Si se accede desde el reporte de equipos sin preventivos, no aplicar validación
    if request.args.get('equipo') and request.args.get('equipo') == field.data:
        return

    if field.data:
        año_actual = datetime.now().year
        # Obtener servicio y frecuencia del formulario
        servicio = form.servicio.data
        frecuencia = form.frecuencia.data
        # Buscar si ya existe un preventivo con la misma combinación
        mantenimientos_existentes = Programado.query.filter(
            Programado.codigo == field.data,
            Programado.tipo_mantenimiento == 'Preventivo',
            Programado.fecha_prog >= datetime(año_actual, 1, 1),
            Programado.fecha_prog <= datetime(año_actual, 12, 31),
            Programado.servicio == servicio,
            Programado.frecuencia == frecuencia
        ).first()
        if mantenimientos_existentes:
            raise ValidationError(f'El equipo {field.data} ya tiene un mantenimiento preventivo con el servicio "{servicio}" y frecuencia "{frecuencia}" programado para el año {año_actual}.')

def validate_frecuencia(form, field):
    if form.tipo_mantenimiento.data == 'Preventivo' and (not field.data or field.data == 'Seleccionar'):
        raise ValidationError('La frecuencia es requerida para mantenimientos preventivos.')

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[
        DataRequired(message='El usuario es requerido'),
        Length(min=3, max=50, message='El usuario debe tener entre 3 y 50 caracteres')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida')
    ])
    submit = SubmitField('Iniciar Sesión')

class MantenimientoForm(FlaskForm):
    codigo = SelectField('Código', validators=[DataRequired(), validate_equipo_sin_preventivo], coerce=str)
    nombre = StringField('Nombre', validators=[DataRequired()])
    fecha_prog = DateField('Fecha Programada', validators=[DataRequired()])
    hora = TimeField('Hora', validators=[Optional()])
    servicio = StringField('Servicio', validators=[DataRequired()])
    tipo_mantenimiento = SelectField('Tipo Mantenimiento', 
                                   choices=[('', 'Seleccione un tipo'), 
					  ('Preventivo', 'Preventivo'), 
                                          ('Correctivo', 'Correctivo'),
					  ('Fabricaciones', 'Fabricaciones'),
					  ('Locativotivo', 'Locativo'),
                                          ('Predictivo', 'Predictivo'),
					  ('Poyectos', 'Proyectos')],
                                   validators=[DataRequired()])
    tiempo = StringField('Tiempo Estimado')
    repuestos = StringField('Repuestos')
    herramientas = StringField('Herramientas')
    ubicacion = StringField('Ubicación')
    autorizado_por = SelectField('Autorizado Por', validators=[Optional()], coerce=int)
    estado_inicial = SelectField('Estado', 
                               choices=[('Seleccionar', 'Seleccionar'),
                                      ('Programado', 'Programado'), 
                                      ('Asignado', 'Asignado'),
                                      ('En Proceso', 'En Proceso'),
                                      ('Completado', 'Completado'),
                                      ('Cancelado', 'Cancelado'),
                                      ('Vencido', 'Vencido')],
                               validators=[DataRequired()])
    motivo = TextAreaField('Motivo', validators=[Optional()])
    costo_rep = FloatField('Costo Repuestos', validators=[Optional()])
    costo_herram = FloatField('Costo Herramientas', validators=[Optional()])
    costo_mdo = FloatField('Costo Mano de Obra', validators=[Optional()])
    frecuencia = SelectField('Frecuencia', 
                           choices=[('Seleccionar', 'Seleccionar'),
                                  ('Diario', 'Diario'),
                                  ('Semanal', 'Semanal'),
                                  ('Quincenal', 'Quincenal'),
                                  ('Mensual', 'Mensual'),
                                  ('Bimestral', 'Bimestral'),
                                  ('Trimestral', 'Trimestral'),
                                  ('Semestral', 'Semestral'),
                                  ('Anual', 'Anual')],
                           validators=[validate_frecuencia])
    prox_mtto = DateField('Próximo Mantenimiento', validators=[Optional()])
    observaciones = TextAreaField('Observaciones')
    tecnico_asignado = SelectField('Técnico Asignado', validators=[Optional()], coerce=int)
    tecnico_realizador = StringField('Técnico Realizador', validators=[Optional()])
    recibido_por = StringField('Recibido Por', validators=[Optional()])
    hora_inicial = DateTimeField('Fecha/Hora Inicial', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    hora_final = DateTimeField('Fecha/Hora Final', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    tiempo_gastado = StringField('Tiempo Gastado')
    company_id = SelectField('Empresa', coerce=int, validators=[Optional()])
    submit = SubmitField('Guardar')

class MantenimientoEditarForm(FlaskForm):
    codigo = SelectField('Código', validators=[DataRequired()], coerce=str)
    nombre = StringField('Nombre', validators=[DataRequired()])
    fecha_prog = DateField('Fecha Programada', validators=[DataRequired()])
    hora = TimeField('Hora', validators=[Optional()])
    servicio = StringField('Servicio', validators=[DataRequired()])
    tipo_mantenimiento = SelectField('Tipo de Mantenimiento', 
                                   choices=[('Preventivo', 'Preventivo'), 
                                          ('Correctivo', 'Correctivo'),
                                          ('Fabricacion', 'Fabricacion'),
                                          ('Locativo', 'Locativo'),
                                          ('Predictivo', 'Predictivo'),
                                          ('Proyectos', 'Proyectos')],
                                   validators=[DataRequired()])
    tiempo = StringField('Tiempo Estimado')
    repuestos = StringField('Repuestos')
    herramientas = StringField('Herramientas')
    ubicacion = StringField('Ubicación')
    autorizado_por = SelectField('Autorizado Por', validators=[Optional()], coerce=int)
    estado_inicial = SelectField('Estado', 
                               choices=[('Programado', 'Programado'), 
                                      ('Asignado', 'Asignado'),
                                      ('En espera(Repuestos)', 'En espera(Repuestos)'),
                                      ('En proceso', 'En proceso'),
                                      ('Aplazado', 'Aplazado'),
                                      ('Pausado', 'Pausado'),
                                      ('Vencido', 'Vencido'),
                                      ('Completado', 'Completado'),
                                      ('Cancelado', 'Cancelado')],
                               validators=[DataRequired()])
    motivo = TextAreaField('Motivo', validators=[Optional()])
    costo_rep = FloatField('Costo Repuestos', validators=[Optional()])
    costo_herram = FloatField('Costo Herramientas', validators=[Optional()])
    costo_mdo = FloatField('Costo Mano de Obra', validators=[Optional()])
    frecuencia = SelectField('Frecuencia', 
                           choices=[('Seleccionar', 'Seleccionar'),
                                  ('Diario', 'Diario'),
                                  ('Semanal', 'Semanal'),
                                  ('Quincenal', 'Quincenal'),
                                  ('Mensual', 'Mensual'),
                                  ('Bimestral', 'Bimestral'),
                                  ('Trimestral', 'Trimestral'),
                                  ('Semestral', 'Semestral'),
                                  ('Anual', 'Anual')],
                           validators=[validate_frecuencia])
    prox_mtto = DateField('Próximo Mantenimiento', validators=[Optional()])
    observaciones = TextAreaField('Observaciones')
    tecnico_asignado = SelectField('Técnico Asignado', validators=[Optional()], coerce=int)
    tecnico_realizador = StringField('Técnico Realizador', validators=[Optional()])
    recibido_por = StringField('Recibido Por', validators=[Optional()])
    hora_inicial = DateTimeField('Fecha/Hora Inicial', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    hora_final = DateTimeField('Fecha/Hora Final', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    tiempo_gastado = StringField('Tiempo Gastado')
    company_id = SelectField('Empresa', coerce=int, validators=[Optional()])
    submit = SubmitField('Guardar')

class CompanyForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    nit = StringField('NIT', validators=[DataRequired()])
    tipo_empresa = SelectField('Tipo de Empresa', choices=[
        ('', 'Seleccione un tipo'),
        ('Interna', 'Interna'),
        ('Tercerizada', 'Tercerizada')
    ], validators=[DataRequired(message="Debe seleccionar un tipo de empresa.")])
    direccion = StringField('Dirección')
    telefono = StringField('Teléfono')
    email = StringField('Correo Electrónico', validators=[
        Length(max=100, message='El correo no puede exceder los 100 caracteres'),
        Optional(),
        Email(message='Ingrese un correo electrónico válido')
    ])
    contacto = StringField('Persona de Contacto', validators=[
        Length(max=100, message='El contacto no puede exceder los 100 caracteres')
    ])
    activo = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar')

class UsuarioForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[Optional()])
    role = SelectField('Rol', choices=[
        ('super_admin', 'Super Administrador'), 
        ('admin', 'Administrador'), 
        ('supervisor', 'Supervisor'), 
        ('tecnico', 'Técnico'), 
        ('user', 'Usuario')
    ], validators=[DataRequired()], default='user')
    is_active = BooleanField('Usuario activo', default=True)
    submit = SubmitField('Guardar')

class EquipoForm(FlaskForm):
    class Meta:
        csrf = True
    codigo = StringField('Código', validators=[DataRequired()])
    nombre = StringField('Nombre', validators=[DataRequired()])
    fecha_ingreso = DateField('Fecha de Ingreso', validators=[Optional()])
    registro_nuevo = BooleanField('Reg. Nuevo')
    actualizacion = BooleanField('Actualización')
    num_fabricacion = StringField('N° Fabricación', validators=[Optional()])
    fabricante = StringField('Fabricante', validators=[Optional()])
    nom_contacto = StringField('Nombre Contacto', validators=[Optional()])
    telefono = StringField('Teléfono', validators=[Optional()])
    propietario = StringField('Propietario', validators=[Optional()])
    tipo_eq = StringField('Tipo Equipo', validators=[Optional()])
    modelo = StringField('Modelo', validators=[Optional()])
    tipo_control = StringField('Tipo de Control', validators=[Optional()])
    ubicacion = StringField('Ubicación', validators=[Optional()])
    proceso = StringField('Proceso', validators=[Optional()])
    centro_costos = StringField('Centro de Costos', validators=[Optional()])
    clase = StringField('Clase', validators=[Optional()])
    marca = StringField('Marca', validators=[Optional()])
    referencia = StringField('Referencia', validators=[Optional()])
    serie = StringField('Serie', validators=[Optional()])
    fecha_fabricacion = StringField('Fecha de Fabricación', validators=[Optional()])
    color = StringField('Color', validators=[Optional()])
    altura = StringField('Altura', validators=[Optional()])
    largo = StringField('Largo', validators=[Optional()])
    ancho = StringField('Ancho', validators=[Optional()])
    peso = StringField('Peso', validators=[Optional()])
    tipo_energia = SelectMultipleField('Tipo de Energía', choices=[
        ('Eléctrica', 'E: Eléctrica'),
        ('Hidráulica', 'H: Hidráulica'),
        ('Neumática', 'N: Neumática'),
        ('Térmica', 'T: Térmica'),
        ('Mecánica', 'M: Mecánica'),
        ('Electrónica', 'EL: Electrónica'),
        ('Química', 'Q: Química'),
    ])
        
    corriente = StringField('Corriente', validators=[Optional()])
    potencia = StringField('Potencia Inst.', validators=[Optional()])
    voltaje = StringField('Voltaje', validators=[Optional()])
    tipo_instalacion = SelectField('Tipo de Inst. Eléctrica', choices=[
        ('Seleccionar', 'Seleccionar'),
        ('Alta Tensión', 'Alta Tensión'),
        ('Media Tensión', 'Media Tensión'),
        ('Baja Tensión', 'Baja Tensión')
    ])
    tipo_refrig = StringField('Tipo Refrigerante', validators=[Optional()])
    tipo_comb = StringField('Tipo Combustible', validators=[Optional()])
    tipo_lub = StringField('Tipo Lubricante', validators=[Optional()])
    repuestos = StringField('Repuestos', validators=[Optional()])
    estado_eq = SelectField('Estado', choices=[
        ('Seleccionar', 'Seleccionar'),
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
        ('De baja', 'De baja'),
        ('Dañado', 'Dañado'),
        ('Funcional', 'Funcional')
    ])
    n_motores = HiddenField('N° Motores', default=0)
    imagen = FileField('Imagen', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp'], 'Solo imágenes')])
    observaciones = StringField('Observaciones', validators=[Optional()])
    hist_mtto = StringField('Historial de Mantenimientos', validators=[Optional()])
    funcion_maq = StringField('Función de la Máquina', validators=[Optional()])
    operacion_file = FileField('Operación', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Solo se permiten archivos PDF y Word')])
    mecanico_file = FileField('Mecánico', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Solo se permiten archivos PDF y Word')])
    electrico_file = FileField('Eléctrico', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Solo se permiten archivos PDF y Word')])
    partes_file = FileField('Partes', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Solo se permiten archivos PDF y Word')])
    acciones = StringField('Acciones', validators=[Optional()])
    company_id = StringField('Empresa', validators=[Optional()])
    ficha_tecnica = BooleanField('Ficha técnica')
    hoja_vida = BooleanField('Hoja de vida')
    es_equipo = BooleanField('Equipo')
    es_maquina = BooleanField('Máquina')
    preoperacional = BooleanField('Preoperacional')
    plan_mantenimiento = BooleanField('Plan de mantenimiento')
    inspeccion_seguridad = BooleanField('Inspección de Seguridad')
    procedimientos_operacion = BooleanField('Procedimientos de Operación')
    manual_usuario = BooleanField('Manuales')
    certificaciones = BooleanField('Certificaciones')
    registro_mantenimientos = BooleanField('Registro de Mantenimientos')
    anios_operacion = StringField('Años de operación', validators=[Optional()])
    cartas_lubricacion = SelectField('Cartas de lubricación', choices=[('','Seleccionar'),('Tiene', 'Tiene'), ('No tiene', 'No tiene'), ('No aplica', 'No aplica')])
    imagen_lubricacion = FileField('Imagen de lubricación', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten archivos de imagen')])
    instructivos_file = FileField('Instructivo', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Solo se permiten archivos PDF y Word')])
    estandar_seguridad_file = FileField('Estándar de seguridad', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Solo se permiten archivos PDF y Word')])
    metodo_codificacion = StringField('Método de codificación', validators=[Optional()])
    frecuencia_mantenimiento = SelectField('Frecuencia de mantenimiento', 
        choices=[
            ('Seleccionar', 'Seleccionar'),
            ('Diario', 'Diario'),
            ('Semanal', 'Semanal'),
            ('Quincenal', 'Quincenal'),
            ('Mensual', 'Mensual'),
            ('Bimestral', 'Bimestral'),
            ('Trimestral', 'Trimestral'),
            ('Semestral', 'Semestral'),
            ('Anual', 'Anual')
        ],
        validators=[Optional()]
    )
    manuales = BooleanField('Manuales')
    submit = SubmitField('Guardar')

class LubricacionForm(FlaskForm):
    numero = IntegerField('Número', validators=[DataRequired()])
    mecanismo = StringField('Mecanismo', validators=[DataRequired()])
    cantidad = StringField('Cantidad', validators=[DataRequired()])
    tipo_lubricante = StringField('Tipo de lubricante', validators=[DataRequired()])
    producto = StringField('Producto', validators=[DataRequired()])
    metodo_lubricacion = StringField('Método de lubricación', validators=[DataRequired()])
    frecuencia_inspeccion = StringField('Frecuencia de inspección', validators=[DataRequired()])
    observaciones = TextAreaField('Observaciones', validators=[Optional()])
    submit = SubmitField('Guardar')

class EliminarForm(FlaskForm):
    pass

