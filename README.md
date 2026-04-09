# Abnahmetest-Anwendung für Weichenheizungsprojekte (SBB AG)

Eine webbasierte Anwendung zur Verwaltung und Dokumentation von Abnahmetests für Weichenheizungsprojekte (EWH und GWH) der Schweizerischen Bundesbahnen.

## Funktionen

- **Projektverwaltung:** Vollständige CRUD-Operationen für Weichenheizungsprojekte mit Live-Suche
- **WHK-Konfiguration:** Verwaltung von Weichenheizkabinen (WHKs) mit Abgängen, Temperatursonden und Antriebsheizungen
- **Abnahmetest-Durchführung:** Dual-System-Tests (LSS-CH und WH-LTS) mit Auto-Save
  - 🆕 Optimierte kompakte Darstellung aller 12 Abgänge ohne Scrollen
  - 🆕 Zweizeilige Abgang-Header für platzsparende Anzeige
  - 🆕 Komponenten-spezifische Fragenzählung
  - 🆕 Dynamischer Success-Frame mit Testname
  - 🆕 Integrierte Navigation für kompakteres Layout
- **Testfragen-Verwaltung:** Wiederverwendbare Testfragen mit Preset-Antworten
- **🆕 Testabschluss-Seite:** Post-Test-Einstellungen für WH-Leitstand
  - EWH-Kategorie mit 3 Checklisten-Punkten für wichtige Einstellungen
  - GWH-Kategorie (Platzhalter für zukünftige Inhalte)
  - Visuell ansprechend mit farbigen Kategorie-Headern und Hover-Effekten
- **🆕 Export-System (3-Stufen-Workflow):**
  - Stufe 1: Export-Übersicht mit allen Projekten
  - Stufe 2: Flexible Sektion-Auswahl (Deckblatt, WHKs, Meteostationen)
  - Stufe 3: PDF/Excel-Export mit intelligenten Dateinamen
- **Live-Suche:** Echtzeit-Filterung auf Projekt- und Export-Übersicht
- **Responsive Design:** Optimiert für Desktop und Mobile mit Dark Mode

## Technologie-Stack

- **Backend:** Flask 3.0.0
- **ORM:** SQLAlchemy 3.1.1 (Flask-SQLAlchemy)
- **Datenbank:** SQLite 3 (Datei-basiert, keine Installation erforderlich)
- **Frontend:** HTML5, CSS3, Jinja2
- **PDF-Export:** WeasyPrint 66.0
- **Excel-Export:** openpyxl 3.1.2
- **Production Server:** Waitress 2.1.2

## Installation

### Voraussetzungen

- Python 3.11 oder höher
- pip (Python Package Manager)
- Windows 10/11 oder Windows Server (empfohlen)

### Schritte

1. **Repository klonen oder Dateien kopieren**

   ```bash
   git clone <repository-url>
   cd whs_app
   ```

2. **Virtuelle Umgebung erstellen und aktivieren**

   Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   Linux/Mac:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Dependencies installieren**

   ```bash
   pip install -r requirements.txt
   ```

4. **Datenbank initialisieren**

   Die SQLite-Datenbank wird automatisch beim ersten Start der Anwendung erstellt.
   Alternativ können Sie sie manuell initialisieren:

   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Datenbank erstellt!')"
   ```

## Anwendung starten

### Development-Modus (mit Debug)

```bash
# Virtual Environment aktivieren
venv\Scripts\activate

# Development-Server starten
python run_dev.py
```

### Production-Modus (mit Waitress)

```bash
# Virtual Environment aktivieren
venv\Scripts\activate

# Production-Server starten
python run_production.py
```

**Server läuft standardmäßig auf:** http://localhost:5000

## Projektstruktur

```
whs_app/
│
├── app.py                      # Hauptanwendung (Flask-Server)
├── config.py                   # Production-Konfiguration
├── config_dev.py               # Development-Konfiguration
├── models.py                   # SQLAlchemy Datenbankmodelle
├── requirements.txt            # Python-Abhängigkeiten
├── run_dev.py                  # Development-Server-Script
├── run_production.py           # Production-Server-Script
├── README.md                   # Diese Datei
├── SOFTWAREBESCHREIBUNG.md     # Detaillierte Software-Dokumentation
│
├── database/                   # SQLite Datenbank-Verzeichnis
│   └── whs.db                  # Haupt-Datenbank (wird automatisch erstellt)
│
├── templates/                  # HTML-Templates (Jinja2)
│   ├── base.html              # Basis-Layout
│   ├── projekte.html          # Projektübersicht
│   ├── projekt_form.html      # Projekt-Formular
│   ├── konfiguration.html     # WHK-Konfiguration
│   ├── abnahmetest.html       # Abnahmetest-Durchführung
│   ├── testfragen_verwaltung.html  # Testfragen-Verwaltung
│   ├── pdf_abnahmetest.html   # PDF-Template
│   └── ...
│
├── static/                     # Statische Dateien
│   ├── css/
│   │   └── style.css          # Haupt-Stylesheet
│   └── js/
│       ├── abnahmetest.js     # Abnahmetest-Logik
│       └── konfiguration.js   # WHK-Konfigurations-Logik
│
├── assets/                     # Assets (Logos, Icons)
│   ├── sbb06.gif              # SBB Logo
│   ├── Logo Achermann black.svg  # Achermann Logo
│   ├── richtig.svg            # ✓ Icon
│   ├── falsch.svg             # ✗ Icon
│   └── nicht_testbar.svg      # ⊘ Icon
│
├── scripts/                    # Utility-Scripts
│   ├── import_json_project.py # JSON-Projekt-Import
│   ├── export_database.py     # Datenbank-Export
│   ├── generate_test_data.py  # Testdaten generieren
│   └── ...
│
└── venv/                       # Virtuelle Python-Umgebung (nicht in Git)
```

## Verwendung

### Neues Projekt erstellen

1. Navigiere zu "Projekte" → "Neues Projekt"
2. Fülle die Projektdaten aus (Energie-Typ: EWH oder GWH, Projektname, etc.)
3. Klicke auf "Projekt speichern"

### WHK-Konfiguration

1. Öffne ein Projekt
2. Klicke auf "WH-Anlage" (Konfiguration)
3. Füge WHK-Einträge hinzu und konfiguriere:
   - WHK-Nummer
   - Anzahl Abgänge (1-12)
   - Anzahl Temperatursonden (1-12)
   - Antriebsheizung (Ja/Nein)
   - Meteostation
4. Die Konfiguration wird automatisch gespeichert (Auto-Save)

### Abnahmetest durchführen

1. Öffne ein Projekt
2. Klicke auf "Abnahmetest"
3. Beantworte die Testfragen für LSS-CH und WH-LTS
4. Antworten werden automatisch gespeichert
5. Exportiere das Protokoll als PDF oder Excel

## Konfiguration

Die Anwendung verwendet SQLite als Datenbank. Die Konfiguration befindet sich in `config.py`:

```python
# SQLite Datenbank (PRODUCTION)
SQLALCHEMY_DATABASE_URI = 'sqlite:///database/whs.db'
```

**Wichtig für Produktionsumgebung:**
- Verwende einen starken SECRET_KEY (Umgebungsvariable)
- Aktiviere HTTPS (SESSION_COOKIE_SECURE = True)
- Setze DEBUG = False
- Erstelle regelmäßige Backups der Datenbank

### Umgebungsvariablen (optional)

```bash
# Windows CMD
set SECRET_KEY=your-super-secret-production-key
set DATABASE_URL=sqlite:///path/to/custom/database.db

