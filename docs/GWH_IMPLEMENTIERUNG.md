# GWH-Abnahmetest Implementierung

## Übersicht

Die GWH (Gasweichenheizung) Abnahmetest-Implementierung erweitert das bestehende Abnahmetest-System um spezifische Tests für GWH-Anlagen. Im Gegensatz zum EWH-System (Elektroweichenheizung) mit WHK (Weichenheizkasten) verwendet GWH eine hierarchische Struktur mit ZSK (Zentralsteuerkasten) und zugehörigen Komponenten.

## Architektur

### Komponenten-Hierarchie

```
GWH-Projekt
├── GWH-Anlage (1x pro Projekt)
├── HGLS (0-1x pro Projekt, optional)
├── ZSK (1-n pro Projekt)
│   ├── ZSK-Parameter
│   ├── Teile (1-n pro ZSK)
│   └── Temperatursonde (0-1 pro ZSK, optional)
└── Meteostationen (0-5 pro Projekt, optional)
    └── Zugeordnet zu einem ZSK
```

### Datenbank-Modelle

#### ZSKConfig (`models.py`)
```python
class ZSKConfig(db.Model):
    __tablename__ = 'zsk_configs'

    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, ForeignKey)
    zsk_nummer = db.Column(db.String(5))      # z.B. "01", "02"
    name = db.Column(db.String(50))            # z.B. "ZSK Nord"
    anzahl_teile = db.Column(db.Integer)       # Anzahl Heizteile
    hat_temperatursonde = db.Column(db.Boolean)
    modbus_adresse = db.Column(db.Integer)
    reihenfolge = db.Column(db.Integer)
```

#### HGLSConfig (`models.py`)
```python
class HGLSConfig(db.Model):
    __tablename__ = 'hgls_configs'

    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, ForeignKey)
    name = db.Column(db.String(50))
    modbus_adresse = db.Column(db.Integer)
```

#### GWHMeteostation (`models.py`)
```python
class GWHMeteostation(db.Model):
    __tablename__ = 'gwh_meteostations'

    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, ForeignKey)
    zugeordneter_zsk_id = db.Column(db.Integer, ForeignKey)
    ms_nummer = db.Column(db.String(5))        # z.B. "01", "02"
    name = db.Column(db.String(12))            # z.B. "MS Nord"
    modbus_adresse = db.Column(db.Integer)
    reihenfolge = db.Column(db.Integer)
```

#### TestQuestion (`models.py`)
```python
class TestQuestion(db.Model):
    komponente_typ = db.Column(db.String(50))  # GWH-Typen:
    # - 'GWH_Anlage'
    # - 'HGLS'
    # - 'ZSK'
    # - 'GWH_Teile'
    # - 'GWH_Temperatursonde'
    # - 'GWH_Meteostation'
```

#### Parameter-Prüfungen
```python
class ZSKParameterPruefung(db.Model):
    projekt_id, zsk_nummer, parameter_name
    ist_wert, geprueft, nicht_testbar

class HGLSParameterPruefung(db.Model):
    projekt_id, parameter_name
    ist_wert, geprueft, nicht_testbar
```

---

## Routes (app.py)

### Übersichtsseite

#### `GET /projekt/<projekt_id>/gwh-abnahmetest`
**Funktion:** `gwh_abnahmetest(projekt_id)`

Zeigt die Navigations-Übersicht mit Links zu allen Test-Seiten.

**Template:** `gwh_abnahmetest.html`

