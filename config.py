"""
Produktions-Konfiguration für die WHS Testprotokoll-Anwendung.

Diese Konfiguration ist für den Produktivbetrieb optimiert mit:
- SQLite-Datenbank (Production-ready)
- Sicherheits-Features (Secret Key, Session-Schutz)
- Upload-Limits
- Deaktiviertem Debug-Modus
"""

import os
import sys
from datetime import timedelta

# Basis-Verzeichnis der Anwendung
basedir = os.path.abspath(os.path.dirname(__file__))

# Standard-Fallback-DB (DEV). PROD setzt DATABASE_URL explizit in der .env.
_DEFAULT_DB_URI = 'sqlite:///' + os.path.join(basedir, 'database', 'whs_dev.db')

# Test-Isolations-Guard: Wird die App/Config ohne explizite DATABASE_URL
# importiert, laeuft alles auf der Fallback-DEV-DB. Fuer den regulaeren
# DEV-Start ist das gewollt; in Tests/Skripten kann es aber unbeabsichtigt die
# echte DB treffen. Darum EINMALIG eine stderr-Warnung ausgeben — kein Abbruch,
# damit weder DEV-Start noch der PROD-Dienst gestoert werden (PROD liefert die
# URI ohnehin via .env, also feuert die Warnung dort nicht).
_db_guard_warned = False


def _warn_default_db_once():
    global _db_guard_warned
    if _db_guard_warned or os.environ.get('DATABASE_URL'):
        return
    _db_guard_warned = True
    print(
        '[config] WARNUNG: DATABASE_URL nicht gesetzt -> Fallback auf DEV-DB '
        f'{_DEFAULT_DB_URI}. In Tests/Skripten DATABASE_URL explizit setzen, '
        'um die echte DB nicht zu beruehren.',
        file=sys.stderr,
    )


_warn_default_db_once()


class Config:
    """
    Haupt-Konfigurationsklasse für Production-Umgebung.

    Umgebungsvariablen (optional):
        SECRET_KEY: Geheimer Schlüssel für Session-Verschlüsselung
        DATABASE_PATH: Alternativer Pfad zur SQLite-Datenbank
        MAX_CONTENT_LENGTH: Maximale Upload-Größe in MB

    Verwendung:
        app.config.from_object(Config)
    """

    # ==================== DATENBANK-KONFIGURATION ====================

    # SQLite Datenbank (PRODUCTION)
    # Pfad: C:\inetpub\whs_app\database\whs.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or _DEFAULT_DB_URI

    # Deaktiviert Tracking von Objektänderungen (Performance-Optimierung)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Verbindungspool-Konfiguration (SQLite)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Prüft Verbindung vor Nutzung
        'pool_recycle': 3600,   # Recycelt Verbindungen nach 1 Stunde
    }


    # ==================== SICHERHEITS-KONFIGURATION ====================

    # Geheimer Schlüssel für Session-Verschlüsselung
    # WICHTIG: In Production über Umgebungsvariable setzen!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Session-Konfiguration
    SESSION_COOKIE_SECURE = False  # Auf True setzen bei HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Verhindert JavaScript-Zugriff
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF-Schutz
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # Session-Timeout: 2 Stunden

    # CSRF-Schutz (falls Flask-WTF verwendet wird)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Kein Timeout für CSRF-Token


    # ==================== UPLOAD-KONFIGURATION ====================

    # Upload-Verzeichnis (relativ zum basedir)
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')

    # Maximale Upload-Größe (16 MB)
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH_MB', 16)) * 1024 * 1024

    # Erlaubte Datei-Endungen für Uploads
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'csv'}


    # ==================== APP-KONFIGURATION ====================

    # Debug-Modus (IMMER False in Production!)
    DEBUG = False

    # Testing-Modus
    TESTING = False

    # JSON-Konfiguration
    JSON_AS_ASCII = False  # Erlaubt Unicode-Zeichen in JSON-Responses
    JSON_SORT_KEYS = False  # Behält Reihenfolge der Keys
    JSONIFY_PRETTYPRINT_REGULAR = False  # Kompakte JSON-Ausgabe

    # Timezone (für Datums-Formatierung)
    TIMEZONE = 'Europe/Zurich'  # SBB-Zeitzone


    # ==================== LOGGING-KONFIGURATION ====================

    # Log-Verzeichnis
    LOG_FOLDER = os.path.join(basedir, 'logs')

    # Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Log-Datei
    LOG_FILE = os.path.join(LOG_FOLDER, 'production.log')

    # Maximale Log-Größe (10 MB)
    LOG_MAX_BYTES = 10 * 1024 * 1024

    # Anzahl Backup-Logs
    LOG_BACKUP_COUNT = 5


    # ==================== PERFORMANCE-KONFIGURATION ====================

    # Template-Auto-Reload (False für bessere Performance)
    TEMPLATES_AUTO_RELOAD = False

    # Send-File-Max-Age (Cache-Dauer für statische Dateien: 1 Jahr)
    SEND_FILE_MAX_AGE_DEFAULT = 31536000


    @staticmethod
    def init_app(app):
        """
        Initialisiert anwendungsspezifische Konfigurationen.

        Args:
            app: Flask-Applikationsinstanz
        """
        # Stelle sicher, dass wichtige Verzeichnisse existieren
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)

        # Datenbank-Verzeichnis erstellen
        db_dir = os.path.join(basedir, 'database')
        os.makedirs(db_dir, exist_ok=True)
