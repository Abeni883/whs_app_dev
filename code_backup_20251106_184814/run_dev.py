"""
Development Server für WHS Testprotokoll-Anwendung

Startet die Flask-Anwendung im Development-Modus mit:
- DEBUG = True (automatisches Reload bei Code-Änderungen)
- Host = 127.0.0.1 (localhost only)
- Port = 5000

VERWENDUNG:
    venv\Scripts\python.exe run_dev.py

ODER (wenn venv aktiviert):
    python run_dev.py
"""

import os
import sys

# Stelle sicher, dass wir im richtigen Verzeichnis sind
basedir = os.path.abspath(os.path.dirname(__file__))
os.chdir(basedir)

# Importiere die Flask-App
from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("WHS TESTPROTOKOLL - DEVELOPMENT SERVER")
    print("=" * 60)
    print(f"Projekt-Verzeichnis: {basedir}")
    print(f"Datenbank: {app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')}")
    print(f"Debug-Modus: {app.config.get('DEBUG', False)}")
    print()
    print("Server läuft auf: http://127.0.0.1:5000")
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
        host='127.0.0.1',
        port=5000,
        use_reloader=True  # Auto-Reload bei Code-Änderungen
    )