**Kontext-Variablen:**
- `projekt` - Projekt-Objekt
- `hgls_config` - HGLS-Konfiguration (oder None)
- `zsk_configs` - Liste aller ZSKs
- `gwh_meteostationen` - Liste aller Meteostationen
- `anlage_complete` - Boolean: GWH-Anlage Tests abgeschlossen
- `hgls_complete` - Boolean: HGLS Tests abgeschlossen
- `hgls_param_complete` - Boolean: HGLS Parameter abgeschlossen
- `zsk_complete` - Boolean: ZSK Tests abgeschlossen
- `zsk_param_fortschritt` - Dict: Fortschritt pro ZSK
- `teile_fortschritt` - Dict: Teile-Fortschritt pro ZSK
- `ts_fortschritt` - Dict: Temperatursonde-Fortschritt pro ZSK
- `ms_fortschritt` - Dict: Meteostation-Fortschritt pro MS

---

### Test-Seiten

Alle Test-Seiten verwenden das gemeinsame Template `gwh_test_seite.html`.

#### 1. GWH-Anlage Test
**Route:** `GET/POST /projekt/<projekt_id>/gwh-test/anlage`
**Funktion:** `gwh_test_anlage(projekt_id)`

| Parameter | Wert |
|-----------|------|
| komponente_typ | `GWH_Anlage` |
| komponente_label | `GWH-Anlage` |
| spalten | `['GWH-Anlage']` |

#### 2. HGLS Test
**Route:** `GET/POST /projekt/<projekt_id>/gwh-test/hgls`
**Funktion:** `gwh_test_hgls(projekt_id)`

| Parameter | Wert |
|-----------|------|
| komponente_typ | `HGLS` |
| komponente_label | `HGLS` |
| spalten | `['HGLS']` |
| Voraussetzung | HGLS muss konfiguriert sein |

#### 3. ZSK Test
**Route:** `GET/POST /projekt/<projekt_id>/gwh-test/zsk`
**Funktion:** `gwh_test_zsk(projekt_id)`

| Parameter | Wert |
|-----------|------|
| komponente_typ | `ZSK` |
| komponente_label | `ZSK` |
| spalten | `['ZSK 01', 'ZSK 02', ...]` (dynamisch) |

#### 4. Teile Test
**Route:** `GET/POST /projekt/<projekt_id>/gwh-test/teile/<zsk_nummer>`
**Funktion:** `gwh_test_teile(projekt_id, zsk_nummer)`

| Parameter | Wert |
|-----------|------|
| komponente_typ | `GWH_Teile` |
| komponente_label | `Teile - ZSK {zsk_nummer}` |
| komponente_index | `ZSK {zsk_nummer}` |
| spalten | `['Teil 01', 'Teil 02', ...]` (basierend auf `anzahl_teile`) |

#### 5. Temperatursonde Test
**Route:** `GET/POST /projekt/<projekt_id>/gwh-test/temperatursonde/<zsk_nummer>`
**Funktion:** `gwh_test_temperatursonde(projekt_id, zsk_nummer)`

| Parameter | Wert |
|-----------|------|
| komponente_typ | `GWH_Temperatursonde` |
| komponente_label | `Temperatursonde - ZSK {zsk_nummer}` |
| komponente_index | `ZSK {zsk_nummer}` |
| spalten | `['TS']` |
| Voraussetzung | `zsk.hat_temperatursonde == True` |

#### 6. Meteostation Test
**Route:** `GET/POST /projekt/<projekt_id>/gwh-test/meteostation/<ms_nummer>`
**Funktion:** `gwh_test_meteostation(projekt_id, ms_nummer)`

| Parameter | Wert |
|-----------|------|
| komponente_typ | `GWH_Meteostation` |
| komponente_label | `Meteostation - {ms.name}` |
| komponente_index | `MS {ms_nummer}` |
| spalten | `[ms.name]` (z.B. `['MS Nord']`) |

---

### Parameter-Prüfungen

#### ZSK Parameter
**Route:** `GET/POST /projekt/<projekt_id>/zsk-parameter/<zsk_nummer>`
**Funktion:** `zsk_parameter(projekt_id, zsk_nummer)`
**Template:** `zsk_parameter.html`

