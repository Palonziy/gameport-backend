from src.models.user import db
from datetime import datetime
import os

class MediaFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # 'image' or 'video'
    file_size = db.Column(db.Integer, nullable=False)  # bytes
    mime_type = db.Column(db.String(100), nullable=False)
    
    game_club_id = db.Column(db.Integer, db.ForeignKey('game_club.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_files')

    def __repr__(self):
        return f'<MediaFile {self.filename}>'

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_size_mb': round(self.file_size / (1024 * 1024), 2),
            'mime_type': self.mime_type,
            'game_club_id': self.game_club_id,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.full_name if self.uploader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'url': f'/api/media/{self.id}'
        }

    def delete_file(self):
        """Faylni diskdan o'chirish"""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            return True
        except Exception as e:
            print(f"Fayl o'chirishda xatolik: {e}")
            return False

    @staticmethod
    def validate_file_size(file_size, file_type):
        """Fayl hajmini tekshirish"""
        if file_type == 'image':
            max_size = 1 * 1024 * 1024  # 1MB
            if file_size > max_size:
                return False, "Rasm hajmi 1MB dan oshmasligi kerak"
        elif file_type == 'video':
            max_size = 10 * 1024 * 1024  # 10MB
            if file_size > max_size:
                return False, "Video hajmi 10MB dan oshmasligi kerak"
        return True, "OK"

    @staticmethod
    def validate_file_type(mime_type):
        """Fayl turini tekshirish"""
        allowed_images = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        allowed_videos = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv']
        
        if mime_type in allowed_images:
            return True, 'image'
        elif mime_type in allowed_videos:
            return True, 'video'
        else:
            return False, None

    @staticmethod
    def count_files_by_club_and_type(game_club_id, file_type):
        """Klub va fayl turi bo'yicha fayllar sonini hisoblash"""
        return MediaFile.query.filter_by(
            game_club_id=game_club_id,
            file_type=file_type,
            is_active=True
        ).count()

