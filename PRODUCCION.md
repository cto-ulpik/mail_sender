# 🚀 Guía de Actualización y Ejecución en Producción

## Paso 1: Actualizar el código desde GitHub

```bash
cd /var/www/html/mail_sender
git pull origin main
```

## Paso 2: Activar el entorno virtual

```bash
source venv/bin/activate
```

## Paso 3: Actualizar dependencias (si es necesario)

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

## Paso 4: Verificar/Crear archivo .env

```bash
# Verificar si existe
ls -la .env

# Si no existe, crearlo
nano .env
```

Contenido del archivo `.env`:

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

## Paso 5: Crear directorio instance (si no existe)

```bash
mkdir -p instance
```

## Paso 6: Ejecutar la aplicación

### Opción A: Modo Desarrollo (temporal, para pruebas)

```bash
cd /var/www/html/mail_sender
source venv/bin/activate
python3 app.py
```

La aplicación estará disponible en: `http://tu-servidor:5010`

Presiona `Ctrl+C` para detener.

### Opción B: Producción con Gunicorn (recomendado)

```bash
cd /var/www/html/mail_sender
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5010 --timeout 120 app:app
```

### Opción C: Como servicio systemd (recomendado para producción permanente)

#### 1. Crear el archivo del servicio:

```bash
sudo nano /etc/systemd/system/mail-sender.service
```

#### 2. Pegar este contenido:

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

#### 3. Activar y iniciar el servicio:

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar el servicio para que inicie automáticamente
sudo systemctl enable mail-sender

# Iniciar el servicio
sudo systemctl start mail-sender

# Verificar el estado
sudo systemctl status mail-sender
```

#### 4. Comandos útiles del servicio:

```bash
# Ver estado
sudo systemctl status mail-sender

# Ver logs en tiempo real
sudo journalctl -u mail-sender -f

# Reiniciar el servicio
sudo systemctl restart mail-sender

# Detener el servicio
sudo systemctl stop mail-sender

# Iniciar el servicio
sudo systemctl start mail-sender
```

## Paso 7: Configurar Nginx (Opcional - para usar dominio mails.ulpik.com)

#### 1. Crear configuración de Nginx:

```bash
sudo nano /etc/nginx/sites-available/mails.ulpik.com
```

#### 2. Pegar este contenido:

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

#### 3. Activar la configuración:

```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/mails.ulpik.com /etc/nginx/sites-enabled/

# Verificar la configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

#### 4. Configurar SSL con Let's Encrypt (recomendado):

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado SSL
sudo certbot --nginx -d mails.ulpik.com

# El certificado se renovará automáticamente
```

## Verificación Final

1. **Verificar que el servicio está corriendo:**
   ```bash
   sudo systemctl status mail-sender
   ```

2. **Verificar que el puerto 5010 está escuchando:**
   ```bash
   sudo netstat -tlnp | grep 5010
   # o
   sudo ss -tlnp | grep 5010
   ```

3. **Probar la aplicación:**
   - Acceder a: `http://tu-servidor-ip:5010`
   - O si configuraste Nginx: `http://mails.ulpik.com`

4. **Ver logs si hay problemas:**
   ```bash
   sudo journalctl -u mail-sender -n 50
   ```

## Resumen de Comandos Rápidos

```bash
# Actualizar código
cd /var/www/html/mail_sender && git pull origin main

# Reiniciar servicio después de actualizar
sudo systemctl restart mail-sender

# Ver logs
sudo journalctl -u mail-sender -f
```

