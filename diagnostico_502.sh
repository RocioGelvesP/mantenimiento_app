#!/bin/bash

# Script de diagnóstico para error 502 Bad Gateway
# Ejecutar como root: sudo bash diagnostico_502.sh

echo "=========================================="
echo "  DIAGNÓSTICO ERROR 502 BAD GATEWAY"
echo "  Sistema de Mantenimiento"
echo "=========================================="

# Configuración
APP_DIR="/opt/mantenimiento_app"
SERVICE_NAME="mantenimiento_app"
NGINX_CONF="/etc/nginx/sites-enabled/mantenimiento_app"

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Este script debe ejecutarse como root (sudo)"
    exit 1
fi

echo "1. Verificando estado de Nginx..."
systemctl status nginx --no-pager

echo ""
echo "2. Verificando estado del servicio de la aplicación..."
systemctl status $SERVICE_NAME --no-pager

echo ""
echo "3. Verificando si el puerto 5000 está en uso..."
netstat -tlnp | grep :5000

echo ""
echo "4. Verificando logs de Nginx..."
echo "--- Últimas 10 líneas del error log ---"
tail -10 /var/log/nginx/mantenimiento_app_error.log 2>/dev/null || echo "No se encontró el archivo de log"

echo ""
echo "5. Verificando logs del servicio..."
echo "--- Últimas 10 líneas del journal ---"
journalctl -u $SERVICE_NAME --no-pager -n 10

echo ""
echo "6. Verificando configuración de Nginx..."
nginx -t

echo ""
echo "7. Verificando que el directorio de la app existe..."
if [ -d "$APP_DIR" ]; then
    echo "✅ Directorio encontrado: $APP_DIR"
    ls -la "$APP_DIR"
else
    echo "❌ Directorio no encontrado: $APP_DIR"
fi

echo ""
echo "8. Verificando archivo app.py..."
if [ -f "$APP_DIR/app.py" ]; then
    echo "✅ Archivo app.py encontrado"
else
    echo "❌ Archivo app.py no encontrado"
fi

echo ""
echo "9. Verificando entorno virtual..."
if [ -d "$APP_DIR/venv" ]; then
    echo "✅ Entorno virtual encontrado"
else
    echo "❌ Entorno virtual no encontrado"
fi

echo ""
echo "10. Intentando conectar al puerto 5000..."
if curl -s http://127.0.0.1:5000 > /dev/null; then
    echo "✅ La aplicación responde en puerto 5000"
else
    echo "❌ La aplicación no responde en puerto 5000"
fi

echo ""
echo "=========================================="
echo "  SOLUCIONES RECOMENDADAS"
echo "=========================================="

# Verificar si el servicio está ejecutándose
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "🔧 El servicio no está ejecutándose. Iniciando..."
    systemctl start $SERVICE_NAME
    sleep 3
    systemctl status $SERVICE_NAME --no-pager
fi

# Verificar si nginx está ejecutándose
if ! systemctl is-active --quiet nginx; then
    echo "🔧 Nginx no está ejecutándose. Iniciando..."
    systemctl start nginx
    sleep 2
    systemctl status nginx --no-pager
fi

echo ""
echo "Comandos para solucionar problemas:"
echo "1. Reiniciar servicio: systemctl restart $SERVICE_NAME"
echo "2. Reiniciar nginx: systemctl restart nginx"
echo "3. Ver logs en tiempo real: journalctl -u $SERVICE_NAME -f"
echo "4. Ver logs de nginx: tail -f /var/log/nginx/mantenimiento_app_error.log"
echo "5. Verificar puerto: netstat -tlnp | grep :5000"
echo "6. Probar aplicación: curl http://127.0.0.1:5000"
echo ""

echo "¿Deseas que ejecute alguna de estas soluciones automáticamente? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Ejecutando soluciones automáticas..."
    
    echo "Reiniciando servicio..."
    systemctl restart $SERVICE_NAME
    sleep 3
    
    echo "Reiniciando nginx..."
    systemctl restart nginx
    sleep 2
    
    echo "Verificando estado final..."
    systemctl status $SERVICE_NAME --no-pager
    echo ""
    systemctl status nginx --no-pager
    
    echo ""
    echo "Probando conexión..."
    if curl -s http://127.0.0.1:5000 > /dev/null; then
        echo "✅ La aplicación ahora responde correctamente"
    else
        echo "❌ La aplicación aún no responde. Revisar logs manualmente."
    fi
fi 