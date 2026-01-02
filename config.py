import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Amazon SES SMTP Configuration
    SES_SMTP_HOST = os.getenv('SES_SMTP_HOST', 'email-smtp.us-east-1.amazonaws.com')
    SES_SMTP_PORT = int(os.getenv('SES_SMTP_PORT', 587))
    SES_SMTP_USERNAME = os.getenv('SES_SMTP_USERNAME', '')
    SES_SMTP_PASSWORD = os.getenv('SES_SMTP_PASSWORD', '')
    
    # Sender configuration - Multiple senders
    # Sender 1 (default)
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
    SENDER_NAME = os.getenv('SENDER_NAME', 'Cursos De Shunsho A Crack')
    
    # Sender 2
    SENDER2_EMAIL = os.getenv('SENDER2_EMAIL', 'churchill@ulpik.com')
    SENDER2_NAME = os.getenv('SENDER2_NAME', 'Churchill de Ulpik')
    
    @staticmethod
    def get_senders():
        """Retorna lista de remitentes disponibles"""
        senders = []
        
        # Sender 1
        if Config.SENDER_EMAIL:
            senders.append({
                'email': Config.SENDER_EMAIL,
                'name': Config.SENDER_NAME,
                'id': 'sender1'
            })
        
        # Sender 2
        if Config.SENDER2_EMAIL:
            senders.append({
                'email': Config.SENDER2_EMAIL,
                'name': Config.SENDER2_NAME,
                'id': 'sender2'
            })
        
        return senders
    
    # Application settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    BASE_URL = os.getenv('BASE_URL', 'https://mails.ulpik.com')
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///email_campaigns.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False















