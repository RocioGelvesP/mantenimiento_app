#!/bin/bash

# Script de actualización para Docker
# Ejecutar en el servidor de producción

echo "=========================================="
echo "  ACTUALIZACIÓN DOCKER - PRODUCCIÓN"
echo "  Sistema de Mantenimiento"
echo "  Fecha: $(date)"
echo "=========================================="

# Configuración
APP_DIR="/opt/mantenimiento_app"  # Ajustar según tu ruta
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/mantenimiento_app/docker_update_$(date +%Y%m%d_%H%M%S).log"

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
if [ ! -d "$APP_DIR" ]; then
    error_exit "Directorio de la aplicación no encontrado: $APP_DIR"
fi

cd "$APP_DIR" || error_exit "No se pudo cambiar al directorio: $APP_DIR"

log "Iniciando actualización Docker..."

# 1. Crear backup de la base de datos
log "1. Creando backup de la base de datos..."
mkdir -p "$BACKUP_DIR"

# Backup de la base de datos desde el contenedor
if docker-compose exec -T app sqlite3 instance/mantenimiento.db ".backup '/tmp/backup_$(date +%Y%m%d_%H%M%S).sql'" 2>/dev/null; then
    docker cp $(docker-compose ps -q app):/tmp/backup_$(date +%Y%m%d_%H%M%S).sql "$BACKUP_DIR/"
    log "Backup creado exitosamente"
else
    log "ADVERTENCIA: No se pudo crear backup de la base de datos"
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

# 8. Detener contenedores
log "5. Deteniendo contenedores Docker..."
docker-compose down || error_exit "Error al detener contenedores"

# 9. Reconstruir imágenes
log "6. Reconstruyendo imágenes Docker..."
docker-compose build --no-cache || error_exit "Error al reconstruir imágenes"

# 10. Levantar contenedores
log "7. Levantando contenedores Docker..."
docker-compose up -d || error_exit "Error al levantar contenedores"

# 11. Esperar a que los contenedores estén listos
log "8. Esperando a que los contenedores estén listos..."
sleep 10

# 12. Verificar que los contenedores estén funcionando
log "9. Verificando estado de los contenedores..."
if docker-compose ps | grep -q "Up"; then
    log "Contenedores están ejecutándose correctamente"
else
    error_exit "Los contenedores no están ejecutándose"
fi

# 13. Ejecutar migraciones si es necesario
log "10. Ejecutando migraciones de base de datos..."
if [ -f "alembic.ini" ] && [ -d "migrations" ]; then
    docker-compose exec -T app alembic upgrade head || log "ADVERTENCIA: Error en migraciones"
    log "Migraciones completadas"
fi

# 14. Verificar que la aplicación esté respondiendo
log "11. Verificando que la aplicación esté respondiendo..."
sleep 5

# Intentar hacer una petición HTTP a la aplicación
if curl -f http://localhost:5000 > /dev/null 2>&1; then
    log "La aplicación está respondiendo correctamente"
else
    log "ADVERTENCIA: La aplicación no responde en localhost:5000"
    log "Verificando logs del contenedor..."
    docker-compose logs app --tail=20
fi

# 15. Limpiar imágenes no utilizadas
log "12. Limpiando imágenes Docker no utilizadas..."
docker image prune -f || log "ADVERTENCIA: Error al limpiar imágenes"

# 16. Información final
log "=========================================="
log "ACTUALIZACIÓN DOCKER COMPLETADA EXITOSAMENTE"
log "=========================================="
log "Rama: $CURRENT_BRANCH"
log "Commit anterior: $CURRENT_COMMIT"
log "Commit actual: $(git rev-parse HEAD)"

echo ""
echo "=========================================="
echo "  ACTUALIZACIÓN DOCKER COMPLETADA"
echo "=========================================="
echo "✅ La aplicación ha sido actualizada exitosamente"
echo "📋 Log de la actualización: $LOG_FILE"
echo "🔄 Commit actual: $(git rev-parse HEAD)"
echo "🐳 Contenedores:"
docker-compose ps
echo ""
echo "📋 Comandos útiles:"
echo "- Ver logs: docker-compose logs -f"
echo "- Ver estado: docker-compose ps"
echo "- Reiniciar: docker-compose restart"
echo "- Ver logs específicos: docker-compose logs -f app"
echo "" 