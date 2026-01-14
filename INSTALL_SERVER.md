# Instrucciones de Instalación en Servidor Ubuntu

## Paso 1: Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

## Paso 2: Clonar el repositorio

```bash
cd /var/www/html
git clone https://github.com/cto-ulpik/mail_sender.git
cd mail_sender
```

## Paso 3: Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

## Paso 4: Instalar dependencias de Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

## Paso 5: Crear directorio instance

```bash
mkdir -p instance
```

## Paso 6: Configurar archivo .env

```bash
nano .env
```

Pegar el siguiente contenido (y editar con tus credenciales reales):

```env
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
```

Guardar con `Ctrl+O`, `Enter`, `Ctrl+X`

## Paso 7: Probar la aplicación

```bash
source venv/bin/activate
python3 app.py
```

Debería iniciar en `http://0.0.0.0:5010`

## Paso 8: Configurar como servicio systemd (Producción)

```bash
sudo nano /etc/systemd/system/mail-sender.service
```

Pegar:

```ini
[Unit]
Description=Mail Sender Flask App
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/html/mail_sender
Environment="PATH=/var/www/html/mail_sender/venv/bin"
ExecStart=/var/www/html/mail_sender/venv/bin/gunicorn -w 4 -b 127.0.0.1:5010 --timeout 120 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mail-sender
sudo systemctl start mail-sender
sudo systemctl status mail-sender
```

## Paso 9: Configurar Nginx (Opcional)

```bash
sudo nano /etc/nginx/sites-available/mails.ulpik.com
```

Pegar:

```nginx
server {
    listen 80;
    server_name mails.ulpik.com;

    location / {
        proxy_pass http://127.0.0.1:5010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

Activar:

```bash
sudo ln -s /etc/nginx/sites-available/mails.ulpik.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

