# 🚀 Instrucciones para Actualizar en Producción

## Pasos Rápidos

### 1. Conectarse al servidor

```bash
ssh root@45.55.81.191
# O usa el método que tengas configurado
```

### 2. Ir al directorio del proyecto

```bash
cd /var/www/html/mail_sender
```

### 3. Detener el servicio (opcional, pero recomendado)

```bash
sudo systemctl stop mail-sender
```

### 4. Activar el entorno virtual

```bash
source venv/bin/activate
```

### 5. Actualizar el código desde GitHub

```bash
git pull origin main
```

### 6. Instalar nuevas dependencias (si hay cambios en requirements.txt)

```bash
pip install -r requirements.txt
```

### 7. Ejecutar migraciones de base de datos (si es necesario)

Si es la primera vez que actualizas después de agregar múltiples remitentes:

```bash
python3 migrate_add_sender_fields.py
```

Esto agregará las columnas `sender_email` y `sender_name` a la tabla `campaigns` si no existen.

### 8. Verificar archivo .env

Asegúrate de que el archivo `.env` tenga la configuración correcta:

```bash
nano .env
```

Verifica que tenga:

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
SECRET_KEY=tu-clave-secreta-segura
BASE_URL=https://mails.ulpik.com
```

### 9. Reiniciar el servicio

```bash
sudo systemctl start mail-sender
```

### 10. Verificar que el servicio está corriendo

```bash
sudo systemctl status mail-sender
```

Deberías ver algo como:
```
● mail-sender.service - Mail Sender Flask App
   Loaded: loaded
   Active: active (running)
```

### 11. Ver logs si hay problemas

```bash
# Ver logs en tiempo real
sudo journalctl -u mail-sender -f

# Ver últimos 50 logs
sudo journalctl -u mail-sender -n 50
```

### 12. Probar la aplicación

Accede a: `http://mails.ulpik.com` o `http://45.55.81.191:5010`

---

## Comandos Útiles

### Ver estado del servicio
```bash
sudo systemctl status mail-sender
```

### Reiniciar el servicio
```bash
sudo systemctl restart mail-sender
```

### Ver logs en tiempo real
```bash
sudo journalctl -u mail-sender -f
```

### Verificar que el puerto está escuchando
```bash
sudo ss -tlnp | grep 5010
```

### Verificar configuración de Nginx
```bash
sudo nginx -t
sudo systemctl status nginx
```

---

## Checklist de Actualización

- [ ] Código actualizado desde GitHub (`git pull`)
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Migración de base de datos ejecutada (si es necesario)
- [ ] Archivo `.env` verificado y configurado
- [ ] Servicio reiniciado (`sudo systemctl restart mail-sender`)
- [ ] Servicio funcionando correctamente (`sudo systemctl status mail-sender`)
- [ ] Aplicación accesible en el navegador
- [ ] Sin errores en los logs

---

## Solución de Problemas

### Si el servicio no inicia:

1. Ver logs detallados:
   ```bash
   sudo journalctl -u mail-sender -n 100
   ```

2. Verificar permisos:
   ```bash
   ls -la /var/www/html/mail_sender
   ```

3. Verificar que el entorno virtual esté activo:
   ```bash
   which python
   # Debería mostrar: /var/www/html/mail_sender/venv/bin/python
   ```

### Si hay errores de base de datos:

1. Ejecutar migración:
   ```bash
   cd /var/www/html/mail_sender
   source venv/bin/activate
   python3 migrate_add_sender_fields.py
   ```

2. Verificar estructura de la base de datos:
   ```bash
   sqlite3 instance/email_campaigns.db ".schema campaigns"
   ```

### Si hay errores de permisos:

```bash
sudo chown -R www-data:www-data /var/www/html/mail_sender
sudo chmod -R 755 /var/www/html/mail_sender
```

---

## Notas Importantes

1. **Siempre haz backup antes de actualizar** (opcional pero recomendado):
   ```bash
   cp -r /var/www/html/mail_sender /var/www/html/mail_sender.backup
   ```

2. **No actualices durante envíos activos**: Si hay una campaña enviándose, espera a que termine.

3. **Verifica los logs después de actualizar**: Asegúrate de que no hay errores.

4. **El servicio se reinicia automáticamente** si falla (gracias a `Restart=always` en systemd).
