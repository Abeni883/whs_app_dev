# Softwarebeschreibung: Abnahmetest-Anwendung für Weichenheizungsprojekte

## 1. Übersicht

Die Abnahmetest-Anwendung ist eine webbasierte Lösung zur Verwaltung und Durchführung von Abnahmetests für Weichenheizungsprojekte (WH-Anlagen) der Schweizerischen Bundesbahnen (SBB AG). Die Anwendung unterstützt sowohl elektrische Weichenheizungen (EWH) als auch gasbasierte Weichenheizungen (GWH).

### Technologie-Stack
- **Backend:** Python 3.11+, Flask 3.0.0
- **Datenbank:** SQLite 3 (Datei-basiert)
- **ORM:** SQLAlchemy 2.0.44 (Flask-SQLAlchemy 3.1.1)
- **Template-Engine:** Jinja2 3.1.6
- **Frontend:** HTML5, CSS3 (responsive Design), JavaScript (ES6+)
- **PDF-Export:** WeasyPrint 66.0
- **Excel-Export:** openpyxl 3.1.2
- **Production Server:** Waitress 2.1.2
- **Entwicklungsumgebung:** Windows, Python Virtual Environment

---

## 2. Hauptfunktionen

### 2.1 Projektverwaltung

Die Anwendung ermöglicht die vollständige Verwaltung von Weichenheizungsprojekten mit folgenden Funktionen:

#### Projektanlage
- Erfassung neuer Weichenheizungsprojekte
- Pflichtfelder:
  - **Energie-Typ:** EWH (Elektrische Weichenheizung) oder GWH (Gas-Weichenheizung)
  - **Projektname:** Beschreibende Bezeichnung des Projekts
- Optionale Felder:
  - **DIDOK Betriebspunkt:** Eindeutige Kennzeichnung des Bahnhofs/Standorts
  - **Baumappenversion:** Datum der Planungsversion
  - **Projektleiter (SBB AG):** Verantwortlicher Projektleiter
  - **Prüfer (Achermann & Co. AG):** Zuständiger Prüfer
  - **Prüfdatum:** Geplantes oder durchgeführtes Prüfdatum
  - **Bemerkung:** Freitextfeld für zusätzliche Informationen

#### Projektbearbeitung
- Bearbeitung aller Projektdaten
- Dynamisches Formular mit vorausgefüllten Werten
- Unterscheidung zwischen Neu-Modus und Bearbeitungs-Modus
- Datums-Felder mit HTML5-Datumsauswahl
- Validierung von Pflichtfeldern

#### Projektlöschung
- Sicherheitsabfrage via JavaScript-Dialog
- Prüfung auf zugeordnete Tests vor Löschung
- Schutz vor versehentlichem Löschen
- Flash-Messages für Erfolg und Fehler

#### Projektübersicht
- Tabellarische Darstellung aller Projekte
- Spalten:
  1. Energie (farbcodiert: EWH=Rot, GWH=Gelb)
  2. Projektname
  3. DIDOK Betriebspunkt
  4. Bearbeiten (Link)
  5. WH-Anlage (Konfiguration)
  6. Abnahmetest (Link)
  7. Löschen (Link)
- Sortierung nach Erstellungsdatum (neueste zuerst)
- Responsive Tabellendarstellung
- **Live-Suche:** Echtzeit-Filterung während der Eingabe (clientseitig)

#### Live-Suchfunktion
- **Echtzeit-Filterung:** Sofortige Anzeige während der Eingabe
- **Clientseitige Filterung:** Keine Server-Requests nötig
- **Suchfelder:**
  - Projektname
  - DIDOK Betriebspunkt
  - Projektleiter (SBB AG)
  - Prüfer (Achermann & Co. AG)
- **Features:**
  - Case-insensitive Suche
  - Ergebnis-Zähler ("X von Y Projekten gefunden")
  - "Zurücksetzen"-Button (erscheint nur bei aktiver Suche)
  - Escape-Taste zum Zurücksetzen
  - Automatischer Fokus auf Suchfeld beim Laden

### 2.2 WH-Anlagen-Konfiguration

Die Anwendung bietet einen dedizierten Bereich für die Konfiguration von Weichenheizungsanlagen mit Energie-Typ-spezifischer Darstellung.

