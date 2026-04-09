"""
Hauptanwendung für das WHS Testprotokoll (SBB AG).

Flask-Webanwendung zur Verwaltung und Durchführung von Abnahmetests für
Weichenheizungsprojekte (EWH und GWH). Bietet vollständige CRUD-Operationen
für Projekte, WHK-Konfigurationen, Testfragen und Abnahmetest-Ergebnisse.

Hauptfunktionen:
    - Projektverwaltung (EWH/GWH)
    - WHK-Konfiguration (Abgänge, Temperatursonden, Antriebsheizungen)
    - Abnahmetest-Durchführung (LSS-CH und WH-LTS parallel)
    - Testfragen-Verwaltung
    - PDF/Excel-Export von Testprotokollen

Routes:
    - /projekte: Projektübersicht mit Suche
    - /projekt/neu: Neues Projekt anlegen
    - /projekt/bearbeiten/<id>: Projekt bearbeiten
    - /projekt/konfiguration/<id>: WHK-Konfiguration (EWH)
    - /projekt/<id>/gwh-konfiguration: GWH-Konfiguration (ZSK, HGLS, Meteostationen)
    - /projekt/abnahmetest/<id>: Abnahmetest durchführen
    - /testfragen: Testfragen-Verwaltung
    - /projekt/<id>/export/pdf: PDF-Export
    - /projekt/<id>/export/excel: Excel-Export
"""

# ==================== STANDARD-BIBLIOTHEKEN ====================
import json
from datetime import datetime, timedelta
from io import BytesIO
import os
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

# ==================== FLASK & EXTENSIONS ====================
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    send_file,
    send_from_directory,
    session,
    make_response
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

# ==================== EIGENE MODULE ====================
from config import Config
from models import (
    db,
    User,
    Project,
    WHKConfig,
    TestQuestion,
    AbnahmeTestResult,
    TestResult,  # Legacy
    ProjectTimeLog,
    AppSettings,
    TestabschlussItem,
    # GWH-Modelle
    ZSKConfig,
    HGLSConfig,
    GWHMeteostation
)

# ==================== BLUEPRINTS ====================
from blueprints.auth import auth_bp, init_app as auth_init
from blueprints.api import api_bp, cleanup_stale_sessions
from blueprints.zeiterfassung import zeiterfassung_bp
from blueprints.testfragen import testfragen_bp
from blueprints.projekte import projekte_bp
from blueprints.konfiguration import konfiguration_bp
from blueprints.export import export_bp
from blueprints.ewh import ewh_bp
from blueprints.gwh import gwh_bp
from blueprints.stuecknachweis import stuecknachweis_bp

# ==================== FLASK-APP INITIALISIERUNG ====================

app = Flask(__name__)
app.config.from_object(Config)

# Session-Konfiguration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Upload-Konfiguration für Screenshots
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads', 'screenshots')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db.init_app(app)

# Flask-Login initialisieren
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bitte melden Sie sich an, um diese Seite zu sehen.'
login_manager.login_message_category = 'info'

# Bcrypt initialisieren
bcrypt = Bcrypt(app)

# Blueprints registrieren
app.register_blueprint(auth_bp)
auth_init(app)
app.register_blueprint(api_bp)
app.register_blueprint(zeiterfassung_bp)
app.register_blueprint(testfragen_bp)
app.register_blueprint(projekte_bp)
app.register_blueprint(konfiguration_bp)
app.register_blueprint(export_bp)
app.register_blueprint(ewh_bp)
app.register_blueprint(gwh_bp)
app.register_blueprint(stuecknachweis_bp)


def allowed_file(filename):
    """Prüft ob die Dateiendung erlaubt ist."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def is_gwh_komponente(komponente_typ):
    """Prüft ob der Komponententyp zu GWH gehört."""
    gwh_komponenten = ['GWH_Anlage', 'HGLS', 'ZSK', 'GWH_Teile', 'GWH_Temperatursonde', 'GWH_Meteostation']
    return komponente_typ in gwh_komponenten


@login_manager.user_loader
def load_user(user_id):
    """Lädt einen Benutzer anhand der ID für Flask-Login."""
    return User.query.get(int(user_id))


def admin_required(f):
    """Decorator für Admin-only Routen."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Sie haben keine Berechtigung für diese Seite.', 'error')
            return redirect(url_for('projekte.projekte'))
        return f(*args, **kwargs)
    return decorated_function


