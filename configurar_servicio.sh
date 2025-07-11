#!/bin/bash

# Script para configurar el servicio systemd en producción
# Ejecutar como root: sudo bash configurar_servicio.sh

echo "=========================================="
echo "  CONFIGURACIÓN DE SERVICIO SYSTEMD"
echo "  Sistema de Mantenimiento"
echo "=========================================="

# Configuración
APP_DIR="/opt/mantenimiento_app"
SERVICE_USER="www-data"
SERVICE_NAME="mantenimiento_app"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# Verificar que el directorio de la aplicación existe
if [ ! -d "$APP_DIR" ]; then
    echo "ERROR: Directorio de la aplicación no encontrado: $APP_DIR"
    exit 1
fi

# Crear usuario si no existe
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "Creando usuario $SERVICE_USER..."
    useradd -r -s /bin/false -d "$APP_DIR" "$SERVICE_USER"
fi

# Configurar permisos
echo "Configurando permisos..."
chown -R $SERVICE_USER:$SERVICE_USER "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod 644 "$APP_DIR"/*.py
chmod 644 "$APP_DIR"/*.txt
chmod 644 "$APP_DIR"/*.ini

# Crear directorio de logs
mkdir -p /var/log/mantenimiento_app
chown $SERVICE_USER:$SERVICE_USER /var/log/mantenimiento_app

# Crear archivo de servicio systemd
echo "Creando archivo de servicio systemd..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Sistema de Mantenimiento App
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=FLASK_ENV=production
Environment=FLASK_APP=app.py
ExecStart=$APP_DIR/venv/bin/python app.py
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mantenimiento_app

# Configuración de seguridad
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR /var/log/mantenimiento_app

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
echo "Recargando systemd..."
systemctl daemon-reload

# Habilitar y iniciar el servicio
echo "Habilitando y iniciando el servicio..."
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Verificar estado
echo "Verificando estado del servicio..."
systemctl status $SERVICE_NAME --no-pager

echo ""
echo "=========================================="
echo "  CONFIGURACIÓN COMPLETADA"
echo "=========================================="
echo "✅ Servicio configurado: $SERVICE_NAME"
echo "✅ Usuario del servicio: $SERVICE_USER"
echo "✅ Directorio de la app: $APP_DIR"
echo ""
echo "Comandos útiles:"
echo "- Ver estado: systemctl status $SERVICE_NAME"
echo "- Ver logs: journalctl -u $SERVICE_NAME -f"
echo "- Reiniciar: systemctl restart $SERVICE_NAME"
echo "- Detener: systemctl stop $SERVICE_NAME"
echo ""

# Verificar si el servicio está funcionando
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ El servicio está ejecutándose correctamente"
else
    echo "❌ El servicio no está ejecutándose. Revisar logs:"
    echo "journalctl -u $SERVICE_NAME --no-pager -n 20"
fi 