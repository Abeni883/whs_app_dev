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
from models import db, enable_sqlite_foreign_keys


def make_temp_app(register_blueprints=False):
    """Erzeugt (app, db_path) mit leerer, frisch erstellter Schema-DB.

    register_blueprints=True registriert den stuecknachweis-Blueprint und
    deaktiviert Login (LOGIN_DISABLED) fuer Route-Tests via Test-Client.
    """
    fd, path = tempfile.mkstemp(suffix='.db', prefix='whs_test_')
    os.close(fd)
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + path.replace('\\', '/')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.config['LOGIN_DISABLED'] = True
    app.secret_key = 'test'
    db.init_app(app)
    with app.app_context():
        enable_sqlite_foreign_keys(db.engine)
    if register_blueprints:
        from blueprints.stuecknachweis import stuecknachweis_bp
        app.register_blueprint(stuecknachweis_bp)
    return app, path
