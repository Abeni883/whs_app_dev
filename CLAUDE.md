# CLAUDE.md — SBB Weichenheizung Abnahmetest-App (DEV)

## Projektübersicht

**Name:** SBB Weichenheizung Abnahmetest-App — Developer-Instanz  
**Zweck:** Verwaltung und Durchführung von Abnahmetests für Weichenheizungssysteme (EWH/GWH) der SBB  
**Pfad:** `C:\inetpub\whs_app_dev`  
**Port:** `5002` (Produktion läuft auf Port 5001)  
**GitHub:** `github.com/Abeni883/sbb-weichenheizung-dev`  
**Produktion:** `C:\inetpub\whs_app_prod_neu` (Port 5001, separates Repo)

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

## Server-Management

**WICHTIG: Niemals `taskkill //F //IM python.exe` verwenden!**  
Das beendet BEIDE Server (Prod + Dev).

| | Prod | Dev |
|---|---|---|
| Port | 5001 | 5002 |
| Pfad | `C:\inetpub\whs_app_prod_neu` | `C:\inetpub\whs_app_dev` |
| Status | Muss IMMER laufen | Nur während Entwicklung |

**Dev-Server neustarten (nur Dev-Prozess beenden):**
```bash
# Port-spezifisch den Dev-Prozess finden und beenden
for pid in $(netstat -ano | grep ":5002 " | grep "ABH" | awk '{print $5}' | sort -u); do
  taskkill //F //PID $pid 2>/dev/null
done
# Neu starten
cd C:\inetpub\whs_app_dev && ./venv/Scripts/python.exe app.py > /dev/null 2>&1 &
```

**Prod-Server starten (falls nötig):**
```bash
cd C:\inetpub\whs_app_prod_neu && FLASK_PORT=5001 ./venv/Scripts/python.exe app.py > /dev/null 2>&1 &
```

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

### PDF-Export (xhtml2pdf) — Wichtige Regeln

**Grundregeln:**
- **Kein WeasyPrint** — läuft nicht ohne GTK auf Windows
- Nur **Inline-Styles** (kein externes CSS, kein `<link>`)
- Nur **PNG** für Bilder (kein SVG)
- Logos als **Base64 Data-URLs** einbetten (siehe `get_image_as_base64()` in `export.py`)
- Schrift: Arial oder Helvetica

**Header/Footer:**
- `@page` margin-box (`@bottom-left/right`) funktioniert **NICHT**
- `position: fixed/absolute` funktioniert **NICHT**
- Lösung: `@frame` mit `-pdf-frame-content` verwenden:
```css
@frame footer_frame {
    -pdf-frame-content: footerContent;
    bottom: 0.3cm; left: 1.5cm; right: 1.5cm; height: 2cm;
}
```
```html
<div id="footerContent">...</div>
```

**Vertikale Zentrierung:**
- `vertical-align: middle` wird **komplett ignoriert**
- `padding-top/bottom` wirkt asymmetrisch (nur unten)
- Lösung: Unsichtbare Spacer-Zeilen mit `&nbsp;` + `<br>`:
```html
<span style="font-size:12pt;">&nbsp;</span><br>
Text hier
<span style="font-size:6pt;">&nbsp;</span>
```

**Logo-Grösse:**
- `max-height` wird ignoriert
- Lösung: `height="20"` als HTML-Attribut setzen

**Testen ohne Server-Neustart:**
- Test-PDFs direkt via Python-Script generieren (`pisa.CreatePDF`)
- `taskkill //F //IM python.exe` falls Server-Prozesse hängen

**Bekannte nicht-unterstützte CSS:**
- `position: fixed / absolute`
- `@page` margin-box
- `vertical-align: middle`
- `max-height` bei Bildern
- `@bottom-left / @bottom-right`

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

## HTTPS-Konfiguration (SSL/TLS)

App läuft über HTTPS mit selbstsigniertem Zertifikat. `cert.pem` + `key.pem` liegen im App-Root, sind in `.gitignore`.

