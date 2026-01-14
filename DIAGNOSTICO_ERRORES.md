# 🔍 Diagnóstico: Proyecto no se ejecuta en producción

## Pasos para diagnosticar

### 1. Verificar estado del servicio

```bash
sudo systemctl status mail-sender
```

**Si está "failed" o "inactive":**
- Ver los logs detallados (paso 2)

### 2. Ver logs del servicio

```bash
# Ver últimos 50 logs
sudo journalctl -u mail-sender -n 50

# Ver logs en tiempo real
sudo journalctl -u mail-sender -f
```

**Errores comunes a buscar:**
- `ModuleNotFoundError: No module named 'flask_login'` → Falta instalar Flask-Login
- `ImportError` → Falta alguna dependencia
- `Permission denied` → Problema de permisos
- `Address already in use` → Puerto 5010 ya está en uso

### 3. Verificar que Flask-Login está instalado

```bash
cd /var/www/html/mail_sender
source venv/bin/activate
pip list | grep Flask-Login
```

**Si no aparece:**
```bash
pip install Flask-Login==0.6.3
```

### 4. Verificar que todas las dependencias están instaladas

```bash
cd /var/www/html/mail_sender
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Probar ejecutar manualmente

```bash
cd /var/www/html/mail_sender
source venv/bin/activate
python3 app.py
```

**Si hay errores, verás el mensaje completo en la terminal.**

### 6. Verificar sintaxis del código

```bash
cd /var/www/html/mail_sender
source venv/bin/activate
python3 -m py_compile app.py
```

**Si hay errores de sintaxis, los verás aquí.**

### 7. Verificar que el código está actualizado

```bash
cd /var/www/html/mail_sender
git log --oneline -3
```

**Debería mostrar:**
- `95a429f Actualizar README con información de autenticación`
- `765a07f Agregar sistema de autenticación...`

## Soluciones comunes

### Error: ModuleNotFoundError: No module named 'flask_login'

**Solución:**
```bash
cd /var/www/html/mail_sender
source venv/bin/activate
pip install Flask-Login==0.6.3
sudo systemctl restart mail-sender
```

### Error: ImportError o AttributeError

**Solución:**
```bash
cd /var/www/html/mail_sender
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart mail-sender
```

### Error: Permission denied

**Solución:**
```bash
sudo chown -R www-data:www-data /var/www/html/mail_sender
sudo chmod -R 755 /var/www/html/mail_sender
sudo chmod -R 775 instance/
sudo systemctl restart mail-sender
```

### Error: Address already in use (puerto 5010)

**Solución:**
```bash
# Ver qué proceso está usando el puerto
sudo lsof -ti:5010

# Matar el proceso si es necesario
sudo kill -9 $(sudo lsof -ti:5010)

# Reiniciar servicio
sudo systemctl restart mail-sender
```

### El servicio inicia pero se detiene inmediatamente

**Solución:**
```bash
# Ver logs detallados
sudo journalctl -u mail-sender -n 100 --no-pager

# Probar ejecutar manualmente para ver el error
cd /var/www/html/mail_sender
source venv/bin/activate
python3 app.py
```

## Comandos de diagnóstico completo

```bash
# 1. Ver estado
sudo systemctl status mail-sender

# 2. Ver logs
sudo journalctl -u mail-sender -n 100

# 3. Verificar dependencias
cd /var/www/html/mail_sender
source venv/bin/activate
pip list | grep -E "Flask|Login"

# 4. Probar manualmente
python3 app.py

# 5. Verificar código actualizado
git log --oneline -3
```
