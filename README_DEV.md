# WHS Testprotokoll - Development Setup

## 🚀 Schnellstart

### Voraussetzungen
- **Python 3.11+** (aktuell installiert: Python 3.13.6)
- **Git** (optional, für Versionskontrolle)
- **Windows 10/11** oder **Windows Server 2022**

---

## 📦 Installation & Setup

### 1. Repository klonen / Projekt kopieren
```bash
# Falls aus Git:
git clone <repository-url>
cd whs_app

# Oder einfach Projekt-Ordner kopieren
```

### 2. Virtual Environment erstellen
```bash
# Virtual Environment erstellen
python -m venv venv

# Virtual Environment aktivieren (Windows)
venv\Scripts\activate

# Wenn aktiviert, sollte (venv) vor dem Prompt erscheinen
```

### 3. Dependencies installieren
```bash
# Alle Abhängigkeiten installieren
pip install -r requirements.txt
```

### 4. Datenbank-Status prüfen
```bash
# SQLite-Version prüfen
python -c "import sqlite3; print(f'SQLite: {sqlite3.sqlite_version}')"

# Tabellen in Datenbank anzeigen
python -c "import sqlite3; conn=sqlite3.connect('database/whs.db'); print([row[0] for row in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()]); conn.close()"
```

---

## 🖥️ Development Server starten

### Methode 1: Mit run_dev.py (empfohlen)
```bash
# Virtual Environment aktivieren (falls nicht aktiv)
venv\Scripts\activate

# Development-Server starten
python run_dev.py
```

### Methode 2: Direkt mit app.py
```bash
# Virtual Environment aktivieren
venv\Scripts\activate

# App direkt starten
python app.py
```

### Methode 3: Mit Flask-CLI
```bash
# Virtual Environment aktivieren
venv\Scripts\activate

# Flask Development Server
set FLASK_APP=app.py
set FLASK_ENV=development
flask run
```

**Server läuft auf:** http://127.0.0.1:5000

---

## 🗂️ Projekt-Struktur

```
whs_app/
├── venv/                      # Virtual Environment (nicht in Git)
├── database/                  # SQLite Datenbank
│   └── whs.db                 # Haupt-Datenbank (nicht in Git)
├── docs/                      # Technische Dokumentation
│   └── EXPORT_SYSTEM.md       # Export-System-Dokumentation
├── templates/                 # HTML Jinja2-Templates
│   ├── base.html              # Basis-Template
│   ├── index.html             # Dashboard
│   ├── projekte.html          # Projektübersicht mit Live-Suche
│   ├── projekt_form.html      # Projekt-Formular
│   ├── konfiguration.html     # WHK-Konfiguration
│   ├── abnahmetest.html       # Abnahmetest-Durchführung
│   ├── testfragen_verwaltung.html  # Testfragen-Verwaltung
│   ├── export.html            # Export-Übersicht (Stufe 1)
│   ├── export_config.html     # Export-Konfiguration (Stufe 2)
│   └── pdf_abnahmetest.html   # PDF-Template (Stufe 3)
├── static/                    # CSS, JS, Bilder
│   ├── css/
│   │   └── style.css          # Haupt-Stylesheet (Dark Mode)
│   └── js/
│       ├── abnahmetest.js     # Abnahmetest-Logik
│       └── konfiguration.js   # WHK-Konfigurations-Logik
├── assets/                    # Assets (SVGs, Logos)
│   ├── sbb06.gif              # SBB Logo
│   ├── Logo Achermann black.svg  # Achermann Logo
│   ├── richtig.svg            # ✓ Icon
│   ├── falsch.svg             # ✗ Icon
│   └── nicht_testbar.svg      # ⊘ Icon
├── scripts/                   # Utility-Scripts
│   ├── import_json_project.py # JSON-Projekt-Import
│   ├── export_database.py     # Datenbank-Export
│   └── generate_test_data.py  # Testdaten generieren
├── uploads/                   # Hochgeladene Dateien (nicht in Git)
├── logs/                      # Log-Dateien (nicht in Git)
├── Projekte/                  # Projekt-Imports/Exports
│
├── app.py                     # Haupt-Flask-Anwendung
├── models.py                  # Datenbank-Modelle (SQLAlchemy)
├── config.py                  # Production-Konfiguration
├── config_dev.py              # Development-Konfiguration (DEBUG=True)
├── run_dev.py                 # Development-Server-Script
├── run_production.py          # Production-Server (Waitress)
│
├── requirements.txt           # Python-Dependencies
├── .gitignore                 # Git-Ignore-Regeln
├── README.md                  # Production-Dokumentation
├── README_DEV.md              # Diese Datei (Development-Guide)
├── CHANGELOG.md               # Versionshistorie
└── SOFTWAREBESCHREIBUNG.md    # Software-Dokumentation
```

---

## 🔧 Konfiguration

### Development vs. Production

**Development (config_dev.py):**
```python
DEBUG = True
TESTING = False
ENV = 'development'
SQLALCHEMY_DATABASE_URI = 'sqlite:///database/whs.db'
SECRET_KEY = 'dev-secret-key-not-for-production'
```

**Production (config.py):**
```python
DEBUG = False
TESTING = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///database/whs.db'
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
```

### Umgebungsvariablen setzen (optional)
```bash
# Windows CMD
set SECRET_KEY=your-super-secret-key
set FLASK_ENV=development

# Windows PowerShell
$env:SECRET_KEY = "your-super-secret-key"
$env:FLASK_ENV = "development"
```

---

## 🧪 Testing & Debugging

