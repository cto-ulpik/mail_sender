from flask import Flask, render_template, request, jsonify, redirect, Response, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from models import db, Campaign, Recipient
from config import Config
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
import io
import re
import time
import threading
from urllib.parse import quote, unquote
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

# Clase de usuario simple para autenticación
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    # Solo hay un usuario admin
    if user_id == Config.ADMIN_EMAIL:
        return User(user_id)
    return None

# Create tables
with app.app_context():
    db.create_all()


def send_email_smtp(recipient, campaign, smtp_connection=None):
    """Envía un email usando Amazon SES SMTP"""
    try:
        # Obtener remitente de la campaña o usar el por defecto
        sender_email = campaign.sender_email or Config.SENDER_EMAIL
        sender_name = campaign.sender_name or Config.SENDER_NAME
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = campaign.subject
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = recipient.email
        
        # Agregar pixel de tracking y modificar links
        html_content = add_tracking(campaign.html_content, recipient.tracking_token)
        
        # Agregar contenido HTML
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Usar conexión existente o crear nueva
        if smtp_connection:
            smtp_connection.sendmail(sender_email, recipient.email, msg.as_string())
        else:
            with smtplib.SMTP(Config.SES_SMTP_HOST, Config.SES_SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SES_SMTP_USERNAME, Config.SES_SMTP_PASSWORD)
                server.sendmail(sender_email, recipient.email, msg.as_string())
        
        return True, None
    except Exception as e:
        return False, str(e)


def get_smtp_connection():
    """Crear y retornar una conexión SMTP reutilizable"""
    server = smtplib.SMTP(Config.SES_SMTP_HOST, Config.SES_SMTP_PORT)
    server.starttls()
    server.login(Config.SES_SMTP_USERNAME, Config.SES_SMTP_PASSWORD)
    return server


def add_tracking(html_content, tracking_token):
    """Agrega pixel de tracking para aperturas y modifica links para tracking de clics"""
    base_url = Config.BASE_URL
    
    # Agregar pixel de tracking antes del cierre de </body>
    tracking_pixel = f'<img src="{base_url}/track/open/{tracking_token}" width="1" height="1" style="display:none;" />'
    
    if '</body>' in html_content.lower():
        html_content = re.sub(
            r'</body>',
            f'{tracking_pixel}</body>',
            html_content,
            flags=re.IGNORECASE
        )
    else:
        html_content += tracking_pixel
    
    # Debug: contar enlaces antes de modificar
    links_before = len(re.findall(r'<a\s+[^>]*href\s*=\s*["\']?[^"\'>\s]+["\']?[^>]*>', html_content, re.IGNORECASE))
    
    # Modificar todos los enlaces <a href="..."> para que pasen por el tracking
    def replace_link(match):
        original_tag = match.group(0)
        # El grupo 3 es el URL (después de href=" o href=')
        url = match.group(3) if match.lastindex >= 3 else ''
        
        if not url:
            return original_tag
        
        # Limpiar el URL de espacios
        url = url.strip()
        
        # No modificar enlaces que ya sean de tracking o enlaces javascript/mailto/data
        if '/track/' in url or url.startswith(('javascript:', 'mailto:', '#', 'data:', 'vbscript:')):
            return original_tag
        
        # Crear URL de tracking
        encoded_url = quote(url, safe='')
        tracking_url = f"{base_url}/track/click/{tracking_token}?url={encoded_url}"
        
        # Reemplazar el href en el tag (manejar comillas simples y dobles)
        quote_char = match.group(2)  # La comilla usada (simple o doble)
        return original_tag.replace(f'href={quote_char}{url}{quote_char}', f'href={quote_char}{tracking_url}{quote_char}')
    
    # Buscar y reemplazar todos los enlaces <a href="...">
    # Patrón mejorado para capturar href con comillas simples o dobles, y manejar espacios
    # Patrón: <a ... href=["'](url)["'] ...>
    html_content = re.sub(
        r'<a\s+([^>]*\s+)?href\s*=\s*(["\'])([^"\']+)\2([^>]*)>',
        replace_link,
        html_content,
        flags=re.IGNORECASE
    )
    
    # También buscar enlaces sin comillas (menos común pero posible)
    def replace_link_no_quotes(match):
        original_tag = match.group(0)
        url = match.group(2) if match.lastindex >= 2 else ''
        
        if not url:
            return original_tag
        
        url = url.strip()
        
        # No modificar enlaces que ya sean de tracking o enlaces especiales
        if '/track/' in url or url.startswith(('javascript:', 'mailto:', '#', 'data:', 'vbscript:')):
            return original_tag
        
        # Crear URL de tracking
        encoded_url = quote(url, safe='')
        tracking_url = f"{base_url}/track/click/{tracking_token}?url={encoded_url}"
        
        # Reemplazar el href
        return original_tag.replace(f'href={url}', f'href="{tracking_url}"')
    
    # Buscar enlaces sin comillas (href=url sin comillas)
    html_content = re.sub(
        r'<a\s+([^>]*\s+)?href\s*=\s*([^\s>]+)([^>]*)>',
        replace_link_no_quotes,
        html_content,
        flags=re.IGNORECASE
    )
    
    # Debug: contar enlaces después de modificar
    links_after = len(re.findall(r'/track/click/', html_content))
    
    # Log para debugging (solo en desarrollo)
    if app.debug:
        print(f"Tracking: {links_before} enlaces encontrados, {links_after} enlaces modificados")
    
    return html_content


