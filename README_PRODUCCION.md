# Sistema de Mantenimiento - Guía de Producción

## 📋 Índice
1. [Instalación Inicial](#instalación-inicial)
2. [Actualización Automática](#actualización-automática)
3. [Configuración Manual](#configuración-manual)
4. [Monitoreo y Logs](#monitoreo-y-logs)
5. [Solución de Problemas](#solución-de-problemas)
6. [Backup y Restauración](#backup-y-restauración)

## 🚀 Instalación Inicial

### Requisitos Previos
- Ubuntu 20.04+ o Debian 11+
- Acceso root (sudo)
- Conexión a internet
- Dominio configurado (opcional para SSL)

### Pasos de Instalación

1. **Clonar el repositorio en el servidor:**
```bash
cd /opt
sudo git clone https://github.com/tu-usuario/mantenimiento_app.git
cd mantenimiento_app
```

2. **Ejecutar instalación automática:**
```bash
sudo bash instalar_produccion.sh
```

3. **Configurar variables de entorno:**
```bash
sudo nano config.py
```

Ajustar las siguientes configuraciones:
```python
class ProductionConfig:
    SECRET_KEY = 'tu-clave-secreta-muy-segura'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/mantenimiento.db'
    FLASK_ENV = 'production'
    DEBUG = False
```

4. **Configurar dominio (opcional):**
```bash
sudo nano /etc/nginx/sites-available/mantenimiento_app
```
Cambiar `tu-dominio.com` por tu dominio real.

5. **Configurar SSL con Let's Encrypt:**
```bash
sudo certbot --nginx -d tu-dominio.com
```

## 🔄 Actualización Automática

### Actualización Manual
```bash
cd /opt/mantenimiento_app
sudo bash actualizar_produccion.sh
```

### Actualización Automática
El sistema está configurado para actualizarse automáticamente todos los días a las 2:00 AM.

Para verificar el estado de las actualizaciones automáticas:
```bash
sudo systemctl status cron
sudo tail -f /var/log/mantenimiento_app/cron.log
```

## ⚙️ Configuración Manual

### Servicios del Sistema

#### 1. Servicio de la Aplicación (Systemd)
```bash
# Ver estado
sudo systemctl status mantenimiento_app

# Reiniciar
sudo systemctl restart mantenimiento_app

# Ver logs
sudo journalctl -u mantenimiento_app -f

# Habilitar/Deshabilitar
sudo systemctl enable mantenimiento_app
sudo systemctl disable mantenimiento_app
```

#### 2. Nginx (Proxy Reverso)
```bash
# Ver estado
sudo systemctl status nginx

# Reiniciar
sudo systemctl reload nginx

# Ver logs
sudo tail -f /var/log/nginx/mantenimiento_app_access.log
sudo tail -f /var/log/nginx/mantenimiento_app_error.log

# Verificar configuración
sudo nginx -t
```

#### 3. Firewall (UFW)
```bash
# Ver estado
sudo ufw status

# Permitir puertos adicionales
sudo ufw allow 8080

# Ver reglas
sudo ufw status numbered
```

### Configuración de Base de Datos

#### Migraciones
```bash
cd /opt/mantenimiento_app
source venv/bin/activate
alembic upgrade head
```

#### Backup Manual
```bash
cd /opt/mantenimiento_app
sqlite3 instance/mantenimiento.db ".backup '/opt/backups/backup_manual_$(date +%Y%m%d_%H%M%S).sql'"
```

## 📊 Monitoreo y Logs

### Logs de la Aplicación
```bash
# Logs del servicio
sudo journalctl -u mantenimiento_app -f

# Logs de actualización
sudo tail -f /var/log/mantenimiento_app/update_*.log

# Logs de cron
sudo tail -f /var/log/mantenimiento_app/cron.log
```

### Logs de Nginx
```bash
# Logs de acceso
sudo tail -f /var/log/nginx/mantenimiento_app_access.log

# Logs de error
sudo tail -f /var/log/nginx/mantenimiento_app_error.log
```

### Monitoreo de Recursos
```bash
# Ver procesos
ps aux | grep python

# Ver uso de memoria
free -h

# Ver uso de disco
df -h

# Ver puertos abiertos
sudo netstat -tlnp
```

### Monitor Automático
El sistema incluye un monitor que verifica cada 5 minutos si la aplicación está ejecutándose:
```bash
# Ver estado del monitor
sudo systemctl status mantenimiento_app_monitor.timer

# Ver logs del monitor
sudo journalctl -u mantenimiento_app_monitor.service
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### 1. La aplicación no inicia
```bash
# Verificar logs
sudo journalctl -u mantenimiento_app --no-pager -n 50

# Verificar permisos
ls -la /opt/mantenimiento_app/
sudo chown -R www-data:www-data /opt/mantenimiento_app/

# Verificar entorno virtual
cd /opt/mantenimiento_app
source venv/bin/activate
python -c "import flask; print('Flask OK')"
```

#### 2. Error de base de datos
```bash
# Verificar archivo de BD
ls -la /opt/mantenimiento_app/instance/

# Verificar permisos
sudo chown www-data:www-data /opt/mantenimiento_app/instance/mantenimiento.db

# Ejecutar migraciones
cd /opt/mantenimiento_app
source venv/bin/activate
alembic upgrade head
```

#### 3. Error de Nginx
```bash
# Verificar configuración
sudo nginx -t

# Ver logs de error
sudo tail -f /var/log/nginx/error.log

# Reiniciar Nginx
sudo systemctl restart nginx
```

#### 4. Problemas de SSL
```bash
# Renovar certificado
sudo certbot renew

# Verificar certificado
sudo certbot certificates

# Reinstalar certificado
sudo certbot --nginx -d tu-dominio.com
```

### Comandos de Diagnóstico
```bash
# Verificar todos los servicios
sudo systemctl status mantenimiento_app nginx

# Verificar puertos
sudo netstat -tlnp | grep -E ':(80|443|5000)'

# Verificar logs del sistema
sudo dmesg | tail -20

# Verificar espacio en disco
df -h /opt /var/log
```

## 💾 Backup y Restauración

### Backup Automático
Los backups se crean automáticamente antes de cada actualización en `/opt/backups/`.

### Backup Manual Completo
```bash
#!/bin/bash
# Script de backup completo
FECHA=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/backup_completo_$FECHA"

mkdir -p "$BACKUP_DIR"

# Backup de base de datos
sqlite3 /opt/mantenimiento_app/instance/mantenimiento.db ".backup '$BACKUP_DIR/mantenimiento.db'"

# Backup de archivos
cp -r /opt/mantenimiento_app/static/uploads "$BACKUP_DIR/"
cp -r /opt/mantenimiento_app/instance "$BACKUP_DIR/"

# Backup de configuración
cp /opt/mantenimiento_app/config.py "$BACKUP_DIR/"
cp /etc/nginx/sites-available/mantenimiento_app "$BACKUP_DIR/"

echo "Backup completo creado en: $BACKUP_DIR"
```

### Restauración
```bash
# Restaurar base de datos
sqlite3 /opt/mantenimiento_app/instance/mantenimiento.db ".restore '/opt/backups/backup_archivo.sql'"

# Restaurar archivos
cp -r /opt/backups/backup_completo_*/uploads/* /opt/mantenimiento_app/static/uploads/

# Reiniciar servicios
sudo systemctl restart mantenimiento_app
sudo systemctl reload nginx
```

## 🔒 Seguridad

### Configuración de Seguridad
1. **Firewall configurado** con UFW
2. **Usuario no privilegiado** (www-data) para la aplicación
3. **Headers de seguridad** en Nginx
4. **Certificados SSL** con Let's Encrypt
5. **Actualizaciones automáticas** del sistema

### Mantenimiento de Seguridad
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Verificar servicios
sudo systemctl status --failed

# Revisar logs de seguridad
sudo journalctl -f | grep -i "error\|fail\|denied"
```

## 📞 Soporte

### Información del Sistema
```bash
# Versión del sistema
cat /etc/os-release

# Versión de Python
python3 --version

# Versión de Flask
cd /opt/mantenimiento_app
source venv/bin/activate
flask --version

# Estado de todos los servicios
sudo systemctl list-units --type=service --state=running | grep mantenimiento
```

### Contacto
Para soporte técnico, proporcionar:
1. Versión del sistema operativo
2. Logs de error específicos
3. Pasos para reproducir el problema
4. Configuración actual

---

**Nota:** Esta guía asume que la aplicación está instalada en `/opt/mantenimiento_app/`. Ajusta las rutas según tu configuración específica. 