#### EWH-Konfiguration
- Tabellenbasierte Konfigurationsstruktur
- Spalten für Weichenheizkabinen (WHK):
  - **WHK Nr.:** Nummerierung der Weichenheizkabinen
  - **Abgänge:** Anzahl der Heizabgänge
  - **Temperatursonden:** Anzahl der Temperatursensoren
  - **Antriebsheizung:** Vorhandensein/Anzahl von Antriebsheizungen
  - **Meteostation:** Information zur Meteostation
- Visuell hervorgehobener Bereich (rötlicher Rahmen)
- Platzhalter für zukünftige Dateneingabe

#### GWH-Konfiguration
- Separater Konfigurationsbereich (orangener Rahmen)
- Vorbereitet für GWH-spezifische Konfigurationen
- Platzhalter-Text für zukünftige Implementierung

#### Energie-Typ-Unterscheidung
- Automatische Erkennung des Projekt-Energie-Typs
- Dynamische Anzeige der entsprechenden Konfiguration
- Farbcodierung:
  - EWH: Rot/Rosa-Töne
  - GWH: Orange/Gelb-Töne

### 2.3 Abnahmetest-Bereich

Die Anwendung bietet einen Platzhalter-Bereich für zukünftige Abnahmetest-Funktionalitäten.

#### Projektspezifische Abnahmetests
- Jedes Projekt hat einen eigenen Abnahmetest-Bereich
- Anzeige der Projektinformationen
- Vorbereitet für:
  - Test-Konfiguration
  - Test-Durchführung
  - Test-Ergebnisse
  - Test-Protokoll-Generierung

### 2.4 Dashboard

Das Dashboard bietet eine Übersicht über alle wichtigen Kennzahlen:

#### Statistiken
- **Projekte gesamt:** Gesamtanzahl aller Projekte
- **EWH Projekte:** Anzahl der elektrischen Weichenheizungsprojekte
- **GWH Projekte:** Anzahl der gasbasierten Weichenheizungsprojekte
- **Tests gesamt:** Gesamtanzahl aller erfassten Tests

#### Schnellzugriff
- Direkte Links zu häufig verwendeten Funktionen:
  - Projekte verwalten
  - Neues Projekt anlegen
  - Neuer Test

#### Neueste Projekte
- Anzeige der 5 neuesten Projekte
- Tabellenform mit Energie-Typ, Projektname, DIDOK, Erstellungsdatum

#### Neueste Tests
- Anzeige der 5 neuesten Tests (falls vorhanden)

### 2.5 Test-Verwaltung

Die Anwendung unterstützt die Erfassung von Test-Ergebnissen.

#### Test-Erfassung
- Erfassung von Test-Metadaten:
  - Test-Name
  - Hardware-ID
  - Software-Version
  - Test-Ergebnis (Pass/Fail/Pending)
  - Tester-Name
  - Notizen
- Optionale Zuordnung zu einem Projekt
- Automatische Zeitstempelung

#### Test-Übersicht
- Tabellarische Darstellung aller Tests
- Farbcodierung der Ergebnisse:
  - Pass: Grün
  - Fail: Rot
  - Pending: Gelb

### 2.6 Export-System (3-Stufen-Workflow)

Die Anwendung verfügt über ein umfassendes Export-System für strukturierte Projekt-Exporte als PDF oder Excel.

#### Stufe 1: Export-Übersicht (`/export`)

**Funktionen:**
- Übersicht aller Projekte mit Export-Optionen
- **Live-Suche:** Echtzeit-Filterung nach Projektname (clientseitig)
- Kompakte Darstellung mit Energie-Badge, Projektname, DIDOK
- "Exportieren"-Button pro Projekt führt zur Konfigurationsseite

**Darstellung:**
- Tabellarische Übersicht mit 4 Spalten:
  1. Energie (Badge: EWH/GWH)
  2. Projektname
  3. DIDOK Betriebspunkt
  4. Exportieren-Button
- Live-Suche mit Ergebnis-Zähler
- Responsive Design mit Dark Mode Unterstützung

#### Stufe 2: Export-Konfiguration (`/export/projekt/<id>`)

