from src.models.user import db
from datetime import datetime

class Computer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)  # Kompyuter raqami (1, 2, 3...)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    bookings = db.relationship('Booking', backref='computer', lazy=True)

    def __repr__(self):
        return f'<Computer {self.number} in Room {self.room_id}>'

    def to_dict(self):
        current_booking = self.get_current_booking()
        return {
            'id': self.id,
            'number': self.number,
            'room_id': self.room_id,
            'is_available': self.is_available,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'current_booking': current_booking.to_dict() if current_booking else None
        }

    def get_current_booking(self):
        """Hozirgi faol bronni qaytarish"""
        from src.models.booking import Booking
        return Booking.query.filter_by(
            computer_id=self.id,
            is_active=True
        ).filter(
            Booking.end_time > datetime.utcnow()
        ).first()

    def book(self, customer_username, start_time, end_time):
        """Kompyuterni bron qilish"""
        if not self.is_available:
            return False, "Kompyuter allaqachon band"
        
        self.is_available = False
        db.session.commit()
        return True, "Muvaffaqiyatli bron qilindi"

    def release(self):
        """Kompyuterni bo'shatish"""
        self.is_available = True
        db.session.commit()
        return True, "Kompyuter bo'shatildi"