Parameter werden in `parameter_definitionen.py` definiert:
```python
ZSK_PARAMETER = [
    {'name': 'anstiegsdruck_max', 'label': 'Anstiegsdruck maximal', 'einheit': 'bar'},
    {'name': 'druckanstiegsdifferenz', 'label': 'Druckanstiegsdifferenz', 'einheit': 'bar'},
    # ... weitere Parameter
]
```

#### HGLS Parameter
**Route:** `GET/POST /projekt/<projekt_id>/hgls-parameter`
**Funktion:** `hgls_parameter(projekt_id)`
**Template:** `hgls_parameter.html`

Parameter werden in `parameter_definitionen.py` definiert:
```python
HGLS_PARAMETER = [
    {'name': 'param1', 'label': 'Parameter 1', 'einheit': 'unit'},
    # ... weitere Parameter
]
```

---

## Templates

### gwh_abnahmetest.html
Übersichtsseite mit Navigation zu allen Test-Seiten.

**Struktur:**
```
┌─────────────────────────────────────────────────────┐
│ GWH-Abnahmetest: Projektname    [← Zurück]         │
├─────────────────────────────────────────────────────┤
│ Allgemein                                           │
│ [GWH-Anlage ✓] [HGLS] [HGLS-Parameter] [ZSK]       │
├─────────────────────────────────────────────────────┤
│ ZSK Nr. │ Parameter │ ZSK-Tests │ Teile │ TS │ MS  │
│─────────│───────────│───────────│───────│────│─────│
│ ZSK 01  │ [Param ✓] │ [ZSK]     │[Teile]│[TS]│[MS] │
│ ZSK 02  │ [Param]   │ [ZSK]     │[Teile]│ —  │ —   │
└─────────────────────────────────────────────────────┘
```

**Fortschrittsanzeige:**
- Grüner Haken (✓) bei `complete == True`
- Buttons werden grün eingefärbt (CSS-Klasse `completed`)

### gwh_test_seite.html
Generisches Template für alle GWH-Test-Seiten.

**Struktur:**
```
┌─────────────────────────────────────────────────────┐
│ {komponente_label} Test        [← Zurück]          │
├─────────────────────────────────────────────────────┤
│ Fragen-Info-Tabelle                                 │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Testfrage │ Testbeschreibung │ Erwartet │ 📷   │ │
│ └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│ [◄ Vorherige Frage]  Frage 1/5  [Nächste Frage ►]  │
│ ████████████░░░░░░░░░░░░░░░░░░ 20%                 │
├─────────────────────────────────────────────────────┤
│ LSS-CH        │ Spalte1 │ Spalte2 │ ...            │
│───────────────│─────────│─────────│────            │
│ Richtig       │   ☑     │   ☐     │                │
│ Falsch        │   ☐     │   ☐     │                │
│ Nicht Testbar │   ☐     │   ☐     │                │
│ Bemerkung     │   💬    │   💬    │                │
├─────────────────────────────────────────────────────┤
│ WH-LTS        │ Spalte1 │ Spalte2 │ ...            │
│ (gleiche Struktur wie LSS-CH)                      │
└─────────────────────────────────────────────────────┘
```

**Kontext-Variablen:**
- `projekt` - Projekt-Objekt
- `komponente_typ` - String (z.B. 'GWH_Anlage')
- `komponente_label` - Anzeigename (z.B. 'GWH-Anlage')
- `fragen` - Liste der TestQuestion-Objekte
- `spalten` - Liste der Spaltennamen
- `fragen_json` - JSON für JavaScript
- `ergebnisse_json` - Bestehende Ergebnisse als JSON
- `zurueck_url` - URL für Zurück-Button

### zsk_parameter.html / hgls_parameter.html
Parameter-Prüfungsseiten mit Auto-Save.