def check_first_user():
    """Prüft ob es bereits Benutzer gibt - wenn nicht, Registrierung ohne Login erlauben."""
    return User.query.count() == 0


# Datenbank-Tabellen erstellen (falls nicht vorhanden)
with app.app_context():
    db.create_all()

    # Migration: user_id Spalte zu project_time_logs hinzufügen (falls nicht vorhanden)
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    if 'project_time_logs' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('project_time_logs')]
        if 'user_id' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE project_time_logs ADD COLUMN user_id INTEGER REFERENCES users(id)'))
                conn.commit()
            print("Migration: user_id Spalte zu project_time_logs hinzugefügt")

    # AppSettings initialisieren (falls nicht vorhanden)
    if not AppSettings.query.first():
        default_settings = AppSettings(zeiterfassung_timeout_minuten=60)
        db.session.add(default_settings)
        db.session.commit()
        print("AppSettings: Standardeinstellungen erstellt")

    # TestabschlussItem initialisieren (falls nicht vorhanden)
    TestabschlussItem.init_default_items()


# ==================== HELPER-FUNKTIONEN ====================

def parse_date_from_form(date_string, date_format='%d.%m.%Y'):
    """
    Konvertiert Datumsstring aus Formular in date-Objekt.

    Args:
        date_string: Datumsstring aus Formular (kann None oder leer sein)
        date_format: Erwartetes Datumsformat (Standard: '%d.%m.%Y')

    Returns:
        date-Objekt oder None bei leerem/ungültigem Input

    Example:
        >>> parse_date_from_form('31.12.2024')
        datetime.date(2024, 12, 31)
    """
    if not date_string or not date_string.strip():
        return None
    try:
        return datetime.strptime(date_string, date_format).date()
    except ValueError:
        return None


def calculate_all_projects_test_progress():
    """
    Berechnet den Testfortschritt für alle Projekte effizient.

    Verwendet Bulk-Queries um N+1 Query-Probleme zu vermeiden.
    Der Fortschritt wird basierend auf der Anzahl vollständig beantworteter
    Tests (beide Systeme: LSS-CH und WH-LTS) berechnet.

    Returns:
        dict: {projekt_id: progress_percent (0-100)}
    """
    progress_dict = {}

    # 1. Alle Projekte laden
    projekte = Project.query.all()
    if not projekte:
        return progress_dict

    projekt_ids = [p.id for p in projekte]

    # 2. Alle WHKConfigs für alle Projekte in einem Query laden
    all_whk_configs = WHKConfig.query.filter(WHKConfig.projekt_id.in_(projekt_ids)).all()

    # Gruppiere WHKConfigs nach projekt_id
    whk_configs_by_projekt = {}
    for whk in all_whk_configs:
        if whk.projekt_id not in whk_configs_by_projekt:
            whk_configs_by_projekt[whk.projekt_id] = []
        whk_configs_by_projekt[whk.projekt_id].append(whk)

    # 3. Alle TestQuestions laden
    all_test_questions = TestQuestion.query.all()

    # 4. Alle AbnahmeTestResults für alle Projekte in einem Query laden
    all_results = AbnahmeTestResult.query.filter(
        AbnahmeTestResult.projekt_id.in_(projekt_ids)
    ).all()

    # Gruppiere Results nach projekt_id
    results_by_projekt = {}
    for result in all_results:
        if result.projekt_id not in results_by_projekt:
            results_by_projekt[result.projekt_id] = []
        results_by_projekt[result.projekt_id].append(result)

    # 5. Berechne Fortschritt für jedes Projekt
    for projekt in projekte:
        whk_configs = whk_configs_by_projekt.get(projekt.id, [])
        results = results_by_projekt.get(projekt.id, [])

        # Keine WHK-Konfiguration = 0%
        if not whk_configs:
            progress_dict[projekt.id] = 0
            continue

        # Berechne erwartete Anzahl Tests (Spalten pro Frage)
        expected_tests = 0

        for frage in all_test_questions:
            if frage.komponente_typ == "Anlage":
                # 1 Test für die Anlage
                expected_tests += 1

            elif frage.komponente_typ == "WHK":
                # 1 Test pro WHK
                expected_tests += len(whk_configs)

            elif frage.komponente_typ == "Abgang":
                # 1 Test pro Abgang pro WHK
                for whk in whk_configs:
                    expected_tests += whk.anzahl_abgaenge

            elif frage.komponente_typ == "Temperatursonde":
                # 1 Test pro Temperatursonde pro WHK
                for whk in whk_configs:
                    expected_tests += whk.anzahl_temperatursonden

            elif frage.komponente_typ == "Antriebsheizung":
                # 1 Test pro WHK mit Antriebsheizung
                for whk in whk_configs:
                    if whk.hat_antriebsheizung:
                        expected_tests += 1

            elif frage.komponente_typ == "Meteostation":
                # 1 Test pro eindeutiger Meteostation
                meteostationen = set()
                for whk in whk_configs:
                    if whk.meteostation:
                        meteostationen.add(whk.meteostation)
                expected_tests += len(meteostationen)

        # Keine erwarteten Tests = 0%
        if expected_tests == 0:
            progress_dict[projekt.id] = 0
            continue

        # Zähle vollständig beantwortete Tests
        # Ein Test ist komplett wenn BEIDE Systeme (lss_ch UND wh_lts) ausgefüllt sind
        completed_tests = 0
        for result in results:
            if result.lss_ch_result and result.wh_lts_result:
                completed_tests += 1

        # Berechne Prozentsatz
        progress = round((completed_tests / expected_tests) * 100)
        # Begrenze auf 0-100
        progress_dict[projekt.id] = min(100, max(0, progress))

    return progress_dict


