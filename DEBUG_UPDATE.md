# 🔍 Diagnóstico: Cambios no se actualizaron en producción

## Pasos para diagnosticar

### 1. Verificar estado del repositorio Git

```bash
cd /var/www/html/mail_sender
git status
```

**Si muestra "Your branch is behind 'origin/main'":**
```bash
git pull origin main
```

**Si muestra "Your branch is up to date" pero los cambios no están:**
```bash
# Forzar actualización
git fetch origin
git reset --hard origin/main
```

### 2. Verificar que estás en la rama correcta

```bash
git branch
# Debería mostrar: * main
```

Si no estás en main:
```bash
git checkout main
git pull origin main
```

### 3. Verificar cambios locales que puedan estar bloqueando

```bash
# Ver si hay cambios locales sin commitear
git status

# Si hay cambios, puedes descartarlos (CUIDADO: esto elimina cambios locales)
git reset --hard HEAD

# O guardarlos en un stash
git stash
git pull origin main
```

### 4. Verificar que el repositorio remoto está configurado

```bash
git remote -v
# Debería mostrar:
# origin  https://github.com/cto-ulpik/mail_sender.git (fetch)
# origin  https://github.com/cto-ulpik/mail_sender.git (push)
```

### 5. Forzar actualización completa

```bash
cd /var/www/html/mail_sender

# Hacer backup por seguridad
cp -r . ../mail_sender.backup

# Forzar actualización
git fetch origin
git reset --hard origin/main

# Verificar que se actualizó
git log --oneline -3
```

### 6. Verificar que los archivos se actualizaron

```bash
# Verificar fecha de modificación de app.py
ls -la app.py

# Verificar que tiene los cambios recientes
grep -n "track/click" app.py
# Debería mostrar líneas relacionadas con tracking
```

### 7. Reiniciar el servicio después de actualizar

```bash
sudo systemctl restart mail-sender
sudo systemctl status mail-sender
```

## Solución paso a paso completa

```bash
# 1. Ir al directorio
cd /var/www/html/mail_sender

# 2. Ver estado actual
git status
git log --oneline -3

# 3. Hacer backup (por seguridad)
sudo cp -r /var/www/html/mail_sender /var/www/html/mail_sender.backup.$(date +%Y%m%d_%H%M%S)

# 4. Forzar actualización
git fetch origin
git reset --hard origin/main

# 5. Verificar cambios
git log --oneline -5

# 6. Instalar dependencias si hay cambios
source venv/bin/activate
pip install -r requirements.txt

# 7. Reiniciar servicio
sudo systemctl restart mail-sender

# 8. Verificar logs
sudo journalctl -u mail-sender -n 20
```

## Problemas comunes y soluciones

### Problema: "fatal: not a git repository"

**Solución:**
```bash
cd /var/www/html/mail_sender
git init
git remote add origin https://github.com/cto-ulpik/mail_sender.git
git fetch origin
git checkout -b main origin/main
```

### Problema: "error: Your local changes would be overwritten"

**Solución:**
```bash
# Opción 1: Guardar cambios locales
git stash
git pull origin main
git stash pop

# Opción 2: Descartar cambios locales (CUIDADO)
git reset --hard HEAD
git pull origin main
```

### Problema: "Permission denied"

**Solución:**
```bash
# Verificar permisos
ls -la /var/www/html/mail_sender/.git

# Corregir permisos si es necesario
sudo chown -R www-data:www-data /var/www/html/mail_sender/.git
```

## Verificar que los cambios están aplicados

Después de actualizar, verifica:

```bash
# 1. Verificar que app.py tiene la función mejorada
grep -A 5 "def add_tracking" app.py

# 2. Verificar que tiene tracking de clics
grep -n "track/click" app.py

# 3. Verificar versión del código
git log --oneline -1
# Debería mostrar: "Mejorar detección de enlaces para tracking de clics"
```

## Si nada funciona: Clonar de nuevo

Como último recurso:

```bash
# 1. Hacer backup completo
sudo cp -r /var/www/html/mail_sender /var/www/html/mail_sender.backup.full

# 2. Mover el directorio actual
sudo mv /var/www/html/mail_sender /var/www/html/mail_sender.old

# 3. Clonar de nuevo
cd /var/www/html
git clone https://github.com/cto-ulpik/mail_sender.git

# 4. Copiar configuración del backup
cp mail_sender.old/.env mail_sender/.env
cp -r mail_sender.old/venv mail_sender/ 2>/dev/null || echo "Recrear venv"
cp -r mail_sender.old/instance mail_sender/ 2>/dev/null || echo "Instance se creará automáticamente"

# 5. Recrear venv si es necesario
cd mail_sender
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 6. Asegurar permisos
sudo chown -R www-data:www-data /var/www/html/mail_sender
sudo chmod -R 755 /var/www/html/mail_sender
sudo chmod -R 775 instance/

# 7. Reiniciar servicio
sudo systemctl restart mail-sender
```