# ============ RUTAS DE AUTENTICACIÓN ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Verificar credenciales
        if email == Config.ADMIN_EMAIL and password == Config.ADMIN_PASSWORD:
            user = User(email)
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Credenciales incorrectas. Por favor intenta de nuevo.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Sesión cerrada exitosamente.', 'success')
    return redirect(url_for('login'))


# ============ RUTAS WEB ============

@app.route('/')
@login_required
def index():
    """Página principal - Dashboard"""
    return render_template('index.html')


@app.route('/campaign/new')
@login_required
def new_campaign():
    """Página para crear nueva campaña"""
    return render_template('new_campaign.html')


@app.route('/campaign/<campaign_id>')
@login_required
def view_campaign(campaign_id):
    """Ver detalles de una campaña"""
    return render_template('campaign_detail.html', campaign_id=campaign_id)


# ============ API ENDPOINTS ============

@app.route('/api/senders', methods=['GET'])
@login_required
def get_senders():
    """Obtener lista de remitentes disponibles"""
    senders = Config.get_senders()
    return jsonify(senders)


@app.route('/api/campaigns', methods=['GET'])
@login_required
def get_campaigns():
    """Obtener todas las campañas"""
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return jsonify([c.to_dict() for c in campaigns])


@app.route('/api/campaigns/<campaign_id>', methods=['GET'])
@login_required
def get_campaign(campaign_id):
    """Obtener una campaña específica"""
    campaign = Campaign.query.get_or_404(campaign_id)
    return jsonify(campaign.to_dict())


@app.route('/api/campaigns/<campaign_id>/recipients', methods=['GET'])
@login_required
def get_campaign_recipients(campaign_id):
    """Obtener recipients de una campaña"""
    campaign = Campaign.query.get_or_404(campaign_id)
    return jsonify([r.to_dict() for r in campaign.recipients])


