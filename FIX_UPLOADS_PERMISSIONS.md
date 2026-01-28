# 🔧 Solución: Error de Permisos en Directorio uploads/

## Problema
```
[Errno 13] Permission denied: 'uploads/Jae_Cafe_Design-Ulpik_1.xlsx'
```

Este error ocurre cuando el usuario `www-data` (que ejecuta el servicio) no tiene permisos de escritura en el directorio `uploads/` o el directorio no existe.

## Solución Rápida

Ejecuta estos comandos en el servidor:

```bash
# 1. Ir al directorio del proyecto
cd /var/www/html/mail_sender

# 2. Crear el directorio uploads si no existe
mkdir -p uploads

# 3. Cambiar propietario del directorio uploads a www-data
sudo chown -R www-data:www-data uploads/

# 4. Dar permisos de escritura
sudo chmod -R 775 uploads/

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

# 2. Crear directorio uploads
mkdir -p uploads

# 3. Cambiar propietario de uploads a www-data
sudo chown -R www-data:www-data uploads/

# 4. Dar permisos apropiados (lectura, escritura, ejecución para propietario y grupo)
sudo chmod -R 775 uploads/

# 5. Verificar permisos
ls -la uploads/

# Debería mostrar algo como:
# drwxrwxr-x 2 www-data www-data 4096 ... uploads/

# 6. Reiniciar el servicio
sudo systemctl restart mail-sender
```

## Verificar Permisos

Después de corregir, verifica:

```bash
# Ver propietario y permisos del directorio uploads
ls -la uploads/

# Intentar crear un archivo de prueba (como www-data)
sudo -u www-data touch uploads/test.txt
sudo -u www-data rm uploads/test.txt

# Si no hay error, los permisos están correctos
```

## Si el Problema Persiste

### Opción 1: Verificar que el directorio existe

```bash
cd /var/www/html/mail_sender
ls -la | grep uploads
```

Si no existe, créalo:
```bash
mkdir -p uploads
sudo chown -R www-data:www-data uploads/
sudo chmod -R 775 uploads/
```

### Opción 2: Verificar el usuario del servicio

```bash
# Ver qué usuario ejecuta el servicio
sudo systemctl show mail-sender | grep User

# Debería mostrar: User=www-data
```

### Opción 3: Ver logs detallados

```bash
# Ver logs del servicio
sudo journalctl -u mail-sender -n 50

# Buscar errores relacionados con uploads
sudo journalctl -u mail-sender | grep -i "permission\|uploads"
```

## Notas Importantes

1. **El directorio `uploads/` se crea automáticamente** al iniciar la aplicación (desde la versión actualizada del código).

2. **Si el servicio no puede crear el directorio**, créalo manualmente con los comandos anteriores.

3. **Los permisos 775** permiten:
   - Lectura, escritura y ejecución para el propietario (www-data)
   - Lectura, escritura y ejecución para el grupo (www-data)
   - Lectura y ejecución para otros

4. **Después de corregir permisos**, siempre reinicia el servicio:
   ```bash
   sudo systemctl restart mail-sender
   ```

## Comandos Útiles

```bash
# Ver todos los directorios y sus permisos
ls -la /var/www/html/mail_sender/

# Verificar permisos específicos
stat uploads/

# Cambiar permisos recursivamente
sudo chmod -R 775 uploads/

# Cambiar propietario recursivamente
sudo chown -R www-data:www-data uploads/
```
