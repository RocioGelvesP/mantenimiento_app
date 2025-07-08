#!/bin/bash

# Script de instalación inicial para Docker
# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  INSTALACIÓN INICIAL DE DOCKER        ${NC}"
echo -e "${BLUE}========================================${NC}"

# Verificar si Docker está instalado
echo -e "${YELLOW}Verificando instalación de Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker no está instalado. Instalando...${NC}"
    # Instalar Docker en Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✓ Docker instalado correctamente${NC}"
    echo -e "${YELLOW}⚠ Necesitas reiniciar la sesión para que los cambios surtan efecto${NC}"
else
    echo -e "${GREEN}✓ Docker ya está instalado${NC}"
fi

# Verificar si Docker Compose está instalado
echo -e "${YELLOW}Verificando Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose no está instalado. Instalando...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose instalado correctamente${NC}"
else
    echo -e "${GREEN}✓ Docker Compose ya está instalado${NC}"
fi

# Crear directorios necesarios
echo -e "${YELLOW}Creando directorios necesarios...${NC}"
mkdir -p data
mkdir -p backups
mkdir -p logs
mkdir -p static/uploads/companies
mkdir -p static/uploads/documentos
mkdir -p static/uploads/lubricacion
echo -e "${GREEN}✓ Directorios creados${NC}"

# Dar permisos al script de actualización
echo -e "${YELLOW}Configurando permisos...${NC}"
chmod +x actualizar_app.sh
echo -e "${GREEN}✓ Permisos configurados${NC}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ¡INSTALACIÓN COMPLETADA!             ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Próximos pasos:${NC}"
echo -e "1. ${GREEN}Reinicia la sesión si Docker se instaló${NC}"
echo -e "2. ${GREEN}Ejecuta: ./actualizar_app.sh${NC}"
echo -e "3. ${GREEN}Accede a: http://localhost:5000${NC}" 