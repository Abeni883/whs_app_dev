"""
Datenbank-Modelle für die WHS Testprotokoll-Anwendung.

Definiert SQLAlchemy-Modelle für Weichenheizungsprojekte, WHK-Konfigurationen,
Testfragen und Abnahmetest-Ergebnisse der SBB AG.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import secrets

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    Benutzer-Modell für Authentifizierung.

    Unterstützt Login, Registrierung, Passwort-Reset und Admin-Funktionen.
    Der erste registrierte Benutzer wird automatisch zum Admin.
    """
    __tablename__ = 'users'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Login-Daten
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profil-Daten
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_admin = db.Column(db.Boolean, default=False, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_login = db.Column(db.DateTime, nullable=True)

    # Passwort-Reset
    password_reset_token = db.Column(db.String(100), nullable=True, unique=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)

    # Login-Versuche (Rate Limiting)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    def get_id(self):
        """Für Flask-Login: Gibt die User-ID als String zurück."""
        return str(self.id)

    @property
    def full_name(self):
        """Gibt den vollen Namen zurück oder den Benutzernamen."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username

    def generate_reset_token(self):
        """Generiert einen Passwort-Reset-Token (1 Stunde gültig)."""
        from datetime import timedelta
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token

    def clear_reset_token(self):
        """Löscht den Reset-Token nach Verwendung."""
        self.password_reset_token = None
        self.password_reset_expires = None

    def is_reset_token_valid(self):
        """Prüft ob der Reset-Token noch gültig ist."""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        return datetime.utcnow() < self.password_reset_expires

    def increment_failed_login(self):
        """Erhöht den Zähler für fehlgeschlagene Login-Versuche."""
        from datetime import timedelta
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)

    def reset_failed_login(self):
        """Setzt den Zähler für fehlgeschlagene Logins zurück."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def is_locked(self):
        """Prüft ob der Account temporär gesperrt ist."""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        if self.locked_until and datetime.utcnow() >= self.locked_until:
            self.reset_failed_login()
        return False

    def __repr__(self):
        return f'<User id={self.id} username="{self.username}" admin={self.is_admin}>'


class Project(db.Model):
    """
    Weichenheizungsprojekt (EWH oder GWH) der SBB AG.

    Zentrale Entität für die Verwaltung von Weichenheizungsprojekten mit
    Metadaten, Projektleiter-Informationen und Prüfdaten.

    Relationships:
        - tests: Legacy TestResults (One-to-Many)
        - whk_configs: WHK-Konfigurationen (One-to-Many, CASCADE)
        - abnahme_results: Abnahmetest-Ergebnisse (One-to-Many, CASCADE)
    """
    __tablename__ = 'projects'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Pflichtfelder
    energie = db.Column(db.String(10), nullable=False, index=True)  # EWH oder GWH
    projektname = db.Column(db.String(200), nullable=False, index=True)

    # Optionale Felder
    didok_betriebspunkt = db.Column(db.String(100), index=True)
    baumappenversion = db.Column(db.Date)
    projektleiter_sbb = db.Column(db.String(150))
    pruefer_achermann = db.Column(db.String(150))
    pruefdatum = db.Column(db.Date)
    ibn_inbetriebnahme_jahre = db.Column(db.String(200), nullable=True)  # Kommaseparierte Jahre, z.B. "2024, 2025"
    bemerkung = db.Column(db.Text)

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    geaendert_am = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tests = db.relationship('TestResult', backref='projekt', lazy=True)
    whk_configs = db.relationship('WHKConfig', backref='projekt', lazy=True,
                                   cascade='all, delete-orphan', order_by='WHKConfig.whk_nummer')
    abnahme_results = db.relationship('AbnahmeTestResult', backref='projekt',
                                       lazy=True, cascade='all, delete-orphan')

    # GWH-spezifische Relationships
    zsk_configs = db.relationship('ZSKConfig', backref='projekt', lazy=True,
                                  cascade='all, delete-orphan', order_by='ZSKConfig.reihenfolge')
    hgls_config = db.relationship('HGLSConfig', backref='projekt', lazy=True,
                                  cascade='all, delete-orphan', uselist=False)
    gwh_meteostations = db.relationship('GWHMeteostation', backref='projekt', lazy=True,
                                        cascade='all, delete-orphan', order_by='GWHMeteostation.reihenfolge')
    ewh_meteostations = db.relationship('EWHMeteostation', backref='projekt', lazy=True,
                                        cascade='all, delete-orphan', order_by='EWHMeteostation.reihenfolge')

    # GWH Parameter-Prüfung Relationships
    zsk_parameter_pruefungen = db.relationship('ZSKParameterPruefung', backref='projekt', lazy=True,
                                               cascade='all, delete-orphan')
    hgls_parameter_pruefungen = db.relationship('HGLSParameterPruefung', backref='projekt', lazy=True,
                                                cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project id={self.id} name="{self.projektname}" energie={self.energie}>'


class TestResult(db.Model):
    """
    Legacy Test-Ergebnisse (vor Abnahmetest-System).

    Historische Tabelle für generische Hardware-/Software-Tests.
    Neue Tests sollten über AbnahmeTestResult gespeichert werden.
    """
    __tablename__ = 'test_results'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Test-Metadaten
    test_name = db.Column(db.String(100), nullable=False, index=True)
    hardware_id = db.Column(db.String(50))
    software_version = db.Column(db.String(50))
    result = db.Column(db.String(20), index=True)  # Pass, Fail, Pending
    tester_name = db.Column(db.String(100))
    test_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    notes = db.Column(db.Text)

    # Foreign Key zu Project (optional, mit SET NULL on delete)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'),
                          nullable=True, index=True)

    def __repr__(self):
        return f'<TestResult id={self.id} name="{self.test_name}" result={self.result}>'


class WHKConfig(db.Model):
    """
    Weichenheizungskasten (WHK) Konfiguration für ein Projekt.

    Definiert die Anzahl der Abgänge, Temperatursonden, Antriebsheizungen
    und zugehörige Meteostationen pro WHK innerhalb eines Projekts.

    Constraints:
        - UNIQUE (projekt_id, whk_nummer): Jede WHK-Nummer nur einmal pro Projekt
    """
    __tablename__ = 'whk_configs'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Key
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                          nullable=False, index=True)

    # WHK-Daten
    whk_nummer = db.Column(db.String(20), nullable=False)  # z.B. "WHK 01"
    whk_typ = db.Column(db.String(50), nullable=True)  # z.B. "WHK_20_LU_01_16"
    preset_typ = db.Column(db.String(20), nullable=False, default='kabine_16hz')  # kabine_16hz, kabine_50hz, rahmen_16hz, rahmen_50hz
    anzahl_abgaenge = db.Column(db.Integer, nullable=False, default=1)  # 1-12
    anzahl_temperatursonden = db.Column(db.Integer, nullable=False, default=1)  # 1-12
    hat_antriebsheizung = db.Column(db.Boolean, default=False)
    meteostation = db.Column(db.String(50))  # Optional

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('projekt_id', 'whk_nummer', name='uq_projekt_whk'),
    )

    def __repr__(self):
        return (f'<WHKConfig id={self.id} projekt_id={self.projekt_id} '
                f'whk="{self.whk_nummer}" abgaenge={self.anzahl_abgaenge}>')