**Flexible Sektion-Auswahl:**
Die Benutzer können individuell wählen, welche Sektionen exportiert werden sollen:

**Allgemeine Sektionen:**
- ☐ **Deckblatt** (optional)
  - Projektinformationen, Prüfer, Datum
- ☐ **WH-Anlage** (optional)
  - Allgemeine Anlage-Tests

**Weichenheizkabinen (WHK):**
- ☐ Einzelne WHKs individuell auswählbar
- Anzeige pro WHK:
  - WHK-Nummer
  - Anzahl Abgänge
  - Anzahl Temperatursonden
  - Antriebsheizung (falls vorhanden)
  - Meteostation (falls zugeordnet)

**Meteostationen:**
- ☐ Einzelne Meteostationen individuell auswählbar
- Gruppierung nach Meteostation-Name
- Anzeige der zugeordneten WHK-Nummern
- WHK-Anzahl pro Meteostation

**Steuerungselemente:**
- **"Alle auswählen"** - Wählt alle Sektionen aus
- **"Alle abwählen"** - Deaktiviert alle Sektionen
- **Validierung:** Export nur möglich wenn mindestens 1 Sektion ausgewählt

**Format-Auswahl:**
- ☐ **PDF-Export:** Professionelles Dokument für Archivierung und Druck
- ☐ **Excel-Export:** Tabellarische Darstellung für Weiterverarbeitung

**Intelligente Dateinamen-Generierung:**
- Basierend auf ausgewählten Sektionen
- Format: `Abnahmetest_{Projektname}_{Sektionen}_{Datum}.{pdf|xlsx}`
- Beispiele:
  - `Abnahmetest_Projekt_XY_Komplett_2025-01-12.pdf`
  - `Abnahmetest_Projekt_XY_Deckblatt_WHK1_WHK2_2025-01-12.xlsx`
  - `Abnahmetest_Projekt_XY_Meteo_Alpha_2025-01-12.pdf`

#### Stufe 3: Export-Generierung (`/export/generate` POST)

**PDF-Export (WeasyPrint 66.0):**
- Bedingte Sektion-Filterung im Template
- Professionelles Layout mit Firmen-Logos (SBB AG, Achermann & Co. AG)
- Unterstützung für komplexe Tabellen und Formatierung
- Automatischer Download mit Content-Disposition Header
- **Voraussetzung:** GTK3-Runtime auf Windows erforderlich

**Excel-Export (openpyxl 3.1.2):**
- Separate Sheets für jede Sektion:
  - Sheet "Deckblatt" (falls ausgewählt)
  - Sheet "WH-Anlage" (falls ausgewählt)
  - Sheet "WHK {Nummer}" (für jede ausgewählte WHK)
  - Sheet "Meteostation {Name}" (für jede ausgewählte Meteostation)
- Bedingte Sheet-Erstellung basierend auf Auswahl
- Formatierung und Styling (Fettdruck für Header, Border, Alignment)
- **Vorteil:** Funktioniert ohne zusätzliche Dependencies

**Fehlerbehandlung:**
- Validierung der Sektion-Auswahl
- 404-Fehler bei nicht existierenden Projekten
- Graceful Degradation bei fehlenden Daten
- Debug-Logging für Troubleshooting

**Navigation:**
- Breadcrumb-Navigation auf allen Export-Seiten
- "Zurück zur Übersicht"-Button
- Integration in Hauptmenü unter "Export"

---

## 3. Datenmodell

### 3.1 Datenbank-Schema

#### Tabelle: projects
Zentrale Tabelle für Weichenheizungsprojekte

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INT | Primärschlüssel, Auto-Increment |
| energie | VARCHAR(10) | Energie-Typ: EWH oder GWH (NOT NULL) |
| projektname | VARCHAR(200) | Bezeichnung des Projekts (NOT NULL) |
| didok_betriebspunkt | VARCHAR(100) | DIDOK-Nummer des Betriebspunkts |
| baumappenversion | DATE | Datum der Planungsversion |
| projektleiter_sbb | VARCHAR(150) | Name des SBB-Projektleiters |
| pruefer_achermann | VARCHAR(150) | Name des Prüfers (Achermann) |
| pruefdatum | DATE | Datum der Prüfung |
| bemerkung | TEXT | Freitext-Bemerkungen |
| erstellt_am | DATETIME | Erstellungszeitpunkt (automatisch) |
| geaendert_am | DATETIME | Letzte Änderung (automatisch) |

