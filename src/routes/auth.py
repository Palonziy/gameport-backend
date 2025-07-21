from flask import Blueprint, request, jsonify, current_app
from src.models.user import User, db
import jwt
from datetime import datetime, timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """JWT token tekshirish decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Header dan token olish
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # "Bearer TOKEN"
            except IndexError:
                return jsonify({'message': 'Token formati noto\'g\'ri'}), 401
        
        if not token:
            return jsonify({'message': 'Token topilmadi'}), 401
        
        try:
            # Token ni decode qilish
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['user_id']).first()
            
            if not current_user or not current_user.is_active:
                return jsonify({'message': 'Foydalanuvchi topilmadi yoki faol emas'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token muddati tugagan'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Noto\'g\'ri token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """Admin yoki superadmin huquqi tekshirish"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role not in ['admin', 'superadmin']:
            return jsonify({'message': 'Admin huquqi talab qilinadi'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

def superadmin_required(f):
    """Superadmin huquqi tekshirish"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'superadmin':
            return jsonify({'message': 'Superadmin huquqi talab qilinadi'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['POST'])
def login():
    """Kirish"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email va parol talab qilinadi'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'message': 'Email yoki parol noto\'g\'ri'}), 401
        
        if not user.is_active:
            return jsonify({'message': 'Foydalanuvchi faol emas'}), 401
        
        # JWT token yaratish
        token = jwt.encode({
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(days=7)  # 7 kun
        }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Muvaffaqiyatli kirildi',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """Token tekshirish"""
    return jsonify({
        'message': 'Token to\'g\'ri',
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """Chiqish (frontend da token o'chiriladi)"""
    return jsonify({'message': 'Muvaffaqiyatli chiqildi'}), 200

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Parolni o'zgartirish"""
    try:
        data = request.get_json()
        
        if not data or not data.get('old_password') or not data.get('new_password'):
            return jsonify({'message': 'Eski va yangi parol talab qilinadi'}), 400
        
        if not current_user.check_password(data['old_password']):
            return jsonify({'message': 'Eski parol noto\'g\'ri'}), 400
        
        if len(data['new_password']) < 6:
            return jsonify({'message': 'Yangi parol kamida 6 ta belgidan iborat bo\'lishi kerak'}), 400
        
        current_user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Parol muvaffaqiyatli o\'zgartirildi'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