class TestQuestion(db.Model):
    """
    Testfragen-Vorlagen für Abnahmetests.

    Definiert wiederverwendbare Testfragen für verschiedene Komponententypen
    (Anlage, WHK, Abgang, Temperatursonde, Antriebsheizung, Meteostation).

    Constraints:
        - UNIQUE frage_nummer: Jede Fragenummer nur einmal
    """
    __tablename__ = 'test_questions'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Frage-Metadaten
    komponente_typ = db.Column(db.String(50), nullable=False, index=True)
    testszenario = db.Column(db.String(200), nullable=False)
    frage_nummer = db.Column(db.Integer, nullable=False, unique=True, index=True)
    frage_text = db.Column(db.Text, nullable=False)
    test_information = db.Column(db.Text)
    reihenfolge = db.Column(db.Integer, nullable=False, index=True)

    # JSON-Feld für Preset-Antworten (lss_ch, wh_lts)
    preset_antworten = db.Column(db.JSON, nullable=True)

    # Erwartetes Ergebnis und Screenshot
    erwartetes_ergebnis = db.Column(db.Text, nullable=True)
    screenshot_pfad = db.Column(db.String(255), nullable=True)

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    abnahme_results = db.relationship('AbnahmeTestResult', backref='test_question',
                                       lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return (f'<TestQuestion id={self.id} typ="{self.komponente_typ}" '
                f'nr={self.frage_nummer} szenario="{self.testszenario[:30]}">')


class AbnahmeTestResult(db.Model):
    """
    Abnahmetest-Ergebnisse für WHS-Projekte.

    Speichert Test-Ergebnisse für beide Systeme (LSS-CH und WH-LTS) mit
    separaten Bemerkungsfeldern. Unterstützt Tests auf verschiedenen
    Komponenten-Ebenen (Anlage, WHK, Abgang, Temperatursonde, etc.).

    Composite Indizes:
        - (projekt_id, test_question_id): Schnelles Laden aller Tests eines Projekts
        - (komponente_index, spalte): Schnelle Filterung nach Komponente
        - (getestet_am): Zeitbasierte Sortierung
    """
    __tablename__ = 'abnahme_test_results'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    test_question_id = db.Column(db.Integer, db.ForeignKey('test_questions.id', ondelete='CASCADE'),
                                nullable=False, index=True)

    # Komponenten-Identifikation
    komponente_index = db.Column(db.String(50), nullable=False, index=True)  # z.B. "WHK 01", "MS 01A"
    spalte = db.Column(db.String(100), index=True)  # z.B. "Abgang 01", "TS 02", "Antriebsheizung"

    # Test-Ergebnisse (richtig, falsch, nicht_testbar, null)
    lss_ch_result = db.Column(db.String(20), index=True)
    wh_lts_result = db.Column(db.String(20), index=True)

    # System-spezifische Bemerkungen
    lss_ch_bemerkung = db.Column(db.Text)
    wh_lts_bemerkung = db.Column(db.Text)

    # Timestamps und Tester
    getestet_am = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    tester = db.Column(db.String(100))

    # Composite Indizes für Performance
    __table_args__ = (
        db.Index('ix_projekt_question', 'projekt_id', 'test_question_id'),
        db.Index('ix_komponente_spalte', 'komponente_index', 'spalte'),
    )

    def __repr__(self):
        return (f'<AbnahmeTestResult id={self.id} projekt_id={self.projekt_id} '
                f'question_id={self.test_question_id} komponente="{self.komponente_index}" '
                f'spalte="{self.spalte}">')


class ProjectTimeLog(db.Model):
    """
    Zeiterfassung für Projektaktivitäten.

    Erfasst die Zeit, die Benutzer auf verschiedenen Seiten der Anwendung
    verbringen (Konfiguration, Abnahmetest, Export, etc.).

    Activity Types:
        - 'konfiguration': WHK-Konfigurationsseite
        - 'abnahmetest': Abnahmetest-Durchführung
        - 'export': Export-Übersicht und Konfiguration
        - 'testabschluss': Testabschluss-Seite
        - 'testfragen': Testfragen-Verwaltung
    """
    __tablename__ = 'project_time_logs'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Key zu Project (nullable für allgemeine Aktivitäten)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                          nullable=True, index=True)

    # Foreign Key zu User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
                       nullable=True, index=True)

    # Aktivitätstyp
    activity_type = db.Column(db.String(50), nullable=False, index=True)

    # Zeitstempel
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)

    # Berechnete Dauer in Sekunden
    duration_seconds = db.Column(db.Integer, nullable=True)

    # Besuchte Seite
    page_url = db.Column(db.String(500), nullable=True)

    # Status (aktiv, beendet, abgebrochen)
    status = db.Column(db.String(20), default='aktiv', index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    projekt = db.relationship('Project', backref=db.backref('time_logs', lazy=True,
                              cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('time_logs', lazy=True))

    # Composite Indizes für Performance
    __table_args__ = (
        db.Index('ix_timelog_projekt_activity', 'projekt_id', 'activity_type'),
        db.Index('ix_timelog_status_start', 'status', 'start_time'),
    )

    def calculate_duration(self):
        """Berechnet die Dauer in Sekunden wenn end_time gesetzt ist."""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())
            return self.duration_seconds
        return None

    def format_duration(self):
        """Formatiert die Dauer als HH:MM:SS String."""
        if self.duration_seconds is None:
            return '-'
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        if hours > 0:
            return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
        return f'{minutes:02d}:{seconds:02d}'

    def __repr__(self):
        return (f'<ProjectTimeLog id={self.id} projekt_id={self.projekt_id} '
                f'activity="{self.activity_type}" duration={self.duration_seconds}s>')


class AppSettings(db.Model):
    """
    Anwendungsweite Einstellungen.

    Speichert konfigurierbare Parameter wie Timeout-Zeiten.
    Es sollte nur einen Datensatz geben (Singleton-Pattern).
    """
    __tablename__ = 'app_settings'

    id = db.Column(db.Integer, primary_key=True)

    # Zeiterfassung
    zeiterfassung_timeout_minuten = db.Column(db.Integer, default=60)  # Standard: 60 Minuten

    # Timestamps
    geaendert_am = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_settings():
        """Holt die Einstellungen oder erstellt Standardwerte."""
        settings = AppSettings.query.first()
        if not settings:
            settings = AppSettings(zeiterfassung_timeout_minuten=60)
            db.session.add(settings)
            db.session.commit()
        return settings

    def __repr__(self):
        return f'<AppSettings timeout={self.zeiterfassung_timeout_minuten}min>'


class TestabschlussItem(db.Model):
    """
    Testabschluss-Einträge für EWH und GWH.

    Speichert die Checklisten-Punkte für die Testabschluss-Seite,
    die nach einem Abnahmetest durchgeführt werden müssen.
    """
    __tablename__ = 'testabschluss_items'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Energie-Typ (EWH oder GWH)
    energie_typ = db.Column(db.String(10), nullable=False, index=True)

    # Inhalt
    titel = db.Column(db.String(200), nullable=False)
    beschreibung = db.Column(db.Text, nullable=False)
    highlight_text = db.Column(db.String(100), nullable=True)  # Der grün hervorgehobene Text

    # Sortierung und Status
    reihenfolge = db.Column(db.Integer, nullable=False, default=0, index=True)
    aktiv = db.Column(db.Boolean, default=True, index=True)

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    geaendert_am = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_items_by_energie(energie_typ):
        """Holt alle aktiven Einträge für einen Energie-Typ, sortiert nach Reihenfolge."""
        return TestabschlussItem.query.filter_by(
            energie_typ=energie_typ,
            aktiv=True
        ).order_by(TestabschlussItem.reihenfolge).all()

    @staticmethod
    def init_default_items():
        """Initialisiert die Standard-EWH-Einträge falls keine vorhanden sind."""
        if TestabschlussItem.query.count() == 0:
            default_items = [
                TestabschlussItem(
                    energie_typ='EWH',
                    titel='Freigabe deaktivieren',
                    beschreibung='Die WH-Anlage muss nach dem Abnahmetest auf {highlight} geschaltet werden.',
                    highlight_text='Freigabe Aus',
                    reihenfolge=1
                ),
                TestabschlussItem(
                    energie_typ='EWH',
                    titel='LSS-CH Meldung deaktivieren',
                    beschreibung='Die WH-Anlage muss nach dem Abnahmetest auf {highlight} geschaltet werden.',
                    highlight_text='Meldung an LSS-CH Aus',
                    reihenfolge=2
                ),
                TestabschlussItem(
                    energie_typ='EWH',
                    titel='Betriebszentrale Einschaltdauer',
                    beschreibung='Falls die Einschaltdauer der Betriebszentrale verändert wurde, muss sie wieder auf den {highlight} gesetzt werden.',
                    highlight_text='Standardwert',
                    reihenfolge=3
                )
            ]
            for item in default_items:
                db.session.add(item)
            db.session.commit()

    def __repr__(self):
        return f'<TestabschlussItem id={self.id} typ={self.energie_typ} titel="{self.titel[:30]}">'


class ZSKConfig(db.Model):
    """
    Zündschaltkasten (ZSK) Konfiguration für GWH-Projekte.

    Definiert die Anzahl der Teile (Brennerrohre/Weichen), Temperatursonden,
    Gasversorgung und Kathodenschutz pro ZSK innerhalb eines GWH-Projekts.

    Constraints:
        - UNIQUE (projekt_id, zsk_nummer): Jede ZSK-Nummer nur einmal pro Projekt
    """
    __tablename__ = 'zsk_configs'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Key
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                          nullable=False, index=True)

    # ZSK-Daten
    zsk_nummer = db.Column(db.String(4), nullable=False)  # z.B. "01", "02"
    anzahl_teile = db.Column(db.Integer, nullable=False, default=1)  # 1-12 (Brennerrohre/Weichen)
    hat_temperatursonde = db.Column(db.Boolean, default=False)
    gasversorgung = db.Column(db.String(20), default='zentral')  # 'zentral' oder 'dezentral'
    kathodenschutz = db.Column(db.Boolean, default=False)
    reihenfolge = db.Column(db.Integer, nullable=False, default=0, index=True)

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    meteostations = db.relationship('GWHMeteostation', backref='zugeordneter_zsk',
                                    lazy=True, foreign_keys='GWHMeteostation.zugeordneter_zsk_id',
                                    order_by='GWHMeteostation.reihenfolge')

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('projekt_id', 'zsk_nummer', name='uq_projekt_zsk'),
    )

    def __repr__(self):
        return (f'<ZSKConfig id={self.id} projekt_id={self.projekt_id} '
                f'zsk="{self.zsk_nummer}" teile={self.anzahl_teile}>')


