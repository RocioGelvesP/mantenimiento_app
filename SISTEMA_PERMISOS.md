# Sistema de Gestión de Usuarios y Permisos

## Descripción General

Se ha implementado un sistema completo de gestión de usuarios y permisos basado en roles para la aplicación de mantenimiento. El sistema define roles claros y restringe acciones según el rol del usuario, con especial énfasis en la seguridad de eliminación de registros.

## Roles Definidos

### 1. **Super Admin** (Super Administrador)
- **Acceso completo** a todas las funciones del sistema
- **ÚNICO** que puede eliminar registros (usuarios, equipos, empresas, mantenimientos, cartas de lubricación)
- Puede gestionar usuarios, equipos, empresas, mantenimientos y cartas de lubricación
- Puede ver y gestionar todos los usuarios incluyendo otros administradores
- **Permisos especiales**: Solo este rol puede eliminar registros del sistema

### 2. **Admin** (Administrador)
- **Acceso completo** a todas las funciones del sistema
- Puede gestionar usuarios, equipos, empresas, mantenimientos y cartas de lubricación
- Puede ver reportes y estadísticas completas
- **NO puede** eliminar registros (restricción de seguridad)

### 3. **Supervisor**
- Puede gestionar equipos, empresas, mantenimientos y cartas de lubricación
- Puede crear, editar equipos, empresas y cartas de lubricación
- Puede programar y gestionar mantenimientos
- Puede ver reportes de equipos sin mantenimientos preventivos
- **NO puede** gestionar usuarios
- **NO puede** eliminar registros (restricción de seguridad)

### 4. **Técnico**
- Solo puede ver y editar mantenimientos **asignados a él**
- Puede ver equipos que tienen mantenimientos asignados a él
- Puede ver cartas de lubricación de equipos
- Puede registrar tiempo y completar mantenimientos
- **No puede** gestionar equipos, empresas, usuarios o cartas de lubricación
- **No puede** eliminar registros

### 5. **User** (Usuario Regular)
- Acceso muy limitado
- Solo puede ver datos básicos
- **No puede** realizar acciones de gestión
- **No puede** eliminar registros

## Funcionalidades Implementadas

### 🔐 Decoradores de Permisos

Se han creado decoradores personalizados en `utils.py`:

- `@require_role('admin')` - Requiere un rol específico
- `@require_any_role('admin', 'supervisor')` - Requiere cualquiera de los roles especificados
- `@require_delete_permission()` - Requiere permisos de eliminación (solo super_admin)

### 🔍 Funciones de Verificación

- `can_edit_mantenimiento(mantenimiento)` - Verifica si puede editar un mantenimiento
- `can_view_mantenimiento(mantenimiento)` - Verifica si puede ver un mantenimiento
- `get_mantenimientos_filtrados_por_rol()` - Filtra mantenimientos según el rol
- `get_usuarios_filtrados_por_rol()` - Filtra usuarios según el rol
- `get_equipos_filtrados_por_rol()` - Filtra equipos según el rol

### 📋 Rutas Protegidas

#### Mantenimientos (`routes/maintenance.py`)
- **Lista de mantenimientos**: Filtrada por rol
- **Editar mantenimiento**: Solo super_admin, admin, supervisor o técnico asignado
- **Eliminar mantenimiento**: Solo super_admin
- **Imprimir/Descargar**: Solo si puede ver el mantenimiento
- **Equipos sin preventivo**: Solo super_admin, admin y supervisor

#### Equipos (`routes/equipment.py`)
- **Listar equipos**: Filtrada por rol
- **Crear/Editar**: Solo super_admin, admin y supervisor
- **Eliminar**: Solo super_admin
- **Importar/Exportar**: Solo super_admin, admin y supervisor
- **Historial**: Solo super_admin, admin y supervisor

#### Cartas de Lubricación (`routes/lubrication.py`)
- **Lista general**: Solo super_admin, admin y supervisor
- **Ver cartas de equipo**: super_admin, admin, supervisor y técnico
- **Crear carta**: Solo super_admin, admin y supervisor
- **Editar carta**: Solo super_admin, admin y supervisor
- **Eliminar carta**: Solo super_admin
- **Imprimir cartas**: super_admin, admin, supervisor y técnico

