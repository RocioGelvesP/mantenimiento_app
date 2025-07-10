#!/bin/bash

# Script para actualizar la aplicación usando Git y Docker Compose
# Configuración
NOMBRE_CONTENEDOR="mantenimiento_app"
BACKUP_DIR="./backups"
DATA_DIR="./data"
FECHA=$(date +%Y-%m-%d_%H-%M-%S)

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ACTUALIZACIÓN DE APLICACIÓN DOCKER   ${NC}"
echo -e "${GREEN}========================================${NC}"

# Crear directorios necesarios
mkdir -p $BACKUP_DIR
mkdir -p $DATA_DIR
mkdir -p ./logs

echo -e "${YELLOW}1. Realizando backup de la base de datos SQLite...${NC}"
# Backup de la base de datos SQLite
if [ -f "$DATA_DIR/mantenimiento.db" ]; then
    cp "$DATA_DIR/mantenimiento.db" "$BACKUP_DIR/backup_sqlite_$FECHA.db"
    echo -e "${GREEN}✓ Backup realizado: backup_sqlite_$FECHA.db${NC}"
else
    echo -e "${YELLOW}⚠ No se encontró base de datos existente${NC}"
fi

echo -e "${YELLOW}2. Actualizando código con Git...${NC}"
git pull origin main
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Código actualizado correctamente${NC}"
else
    echo -e "${RED}✗ Error al actualizar el código${NC}"
    exit 1
fi

echo -e "${YELLOW}3. Deteniendo contenedores existentes...${NC}"
docker-compose down
echo -e "${GREEN}✓ Contenedores detenidos${NC}"

echo -e "${YELLOW}4. Construyendo nueva imagen Docker...${NC}"
docker-compose build --no-cache
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Imagen construida correctamente${NC}"
else
    echo -e "${RED}✗ Error al construir la imagen${NC}"
    exit 1
fi

echo -e "${YELLOW}5. Levantando nuevos contenedores...${NC}"
docker-compose up -d
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Contenedores levantados correctamente${NC}"
else
    echo -e "${RED}✗ Error al levantar contenedores${NC}"
    exit 1
fi

echo -e "${YELLOW}6. Verificando estado de la aplicación...${NC}"
sleep 5
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Aplicación funcionando correctamente${NC}"
else
    echo -e "${RED}✗ Error: La aplicación no está funcionando${NC}"
    echo -e "${YELLOW}Revisando logs...${NC}"
    docker-compose logs
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ¡ACTUALIZACIÓN COMPLETADA CON ÉXITO!  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Comandos útiles:${NC}"
echo -e "  Ver logs: ${GREEN}docker-compose logs -f${NC}"
echo -e "  Ver estado: ${GREEN}docker-compose ps${NC}"
echo -e "  Detener: ${GREEN}docker-compose down${NC}"
echo -e "  Reiniciar: ${GREEN}docker-compose restart${NC}" 