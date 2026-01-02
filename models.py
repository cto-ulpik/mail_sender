from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Campaign(db.Model):
    """Representa una campaña de email"""
    __tablename__ = 'campaigns'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, sending, sent, failed
    
    # Relationships
    recipients = db.relationship('Recipient', backref='campaign', lazy=True, cascade='all, delete-orphan')
    
    @property
    def total_sent(self):
        return len([r for r in self.recipients if r.sent])
    
    @property
    def total_opened(self):
        return len([r for r in self.recipients if r.opened_at])
    
    @property
    def total_clicked(self):
        return len([r for r in self.recipients if r.clicked_at])
    
    @property
    def open_rate(self):
        if self.total_sent == 0:
            return 0
        return round((self.total_opened / self.total_sent) * 100, 2)
    
    @property
    def click_rate(self):
        if self.total_sent == 0:
            return 0
        return round((self.total_clicked / self.total_sent) * 100, 2)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'html_content': self.html_content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status,
            'total_recipients': len(self.recipients),
            'total_sent': self.total_sent,
            'total_opened': self.total_opened,
            'total_clicked': self.total_clicked,
            'open_rate': self.open_rate,
            'click_rate': self.click_rate
        }


class Recipient(db.Model):
    """Representa un destinatario de email"""
    __tablename__ = 'recipients'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False)
    email = db.Column(db.String(320), nullable=False)
    name = db.Column(db.String(200), nullable=True)
    sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    opened_at = db.Column(db.DateTime, nullable=True)
    clicked_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Tracking token único para este recipient
    tracking_token = db.Column(db.String(64), unique=True, default=lambda: str(uuid.uuid4()))
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'sent': self.sent,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'error_message': self.error_message
        }















