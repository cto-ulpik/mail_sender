# 🔧 Solución: Error de Base de Datos de Solo Lectura

## Problema
```
sqlite3.OperationalError: attempt to write a readonly database
```

Este error ocurre cuando el usuario `www-data` (que ejecuta el servicio) no tiene permisos de escritura en el directorio `instance/` o en el archivo de base de datos.

## Solución Rápida

Ejecuta estos comandos en el servidor:

```bash
# 1. Ir al directorio del proyecto
cd /var/www/html/mail_sender

# 2. Cambiar propietario del directorio instance a www-data
sudo chown -R www-data:www-data instance/

# 3. Dar permisos de escritura
sudo chmod -R 755 instance/

# 4. Si el archivo de base de datos ya existe, asegurar permisos
sudo chmod 664 instance/email_campaigns.db 2>/dev/null || echo "Base de datos se creará automáticamente"

# 5. Reiniciar el servicio
sudo systemctl restart mail-sender

# 6. Verificar que funciona
sudo systemctl status mail-sender
```

## Solución Completa (Recomendada)

Si quieres asegurar todos los permisos correctamente:

```bash
# 1. Ir al directorio del proyecto
cd /var/www/html/mail_sender

# 2. Cambiar propietario de todo el proyecto a www-data
sudo chown -R www-data:www-data /var/www/html/mail_sender

# 3. Dar permisos apropiados
sudo chmod -R 755 /var/www/html/mail_sender

# 4. Permisos especiales para el directorio instance (escritura)
sudo chmod -R 775 instance/

# 5. Asegurar que el archivo .env tenga permisos correctos
sudo chmod 640 .env
sudo chown www-data:www-data .env

# 6. Reiniciar el servicio
sudo systemctl restart mail-sender
```

## Verificar Permisos

Después de corregir, verifica:

```bash
# Ver propietario y permisos del directorio instance
ls -la instance/

# Debería mostrar algo como:
# drwxrwxr-x 2 www-data www-data 4096 ... instance/
# -rw-rw-r-- 1 www-data www-data ... email_campaigns.db
```

## Si el Problema Persiste

### Opción 1: Recrear la base de datos

```bash
cd /var/www/html/mail_sender
sudo systemctl stop mail-sender

# Hacer backup de la base de datos actual
sudo cp instance/email_campaigns.db instance/email_campaigns.db.backup

# Eliminar la base de datos (se recreará automáticamente)
sudo rm instance/email_campaigns.db

# Asegurar permisos
sudo chown -R www-data:www-data instance/
sudo chmod -R 775 instance/

# Reiniciar servicio
sudo systemctl start mail-sender
```

### Opción 2: Verificar SELinux (si está activo)

```bash
# Verificar si SELinux está activo
getenforce

# Si está en "Enforcing", puede necesitar ajustar contextos
# (Generalmente no es necesario en Ubuntu/Debian)
```

## Prevenir el Problema

Para evitar este problema en el futuro:

1. **Siempre crear archivos como www-data o cambiar permisos después:**
   ```bash
   sudo -u www-data touch /var/www/html/mail_sender/instance/test
   ```

2. **Asegurar que el servicio tenga permisos correctos desde el inicio:**
   ```bash
   sudo chown -R www-data:www-data /var/www/html/mail_sender
   ```

## Comandos de Verificación

```bash
# Ver quién es el propietario del directorio
ls -ld /var/www/html/mail_sender/instance

# Ver permisos del archivo de base de datos
ls -l /var/www/html/mail_sender/instance/email_campaigns.db

# Ver logs del servicio para más detalles
sudo journalctl -u mail-sender -n 50
```

