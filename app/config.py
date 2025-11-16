"""
Application Configuration
Store all configuration variables here
SECURITY NOTE: Never commit sensitive credentials to Git
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Secret key for session management (generate with: python -c 'import secrets; print(secrets.token_hex(32))')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'foodlink_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'your_password'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'foodlink_db'
    
    # Upload configuration (for income proof documents)
    UPLOAD_FOLDER = 'app/static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    
    # Food pickup time window
    PICKUP_START_TIME = '13:00'  # 1:00 PM
    PICKUP_END_TIME = '13:45'    # 1:45 PM
    
    # Client number format (e.g., LOC-001, LOC-002)
    CLIENT_NUMBER_PREFIX = 'FL'


