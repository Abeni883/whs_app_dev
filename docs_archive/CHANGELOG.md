# Changelog - Abnahmetest Weichenheizung

Alle wichtigen Änderungen und Erweiterungen der Software werden in dieser Datei dokumentiert.

---

## Version 2.0 - Dark Mode & UI Verbesserungen (2025-11-03)

### Neue Features

#### 1. Dark Mode / Light Mode Toggle
**Implementiert:** Vollständiges Theme-Switching System

**Funktionen:**
- Toggle-Button in der Navigation mit 🌙/☀️ Icons
- Automatische Erkennung der System-Präferenz (prefers-color-scheme)
- LocalStorage-Persistierung der Benutzerauswahl
- Flash-Prevention beim Seitenladen (kein Flackern)
- Sanfte Übergänge zwischen Themes (0.3s transitions)
- Vollständige Unterstützung auf allen Seiten

**Technische Details:**
- CSS Custom Properties (CSS-Variablen) für beide Themes
- `[data-theme="dark"]` und `:root` für Theme-Management
- JavaScript für Theme-Switching und Persistierung
- 180+ Zeilen CSS-Variablen für konsistentes Theming

**Dateien:**
- `templates/base.html` (Zeilen 7-15, 26-32, 55-107)
- `static/style.css` (Zeilen 1-280)

---

### UI/UX Verbesserungen

#### 2. Light Mode Komplettüberholung
**Problem:** Ursprüngliches Design hatte zu wenig Kontrast, wirkte unprofessionell

**Neue Farbpalette:**
- Body-Hintergrund: `#f5f7fa` (soft blue-gray statt white)
- Container: `#ffffff` (white cards on gray background)
- Text Primary: `#1a202c` (soft dark gray statt harsh black)
- Text Secondary: `#4a5568` (medium gray)
- Borders: `#e2e8f0` (visible but subtle)
- Akzent-Farben: Professionelle Grün/Blau/Rot-Töne

**Header-Design:**
- Von dunklem zu hellem Header gewechselt
- Weißer Hintergrund mit subtiler Schattierung
- Klare Trennung durch Border-Bottom

**Action-Links:**
- Verbesserte Kontraste für Bearbeiten/Löschen/Test/Konfiguration
- Hover-Effekte mit Transform und Shadow
- Spezifische Text-Farben für jeden Link-Typ

**Dateien:**
- `static/style.css` (Zeilen 1-140: :root Variablen)
- `static/style.css` (Zeilen 248-290: Header)
- `static/style.css` (Zeilen 581-662: Action Links)

#### 3. Dark Mode Optimierung
**Problem:** Ursprüngliche Dark Mode Farben waren zu dunkel, schlechter Kontrast

**Kritische Fixes:**
- Text-Primary: `#fafafa` (war `#4a4a4a` - fast unsichtbar!)
- Header-Text: `#ffffff` (war `var(--border-light)` = dunkelgrau)
- Navigation-Links: `#e5e7eb` (war zu dunkel)
- Alle Akzent-Farben aufgehellt für bessere Sichtbarkeit

**Verbesserte Elemente:**
- Tabellenheader: Hellerer Hintergrund `#475569`, weißer Text
- Input-Felder: Dunkelgrau `#374151` mit hellem Text `#f5f5f5`
- Placeholder: `#9ca3af` (gut sichtbar)
- Focus-State: Grüner Glow `#34d399`

**Dateien:**
- `static/style.css` (Zeilen 143-280: [data-theme="dark"] Variablen)
- `static/style.css` (Zeilen 282-393: Dark Mode Selektoren)

#### 4. Abnahmetest-Seite Lesbarkeit
**Problem:** WHK-Labels und Navigation zu blass, schwer lesbar

**Optimierungen:**
- WHK-Labels: `#111827` (sehr dunkel), `font-weight: 700`, größer
- Tabellen-Header: `#1e293b` Hintergrund, weißer Text
- Navigation-Buttons:
  - Inaktiv: `#e5e7eb` mit dunklem Text
  - Aktiv: `#fef3c7` (gold) mit `#92400e` Text und goldenem Border
  - Abgeschlossen: `#10b981` (grün) mit weißem Text
- Test-Fragen: `#111827`, `font-weight: 700`, `1.2rem`

**Dateien:**
- `static/style.css` (Zeilen 1816-1824: WHK Labels)
- `static/style.css` (Zeilen 1826-1878: Navigation Buttons)
- `static/style.css` (Zeilen 1495-1527: Tabellen)

#### 5. Tabellenüberschriften und Suchfeld Dark Mode
**Problem:** Tabellenheader zu dunkel, Suchfeld hatte weißen Hintergrund

