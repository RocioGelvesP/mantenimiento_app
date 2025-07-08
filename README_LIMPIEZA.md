# 🧹 Scripts de Limpieza del Sistema de Mantenimiento

Este conjunto de scripts permite limpiar completamente la base de datos del sistema de mantenimiento, preservando solo los usuarios autorizados.

## 📋 Scripts Disponibles

### 1. `limpieza_completa_sistema.py` (RECOMENDADO)
**Script principal que ejecuta la limpieza completa del sistema**
- Limpia la base de datos
- Limpia archivos de uploads
- Muestra estado antes y después
- Confirmaciones de seguridad

### 2. `limpiar_base_datos.py`
**Solo limpia la base de datos**
- Elimina todos los datos excepto usuarios autorizados
- Preserva usuarios con roles: super_admin, admin, supervisor, tecnico, user

### 3. `limpiar_archivos_uploads.py`
**Solo limpia archivos de uploads**
- Elimina imágenes y documentos no referenciados
- Libera espacio en disco

## 🚀 Cómo Usar

### Opción 1: Limpieza Completa (Recomendada)

```bash
python limpieza_completa_sistema.py
```

Este script:
1. Muestra el estado actual de la base de datos
2. Solicita confirmación doble
3. Limpia la base de datos
4. Limpia archivos de uploads
5. Muestra el estado final

### Opción 2: Limpieza Individual

```bash
# Solo limpiar base de datos
python limpiar_base_datos.py

# Solo limpiar archivos
python limpiar_archivos_uploads.py
```

## ⚠️ ADVERTENCIAS IMPORTANTES

### 🔴 ACCIÓN IRREVERSIBLE
- **NO se puede deshacer** la limpieza
- **NO hay backup automático**
- **Se pierden TODOS los datos** excepto usuarios autorizados

### 📊 Datos que se Eliminan
- ✅ **Todos los equipos** y sus datos
- ✅ **Todos los mantenimientos** programados
- ✅ **Todas las empresas**
- ✅ **Todas las cartas de lubricación**
- ✅ **Todo el historial** de cambios
- ✅ **Todo el historial** de equipos
- ✅ **Todos los motores** de equipos
- ✅ **Todos los equipos** de medición
- ✅ **Todos los usuarios** no autorizados
- ✅ **Todos los archivos** de uploads

### ✅ Datos que se Preservan
- 👥 **Usuarios con roles**: super_admin, admin, supervisor, tecnico, user
- 🔐 **Credenciales** de acceso
- 🏗️ **Estructura** de la base de datos

## 🔧 Antes de Ejecutar

### 1. Hacer Backup (OBLIGATORIO)
```bash
# Crear copia de seguridad de la base de datos
cp instance/mantenimiento.db instance/mantenimiento_backup_$(date +%Y%m%d_%H%M%S).db

# Crear copia de seguridad de archivos
cp -r static/uploads static/uploads_backup_$(date +%Y%m%d_%H%M%S)
```

### 2. Verificar Usuarios
Asegúrate de que existan usuarios con los roles necesarios:
- super_admin
- admin
- supervisor
- tecnico
- user

### 3. Detener la Aplicación
```bash
# Detener cualquier instancia en ejecución
# Ctrl+C en la terminal donde corre la aplicación
```

## 📋 Proceso de Limpieza

### Paso 1: Confirmación
El script solicita confirmación doble:
1. Primera confirmación: `SI`
2. Segunda confirmación: `CONFIRMO`

### Paso 2: Limpieza de Base de Datos
Elimina en orden correcto (respetando foreign keys):
1. Mantenimientos programados
2. Historial de cambios
3. Motores de equipos
4. Equipos de medición
5. Cartas de lubricación
6. Historial de equipos
7. Equipos
8. Empresas
9. Usuarios no autorizados

### Paso 3: Limpieza de Archivos
Elimina archivos no referenciados:
- Imágenes de equipos
- Documentos de equipos
- Imágenes de lubricación
- Otros archivos subidos

### Paso 4: Verificación Final
Muestra el estado final:
- Conteo de registros por tabla
- Lista de usuarios preservados
- Resumen de archivos eliminados

## 🔍 Verificación Post-Limpieza

### 1. Verificar Base de Datos
```bash
python check_db.py
```

### 2. Verificar Usuarios
```bash
python probar_permisos.py
```

### 3. Iniciar Aplicación
```bash
python app.py
```

### 4. Probar Acceso
- Iniciar sesión con usuarios preservados
- Verificar que no hay datos residuales
- Confirmar que el sistema funciona correctamente

## 🛠️ Solución de Problemas

### Error: "No module named 'app'"
```bash
# Asegúrate de estar en el directorio correcto
cd /ruta/a/mantenimiento_app
```

### Error: "Database is locked"
```bash
# Detener la aplicación si está corriendo
# Cerrar cualquier conexión a la base de datos
```

### Error: "Permission denied"
```bash
# Verificar permisos de escritura
chmod +x limpieza_completa_sistema.py
```

### Rollback Automático
Si ocurre un error durante la limpieza:
- Se ejecuta `db.session.rollback()` automáticamente
- Los datos NO se pierden
- Revisar el mensaje de error
- Intentar nuevamente

## 📞 Soporte

Si encuentras problemas:
1. Revisar los mensajes de error
2. Verificar que tienes permisos de escritura
3. Asegurar que la aplicación no está corriendo
4. Hacer backup antes de intentar nuevamente

## 🎯 Casos de Uso

### Caso 1: Reinicio Completo del Sistema
```bash
python limpieza_completa_sistema.py
```

### Caso 2: Solo Limpiar Datos de Prueba
```bash
python limpiar_base_datos.py
```

### Caso 3: Liberar Espacio en Disco
```bash
python limpiar_archivos_uploads.py
```

## 📝 Notas Importantes

- **Siempre hacer backup** antes de ejecutar
- **Verificar usuarios** que se preservarán
- **Detener la aplicación** antes de limpiar
- **Probar el sistema** después de la limpieza
- **Mantener copias de seguridad** por seguridad

---

**⚠️ RECUERDA: Esta acción es IRREVERSIBLE. Una vez ejecutada, NO se pueden recuperar los datos eliminados.** 