def create_test_results_for_new_question(test_question):
    """
    Erstellt Abnahmetest-Ergebnisse für eine neue Testfrage in allen bestehenden Projekten.

    Setzt alle Ergebnisse auf "nicht_testbar" mit einer entsprechenden Bemerkung,
    damit die Fortschritts-Anzeige weiterhin 100% erreichen kann.

    Args:
        test_question: Die neu erstellte TestQuestion-Instanz

    Returns:
        int: Anzahl der erstellten Einträge
    """
    created_count = 0
    bemerkung = "Neue Abnahmetestfrage, wurde damals nicht getestet"

    # Hole alle Projekte mit ihren WHK-Konfigurationen
    projekte = Project.query.all()

    for projekt in projekte:
        whk_configs = WHKConfig.query.filter_by(projekt_id=projekt.id).all()

        if test_question.komponente_typ == "Anlage":
            # Anlage: Ein Eintrag pro Projekt
            result = AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=test_question.id,
                komponente_index="Anlage",
                spalte=None,
                lss_ch_result="nicht_testbar",
                wh_lts_result="nicht_testbar",
                lss_ch_bemerkung=bemerkung,
                wh_lts_bemerkung=bemerkung,
                getestet_am=datetime.utcnow()
            )
            db.session.add(result)
            created_count += 1

        elif test_question.komponente_typ == "WHK":
            # WHK: Ein Eintrag pro WHK im Projekt
            for whk in whk_configs:
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=test_question.id,
                    komponente_index=whk.whk_nummer,
                    spalte=None,
                    lss_ch_result="nicht_testbar",
                    wh_lts_result="nicht_testbar",
                    lss_ch_bemerkung=bemerkung,
                    wh_lts_bemerkung=bemerkung,
                    getestet_am=datetime.utcnow()
                )
                db.session.add(result)
                created_count += 1

        elif test_question.komponente_typ == "Abgang":
            # Abgang: Ein Eintrag pro Abgang pro WHK
            for whk in whk_configs:
                for i in range(1, whk.anzahl_abgaenge + 1):
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=test_question.id,
                        komponente_index=whk.whk_nummer,
                        spalte=f"Abgang {i:02d}",
                        lss_ch_result="nicht_testbar",
                        wh_lts_result="nicht_testbar",
                        lss_ch_bemerkung=bemerkung,
                        wh_lts_bemerkung=bemerkung,
                        getestet_am=datetime.utcnow()
                    )
                    db.session.add(result)
                    created_count += 1

        elif test_question.komponente_typ == "Temperatursonde":
            # Temperatursonde: Ein Eintrag pro TS pro WHK
            for whk in whk_configs:
                for i in range(1, whk.anzahl_temperatursonden + 1):
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=test_question.id,
                        komponente_index=whk.whk_nummer,
                        spalte=f"TS {i:02d}",
                        lss_ch_result="nicht_testbar",
                        wh_lts_result="nicht_testbar",
                        lss_ch_bemerkung=bemerkung,
                        wh_lts_bemerkung=bemerkung,
                        getestet_am=datetime.utcnow()
                    )
                    db.session.add(result)
                    created_count += 1

        elif test_question.komponente_typ == "Antriebsheizung":
            # Antriebsheizung: Ein Eintrag pro WHK mit Antriebsheizung
            for whk in whk_configs:
                if whk.hat_antriebsheizung:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=test_question.id,
                        komponente_index=whk.whk_nummer,
                        spalte="Antriebsheizung",
                        lss_ch_result="nicht_testbar",
                        wh_lts_result="nicht_testbar",
                        lss_ch_bemerkung=bemerkung,
                        wh_lts_bemerkung=bemerkung,
                        getestet_am=datetime.utcnow()
                    )
                    db.session.add(result)
                    created_count += 1

        elif test_question.komponente_typ == "Meteostation":
            # Meteostation: Ein Eintrag pro einzigartiger Meteostation
            meteostationen = set()
            for whk in whk_configs:
                if whk.meteostation:
                    meteostationen.add(whk.meteostation)

            for ms_name in meteostationen:
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=test_question.id,
                    komponente_index=ms_name,
                    spalte=None,
                    lss_ch_result="nicht_testbar",
                    wh_lts_result="nicht_testbar",
                    lss_ch_bemerkung=bemerkung,
                    wh_lts_bemerkung=bemerkung,
                    getestet_am=datetime.utcnow()
                )
                db.session.add(result)
                created_count += 1

    return created_count


