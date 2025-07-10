#!/bin/bash

# Script para migrar datos existentes a Docker
# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MIGRACIÓN DE DATOS A DOCKER         ${NC}"
echo -e "${BLUE}========================================${NC}"

# Verificar si existe base de datos actual
echo -e "${YELLOW}Verificando base de datos existente...${NC}"

# Buscar archivo de base de datos en ubicaciones comunes
DB_LOCATIONS=(
    "mantenimiento.db"
    "instance/mantenimiento.db"
    "app.db"
    "instance/app.db"
)

DB_FOUND=""
for location in "${DB_LOCATIONS[@]}"; do
    if [ -f "$location" ]; then
        DB_FOUND="$location"
        echo -e "${GREEN}✓ Base de datos encontrada en: $location${NC}"
        break
    fi
done

if [ -z "$DB_FOUND" ]; then
    echo -e "${YELLOW}⚠ No se encontró base de datos existente${NC}"
    echo -e "${YELLOW}Se creará una nueva base de datos al iniciar Docker${NC}"
else
    echo -e "${YELLOW}Migrando base de datos...${NC}"
    mkdir -p data
    cp "$DB_FOUND" "data/mantenimiento.db"
    echo -e "${GREEN}✓ Base de datos migrada a data/mantenimiento.db${NC}"
fi

# Verificar archivos de uploads existentes
echo -e "${YELLOW}Verificando archivos subidos...${NC}"
if [ -d "static/uploads" ]; then
    echo -e "${GREEN}✓ Directorio de uploads encontrado${NC}"
    # Asegurar que los subdirectorios existen
    mkdir -p static/uploads/companies
    mkdir -p static/uploads/documentos
    mkdir -p static/uploads/lubricacion
    echo -e "${GREEN}✓ Estructura de directorios verificada${NC}"
else
    echo -e "${YELLOW}⚠ No se encontró directorio de uploads${NC}"
    mkdir -p static/uploads/companies
    mkdir -p static/uploads/documentos
    mkdir -p static/uploads/lubricacion
    echo -e "${GREEN}✓ Directorios de uploads creados${NC}"
fi

# Crear directorios necesarios
echo -e "${YELLOW}Creando directorios necesarios...${NC}"
mkdir -p backups
mkdir -p logs
echo -e "${GREEN}✓ Directorios creados${NC}"

# Verificar permisos
echo -e "${YELLOW}Configurando permisos...${NC}"
chmod +x actualizar_app.sh
chmod +x instalar_docker.sh
echo -e "${GREEN}✓ Permisos configurados${NC}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ¡MIGRACIÓN COMPLETADA!              ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Próximos pasos:${NC}"
echo -e "1. ${GREEN}Ejecuta: ./instalar_docker.sh${NC}"
echo -e "2. ${GREEN}Ejecuta: ./actualizar_app.sh${NC}"
echo -e "3. ${GREEN}Accede a: http://localhost:5000${NC}"
echo -e ""
echo -e "${YELLOW}Nota: Si tienes datos importantes, verifica que la migración fue exitosa${NC}" 