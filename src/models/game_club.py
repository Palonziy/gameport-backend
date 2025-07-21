from src.models.user import db
from datetime import datetime

class GameClub(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    
    # Ish vaqti
    work_start_time = db.Column(db.String(5), nullable=False, default='07:00')  # HH:MM format
    work_end_time = db.Column(db.String(5), nullable=False, default='22:00')   # HH:MM format
    
    # Narxlar
    day_price = db.Column(db.Integer, nullable=False, default=12000)    # 07:00-22:00
    night_price = db.Column(db.Integer, nullable=False, default=20000)  # 22:00-06:00
    
    # Aksiya
    promo_hours = db.Column(db.Integer, nullable=True, default=3)       # 3 soat
    promo_price = db.Column(db.Integer, nullable=True, default=35000)   # 35 ming
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    rooms = db.relationship('Room', backref='game_club', lazy=True, cascade='all, delete-orphan')
    media_files = db.relationship('MediaFile', backref='game_club', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='game_club', lazy=True)

    def __repr__(self):
        return f'<GameClub {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'phone': self.phone,
            'work_start_time': self.work_start_time,
            'work_end_time': self.work_end_time,
            'day_price': self.day_price,
            'night_price': self.night_price,
            'promo_hours': self.promo_hours,
            'promo_price': self.promo_price,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'rooms_count': len(self.rooms) if self.rooms else 0,
            'media_files': [media.to_dict() for media in self.media_files] if self.media_files else []
        }

    def to_summary_dict(self):
        """Qisqa ma'lumot uchun"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'is_active': self.is_active,
            'rooms_count': len(self.rooms) if self.rooms else 0
        }

