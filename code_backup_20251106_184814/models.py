from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    energie = db.Column(db.String(10), nullable=False)  # EWH oder GWH
    projektname = db.Column(db.String(200), nullable=False)
    didok_betriebspunkt = db.Column(db.String(100))
    baumappenversion = db.Column(db.Date)  # Nur Datum
    projektleiter_sbb = db.Column(db.String(150))
    pruefer_achermann = db.Column(db.String(150))
    pruefdatum = db.Column(db.Date)  # Nur Datum
    bemerkung = db.Column(db.Text)
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    geaendert_am = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Beziehung zu TestResults (One-to-Many)
    tests = db.relationship('TestResult', backref='projekt', lazy=True)

    # Beziehung zu WHK-Konfigurationen (One-to-Many)
    whk_configs = db.relationship('WHKConfig', backref='projekt', lazy=True, cascade='all, delete-orphan')

    # Beziehung zu Abnahmetest-Ergebnissen (One-to-Many)
    abnahme_results = db.relationship('AbnahmeTestResult', backref='projekt', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.projektname} - {self.energie}>'


class TestResult(db.Model):
    __tablename__ = 'test_results'

    id = db.Column(db.Integer, primary_key=True)
    test_name = db.Column(db.String(100), nullable=False)
    hardware_id = db.Column(db.String(50))
    software_version = db.Column(db.String(50))
    result = db.Column(db.String(20))
    tester_name = db.Column(db.String(100))
    test_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    # Fremdschlüssel zu Project (optional)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)

    def __repr__(self):
        return f'<TestResult {self.test_name} - {self.result}>'


class WHKConfig(db.Model):
    """WHK-Konfiguration für ein Projekt"""
    __tablename__ = 'whk_configs'

    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    whk_nummer = db.Column(db.String(20), nullable=False)  # z.B. "WHK 01"
    anzahl_abgaenge = db.Column(db.Integer, nullable=False)  # 1-12
    anzahl_temperatursonden = db.Column(db.Integer, nullable=False)  # 1-12
    hat_antriebsheizung = db.Column(db.Boolean, default=False)
    meteostation = db.Column(db.String(50))  # Optional
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WHKConfig {self.whk_nummer} - Projekt {self.projekt_id}>'


class TestQuestion(db.Model):
    """Testfragen-Vorlagen für Abnahmetests"""
    __tablename__ = 'test_questions'

    id = db.Column(db.Integer, primary_key=True)
    komponente_typ = db.Column(db.String(50), nullable=False)  # Anlage, WHK, Abgang, Temperatursonde, Antriebsheizung, Meteostation
    testszenario = db.Column(db.String(200), nullable=False)  # z.B. "Kommunikation zum LSS-CH"
    frage_nummer = db.Column(db.Integer, nullable=False)  # Laufende Nummer
    frage_text = db.Column(db.Text, nullable=False)
    test_information = db.Column(db.Text)  # Zusätzliche Informationen
    reihenfolge = db.Column(db.Integer, nullable=False)  # Für Sortierung
    preset_antworten = db.Column(db.JSON, nullable=True)  # Preset für Checkboxen
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)

    # Beziehung zu Abnahmetest-Ergebnissen (One-to-Many)
    abnahme_results = db.relationship('AbnahmeTestResult', backref='test_question', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TestQuestion {self.komponente_typ} - {self.testszenario}>'


class AbnahmeTestResult(db.Model):
    """Test-Ergebnisse für Abnahmetests"""
    __tablename__ = 'abnahme_test_results'

    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    test_question_id = db.Column(db.Integer, db.ForeignKey('test_questions.id'), nullable=False)
    komponente_index = db.Column(db.String(50), nullable=False)  # z.B. "WHK 01", "MS 01A"
    spalte = db.Column(db.String(100))  # z.B. "Abgang 01", "TS 02", "Antriebsheizung"
    lss_ch_result = db.Column(db.String(20))  # richtig, falsch, nicht_testbar, null
    wh_lts_result = db.Column(db.String(20))  # richtig, falsch, nicht_testbar, null
    bemerkung = db.Column(db.Text)  # Legacy-Feld
    lss_ch_bemerkung = db.Column(db.Text)  # Bemerkung für LSS-CH System
    wh_lts_bemerkung = db.Column(db.Text)  # Bemerkung für WH-LTS System
    getestet_am = db.Column(db.DateTime, default=datetime.utcnow)
    tester = db.Column(db.String(100))  # Name des Testers

    def __repr__(self):
        return f'<AbnahmeTestResult Projekt {self.projekt_id} - {self.komponente_index}>'