**Indizes:**
- Primärschlüssel auf `id`

**Charakteristiken:**
- Engine: InnoDB
- Charset: utf8mb4
- Collation: utf8mb4_unicode_ci

#### Tabelle: test_results
Tabelle für Test-Ergebnisse

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INT | Primärschlüssel, Auto-Increment |
| test_name | VARCHAR(200) | Bezeichnung des Tests (NOT NULL) |
| hardware_id | VARCHAR(100) | Hardware-Identifikation |
| software_version | VARCHAR(50) | Software-Version |
| result | VARCHAR(20) | Ergebnis: Pass, Fail, Pending |
| tester_name | VARCHAR(100) | Name des Testers |
| notes | TEXT | Zusätzliche Notizen |
| test_date | DATETIME | Datum/Zeit des Tests (automatisch) |
| project_id | INT | Fremdschlüssel zu projects (NULL erlaubt) |

**Relationen:**
- Foreign Key: `project_id` → `projects.id` (ON DELETE SET NULL)

### 3.2 Datenbank-Migrationen

Die Anwendung beinhaltet Migrations-Skripte:

#### migrate_weichenheizung.py
Vollständige Umstellung der Projektstruktur auf Weichenheizungs-spezifische Felder:
1. Löscht Foreign Key Constraint von test_results
2. Löscht alte projects-Tabelle
3. Erstellt neue projects-Tabelle mit WH-Struktur
4. Fügt Foreign Key Constraint wieder hinzu
5. Fügt 3 Beispiel-Projekte ein

---

## 4. Benutzeroberfläche

### 4.1 Design-Prinzipien

- **Responsive Design:** Optimiert für Desktop und Mobile
- **Konsistenz:** Einheitliches Farbschema und Layout
- **Benutzerfreundlichkeit:** Intuitive Navigation und klare Struktur
- **Barrierefreiheit:** Ausreichende Kontraste und lesbare Schriften

### 4.2 Farbschema

#### Hauptfarben
- **Header/Navigation:** #2c3e50 (Dunkles Blaugrau)
- **Primär-Aktionen:** #1abc9c (Türkis/Grün)
- **Sekundär-Aktionen:** #95a5a6 (Grau)

#### Energie-Typ-Farbcodierung
- **EWH (Elektrisch):**
  - Badge: #f8d7da (Helles Rosa-Rot)
  - Text: #721c24 (Dunkles Rot)
  - Konfigurationsbereich: Rötlicher Rahmen
- **GWH (Gas):**
  - Badge: #fff3cd (Helles Gelb)
  - Text: #856404 (Dunkles Orange)
  - Konfigurationsbereich: Orangener Rahmen

#### Aktions-Links
- **Bearbeiten:** #1abc9c (Grün)
- **WH-Anlage:** #8e44ad (Lila)
- **Abnahmetest:** #2980b9 (Blau)
- **Löschen:** #c0392b (Rot)

#### Status-Farben
- **Erfolg:** #d4edda (Hellgrün)
- **Fehler:** #f8d7da (Hellrot)
- **Warnung:** #fff3cd (Hellgelb)

#### Dark Mode Farben (CSS-Variablen)
- **Primär-Akzent:** `--accent-primary: #34d399` (Grün)
- **Blau-Akzent:** `--accent-blue: #60a5fa` (Blau)
- **Hintergründe:**
  - `--bg-primary: #1a202c` (Dunkel)
  - `--bg-secondary: #2d3748` (Mittel)
  - `--bg-tertiary: #374151` (Hell)
- **Text:**
  - `--text-primary: #f7fafc` (Hell)
  - `--text-secondary: #cbd5e0` (Gedämpft)
  - `--text-tertiary: #a0aec0` (Sehr gedämpft)
  - `--text-inverse: #1a202c` (Dunkel auf hellem Hintergrund)
- **Buttons:**
  - `--btn-primary-bg: #34d399` (Grün)
  - `--btn-primary-hover: #10b981` (Dunkleres Grün)
  - `--btn-secondary-bg: #4b5563` (Grau)
  - `--btn-secondary-hover: #374151` (Dunkleres Grau)