@app.route('/testabschluss')
@login_required
def testabschluss():
    """Testabschluss-Seite mit Post-Test-Einstellungen."""
    # Lade Einträge aus der Datenbank
    ewh_items = TestabschlussItem.get_items_by_energie('EWH')
    gwh_items = TestabschlussItem.get_items_by_energie('GWH')
    return render_template('testabschluss.html', ewh_items=ewh_items, gwh_items=gwh_items)


# ==================== TESTABSCHLUSS-TEXTE VERWALTUNG ====================

@app.route('/einstellungen/testabschluss')
@login_required
def testabschluss_settings():
    """Verwaltungsseite für Testabschluss-Texte."""
    ewh_items = TestabschlussItem.query.filter_by(energie_typ='EWH').order_by(TestabschlussItem.reihenfolge).all()
    gwh_items = TestabschlussItem.query.filter_by(energie_typ='GWH').order_by(TestabschlussItem.reihenfolge).all()
    return render_template('testabschluss_settings.html', ewh_items=ewh_items, gwh_items=gwh_items)


@app.route('/einstellungen/testabschluss/neu', methods=['POST'])
@login_required
def testabschluss_item_neu():
    """Neuen Testabschluss-Eintrag erstellen."""
    energie_typ = request.form.get('energie_typ', 'EWH')
    titel = request.form.get('titel', '').strip()
    beschreibung = request.form.get('beschreibung', '').strip()
    highlight_text = request.form.get('highlight_text', '').strip() or None
    reihenfolge = request.form.get('reihenfolge', 0, type=int)

    if not titel or not beschreibung:
        flash('Titel und Beschreibung sind Pflichtfelder.', 'error')
        return redirect(url_for('testabschluss_settings'))

    # Nächste Reihenfolge ermitteln falls 0
    if reihenfolge == 0:
        max_order = db.session.query(db.func.max(TestabschlussItem.reihenfolge)).filter_by(energie_typ=energie_typ).scalar()
        reihenfolge = (max_order or 0) + 1

    item = TestabschlussItem(
        energie_typ=energie_typ,
        titel=titel,
        beschreibung=beschreibung,
        highlight_text=highlight_text,
        reihenfolge=reihenfolge
    )
    db.session.add(item)
    db.session.commit()

    flash(f'Eintrag "{titel}" wurde erstellt.', 'success')
    return redirect(url_for('testabschluss_settings'))


