import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # SQLite Datenbank (PRODUCTION)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database', 'whs.db')
    
    # MySQL Datenbank (auskommentiert - für später)
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@localhost/whs_db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Upload-Konfiguration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # App-Konfiguration
    DEBUG = False
    TESTING = False
