from flask import Blueprint, request, jsonify
from src.models.user import User, db
from src.models.game_club import GameClub
from src.models.booking import Booking
from src.routes.auth import token_required, superadmin_required
from sqlalchemy import func
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/list', methods=['GET'])
@token_required
@superadmin_required
def get_admins(current_user):
    """Adminlar ro'yxati (faqat superadmin)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        query = User.query.filter_by(role='admin')
        
        if search:
            query = query.filter(
                (User.full_name.contains(search)) |
                (User.email.contains(search))
            )
        
        admins = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'admins': [admin.to_dict() for admin in admins.items],
            'total': admins.total,
            'pages': admins.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@admin_bp.route('/create', methods=['POST'])
@token_required
@superadmin_required
def create_admin(current_user):
    """Admin yaratish (faqat superadmin)"""
    try:
        data = request.get_json()
        
        required_fields = ['full_name', 'email', 'password', 'game_club_name', 'address', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} talab qilinadi'}), 400
        
        # Email tekshirish
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Bu email allaqachon mavjud'}), 400
        
        # Game club yaratish
        game_club = GameClub(
            name=data['game_club_name'],
            description=data.get('description', ''),
            address=data['address'],
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            phone=data['phone']
        )
        db.session.add(game_club)
        db.session.flush()  # ID olish uchun
        
        # Admin yaratish
        admin = User(
            full_name=data['full_name'],
            email=data['email'],
            role='admin',
            phone=data['phone'],
            additional_phone=data.get('additional_phone'),
            game_club_id=game_club.id
        )
        admin.set_password(data['password'])
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'message': 'Admin muvaffaqiyatli yaratildi',
            'admin': admin.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@admin_bp.route('/<int:admin_id>', methods=['GET'])
@token_required
@superadmin_required
def get_admin(current_user, admin_id):
    """Admin ma'lumotlarini olish"""
    try:
        admin = User.query.filter_by(id=admin_id, role='admin').first()
        
        if not admin:
            return jsonify({'message': 'Admin topilmadi'}), 404
        
        return jsonify({'admin': admin.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@admin_bp.route('/<int:admin_id>', methods=['PUT'])
@token_required
@superadmin_required
def update_admin(current_user, admin_id):
    """Admin ma'lumotlarini yangilash"""
    try:
        admin = User.query.filter_by(id=admin_id, role='admin').first()
        
        if not admin:
            return jsonify({'message': 'Admin topilmadi'}), 404
        
        data = request.get_json()
        
        # Email tekshirish (o'zgargan bo'lsa)
        if data.get('email') and data['email'] != admin.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'message': 'Bu email allaqachon mavjud'}), 400
            admin.email = data['email']
        
        # Ma'lumotlarni yangilash
        if data.get('full_name'):
            admin.full_name = data['full_name']
        if data.get('phone'):
            admin.phone = data['phone']
        if data.get('additional_phone'):
            admin.additional_phone = data['additional_phone']
        if 'is_active' in data:
            admin.is_active = data['is_active']
        
        # Parolni yangilash (agar berilgan bo'lsa)
        if data.get('password'):
            admin.set_password(data['password'])
        
        # Game club ma'lumotlarini yangilash
        if admin.game_club and data.get('game_club'):
            club_data = data['game_club']
            if club_data.get('name'):
                admin.game_club.name = club_data['name']
            if club_data.get('description'):
                admin.game_club.description = club_data['description']
            if club_data.get('address'):
                admin.game_club.address = club_data['address']
            if club_data.get('phone'):
                admin.game_club.phone = club_data['phone']
            if club_data.get('latitude'):
                admin.game_club.latitude = club_data['latitude']
            if club_data.get('longitude'):
                admin.game_club.longitude = club_data['longitude']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Admin muvaffaqiyatli yangilandi',
            'admin': admin.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@admin_bp.route('/<int:admin_id>', methods=['DELETE'])
@token_required
@superadmin_required
def delete_admin(current_user, admin_id):
    """Adminni o'chirish"""
    try:
        admin = User.query.filter_by(id=admin_id, role='admin').first()
        
        if not admin:
            return jsonify({'message': 'Admin topilmadi'}), 404
        
        # Game club ham o'chiriladi (cascade)
        db.session.delete(admin)
        db.session.commit()
        
        return jsonify({'message': 'Admin muvaffaqiyatli o\'chirildi'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@admin_bp.route('/statistics', methods=['GET'])
@token_required
@superadmin_required
def get_admin_statistics(current_user):
    """Adminlar statistikasi"""
    try:
        # Umumiy adminlar soni
        total_admins = User.query.filter_by(role='admin').count()
        active_admins = User.query.filter_by(role='admin', is_active=True).count()
        
        # Oylik tushum (barcha klublar)
        current_month = datetime.now().replace(day=1)
        monthly_revenue = db.session.query(func.sum(Booking.total_price)).filter(
            Booking.created_at >= current_month,
            Booking.is_completed == True
        ).scalar() or 0
        
        # Eng faol klublar (oxirgi 30 kun)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        top_clubs = db.session.query(
            GameClub.name,
            func.count(Booking.id).label('bookings_count'),
            func.sum(Booking.total_price).label('revenue')
        ).join(Booking).filter(
            Booking.created_at >= thirty_days_ago
        ).group_by(GameClub.id).order_by(
            func.count(Booking.id).desc()
        ).limit(5).all()
        
        return jsonify({
            'total_admins': total_admins,
            'active_admins': active_admins,
            'monthly_revenue': monthly_revenue,
            'top_clubs': [
                {
                    'name': club.name,
                    'bookings_count': club.bookings_count,
                    'revenue': club.revenue or 0
                }
                for club in top_clubs
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

