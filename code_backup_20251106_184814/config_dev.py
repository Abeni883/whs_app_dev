import os

basedir = os.path.abspath(os.path.dirname(__file__))

class DevelopmentConfig:
    """Development-Konfiguration für lokale Entwicklung"""

    # SQLite Datenbank (DEVELOPMENT)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database', 'whs.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'dev-secret-key-not-for-production'

    # Upload-Konfiguration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Development-spezifische Konfiguration
    DEBUG = True
    TESTING = False
    ENV = 'development'

    # Logging
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = os.path.join(basedir, 'logs', 'development.log')
