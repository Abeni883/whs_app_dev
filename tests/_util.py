"""Gemeinsame Test-Utilities: hermetische App mit temporaerer SQLite-DB.

Beruehrt NIE die echten DBs (whs_dev.db / whs.db) — jeder Test bekommt eine
frische Temp-Datei, die im tearDown geloescht wird.
"""
import os
import sys
import tempfile

# DEV-Repo-Wurzel auf den Pfad (tests/ liegt darunter)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from flask import Flask
from models import db


def make_temp_app():
    """Erzeugt (app, db_path) mit leerer, frisch erstellter Schema-DB."""
    fd, path = tempfile.mkstemp(suffix='.db', prefix='whs_test_')
    os.close(fd)
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + path.replace('\\', '/')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.secret_key = 'test'
    db.init_app(app)
    return app, path
