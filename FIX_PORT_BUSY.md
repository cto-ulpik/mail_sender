# 🔧 Solución: Puerto 5010 en uso

## Problema
El puerto 5010 está ocupado por un proceso anterior (probablemente `python3 app.py` ejecutado manualmente).

## Solución Rápida

```bash
# 1. Encontrar y matar el proceso que está usando el puerto
sudo lsof -ti:5010 | xargs sudo kill -9

# 2. Verificar que el puerto está libre
sudo ss -tlnp | grep 5010
# No debería mostrar nada

# 3. Reiniciar el servicio
sudo systemctl start mail-sender

# 4. Verificar que funciona
sudo systemctl status mail-sender
```

## Solución Alternativa (si la anterior no funciona)

```bash
# 1. Ver qué proceso está usando el puerto
sudo lsof -i:5010

# 2. Matar el proceso específico (reemplaza PID con el número que aparezca)
sudo kill -9 PID

# 3. O matar todos los procesos de Python relacionados
sudo pkill -f "python3 app.py"
sudo pkill -f "gunicorn.*app:app"

# 4. Esperar unos segundos
sleep 2

# 5. Verificar que el puerto está libre
sudo ss -tlnp | grep 5010

# 6. Reiniciar servicio
sudo systemctl start mail-sender
```

## Verificar procesos en segundo plano

Si ejecutaste `python3 app.py` y lo detuviste con Ctrl+Z:

```bash
# Ver trabajos en segundo plano
jobs

# Matar el trabajo (reemplaza [1] con el número del trabajo)
kill %1

# O matar todos los trabajos
killall python3
```

## Comandos completos

```bash
# Matar todos los procesos que puedan estar usando el puerto
sudo pkill -f "python3 app.py"
sudo pkill -f "gunicorn"
sudo lsof -ti:5010 | xargs sudo kill -9 2>/dev/null

# Esperar un momento
sleep 2

# Verificar que está libre
sudo ss -tlnp | grep 5010

# Reiniciar servicio
sudo systemctl start mail-sender
sudo systemctl status mail-sender
```