class HGLSConfig(db.Model):
    """
    Hauptgasleitungssteuerung (HGLS) Konfiguration für GWH-Projekte.

    Definiert die zentrale HGLS-Konfiguration eines GWH-Projekts mit
    Gastyp, Ventilen, Gaswarnanlage, Verdampfern und weiteren Komponenten.

    Constraints:
        - UNIQUE projekt_id: Maximal eine HGLS pro Projekt
    """
    __tablename__ = 'hgls_configs'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Key (unique: max. 1 HGLS pro Projekt)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                          nullable=False, unique=True, index=True)

    # HGLS-Daten
    hgls_typ = db.Column(db.String(20), nullable=True)  # 'Propan' oder 'Erdgas'
    hat_fuellventil = db.Column(db.Boolean, default=False)
    hat_bypassventil = db.Column(db.Boolean, default=False)
    hat_gaswarnanlage = db.Column(db.Boolean, default=False)
    hat_lueftungsanlage = db.Column(db.Boolean, default=False)
    hat_mengenmesser_blockade = db.Column(db.Boolean, default=False)
    hat_elektroverdampfer = db.Column(db.Boolean, default=False)
    gasverdampfer_anzahl = db.Column(db.Integer, default=0)  # 0-2
    hat_tankdruckueberwachung = db.Column(db.Boolean, default=False)
    hat_tankberieselung = db.Column(db.Boolean, default=False)
    hat_kathodenschutz = db.Column(db.Boolean, default=False)

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (f'<HGLSConfig id={self.id} projekt_id={self.projekt_id} '
                f'typ="{self.hgls_typ}" verdampfer={self.gasverdampfer_anzahl}>')


