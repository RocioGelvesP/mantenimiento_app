#!/bin/bash

# Script para configurar Nginx como proxy reverso
# Ejecutar como root: sudo bash configurar_nginx.sh

echo "=========================================="
echo "  CONFIGURACIÓN DE NGINX"
echo "  Sistema de Mantenimiento"
echo "=========================================="

# Configuración
APP_DIR="/opt/mantenimiento_app"
NGINX_CONF="/etc/nginx/sites-available/mantenimiento_app"
NGINX_ENABLED="/etc/nginx/sites-enabled/mantenimiento_app"
DOMAIN="tu-dominio.com"  # Cambiar por tu dominio real

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# Verificar que Nginx esté instalado
if ! command -v nginx &> /dev/null; then
    echo "Instalando Nginx..."
    apt update
    apt install -y nginx
fi

# Crear configuración de Nginx
echo "Creando configuración de Nginx..."
cat > "$NGINX_CONF" << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirigir HTTP a HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # Configuración SSL (ajustar rutas según tu certificado)
    ssl_certificate /etc/ssl/certs/$DOMAIN.crt;
    ssl_certificate_key /etc/ssl/private/$DOMAIN.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Configuración de seguridad
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logs
    access_log /var/log/nginx/mantenimiento_app_access.log;
    error_log /var/log/nginx/mantenimiento_app_error.log;
    
    # Archivos estáticos
    location /static/ {
        alias $APP_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Proxy a la aplicación Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Configuración para archivos grandes (uploads)
    location /static/uploads/ {
        alias $APP_DIR/static/uploads/;
        client_max_body_size 10M;
        expires 1d;
    }
    
    # Configuración para favicon
    location = /favicon.ico {
        log_not_found off;
        access_log off;
    }
    
    # Configuración para robots.txt
    location = /robots.txt {
        log_not_found off;
        access_log off;
    }
}

# Configuración para desarrollo (sin SSL)
server {
    listen 80;
    server_name localhost;
    
    # Logs
    access_log /var/log/nginx/mantenimiento_app_dev_access.log;
    error_log /var/log/nginx/mantenimiento_app_dev_error.log;
    
    # Archivos estáticos
    location /static/ {
        alias $APP_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Proxy a la aplicación Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Configuración para archivos grandes (uploads)
    location /static/uploads/ {
        alias $APP_DIR/static/uploads/;
        client_max_body_size 10M;
        expires 1d;
    }
}
EOF

# Habilitar el sitio
echo "Habilitando sitio en Nginx..."
ln -sf "$NGINX_CONF" "$NGINX_ENABLED"

# Verificar configuración de Nginx
echo "Verificando configuración de Nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Configuración de Nginx válida"
    
    # Recargar Nginx
    echo "Recargando Nginx..."
    systemctl reload nginx
    
    # Verificar estado
    echo "Verificando estado de Nginx..."
    systemctl status nginx --no-pager
else
    echo "❌ Error en la configuración de Nginx"
    exit 1
fi

echo ""
echo "=========================================="
echo "  CONFIGURACIÓN DE NGINX COMPLETADA"
echo "=========================================="
echo "✅ Sitio configurado: $DOMAIN"
echo "✅ Proxy reverso configurado en puerto 80/443"
echo "✅ Archivos estáticos servidos desde $APP_DIR/static/"
echo ""
echo "IMPORTANTE:"
echo "1. Ajusta el dominio en la configuración: $NGINX_CONF"
echo "2. Configura certificados SSL si es necesario"
echo "3. Ajusta las rutas de certificados SSL"
echo ""
echo "Comandos útiles:"
echo "- Ver logs: tail -f /var/log/nginx/mantenimiento_app_*.log"
echo "- Recargar: systemctl reload nginx"
echo "- Ver estado: systemctl status nginx"
echo "- Ver configuración: nginx -t"
echo "" 