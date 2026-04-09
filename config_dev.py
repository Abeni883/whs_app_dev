"""
Development-Konfiguration für die WHS Testprotokoll-Anwendung.

Diese Konfiguration ist für lokale Entwicklung optimiert mit:
- Aktiviertem Debug-Modus
- Ausführlichem Logging (DEBUG-Level)
- Hot-Reload für Templates
- SQLite-Datenbank (shared mit Production)
"""

import os
from datetime import timedelta

# Basis-Verzeichnis der Anwendung
basedir = os.path.abspath(os.path.dirname(__file__))


class DevelopmentConfig:
    """
    Development-Konfigurationsklasse für lokale Entwicklung.

    Features:
        - Debug-Modus aktiviert
        - Auto-Reload für Templates
        - Ausführliches Logging
        - Kürzere Session-Timeouts für Testing
        - Entspannte CORS-Policies

    Verwendung:
        app.config.from_object(DevelopmentConfig)
    """

    # ==================== DATENBANK-KONFIGURATION ====================

    # SQLite Datenbank (DEVELOPMENT)
    # Nutzt die gleiche Datenbank wie Production für Konsistenz
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database', 'whs_dev.db')

    # Deaktiviert Tracking von Objektänderungen
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Echo SQL-Queries in Konsole (für Debugging)
    SQLALCHEMY_ECHO = False  # Auf True setzen für SQL-Debugging

    # Verbindungspool-Konfiguration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }


    # ==================== SICHERHEITS-KONFIGURATION ====================

    # Development Secret Key (NICHT in Production verwenden!)
    SECRET_KEY = 'dev-secret-key-not-for-production'

    # Session-Konfiguration (relaxed für Development)
    SESSION_COOKIE_SECURE = False  # HTTP erlaubt (kein HTTPS erforderlich)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Längere Sessions beim Entwickeln

    # CSRF-Schutz (deaktiviert für API-Testing)
    WTF_CSRF_ENABLED = False  # Vereinfacht Testing mit curl/Postman
    WTF_CSRF_TIME_LIMIT = None


    # ==================== UPLOAD-KONFIGURATION ====================

    # Upload-Verzeichnis
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')

    # Maximale Upload-Größe (16 MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Erlaubte Datei-Endungen
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'csv', 'txt', 'json'}


    # ==================== APP-KONFIGURATION ====================

    # Debug-Modus (AKTIVIERT für Development!)
    DEBUG = True

    # Testing-Modus
    TESTING = False

    # Environment
    ENV = 'development'

    # JSON-Konfiguration (Pretty-Print für bessere Lesbarkeit)
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True  # Formatiertes JSON

    # Timezone
    TIMEZONE = 'Europe/Zurich'


    # ==================== LOGGING-KONFIGURATION ====================

    # Log-Verzeichnis
    LOG_FOLDER = os.path.join(basedir, 'logs')

    # Log-Level (DEBUG für ausführliches Logging)
    LOG_LEVEL = 'DEBUG'

    # Log-Datei
    LOG_FILE = os.path.join(LOG_FOLDER, 'development.log')

    # Maximale Log-Größe (5 MB)
    LOG_MAX_BYTES = 5 * 1024 * 1024

    # Anzahl Backup-Logs
    LOG_BACKUP_COUNT = 3


    # ==================== PERFORMANCE-KONFIGURATION ====================

    # Template-Auto-Reload (AKTIVIERT für Live-Updates)
    TEMPLATES_AUTO_RELOAD = True

    # Send-File-Max-Age (Kein Caching für sofortige Änderungen)
    SEND_FILE_MAX_AGE_DEFAULT = 0


    # ==================== DEVELOPMENT-TOOLS ====================

    # Flask-DebugToolbar (falls installiert)
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # Profiling (Performance-Analyse)
    PROFILE = False  # Auf True setzen für Profiling

    # Explain Template Loading (zeigt welche Templates geladen werden)
    EXPLAIN_TEMPLATE_LOADING = False


    @staticmethod
    def init_app(app):
        """
        Initialisiert Development-spezifische Konfigurationen.

        Args:
            app: Flask-Applikationsinstanz
        """
        # Stelle sicher, dass wichtige Verzeichnisse existieren
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)

        # Datenbank-Verzeichnis erstellen
        db_dir = os.path.join(basedir, 'database')
        os.makedirs(db_dir, exist_ok=True)

        # Development-Hinweise in Konsole ausgeben
        print("=" * 60)
        print("DEVELOPMENT MODE - Debug-Modus aktiviert")
        print(f"Datenbank: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Log-Level: {app.config['LOG_LEVEL']}")
        print(f"Templates Auto-Reload: {app.config['TEMPLATES_AUTO_RELOAD']}")
        print("=" * 60)