class GWHMeteostation(db.Model):
    """
    Meteostation für GWH-Projekte.

    Definiert Meteostationen die an ZSKs angeschlossen sind, mit
    Namen, Modbus-Adresse und Zuordnung zum jeweiligen ZSK.

    Constraints:
        - UNIQUE (projekt_id, ms_nummer): Jede MS-Nummer nur einmal pro Projekt
    """
    __tablename__ = 'gwh_meteostations'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    zugeordneter_zsk_id = db.Column(db.Integer, db.ForeignKey('zsk_configs.id', ondelete='SET NULL'),
                                   nullable=True, index=True)

    # Meteostation-Daten
    ms_nummer = db.Column(db.String(5), nullable=False)  # z.B. "01", "02", max. "05"
    name = db.Column(db.String(12), default='MS 01')  # max. 12 Zeichen
    modbus_adresse = db.Column(db.Integer, default=50)
    reihenfolge = db.Column(db.Integer, nullable=False, default=0, index=True)

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('projekt_id', 'ms_nummer', name='uq_projekt_ms'),
    )

    def __repr__(self):
        return (f'<GWHMeteostation id={self.id} projekt_id={self.projekt_id} '
                f'ms="{self.ms_nummer}" name="{self.name}">')


class EWHMeteostation(db.Model):
    """
    Meteostation für EWH-Projekte.

    Definiert Meteostationen die an WHKs angeschlossen sind.

    Constraints:
        - UNIQUE (projekt_id, ms_nummer): Jede MS-Nummer nur einmal pro Projekt
    """
    __tablename__ = 'ewh_meteostations'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    zugeordnete_whk_id = db.Column(db.Integer, db.ForeignKey('whk_configs.id', ondelete='SET NULL'),
                                   nullable=True, index=True)

    # Meteostation-Daten
    ms_nummer = db.Column(db.String(20), nullable=False)  # z.B. "01", "02"
    reihenfolge = db.Column(db.Integer, nullable=False, default=0, index=True)

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    zugeordnete_whk = db.relationship('WHKConfig', backref='meteostationen', foreign_keys=[zugeordnete_whk_id])

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('projekt_id', 'ms_nummer', name='uq_ewh_projekt_ms'),
    )

    def __repr__(self):
        return (f'<EWHMeteostation id={self.id} projekt_id={self.projekt_id} '
                f'ms="{self.ms_nummer}">')


