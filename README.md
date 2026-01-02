# 📧 SES Mailer - Email Campaign Manager

Aplicación web para enviar campañas de email usando Amazon SES via SMTP, con tracking de aperturas y clics.

## ✨ Características

- ✅ Envío de emails via SMTP con Amazon SES
- ✅ Carga de destinatarios desde archivos CSV
- ✅ Tracking de aperturas (pixel tracking)
- ✅ Tracking de clics (redirect tracking)
- ✅ Dashboard con estadísticas en tiempo real
- ✅ Historial completo de campañas
- ✅ Vista detallada por campaña
- ✅ Interfaz moderna y responsiva
- ✅ Envío masivo optimizado con conexiones SMTP reutilizables
- ✅ Reintento automático de envíos fallidos

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/cto-ulpik/mail_sender.git
cd mail_sender
```

### 2. Crear entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar credenciales de Amazon SES

Crea un archivo `.env` en la raíz del proyecto:

```env
# Amazon SES SMTP Credentials
SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SES_SMTP_PORT=587
SES_SMTP_USERNAME=TU_SMTP_USERNAME
SES_SMTP_PASSWORD=TU_SMTP_PASSWORD

# Email del remitente (debe estar verificado en SES)
SENDER_EMAIL=tu-email-verificado@dominio.com
SENDER_NAME=Tu Nombre o Empresa

# Remitente 2 (opcional)
SENDER2_EMAIL=churchill@ulpik.com
SENDER2_NAME=Churchill de Ulpik

# Configuración de la aplicación
SECRET_KEY=una-clave-secreta-segura-y-aleatoria
BASE_URL=https://mails.ulpik.com
```

**Nota importante:** El `BASE_URL` debe apuntar al dominio donde esté desplegada la aplicación para que el tracking funcione correctamente. Por defecto está configurado para `https://mails.ulpik.com`.

### 5. Inicializar la base de datos

La base de datos se crea automáticamente al ejecutar la aplicación por primera vez.

### 6. Ejecutar la aplicación

#### Desarrollo local:

```bash
python3 app.py
```

La aplicación estará disponible en: `http://localhost:5010`

#### Producción:

Para producción, se recomienda usar un servidor WSGI como Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5010 app:app
```

## 📝 Cómo obtener credenciales SMTP de Amazon SES

1. Inicia sesión en la [Consola de AWS](https://console.aws.amazon.com/)
2. Ve a **Amazon Simple Email Service (SES)**
3. En el menú lateral, selecciona **SMTP Settings**
4. Haz clic en **Create SMTP Credentials**
5. Copia el **SMTP Username** y **SMTP Password**
6. Asegúrate de verificar tu email de envío en **Verified Identities**
7. Si estás en modo Sandbox, solicita el acceso de producción para enviar a cualquier email

## 📋 Formato del archivo CSV

El archivo CSV debe tener el siguiente formato:

```csv
email,name
juan@ejemplo.com,Juan Pérez
maria@ejemplo.com,María García
pedro@ejemplo.com,Pedro López
```

- La columna `email` es **obligatoria** (puede llamarse: `email`, `Email`, `EMAIL`, `e-mail`, `E-mail`, `correo`, `Correo`)
- La columna `name` es **opcional** (puede llamarse: `name`, `Name`, `NAME`, `nombre`, `Nombre`)

El sistema detecta automáticamente diferentes variaciones de nombres de columnas.

## 🎯 Uso

### 1. Crear una campaña

1. Accede a la aplicación en tu navegador
2. Haz clic en "Nueva Campaña"
3. Ingresa el nombre y asunto de la campaña
4. Pega el contenido HTML del email
5. Sube el archivo CSV con los destinatarios
6. Revisa la lista de destinatarios
7. Haz clic en "Enviar Campaña"

### 2. Ver estadísticas

- El Dashboard muestra estadísticas globales:
  - Total de campañas
  - Total de emails enviados
  - Total de aperturas
  - Total de clics
  - Tasa de apertura global
  - Tasa de clics global

- Cada campaña tiene su vista detallada con:
  - Total de emails enviados
  - Porcentaje de aperturas
  - Porcentaje de clics
  - Lista de destinatarios con su estado (enviado, abierto, clic)
  - Opción para reintentar envíos fallidos

### 3. Reintentar envíos fallidos

Si algunos emails fallaron al enviarse, puedes:
1. Ir a la vista de detalle de la campaña
2. Hacer clic en "Reintentar Fallidos"
3. El sistema reintentará enviar solo los emails que fallaron

### 4. Detener un envío en progreso

Si necesitas detener un envío que está en progreso:
1. Ve a la vista de detalle de la campaña
2. Haz clic en "Detener Envío"
3. El envío se detendrá después del email actual

## 📊 Tracking

### Tracking de Aperturas

Se inserta automáticamente un pixel de 1x1 px transparente en cada email. Cuando el destinatario abre el email y carga las imágenes, se registra la apertura con la fecha y hora.

**URL de tracking:** `https://mails.ulpik.com/track/open/{tracking_token}`