@app.route('/einstellungen/testabschluss/<int:item_id>/bearbeiten', methods=['POST'])
@login_required
def testabschluss_item_bearbeiten(item_id):
    """Testabschluss-Eintrag bearbeiten."""
    item = TestabschlussItem.query.get_or_404(item_id)

    item.titel = request.form.get('titel', '').strip()
    item.beschreibung = request.form.get('beschreibung', '').strip()
    item.highlight_text = request.form.get('highlight_text', '').strip() or None
    item.reihenfolge = request.form.get('reihenfolge', item.reihenfolge, type=int)
    item.aktiv = request.form.get('aktiv') == 'on'

    if not item.titel or not item.beschreibung:
        flash('Titel und Beschreibung sind Pflichtfelder.', 'error')
        return redirect(url_for('testabschluss_settings'))

    db.session.commit()
    flash(f'Eintrag "{item.titel}" wurde aktualisiert.', 'success')
    return redirect(url_for('testabschluss_settings'))


@app.route('/einstellungen/testabschluss/<int:item_id>/loeschen', methods=['POST'])
@login_required
def testabschluss_item_loeschen(item_id):
    """Testabschluss-Eintrag löschen."""
    item = TestabschlussItem.query.get_or_404(item_id)
    titel = item.titel
    db.session.delete(item)
    db.session.commit()
    flash(f'Eintrag "{titel}" wurde gelöscht.', 'success')
    return redirect(url_for('testabschluss_settings'))



@app.route('/tests')
@login_required
def tests():
    """
    Übersicht aller Legacy-Tests.

    Returns:
        HTML-Seite mit Test-Liste (tests.html)
    """
    tests = TestResult.query.order_by(TestResult.test_date.desc()).all()
    return render_template('tests.html', tests=tests)


@app.route('/new_test', methods=['GET', 'POST'])
@login_required
def new_test():
    """
    Neuen Legacy-Test erstellen.

    GET: Zeigt Test-Formular
    POST: Speichert neuen Test

    Returns:
        GET: HTML-Formular (test_form.html)
        POST: Redirect zur Startseite mit Flash-Message
    """
    if request.method == 'POST':
        # Projekt-ID holen (optional)
        project_id = request.form.get('project_id')
        if project_id == '':
            project_id = None

        test = TestResult(
            test_name=request.form['test_name'],
            hardware_id=request.form['hardware_id'],
            software_version=request.form['software_version'],
            result=request.form['result'],
            tester_name=request.form['tester_name'],
            notes=request.form.get('notes', ''),
            project_id=project_id
        )
        db.session.add(test)
        db.session.commit()
        flash('Test erfolgreich gespeichert!', 'success')
        return redirect(url_for('index'))

    # Alle Projekte für Dropdown laden
    projekte = Project.query.order_by(Project.projektname).all()
    return render_template('test_form.html', projekte=projekte)
# ==================== PDF-EXPORT ====================
@app.route('/einstellungen/allgemein', methods=['GET', 'POST'])
@login_required
def einstellungen_allgemein():
    """
    Allgemeine Einstellungen der Anwendung.
    Nur für Administratoren zugänglich.
    """
    if not current_user.is_admin:
        flash('Nur Administratoren können die Einstellungen ändern.', 'error')
        return redirect(url_for('projekte.projekte'))

    settings = AppSettings.get_settings()

    if request.method == 'POST':
        try:
            timeout = request.form.get('zeiterfassung_timeout', type=int)
            if timeout and 1 <= timeout <= 480:
                settings.zeiterfassung_timeout_minuten = timeout
                db.session.commit()
                flash('Einstellungen wurden gespeichert.', 'success')
            else:
                flash('Timeout muss zwischen 1 und 480 Minuten liegen.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Speichern: {str(e)}', 'error')

        return redirect(url_for('einstellungen_allgemein'))

    return render_template('einstellungen_allgemein.html', settings=settings)


if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