class ZSKParameterPruefung(db.Model):
    """
    Parameter-Prüfungsergebnisse für ZSK-Komponenten.

    Speichert die Ist-Werte und Prüfstatus für jeden ZSK-Parameter
    bei der Inbetriebnahme (Parameter-Prüfung).

    Constraints:
        - UNIQUE (projekt_id, zsk_nummer, parameter_name): Jeder Parameter
          nur einmal pro ZSK pro Projekt
    """
    __tablename__ = 'zsk_parameter_pruefung'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                          nullable=False, index=True)

    # ZSK-Identifikation
    zsk_nummer = db.Column(db.String(4), nullable=False)  # z.B. "01", "02"

    # Parameter-Daten
    parameter_name = db.Column(db.String(50), nullable=False)  # z.B. "anstiegsdruck_maximal"
    ist_wert = db.Column(db.String(50), nullable=True)  # Eingegebener Ist-Wert

    # Prüfstatus
    geprueft = db.Column(db.Boolean, default=False, nullable=False)
    nicht_testbar = db.Column(db.Boolean, default=False, nullable=False)
    geprueft_am = db.Column(db.DateTime, nullable=True)
    geprueft_von = db.Column(db.String(100), nullable=True)  # Benutzername

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    aktualisiert_am = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('projekt_id', 'zsk_nummer', 'parameter_name',
                          name='uq_zsk_parameter'),
    )

    def __repr__(self):
        return (f'<ZSKParameterPruefung id={self.id} projekt_id={self.projekt_id} '
                f'zsk="{self.zsk_nummer}" param="{self.parameter_name}" '
                f'geprueft={self.geprueft}>')


