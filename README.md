# 🐳 Guía de Docker para Aplicación de Mantenimiento

Esta guía te ayudará a implementar y gestionar tu aplicación de mantenimiento usando Docker.

## 📋 Prerrequisitos

- Servidor Linux (Ubuntu/Debian recomendado)
- Acceso SSH al servidor
- Git configurado en el servidor

## 🚀 Instalación Inicial

### 1. Clonar el repositorio (si no lo tienes)
```bash
git clone <tu-repositorio>
cd mantenimiento_app
```

### 2. Ejecutar script de instalación
```bash
chmod +x instalar_docker.sh
./instalar_docker.sh
```

### 3. Reiniciar sesión (si Docker se instaló)
```bash
# Cerrar sesión y volver a conectarse
exit
# Reconectar por SSH
```

## 🔧 Configuración

### Variables de Entorno
Edita el archivo `docker-compose.yml` y cambia:
- `SECRET_KEY`: Una clave secreta segura
- `DATABASE_URL`: URL de tu base de datos (por defecto SQLite)

### Puertos
Por defecto la aplicación corre en el puerto 5000. Si necesitas cambiarlo:
1. Modifica `docker-compose.yml` línea `"5000:5000"`
2. Cambia el primer número (puerto del host)

## 🚀 Despliegue

### Primera vez
```bash
./actualizar_app.sh
```

### Actualizaciones posteriores
```bash
./actualizar_app.sh
```

## 📊 Comandos Útiles

### Ver estado de la aplicación
```bash
docker-compose ps
```

### Ver logs en tiempo real
```bash
docker-compose logs -f
```

### Ver logs de un servicio específico
```bash
docker-compose logs app
```

### Detener la aplicación
```bash
docker-compose down
```

### Reiniciar la aplicación
```bash
docker-compose restart
```

### Reconstruir imagen (forzar actualización)
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 💾 Gestión de Datos

### Backup automático
El script `actualizar_app.sh` realiza backups automáticos de la base de datos SQLite en la carpeta `./backups/`

### Backup manual
```bash
cp ./data/mantenimiento.db ./backups/backup_manual_$(date +%Y-%m-%d_%H-%M-%S).db
```

### Restaurar backup
```bash
# Detener aplicación
docker-compose down

# Restaurar backup
cp ./backups/backup_sqlite_YYYY-MM-DD_HH-MM-SS.db ./data/mantenimiento.db

# Levantar aplicación
docker-compose up -d
```

## 🔍 Solución de Problemas

### La aplicación no inicia
```bash
# Ver logs detallados
docker-compose logs app

# Verificar puertos
netstat -tulpn | grep 5000

# Verificar recursos del sistema
docker stats
```

### Error de permisos
```bash
# Dar permisos a directorios
sudo chown -R $USER:$USER ./data ./static/uploads ./logs

# Dar permisos a scripts
chmod +x *.sh
```

### Limpiar Docker (si hay problemas)
```bash
# Detener y eliminar contenedores
docker-compose down

# Eliminar imágenes no utilizadas
docker system prune -a

# Reconstruir desde cero
docker-compose build --no-cache
docker-compose up -d
```

## 📁 Estructura de Directorios

```
mantenimiento_app/
├── data/                    # Base de datos SQLite
├── backups/                 # Backups automáticos
├── logs/                    # Logs de la aplicación
├── static/uploads/          # Archivos subidos
│   ├── companies/          # Logos de empresas
│   ├── documentos/         # Documentos
│   └── lubricacion/        # Archivos de lubricación
├── Dockerfile              # Configuración de Docker
├── docker-compose.yml      # Orquestación de servicios
├── actualizar_app.sh       # Script de actualización
└── instalar_docker.sh      # Script de instalación
```

## 🔒 Seguridad

### Variables de entorno sensibles
- Cambia `SECRET_KEY` en `docker-compose.yml`
- Usa variables de entorno del sistema para datos sensibles
- No subas claves secretas al repositorio Git

### Firewall
```bash
# Permitir solo puerto 5000
sudo ufw allow 5000
sudo ufw enable
```

## 📈 Monitoreo

### Ver uso de recursos
```bash
docker stats
```

### Ver espacio en disco
```bash
docker system df
```

### Limpiar espacio
```bash
docker system prune
```

## 🔄 Actualización Automática (Opcional)

Para actualizaciones automáticas, puedes configurar un cron job:

```bash
# Editar crontab
crontab -e

# Agregar línea para actualizar cada día a las 2 AM
0 2 * * * cd /ruta/a/mantenimiento_app && ./actualizar_app.sh >> logs/cron.log 2>&1
```

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs: `docker-compose logs app`
2. Verifica la configuración en `docker-compose.yml`
3. Asegúrate de que Docker esté funcionando: `docker --version`
4. Revisa los permisos de archivos y directorios

---

**¡Tu aplicación está lista para funcionar con Docker! 🎉** 