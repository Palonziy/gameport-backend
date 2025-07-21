from src.models.user import db
from datetime import datetime

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_username = db.Column(db.String(100), nullable=False)
    
    # Bron ma'lumotlari
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_hours = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    
    # Foreign keys
    game_club_id = db.Column(db.Integer, db.ForeignKey('game_club.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    computer_id = db.Column(db.Integer, db.ForeignKey('computer.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('User', backref='created_bookings')

    def __repr__(self):
        return f'<Booking {self.customer_username} - Computer {self.computer_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_username': self.customer_username,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_hours': self.total_hours,
            'total_price': self.total_price,
            'game_club_id': self.game_club_id,
            'room_id': self.room_id,
            'computer_id': self.computer_id,
            'admin_id': self.admin_id,
            'is_active': self.is_active,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'game_club_name': self.game_club.name if self.game_club else None,
            'room_name': self.room.name if self.room else None,
            'computer_number': self.computer.number if self.computer else None,
            'admin_name': self.admin.full_name if self.admin else None
        }

    def is_expired(self):
        """Bron muddati tugaganmi?"""
        return datetime.utcnow() > self.end_time

    def complete_booking(self):
        """Bronni yakunlash"""
        self.is_completed = True
        self.is_active = False
        # Kompyuterni bo'shatish
        if self.computer:
            self.computer.release()
        db.session.commit()

    def calculate_price(self, room_hourly_price, total_hours):
        """Narxni hisoblash"""
        return int(room_hourly_price * total_hours)

    @staticmethod
    def get_active_bookings():
        """Faol bronlar ro'yxati"""
        return Booking.query.filter_by(is_active=True).filter(
            Booking.end_time > datetime.utcnow()
        ).all()

    @staticmethod
    def get_expired_bookings():
        """Muddati tugagan bronlar"""
        return Booking.query.filter_by(is_active=True).filter(
            Booking.end_time <= datetime.utcnow()
        ).all()

    @staticmethod
    def cleanup_expired_bookings():
        """Muddati tugagan bronlarni tozalash"""
        expired_bookings = Booking.get_expired_bookings()
        for booking in expired_bookings:
            booking.complete_booking()
        return len(expired_bookings)