class HGLSParameterPruefung(db.Model):
    """
    Parameter-Prüfungsergebnisse für HGLS-Komponente.

    Speichert die Ist-Werte und Prüfstatus für jeden HGLS-Parameter
    bei der Inbetriebnahme (Parameter-Prüfung).

    Constraints:
        - UNIQUE (projekt_id, parameter_name): Jeder Parameter nur einmal pro Projekt
    """
    __tablename__ = 'hgls_parameter_pruefung'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    projekt_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'),
                          nullable=False, index=True)

    # Parameter-Daten
    parameter_name = db.Column(db.String(50), nullable=False)  # z.B. "druckanstiegszeit"
    ist_wert = db.Column(db.String(50), nullable=True)  # Eingegebener Ist-Wert

    # Prüfstatus
    geprueft = db.Column(db.Boolean, default=False, nullable=False)
    nicht_testbar = db.Column(db.Boolean, default=False, nullable=False)
    geprueft_am = db.Column(db.DateTime, nullable=True)
    geprueft_von = db.Column(db.String(100), nullable=True)  # Benutzername

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    aktualisiert_am = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('projekt_id', 'parameter_name', name='uq_hgls_parameter'),
    )

    def __repr__(self):
        return (f'<HGLSParameterPruefung id={self.id} projekt_id={self.projekt_id} '
                f'param="{self.parameter_name}" geprueft={self.geprueft}>')


