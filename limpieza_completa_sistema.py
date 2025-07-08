#!/usr/bin/env python3
"""
Script principal para limpieza completa del sistema de mantenimiento.
Ejecuta tanto la limpieza de la base de datos como la limpieza de archivos.
"""

import os
import sys
from datetime import datetime

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Equipo, Programado, HistorialCambio, Company, Lubricacion, MotorEquipo, EquipoMedicion, HistorialEquipo

def mostrar_estado_actual():
    """
    Muestra el estado actual de la base de datos
    """
    print("📊 ESTADO ACTUAL DE LA BASE DE DATOS:")
    print("=" * 50)
    
    with app.app_context():
        total_usuarios = User.query.count()
        total_equipos = Equipo.query.count()
        total_mantenimientos = Programado.query.count()
        total_empresas = Company.query.count()
        total_lubricacion = Lubricacion.query.count()
        total_historial = HistorialCambio.query.count()
        total_historial_equipos = HistorialEquipo.query.count()
        total_motores = MotorEquipo.query.count()
        total_medicion = EquipoMedicion.query.count()
        
        print(f"👥 Usuarios: {total_usuarios}")
        print(f"🔧 Equipos: {total_equipos}")
        print(f"🔧 Mantenimientos: {total_mantenimientos}")
        print(f"🏢 Empresas: {total_empresas}")
        print(f"🛢️ Cartas de lubricación: {total_lubricacion}")
        print(f"📝 Historial de cambios: {total_historial}")
        print(f"📝 Historial de equipos: {total_historial_equipos}")
        print(f"⚙️ Motores: {total_motores}")
        print(f"📏 Equipos de medición: {total_medicion}")
        
        # Mostrar usuarios por rol
        print(f"\n👥 USUARIOS POR ROL:")
        print("-" * 30)
        roles = ['super_admin', 'admin', 'supervisor', 'tecnico', 'user']
        for rol in roles:
            count = User.query.filter_by(role=rol).count()
            print(f"   • {rol}: {count}")
        
        # Mostrar usuarios específicos
        print(f"\n👥 USUARIOS DETALLADOS:")
        print("-" * 30)
        usuarios = User.query.all()
        for usuario in usuarios:
            print(f"   • {usuario.username} ({usuario.role}) - {usuario.name or 'Sin nombre'}")

def limpiar_base_datos():
    """
    Limpia completamente la base de datos preservando solo usuarios específicos
    """
    print("\n🧹 INICIANDO LIMPIEZA DE BASE DE DATOS")
    print("=" * 50)
    
    with app.app_context():
        try:
            # 1. Obtener usuarios a preservar
            print("📋 Identificando usuarios a preservar...")
            usuarios_preservar = User.query.filter(
                User.role.in_(['super_admin', 'admin', 'supervisor', 'tecnico', 'user'])
            ).all()
            
            print(f"✅ Se preservarán {len(usuarios_preservar)} usuarios:")
            for usuario in usuarios_preservar:
                print(f"   • {usuario.username} ({usuario.role})")
            
            # 2. Eliminar datos en orden correcto (respetando foreign keys)
            print("\n🗑️ Eliminando datos de mantenimientos...")
            mantenimientos_eliminados = Programado.query.delete()
            print(f"   ✅ {mantenimientos_eliminados} mantenimientos eliminados")
            
            print("🗑️ Eliminando historial de cambios...")
            historial_eliminado = HistorialCambio.query.delete()
            print(f"   ✅ {historial_eliminado} registros de historial eliminados")
            
            print("🗑️ Eliminando motores de equipos...")
            motores_eliminados = MotorEquipo.query.delete()
            print(f"   ✅ {motores_eliminados} motores eliminados")
            
            print("🗑️ Eliminando equipos de medición...")
            medicion_eliminados = EquipoMedicion.query.delete()
            print(f"   ✅ {medicion_eliminados} equipos de medición eliminados")
            
            print("🗑️ Eliminando cartas de lubricación...")
            lubricacion_eliminadas = Lubricacion.query.delete()
            print(f"   ✅ {lubricacion_eliminadas} cartas de lubricación eliminadas")
            
            print("🗑️ Eliminando historial de equipos...")
            historial_equipos_eliminado = HistorialEquipo.query.delete()
            print(f"   ✅ {historial_equipos_eliminado} registros de historial de equipos eliminados")
            
            print("🗑️ Eliminando equipos...")
            equipos_eliminados = Equipo.query.delete()
            print(f"   ✅ {equipos_eliminados} equipos eliminados")
            
            print("🗑️ Eliminando empresas...")
            empresas_eliminadas = Company.query.delete()
            print(f"   ✅ {empresas_eliminadas} empresas eliminadas")
            
            print("🗑️ Eliminando usuarios no autorizados...")
            usuarios_eliminados = User.query.filter(
                ~User.role.in_(['super_admin', 'admin', 'supervisor', 'tecnico', 'user'])
            ).delete()
            print(f"   ✅ {usuarios_eliminados} usuarios no autorizados eliminados")
            
            # Confirmar cambios
            db.session.commit()
            
            print("\n✅ ¡LIMPIEZA DE BASE DE DATOS COMPLETADA!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERROR durante la limpieza: {str(e)}")
            print("🔄 Se ha realizado rollback de los cambios")
            return False
    
    return True

