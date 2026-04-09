# Changelog

Alle wesentlichen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

## [Unreleased]

### Hinzugefügt

#### Abnahmetest-Seite Optimierungen (2025-11-22)
- **Zweizeilige Abgang-Header** für kompaktere Darstellung
  - Abgang-Spalten zeigen "Abg." in erster Zeile und Nummer in zweiter Zeile
  - Spart horizontalen Platz und ermöglicht Darstellung aller 12 Abgänge
  - Implementiert in `templates/abnahmetest.html` (Zeilen 366-372)
  - CSS-Styling in `static/style.css` (Zeilen 2290-2305)

- **Dynamischer Success-Frame Titel**
  - Zeigt spezifischen Testname statt generischem Text
  - Format: "✓ [Testname] - Alle Fragen durchlaufen" (z.B. "✓ Anlage - Alle Fragen durchlaufen")
  - Automatische Testname-Generierung basierend auf currentFilter
  - Implementiert in `showSaveSection()` Funktion (Zeilen 670-683)

#### UI-Verbesserungen (2025-01-20)
- **WHK-Tabelle Überschrift** auf Abnahmetest-Seite
  - "WHK Nr." als Überschrift zur ersten Spalte der WHK-Übersichtstabelle hinzugefügt
  - Verbessert die Lesbarkeit und Struktur der Tabelle
  - Konsistent mit den anderen Spalten-Überschriften

#### Testabschluss-Seite
- **Neue Testabschluss-Seite** (`/testabschluss`) für Post-Test-Einstellungen
  - Menüpunkt "Testabschluss" im Hauptmenü
  - **EWH-Kategorie** (Elektroweichenheizung):
    - Roter Header-Banner mit EWH-Badge
    - 3 nummerierte Checklisten-Punkte mit WH-Leitstand-Einstellungen:
      1. Freigabe deaktivieren ("Freigabe Aus")
      2. LSS-CH Meldung deaktivieren ("Meldung an LSS-CH Aus")
      3. Betriebszentrale Einschaltdauer auf Standardwert setzen
    - Animiertes Zahnrad-Icon (⚙️) beim Titel
    - Grüne Hervorhebungen für wichtige Begriffe
    - Hover-Effekte für bessere Interaktivität
  - **GWH-Kategorie** (Gasweichenheizung):
    - Oranger Header-Banner mit GWH-Badge
    - Platzhalter "Inhalte folgen in Kürze"
  - Vollständig Dark Mode und Light Mode kompatibel
  - Responsive Design für alle Bildschirmgrößen

#### Export-System (Hauptfeature)
- **Neues 3-Stufen-Export-System** für strukturierte Projekt-Exporte
  - Stufe 1: Export-Übersichtsseite (`/export`) mit allen Projekten
  - Stufe 2: Export-Konfigurationsseite (`/export/projekt/<id>`) zur Sektion-Auswahl
  - Stufe 3: Export-Generierung mit PDF oder Excel

- **Export-Übersichtsseite** (`templates/export.html`)
  - Übersicht aller Projekte mit Energie-Badge, Projektname, DIDOK
  - Live-Suche (clientseitig) für schnelles Filtern
  - "Exportieren"-Button pro Projekt führt zur Konfigurationsseite
  - Responsive Dark Mode Design konsistent mit restlicher App

- **Export-Konfigurationsseite** (`templates/export_config.html`)
  - Flexible Auswahl von zu exportierenden Sektionen:
    - Deckblatt (optional)
    - WH-Anlage (optional)
    - Einzelne Weichenheizkabinen (WHKs) - individuell auswählbar
    - Einzelne Meteostationen - individuell auswählbar
  - "Alle auswählen" / "Alle abwählen" Buttons für schnelle Konfiguration
  - Format-Auswahl: PDF oder Excel
  - Validierung: Export nur möglich wenn mindestens 1 Sektion ausgewählt
  - Intelligente Dateinamen-Generierung basierend auf ausgewählten Sektionen

- **Export-Generierung** (`app.py: generate_export()`)
  - PDF-Export mit WeasyPrint 66.0
    - Bedingte Sektion-Filterung im Template
    - Professionelles Layout mit Firmen-Logos
    - Unterstützung für komplexe Tabellen und Formatierung
  - Excel-Export mit openpyxl
    - Separate Sheets für jede Sektion
    - Bedingte Sheet-Erstellung basierend auf Auswahl
    - Formatierung und Styling