# Windows PowerShell
$env:SECRET_KEY = "your-super-secret-production-key"
$env:DATABASE_URL = "sqlite:///path/to/custom/database.db"
```

## Datenbank-Verwaltung

### Backup erstellen

```bash
# Einfache Datei-Kopie (SQLite)
copy database\whs.db database_backups\whs_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db

# Oder mit Python-Script
python scripts\export_database.py
```

### Datenbank zurücksetzen

```bash
# ACHTUNG: Löscht alle Daten!
del database\whs.db
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Datenbank neu erstellt!')"
```

### Testdaten generieren

```bash
python scripts\generate_test_data.py
```

## Export-Funktionen

### Neues 3-Stufen-Export-System

1. **Export-Übersicht** (`/export`)
   - Alle Projekte mit Live-Suche
   - "Exportieren"-Button pro Projekt

2. **Export-Konfiguration** (`/export/projekt/<id>`)
   - Flexible Sektion-Auswahl:
     - ☐ Deckblatt (optional)
     - ☐ WH-Anlage (optional)
     - ☐ Einzelne WHKs (individuell auswählbar)
     - ☐ Einzelne Meteostationen (individuell auswählbar)
   - Format-Wahl: PDF oder Excel
   - "Alle auswählen" / "Alle abwählen" Buttons

3. **Export-Generierung**
   - Intelligente Dateinamen basierend auf Auswahl
   - Nur gewählte Sektionen im Export

### PDF-Export

- Benötigt GTK3-Runtime auf Windows
- Download: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
- WeasyPrint 66.0
- Alternative: Nutzen Sie den Excel-Export

### Excel-Export

- Funktioniert ohne zusätzliche Dependencies
- Separate Sheets pro Sektion
- Bedingte Sheet-Erstellung basierend auf Auswahl

**Detaillierte Dokumentation:** Siehe `docs/EXPORT_SYSTEM.md`

## Fehlerbehebung

### Problem: "ModuleNotFoundError: No module named 'flask'"
**Lösung:** Aktiviere die virtuelle Umgebung und installiere die Dependencies
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Problem: "OperationalError: unable to open database file"
**Lösung:** Erstelle das database-Verzeichnis
```bash
mkdir database
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Problem: "Address already in use (Port 5000)"
**Lösung:** Verwende einen anderen Port oder beende den blockierenden Prozess
```bash
# Port 5001 verwenden
python -c "from app import app; app.run(port=5001)"

# Oder blockierenden Prozess beenden (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Problem: PDF-Export funktioniert nicht
**Lösung:** Installiere GTK3-Runtime oder nutze Excel-Export als Alternative

## Dokumentation

- **README.md** (diese Datei) - Übersicht und Installation
- **README_DEV.md** - Development-Setup und Befehle
- **SOFTWAREBESCHREIBUNG.md** - Detaillierte Software-Dokumentation
- **CHANGELOG.md** - Versionshistorie und Änderungen
- **docs/EXPORT_SYSTEM.md** - Export-System-Dokumentation (Routen, Templates, Code-Beispiele)

## Lizenz

© 2025 SBB AG / Achermann & Co. AG. Alle Rechte vorbehalten.

## Support

Bei Fragen oder Problemen:
1. Prüfe die Dokumentation (README_DEV.md, SOFTWAREBESCHREIBUNG.md)
2. Prüfe die Log-Dateien in `logs/`
3. Kontaktiere den System-Administrator

---

**Version:** 1.2
**Letzte Aktualisierung:** 2025-11-22
**Datenbank:** SQLite 3
**Changelog:** Siehe CHANGELOG.md