@app.route('/api/campaigns', methods=['POST'])
@login_required
def create_campaign():
    """Crear nueva campaña"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type debe ser application/json'}), 400
        
        data = request.json
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
        
        # Validar campos requeridos
        if not data.get('name'):
            return jsonify({'error': 'El nombre de la campaña es requerido'}), 400
        
        if not data.get('subject'):
            return jsonify({'error': 'El asunto es requerido'}), 400
        
        if not data.get('html_content'):
            return jsonify({'error': 'El contenido HTML es requerido'}), 400
        
        campaign = Campaign(
            name=data.get('name', 'Sin nombre'),
            subject=data.get('subject', ''),
            html_content=data.get('html_content', ''),
            sender_email=data.get('sender_email'),
            sender_name=data.get('sender_name')
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify(campaign.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        print(f"Error al crear campaña: {error_msg}")
        return jsonify({'error': f'Error al crear la campaña: {error_msg}'}), 500


@app.route('/api/campaigns/<campaign_id>/recipients', methods=['POST'])
@login_required
def add_recipients(campaign_id):
    """Agregar recipients desde CSV"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Archivo vacío'}), 400
    
    try:
        # Leer CSV con diferentes encodings
        file_content = file.stream.read()
        
        # Intentar diferentes encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
        csv_content = None
        
        for encoding in encodings:
            try:
                csv_content = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if csv_content is None:
            return jsonify({'error': 'No se pudo decodificar el archivo CSV. Por favor usa UTF-8.'}), 400
        
        # Leer CSV
        stream = io.StringIO(csv_content)
        reader = csv.DictReader(stream)
        
        # Verificar que el CSV tiene columnas
        if not reader.fieldnames:
            return jsonify({'error': 'El archivo CSV está vacío o no tiene encabezados'}), 400
        
        added = 0
        skipped = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):  # Empezar en 2 porque la línea 1 es el header
            try:
                # Detectar columna de email (varios formatos posibles, case-insensitive)
                email = None
                for key in row.keys():
                    if key and key.lower().strip() in ['email', 'e-mail', 'correo', 'mail']:
                        email = row.get(key, '').strip()
                        break
                
                # Si no se encontró, intentar con los nombres exactos
                if not email:
                    email = (
                        row.get('email', '') or 
                        row.get('Email', '') or 
                        row.get('EMAIL', '') or
                        row.get('e-mail', '') or
                        row.get('E-mail', '') or
                        row.get('Otro e-mail', '') or
                        row.get('correo', '') or
                        row.get('Correo', '') or
                        ''
                    ).strip()
                
                # Detectar columna de nombre (varios formatos posibles, case-insensitive)
                name = None
                for key in row.keys():
                    if key and key.lower().strip() in ['name', 'nombre', 'nombre completo', 'full name']:
                        name = row.get(key, '').strip()
                        break
                
                # Si no se encontró, intentar con los nombres exactos
                if not name:
                    name = (
                        row.get('name', '') or 
                        row.get('Name', '') or 
                        row.get('NAME', '') or
                        row.get('nombre', '') or
                        row.get('Nombre', '') or
                        ''
                    ).strip()
                
                # Validar email
                if not email:
                    skipped += 1
                    continue
                
                if '@' not in email:
                    skipped += 1
                    continue
                
                # Validar formato básico de email
                if email.count('@') != 1 or '.' not in email.split('@')[1]:
                    skipped += 1
                    continue
                
                # Crear recipient
                recipient = Recipient(
                    campaign_id=campaign.id,
                    email=email,
                    name=name if name else None
                )
                db.session.add(recipient)
                added += 1
                
            except Exception as e:
                errors.append(f"Línea {row_num}: {str(e)}")
                skipped += 1
                continue
        
        db.session.commit()
        
        response = {
            'message': f'Se agregaron {added} destinatarios',
            'count': added,
            'skipped': skipped
        }
        
        if errors and len(errors) <= 10:
            response['errors'] = errors
        elif errors:
            response['errors'] = errors[:10]
            response['error_count'] = len(errors)
        
        return jsonify(response)
    
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        print(f"Error al procesar CSV: {error_msg}")
        return jsonify({'error': f'Error al procesar el archivo CSV: {error_msg}'}), 400