**Struktur:**
```
┌─────────────────────────────────────────────────────┐
│ ZSK Parameter-Prüfung: ZSK 01  [← Zurück]          │
│ Projekt: Projektname                                │
├─────────────────────────────────────────────────────┤
│ ████████████████░░░░░░░░░░░░░░░░ 3 von 18 erledigt │
├─────────────────────────────────────────────────────┤
│ Parameter      │ Einheit │ Ist-Wert │ ✓ │ n.t.    │
│────────────────│─────────│──────────│───│─────────│
│ Param 1        │ bar     │ [____]   │ ☑ │ ☐       │
│ Param 2        │ sec     │ [____]   │ ☐ │ ☑       │
│ Param 3        │ bar     │ [____]   │ ☐ │ ☐       │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Auto-Save bei jeder Änderung (500ms Debounce)
- Zeilen-Highlighting: Grün (geprüft), Grau (nicht testbar)
- Radio-Verhalten: Geprüft und Nicht-Testbar schließen sich aus
- Fortschrittsbalken mit Live-Update

---

## CSS-Styling

### Farbschema

| Element | Light Theme | Dark Theme |
|---------|-------------|------------|
| Tabellen-Header | `#2c3e50` | `#2c3e50` |
| Header-Text | `#ffffff` | `#ffffff` |
| Richtig/Geprüft | `#d1fae5` | `rgba(34, 197, 94, 0.2)` |
| Falsch | `#fee2e2` | `rgba(239, 68, 68, 0.2)` |
| Nicht Testbar | `#f3f4f6` | `rgba(107, 114, 128, 0.3)` |
| Fortschrittsbalken | `#22c55e → #10b981` | (gleich) |
| Button completed | `#dcfce7` | `#166534` |

### CSS-Klassen

```css
/* Navigation Buttons */
.nav-btn              /* Standard Button */
.nav-btn.completed    /* Abgeschlossener Button (grün) */
.nav-btn-compact      /* Kompakter Button für Tabellen */

/* Tabellen */
.nav-table            /* Übersichts-Tabelle */
.dark-header          /* Dunkler Tabellen-Header */
.parameter-table      /* Parameter-Prüfungs-Tabelle */

/* Zeilen-Status */
.row-geprueft         /* Geprüfte Zeile (grün) */
.row-nicht-testbar    /* Nicht testbare Zeile (grau) */
.result-row-richtig   /* Test: Richtig */
.result-row-falsch    /* Test: Falsch */
.result-row-nicht-testbar /* Test: Nicht testbar */

/* Fortschritt */
.progress-info        /* Container */
.progress-bar-container /* Balken-Hintergrund */
.progress-bar         /* Grüner Fortschrittsbalken */
```

---

## JavaScript-Funktionalität