- **Borders & Shadows:**
  - `--border-color: #4a5568` (Grau)
  - `--shadow-color: rgba(0, 0, 0, 0.3)` (Schatten)

#### Export-Button-Farben
- **"Alle auswählen":** #3b82f6 (Primär-Blau)
- **"Alle abwählen":** #6b7280 (Sekundär-Grau)
- **"Zurück zur Übersicht":** #6b7280 (Sekundär-Grau)
- **"Exportieren":** #60a5fa (Akzent-Blau)
- **Hover-Effekte:** translateY(-1px bis -2px) + Box-Shadow

### 4.3 Navigation

Die Anwendung verfügt über eine persistente Hauptnavigation:
- **Dashboard:** Übersicht und Statistiken
- **Projekte:** Projektverwaltung
- **Export:** Export-System mit 3-Stufen-Workflow
- **Test-Uebersicht:** Alle Test-Ergebnisse
- **Neuer Test:** Test-Erfassung

### 4.4 Responsive Verhalten

#### Desktop (>768px)
- Volle Tabellenbreite
- Horizontale Navigation
- Grid-Layouts für Dashboard-Statistiken

#### Mobile (<768px)
- Vertikale Navigation
- Scrollbare Tabellen
- Einspaltiges Layout
- Vollbreite Buttons

---

## 5. Sicherheit und Validierung

### 5.1 Datenbank-Sicherheit

- **Parametrisierte Queries:** SQLAlchemy ORM verhindert SQL-Injection
- **Foreign Key Constraints:** Sicherstellung der Datenintegrität
- **Cascade Rules:** Definiertes Verhalten bei Löschoperationen (SET NULL)

### 5.2 Eingabevalidierung

- **Pflichtfelder:** Server- und clientseitige Validierung
- **Datums-Validierung:** HTML5-Date-Input mit Format-Prüfung
- **Längen-Begrenzungen:** Maxlength-Attribute in Formularen
- **Typen-Sicherheit:** Energie-Typ-Dropdown verhindert ungültige Werte

### 5.3 Benutzer-Feedback

- **Flash-Messages:** Kategorisiert nach success, error, warning
- **Bestätigungsdialoge:** JavaScript-Bestätigung vor kritischen Aktionen
- **Fehlerbehandlung:** Graceful Degradation bei fehlenden Daten

---

## 6. Datenbankmigrationen

### 6.1 Initiale Migration (migrate_database.py)
- Hinzufügen der project_id-Spalte zu test_results
- Erstellung des Foreign Key Constraints

### 6.2 Weichenheizungs-Migration (migrate_weichenheizung.py)
- Komplette Umstrukturierung der projects-Tabelle
- Von generischen Projektfeldern zu WH-spezifischen Feldern
- Einfügen von Beispiel-Daten:
  - Weichenheizung Bahnhof Zürich HB (EWH)
  - Weichenheizung Bern (GWH)
  - Weichenheizung Luzern (EWH)

---

## 7. Konfiguration

### 7.1 Datenbank-Konfiguration (config.py)

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database/whs.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### 7.2 Abhängigkeiten (requirements.txt)

- Flask==3.0.0
- Flask-SQLAlchemy==3.1.1
- SQLAlchemy==2.0.44
- WeasyPrint==66.0
- openpyxl==3.1.2
- waitress==2.1.2

---

## 8. Deployment

### 8.1 Entwicklungsumgebung