def send_emails_background(campaign_id):
    """Función para enviar emails en segundo plano con conexión SMTP reutilizada"""
    with app.app_context():
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return
        
        # Configuración - SIN pausas artificiales, máxima velocidad
        BATCH_SIZE = 500                # Reconectar cada 500 emails
        
        batch_count = 0
        pending_recipients = [r for r in campaign.recipients if not r.sent and not r.error_message]
        smtp_conn = None
        
        try:
            # Crear conexión SMTP reutilizable
            smtp_conn = get_smtp_connection()
            
            for recipient in pending_recipients:
                # Verificar si la campaña sigue en estado "sending"
                db.session.refresh(campaign)
                if campaign.status != 'sending':
                    break
                
                success, error = send_email_smtp(recipient, campaign, smtp_conn)
                
                if success:
                    recipient.sent = True
                    recipient.sent_at = datetime.utcnow()
                else:
                    recipient.error_message = error
                    # Si hay error de conexión, reconectar
                    if 'connection' in str(error).lower() or 'smtp' in str(error).lower():
                        try:
                            smtp_conn.quit()
                        except:
                            pass
                        smtp_conn = get_smtp_connection()
                
                db.session.commit()
                batch_count += 1
                
                # Reconectar cada BATCH_SIZE para evitar timeouts
                if batch_count >= BATCH_SIZE:
                    batch_count = 0
                    try:
                        smtp_conn.quit()
                    except:
                        pass
                    smtp_conn = get_smtp_connection()
        
        except Exception as e:
            print(f"Error en envío: {e}")
        
        finally:
            if smtp_conn:
                try:
                    smtp_conn.quit()
                except:
                    pass
        
        # Actualizar estado final
        total_errors = len([r for r in campaign.recipients if r.error_message])
        campaign.status = 'sent' if total_errors == 0 else 'sent_with_errors'
        db.session.commit()


@app.route('/api/campaigns/<campaign_id>/send', methods=['POST'])
@login_required
def send_campaign(campaign_id):
    """Iniciar envío de campaña en segundo plano"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if not Config.SES_SMTP_USERNAME or not Config.SES_SMTP_PASSWORD:
        return jsonify({'error': 'Credenciales SES no configuradas'}), 400
    
    if not campaign.recipients:
        return jsonify({'error': 'No hay destinatarios'}), 400
    
    if campaign.status == 'sending':
        return jsonify({'error': 'La campaña ya se está enviando'}), 400
    
    # Marcar como enviando
    campaign.status = 'sending'
    campaign.sent_at = datetime.utcnow()
    db.session.commit()
    
    # Iniciar envío en segundo plano
    thread = threading.Thread(target=send_emails_background, args=(campaign_id,))
    thread.daemon = True
    thread.start()
    
    pending = len([r for r in campaign.recipients if not r.sent and not r.error_message])
    
    return jsonify({
        'message': f'Envío iniciado para {pending} destinatarios. El proceso continuará en segundo plano.',
        'pending': pending,
        'status': 'sending'
    })


@app.route('/api/campaigns/<campaign_id>', methods=['DELETE'])
@login_required
def delete_campaign(campaign_id):
    """Eliminar una campaña"""
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    return jsonify({'message': 'Campaña eliminada'})


def retry_emails_background(campaign_id):
    """Reintentar envíos fallidos en segundo plano con conexión reutilizada"""
    with app.app_context():
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return
        
        BATCH_SIZE = 500
        batch_count = 0
        failed_recipients = [r for r in campaign.recipients if r.error_message and not r.sent]
        smtp_conn = None
        
        try:
            smtp_conn = get_smtp_connection()
            
            for recipient in failed_recipients:
                db.session.refresh(campaign)
                if campaign.status != 'sending':
                    break
                
                recipient.error_message = None
                success, error = send_email_smtp(recipient, campaign, smtp_conn)
                
                if success:
                    recipient.sent = True
                    recipient.sent_at = datetime.utcnow()
                else:
                    recipient.error_message = error
                    if 'connection' in str(error).lower():
                        try:
                            smtp_conn.quit()
                        except:
                            pass
                        smtp_conn = get_smtp_connection()
                
                db.session.commit()
                batch_count += 1
                
                if batch_count >= BATCH_SIZE:
                    batch_count = 0
                    try:
                        smtp_conn.quit()
                    except:
                        pass
                    smtp_conn = get_smtp_connection()
        
        finally:
            if smtp_conn:
                try:
                    smtp_conn.quit()
                except:
                    pass
        
        total_errors = len([r for r in campaign.recipients if r.error_message])
        campaign.status = 'sent' if total_errors == 0 else 'sent_with_errors'
        db.session.commit()


@app.route('/api/campaigns/<campaign_id>/retry', methods=['POST'])
@login_required
def retry_failed(campaign_id):
    """Reintentar envío a destinatarios fallidos"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if not Config.SES_SMTP_USERNAME or not Config.SES_SMTP_PASSWORD:
        return jsonify({'error': 'Credenciales SES no configuradas'}), 400
    
    failed_count = len([r for r in campaign.recipients if r.error_message and not r.sent])
    
    if failed_count == 0:
        return jsonify({'error': 'No hay envíos fallidos para reintentar'}), 400
    
    if campaign.status == 'sending':
        return jsonify({'error': 'Ya hay un envío en progreso'}), 400
    
    campaign.status = 'sending'
    db.session.commit()
    
    thread = threading.Thread(target=retry_emails_background, args=(campaign_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': f'Reintentando {failed_count} envíos fallidos en segundo plano.',
        'retrying': failed_count,
        'status': 'sending'
    })