**Fixes:**
- Tabellenheader-Hintergrund: `#475569` (aufgehellt)
- Tabellenheader-Text: `#ffffff` (reines Weiß)
- Suchfeld-Hintergrund: `#374151` (dunkel statt weiß)
- Suchfeld-Text: `#f5f5f5` (hell)
- Focus-Border: `#34d399` (grün mit Glow)

**Dateien:**
- `static/style.css` (Zeilen 226-237: Input Variablen)
- `static/style.css` (Zeilen 283-333: Dark Mode Tabellen/Inputs)

#### 6. Konfigurationsseite Dark Mode
**Problem:** Container blieb weiß im Dark Mode, Überschriften falsch gefärbt

**Lösungen:**
- Inline-Styles aus Templates entfernt (hardcoded `color: #2c3e50`)
- CSS mit maximaler Spezifität und !important
- JavaScript-Fallback für sofortige Anwendung
- Alle Container: `#262626` (dunkel)
- Alle Überschriften: `#ffffff` (weiß)
- WHK-Counter: `#9ca3af` (hellgrau)

**Dateien:**
- `templates/konfiguration.html` (Zeilen 6-35: JavaScript Fix)
- `templates/konfiguration.html` (Zeilen 14, 118: Inline-Styles entfernt)
- `static/style.css` (Zeilen 2918-2980: Maximale Spezifität)

---

### Funktionale Änderungen

#### 7. Spaltenüberschrift Umbenennung
**Änderung:** "Bearbeiten" → "Projektinformationen" in Projekt-Tabelle

**Grund:** Klarere Bezeichnung für die Funktion

**Dateien:**
- `templates/projekte.html` (Zeile 34)

#### 8. Baumappenversion Eingabefeld
**Änderung:** Von Kalender-Picker zu manuellem Text-Eingabefeld

**Vorher:** `<input type="date">` mit ISO-Format (YYYY-MM-DD)
**Nachher:** `<input type="text" placeholder="TT.MM.JJJJ">` mit deutschem Format

**Backend-Anpassungen:**
- Parse-Format geändert: `%Y-%m-%d` → `%d.%m.%Y`
- Display-Format geändert: ISO → deutsches Format
- Beide Routes angepasst (neues_projekt, projekt_bearbeiten)

**Dateien:**
- `templates/projekt_form.html` (Zeile 30)
- `app.py` (Zeilen 65, 105)

---

### Technische Details

#### CSS-Architektur
**CSS Custom Properties System:**
- 90+ Variablen für Light Mode (`:root`)
- 90+ Variablen für Dark Mode (`[data-theme="dark"]`)
- Kategorisiert: Hintergründe, Text, Borders, Buttons, Tabellen, Alerts, etc.

**Farbvariablen (Beispiele):**
```css
:root {
  --bg-primary: #f5f7fa;
  --text-primary: #1a202c;
  --accent-primary: #10b981;
}

[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --text-primary: #fafafa;
  --accent-primary: #34d399;
}
```

#### JavaScript Theme-Management
**Features:**
- Flash-Prevention: Theme vor Rendering setzen
- LocalStorage: Benutzer-Präferenz speichern
- System-Erkennung: `window.matchMedia('(prefers-color-scheme: dark)')`
- Icon-Update: 🌙 ↔ ☀️
- Event-Listener für System-Theme-Änderungen

**Code-Struktur:**
```javascript
// Flash Prevention (Inline im <head>)
(function() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
})();

// Theme Toggle (Ende der Seite)
function toggleTheme() {
    const currentTheme = getCurrentTheme();
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateIcon();
}
```

---

### Barrierefreiheit (Accessibility)

#### WCAG-Konformität
**Kontrast-Verhältnisse verbessert:**
- Light Mode: Minimaler Kontrast 4.5:1 (AA-Standard)
- Dark Mode: Optimiert für Augenkomfort bei geringem Umgebungslicht
- Überschriften: Maximaler Kontrast (weiß auf dunkel)

**ARIA-Labels:**
- Theme-Toggle: `aria-label="Theme umschalten"`
- Dynamische Labels: "Zu Dark Mode wechseln" / "Zu Light Mode wechseln"

---

### Performance

#### Optimierungen
- CSS-Transitions nur für Theme-Wechsel (0.3s)
- Keine JavaScript-Berechnungen bei jedem Render
- LocalStorage für instant Theme-Anwendung
- Minimale Repaint-Operationen

#### Browser-Kompatibilität
- CSS Custom Properties: Alle modernen Browser
- `matchMedia`: Alle modernen Browser
- LocalStorage: Universelle Unterstützung
- Fallback für alte Browser: Light Mode

---

### Testing & Quality Assurance