**URL:** `https://192.168.1.202:5002`  (**http:// funktioniert nicht** — Server hört nur TLS)

### Zertifikat erzeugen / rezertifizieren
```powershell
cd C:\inetpub\whs_app_dev
venv\Scripts\python.exe scripts\generate_cert.py
```
Zertifikat: CN `192.168.1.202`, SAN `IP:192.168.1.202, DNS:localhost, IP:127.0.0.1`, 3 Jahre gültig.

Das Script liegt original in `C:\inetpub\whs_app_prod_neu\scripts\generate_cert.py` — bei Bedarf in Dev synchronisieren.

### Browser-Warnung beim ersten Aufruf
„Erweitert" → „Weiter zu 192.168.1.202". Danach erscheint die Warnung nicht mehr für diese Adresse.

### Server-Management (WICHTIG)

- **Nie** `taskkill /F /IM python.exe` verwenden — das tötet Prod **und** Dev gleichzeitig.
- Port-spezifisch killen:
  ```cmd
  for /f "tokens=5" %a in ('netstat -ano ^| findstr :5002 ^| findstr LISTENING') do taskkill /F /PID %a
  ```
- Server **immer** aus dem App-Verzeichnis starten (sonst werden `cert.pem`/`key.pem` nicht gefunden → Fallback auf HTTP):
  ```cmd
  cd /d C:\inetpub\whs_app_dev
  start "WHS DEV 5002" cmd /k "venv\Scripts\python.exe app.py"
  ```
- SSL wird automatisch aktiviert, wenn `cert.pem` + `key.pem` im cwd existieren. Fehlen sie, startet die App auf HTTP.

---

## Unterschiede zur Produktion

| | Produktion | Developer |
|---|---|---|
| Pfad | `C:\inetpub\whs_app_prod_neu` | `C:\inetpub\whs_app_dev` |
| Port | 5001 | 5002 |
| Git Repo | `sbb-weichenheizung` | `sbb-weichenheizung-dev` |
| Datenbank | `whs.db` | `whs_dev.db` |
| Debug | False | True |
| Server | Waitress | Flask built-in |

---

## Implementierter Stand — Stücknachweis Feature ✅

### Datenbank (neue Tabellen)
- `stuecknachweis` — Kopfdaten, Normen (16 Checkboxen), Messungen, Grund/Schutz/Berührungsschutz, Schutzgrad, Messgeräte
- `fi_messungen` — Sicherungen, Fehlerstrom (30mA/300mA), ∆I/∆t, Status

### WHKConfig Erweiterungen
- `whk_typ` (Typbezeichnung z.B. WHK_20_LU_01_16)
- `preset_typ` (kabine_16hz/50hz, rahmen_16hz/50hz)

### Neue Routen (blueprints/stuecknachweis.py)
- `GET /projekt/<id>/stuecknachweis/whk-auswahl`
- `GET/POST /projekt/<id>/whk/<id>/stuecknachweis`
- `GET /projekt/<id>/whk/<id>/stuecknachweis/pdf`
- `GET /projekt/<id>/whk/<id>/konformitaet/pdf`

### Neue Templates
- `templates/stuecknachweis/formular.html`
- `templates/stuecknachweis/whk_auswahl.html`
- `templates/stuecknachweis/pdf_stuecknachweis.html` (3 Seiten)
- `templates/stuecknachweis/pdf_konformitaet.html` (1 Seite)

### PDF-Export
- **Stücknachweisprotokoll** — 3 Seiten: Kopfdaten | Normen EN 61439-1 | Messungen + FI + Vorbehalt
- **Konformitätserklärung** — 1 Seite: Firma, Produkt, Norm, CE-Jahr, Unterschrift
- Beide via xhtml2pdf mit `@frame` Header/Footer, Base64-Logo

### UI-Änderungen
- Projektübersicht: EN 61439 Button (blau, eigene `.en61439-link` Klasse)
- Konfiguration: Spalte "Typ" (`whk_typ`), TS/AH gekürzt, Tabelle zentriert
- WHK-Auswahl: Status-Badge (Vorhanden/Nicht erstellt)
- Stücknachweis-Formular: Normen-Tabelle mit rowspan-Gruppierung, Exklusiv-Checkboxen (Grund/Berührungsschutz), editierbare Messgeräte/Schutzgrad

---

## Offene Punkte / Nächste Schritte

- Produktiv-Übernahme (DB-Migrationen beachten!)
- GWH-Abnahmetest: Parameter-Prüfung (ZSK/HGLS) noch nicht vollständig
- Zeiterfassung: API-Endpunkte vorhanden, UI-Integration laufend

---

## Kontakt / Verantwortlich

Entwickler: Nicolas  
Auftraggeber: SBB AG  
Letzte Aktualisierung: April 2026
