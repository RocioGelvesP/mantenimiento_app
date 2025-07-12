from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # roles: super_admin, admin, supervisor, tecnico, user
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def has_role(self, role):
        if role == 'super_admin':
            return self.role == 'super_admin'
        if role == 'admin':
            return self.role in ['super_admin', 'admin']
        if role == 'supervisor':
            return self.role in ['super_admin', 'admin', 'supervisor']
        if role == 'tecnico':
            return self.role in ['super_admin', 'admin', 'supervisor', 'tecnico']
        return self.role == role
    
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    def is_admin(self):
        return self.role in ['super_admin', 'admin']
    
    def is_supervisor(self):
        return self.role in ['super_admin', 'admin', 'supervisor']
    
    def is_tecnico(self):
        return self.role in ['super_admin', 'admin', 'supervisor', 'tecnico']
    
    def can_delete(self):
        """Verifica si el usuario puede eliminar registros"""
        return self.role == 'super_admin'
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

class MaintenanceRecord(db.Model):
    codigo = db.Column(db.String(50), primary_key=True)
    equipment_name = db.Column(db.String(100), nullable=False)
    maintenance_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200), nullable=False)   

class Equipo(db.Model):
    __tablename__ = 'equipos'
    
    codigo = db.Column(db.String(50), primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    fecha_ingreso = db.Column(db.Date, nullable=True) 
    registro_nuevo = db.Column(db.Boolean, default=False)
    actualizacion = db.Column(db.Boolean, default=False)
    num_fabricacion = db.Column(db.String(100))
    fabricante = db.Column(db.String(100))
    nom_contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(100))
    propietario = db.Column(db.String(100))
    tipo_eq = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    tipo_control = db.Column(db.String(100))
    ubicacion = db.Column(db.String(100))
    clase = db.Column(db.String(100))
    marca = db.Column(db.String(100))
    referencia = db.Column(db.String(100))
    serie = db.Column(db.String(100))
    color = db.Column(db.String(100))
    altura = db.Column(db.String(100))
    largo = db.Column(db.String(100))
    ancho = db.Column(db.String(100))
    peso = db.Column(db.String(100))
    tipo_energia = db.Column(db.String(255))
    corriente = db.Column(db.String(50))
    potencia = db.Column(db.String(50))
    voltaje = db.Column(db.String(50))
    tipo_refrig = db.Column(db.String(50))
    tipo_comb = db.Column(db.String(50))
    tipo_lub = db.Column(db.String(50))
    repuestos = db.Column(db.String(50))
    estado_eq = db.Column(db.String(50))
    n_motores = db.Column(db.Integer)
    imagen = db.Column(db.String(100))
    observaciones = db.Column(db.String(150))
    hist_mtto = db.Column(db.String(150))
    funcion_maq = db.Column(db.String(150)) 
    operacion = db.Column(db.String(50))
    mecanico = db.Column(db.String(50))
    electrico = db.Column(db.String(50))
    partes = db.Column(db.String(50))
    acciones = db.Column(db.String(100))
    company_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=True)
    ficha_tecnica = db.Column(db.Boolean, default=False)
    hoja_vida = db.Column(db.Boolean, default=False)
    es_equipo = db.Column(db.Boolean, default=False)
    es_maquina = db.Column(db.Boolean, default=False)
    preoperacional = db.Column(db.Boolean, default=False)
    plan_mantenimiento = db.Column(db.Boolean, default=False)
    inspeccion_seguridad = db.Column(db.Boolean, default=False)
    procedimientos_operacion = db.Column(db.Boolean, default=False)
    manual_usuario = db.Column(db.Boolean, default=False)
    certificaciones = db.Column(db.Boolean, default=False)
    registro_mantenimientos = db.Column(db.Boolean, default=False)
    anios_operacion = db.Column(db.String(20))
    cartas_lubricacion = db.Column(db.String(20))
    imagen_lubricacion = db.Column(db.String(255))
    instructivos_link = db.Column(db.String(255))
    estandar_seguridad_link = db.Column(db.String(255))
    instructivos_file = db.Column(db.String(255))
    estandar_seguridad_file = db.Column(db.String(255))
    operacion_file = db.Column(db.String(255))
    mecanico_file = db.Column(db.String(255))
    electrico_file = db.Column(db.String(255))
    partes_file = db.Column(db.String(255))
    metodo_codificacion = db.Column(db.String(100))
    frecuencia_mantenimiento = db.Column(db.String(30))
    proceso = db.Column(db.String(100))
    centro_costos = db.Column(db.String(100))
    manuales = db.Column(db.Boolean, default=False)
    tipo_instalacion = db.Column(db.String(50))
    fecha_fabricacion = db.Column(db.String(50))
    
    # Relaciones
    company = db.relationship('Company', backref=db.backref('equipos', lazy=True))
    motores = db.relationship('MotorEquipo', backref='equipo', lazy=True, cascade='all, delete-orphan')
    mantenimientos = db.relationship('Programado', backref='equipo_mant', lazy=True)
    equipos_medicion = db.relationship('EquipoMedicion', backref='equipo', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Equipo {self.codigo} - {self.nombre}>'
    
    def set_tipo_energia(self, tipos):
        if tipos:
            self.tipo_energia = ','.join(tipos)
        else:
            self.tipo_energia = None

    def get_tipo_energia(self):
        if self.tipo_energia:
            return self.tipo_energia.split(',')
        return []

class Lubricacion(db.Model):
    __tablename__ = 'lubricacion'
    
    id = db.Column(db.Integer, primary_key=True)
    equipo_codigo = db.Column(db.String(50), db.ForeignKey('equipos.codigo'), nullable=False)
    numero = db.Column(db.Integer)
    mecanismo = db.Column(db.String(200))
    cantidad = db.Column(db.String(50))
    tipo_lubricante = db.Column(db.String(100))
    producto = db.Column(db.String(100))
    metodo_lubricacion = db.Column(db.String(100))
    frecuencia_inspeccion = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    
    # Relación con Equipo
    equipo = db.relationship('Equipo', backref=db.backref('lubricaciones', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<Lubricacion {self.id} - {self.equipo_codigo}>'

class MotorEquipo(db.Model):
    __tablename__ = 'motores_equipo'
    
    id = db.Column(db.Integer, primary_key=True)
    equipo_codigo = db.Column(db.String(50), db.ForeignKey('equipos.codigo'), nullable=False)
    nomb_Motor = db.Column(db.String(100))
    descrip_Motor = db.Column(db.String(100))
    tipo_Motor = db.Column(db.String(50))
    potencia_Motor = db.Column(db.String(50))
    voltaje_Motor = db.Column(db.String(50))
    corriente_Motor = db.Column(db.String(50))
    rpm_Motor = db.Column(db.String(50))
    eficiencia = db.Column(db.String(50))
    rotacion = db.Column(db.String(50))

class Programado(db.Model):
    __tablename__ = 'programado'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), db.ForeignKey('equipos.codigo'))
    nombre = db.Column(db.String(100), nullable=False)
    fecha_prog = db.Column(db.Date, nullable=False)
    hora = db.Column(db.String(5), nullable=True)
    servicio = db.Column(db.String(200), nullable=False)
    tipo_mantenimiento = db.Column(db.String(50), nullable=False)
    tiempo = db.Column(db.String(50))
    repuestos = db.Column(db.String(200))
    herramientas = db.Column(db.String(200))
    ubicacion = db.Column(db.String(100))
    autorizado_por = db.Column(db.String(100), nullable=True)
    estado_inicial = db.Column(db.String(50), nullable=False)
    estado_final = db.Column(db.String(50))
    motivo = db.Column(db.String(200))
    costo_rep = db.Column(db.Float, default=0.0)
    costo_herram = db.Column(db.Float, default=0.0)
    costo_mdo = db.Column(db.Float, default=0.0)
    costo_total = db.Column(db.Float, default=0.0)
    frecuencia = db.Column(db.String(50))
    prox_mtto = db.Column(db.Date)
    observaciones = db.Column(db.String(200))
    tecnico_asignado = db.Column(db.String(100))
    tecnico_realizador = db.Column(db.String(100))
    recibido_por = db.Column(db.String(100), nullable=True)
    hora_inicial = db.Column(db.DateTime)
    hora_final = db.Column(db.DateTime)
    tiempo_gastado = db.Column(db.String(50))
    company_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=True)
    company = db.relationship('Company', backref=db.backref('mantenimientos', lazy=True))
    
    def calcular_costo_total(self):
        self.costo_total = (self.costo_rep or 0.0) + (self.costo_herram or 0.0) + (self.costo_mdo or 0.0)

    def calcular_prox_mtto(self):
        if not self.fecha_prog or not self.frecuencia:
            return
        fecha = self.fecha_prog
        def sumar_meses(fecha, meses):
            mes = fecha.month - 1 + meses
            anio = fecha.year + mes // 12
            mes = mes % 12 + 1
            dia = min(fecha.day, calendar.monthrange(anio, mes)[1])
            return fecha.replace(year=anio, month=mes, day=dia)
        if self.frecuencia == 'Diario':
            delta = timedelta(days=1)
            self.prox_mtto = fecha + delta
        elif self.frecuencia == 'Semanal':
            delta = timedelta(weeks=1)
            self.prox_mtto = fecha + delta
        elif self.frecuencia == 'Quincenal':
            delta = timedelta(days=15)
            self.prox_mtto = fecha + delta
        elif self.frecuencia == 'Mensual':
            self.prox_mtto = sumar_meses(fecha, 1)
        elif self.frecuencia == 'Bimestral':
            self.prox_mtto = sumar_meses(fecha, 2)
        elif self.frecuencia == 'Trimestral':
            self.prox_mtto = sumar_meses(fecha, 3)
        elif self.frecuencia == 'Semestral':
            self.prox_mtto = sumar_meses(fecha, 6)
        elif self.frecuencia == 'Anual':
            try:
                self.prox_mtto = fecha.replace(year=fecha.year + 1)
            except ValueError:
                # Si el día no existe (29 de febrero en año no bisiesto), usar último día de febrero
                self.prox_mtto = fecha.replace(year=fecha.year + 1, day=28)
        else:
            self.prox_mtto = None