def limpiar_archivos_uploads():
    """
    Limpia archivos de uploads que ya no están referenciados en la base de datos
    """
    print("\n🗂️ INICIANDO LIMPIEZA DE ARCHIVOS DE UPLOADS")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Directorios a limpiar
            directorios = [
                'static/uploads',
                'static/uploads/documentos',
                'static/uploads/lubricacion'
            ]
            
            archivos_eliminados = 0
            espacio_liberado = 0
            
            for directorio in directorios:
                if not os.path.exists(directorio):
                    print(f"📁 Directorio {directorio} no existe, saltando...")
                    continue
                
                print(f"\n📁 Limpiando directorio: {directorio}")
                
                # Obtener archivos en el directorio
                archivos = []
                for root, dirs, files in os.walk(directorio):
                    for file in files:
                        archivos.append(os.path.join(root, file))
                
                if not archivos:
                    print(f"   ℹ️ No hay archivos en {directorio}")
                    continue
                
                print(f"   📋 Encontrados {len(archivos)} archivos")
                
                # Verificar cada archivo
                for archivo in archivos:
                    try:
                        # Obtener el tamaño del archivo antes de eliminarlo
                        tamaño = os.path.getsize(archivo)
                        
                        # Verificar si el archivo está referenciado en la base de datos
                        archivo_referenciado = False
                        
                        # Buscar en equipos (aunque ya no deberían existir)
                        equipos_con_archivo = Equipo.query.filter(
                            (Equipo.imagen == archivo.replace('static/', '')) |
                            (Equipo.imagen_lubricacion == archivo.replace('static/', '')) |
                            (Equipo.instructivos_file == archivo.replace('static/', '')) |
                            (Equipo.estandar_seguridad_file == archivo.replace('static/', '')) |
                            (Equipo.operacion_file == archivo.replace('static/', '')) |
                            (Equipo.mecanico_file == archivo.replace('static/', '')) |
                            (Equipo.electrico_file == archivo.replace('static/', '')) |
                            (Equipo.partes_file == archivo.replace('static/', ''))
                        ).first()
                        
                        if equipos_con_archivo:
                            archivo_referenciado = True
                        
                        # Si no está referenciado, eliminarlo
                        if not archivo_referenciado:
                            os.remove(archivo)
                            archivos_eliminados += 1
                            espacio_liberado += tamaño
                            print(f"   🗑️ Eliminado: {os.path.basename(archivo)}")
                        else:
                            print(f"   ✅ Preservado: {os.path.basename(archivo)} (referenciado en BD)")
                            
                    except Exception as e:
                        print(f"   ⚠️ Error al procesar {archivo}: {str(e)}")
            
            # Convertir bytes a MB para mostrar
            espacio_liberado_mb = espacio_liberado / (1024 * 1024)
            
            print(f"\n📊 RESUMEN DE LIMPIEZA DE ARCHIVOS:")
            print("-" * 40)
            print(f"🗑️ Archivos eliminados: {archivos_eliminados}")
            print(f"💾 Espacio liberado: {espacio_liberado_mb:.2f} MB")
            
            print("\n✅ ¡LIMPIEZA DE ARCHIVOS COMPLETADA!")
            
        except Exception as e:
            print(f"\n❌ ERROR durante la limpieza de archivos: {str(e)}")
            return False
    
    return True

