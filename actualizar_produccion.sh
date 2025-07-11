#!/bin/bash

# Script de actualización para producción
# Autor: Sistema de Mantenimiento
# Fecha: $(date +%Y-%m-%d)

echo "=========================================="
echo "  ACTUALIZACIÓN DE PRODUCCIÓN"
echo "  Sistema de Mantenimiento"
echo "  Fecha: $(date)"
echo "=========================================="

# Configuración
REPO_DIR="/opt/mantenimiento_app"
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/mantenimiento_app/update_$(date +%Y%m%d_%H%M%S).log"

# Crear directorio de logs si no existe
mkdir -p /var/log/mantenimiento_app

# Función para logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función para manejo de errores
error_exit() {
    log "ERROR: $1"
    echo "ERROR: $1"
    exit 1
}

# Verificar si estamos en el directorio correcto
if [ ! -d "$REPO_DIR" ]; then
    error_exit "Directorio del repositorio no encontrado: $REPO_DIR"
fi

cd "$REPO_DIR" || error_exit "No se pudo cambiar al directorio: $REPO_DIR"

log "Iniciando actualización de producción..."

# 1. Crear backup de la base de datos
log "1. Creando backup de la base de datos..."
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"

if [ -f "instance/mantenimiento.db" ]; then
    sqlite3 instance/mantenimiento.db ".backup '$BACKUP_FILE'" || error_exit "Error al crear backup de la base de datos"
    log "Backup creado: $BACKUP_FILE"
else
    log "ADVERTENCIA: Base de datos no encontrada, continuando sin backup"
fi

# 2. Guardar estado actual de Git
log "2. Guardando estado actual de Git..."
CURRENT_BRANCH=$(git branch --show-current)
CURRENT_COMMIT=$(git rev-parse HEAD)
log "Rama actual: $CURRENT_BRANCH"
log "Commit actual: $CURRENT_COMMIT"

# 3. Verificar si hay cambios locales
if [ -n "$(git status --porcelain)" ]; then
    log "ADVERTENCIA: Hay cambios locales sin commitear"
    git status --porcelain
    read -p "¿Desea continuar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error_exit "Actualización cancelada por el usuario"
    fi
fi

# 4. Obtener cambios del repositorio remoto
log "3. Obteniendo cambios del repositorio remoto..."
git fetch origin || error_exit "Error al obtener cambios del repositorio"

# 5. Verificar si hay cambios para aplicar
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/$CURRENT_BRANCH)

if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
    log "No hay cambios nuevos para aplicar"
    echo "La aplicación ya está actualizada"
    exit 0
fi

log "Cambios detectados:"
git log --oneline HEAD..origin/$CURRENT_BRANCH

# 6. Aplicar cambios
log "4. Aplicando cambios..."
git pull origin $CURRENT_BRANCH || error_exit "Error al aplicar cambios"

# 7. Verificar si hay conflictos de merge
if [ -n "$(git status --porcelain)" ]; then
    log "ERROR: Conflictos de merge detectados"
    git status
    error_exit "Hay conflictos de merge que deben resolverse manualmente"
fi

# 8. Instalar/actualizar dependencias
log "5. Actualizando dependencias..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --upgrade || error_exit "Error al actualizar dependencias"
    log "Dependencias actualizadas"
fi

# 9. Ejecutar migraciones de base de datos
log "6. Ejecutando migraciones de base de datos..."
if [ -f "alembic.ini" ] && [ -d "migrations" ]; then
    alembic upgrade head || error_exit "Error al ejecutar migraciones"
    log "Migraciones completadas"
fi

# 10. Verificar sintaxis de archivos Python
log "7. Verificando sintaxis de archivos Python..."
find . -name "*.py" -exec python3 -m py_compile {} \; || error_exit "Error de sintaxis en archivos Python"

# 11. Reiniciar servicios
log "8. Reiniciando servicios..."

# Reiniciar servicio systemd si existe
if systemctl list-unit-files | grep -q "mantenimiento_app"; then
    log "Reiniciando servicio systemd..."
    systemctl restart mantenimiento_app || error_exit "Error al reiniciar servicio systemd"
    systemctl status mantenimiento_app --no-pager
fi

# Reiniciar servicio supervisor si existe
if [ -f "/etc/supervisor/conf.d/mantenimiento_app.conf" ]; then
    log "Reiniciando servicio supervisor..."
    supervisorctl restart mantenimiento_app || error_exit "Error al reiniciar servicio supervisor"
    supervisorctl status mantenimiento_app
fi

# Si no hay servicios configurados, intentar matar procesos existentes
if ! systemctl list-unit-files | grep -q "mantenimiento_app" && [ ! -f "/etc/supervisor/conf.d/mantenimiento_app.conf" ]; then
    log "No se encontraron servicios configurados, verificando procesos..."
    PIDS=$(pgrep -f "python.*app.py")
    if [ -n "$PIDS" ]; then
        log "Deteniendo procesos existentes: $PIDS"
        kill $PIDS
        sleep 2
    fi
fi

# 12. Verificar que la aplicación esté funcionando
log "9. Verificando que la aplicación esté funcionando..."
sleep 5

# Verificar si hay procesos de la aplicación ejecutándose
if pgrep -f "python.*app.py" > /dev/null; then
    log "La aplicación está ejecutándose correctamente"
else
    log "ADVERTENCIA: No se detectaron procesos de la aplicación ejecutándose"
fi

# 13. Limpiar archivos temporales
log "10. Limpiando archivos temporales..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.log" -mtime +7 -delete 2>/dev/null || true

# 14. Verificar espacio en disco
log "11. Verificando espacio en disco..."
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    log "ADVERTENCIA: Espacio en disco crítico: ${DISK_USAGE}%"
else
    log "Espacio en disco OK: ${DISK_USAGE}%"
fi

# 15. Información final
log "=========================================="
log "ACTUALIZACIÓN COMPLETADA EXITOSAMENTE"
log "=========================================="
log "Rama: $CURRENT_BRANCH"
log "Commit anterior: $CURRENT_COMMIT"
log "Commit actual: $(git rev-parse HEAD)"
log "Log de cambios:"
git log --oneline -5

echo ""
echo "=========================================="
echo "  ACTUALIZACIÓN COMPLETADA"
echo "=========================================="
echo "✅ La aplicación ha sido actualizada exitosamente"
echo "📋 Log de la actualización: $LOG_FILE"
echo "💾 Backup de BD: $BACKUP_FILE"
echo "🔄 Commit actual: $(git rev-parse HEAD)"
echo ""

# Mostrar últimos commits
echo "Últimos cambios aplicados:"
git log --oneline -5

echo ""
echo "Para verificar el estado de la aplicación:"
echo "- Revisar logs: tail -f $LOG_FILE"
echo "- Verificar procesos: ps aux | grep python"
echo "- Verificar servicios: systemctl status mantenimiento_app"
echo ""