@app.route('/api/campaigns/<campaign_id>/stop', methods=['POST'])
@login_required
def stop_campaign(campaign_id):
    """Detener el envío de una campaña"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if campaign.status != 'sending':
        return jsonify({'error': 'La campaña no está en envío'}), 400
    
    campaign.status = 'stopped'
    db.session.commit()
    
    return jsonify({'message': 'Envío detenido. Puedes reanudarlo después.'})


# ============ TRACKING ENDPOINTS ============

@app.route('/track/open/<tracking_token>')
def track_open(tracking_token):
    """Registrar apertura de email"""
    recipient = Recipient.query.filter_by(tracking_token=tracking_token).first()
    
    if recipient and not recipient.opened_at:
        recipient.opened_at = datetime.utcnow()
        db.session.commit()
    
    # Retornar imagen transparente 1x1
    transparent_pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return Response(transparent_pixel, mimetype='image/gif')


@app.route('/track/click/<tracking_token>')
def track_click(tracking_token):
    """Registrar clic en link"""
    recipient = Recipient.query.filter_by(tracking_token=tracking_token).first()
    
    if recipient:
        # Registrar el clic (aunque ya haya hecho clic antes, actualizamos la fecha)
        recipient.clicked_at = datetime.utcnow()
        db.session.commit()
    
    # Redirigir al URL original
    original_url = request.args.get('url', '/')
    original_url = unquote(original_url)
    
    # Validar que la URL sea segura (no javascript: ni data:)
    if original_url.startswith(('javascript:', 'data:', 'vbscript:')):
        original_url = '/'
    
    return redirect(original_url)


# ============ ESTADÍSTICAS ============

@app.route('/api/stats')
@login_required
def get_stats():
    """Obtener estadísticas generales"""
    total_campaigns = Campaign.query.count()
    total_sent = db.session.query(db.func.count(Recipient.id)).filter(Recipient.sent == True).scalar()
    total_opened = db.session.query(db.func.count(Recipient.id)).filter(Recipient.opened_at != None).scalar()
    total_clicked = db.session.query(db.func.count(Recipient.id)).filter(Recipient.clicked_at != None).scalar()
    
    return jsonify({
        'total_campaigns': total_campaigns,
        'total_sent': total_sent or 0,
        'total_opened': total_opened or 0,
        'total_clicked': total_clicked or 0,
        'global_open_rate': round((total_opened / total_sent * 100), 2) if total_sent else 0,
        'global_click_rate': round((total_clicked / total_sent * 100), 2) if total_sent else 0
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5010)