class Stuecknachweis(db.Model):
    """
    Stücknachweis für WHK-Konfigurationen (EWH).

    Speichert Normen-Prüfungen (EN 61439-1), Messungen und FI-Messungen
    pro WHK innerhalb eines Projekts.

    Constraints:
        - Jeder WHK hat maximal einen Stücknachweis (uselist=False auf backref)
    """
    __tablename__ = 'stuecknachweis'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    whk_config_id = db.Column(db.Integer, db.ForeignKey('whk_configs.id'), nullable=False)

    # Kopfdaten
    typbezeichnung = db.Column(db.String(100), nullable=True)
    auftraggeber = db.Column(db.String(100), default='SBB AG')
    hersteller = db.Column(db.String(100), default='Achermann & Co. AG')

    # Herstellung
    herstellungsdatum = db.Column(db.Date, nullable=True)
    herstellungsjahr = db.Column(db.Integer, nullable=True)

    # Grund der Prüfung
    grund_erstpruefung = db.Column(db.Boolean, default=True)
    grund_wiederholung = db.Column(db.Boolean, default=False)
    grund_aenderung = db.Column(db.Boolean, default=False)
    grund_instandsetzung = db.Column(db.Boolean, default=False)

    # Schutzmassnahme
    schutz_tn_s = db.Column(db.Boolean, default=True)
    schutz_tn_c = db.Column(db.Boolean, default=False)
    schutz_tn_c_s = db.Column(db.Boolean, default=False)
    schutz_tt = db.Column(db.Boolean, default=True)
    schutz_it = db.Column(db.Boolean, default=False)

    # Berührungsschutz
    beruehr_nicht_instruiert = db.Column(db.Boolean, default=False)
    beruehr_instruiert = db.Column(db.Boolean, default=True)

    # Normen-Checkboxen (EN 61439-1) - alle default True
    check_11_2 = db.Column(db.Boolean, default=True)
    check_11_3_kriech = db.Column(db.Boolean, default=True)
    check_11_3_luft_1 = db.Column(db.Boolean, default=True)
    check_11_3_luft_2 = db.Column(db.Boolean, default=True)
    check_11_3_luft_3 = db.Column(db.Boolean, default=True)
    check_11_4_schutz = db.Column(db.Boolean, default=True)
    check_11_4_durch = db.Column(db.Boolean, default=True)
    check_11_4_geschr = db.Column(db.Boolean, default=True)
    check_11_5 = db.Column(db.Boolean, default=True)
    check_11_6_verb = db.Column(db.Boolean, default=True)
    check_11_6_verd = db.Column(db.Boolean, default=True)
    check_11_7 = db.Column(db.Boolean, default=True)
    check_11_8 = db.Column(db.Boolean, default=True)
    check_11_1_kenn = db.Column(db.Boolean, default=True)
    check_11_1_doku = db.Column(db.Boolean, default=True)
    check_11_1_funk = db.Column(db.Boolean, default=True)

    # Messungen
    niederohm_ergebnis = db.Column(db.String(50), nullable=True)
    niederohm_status = db.Column(db.Boolean, default=True)
    spannung_ergebnis = db.Column(db.String(50), nullable=True)
    spannung_status = db.Column(db.Boolean, default=True)
    isolation_ergebnis = db.Column(db.String(50), nullable=True)
    isolation_status = db.Column(db.Boolean, default=True)

    # Bemerkung
    bemerkung = db.Column(db.Text, nullable=True)

    # Timestamps
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    geaendert_am = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='stuecknachweise')
    whk_config = db.relationship('WHKConfig', backref=db.backref('stuecknachweis', uselist=False))
    fi_messungen = db.relationship('FiMessung', backref='stuecknachweis',
                                    cascade='all, delete-orphan', order_by='FiMessung.reihenfolge')

    def __repr__(self):
        return (f'<Stuecknachweis id={self.id} project_id={self.project_id} '
                f'whk_config_id={self.whk_config_id}>')