1. **Virtual Environment erstellen:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Datenbank initialisieren:**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Datenbank erstellt!')"
   ```

4. **Anwendung starten:**
   ```bash
   python app.py
   ```

5. **Zugriff:** http://127.0.0.1:5000

### 8.2 Produktionsumgebung

**Hinweis:** Die aktuelle Konfiguration ist nur für Entwicklung geeignet.

Für Produktivbetrieb erforderlich:
- WSGI-Server (z.B. Gunicorn, uWSGI)
- Reverse Proxy (z.B. Nginx, Apache)
- Sichere SECRET_KEY
- Umgebungsvariablen für Datenbank-Zugangsdaten
- SSL/TLS-Verschlüsselung
- Logging und Monitoring
- Backup-Strategie

---

## 9. Zukünftige Erweiterungen

### 9.1 Geplante Features

#### WH-Anlagen-Konfiguration
- [ ] Dynamisches Hinzufügen von WHK-Einträgen
- [ ] Bearbeitung bestehender WHK-Konfigurationen
- [ ] Löschen von WHK-Einträgen
- [ ] Persistierung in Datenbank
- [ ] GWH-spezifische Konfigurationsfelder

#### Abnahmetest-Funktionalität
- [ ] Test-Konfiguration pro Projekt
- [ ] Test-Durchführungs-Assistent
- [ ] Automatische Protokoll-Generierung
- [ ] PDF-Export von Test-Protokollen
- [ ] Excel-Export von Test-Ergebnissen

#### Benutzer-Verwaltung
- [ ] Login/Logout-Funktionalität
- [ ] Rollen und Berechtigungen (Admin, Prüfer, Viewer)
- [ ] Audit-Log für Änderungen
- [ ] Multi-Mandanten-Fähigkeit

#### Erweiterte Features
- [ ] Dashboard-Diagramme und Visualisierungen
- [ ] Filter- und Sortieroptionen in Tabellen
- [ ] Bulk-Operationen (Mehrfach-Bearbeitung)
- [ ] Import/Export von Projekten
- [ ] API-Schnittstelle (REST/GraphQL)
- [ ] Benachrichtigungs-System

---

## 10. Technische Dokumentation

### 10.1 Verzeichnisstruktur

```
C:\inetpub\whs_app\
├── venv/                          # Virtual Environment
├── database/                      # SQLite Datenbank-Verzeichnis
│   └── whs.db                     # Haupt-Datenbank
├── docs/                          # Technische Dokumentation
│   └── EXPORT_SYSTEM.md           # Export-System-Dokumentation
├── static/
│   ├── css/
│   │   └── style.css              # Haupt-Stylesheet
│   └── js/
│       ├── abnahmetest.js         # Abnahmetest-Logik
│       └── konfiguration.js       # WHK-Konfigurations-Logik
├── assets/                        # Assets (Logos, Icons)
│   ├── sbb06.gif                  # SBB Logo
│   ├── Logo Achermann black.svg   # Achermann Logo
│   ├── richtig.svg                # ✓ Icon
│   ├── falsch.svg                 # ✗ Icon
│   └── nicht_testbar.svg          # ⊘ Icon
├── templates/
│   ├── base.html                  # Basis-Template
│   ├── index.html                 # Dashboard
│   ├── projekte.html              # Projektübersicht
│   ├── projekt_form.html          # Projekt-Formular (Neu/Bearbeiten)
│   ├── konfiguration.html         # WH-Anlagen-Konfiguration
│   ├── abnahmetest.html           # Abnahmetest-Durchführung
│   ├── testfragen_verwaltung.html # Testfragen-Verwaltung
│   ├── export.html                # Export-Übersicht (Stufe 1)
│   ├── export_config.html         # Export-Konfiguration (Stufe 2)
│   ├── pdf_abnahmetest.html       # PDF-Template (Stufe 3)
│   ├── tests.html                 # Test-Übersicht
│   └── test_form.html             # Test-Formular
├── scripts/                       # Utility-Scripts
│   ├── import_json_project.py     # JSON-Projekt-Import
│   ├── export_database.py         # Datenbank-Export
│   └── generate_test_data.py      # Testdaten generieren
├── app.py                         # Haupt-Anwendung (Flask-Server)
├── models.py                      # SQLAlchemy Datenbankmodelle
├── config.py                      # Production-Konfiguration
├── config_dev.py                  # Development-Konfiguration
├── run_dev.py                     # Development-Server-Script
├── run_production.py              # Production-Server-Script
├── requirements.txt               # Python-Abhängigkeiten
├── README.md                      # Übersicht und Installation
├── README_DEV.md                  # Development-Setup und Befehle
├── CHANGELOG.md                   # Versionshistorie und Änderungen
└── SOFTWAREBESCHREIBUNG.md        # Diese Datei
```

### 10.2 Routen-Übersicht

| Route | Methoden | Beschreibung |
|-------|----------|--------------|
| / | GET | Dashboard mit Statistiken |
| /projekte | GET | Projektübersicht mit Live-Suche |
| /projekt/neu | GET, POST | Neues Projekt anlegen |
| /projekt/bearbeiten/<id> | GET, POST | Projekt bearbeiten |
| /projekt/loeschen/<id> | GET | Projekt löschen |
| /projekt/konfiguration/<id> | GET | WH-Anlagen-Konfiguration |
| /projekt/abnahmetest/<id> | GET | Abnahmetest-Bereich |
| /export | GET | Export-Übersicht (Stufe 1) |
| /export/projekt/<id> | GET | Export-Konfiguration (Stufe 2) |
| /export/generate | POST | Export-Generierung PDF/Excel (Stufe 3) |
| /tests | GET | Test-Übersicht |
| /new_test | GET, POST | Neuer Test |

### 10.3 CSS-Klassen-Übersicht

#### Layout
- `.container` - Haupt-Container mit maximaler Breite
- `.page-header` - Kopfzeile mit Flexbox-Layout
- `.form-actions` - Button-Container

#### Navigation
- `header` - Hauptheader
- `nav` - Navigationsleiste
- `footer` - Footer-Bereich

#### Formulare
- `.form-group` - Formular-Gruppe
- `.btn-primary` - Primär-Button (Grün)
- `.btn-secondary` - Sekundär-Button (Grau)

#### Tabellen
- `table` - Standard-Tabelle
- `.config-table` - Konfigurationstabelle
- `.no-data-row` - Platzhalterzeile

#### Badges und Status
- `.energie-badge` - Basis-Klasse für Energie-Badges
- `.energie-ewh` - EWH-Badge (Rot)
- `.energie-gwh` - GWH-Badge (Gelb)
- `.result-pass` - Test bestanden (Grün)
- `.result-fail` - Test fehlgeschlagen (Rot)
- `.result-pending` - Test ausstehend (Gelb)

#### Aktions-Links
- `.action-link` - Standard-Aktion (Grün)
- `.config-link` - Konfiguration (Lila)
- `.test-link` - Abnahmetest (Blau)
- `.delete-link` - Löschen (Rot)

#### Bereiche
- `.ewh-config-area` - EWH-Konfigurationsbereich (Rot)
- `.gwh-config-area` - GWH-Konfigurationsbereich (Orange)
- `.project-info-box` - Projektinformations-Box
- `.config-section` - Konfigurations-Sektion

#### Alerts
- `.alert` - Basis-Alert
- `.alert-success` - Erfolg (Grün)
- `.alert-error` - Fehler (Rot)
- `.alert-warning` - Warnung (Gelb)

#### Export-System CSS-Klassen
- `.export-config-section` - Export-Konfigurationsbereich
- `.checkbox-list` - Liste von Checkboxen
- `.checkbox-group` - Checkbox-Gruppe mit Überschrift
- `.checkbox-item` - Einzelne Checkbox mit Label
- `.checkbox-label` - Label-Text für Checkbox
- `.radio-list` - Liste von Radio-Buttons
- `.radio-item` - Einzelner Radio-Button mit Label
- `.radio-label` - Label-Text für Radio-Button
- `.btn-select-all` - "Alle auswählen"-Button (Blau)
- `.btn-deselect-all` - "Alle abwählen"-Button (Grau)
- `.btn-config` - "Exportieren"-Button (Blau)
- `.btn-export-large` - Großer Export-Button
- `.search-container` - Suchbereich-Container
- `.search-form` - Suchformular
- `.search-input` - Sucheingabefeld
- `.search-info` - Such-Ergebnis-Anzeige
- `.project-table` - Projekt-Tabelle
- `.didok-badge` - DIDOK-Badge

#### JavaScript-Komponenten
- **Live-Suche:** Clientseitige Filterung mit `input` Event-Listener
- **Checkbox-Validierung:** Form-Validierung vor Submit
- **"Alle auswählen/abwählen":** Checkbox-Massensteuerung
- **Escape-Taste:** Suche zurücksetzen

---

## 11. Kontakt und Support

### Entwickler
Diese Anwendung wurde entwickelt von Claude (Anthropic) basierend auf detaillierten Anforderungen.

### Repository
Lokales Projekt-Verzeichnis: `C:\Webapp\Abnahmetest`

### Version
Aktuelle Version: 1.1 (Stand: Januar 2025)

---

## 12. Changelog

### Version 1.1 (Januar 2025)

#### Hauptfeatures
- ✅ **Export-System (3-Stufen-Workflow):**
  - Export-Übersichtsseite (`/export`) mit Live-Suche
  - Export-Konfigurationsseite (`/export/projekt/<id>`) mit flexibler Sektion-Auswahl
  - PDF-Export (WeasyPrint 66.0) und Excel-Export (openpyxl 3.1.2)
  - Intelligente Dateinamen-Generierung basierend auf Auswahl
  - Bedingte Sektion-Filterung (Deckblatt, WH-Anlage, WHKs, Meteostationen)

#### UI-Verbesserungen
- ✅ **Live-Suche** auf Projektübersicht (clientseitig)
- ✅ **Live-Suche** auf Export-Übersicht (clientseitig)
- ✅ **Dark Mode Optimierungen:**
  - Export-Seiten vollständig Dark Mode kompatibel
  - Button-Kontraste verbessert
  - CSS-Variablen für konsistente Farbgebung
- ✅ **Button-Styling:**
  - "Alle auswählen" (Blau #3b82f6)
  - "Alle abwählen" (Grau #6b7280)
  - "Zurück zur Übersicht" (Grau #6b7280)
  - Hover-Effekte mit translateY + Box-Shadow
- ✅ **Checkbox & Radio-Buttons:**
  - Grüne Akzentfarbe (`accent-color: var(--accent-primary)`)
  - Hover-Effekte mit Border-Color-Wechsel
  - Slide-Animation beim Hover

#### Terminologie & Struktur
- ✅ "Weichenheizungskästen" → "Weichenheizkabinen" (WHK)
- ✅ Export-Tabelle: Spalte "Erstellt am" entfernt (Fokus auf Export-relevante Infos)
- ✅ Abnahmetest-Seite: Export-Buttons entfernt (zugunsten zentralem Export-System)
- ✅ Projektübersicht: Formular-basierte Suche entfernt (ersetzt durch Live-Suche)

#### Backend-Optimierungen
- ✅ Route `/export` - Export-Übersicht
- ✅ Route `/export/projekt/<id>` - Export-Konfiguration
- ✅ Route `/export/generate` - Export-Generierung (POST)
- ✅ Clientseitige Filterung reduziert Server-Last
- ✅ Template-Caching optimiert
- ✅ Bedingte Datenbank-Abfragen (nur benötigte Sektionen)

#### Dokumentation
- ✅ CHANGELOG.md erstellt (Keep a Changelog Format)
- ✅ docs/EXPORT_SYSTEM.md erstellt (Technische Dokumentation)
- ✅ README.md aktualisiert (Export-System, WeasyPrint 66.0)
- ✅ SOFTWAREBESCHREIBUNG.md erweitert (Komplette Export-System-Dokumentation)

#### Technische Details
- ✅ WeasyPrint 60.1 → 66.0
- ✅ JavaScript ES6+ für Live-Suche und Formular-Validierung
- ✅ DOM-Manipulation für dynamisches UI
- ✅ Template-Inheritance mit bedingten Blöcken
- ✅ CSS-Grid und Flexbox für responsives Layout

---

### Version 1.0.0 (Oktober 2025)
- ✅ Initiale Implementierung der Projektverwaltung
- ✅ Dashboard mit Statistiken
- ✅ Projekt-CRUD-Operationen (Create, Read, Update, Delete)
- ✅ Suchfunktion für Projekte
- ✅ Energie-Typ-spezifische Badges und Bereiche
- ✅ WH-Anlagen-Konfigurationsseite mit EWH/GWH-Unterscheidung
- ✅ Abnahmetest-Platzhalter
- ✅ Test-Verwaltung
- ✅ Responsive Design
- ✅ Datenbank-Migrationen
- ✅ Vollständige CSS-Implementierung

---

**Erstellt:** 30. Oktober 2025
**Letzte Aktualisierung:** 12. Januar 2025
**Dokumentations-Version:** 1.1
