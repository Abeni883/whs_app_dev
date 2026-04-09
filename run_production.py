"""
Production Server für WHS Testprotokoll-Anwendung.

Startet die Flask-Anwendung im Production-Modus mit Waitress WSGI-Server:
- DEBUG = False (kein automatisches Reload)
- Host = 0.0.0.0 (auf allen Netzwerk-Interfaces)
- Port = 5000
- Threads = 4 (für gleichzeitige Requests)

Waitress ist ein production-ready WSGI-Server der:
- Unter Windows und Linux läuft
- Multi-Threading unterstützt
- Stabil und sicher ist

VERWENDUNG:
    python run_production.py

HINWEIS:
    Für optimale Performance und Sicherheit sollte Waitress hinter
    einem Reverse Proxy (IIS, Nginx, Apache) betrieben werden.
"""

import sys
import os

# ==================== KONFIGURATION ====================
# Diese Werte können angepasst werden

HOST = '0.0.0.0'      # Alle Netzwerk-Interfaces (oder '127.0.0.1' für localhost only)
PORT = 5000           # HTTP-Port
THREADS = 4           # Anzahl Worker-Threads

# ==================== SETUP ====================

# Working Directory DYNAMISCH ermitteln (funktioniert überall!)
BASEDIR = os.path.abspath(os.path.dirname(__file__))
os.chdir(BASEDIR)
sys.path.insert(0, BASEDIR)

# Waitress WSGI-Server importieren
try:
    from waitress import serve
except ImportError:
    print("FEHLER: Waitress ist nicht installiert!")
    print("Installiere mit: pip install waitress")
    sys.exit(1)

# Flask-App importieren
from app import app

if __name__ == '__main__':
    # Banner ausgeben
    print('=' * 70)
    print('WHS TESTPROTOKOLL - PRODUCTION SERVER (Waitress)')
    print('=' * 70)
    print(f'Projekt-Verzeichnis: {BASEDIR}')
    print(f'Datenbank: {app.config.get("SQLALCHEMY_DATABASE_URI", "N/A")}')
    print(f'Debug-Modus: {app.config.get("DEBUG", False)}')
    print()
    print(f'Server läuft auf: http://{HOST}:{PORT}')
    print(f'Lokaler Zugriff: http://127.0.0.1:{PORT}')
    print(f'Worker-Threads: {THREADS}')
    print()
    print('Drücke CTRL+C zum Beenden')
    print('=' * 70)
    print()

    # Starte Waitress Production-Server
    try:
        serve(
            app,
            host=HOST,
            port=PORT,
            threads=THREADS,
            url_scheme='http',
            ident='WHS-Waitress'
        )
    except KeyboardInterrupt:
        print('\n\nServer wird beendet...')
        sys.exit(0)
    except Exception as e:
        print(f'\n\nFEHLER beim Starten des Servers: {e}')
        sys.exit(1)
