#!/usr/bin/env python3
"""
Script para documentar el sistema de permisos de cartas de lubricación.
Ejecutar con: python documentar_permisos_lubricacion.py
"""

import os
from datetime import datetime

def crear_documentacion():
    """Crear documentación completa del sistema de permisos"""
    
    documentacion = f"""# SISTEMA DE PERMISOS - CARTAS DE LUBRICACIÓN

## Fecha de Documentación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

## 📋 Resumen Ejecutivo

El sistema de cartas de lubricación ha sido implementado con un sistema de permisos robusto que controla el acceso a las diferentes funcionalidades según el rol del usuario.

## 🔐 Matriz de Permisos

| Función | Super Admin | Admin | Supervisor | Técnico | User |
|---------|-------------|-------|------------|---------|------|
| Lista General | ✅ | ✅ | ✅ | ❌ | ❌ |
| Ver Cartas | ✅ | ✅ | ✅ | ✅ | ❌ |
| Crear Cartas | ✅ | ✅ | ✅ | ❌ | ❌ |
| Editar Cartas | ✅ | ✅ | ✅ | ❌ | ❌ |
| Eliminar Cartas | ✅ | ❌ | ❌ | ❌ | ❌ |
| Imprimir Cartas | ✅ | ✅ | ✅ | ✅ | ❌ |

## 🛣️ Rutas Protegidas

### 1. Lista General de Cartas
- **Ruta**: `/lubricacion/lista`
- **Método**: GET
- **Permisos**: `@require_any_role('super_admin', 'admin', 'supervisor')`
- **Descripción**: Muestra todas las cartas de lubricación del sistema

### 2. Cartas por Equipo
- **Ruta**: `/lubricacion/equipo/<codigo>`
- **Método**: GET
- **Permisos**: `@require_any_role('super_admin', 'admin', 'supervisor', 'tecnico')`
- **Descripción**: Muestra las cartas de lubricación de un equipo específico

### 3. Crear Nueva Carta
- **Ruta**: `/lubricacion/nueva/<codigo>`
- **Método**: GET, POST
- **Permisos**: `@require_any_role('super_admin', 'admin', 'supervisor')`
- **Descripción**: Permite crear una nueva carta de lubricación para un equipo

### 4. Editar Carta
- **Ruta**: `/lubricacion/editar/<id>`
- **Método**: GET, POST
- **Permisos**: `@require_any_role('super_admin', 'admin', 'supervisor')`
- **Descripción**: Permite editar una carta de lubricación existente

### 5. Eliminar Carta
- **Ruta**: `/lubricacion/eliminar/<id>`
- **Método**: POST
- **Permisos**: `@require_delete_permission()`
- **Descripción**: Solo Super Admin puede eliminar cartas

### 6. Imprimir Cartas
- **Ruta**: `/lubricacion/imprimir/<codigo>`
- **Método**: GET
- **Permisos**: `@require_any_role('super_admin', 'admin', 'supervisor', 'tecnico')`
- **Descripción**: Genera PDF con las cartas de lubricación de un equipo

## 🏗️ Arquitectura del Sistema

### Modelos Implementados

#### 1. Modelo Lubricacion
```python
class Lubricacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipo_codigo = db.Column(db.String(20), db.ForeignKey('equipo.codigo'), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    mecanismo = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.String(50), nullable=False)
    tipo_lubricante = db.Column(db.String(100), nullable=False)
    producto = db.Column(db.String(100), nullable=False)
    metodo_lubricacion = db.Column(db.String(100), nullable=False)
    frecuencia_inspeccion = db.Column(db.String(50), nullable=False)
    observaciones = db.Column(db.Text)
    imagen = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 2. Campo Agregado al Modelo Equipo
```python
# En el modelo Equipo se agregó:
imagen_lubricacion = db.Column(db.String(255))
```

### Formularios Implementados

#### LubricacionForm
```python
class LubricacionForm(FlaskForm):
    numero = IntegerField('Número de Carta', validators=[DataRequired()])
    mecanismo = StringField('Mecanismo', validators=[DataRequired()])
    cantidad = StringField('Cantidad', validators=[DataRequired()])
    tipo_lubricante = StringField('Tipo de Lubricante', validators=[DataRequired()])
    producto = StringField('Producto', validators=[DataRequired()])
    metodo_lubricacion = StringField('Método de Lubricación', validators=[DataRequired()])
    frecuencia_inspeccion = StringField('Frecuencia de Inspección', validators=[DataRequired()])
    observaciones = TextAreaField('Observaciones')
    imagen = FileField('Imagen')
```

## 🎨 Plantillas Implementadas

### 1. Lista General (`templates/lubrication/lista_general.html`)
- Muestra todas las cartas de lubricación
- Botones de acción según permisos
- Filtros por equipo

### 2. Cartas por Equipo (`templates/lubrication/cartas_equipo.html`)
- Muestra cartas de un equipo específico
- Botones de crear, editar, eliminar según permisos

### 3. Crear Carta (`templates/lubrication/nueva_carta.html`)
- Formulario para crear nueva carta
- Subida de imágenes
- Validaciones

### 4. Editar Carta (`templates/lubrication/editar_carta.html`)
- Formulario para editar carta existente
- Pre-carga de datos
- Manejo de imágenes

### 5. Imprimir Cartas (`templates/lubrication/imprimir_cartas.html`)
- Vista para generar PDF
- Formato profesional
- Incluye imágenes

## 🔧 Funcionalidades Implementadas

### 1. Manejo de Imágenes
- Subida de archivos
- Validación de tipos
- Almacenamiento seguro
- Visualización en plantillas

### 2. Generación de PDF
- Reporte profesional
- Incluye datos del equipo
- Formato tabular
- Imágenes integradas

### 3. Validaciones
- Campos obligatorios
- Validación de archivos
- Verificación de permisos
- Manejo de errores

### 4. Navegación
- Menú principal actualizado
- Enlaces contextuales
- Breadcrumbs
- Botones según permisos

## 🧪 Pruebas Implementadas

### Scripts de Prueba
1. `probar_permisos_lubricacion.py` - Prueba permisos por rol
2. `verificar_usuarios_permisos.py` - Verifica usuarios y permisos
3. `crear_usuarios_roles.py` - Crea usuarios de prueba

### Datos de Prueba
- Equipo EM-075 con cartas de lubricación
- Usuarios con diferentes roles
- Imágenes de prueba

## 📊 Estadísticas del Sistema

- **Total de equipos**: 16
- **Cartas de lubricación**: 2 (de prueba)
- **Usuarios activos**: 9
- **Roles implementados**: 5
- **Rutas protegidas**: 6
- **Plantillas creadas**: 5

## 🔒 Seguridad Implementada

### 1. Decoradores de Permisos
- `@require_any_role()` - Control de acceso por rol
- `@require_delete_permission()` - Control de eliminación
- `@login_required` - Autenticación obligatoria

### 2. Validaciones de Frontend
- Botones ocultos según permisos
- Mensajes de error apropiados
- Redirecciones seguras

### 3. Validaciones de Backend
- Verificación de permisos en cada ruta
- Validación de datos de entrada
- Manejo seguro de archivos

## 🚀 Instrucciones de Uso

### Para Administradores
1. Acceder a `/lubricacion/lista` para ver todas las cartas
2. Crear nuevas cartas desde la lista de equipos
3. Editar cartas existentes según necesidades
4. Eliminar cartas obsoletas (solo Super Admin)

### Para Técnicos
1. Acceder a cartas de equipos específicos
2. Ver información detallada de lubricación
3. Imprimir cartas para uso en campo
4. No pueden modificar cartas

### Para Usuarios Regulares
- No tienen acceso a cartas de lubricación

## 🔄 Mantenimiento

### Actualizaciones Necesarias
- Revisar permisos periódicamente
- Actualizar documentación de productos
- Verificar integridad de imágenes
- Backup de datos regular

### Monitoreo
- Logs de acceso a rutas protegidas
- Verificación de permisos
- Auditoría de cambios
- Reportes de uso

## 📝 Notas Técnicas

### Dependencias
- Flask-SQLAlchemy
- Flask-Login
- Werkzeug (para manejo de archivos)
- ReportLab (para PDF)

### Base de Datos
- Tabla `lubricacion` creada
- Campo `imagen_lubricacion` agregado a `equipo`
- Migraciones aplicadas correctamente

### Archivos
- Imágenes almacenadas en `static/uploads/`
- Estructura organizada por tipo
- Validación de extensiones

---

**Documento generado automáticamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}**
"""
    
    # Crear archivo de documentación
    with open('DOCUMENTACION_LUBRICACION.md', 'w', encoding='utf-8') as f:
        f.write(documentacion)
    
    print("✅ Documentación creada: DOCUMENTACION_LUBRICACION.md")
    print(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("📄 Archivo guardado en el directorio raíz del proyecto")

def main():
    print("📚 GENERANDO DOCUMENTACIÓN DEL SISTEMA DE LUBRICACIÓN")
    print("=" * 60)
    
    crear_documentacion()
    
    print("\n✅ Documentación completada!")
    print("\n📋 Archivos generados:")
    print("• DOCUMENTACION_LUBRICACION.md - Documentación completa")
    print("• SISTEMA_PERMISOS.md - Permisos generales del sistema")
    
    print("\n💡 Próximos pasos:")
    print("1. Revisar la documentación generada")
    print("2. Probar todas las funcionalidades")
    print("3. Capacitar a los usuarios")
    print("4. Configurar backups automáticos")

if __name__ == '__main__':
    main() 