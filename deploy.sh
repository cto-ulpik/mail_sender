#!/bin/bash

# Script de instalación y despliegue para Ubuntu
# Ejecutar como root o con sudo

set -e

echo "🚀 Iniciando instalación de SES Mailer..."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directorio de trabajo
WORK_DIR="/var/www/html"
PROJECT_DIR="$WORK_DIR/mail_sender"

echo -e "${YELLOW}📁 Cambiando al directorio de trabajo...${NC}"
cd $WORK_DIR

# Verificar si git está instalado
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}📦 Instalando git...${NC}"
    apt-get update
    apt-get install -y git
fi

# Verificar si Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}📦 Instalando Python3...${NC}"
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
fi

# Clonar o actualizar el repositorio
if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}📥 Actualizando repositorio existente...${NC}"
    cd $PROJECT_DIR
    git pull origin main
else
    echo -e "${YELLOW}📥 Clonando repositorio...${NC}"
    git clone https://github.com/cto-ulpik/mail_sender.git $PROJECT_DIR
    cd $PROJECT_DIR
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🐍 Creando entorno virtual...${NC}"
    python3 -m venv venv
fi

# Activar entorno virtual e instalar dependencias
echo -e "${YELLOW}📦 Instalando dependencias...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Instalar Gunicorn para producción
if ! pip list | grep -q gunicorn; then
    echo -e "${YELLOW}📦 Instalando Gunicorn...${NC}"
    pip install gunicorn
fi

# Crear directorio instance si no existe
mkdir -p instance

# Verificar si existe .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado.${NC}"
    echo -e "${YELLOW}📝 Creando archivo .env de ejemplo...${NC}"
    cat > .env << 'EOF'
# Amazon SES SMTP Credentials
SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SES_SMTP_PORT=587
SES_SMTP_USERNAME=TU_SMTP_USERNAME
SES_SMTP_PASSWORD=TU_SMTP_PASSWORD

# Email del remitente (debe estar verificado en SES)
SENDER_EMAIL=tu-email-verificado@dominio.com
SENDER_NAME=Tu Nombre o Empresa

# Configuración de la aplicación
SECRET_KEY=genera-una-clave-secreta-segura-y-aleatoria-aqui
BASE_URL=https://mails.ulpik.com
EOF
    echo -e "${GREEN}✅ Archivo .env creado. Por favor, edítalo con tus credenciales reales.${NC}"
    echo -e "${YELLOW}   nano $PROJECT_DIR/.env${NC}"
else
    echo -e "${GREEN}✅ Archivo .env ya existe.${NC}"
fi

echo -e "${GREEN}✅ Instalación completada!${NC}"
echo ""
echo -e "${YELLOW}📋 Próximos pasos:${NC}"
echo "1. Edita el archivo .env con tus credenciales:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Para ejecutar en desarrollo:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python3 app.py"
echo ""
echo "3. Para ejecutar en producción con Gunicorn:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   gunicorn -w 4 -b 0.0.0.0:5010 --timeout 120 app:app"
echo ""
echo "4. Para crear un servicio systemd, ejecuta:"
echo "   sudo nano /etc/systemd/system/mail-sender.service"
echo "   (Ver README.md para la configuración del servicio)"

