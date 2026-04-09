"""
Development Server für WHS Testprotokoll-Anwendung.

Startet die Flask-Anwendung im Development-Modus mit:
- DEBUG = True (automatisches Reload bei Code-Änderungen)
- Host = 127.0.0.1 (localhost only)
- Port = 5000 (gleicher Port wie Production für Konsistenz)

VERWENDUNG:
    python run_dev.py

Server erreichbar unter: http://127.0.0.1:5000
"""

import os
import sys

# Stelle sicher, dass wir im richtigen Verzeichnis sind
basedir = os.path.abspath(os.path.dirname(__file__))
os.chdir(basedir)

# Importiere die Flask-App
from app import app

if __name__ == '__main__':
    # ==================== KONFIGURATION ====================
    HOST = '127.0.0.1'    # Localhost only (sicher für Development)
    PORT = 5000           # Gleicher Port wie Production!
    
    print("=" * 60)
    print("WHS TESTPROTOKOLL - DEVELOPMENT SERVER")
    print("=" * 60)
    print(f"Projekt-Verzeichnis: {basedir}")
    print(f"Datenbank: {app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')}")
    print(f"Debug-Modus: {app.config.get('DEBUG', False)}")
    print()
    print(f"Server läuft auf: http://{HOST}:{PORT}")
    print("Drücke CTRL+C zum Beenden")
    print("=" * 60)
    print()

    # Setze Development-Config (falls nicht bereits gesetzt)
    if not app.config.get('DEBUG'):
        app.config['DEBUG'] = True
        app.config['ENV'] = 'development'

    # Starte Development-Server
    app.run(
        debug=True,
        host=HOST,
        port=PORT,
        use_reloader=True  # Auto-Reload bei Code-Änderungen
    )