#### Usuarios (`routes/users.py`)
- **Todas las funciones**: Solo super_admin y admin
- **Eliminar usuarios**: Solo super_admin

#### Empresas (`routes/companies.py`)
- **Todas las funciones**: Solo super_admin, admin y supervisor
- **Eliminar empresas**: Solo super_admin

### 🎨 Interfaz de Usuario

#### Plantillas Actualizadas
- **Navegación**: Enlaces mostrados/ocultados según el rol
- **Botones de acción**: Mostrados/ocultados según permisos
- **Botones de eliminar**: Solo visibles para super_admin
- **Alertas**: Solo visibles para roles autorizados
- **Menú principal**: Botón de cartas de lubricación solo para super_admin, admin y supervisor

## Cómo Usar el Sistema

### 1. Crear Usuarios de Prueba

Ejecutar los scripts para crear usuarios con diferentes roles:

```bash
# Crear usuarios básicos
python crear_usuarios_roles.py

# Crear Super Administrador
python crear_usuario_personalizado.py
```

### 2. Credenciales de Acceso

- **Super Admin**: `superadmin` / `superadmin123`
- **Admin**: `admin` / `admin123`
- **Supervisor**: `supervisor` / `supervisor123`
- **Técnico**: `tecnico` / `tecnico123`
- **User**: `user` / `user123`

### 3. Probar Permisos

1. Iniciar sesión con diferentes usuarios
2. Verificar que solo aparezcan las funciones permitidas
3. Verificar que solo el super_admin vea botones de eliminar
4. Intentar acceder a rutas restringidas (deberían redirigir con mensaje de error)

## Estructura de Archivos Modificados

### Archivos Principales
- `utils.py` - Funciones de permisos y decoradores
- `models.py` - Modelo User con métodos de verificación de roles
- `routes/maintenance.py` - Rutas de mantenimiento con permisos
- `routes/equipment.py` - Rutas de equipos con permisos
- `routes/lubrication.py` - Rutas de cartas de lubricación con permisos
- `routes/users.py` - Rutas de usuarios con permisos
- `routes/companies.py` - Rutas de empresas con permisos

### Plantillas Actualizadas
- `templates/maintenance/lista.html` - Botones de eliminar solo para super_admin
- `templates/equipos/listar_equipos.html` - Botones de eliminar solo para super_admin
- `templates/companies/lista.html` - Botones de eliminar solo para super_admin
- `templates/usuarios/listar_usuarios.html` - Botones de eliminar solo para super_admin
- `templates/lubrication/lista_general.html` - Botones de eliminar solo para super_admin
- `templates/lubrication/cartas_equipo.html` - Botones de eliminar solo para super_admin
- `templates/home/index.html` - Navegación actualizada para incluir super_admin

### Scripts de Utilidad
- `crear_usuarios_roles.py` - Crear usuarios de prueba
- `crear_usuario_personalizado.py` - Crear super administrador
- `probar_permisos.py` - Probar el sistema de permisos
- `probar_acceso_completo.py` - Probar acceso completo del super_admin

## Seguridad de Eliminación

### 🔒 Restricciones Implementadas

1. **Solo Super Admin puede eliminar**: Todas las rutas de eliminación están protegidas con `@require_delete_permission()`
2. **Botones ocultos**: Los botones de eliminar solo se muestran para usuarios con permisos
3. **Verificación en servidor**: Doble verificación en frontend y backend
4. **Mensajes informativos**: Los usuarios sin permisos reciben mensajes claros

### 🛡️ Beneficios de Seguridad

- **Prevención de eliminaciones accidentales**: Solo usuarios autorizados pueden eliminar
- **Auditoría**: El super_admin tiene control total sobre eliminaciones
- **Integridad de datos**: Protección contra pérdida de información crítica
- **Separación de responsabilidades**: Administradores pueden gestionar pero no eliminar

## Notas Importantes

- **Super Admin es único**: Solo debe haber un usuario con este rol en el sistema
- **Creación segura**: El super_admin se crea con un script separado para mayor seguridad
- **Backup recomendado**: Antes de eliminar registros, se recomienda hacer backup
- **Logs de auditoría**: Todas las eliminaciones quedan registradas en el historial
- **Acceso completo**: El super_admin puede acceder a todos los módulos (usuarios, empresas, equipos, mantenimientos, cartas de lubricación) 