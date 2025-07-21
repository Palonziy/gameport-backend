from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')  # 'admin' or 'superadmin'
    phone = db.Column(db.String(20), nullable=True)
    additional_phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Admin uchun game club bilan bog'lanish
    game_club_id = db.Column(db.Integer, db.ForeignKey('game_club.id'), nullable=True)
    game_club = db.relationship('GameClub', backref='admin', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'additional_phone': self.additional_phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'game_club_id': self.game_club_id,
            'game_club': self.game_club.to_dict() if self.game_club else None
        }