#### Getestete Szenarien
1. Theme-Wechsel auf allen Seiten
2. Browser-Reload mit persistiertem Theme
3. System-Theme-Änderung während App läuft
4. Verschiedene Browser (Chrome, Firefox, Edge, Safari)
5. Mobile Responsive Design
6. Keyboard-Navigation
7. Screen-Reader-Kompatibilität

#### Bekannte Issues
- Keine bekannten Probleme

---

### Datei-Übersicht

#### Geänderte Templates
- `templates/base.html` - Theme-System hinzugefügt
- `templates/projekte.html` - Spaltenüberschrift geändert
- `templates/projekt_form.html` - Datumseingabe geändert
- `templates/konfiguration.html` - Dark Mode Fix + Inline-Styles entfernt

#### Geänderte Styles
- `static/style.css` - Komplett überarbeitet:
  - Zeilen 1-140: Light Mode Variablen (neu)
  - Zeilen 143-280: Dark Mode Variablen (neu)
  - Zeilen 282-393: Dark Mode Selektoren (neu)
  - Zeilen 2918-2980: Konfigurationsseite Fix (neu)
  - Zeilen 2459-2504: Theme-Toggle Button (neu)
  - Diverse Optimierungen bestehender Styles

#### Geänderte Backend-Dateien
- `app.py` - Datums-Parsing für Baumappenversion

---

### Statistiken

**Code-Änderungen:**
- ~200 Zeilen neue CSS-Variablen
- ~150 Zeilen neue CSS-Selektoren
- ~100 Zeilen JavaScript (Theme-System)
- ~50 Zeilen Template-Änderungen
- Gesamt: ~500 Zeilen neuer/geänderter Code

**CSS-Datei:**
- Vorher: ~2500 Zeilen
- Nachher: ~2980 Zeilen
- Zuwachs: ~480 Zeilen

---

### Migration & Deployment

#### Keine Breaking Changes
- Alle Änderungen sind abwärtskompatibel
- Bestehende Daten unverändert
- Keine Datenbank-Migration erforderlich
- Keine API-Änderungen

#### Deployment-Schritte
1. CSS-Datei aktualisieren (`static/style.css`)
2. Templates aktualisieren (`templates/base.html`, `templates/konfiguration.html`, etc.)
3. Server neu starten
4. Browser-Cache der Benutzer leeren (Hard Reload empfohlen)

---

### Zukünftige Verbesserungen (Roadmap)

#### Geplante Features
- [ ] Benutzerdefinierte Farbschemata
- [ ] Automatischer Theme-Wechsel nach Tageszeit
- [ ] High-Contrast-Mode für Barrierefreiheit
- [ ] Theme-Preview vor Anwendung
- [ ] Zusätzliche Theme-Varianten (z.B. Sepia, Blue Light Filter)

#### Performance-Optimierungen
- [ ] CSS-Minifizierung für Production
- [ ] Lazy-Loading für Theme-Assets
- [ ] Service-Worker für Offline-Theme-Support

---

### Credits

**Entwickelt:** 2025-11-03
**Framework:** Flask 3.1.2
**Frontend:** HTML5, CSS3 (Custom Properties), Vanilla JavaScript
**Design-System:** Custom Theme-Management mit CSS Variables

---

## Version 1.x - Basis-Funktionalität

### Core Features
- Projektverwaltung für Weichenheizungen (EWH/GWH)
- WHK-Konfiguration mit Auto-Save
- Abnahmetest-Durchführung mit Testfragen
- Testfragen-Verwaltung
- Dashboard mit Projekt-Übersicht
- Suchfunktion für Projekte
- Bemerkung-Funktionalität für Tests

---

## Technologie-Stack

### Backend
- Python 3.x
- Flask 3.1.2
- SQLAlchemy 2.0.44
- MySQL 8.0 (mit PyMySQL)

### Frontend
- HTML5 (Jinja2 Templates 3.1.6)
- CSS3 (Custom Properties, Flexbox, Grid)
- Vanilla JavaScript (ES6+)
- Font: Segoe UI, Tahoma, Geneva, Verdana, sans-serif

### Database
- MySQL 8.0
- Tabellen: projekte, whk_config, testfragen, test_antworten, etc.

---

## Browser-Support

### Getestet
- ✅ Chrome 100+
- ✅ Firefox 100+
- ✅ Edge 100+
- ✅ Safari 15+

### Mindestanforderungen
- CSS Custom Properties Support
- ES6 JavaScript Support
- LocalStorage Support
- flexbox/grid Support

---

## Lizenz & Copyright

© 2025 Abnahmetest Weichenheizung. Alle Rechte vorbehalten.

---

## Kontakt & Support

Bei Fragen oder Problemen wenden Sie sich bitte an das Entwicklungsteam.
