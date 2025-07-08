#!/usr/bin/env python3
"""
Script para limpiar toda la base de datos excepto el superadmin y reiniciar los contadores de autoincremento.
Ejecutar con: python limpieza_total_bd.py
"""

from app import app, db
from models import Programado, Equipo, Company, HistorialCambio, User
from sqlalchemy import text

def limpieza_total_bd():
    with app.app_context():
        print("🧹 LIMPIEZA TOTAL DE LA BASE DE DATOS")
        print("=" * 50)
        
        # Eliminar todos los registros de tablas relacionadas
        print("Eliminando historial de cambios...")
        HistorialCambio.query.delete()
        print("Eliminando mantenimientos...")
        Programado.query.delete()
        print("Eliminando equipos...")
        Equipo.query.delete()
        print("Eliminando empresas...")
        Company.query.delete()
        db.session.commit()
        
        # Eliminar todos los usuarios excepto el superadmin
        print("Eliminando usuarios (excepto superadmin)...")
        superadmins = User.query.filter_by(role='super_admin').all()
        superadmin_ids = [u.id for u in superadmins]
        User.query.filter(~User.id.in_(superadmin_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        # Reiniciar los contadores de autoincremento (solo para SQLite)
        print("Reiniciando contadores de autoincremento...")
        tablas = ['programado', 'equipo', 'company', 'historial_cambio']
        for tabla in tablas:
            db.session.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{tabla}'"))
        db.session.commit()
        
        print("\n✅ Base de datos limpia. Solo queda el superadmin en la tabla de usuarios.")
        print("Puedes empezar a trabajar con una base limpia y los IDs reiniciados.")

if __name__ == '__main__':
    limpieza_total_bd() 