- **Navigation**
  - Neuer Menüpunkt "Export" im Hauptmenü (`templates/base.html`)
  - Breadcrumb-Navigation auf Export-Seiten

#### Live-Suche
- **Live-Suche auf Projektübersicht** (`templates/projekte.html`)
  - Echtzeit-Filterung während der Eingabe (clientseitig)
  - Suche in Projektname, DIDOK, Projektleiter
  - Ergebnis-Zähler ("X von Y Projekten gefunden")
  - "Zurücksetzen"-Button (erscheint nur bei aktiver Suche)
  - Escape-Taste zum Zurücksetzen
  - Kein Server-Request nötig - bessere Performance

- **Live-Suche auf Export-Übersicht** (`templates/export.html`)
  - Identischer Mechanismus wie Projektübersicht
  - Konsistente Benutzererfahrung

#### Design-Verbesserungen
- **Dark Mode Optimierungen**
  - Testabschluss-Seite: Vollständig Dark/Light Mode kompatibel mit CSS-Variablen
  - Export-Konfigurationsseite vollständig Dark Mode kompatibel
  - Export-Übersichtsseite Dark Mode angepasst
  - Button-Kontraste verbessert für bessere Lesbarkeit
  - Konsistente Farben und Kontraste über alle Seiten

- **Button-Styling**
  - Konsistente Button-Styles über alle Seiten
  - "Zurück zur Übersicht": Grauer Secondary-Button (#6b7280)
  - "Alle auswählen": Blauer Primary-Button (#3b82f6)
  - "Alle abwählen": Grauer Secondary-Button (#6b7280)
  - "Zurücksetzen" (Suche): Verbesserter Kontrast im Dark Mode
  - Hover-Effekte: translateY-Animation + Box-Shadow

- **Checkboxen & Radio-Buttons**
  - Grüne Akzentfarbe (`accent-color: var(--accent-primary)`)
  - Hover-Effekte mit Border-Color-Wechsel
  - Slide-Animation beim Hover (translateX)

### Geändert

#### Abnahmetest-Seite Optimierungen (2025-11-22)
- **Maximale Komprimierung der Testtabellen**
  - Spaltenbreite reduziert: 70px → 55px (spart ~180px horizontal)
  - Checkbox-Größe optimiert: 22px → 18px
  - Header-Padding: 0.4rem 0.3rem → 0.35rem 0.2rem
  - TD-Padding: 0.4rem 0.25rem → 0.3rem 0.15rem
  - Bemerkung-Button: kleinere Padding (0.2rem 0.4rem) und Font-Size (0.85rem)
  - Ermöglicht vollständige Darstellung aller 12 Abgänge ohne horizontales Scrollen

- **Frame-Integration**
  - question-navigation in test-section integriert (ein Frame statt zwei)
  - Transparenter Hintergrund für question-navigation
  - Border-bottom statt vollständiger Border
  - Reduzierte Margins für kompakteres vertikales Layout
  - .system-group Margins optimiert

- **Success-Frame Optimierungen**
  - Redundanter Text "Sie haben alle Testfragen beantwortet." entfernt
  - Komponenten-spezifische Fragenzählung implementiert
  - Zeigt nur Fragen der aktuellen Komponente (z.B. "10 von 16" statt "17 von 165")
  - Button "Zurück zur Projektübersicht" entfernt (streamlined workflow)
  - "Zurück zum Anfang" Button scrollt zum Seitenanfang statt erste Frage zu laden
  - Smooth Scrolling mit `window.scrollTo({top: 0, behavior: 'smooth'})`

- **Vertikale Kompaktheit**
  - WHK-Tabelle und Testergebnis-Tabellen vertikal komprimiert
  - Optimierte Abstände zwischen Elementen
  - Bessere Übersicht ohne Informationsverlust

#### UI-Verbesserungen (2025-01-20)
- **WHK-Tabelle Header-Styling** auf Abnahmetest-Seite
  - Alle 5 Header-Zellen (WHK Nr., Abgänge, Temperatursonden, Antriebsheizung, Meteostation) verwenden jetzt den gleichen Hintergrund
  - Entfernt spezielle `background`-Eigenschaft für erste Spalte (`.nav-table th:first-child`)
  - Konsistentes Erscheinungsbild in Light Mode und Dark Mode
  - Alle Header-Zellen sind jetzt visuell identisch

- **Test-Information Dark Mode Styling** auf Abnahmetest-Seite
  - Test-Information (z.B. "Testen Sie die Kommunikation zwischen den Systemen") wird jetzt im Dark Mode rot dargestellt
  - Neue CSS-Regel für `.question-content .test-info` im Dark Mode (Farbe: #f87171)
  - Konsistent mit Light Mode Styling für bessere Lesbarkeit

#### Terminologie
- "Weichenheizungskästen (WHK)" → "Weichenheizkabinen (WHK)" in `templates/export_config.html`

#### UI-Strukturänderungen
- **Abnahmetest-Seite** (`templates/abnahmetest.html`)
  - Export-Buttons entfernt (zugunsten zentralem Export-System)
  - Fokus auf Test-Durchführung

- **Export-Übersicht** (`templates/export.html`)
  - Spalte "Erstellt am" entfernt - Fokus auf Export-relevante Infos
  - Tabelle vereinfacht auf 4 Spalten: Energie, Projektname, DIDOK, Exportieren

- **Projektübersicht** (`templates/projekte.html`)
  - "Suchen"-Button entfernt (ersetzt durch Live-Suche)
  - Formular-basierte Suche entfernt
  - Clientseitige JavaScript-Filterung implementiert

#### Backend-Optimierungen
- **Route `/projekte`** (`app.py`)
  - Serverseitige Such-Logik entfernt
  - Alle Projekte werden geladen, Filterung erfolgt clientseitig
  - Reduzierte Server-Last durch weniger HTTP-Requests

- **Export-Routen** (`app.py`)
  - `/export`: Export-Übersicht (GET)
  - `/export/projekt/<int:projekt_id>`: Export-Konfiguration (GET)
  - `/export/generate`: Export-Generierung (POST)
  - Umfangreiche Validierung und Fehlerbehandlung
  - Debug-Logging für Troubleshooting

#### Datenbank
- Testdaten-Generator (`scripts/generate_complete_test_data.py`)
  - Erstellt 24 Testfragen über alle Komponententypen
  - Generiert 837 Testantworten für 8 Projekte (100% Abdeckung)
  - Automatisches Löschen alter Daten vor Neugenerierung

### Technische Details

#### Dependencies
- WeasyPrint 66.0 - PDF-Generierung
- openpyxl 3.1.2 - Excel-Export
- Flask 3.0.0 - Web-Framework
- SQLAlchemy 2.0.44 - ORM

#### Templates
- `templates/testabschluss.html` - Testabschluss-Seite mit EWH/GWH-Kategorien
- `templates/export.html` - Export-Übersicht mit Live-Suche
- `templates/export_config.html` - Export-Konfiguration mit Sektion-Auswahl
- `templates/pdf_abnahmetest.html` - PDF-Template mit bedingter Sektion-Filterung
- `templates/abnahmetest.html` - WHK-Tabelle mit "WHK Nr." Überschrift (Zeile 25)

#### JavaScript-Funktionalität (2025-11-22)
- **Zweizeilige Abgang-Header** (`templates/abnahmetest.html` Zeilen 366-372)
  - Dynamische HTML-Generierung mit `.th-line-1` und `.th-line-2` divs
  - Erkennung von "Abgang XX" Pattern und Aufteilung in zwei Zeilen

- **Dynamischer Success-Frame Titel** (Zeilen 670-683)
  - Testname-Generierung basierend auf `currentFilter.component` und `currentFilter.index`
  - Format-Logik für verschiedene Komponententypen (Anlage, WHK, Abgänge, etc.)
  - DOM-Update mit `getElementById('completion-title')`

- **Komponenten-spezifische Fragenzählung** (Zeilen 684-695)
  - Iteration durch `currentFilteredQuestions` statt alle `testQuestions`
  - Verwendung von `isQuestionComplete()` für akkurate Zählung
  - Separate Anzeige von `answered-count` und `total-count`

- **Smooth Scroll-to-Top** (Zeilen 653-656)
  - `window.scrollTo({top: 0, behavior: 'smooth'})` in `backToStart()` Funktion
  - Ersetzt vorheriges `loadQuestion(0)` Verhalten

#### JavaScript-Funktionalität (Frühere Versionen)
- Live-Suche mit `input`-Event-Listener
- DOM-Manipulation für dynamisches Zeigen/Verstecken von Tabellenzeilen
- Checkbox-Validierung vor Submit
- "Alle auswählen/abwählen" Logik

#### CSS-Variablen
- `--accent-primary`: #34d399 (Dark Mode)
- `--accent-blue`: #60a5fa (Dark Mode)
- `--btn-primary-bg`: #34d399
- `--btn-secondary-bg`: #4b5563
- `--bg-primary`, `--bg-secondary`, `--bg-tertiary` für konsistente Hintergründe

#### CSS-Änderungen (2025-11-22)
- **`static/style.css` Zeilen 2290-2305**: Zweizeilige Header-Darstellung
  - `.th-line-1` und `.th-line-2` für Abgang-Spalten
  - Font-Size: 0.7rem (erste Zeile), 0.75rem (zweite Zeile)
  - Line-height: 1.1 für kompakte Darstellung

- **`static/style.css` Zeilen 2285-2287**: Spaltenbreiten-Optimierung
  - `.whk-column`: min-width und max-width auf 55px reduziert (vorher 70px)

- **`static/style.css` Zeilen 2307-2312**: Table-Cell-Padding
  - `tbody td`: padding von 0.4rem 0.25rem auf 0.3rem 0.15rem reduziert

- **`static/style.css` Zeilen 2554-2559**: Checkbox-Größe
  - width und height von 22px auf 18px reduziert

- **`static/style.css` Zeilen 2336-2344**: Bemerkung-Button
  - padding: 0.2rem 0.4rem (reduziert)
  - font-size: 0.85rem (reduziert)

- **`static/style.css` Zeilen 2765-2769**: Frame-Integration
  - `.question-navigation`: background transparent, border-bottom only
  - padding: 0 0 1rem 0 (reduziert)

#### CSS-Änderungen (2025-01-20)
- **`static/style.css` Zeile 752-754**: Dark Mode Regel für `.question-content .test-info` (Farbe: #f87171)
- **`static/style.css` Zeile 2581-2583**: `.nav-table th:first-child` - `background`-Eigenschaft entfernt
  - Alle Header verwenden jetzt den gleichen Hintergrund aus `.nav-table th` (Zeile 2572: #34495e)

### Verbessert

#### Abnahmetest-Seite (2025-11-22)
- **Horizontale Platzoptimierung**
  - Alle 12 Abgänge jetzt ohne horizontales Scrollen sichtbar
  - Zweizeilige Header sparen ~50% horizontalen Platz pro Spalte
  - Komprimierte Spaltenbreiten ohne Lesbarkeitseinbuße

- **Vertikale Platzoptimierung**
  - Integration von Frames reduziert unnötige Abstände
  - Kompaktere Tabellen ermöglichen mehr Inhalt pro Bildschirm
  - Weniger Scrollen erforderlich während der Testdurchführung

- **Benutzerführung**
  - Dynamischer Titel zeigt sofort welcher Test abgeschlossen wurde
  - Komponenten-spezifische Zählung verhindert Verwirrung
  - Klarer Workflow: Test durchführen → Zum Anfang scrollen → Nächsten Test auswählen
  - Entfernte Redundanzen vereinfachen die Benutzeroberfläche

- **Workflow-Optimierung**
  - Schnellere Navigation durch reduzierten Button-Clutter
  - Smooth Scrolling für besseres visuelles Feedback
  - Fokussierter Arbeitsablauf ohne unnötige Navigationsoptionen

#### Performance
- Clientseitige Suche reduziert Server-Requests drastisch
- Template-Caching optimiert
- Bedingte Datenbank-Abfragen (nur benötigte Sektionen)

#### Benutzererfahrung
- Testabschluss-Seite: Klare visuelle Struktur mit Checklisten-Format
- Testabschluss-Seite: Animierte Icons für bessere Aufmerksamkeit
- Testabschluss-Seite: Hervorhebungen wichtiger Einstellungen
- Konsistentes Dark Mode Design
- Intuitive 3-Stufen-Navigation
- Sofortiges Feedback bei Suche
- Klare Validierungsmeldungen
- Responsive Design auf allen Seiten

#### Code-Qualität
- Umfangreiche Docstrings in Python-Code
- Inline-Kommentare für komplexe Logik
- Konsistente Naming-Conventions
- Strukturierte Template-Organisation

---

## Ältere Versionen

Siehe Git-History für Details zu früheren Releases.