def confirmar_limpieza_completa():
    """
    Solicita confirmación antes de proceder con la limpieza completa
    """
    print("⚠️  ADVERTENCIA: LIMPIEZA COMPLETA DEL SISTEMA")
    print("=" * 60)
    print("Este script realizará una limpieza COMPLETA del sistema:")
    print("\n🗑️ ELIMINARÁ DE LA BASE DE DATOS:")
    print("• Todos los equipos y sus datos")
    print("• Todos los mantenimientos programados")
    print("• Todas las empresas")
    print("• Todas las cartas de lubricación")
    print("• Todo el historial de cambios")
    print("• Todo el historial de equipos")
    print("• Todos los motores de equipos")
    print("• Todos los equipos de medición")
    print("• Todos los usuarios no autorizados")
    
    print("\n🗂️ ELIMINARÁ ARCHIVOS:")
    print("• Imágenes de equipos")
    print("• Documentos de equipos")
    print("• Imágenes de lubricación")
    print("• Otros archivos subidos")
    
    print("\n✅ PRESERVARÁ:")
    print("• Usuarios con roles: super_admin, admin, supervisor, tecnico, user")
    
    print("\n" + "=" * 60)
    print("⚠️  ESTA ACCIÓN ES IRREVERSIBLE")
    confirmacion = input("¿Estás seguro de que deseas continuar? (escribe 'SI' para confirmar): ")
    
    if confirmacion.upper() != 'SI':
        print("❌ Operación cancelada por el usuario")
        return False
    
    # Segunda confirmación
    print("\n⚠️  ÚLTIMA ADVERTENCIA")
    print("Esta acción NO se puede deshacer.")
    print("Se eliminarán TODOS los datos del sistema.")
    confirmacion_final = input("¿Estás completamente seguro? (escribe 'CONFIRMO' para continuar): ")
    
    if confirmacion_final.upper() != 'CONFIRMO':
        print("❌ Operación cancelada por el usuario")
        return False
    
    return True

def main():
    """
    Función principal que ejecuta la limpieza completa
    """
    print("🧹 SCRIPT DE LIMPIEZA COMPLETA DEL SISTEMA")
    print("=" * 60)
    print(f"📅 Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Directorio: {os.getcwd()}")
    
    # Mostrar estado actual
    mostrar_estado_actual()
    
    if confirmar_limpieza_completa():
        print("\n🚀 Iniciando proceso de limpieza completa...")
        
        # Paso 1: Limpiar base de datos
        print("\n" + "=" * 60)
        print("PASO 1: LIMPIEZA DE BASE DE DATOS")
        print("=" * 60)
        
        if not limpiar_base_datos():
            print("\n❌ Error durante la limpieza de la base de datos")
            sys.exit(1)
        
        # Paso 2: Limpiar archivos
        print("\n" + "=" * 60)
        print("PASO 2: LIMPIEZA DE ARCHIVOS")
        print("=" * 60)
        
        if not limpiar_archivos_uploads():
            print("\n❌ Error durante la limpieza de archivos")
            sys.exit(1)
        
        # Mostrar estado final
        print("\n" + "=" * 60)
        print("ESTADO FINAL DEL SISTEMA")
        print("=" * 60)
        mostrar_estado_actual()
        
        print("\n🎉 ¡LIMPIEZA COMPLETA EXITOSAMENTE!")
        print("=" * 60)
        print("✅ La base de datos ha sido limpiada completamente")
        print("✅ Los archivos de uploads han sido limpiados")
        print("✅ Solo se preservaron los usuarios autorizados")
        print("✅ El sistema está listo para un nuevo inicio")
        
    else:
        print("\n❌ Proceso cancelado")
        sys.exit(0)

if __name__ == "__main__":
    main() 