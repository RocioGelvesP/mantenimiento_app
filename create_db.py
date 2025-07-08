# create_db.py

from app import app
from models import db, User
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Eliminar todas las tablas existentes
        db.drop_all()
        # Crear todas las tablas
        db.create_all()
        print("✔ Base de datos y tablas creadas correctamente.")

        # Crear usuario admin por defecto
        admin_username = 'admin'
        admin_password = 'admin'
        admin_email = 'admin@example.com'

        new_admin = User(
            username=admin_username,
            email=admin_email,
            password=generate_password_hash(admin_password),
            role='admin'
        )
        db.session.add(new_admin)
        db.session.commit()
        print(f"🛠 Usuario administrador '{admin_username}' creado.")

if __name__ == '__main__':
    init_db()
