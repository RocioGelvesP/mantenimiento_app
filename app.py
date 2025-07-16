from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask.cli import with_appcontext
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db, User, Equipo, MotorEquipo, Programado, MaintenanceRecord, Company
from forms import CompanyForm

# Importación de Blueprints
from routes.auth import auth_bp
from routes.equipment import equipment_bp
from routes.home import home_bp
from routes.main import main_bp  
from routes.users import usuarios_bp 
from routes.maintenance import maintenance
from routes.companies import companies_bp
from routes.lubrication import lubrication_bp
import os
from version import APP_VERSION

#Inicializa la app
app = Flask(__name__)
app.config.from_object(Config)
# Solo configurar la URI si no está ya configurada (por ejemplo, por los tests)
if not app.config.get('SQLALCHEMY_DATABASE_URI'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/administrador/mantenimiento_app/data/mantenimiento.db' # Base de datos real en produccióne datos
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Configuración de seguridad
app.config['SESSION_COOKIE_SECURE'] = False  # Cambiar a True en producción
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutos
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hora para tokens CSRF
app.config['WTF_CSRF_ENABLED'] = True

# Inicializar CSRF Protection
csrf = CSRFProtect(app)

# Inicializar base de datos y autenticación
db.init_app(app)

# Inicializa Flask-Migrate
migrate = Migrate(app, db)

# Inicializa LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_default_user():
    from werkzeug.security import generate_password_hash
    with app.app_context():
        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User(username="admin", email="admin@example.com", password=generate_password_hash("admin"))
            db.session.add(user)
            db.session.commit()
            print("Usuario por defecto creado: admin/admin")
        else:
            print("El usuario por defecto ya existe.")

# Ruta para home
# @home_bp.route('/')
# def index():
#     return render_template('home.html')

# Registro de blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(equipment_bp, url_prefix='/equipos')
app.register_blueprint(home_bp, url_prefix='/')
app.register_blueprint(main_bp)
app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
app.register_blueprint(maintenance, url_prefix='/mantenimiento')
app.register_blueprint(companies_bp)
app.register_blueprint(lubrication_bp, url_prefix='/lubricacion')

@app.context_processor
def inject_version():
    return dict(version=APP_VERSION)

# Ejecuta la app
if __name__ == '__main__':
    app.run(debug=True)
