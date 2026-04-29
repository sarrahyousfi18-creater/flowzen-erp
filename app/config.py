import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'flowzen-super-secret-key-change-in-production-2026')
    JWT_SECRET = os.environ.get('JWT_SECRET', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///erp.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 30  # minutes
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Business Rules
    MAX_DISCOUNT_PERCENT = 60
    
    # File Uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = 'static/uploads'