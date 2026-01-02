import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

try:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Test - Correo de Prueba'
    msg['From'] = f"{Config.SENDER_NAME} <{Config.SENDER_EMAIL}>"
    msg['To'] = input("Ingresa el email destinatario para prueba: ")
    
    html = "<h1>Email de Prueba</h1><p>Si recibes este correo, la configuración funciona correctamente.</p>"
    msg.attach(MIMEText(html, 'html'))
    
    print(f"\n📧 Enviando desde: {Config.SENDER_EMAIL}")
    print(f"📧 Nombre remitente: {Config.SENDER_NAME}")
    print(f"📧 Host SMTP: {Config.SES_SMTP_HOST}")
    print(f"📧 Destinatario: {msg['To']}\n")
    
    with smtplib.SMTP(Config.SES_SMTP_HOST, Config.SES_SMTP_PORT) as server:
        server.set_debuglevel(1)  # Ver debug completo
        server.starttls()
        server.login(Config.SES_SMTP_USERNAME, Config.SES_SMTP_PASSWORD)
        server.sendmail(Config.SENDER_EMAIL, msg['To'], msg.as_string())
    
    print("\n✅ EMAIL ENVIADO EXITOSAMENTE")
    print("\nRevisa:")
    print("1. Bandeja de entrada")
    print("2. Carpeta de SPAM")
    print("3. Puede tardar 1-2 minutos en llegar")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nPosibles causas:")
    print("- Email remitente no verificado en SES")
    print("- Cuenta SES en modo sandbox (solo envía a emails verificados)")
    print("- Credenciales incorrectas")
