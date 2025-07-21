import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.game_club import GameClub
from src.models.room import Room
from src.models.computer import Computer
from src.models.booking import Booking
from src.models.media_file import MediaFile

# Routes import
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp
from src.routes.game_club import game_club_bp
from src.routes.booking import booking_bp
from src.routes.media import media_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'gameport_secret_key_2024'
app.config['JWT_SECRET_KEY'] = 'gameport_jwt_secret_2024'

# CORS sozlamalari
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Blueprintlarni ro'yxatdan o'tkazish
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(game_club_bp, url_prefix='/api/game-club')
app.register_blueprint(booking_bp, url_prefix='/api/booking')
app.register_blueprint(media_bp, url_prefix='/api/media')

# Ma'lumotlar bazasi sozlamalari
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Upload papkasini yaratish
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
with app.app_context():
    db.create_all()
    
    # Superadmin yaratish (agar mavjud bo'lmasa)
    from src.models.user import User
    superadmin = User.query.filter_by(email='superadmin@gameport.uz').first()
    if not superadmin:
        superadmin = User(
            full_name='Super Admin',
            email='superadmin@gameport.uz',
            role='superadmin'
        )
        superadmin.set_password('admin123')
        db.session.add(superadmin)
        db.session.commit()
        print("Superadmin yaratildi: superadmin@gameport.uz / admin123")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
