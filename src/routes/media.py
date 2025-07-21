from flask import Blueprint, request, jsonify, send_file
from src.models.user import User, db
from src.models.media_file import MediaFile
from src.routes.auth import token_required, admin_required
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

media_bp = Blueprint('media', __name__)

# Fayl yuklash sozlamalari
UPLOAD_FOLDER = 'uploads'
MAX_IMAGE_SIZE = 1 * 1024 * 1024  # 1MB
MAX_VIDEO_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGES_PER_CLUB = 4
MAX_VIDEOS_PER_CLUB = 3

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'}

def allowed_file(filename, file_type):
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'image':
        return extension in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'video':
        return extension in ALLOWED_VIDEO_EXTENSIONS
    
    return False

def get_file_type(filename):
    if '.' not in filename:
        return None
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    if extension in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    elif extension in ALLOWED_VIDEO_EXTENSIONS:
        return 'video'
    
    return None

@media_bp.route('/upload', methods=['POST'])
@token_required
@admin_required
def upload_file(current_user):
    """Fayl yuklash"""
    try:
        if not current_user.game_club:
            return jsonify({'message': 'Sizga tegishli klub topilmadi'}), 404
        
        if 'file' not in request.files:
            return jsonify({'message': 'Fayl tanlanmadi'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'message': 'Fayl tanlanmadi'}), 400
        
        # Fayl turini aniqlash
        file_type = get_file_type(file.filename)
        if not file_type:
            return jsonify({'message': 'Noto\'g\'ri fayl turi'}), 400
        
        # Fayl hajmini tekshirish
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_type == 'image' and file_size > MAX_IMAGE_SIZE:
            return jsonify({'message': f'Rasm hajmi {MAX_IMAGE_SIZE // (1024*1024)}MB dan oshmasligi kerak'}), 400
        
        if file_type == 'video' and file_size > MAX_VIDEO_SIZE:
            return jsonify({'message': f'Video hajmi {MAX_VIDEO_SIZE // (1024*1024)}MB dan oshmasligi kerak'}), 400
        
        # Mavjud fayllar sonini tekshirish
        club_id = current_user.game_club.id
        
        if file_type == 'image':
            current_images = MediaFile.query.filter_by(
                game_club_id=club_id,
                file_type='image',
                is_active=True
            ).count()
            
            if current_images >= MAX_IMAGES_PER_CLUB:
                return jsonify({'message': f'Maksimal {MAX_IMAGES_PER_CLUB} ta rasm yuklash mumkin'}), 400
        
        elif file_type == 'video':
            current_videos = MediaFile.query.filter_by(
                game_club_id=club_id,
                file_type='video',
                is_active=True
            ).count()
            
            if current_videos >= MAX_VIDEOS_PER_CLUB:
                return jsonify({'message': f'Maksimal {MAX_VIDEOS_PER_CLUB} ta video yuklash mumkin'}), 400
        
        # Fayl nomini xavfsiz qilish
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Upload papkasini yaratish
        upload_path = os.path.join(UPLOAD_FOLDER, file_type + 's')
        os.makedirs(upload_path, exist_ok=True)
        
        # Faylni saqlash
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        # Ma'lumotlar bazasiga saqlash
        media_file = MediaFile(
            original_filename=filename,
            stored_filename=unique_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            file_size_mb=round(file_size / (1024 * 1024), 2),
            game_club_id=club_id
        )
        
        db.session.add(media_file)
        db.session.commit()
        
        return jsonify({
            'message': 'Fayl muvaffaqiyatli yuklandi',
            'file': media_file.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@media_bp.route('/my-files', methods=['GET'])
@token_required
@admin_required
def get_my_files(current_user):
    """O'z fayllarimni olish"""
    try:
        if not current_user.game_club:
            return jsonify({'message': 'Sizga tegishli klub topilmadi'}), 404
        
        files = MediaFile.query.filter_by(
            game_club_id=current_user.game_club.id,
            is_active=True
        ).order_by(MediaFile.created_at.desc()).all()
        
        return jsonify({
            'files': [file.to_dict() for file in files]
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@media_bp.route('/limits', methods=['GET'])
@token_required
@admin_required
def get_upload_limits(current_user):
    """Yuklash limitlarini olish"""
    try:
        if not current_user.game_club:
            return jsonify({'message': 'Sizga tegishli klub topilmadi'}), 404
        
        club_id = current_user.game_club.id
        
        current_images = MediaFile.query.filter_by(
            game_club_id=club_id,
            file_type='image',
            is_active=True
        ).count()
        
        current_videos = MediaFile.query.filter_by(
            game_club_id=club_id,
            file_type='video',
            is_active=True
        ).count()
        
        return jsonify({
            'images': {
                'current': current_images,
                'max': MAX_IMAGES_PER_CLUB,
                'remaining': MAX_IMAGES_PER_CLUB - current_images
            },
            'videos': {
                'current': current_videos,
                'max': MAX_VIDEOS_PER_CLUB,
                'remaining': MAX_VIDEOS_PER_CLUB - current_videos
            },
            'size_limits': {
                'image_mb': MAX_IMAGE_SIZE // (1024 * 1024),
                'video_mb': MAX_VIDEO_SIZE // (1024 * 1024)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@media_bp.route('/<int:file_id>', methods=['GET'])
def get_file(file_id):
    """Faylni olish"""
    try:
        media_file = MediaFile.query.filter_by(id=file_id, is_active=True).first()
        
        if not media_file:
            return jsonify({'message': 'Fayl topilmadi'}), 404
        
        if not os.path.exists(media_file.file_path):
            return jsonify({'message': 'Fayl mavjud emas'}), 404
        
        return send_file(media_file.file_path, as_attachment=False)
        
    except Exception as e:
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

@media_bp.route('/<int:file_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_file(current_user, file_id):
    """Faylni o'chirish"""
    try:
        media_file = MediaFile.query.filter_by(
            id=file_id,
            game_club_id=current_user.game_club.id,
            is_active=True
        ).first()
        
        if not media_file:
            return jsonify({'message': 'Fayl topilmadi'}), 404
        
        # Faylni disk dan o'chirish
        if os.path.exists(media_file.file_path):
            os.remove(media_file.file_path)
        
        # Ma'lumotlar bazasidan o'chirish
        media_file.is_active = False
        media_file.deleted_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Fayl muvaffaqiyatli o\'chirildi'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Xatolik: {str(e)}'}), 500

