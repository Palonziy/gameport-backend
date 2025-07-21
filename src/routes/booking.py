from flask import Blueprint, request, jsonify
from src.models.user import User, db
from src.models.game_club import GameClub
from src.models.room import Room
from src.models.computer import Computer
from src.models.booking import Booking
from src.routes.auth import token_required, admin_required, superadmin_required
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/create', methods=['POST'])
@token_required
@admin_required
def create_booking(current_user):
    """Yangi bron yaratish"""
    try:
        if not current_user.game_club:
            return jsonify({'message': 'Sizga tegishli klub topilmadi'}), 404
        
        data = request.get_json()
        
        required_fields = ['customer_name', 'room_id', 'computer_number', 'start_time', 'duration_hours']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} talab qilinadi'}), 400
        
        # Xonani tekshirish
        room = Room.query.filter_by(
            id=data['room_id'],
            game_club_id=current_user.game_club.id,
            is_active=True
        ).first()
        
        if not room:
            return jsonify({'message': 'Xona topilmadi'}), 404
        
        # Kompyuterni tekshirish
        computer = Computer.query.filter_by(
            room_id=room.id,
            number=data['computer_number'],
            is_active=True
        ).first()
        
        if not computer:
            return jsonify({'message': 'Kompyuter topilmadi'}), 404
        
        # Vaqtni parse qilish
        try:
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        except:
            return jsonify({'message': 'Noto\'g\'ri vaqt formati'}), 400
        
        duration_hours = int(data['duration_hours'])
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Vaqt to'qnashuvini tekshirish
        conflicting_booking = Booking.query.filter(
            and_(
                Booking.computer_id == computer.id,
                Booking.is_active == True,
                or_(
                    and_(Booking.start_time <= start_time, Booking.end_time > start_time),
                    and_(Booking.start_time < end_time, Booking.end_time >= end_time),
                    and_(Booking.start_time >= start_time, Booking.end_time <= end_time)
                )
            )
        ).first()
        
        if conflicting_booking:
            return jsonify({'message': 'Bu vaqtda kompyuter band'}), 400
        
        # Narxni hisoblash
        club = current_user.game_club
        total_price = 0
        
        # Soatlik narxni hisoblash (xona narxi yoki klub narxi)
        hourly_price = room.hourly_price if room.hourly_price else club.day_price
        
        # Aksiya tekshirish
        if duration_hours >= club.promo_hours and club.promo_price:
            total_price = club.promo_price
        else:
            total_price = hourly_price * duration_hours
        
        # Bronni yaratish
        booking = Booking(
            customer_name=data['customer_name'],
            start_time=start_time,
            end_time=end_time,
            duration_hours=duration_hours,
            total_price=total_price,
            computer_id=computer.id,
            room_id=room.id,
            game_club_id=current_user.game_club.id,
            created_by=current_user.id
        )
        
        db.session.add(booking)
        
        # Kompyuterni band qilish
        computer.is_available = False
        computer.current_booking_id = booking.id
        
        db.session.commit()
        
        return jsonify({
            'message': 'Bron muvaffaqiyatli yaratildi',
            'booking': booking.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@booking_bp.route('/my-bookings', methods=['GET'])
@token_required
def get_my_bookings(current_user):
    """O'z bronlarimni olish"""
    try:
        if current_user.role == 'superadmin':
            # Superadmin barcha bronlarni ko'radi
            bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        elif current_user.role == 'admin' and current_user.game_club:
            # Admin faqat o'z klubidagi bronlarni ko'radi
            bookings = Booking.query.filter_by(
                game_club_id=current_user.game_club.id
            ).order_by(Booking.created_at.desc()).all()
        else:
            return jsonify({'message': 'Ruxsat yo\'q'}), 403
        
        return jsonify({
            'bookings': [booking.to_dict() for booking in bookings]
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@booking_bp.route('/<int:booking_id>/complete', methods=['POST'])
@token_required
@admin_required
def complete_booking(current_user, booking_id):
    """Bronni yakunlash"""
    try:
        booking = Booking.query.filter_by(id=booking_id).first()
        
        if not booking:
            return jsonify({'message': 'Bron topilmadi'}), 404
        
        # Faqat o'z klubidagi bronlarni yakunlash mumkin
        if current_user.role == 'admin' and booking.game_club_id != current_user.game_club.id:
            return jsonify({'message': 'Ruxsat yo\'q'}), 403
        
        if not booking.is_active:
            return jsonify({'message': 'Bron allaqachon yakunlangan'}), 400
        
        # Bronni yakunlash
        booking.is_active = False
        booking.is_completed = True
        booking.completed_at = datetime.utcnow()
        
        # Kompyuterni bo'shatish
        computer = Computer.query.get(booking.computer_id)
        if computer:
            computer.is_available = True
            computer.current_booking_id = None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Bron muvaffaqiyatli yakunlandi',
            'booking': booking.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@booking_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@token_required
@admin_required
def cancel_booking(current_user, booking_id):
    """Bronni bekor qilish"""
    try:
        booking = Booking.query.filter_by(id=booking_id).first()
        
        if not booking:
            return jsonify({'message': 'Bron topilmadi'}), 404
        
        # Faqat o'z klubidagi bronlarni bekor qilish mumkin
        if current_user.role == 'admin' and booking.game_club_id != current_user.game_club.id:
            return jsonify({'message': 'Ruxsat yo\'q'}), 403
        
        if not booking.is_active:
            return jsonify({'message': 'Bron allaqachon yakunlangan'}), 400
        
        # Bronni bekor qilish
        booking.is_active = False
        booking.is_cancelled = True
        booking.cancelled_at = datetime.utcnow()
        
        # Kompyuterni bo'shatish
        computer = Computer.query.get(booking.computer_id)
        if computer:
            computer.is_available = True
            computer.current_booking_id = None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Bron muvaffaqiyatli bekor qilindi',
            'booking': booking.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@booking_bp.route('/expired/update', methods=['POST'])
@token_required
def update_expired_bookings(current_user):
    """Muddati tugagan bronlarni yangilash"""
    try:
        current_time = datetime.utcnow()
        
        # Muddati tugagan faol bronlarni topish
        expired_bookings = Booking.query.filter(
            and_(
                Booking.is_active == True,
                Booking.end_time <= current_time
            )
        ).all()
        
        updated_count = 0
        
        for booking in expired_bookings:
            booking.is_active = False
            booking.is_expired = True
            booking.expired_at = current_time
            
            # Kompyuterni bo'shatish
            computer = Computer.query.get(booking.computer_id)
            if computer:
                computer.is_available = True
                computer.current_booking_id = None
            
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'{updated_count} ta muddati tugagan bron yangilandi'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@booking_bp.route('/statistics', methods=['GET'])
@token_required
def get_booking_statistics(current_user):
    """Bron statistikasi"""
    try:
        if current_user.role == 'superadmin':
            # Superadmin uchun barcha statistika
            total_bookings = Booking.query.count()
            active_bookings = Booking.query.filter_by(is_active=True).count()
            completed_bookings = Booking.query.filter_by(is_completed=True).count()
            expired_bookings = Booking.query.filter_by(is_expired=True).count()
            
        elif current_user.role == 'admin' and current_user.game_club:
            # Admin uchun faqat o'z klubidagi statistika
            club_id = current_user.game_club.id
            total_bookings = Booking.query.filter_by(game_club_id=club_id).count()
            active_bookings = Booking.query.filter_by(game_club_id=club_id, is_active=True).count()
            completed_bookings = Booking.query.filter_by(game_club_id=club_id, is_completed=True).count()
            expired_bookings = Booking.query.filter_by(game_club_id=club_id, is_expired=True).count()
            
        else:
            return jsonify({'message': 'Ruxsat yo\'q'}), 403
        
        return jsonify({
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'completed_bookings': completed_bookings,
            'expired_bookings': expired_bookings
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