class HistorialCambio(db.Model):
    __tablename__ = 'historial_cambios'
    id = db.Column(db.Integer, primary_key=True)
    mantenimiento_id = db.Column(db.Integer, db.ForeignKey('programado.id'), nullable=False)
    usuario = db.Column(db.String(100), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    campo = db.Column(db.String(100), nullable=True)
    valor_anterior = db.Column(db.Text, nullable=True)
    valor_nuevo = db.Column(db.Text, nullable=True)
    accion = db.Column(db.String(50), nullable=False)  # 'edición', 'pausa', 'cancelación', etc.

    mantenimiento = db.relationship('Programado', backref='historial_cambios')

class Company(db.Model):
    __tablename__ = 'empresa'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=True)
    nit = db.Column(db.String(20), nullable=False)
    tipo_empresa = db.Column(db.String(20), nullable=True)  # Permitir nulos
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    contacto = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Company {self.nombre}>'

class EquipoMedicion(db.Model):
    __tablename__ = 'equipos_medicion'
    id = db.Column(db.Integer, primary_key=True)
    equipo_codigo = db.Column(db.String(50), db.ForeignKey('equipos.codigo'), nullable=False)
    codigo = db.Column(db.String(50), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(100), nullable=True)

class HistorialEquipo(db.Model):
    __tablename__ = 'historial_equipos'
    id = db.Column(db.Integer, primary_key=True)
    equipo_codigo = db.Column(db.String(50), db.ForeignKey('equipos.codigo'), nullable=False)
    fecha_cambio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tipo_cambio = db.Column(db.String(50), nullable=False)  # 'creacion', 'actualizacion', 'eliminacion'
    campo_modificado = db.Column(db.String(100), nullable=True)
    valor_anterior = db.Column(db.String(500), nullable=True)
    valor_nuevo = db.Column(db.String(500), nullable=True)
    usuario = db.Column(db.String(100), nullable=True)
    observaciones = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'<HistorialEquipo {self.id} - {self.equipo_codigo}>'

class Auditoria(db.Model):
    __tablename__ = 'auditoria'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    ip = db.Column(db.String(50), nullable=True)
    modulo = db.Column(db.String(100), nullable=False)
    accion = db.Column(db.String(100), nullable=False)
    tabla = db.Column(db.String(100), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    datos_anteriores = db.Column(db.Text, nullable=True)
    datos_nuevos = db.Column(db.Text, nullable=True)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def get_or_404(model, id):
    """
    Función helper para obtener un objeto por ID o retornar 404 si no existe.
    Similar a Flask-SQLAlchemy's get_or_404 pero compatible con SQLAlchemy puro.
    """
    from flask import abort
    obj = db.session.get(model, id)
    if obj is None:
        abort(404)
    return obj
