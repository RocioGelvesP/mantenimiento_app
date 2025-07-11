#!/bin/bash

# Script de instalación completa para producción
# Ejecutar como root: sudo bash instalar_produccion.sh

echo "=========================================="
echo "  INSTALACIÓN COMPLETA DE PRODUCCIÓN"
echo "  Sistema de Mantenimiento"
echo "=========================================="

# Configuración
APP_DIR="/opt/mantenimiento_app"
REPO_URL="https://github.com/tu-usuario/mantenimiento_app.git"  # Cambiar por tu repo
SERVICE_USER="www-data"

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# Función para logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Función para manejo de errores
error_exit() {
    log "ERROR: $1"
    echo "ERROR: $1"
    exit 1
}

# 1. Actualizar sistema
log "1. Actualizando sistema..."
apt update && apt upgrade -y || error_exit "Error al actualizar sistema"

# 2. Instalar dependencias del sistema
log "2. Instalando dependencias del sistema..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    sqlite3 \
    curl \
    wget \
    unzip \
    supervisor \
    ufw \
    certbot \
    python3-certbot-nginx \
    || error_exit "Error al instalar dependencias"

# 3. Crear usuario del servicio
log "3. Creando usuario del servicio..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$APP_DIR" "$SERVICE_USER"
    log "Usuario $SERVICE_USER creado"
else
    log "Usuario $SERVICE_USER ya existe"
fi

# 4. Crear directorio de la aplicación
log "4. Creando directorio de la aplicación..."
mkdir -p "$APP_DIR"
chown $SERVICE_USER:$SERVICE_USER "$APP_DIR"

# 5. Clonar repositorio
log "5. Clonando repositorio..."
cd "$APP_DIR" || error_exit "No se pudo cambiar al directorio: $APP_DIR"

if [ -d ".git" ]; then
    log "Repositorio ya existe, actualizando..."
    git pull origin main || error_exit "Error al actualizar repositorio"
else
    log "Clonando repositorio desde: $REPO_URL"
    git clone "$REPO_URL" . || error_exit "Error al clonar repositorio"
fi

# 6. Crear entorno virtual
log "6. Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv || error_exit "Error al crear entorno virtual"
fi

# 7. Activar entorno virtual e instalar dependencias
log "7. Instalando dependencias Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || error_exit "Error al instalar dependencias Python"