### Datenbank zurücksetzen
```bash
# ACHTUNG: Löscht alle Daten!
python -c "from app import db; db.drop_all(); db.create_all(); print('Datenbank zurückgesetzt!')"
```

### Test-Daten generieren
```bash
python generate_test_data.py
```

### Datenbank-Schema anzeigen
```bash
python -c "from models import *; import inspect; print([m.__name__ for m in [Project, WHKConfig, TestQuestion, AbnahmeTestResult, TestResult]])"
```

### Flask-Shell (interaktive Python-Shell)
```bash
flask shell

# Im Shell:
>>> from models import *
>>> Project.query.all()
>>> db.session.query(Project).count()
```

---

## 📊 Datenbank-Management

### SQLite Datenbank-Informationen
- **Pfad:** `database/whs.db`
- **Engine:** SQLite 3.50.4+
- **ORM:** SQLAlchemy 2.0.44

### Vorhandene Tabellen
1. **projects** - Weichenheizungsprojekte (EWH/GWH)
2. **whk_configs** - WHK-Konfigurationen
3. **test_questions** - Testfragen mit Presets
4. **abnahme_test_results** - Abnahmetest-Ergebnisse
5. **test_results** - Legacy Test-Ergebnisse

### Datenbank-Backup erstellen
```bash
# Windows CMD
copy database\whs.db database_backups\whs_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db

# Manuell via Python
python -c "import shutil; from datetime import datetime; shutil.copy('database/whs.db', f'database_backups/whs_backup_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db'); print('Backup erstellt!')"
```

---

## 🐛 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'flask'"
**Lösung:**
```bash
# Virtual Environment aktivieren!
venv\Scripts\activate

# Dependencies erneut installieren
pip install -r requirements.txt
```

### Problem: "OperationalError: unable to open database file"
**Lösung:**
```bash
# Prüfe ob database/ Verzeichnis existiert
mkdir database

# Datenbank neu initialisieren
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Datenbank initialisiert!')"
```

### Problem: "Address already in use (Port 5000 belegt)"
**Lösung:**
```bash
# Anderen Port verwenden
python -c "from app import app; app.run(port=5001)"

# Oder Port 5000 freigeben (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Problem: WeasyPrint PDF-Export funktioniert nicht
**Lösung:**
```bash
# GTK3 Runtime für Windows installieren
# Download: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

# Alternative: Excel-Export verwenden (funktioniert ohne GTK)
```

---

## 📚 Wichtige Entwickler-Befehle

```bash
# Virtual Environment aktivieren
venv\Scripts\activate

# Server starten (mit Auto-Reload)
python run_dev.py

# Dependencies installieren
pip install <package-name>

# Dependencies einfrieren
pip freeze > requirements.txt

# Neue Migration erstellen
python <migration_script>.py

# Datenbank-Export
python export_database.py

# Projekt-Import
python import_json_project.py "Projekte/<projekt>.json"

# Testdaten generieren (inklusive Testfragen und Antworten)
python scripts/generate_test_data.py

# Export-Funktionalität testen
# 1. Browser öffnen: http://127.0.0.1:5000/export
# 2. Projekt auswählen und "Exportieren" klicken
# 3. Sektionen auswählen (Deckblatt, WHKs, Meteostationen)
# 4. PDF oder Excel Format wählen
# 5. "Export starten" klicken
```

---

## 🚢 Deployment auf Production-Server

### 1. Dateien kopieren (ohne venv, database, __pycache__)
```powershell
# PowerShell-Script verwenden
.\deploy_to_server.ps1
```

### 2. Production-Server neu starten
```bash
# Auf Production-Server (Windows Server 2022)
# IIS-Dienst neu starten oder Waitress-Service neu starten
```

### 3. Datenbank-Backup vor Deployment
```bash
# Backup auf Production-Server erstellen
python export_database.py
```

---

## 📝 Git Workflow

```bash
# Änderungen anzeigen
git status

# Dateien hinzufügen
git add .

# Commit erstellen
git commit -m "Beschreibung der Änderungen"

# Push zu Remote
git push origin main

# Pull von Remote
git pull origin main
```

---

## 🔗 Nützliche Links

- **Flask Dokumentation:** https://flask.palletsprojects.com/
- **SQLAlchemy Dokumentation:** https://docs.sqlalchemy.org/
- **WeasyPrint Dokumentation:** https://doc.courtbouillon.org/weasyprint/
- **Python 3.13 Dokumentation:** https://docs.python.org/3.13/

---

## 👨‍💻 Entwickler-Notizen

### Code-Stil
- **PEP 8** für Python-Code
- **4 Spaces** für Einrückung
- **Docstrings** für Funktionen
- **Kommentare** auf Deutsch

### Best Practices
- Immer im Virtual Environment arbeiten
- Vor größeren Änderungen: Datenbank-Backup erstellen
- Neue Dependencies in `requirements.txt` dokumentieren
- Migrations-Scripts für Datenbank-Änderungen verwenden

---

## 📞 Support & Kontakt

Bei Problemen oder Fragen:
1. Prüfe diese Dokumentation (README_DEV.md)
2. Prüfe die Log-Dateien in `logs/`
3. Prüfe die Software-Beschreibung: `SOFTWAREBESCHREIBUNG.md`
4. Prüfe den Changelog: `CHANGELOG.md`
5. Prüfe die Export-System-Doku: `docs/EXPORT_SYSTEM.md`
6. Prüfe die Session-Dokumentation: `SESSION_DOKUMENTATION.md` (falls vorhanden)

---

**Letzte Aktualisierung:** 2025-01-12
**Version:** 1.1
**Author:** WHS Development Team