### Tracking de Clics

Los enlaces en el email se mantienen tal como están en el HTML original. El tracking de clics se puede implementar manualmente si es necesario usando la URL: `https://mails.ulpik.com/track/click/{tracking_token}?url={url_original}`

## ⚙️ Configuración de Producción

### Variables de Entorno Requeridas

Asegúrate de configurar estas variables en tu servidor de producción:

```env
SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SES_SMTP_PORT=587
SES_SMTP_USERNAME=tu_smtp_username
SES_SMTP_PASSWORD=tu_smtp_password
SENDER_EMAIL=tu-email@dominio.com
SENDER_NAME=Tu Nombre
SECRET_KEY=clave-secreta-muy-segura-y-aleatoria
BASE_URL=https://mails.ulpik.com
```

### Despliegue con Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5010 --timeout 120 app:app
```

### Despliegue con systemd (Linux)

Crea un archivo `/etc/systemd/system/mail-sender.service`:

```ini
[Unit]
Description=Mail Sender Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=/ruta/a/mail_sender
Environment="PATH=/ruta/a/mail_sender/venv/bin"
ExecStart=/ruta/a/mail_sender/venv/bin/gunicorn -w 4 -b 0.0.0.0:5010 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Luego:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mail-sender
sudo systemctl start mail-sender
```

## 🔄 Migración de Base de Datos

Si actualizas desde una versión anterior, necesitas ejecutar la migración para agregar los campos de remitente:

```bash
cd /var/www/html/mail_sender
source venv/bin/activate
python3 migrate_add_sender_fields.py
```

Esto agregará las columnas `sender_email` y `sender_name` a la tabla `campaigns` si no existen.

## ⚠️ Notas importantes

1. **Verificación de email**: Todos los emails remitentes deben estar verificados en Amazon SES
2. **Múltiples remitentes**: Puedes configurar múltiples remitentes en el archivo `.env`. Cada uno debe estar verificado en SES
3. **Sandbox mode**: Si tu cuenta SES está en sandbox, solo podrás enviar a emails verificados. Solicita acceso de producción para enviar a cualquier email
4. **Límites de envío**: Respeta los límites de envío de tu cuenta SES:
   - Sandbox: 200 emails/día, 1 email/segundo
   - Producción: Varía según tu plan
5. **BASE_URL**: Debe apuntar al dominio donde esté desplegada la aplicación para que el tracking funcione correctamente
6. **Base de datos**: La base de datos SQLite se crea automáticamente en la carpeta `instance/`. Para producción, considera usar PostgreSQL o MySQL
7. **Seguridad**: Nunca subas el archivo `.env` al repositorio. Está incluido en `.gitignore`

## 🛠 Estructura del proyecto

```
mail_sender/
├── app.py                  # Aplicación principal Flask
├── config.py               # Configuración
├── models.py               # Modelos de base de datos
├── requirements.txt        # Dependencias Python
├── test_email.py          # Script de prueba de envío
├── .env                    # Variables de entorno (no se sube a git)
├── .gitignore             # Archivos ignorados por git
├── README.md              # Este archivo
├── templates/
│   ├── base.html          # Template base
│   ├── index.html         # Dashboard principal
│   ├── new_campaign.html  # Crear nueva campaña
│   └── campaign_detail.html # Detalle de campaña
└── instance/
    └── email_campaigns.db # Base de datos SQLite (se crea automáticamente)
```

## 🧪 Pruebas

Para probar el envío de emails antes de crear una campaña completa:

```bash
python3 test_email.py
```

Este script te pedirá un email de destino y enviará un email de prueba para verificar que la configuración funciona correctamente.

## 📄 Licencia

MIT License - Libre para uso personal y comercial.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Para problemas o preguntas, abre un issue en el repositorio de GitHub.
