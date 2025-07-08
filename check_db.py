from app import app, db
from models import Equipo

with app.app_context():
    # Obtener el último equipo creado
    ultimo_equipo = Equipo.query.order_by(Equipo.codigo.desc()).first()
    
    if ultimo_equipo:
        print("\nDatos del último equipo creado:")
        print(f"Código: {ultimo_equipo.codigo}")
        print(f"Nombre: {ultimo_equipo.nombre}")
        print("\nEstado de los checklists:")
        print(f"Ficha Técnica: {ultimo_equipo.ficha_tecnica}")
        print(f"Hoja de Vida: {ultimo_equipo.hoja_vida}")
        print(f"Equipo/Máquina: {ultimo_equipo.equipo_maquina}")
        print(f"Preoperacional: {ultimo_equipo.preoperacional}")
        print(f"Plan de Mantenimiento: {ultimo_equipo.plan_mantenimiento}")
        print(f"Inspección de Seguridad: {ultimo_equipo.inspeccion_seguridad}")
        print(f"Procedimientos de Operación: {ultimo_equipo.procedimientos_operacion}")
        print(f"Manual de Usuario: {ultimo_equipo.manual_usuario}")
        print(f"Certificaciones: {ultimo_equipo.certificaciones}")
        print(f"Registro de Mantenimientos: {ultimo_equipo.registro_mantenimientos}")
    else:
        print("No hay equipos en la base de datos") 