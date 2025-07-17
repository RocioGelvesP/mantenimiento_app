#!/bin/bash

# Script de solución rápida para error 502 Bad Gateway
# Ejecutar como root: sudo bash solucionar_502.sh

echo "=========================================="
echo "  SOLUCIÓN RÁPIDA ERROR 502"
echo "  Sistema de Mantenimiento"
echo "=========================================="

# Configuración
SERVICE_NAME="mantenimiento_app"

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Este script debe ejecutarse como root (sudo)"
    exit 1
fi

echo "🔧 Solucionando error 502..."

echo "1. Deteniendo servicios..."
systemctl stop nginx
systemctl stop $SERVICE_NAME

echo "2. Esperando 3 segundos..."
sleep 3

echo "3. Iniciando servicio de la aplicación..."
systemctl start $SERVICE_NAME
sleep 5

echo "4. Verificando que la aplicación esté ejecutándose..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Servicio iniciado correctamente"
else
    echo "❌ Error al iniciar el servicio"
    echo "Revisando logs..."
    journalctl -u $SERVICE_NAME --no-pager -n 10
    exit 1
fi

echo "5. Probando conexión al puerto 5000..."
if curl -s http://127.0.0.1:5000 > /dev/null; then
    echo "✅ La aplicación responde correctamente"
else
    echo "❌ La aplicación no responde"
    echo "Esperando 10 segundos más..."
    sleep 10
    if curl -s http://127.0.0.1:5000 > /dev/null; then
        echo "✅ La aplicación ahora responde"
    else
        echo "❌ La aplicación aún no responde"
        echo "Revisando logs del servicio..."
        journalctl -u $SERVICE_NAME --no-pager -n 20
        exit 1
    fi
fi

echo "6. Iniciando Nginx..."
systemctl start nginx
sleep 2

echo "7. Verificando Nginx..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx iniciado correctamente"
else
    echo "❌ Error al iniciar Nginx"
    systemctl status nginx --no-pager
    exit 1
fi

echo "8. Verificando configuración de Nginx..."
nginx -t

echo "9. Probando conexión final..."
if curl -s http://localhost > /dev/null; then
    echo "✅ El sitio web responde correctamente"
else
    echo "❌ El sitio web aún no responde"
    echo "Revisando logs de Nginx..."
    tail -10 /var/log/nginx/mantenimiento_app_error.log 2>/dev/null || echo "No se encontró el archivo de log"
fi

echo ""
echo "=========================================="
echo "  SOLUCIÓN COMPLETADA"
echo "=========================================="
echo "✅ Servicios reiniciados"
echo "✅ Aplicación verificada"
echo "✅ Nginx verificado"
echo ""
echo "Si el problema persiste, ejecutar:"
echo "sudo bash diagnostico_502.sh"
echo ""
echo "Comandos útiles:"
echo "- Ver estado: systemctl status $SERVICE_NAME"
echo "- Ver logs: journalctl -u $SERVICE_NAME -f"
echo "- Ver logs nginx: tail -f /var/log/nginx/mantenimiento_app_error.log" 