### Auto-Save (Parameter-Seiten)
```javascript
// Debounced Save nach 500ms
function debouncedSave() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveParameters, 500);
}

// AJAX POST an Server
function saveParameters() {
    fetch(`/projekt/${projektId}/zsk-parameter/${zskNummer}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
}
```

### Auto-Save (Test-Seiten)
```javascript
// Speichert nach jeder Checkbox-Änderung
function autoSaveResult(questionId, system, spalte, result, bemerkung) {
    fetch(window.location.pathname, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [questionId]: { [system]: { result, bemerkung }}})
    })
}
```

### Fragen-Navigation
```javascript
// Navigation zwischen Fragen
function loadQuestion(index)     // Lädt Frage an Index
function previousQuestion()      // Vorherige Frage
function nextQuestion()          // Nächste Frage
function updateProgressBar()     // Aktualisiert Fortschritt
```

---

## Testfragen-Verwaltung

### Komponenten-Typen für GWH

| komponente_typ | Beschreibung | Spalten |
|----------------|--------------|---------|
| `GWH_Anlage` | Allgemeine GWH-Anlage Tests | 1 (GWH-Anlage) |
| `HGLS` | HGLS-spezifische Tests | 1 (HGLS) |
| `ZSK` | ZSK-Tests (alle ZSKs) | n (ZSK 01, ZSK 02, ...) |
| `GWH_Teile` | Heizteile pro ZSK | n (Teil 01, Teil 02, ...) |
| `GWH_Temperatursonde` | Temperatursonde pro ZSK | 1 (TS) |
| `GWH_Meteostation` | Meteostation | 1 (MS-Name) |

### Testfragen anlegen

Über die Testfragen-Verwaltung (`/testfragen`) können Fragen für jeden Komponenten-Typ angelegt werden:

1. Komponenten-Typ auswählen (z.B. `GWH_Anlage`)
2. Frage-Text eingeben
3. Test-Information (rot/kursiv angezeigt)
4. Erwartetes Ergebnis
5. Optional: Screenshot-Pfad
6. Optional: Preset-Antworten (JSON)

---

## URL-Struktur

```
/projekt/{id}/gwh-abnahmetest           → Übersicht
/projekt/{id}/gwh-test/anlage           → GWH-Anlage Test
/projekt/{id}/gwh-test/hgls             → HGLS Test
/projekt/{id}/gwh-test/zsk              → ZSK Test (alle)
/projekt/{id}/gwh-test/teile/{zsk_nr}   → Teile Test (pro ZSK)
/projekt/{id}/gwh-test/temperatursonde/{zsk_nr} → TS Test (pro ZSK)
/projekt/{id}/gwh-test/meteostation/{ms_nr}     → MS Test (pro MS)
/projekt/{id}/zsk-parameter/{zsk_nr}    → ZSK Parameter
/projekt/{id}/hgls-parameter            → HGLS Parameter
/projekt/{id}/gwh-konfiguration         → GWH Konfiguration
```

---

## Konfiguration

### GWH-Konfiguration (`/projekt/{id}/gwh-konfiguration`)

Ermöglicht das Einrichten von:
- ZSKs (Nummer, Name, Anzahl Teile, Temperatursonde, Modbus-Adresse)
- HGLS (aktivieren/deaktivieren, Modbus-Adresse)
- Meteostationen (Nummer, Name, zugeordneter ZSK, Modbus-Adresse)

---

## Unterschiede zu EWH

| Aspekt | EWH | GWH |
|--------|-----|-----|
| Hauptkomponente | WHK (Weichenheizkasten) | ZSK (Zentralsteuerkasten) |
| Unterkomponenten | WHK direkt | ZSK → Teile, TS, MS |
| Parameter-Prüfung | WHK-Parameter | ZSK-Parameter, HGLS-Parameter |
| Optionale Komponenten | - | HGLS, Temperatursonde, Meteostation |
| Test-Struktur | Alle Tests auf einer Seite | Separate Seiten pro Komponente |
| Spalten-Logik | WHK 01, WHK 02, ... | Dynamisch pro Komponente |

---

## Dateien

### Backend
- `app.py` - Routes (Zeilen ~2187-3310)
- `models.py` - Datenbank-Modelle
- `parameter_definitionen.py` - ZSK_PARAMETER, HGLS_PARAMETER

### Templates
- `templates/gwh_abnahmetest.html` - Übersichtsseite
- `templates/gwh_test_seite.html` - Generisches Test-Template
- `templates/zsk_parameter.html` - ZSK Parameter-Prüfung
- `templates/hgls_parameter.html` - HGLS Parameter-Prüfung
- `templates/gwh_konfiguration.html` - GWH Konfiguration

### Styles
- Inline-Styles in Templates (kein separates CSS-File)
- Dark Theme Support via `[data-theme="dark"]` Selektoren

---

## Erweiterungsmöglichkeiten

1. **PDF-Export** - GWH-spezifischer Export mit allen Komponenten
2. **Batch-Tests** - Mehrere ZSKs gleichzeitig testen
3. **Import/Export** - Konfiguration zwischen Projekten kopieren
4. **Validierung** - Automatische Prüfung von Grenzwerten
5. **Historie** - Änderungsverlauf für Parameter-Werte