# 8. Configurar permisos
log "8. Configurando permisos..."
chown -R $SERVICE_USER:$SERVICE_USER "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod 644 "$APP_DIR"/*.py
chmod 644 "$APP_DIR"/*.txt
chmod 644 "$APP_DIR"/*.ini

# 9. Crear directorios necesarios
log "9. Creando directorios necesarios..."
mkdir -p "$APP_DIR/static/uploads"
mkdir -p "$APP_DIR/instance"
mkdir -p /var/log/mantenimiento_app
mkdir -p /opt/backups

chown -R $SERVICE_USER:$SERVICE_USER "$APP_DIR/static/uploads"
chown -R $SERVICE_USER:$SERVICE_USER "$APP_DIR/instance"
chown -R $SERVICE_USER:$SERVICE_USER /var/log/mantenimiento_app
chown -R $SERVICE_USER:$SERVICE_USER /opt/backups

# 10. Inicializar base de datos
log "10. Inicializando base de datos..."
cd "$APP_DIR"
source venv/bin/activate

if [ ! -f "instance/mantenimiento.db" ]; then
    python create_db.py || error_exit "Error al crear base de datos"
    log "Base de datos creada"
else
    log "Base de datos ya existe"
fi

# 11. Ejecutar migraciones
log "11. Ejecutando migraciones..."
if [ -f "alembic.ini" ] && [ -d "migrations" ]; then
    alembic upgrade head || error_exit "Error al ejecutar migraciones"
    log "Migraciones completadas"
fi

# 12. Configurar firewall
log "12. Configurando firewall..."
ufw --force enable
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 5000  # Puerto de desarrollo (opcional)
log "Firewall configurado"

# 13. Configurar servicio systemd
log "13. Configurando servicio systemd..."
if [ -f "configurar_servicio.sh" ]; then
    bash configurar_servicio.sh || error_exit "Error al configurar servicio"
else
    log "Script de configuración de servicio no encontrado"
fi

# 14. Configurar Nginx
log "14. Configurando Nginx..."
if [ -f "configurar_nginx.sh" ]; then
    bash configurar_nginx.sh || error_exit "Error al configurar Nginx"
else
    log "Script de configuración de Nginx no encontrado"
fi

# 15. Configurar actualizaciones automáticas
log "15. Configurando actualizaciones automáticas..."
cat > /etc/cron.d/mantenimiento_app << EOF
# Actualización automática diaria a las 2:00 AM
0 2 * * * root cd $APP_DIR && bash actualizar_produccion.sh >> /var/log/mantenimiento_app/cron.log 2>&1

# Limpieza de logs semanal (domingos a las 3:00 AM)
0 3 * * 0 root find /var/log/mantenimiento_app -name "*.log" -mtime +30 -delete
EOF

# 16. Configurar monitoreo básico
log "16. Configurando monitoreo básico..."
cat > /etc/systemd/system/mantenimiento_app_monitor.service << EOF
[Unit]
Description=Monitor de Mantenimiento App
After=network.target

[Service]
Type=oneshot
User=root
ExecStart=/bin/bash -c 'if ! pgrep -f "python.*app.py" > /dev/null; then systemctl restart mantenimiento_app; fi'

[Install]
WantedBy=multi-user.target
EOF

# Crear timer para el monitor
cat > /etc/systemd/system/mantenimiento_app_monitor.timer << EOF
[Unit]
Description=Monitor de Mantenimiento App Timer
Requires=mantenimiento_app_monitor.service

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable mantenimiento_app_monitor.timer
systemctl start mantenimiento_app_monitor.timer

# 17. Verificar instalación
log "17. Verificando instalación..."

# Verificar servicios
if systemctl is-active --quiet nginx; then
    log "✅ Nginx está ejecutándose"
else
    log "❌ Nginx no está ejecutándose"
fi

if systemctl is-active --quiet mantenimiento_app; then
    log "✅ Servicio de la aplicación está ejecutándose"
else
    log "❌ Servicio de la aplicación no está ejecutándose"
fi

# Verificar puertos
if netstat -tlnp | grep -q ":80 "; then
    log "✅ Puerto 80 está abierto"
else
    log "❌ Puerto 80 no está abierto"
fi

if netstat -tlnp | grep -q ":443 "; then
    log "✅ Puerto 443 está abierto"
else
    log "❌ Puerto 443 no está abierto"
fi

# 18. Información final
echo ""
echo "=========================================="
echo "  INSTALACIÓN COMPLETADA"
echo "=========================================="
echo "✅ Sistema instalado en: $APP_DIR"
echo "✅ Usuario del servicio: $SERVICE_USER"
echo "✅ Servicios configurados:"
echo "   - Nginx (proxy reverso)"
echo "   - Systemd (mantenimiento_app)"
echo "   - Firewall (UFW)"
echo "   - Monitor automático"
echo ""
echo "📋 Comandos útiles:"
echo "- Ver estado: systemctl status mantenimiento_app"
echo "- Ver logs: journalctl -u mantenimiento_app -f"
echo "- Actualizar: cd $APP_DIR && bash actualizar_produccion.sh"
echo "- Reiniciar: systemctl restart mantenimiento_app"
echo "- Ver logs Nginx: tail -f /var/log/nginx/mantenimiento_app_*.log"
echo ""
echo "🌐 Acceso a la aplicación:"
echo "- HTTP: http://$(hostname -I | awk '{print $1}')"
echo "- HTTPS: https://$(hostname -I | awk '{print $1}') (si SSL está configurado)"
echo ""
echo "🔧 Configuración adicional:"
echo "1. Ajusta el dominio en /etc/nginx/sites-available/mantenimiento_app"
echo "2. Configura certificados SSL con: certbot --nginx"
echo "3. Ajusta la configuración de la aplicación en config.py"
echo ""

log "Instalación completada exitosamente" 