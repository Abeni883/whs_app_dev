# CLAUDE.md — SBB Weichenheizung Abnahmetest-App (DEV)

## Projektübersicht

**Name:** SBB Weichenheizung Abnahmetest-App — Developer-Instanz  
**Zweck:** Verwaltung und Durchführung von Abnahmetests für Weichenheizungssysteme (EWH/GWH) der SBB  
**Pfad:** `C:\inetpub\whs_app_dev`  
**Port:** `5002` (Produktion läuft auf Port 5000)  
**GitHub:** `github.com/Abeni883/sbb-weichenheizung-dev`  
**Produktion:** `C:\inetpub\whs_app` (Port 5000, separates Repo)

---

## Tech-Stack

| Komponente | Technologie |
|---|---|
| Backend | Python 3.11+, Flask 3.0.0 |
| Datenbank | SQLite 3 (`whs_dev.db`), SQLAlchemy |
| Auth | Flask-Login, Flask-Bcrypt |
| PDF-Export | xhtml2pdf (kein WeasyPrint, kein GTK) |
| Frontend | HTML5, CSS3, JavaScript ES6+ |
| Server (Dev) | Flask built-in (debug=True) |
| Server (Prod) | Waitress |

---

## Architektur — Blueprint-Struktur

Die App ist in 9 Flask Blueprints aufgeteilt (app.py ~628 Zeilen):

```
blueprints/
├── auth.py           # Login, Logout, Registrierung
├── api.py            # REST-Endpunkte, Auto-Save, AJAX
├── zeiterfassung.py  # Zeiterfassung pro Projekt
├── testfragen.py     # Testfragen-Verwaltung
├── projekte.py       # Projektverwaltung (CRUD)
├── konfiguration.py  # WHK/ZSK/HGLS-Konfiguration
├── export.py         # PDF/Excel-Export
├── ewh.py            # EWH-Abnahmetest-Workflow
└── gwh.py            # GWH-Abnahmetest-Workflow
```

---

## Datenmodell (Übersicht)

```
projects
  └── whk_configs (EWH)
        └── test_questions → abnahme_test_results
  └── zsk_configs (GWH)
  └── hgls_configs (GWH)
  └── gwh_meteostation
  └── project_time_logs

users (Authentifizierung)
```

**Komponententypen EWH:** Anlage, WHK, Abgang, Temperatursonde, Antriebsheizung, Meteostation  
**Komponententypen GWH:** Anlage, HGLS, ZSK, Teile, Temperatursonde, Meteostation

---

## Dev-Umgebung starten

```powershell
# Option 1: via start_dev.bat
C:\inetpub\whs_app_dev\start_dev.bat

# Option 2: manuell
cd C:\inetpub\whs_app_dev
.\venv\Scripts\Activate.ps1
$env:FLASK_PORT = "5002"
$env:FLASK_DEBUG = "1"
python app.py
```

App läuft dann auf: `http://localhost:5002`

---

## Git-Workflow

```powershell
# Vor dem Arbeiten immer zuerst pullen
git pull origin main

# Nach Änderungen
git add .
git commit -m "feat/fix/refactor: Beschreibung der Änderung"
git push origin main
```

**Commit-Konventionen:**
- `feat:` Neue Funktion
- `fix:` Bugfix
- `refactor:` Code-Umstrukturierung ohne neue Funktion
- `style:` CSS/UI-Änderungen
- `docs:` Dokumentation

---

## Wichtige Entwicklungsregeln

### PDF-Export (xhtml2pdf)
- **Kein WeasyPrint** — läuft nicht ohne GTK auf Windows
- xhtml2pdf benötigt **Inline-Styles** statt CSS-Klassen für Tabellen
- Kein `@page` margin-box, kein `position: running()`
- Logos als **PNG** einbinden (kein SVG)
- Immer mit `--break-system-packages` bei pip wenn nötig

### Datenbank
- Dev-DB: `whs_dev.db` (nie die Produktions-DB verwenden!)
- Bei Modell-Änderungen: Migration testen bevor in Prod übernehmen
- Schema-Änderungen immer mit `db.create_all()` oder Flask-Migrate

### Frontend
- Light/Dark Theme muss immer auf **allen Seiten** konsistent sein
- CSS-Variablen für Farben verwenden, keine hardcodierten Hex-Werte
- JavaScript-Utilities in der gemeinsamen JS-Library (nicht duplizieren)

### Blueprints
- Neue Features immer im passenden Blueprint implementieren
- Keine Logik direkt in `app.py` — nur App-Initialisierung dort
- API-Endpunkte gehören in `api.py`

---

## Umgebungsvariablen (.env)

```
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_PORT=5002
SECRET_KEY=dev-secret-key-change-me
DATABASE_URL=sqlite:///whs_dev.db
```

---

## Unterschiede zur Produktion

| | Produktion | Developer |
|---|---|---|
| Pfad | `C:\inetpub\whs_app` | `C:\inetpub\whs_app_dev` |
| Port | 5000 | 5002 |
| Git Repo | `sbb-weichenheizung` | `sbb-weichenheizung-dev` |
| Datenbank | `whs.db` | `whs_dev.db` |
| Debug | False | True |
| Server | Waitress | Flask built-in |

---

## Bekannte Einschränkungen / Offene Punkte

- xhtml2pdf: Header-Logo und Tabellenformatierung in PDFs noch in Arbeit
- GWH-Abnahmetest: Parameter-Prüfung (ZSK/HGLS) noch nicht vollständig implementiert
- Zeiterfassung: API-Endpunkte vorhanden, UI-Integration laufend

### Stücknachweis-Feature (in Entwicklung)
- Formular: Kopfdaten, Normen EN 61439-1, Messungen, FI-Messungen ✅
- Preset-Logik (4 Typen: kabine_16hz/50hz, rahmen_16hz/50hz) ✅
- WHK-Auswahlseite (`/projekt/<id>/stuecknachweis/whk-auswahl`) ✅
- EN 61439 Button in Projektübersicht ✅
- Grund der Prüfung / Schutzmassnahme / Berührungsschutz ✅
- Schutzgrad editierbar unter Berührungsschutz ✅
- Fehlerstrom-Spalte (30mA/300mA) in FI-Messungen ✅
- Messgerät-Felder editierbar (Messungen + FI separat) ✅
- Normen-Tabelle gruppierte Struktur mit rowspan ✅
- PDF-Export Konformitätserklärung ✅
- PDF-Export Stücknachweis → AUSSTEHEND

---

## Kontakt / Verantwortlich

Entwickler: Nicolas  
Auftraggeber: SBB AG  
Letzte Aktualisierung: April 2026