class FiMessung(db.Model):
    """
    FI-Schutzschalter Messung für Stücknachweise.

    Speichert Auslösestrom (∆I) und Auslösezeit (∆t) pro Sicherung
    innerhalb eines Stücknachweises.
    """
    __tablename__ = 'fi_messungen'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Key
    stuecknachweis_id = db.Column(db.Integer, db.ForeignKey('stuecknachweis.id'), nullable=False)

    # Messdaten
    sicherung = db.Column(db.String(20), nullable=False)    # z.B. 'F302.2'
    delta_i_ma = db.Column(db.Integer, nullable=True)        # ∆I FI [mA]
    delta_t_ms = db.Column(db.Integer, nullable=True)        # ∆t FI [ms]
    status = db.Column(db.Boolean, default=True)
    reihenfolge = db.Column(db.Integer, default=0)

    def __repr__(self):
        return (f'<FiMessung id={self.id} stuecknachweis_id={self.stuecknachweis_id} '
                f'sicherung="{self.sicherung}">')


SICHERUNGEN_PRESET = [
    'F302.2', 'F306.2', 'F312.2', 'F316.2',
    'F322.2', 'F326.2', 'F332.2', 'F336.2',
    'F342.2', 'F346.2', 'F352.2', 'F356.2'
]


def generiere_fi_sicherungen(anzahl_abgaenge):
    """
    Generiert FI-Sicherungsbezeichnungen basierend auf Abgang-Anzahl.

    1 Sicherung pro Abgang, max. 12 Abgänge.
    Schema ist für alle Presets identisch (kabine/rahmen, 16hz/50hz).

    Gibt Liste von Strings zurück.
    """
    anzahl = min(anzahl_abgaenge, 12)
    return SICHERUNGEN_PRESET[:anzahl]
