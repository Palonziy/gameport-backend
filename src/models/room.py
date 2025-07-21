from src.models.user import db
from datetime import datetime

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # VIP xona, Premium xona, Ochiq zal
    computer_count = db.Column(db.Integer, nullable=False, default=1)
    hourly_price = db.Column(db.Integer, nullable=False)  # 1 soatlik narx
    
    # Texnik xususiyatlar (barcha kompyuterlar bir xil)
    cpu = db.Column(db.String(100), nullable=True)
    gpu = db.Column(db.String(100), nullable=True)
    ram = db.Column(db.String(50), nullable=True)
    storage = db.Column(db.String(50), nullable=True)
    
    game_club_id = db.Column(db.Integer, db.ForeignKey('game_club.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    computers = db.relationship('Computer', backref='room', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='room', lazy=True)

    def __repr__(self):
        return f'<Room {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'computer_count': self.computer_count,
            'hourly_price': self.hourly_price,
            'cpu': self.cpu,
            'gpu': self.gpu,
            'ram': self.ram,
            'storage': self.storage,
            'game_club_id': self.game_club_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'computers': [comp.to_dict() for comp in self.computers] if self.computers else [],
            'available_computers': len([comp for comp in self.computers if comp.is_available]) if self.computers else 0
        }

    def get_available_computers(self):
        """Bo'sh kompyuterlar ro'yxati"""
        return [comp for comp in self.computers if comp.is_available]

    def get_busy_computers(self):
        """Band kompyuterlar ro'yxati"""
        return [comp for comp in self.computers if not comp.is_available]

