"""
Development Server für WHS Testprotokoll-Anwendung
Alternative Version auf Port 8080

VERWENDUNG:
    venv\Scripts\python.exe run_dev_alt.py
"""

import os
from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("WHS TESTPROTOKOLL - DEVELOPMENT SERVER (PORT 8080)")
    print("=" * 60)
    print("Server läuft auf: http://127.0.0.1:8080")
    print("Drücke CTRL+C zum Beenden")
    print("=" * 60)

    app.config['DEBUG'] = True
    app.config['ENV'] = 'development'

    app.run(
        debug=True,
        host='127.0.0.1',
        port=8080,
        use_reloader=True
    )
