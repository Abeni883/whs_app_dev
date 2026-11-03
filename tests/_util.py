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


def make_render_app():
    """Wie make_temp_app, aber mit ECHTEM Template-Rendering (base.html inkl.).

    Registriert alle Blueprints, deren Endpunkte base.html/projekte.html per
    url_for referenzieren, stubbt die app-level Routen aus app.py (Testabschluss,
    Einstellungen) und initialisiert Flask-Login mit anonymem User. app.py selbst
    wird NICHT importiert (das wuerde .env laden und gegen die DEV-DB create_all
    fahren).
    """
    from flask_login import LoginManager
    from blueprints.auth import auth_bp
    from blueprints.projekte import projekte_bp
    from blueprints.konfiguration import konfiguration_bp
    from blueprints.export import export_bp
    from blueprints.testfragen import testfragen_bp
    from blueprints.zeiterfassung import zeiterfassung_bp
    from blueprints.ewh import ewh_bp
    from blueprints.gwh import gwh_bp
    from blueprints.stuecknachweis import stuecknachweis_bp
    from blueprints.sps_info import sps_info_bp

    app, path = make_temp_app()
    app.template_folder = os.path.join(_ROOT, 'templates')
    app.static_folder = os.path.join(_ROOT, 'static')
    for bp in (auth_bp, projekte_bp, konfiguration_bp, export_bp, testfragen_bp,
               zeiterfassung_bp, ewh_bp, gwh_bp, stuecknachweis_bp, sps_info_bp):
        app.register_blueprint(bp)
    # app-level Endpunkte aus app.py, die base.html verlinkt
    for endpoint, rule in (('testabschluss', '/testabschluss'),
                           ('testabschluss_settings', '/einstellungen/testabschluss'),
                           ('einstellungen_en61439', '/einstellungen/en61439'),
                           ('einstellungen_allgemein', '/einstellungen/allgemein')):
        app.add_url_rule(rule, endpoint, lambda: '')
    lm = LoginManager()
    lm.init_app(app)
    lm.user_loader(lambda uid: None)
    app.context_processor(lambda: dict(norm_name='EN 61439'))
    return app, path
