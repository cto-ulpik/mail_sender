from flask import Flask, render_template, request, jsonify, redirect, Response
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

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

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
    
    # Modificar todos los enlaces <a href="..."> para que pasen por el tracking
    def replace_link(match):
        original_tag = match.group(0)
        # El grupo 2 es el URL en href="url"
        url = match.group(2) if match.lastindex >= 2 else ''
        
        if not url:
            return original_tag
        
        # No modificar enlaces que ya sean de tracking o enlaces javascript/mailto/data
        if '/track/' in url or url.startswith(('javascript:', 'mailto:', '#', 'data:', 'vbscript:')):
            return original_tag
        
        # Crear URL de tracking
        encoded_url = quote(url, safe='')
        tracking_url = f"{base_url}/track/click/{tracking_token}?url={encoded_url}"
        
        # Reemplazar el href en el tag
        return original_tag.replace(f'href="{url}"', f'href="{tracking_url}"').replace(f"href='{url}'", f"href='{tracking_url}'")
    
    # Buscar y reemplazar todos los enlaces <a href="...">
    # Patrón mejorado para capturar href con comillas simples o dobles
    html_content = re.sub(
        r'<a\s+([^>]*\s+)?href=(["\'])([^"\']+)\2([^>]*)>',
        replace_link,
        html_content,
        flags=re.IGNORECASE
    )
    
    return html_content


# ============ RUTAS WEB ============

@app.route('/')
def index():
    """Página principal - Dashboard"""
    return render_template('index.html')


@app.route('/campaign/new')
def new_campaign():
    """Página para crear nueva campaña"""
    return render_template('new_campaign.html')


@app.route('/campaign/<campaign_id>')
def view_campaign(campaign_id):
    """Ver detalles de una campaña"""
    return render_template('campaign_detail.html', campaign_id=campaign_id)


# ============ API ENDPOINTS ============

@app.route('/api/senders', methods=['GET'])
def get_senders():
    """Obtener lista de remitentes disponibles"""
    senders = Config.get_senders()
    return jsonify(senders)


@app.route('/api/campaigns', methods=['GET'])
def get_campaigns():
    """Obtener todas las campañas"""
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return jsonify([c.to_dict() for c in campaigns])


@app.route('/api/campaigns/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Obtener una campaña específica"""
    campaign = Campaign.query.get_or_404(campaign_id)
    return jsonify(campaign.to_dict())


@app.route('/api/campaigns/<campaign_id>/recipients', methods=['GET'])
def get_campaign_recipients(campaign_id):
    """Obtener recipients de una campaña"""
    campaign = Campaign.query.get_or_404(campaign_id)
    return jsonify([r.to_dict() for r in campaign.recipients])


@app.route('/api/campaigns', methods=['POST'])
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
def add_recipients(campaign_id):
    """Agregar recipients desde CSV"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Archivo vacío'}), 400
    
    try:
        # Leer CSV
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        
        added = 0
        for row in reader:
            # Detectar columna de email (varios formatos posibles)
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
            
            # Detectar columna de nombre (varios formatos posibles)
            name = (
                row.get('name', '') or 
                row.get('Name', '') or 
                row.get('NAME', '') or
                row.get('nombre', '') or
                row.get('Nombre', '') or
                ''
            ).strip()
            
            if email and '@' in email:
                recipient = Recipient(
                    campaign_id=campaign.id,
                    email=email,
                    name=name if name else None
                )
                db.session.add(recipient)
                added += 1
        
        db.session.commit()
        return jsonify({'message': f'Se agregaron {added} destinatarios', 'count': added})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


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

