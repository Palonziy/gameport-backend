from flask import Blueprint, request, jsonify
from src.models.user import User, db
from src.models.game_club import GameClub
from src.models.room import Room
from src.models.computer import Computer
from src.models.booking import Booking
from src.routes.auth import token_required, admin_required
from sqlalchemy import func
from datetime import datetime, timedelta

game_club_bp = Blueprint('game_club', __name__)

@game_club_bp.route('/my-club', methods=['GET'])
@token_required
@admin_required
def get_my_club(current_user):
    """O'z klubini olish (admin)"""
    try:
        if not current_user.game_club:
            return jsonify({'message': 'Sizga tegishli klub topilmadi'}), 404
        
        return jsonify({'club': current_user.game_club.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@game_club_bp.route('/my-club', methods=['PUT'])
@token_required
@admin_required
def update_my_club(current_user):
    """O'z klubini yangilash (admin)"""
    try:
        if not current_user.game_club:
            return jsonify({'message': 'Sizga tegishli klub topilmadi'}), 404
        
        data = request.get_json()
        club = current_user.game_club
        
        # Ma'lumotlarni yangilash
        if data.get('name'):
            club.name = data['name']
        if data.get('description'):
            club.description = data['description']
        if data.get('address'):
            club.address = data['address']
        if data.get('phone'):
            club.phone = data['phone']
        if data.get('latitude'):
            club.latitude = data['latitude']
        if data.get('longitude'):
            club.longitude = data['longitude']
        if data.get('work_start_time'):
            club.work_start_time = data['work_start_time']
        if data.get('work_end_time'):
            club.work_end_time = data['work_end_time']
        if data.get('day_price'):
            club.day_price = data['day_price']
        if data.get('night_price'):
            club.night_price = data['night_price']
        if data.get('promo_hours'):
            club.promo_hours = data['promo_hours']
        if data.get('promo_price'):
            club.promo_price = data['promo_price']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Klub ma\'lumotlari muvaffaqiyatli yangilandi',
            'club': club.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@game_club_bp.route('/rooms', methods=['GET'])
@token_required
@admin_required
def get_my_rooms(current_user):
    """O'z klubidagi xonalar ro'yxati"""
    try:
        if not current_user.game_club:
            return jsonify({'message': 'Sizga tegishli klub topilmadi'}), 404
        
        rooms = Room.query.filter_by(
            game_club_id=current_user.game_club.id,
            is_active=True
        ).all()
        
        return jsonify({
            'rooms': [room.to_dict() for room in rooms]
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@game_club_bp.route('/rooms', methods=['POST'])
@token_required
@admin_required
def create_room(current_user):
    """Yangi xona yaratish"""
    try:
        if not current_user.game_club:
            return jsonify({'message': 'Sizga tegishli klub topilmadi'}), 404
        
        data = request.get_json()
        
        required_fields = ['name', 'computer_count', 'hourly_price']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} talab qilinadi'}), 400
        
        # Xona yaratish
        room = Room(
            name=data['name'],
            computer_count=data['computer_count'],
            hourly_price=data['hourly_price'],
            cpu=data.get('cpu'),
            gpu=data.get('gpu'),
            ram=data.get('ram'),
            storage=data.get('storage'),
            game_club_id=current_user.game_club.id
        )
        
        db.session.add(room)
        db.session.flush()  # ID olish uchun
        
        # Kompyuterlarni yaratish
        for i in range(1, data['computer_count'] + 1):
            computer = Computer(
                number=i,
                room_id=room.id
            )
            db.session.add(computer)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Xona muvaffaqiyatli yaratildi',
            'room': room.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@game_club_bp.route('/rooms/<int:room_id>', methods=['PUT'])
@token_required
@admin_required
def update_room(current_user, room_id):
    """Xonani yangilash"""
    try:
        room = Room.query.filter_by(
            id=room_id,
            game_club_id=current_user.game_club.id
        ).first()
        
        if not room:
            return jsonify({'message': 'Xona topilmadi'}), 404
        
        data = request.get_json()
        
        # Ma'lumotlarni yangilash
        if data.get('name'):
            room.name = data['name']
        if data.get('hourly_price'):
            room.hourly_price = data['hourly_price']
        if data.get('cpu'):
            room.cpu = data['cpu']
        if data.get('gpu'):
            room.gpu = data['gpu']
        if data.get('ram'):
            room.ram = data['ram']
        if data.get('storage'):
            room.storage = data['storage']
        
        # Kompyuter sonini yangilash
        if data.get('computer_count') and data['computer_count'] != room.computer_count:
            new_count = data['computer_count']
            current_count = room.computer_count
            
            if new_count > current_count:
                # Kompyuter qo'shish
                for i in range(current_count + 1, new_count + 1):
                    computer = Computer(number=i, room_id=room.id)
                    db.session.add(computer)
            elif new_count < current_count:
                # Kompyuter o'chirish (oxirgisidan)
                computers_to_delete = Computer.query.filter_by(room_id=room.id).filter(
                    Computer.number > new_count
                ).all()
                for comp in computers_to_delete:
                    if not comp.is_available:
                        return jsonify({'message': 'Band kompyuterlar mavjud, avval ularni bo\'shating'}), 400
                    db.session.delete(comp)
            
            room.computer_count = new_count
        
        db.session.commit()
        
        return jsonify({
            'message': 'Xona muvaffaqiyatli yangilandi',
            'room': room.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@game_club_bp.route('/rooms/<int:room_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_room(current_user, room_id):
    """Xonani o'chirish"""
    try:
        room = Room.query.filter_by(
            id=room_id,
            game_club_id=current_user.game_club.id
        ).first()
        
        if not room:
            return jsonify({'message': 'Xona topilmadi'}), 404
        
        # Faol bronlar tekshirish
        active_bookings = Booking.query.filter_by(
            room_id=room.id,
            is_active=True
        ).count()
        
        if active_bookings > 0:
            return jsonify({'message': 'Xonada faol bronlar mavjud, avval ularni yakunlang'}), 400
        
        db.session.delete(room)
        db.session.commit()
        
        return jsonify({'message': 'Xona muvaffaqiyatli o\'chirildi'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@game_club_bp.route('/dashboard', methods=['GET'])
@token_required
@admin_required
def get_dashboard_stats(current_user):
    """Admin dashboard statistikasi"""
    try:
        if not current_user.game_club:
            return jsonify({'message': 'Sizga tegishli klub topilmadi'}), 404
        
        club_id = current_user.game_club.id
        
        # Xonalar statistikasi
        total_rooms = Room.query.filter_by(game_club_id=club_id, is_active=True).count()
        
        # Kompyuterlar statistikasi
        total_computers = Computer.query.join(Room).filter(
            Room.game_club_id == club_id,
            Computer.is_active == True
        ).count()
        
        available_computers = Computer.query.join(Room).filter(
            Room.game_club_id == club_id,
            Computer.is_active == True,
            Computer.is_available == True
        ).count()
        
        busy_computers = total_computers - available_computers
        
        # Oylik tushum
        current_month = datetime.now().replace(day=1)
        monthly_revenue = db.session.query(func.sum(Booking.total_price)).filter(
            Booking.game_club_id == club_id,
            Booking.created_at >= current_month,
            Booking.is_completed == True
        ).scalar() or 0
        
        # Oxirgi bronlar
        recent_bookings = Booking.query.filter_by(game_club_id=club_id).order_by(
            Booking.created_at.desc()
        ).limit(5).all()
        
        # Oylik grafik ma'lumotlari (oxirgi 12 oy)
        monthly_data = []
        for i in range(12):
            month_start = (datetime.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            
            revenue = db.session.query(func.sum(Booking.total_price)).filter(
                Booking.game_club_id == club_id,
                Booking.created_at >= month_start,
                Booking.created_at < month_end,
                Booking.is_completed == True
            ).scalar() or 0
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': revenue
            })
        
        monthly_data.reverse()  # Eng eskisidan yangiisiga
        
        return jsonify({
            'total_rooms': total_rooms,
            'total_computers': total_computers,
            'available_computers': available_computers,
            'busy_computers': busy_computers,
            'monthly_revenue': monthly_revenue,
            'recent_bookings': [booking.to_dict() for booking in recent_bookings],
            'monthly_chart_data': monthly_data
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

