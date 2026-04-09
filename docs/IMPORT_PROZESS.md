# Import-Prozess: Alte JSON-Daten → Neue Datenbank

**Autor:** Claude Code
**Datum:** 20.11.2025
**Version:** 2.0
**Projekt:** SBB Weichenheizung Abnahmetest-Anwendung

**Änderungshistorie:**
- **v2.0 (20.11.2025):** Generisches Import-Script, WHK-Mapping-Korrekturen, safe_int Funktion, Batch-Import
- **v1.0 (20.11.2025):** Initiale Version mit Bowil-Import

---

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [JSON-Struktur (Alt-System)](#json-struktur-alt-system)
3. [Datenbank-Struktur (Neu-System)](#datenbank-struktur-neu-system)
4. [Import-Ablauf](#import-ablauf)
5. [Spalten-Mapping](#spalten-mapping)
6. [Besonderheiten & Spezialfälle](#besonderheiten--spezialfälle)
7. [Import-Script](#import-script)
8. [Fehlerbehandlung](#fehlerbehandlung)
9. [Verifizierung](#verifizierung)

---

## Übersicht

### Zweck
Der Import-Prozess migriert Weichenheizungs-Projekte vom alten JSON-basierten System in die neue SQLite-Datenbank mit strukturierten Tabellen.

### Datenfluss
```
JSON-File (Alte Projekte/)
    ↓
Import-Script (Python)
    ↓
SQLite-Datenbank (database/whs.db)
    ↓
Flask-Anwendung
```

### Betroffene Datenbereiche
- Projektinformationen (Name, DIDOK, Prüfer, Daten)
- WHK-Konfigurationen (Abgänge, Temperatursonden, Antriebsheizungen, Meteostationen)
- Testergebnisse für beide Systeme (LSS-CH und WH-LTS)

---

## JSON-Struktur (Alt-System)

### Haupt-Struktur
Das JSON-File hat folgende Hauptbereiche:

```json
{
  "anzahl_whk": 1,
  "felder": [...],
  "projektinfo": {...},
  "export": {...},
  "abgaenge": {...}
}
```

### 1. Projektinfo
```json
"projektinfo": {
  "projektname": "Bowil",
  "didok": "BOW",
  "projektleiter": "Norbert Küng",
  "baumappe": "09.04.2025",
  "pruefer": "Nicolas Abé/Christian Duss",
  "pruefdatum": "01.10.2025",
  "bemerkungen": ""
}
```

**Felder:**
- `projektname` (String): Name des Projekts
- `didok` (String): DIDOK-Bezeichnung des Betriebspunkts
- `projektleiter` (String): Projektleiter der SBB
- `baumappe` (Date String): Datum der Baumappenversion
- `pruefer` (String): Prüfer von Achermann
- `pruefdatum` (Date String): Datum der Prüfung
- `bemerkungen` (String): Optionale Bemerkungen

### 2. WHK-Konfiguration (felder)
```json
"felder": [
  {
    "name": "WHK 01",
    "abgang": "2",
    "temp": "1",
    "ah": false,
    "meteo": "MS 01"
  }
]
```

**Felder:**
- `name` (String): WHK-Nummer (z.B. "WHK 01")
- `abgang` (String/Number): Anzahl Abgänge
- `temp` (String/Number): Anzahl Temperatursonden
- `ah` (Boolean): Hat Antriebsheizung
- `meteo` (String): Meteostation-Name

### 3. Testergebnisse (abgaenge)

Die Testergebnisse sind unter dem Schlüssel `"abgaenge"` strukturiert mit **unterschiedlichen Hierarchien** je nach Komponententyp:

#### Hierarchie-Typ 1: OHNE WHK-Ebene
**Komponenten:** `ANLAGE`, `WHK`

```json
"ANLAGE": {
  "0": {                          // Frage-Index
    "auswahl": {
      "C": {"0": "Richtig"},      // Spalte C
      "B": {"0": "Richtig"}       // Spalte B
    },
    "bemerkungen": {}
  },
  "1": {...}
}
```

**Struktur:** `KOMPONENTE → Frage-Index → auswahl → Spalte → Wert`

#### Hierarchie-Typ 2: MIT WHK-Ebene
**Komponenten:** `ABG`, `TS`, `MS`, `AH`

```json
"ABG": {
  "0": {                          // WHK-Index
    "0": {                        // Frage-Index
      "auswahl": {
        "C": {
          "0": "Richtig",         // Instanz 0 (Abgang 01)
          "1": "Richtig"          // Instanz 1 (Abgang 02)
        },
        "B": {...},
        "A": {...}
      },
      "bemerkungen": {}
    },
    "1": {...}
  }
}
```

**Struktur:** `KOMPONENTE → WHK-Index → Frage-Index → auswahl → Spalte → Instanz-Index → Wert`

---

## Datenbank-Struktur (Neu-System)

### Tabellen-Übersicht
1. **projects** - Projektinformationen
2. **whk_configs** - WHK-Konfigurationen
3. **test_questions** - Testfragen-Vorlagen
4. **abnahme_test_results** - Testergebnisse

### 1. Tabelle: projects
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    energie VARCHAR(10) NOT NULL,           -- EWH/GWH
    projektname VARCHAR(200) NOT NULL,
    didok_betriebspunkt VARCHAR(100),
    baumappenversion DATE,
    projektleiter_sbb VARCHAR(150),
    pruefer_achermann VARCHAR(150),
    pruefdatum DATE,
    bemerkung TEXT,
    erstellt_am DATETIME,
    geaendert_am DATETIME
);
```

### 2. Tabelle: whk_configs
```sql
CREATE TABLE whk_configs (
    id INTEGER PRIMARY KEY,
    projekt_id INTEGER NOT NULL,            -- FK zu projects
    whk_nummer VARCHAR(20) NOT NULL,
    anzahl_abgaenge INTEGER NOT NULL,
    anzahl_temperatursonden INTEGER NOT NULL,
    hat_antriebsheizung BOOLEAN,
    meteostation VARCHAR(50),
    erstellt_am DATETIME,
    FOREIGN KEY (projekt_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE (projekt_id, whk_nummer)
);
```

### 3. Tabelle: test_questions
```sql
CREATE TABLE test_questions (
    id INTEGER PRIMARY KEY,
    komponente_typ VARCHAR(50) NOT NULL,    -- Anlage, WHK, Abgang, etc.
    testszenario VARCHAR(200) NOT NULL,
    frage_nummer INTEGER NOT NULL UNIQUE,   -- Global eindeutig
    frage_text TEXT NOT NULL,
    test_information TEXT,
    reihenfolge INTEGER NOT NULL,           -- Sortierung innerhalb Komponente
    preset_antworten JSON,
    erstellt_am DATETIME
);
```

**Komponententypen:**
- `Anlage` (WH-Anlage)
- `WHK` (Weichenheizkabinen)
- `Abgang`
- `Temperatursonde`
- `Antriebsheizung`
- `Meteostation`

### 4. Tabelle: abnahme_test_results
```sql
CREATE TABLE abnahme_test_results (
    id INTEGER PRIMARY KEY,
    projekt_id INTEGER NOT NULL,            -- FK zu projects
    test_question_id INTEGER NOT NULL,      -- FK zu test_questions
    komponente_index VARCHAR(50) NOT NULL,  -- z.B. "WHK 01", "Anlage", "MS 01"
    spalte VARCHAR(100),                    -- z.B. "Abgang 01", "TS 02"
    lss_ch_result VARCHAR(20),              -- richtig/falsch/nicht_testbar
    wh_lts_result VARCHAR(20),              -- richtig/falsch/nicht_testbar
    lss_ch_bemerkung TEXT,
    wh_lts_bemerkung TEXT,
    getestet_am DATETIME,
    tester VARCHAR(100),
    FOREIGN KEY (projekt_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (test_question_id) REFERENCES test_questions(id) ON DELETE CASCADE
);
```

---

## Import-Ablauf

### Schritt 1: Vorbereitung
```python
# 1. JSON-File laden
with open('Alte Projekte/Bowil BOW.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 2. Datenbank-Context aktivieren
with app.app_context():
    # Import-Logik
```

### Schritt 2: Projekt erstellen
```python
projektinfo = data.get('projektinfo', {})

projekt = Project(
    energie='EWH',  # Standard
    projektname=projektinfo.get('projektname'),
    didok_betriebspunkt=projektinfo.get('didok'),
    baumappenversion=parse_date(projektinfo.get('baumappe')),
    projektleiter_sbb=projektinfo.get('projektleiter'),
    pruefer_achermann=projektinfo.get('pruefer'),
    pruefdatum=parse_date(projektinfo.get('pruefdatum')),
    bemerkung=projektinfo.get('bemerkungen')
)

db.session.add(projekt)
db.session.flush()  # Um ID zu erhalten
```

**Datum-Parsing:**
```python
def parse_date(date_string):
    """Konvertiert DD.MM.YYYY zu date-Objekt"""
    formats = ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    return None
```

### Schritt 3: WHK-Konfigurationen erstellen
```python
felder = data.get('felder', [])

for whk_data in felder:
    whk_config = WHKConfig(
        projekt_id=projekt.id,
        whk_nummer=whk_data.get('name'),           # "WHK 01"
        anzahl_abgaenge=int(whk_data.get('abgang')),
        anzahl_temperatursonden=int(whk_data.get('temp')),
        hat_antriebsheizung=bool(whk_data.get('ah')),
        meteostation=whk_data.get('meteo')
    )
    db.session.add(whk_config)

db.session.flush()
```

### Schritt 4: Testergebnisse importieren

Die Testergebnisse werden **nach Komponententyp** verarbeitet:

#### 4.1 ANLAGE (Spezialfall)
```python
if 'ANLAGE' in abgaenge_data:
    for frage_idx_str, frage_data in abgaenge_data['ANLAGE'].items():
        frage_idx = int(frage_idx_str)
        reihenfolge = frage_idx + 1

        # Testfrage aus DB holen
        test_q = TestQuestion.query.filter_by(
            komponente_typ='Anlage',
            reihenfolge=reihenfolge
        ).first()

        if test_q:
            auswahl = frage_data.get('auswahl', {})

            # WICHTIG: ANLAGE hat Spalte C→LSS-CH, B→WH-LTS
            lss_ch_res = standardize_result(auswahl['C']['0'])
            wh_lts_res = standardize_result(auswahl['B']['0'])

            result = AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=test_q.id,
                komponente_index='Anlage',
                spalte=None,
                lss_ch_result=lss_ch_res,
                wh_lts_result=wh_lts_res
            )
            db.session.add(result)
```

#### 4.2 WHK (Direkt, ohne WHK-Ebene)
```python
if 'WHK' in abgaenge_data:
    for frage_idx_str, frage_data in abgaenge_data['WHK'].items():
        frage_idx = int(frage_idx_str)
        reihenfolge = frage_idx + 1

        test_q = TestQuestion.query.filter_by(
            komponente_typ='WHK',
            reihenfolge=reihenfolge
        ).first()

        if test_q:
            auswahl = frage_data.get('auswahl', {})

            # Normal: A→LSS-CH, B→WH-LTS
            lss_ch_res = standardize_result(auswahl['A']['0'])
            wh_lts_res = standardize_result(auswahl['B']['0'])

            result = AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=test_q.id,
                komponente_index='WHK 01',  # Erste WHK
                spalte=None,
                lss_ch_result=lss_ch_res,
                wh_lts_result=wh_lts_res
            )
            db.session.add(result)
```

#### 4.3 ABG (Mit WHK-Ebene, mehrere Instanzen)
```python
if 'ABG' in abgaenge_data:
    for whk_idx_str, whk_data in abgaenge_data['ABG'].items():
        whk_idx = int(whk_idx_str)
        komp_idx = f"WHK {whk_idx + 1:02d}"  # "WHK 01"

        for frage_idx_str, frage_data in whk_data.items():
            frage_idx = int(frage_idx_str)
            reihenfolge = frage_idx + 1

            test_q = TestQuestion.query.filter_by(
                komponente_typ='Abgang',
                reihenfolge=reihenfolge
            ).first()

            if test_q:
                auswahl = frage_data.get('auswahl', {})
                anzahl_abgaenge = len(auswahl['A'])  # Dictionary-Keys

                # Für jeden Abgang
                for abg_idx in range(anzahl_abgaenge):
                    spalte = f"Abgang {abg_idx + 1:02d}"

                    # Zugriff mit String-Key
                    lss_ch_res = standardize_result(
                        auswahl['A'][str(abg_idx)]
                    )
                    wh_lts_res = standardize_result(
                        auswahl['B'][str(abg_idx)]
                    )

                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=test_q.id,
                        komponente_index=komp_idx,  # "WHK 01"
                        spalte=spalte,              # "Abgang 01"
                        lss_ch_result=lss_ch_res,
                        wh_lts_result=wh_lts_res
                    )
                    db.session.add(result)
```

#### 4.4 TS (Mit WHK-Ebene, mehrere Instanzen)
Analog zu ABG, aber:
```python
spalte = f"TS {ts_idx + 1:02d}"  # "TS 01", "TS 02"
```

#### 4.5 MS (Mit WHK-Ebene, eine Instanz)
```python
if 'MS' in abgaenge_data:
    for whk_idx_str, whk_data in abgaenge_data['MS'].items():
        whk_idx = int(whk_idx_str)
        ms_name = whk_configs[whk_idx].meteostation  # "MS 01"

        for frage_idx_str, frage_data in whk_data.items():
            # ... Testfrage holen ...

            auswahl = frage_data.get('auswahl', {})

            lss_ch_res = standardize_result(auswahl['A']['0'])
            wh_lts_res = standardize_result(auswahl['B']['0'])

            result = AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=test_q.id,
                komponente_index=ms_name,   # WICHTIG: "MS 01" (nicht "WHK 01")
                spalte=ms_name,             # "MS 01"
                lss_ch_result=lss_ch_res,
                wh_lts_result=wh_lts_res
            )
            db.session.add(result)
```

### Schritt 5: Commit
```python
db.session.commit()
```

---

## Spalten-Mapping

### Standard-Mapping (alle außer ANLAGE)
```
JSON-Spalte → Datenbank-Feld
────────────────────────────────
A           → lss_ch_result
B           → wh_lts_result
C           → IGNORIERT
```

**Komponenten mit Standard-Mapping:**
- `WHK`
- `ABG` (Abgänge)
- `TS` (Temperatursonden)
- `MS` (Meteostationen)
- `AH` (Antriebsheizungen)

### Spezielles Mapping für ANLAGE
```
JSON-Spalte → Datenbank-Feld
────────────────────────────────
C           → lss_ch_result    (!)
B           → wh_lts_result
A           → NICHT VORHANDEN
```

**Grund:** Im JSON hat ANLAGE nur Spalte C und B (keine Spalte A).

### Ergebnis-Standardisierung
```python
def standardize_result(ergebnis):
    """Konvertiert JSON-Werte zu DB-Format"""
    if ergebnis == 'Richtig':
        return 'richtig'
    elif ergebnis == 'Falsch':
        return 'falsch'
    elif ergebnis == 'Nicht Testbar':
        return 'nicht_testbar'
    return None
```

**Mapping:**
```
JSON-Wert       → DB-Wert
──────────────────────────────
"Richtig"       → "richtig"
"Falsch"        → "falsch"
"Nicht Testbar" → "nicht_testbar"
```

---

## Besonderheiten & Spezialfälle

### 1. Komponente_Index vs. Spalte

**komponente_index:**
- Identifiziert die **Komponenten-Instanz** (z.B. welche WHK)
- Beispiele: `"Anlage"`, `"WHK 01"`, `"MS 01"`

**spalte:**
- Identifiziert die **Spalte innerhalb der Komponente** (z.B. welcher Abgang)
- Beispiele: `"Abgang 01"`, `"TS 02"`, `"MS 01"`, `None`

**Verwendung:**

| Komponente | komponente_index | spalte | Erklärung |
|---|---|---|---|
| Anlage | `"Anlage"` | `None` | Nur eine Anlage |
| WHK | `"WHK 01"` | `None` | WHK-Tests ohne Spalten |
| Abgang | `"WHK 01"` | `"Abgang 01"` | Abgang 01 in WHK 01 |
| TS | `"WHK 01"` | `"TS 01"` | TS 01 in WHK 01 |
| MS | `"MS 01"` | `"MS 01"` | MS 01 (unabhängig) |
| AH | `"WHK 01"` | `"Antriebsheizung"` | AH in WHK 01 |

### 2. Frage-Mapping

**Zuordnung JSON → DB:**
- JSON verwendet: `Frage-Index` (0, 1, 2, ...)
- DB verwendet: `reihenfolge` (1, 2, 3, ...)

**Konvertierung:**
```python
frage_idx = int(frage_idx_str)  # JSON: "0", "1", ...
reihenfolge = frage_idx + 1     # DB:   1,   2,   ...
```

### 3. Mehrere Instanzen pro Frage

Für Komponenten mit mehreren Instanzen (z.B. 2 Abgänge):

**JSON:**
```json
"auswahl": {
  "A": {
    "0": "Richtig",    // Abgang 1
    "1": "Falsch"      // Abgang 2
  }
}
```

**Import:**
```python
anzahl_abgaenge = len(auswahl['A'])  # 2

for abg_idx in range(anzahl_abgaenge):
    # Erstelle separates AbnahmeTestResult für jeden Abgang
    # abg_idx = 0 → "Abgang 01"
    # abg_idx = 1 → "Abgang 02"
```

**Ergebnis in DB:**
- 1 Frage × 2 Abgänge = **2 Datensätze** in `abnahme_test_results`

### 4. Leere Komponenten

**AH (Antriebsheizung):** Wenn `ah: false` in WHK-Konfiguration:
```json
"AH": {}  // Leeres Objekt im JSON
```

**Import:** Keine Testergebnisse werden importiert.

### 5. WHK-Mapping-Probleme und Lösungen **NEU in v2.0**

#### Problem 1: Falsche WHK-Nummern-Zuordnung

**Ursprüngliches Problem:**
```python
# FALSCH: Hart-codierte Berechnung
komp_idx = f"WHK {whk_idx + 1:02d}"
# whk_idx=0 → "WHK 01"
# whk_idx=1 → "WHK 02"
```

**Problem:** Bei Projekten mit nicht-sequenziellen WHK-Nummern (z.B. Sargans: WHK 10, 20, 30, 40, 51, 60, 70, 86, 90) wurden falsche Zuordnungen erstellt.

**Lösung:**
```python
# RICHTIG: WHK-Nummer aus Konfiguration lesen
komp_idx = whk_configs[whk_idx].whk_nummer
# whk_idx=0 → whk_configs[0].whk_nummer → "WHK 10"
# whk_idx=1 → whk_configs[1].whk_nummer → "WHK 20"
```

**Betroffene Komponenten:**
- ABG (Abgänge)
- TS (Temperatursonden)
- MS (Meteostationen)
- AH (Antriebsheizungen)

#### Problem 2: WHK-Komponente mit mehreren WHKs

**Ursprüngliches Problem:**
```python
# FALSCH: Hart-codiert auf WHK 01
komponente_index = 'WHK 01'
```

**Problem:** Bei Projekten mit mehreren WHKs (z.B. GESE: WHK 02-08) wurden alle WHK-Ergebnisse auf "WHK 01" gesetzt, obwohl WHK 01 gar nicht existierte.

**Lösung:**
WHK-Komponente hat **keine WHK-Ebene** im JSON, aber **mehrere WHK-Indizes in den Spalten** (ähnlich wie Abgänge):

```python
# RICHTIG: Durch alle WHK-Indizes iterieren
if 'WHK' in abgaenge_data:
    for frage_idx_str, frage_data in abgaenge_data['WHK'].items():
        auswahl = frage_data.get('auswahl', {})

        # Anzahl WHKs aus Spalten-Daten bestimmen
        anzahl_whks = len(auswahl.get('A', {}))

        # Für jede WHK
        for whk_idx in range(anzahl_whks):
            komp_idx = whk_configs[whk_idx].whk_nummer  # "WHK 02", "WHK 03", ...

            lss_ch_res = standardize_result(auswahl['A'][str(whk_idx)])
            wh_lts_res = standardize_result(auswahl['B'][str(whk_idx)])

            result = AbnahmeTestResult(
                komponente_index=komp_idx,  # Dynamisch aus Config
                ...
            )
```

**Beispiel (GESE):**
```json
"WHK": {
  "0": {  // Frage 0
    "auswahl": {
      "A": {
        "0": "Richtig",  // WHK 02 (whk_idx=0 → whk_configs[0].whk_nummer = "WHK 02")
        "1": "Richtig",  // WHK 03 (whk_idx=1 → whk_configs[1].whk_nummer = "WHK 03")
        "2": "Richtig",  // WHK 04
        ...
        "6": "Richtig"   // WHK 08
      }
    }
  }
}
```

**Ergebnis:** 7 WHKs × 23 Fragen = 161 WHK-Ergebnisse (statt nur 23)

#### Problem 3: Leere String-Werte in WHK-Konfiguration

**Ursprüngliches Problem:**
```python
# FEHLER bei leeren Strings
anzahl_abgaenge = int(whk_data.get('abgang'))
# ValueError: invalid literal for int() with base 10: ''
```

**JSON-Beispiel (Chavornay WHK 02):**
```json
"felder": [
  {
    "name": "WHK 02",
    "abgang": "",    // Leerer String!
    "temp": "1",
    "ah": false
  }
]
```

**Lösung mit `safe_int()`:**
```python
anzahl_abgaenge = safe_int(whk_data.get('abgang'), 0)
# "" → 0
# None → 0
# "5" → 5
```

### 6. Projekt-Spezifische Besonderheiten

**Verschiedene Projekte im Vergleich:**

| Projekt | WHKs | Besonderheit |
|---|---|---|
| Bowil | 1 | WHK 01, einfachste Struktur |
| GESE | 7 | WHK 02-08 (nicht ab 01!) |
| Sargans | 9 | WHK 10, 20, 30, 40, 51, 60, 70, 86, 90 (nicht-sequenziell) |
| Chavornay | 3 | WHK 02 hat 0 Abgänge (leerer String) |
| Düdingen | 3 | WHK 01, WHK 01A, WHK 02 (Buchstaben-Suffix) |

**Wichtig:** Das Script muss flexibel genug sein, um alle diese Variationen zu verarbeiten!

---

## Import-Script

### Generisches Import-Script (v2.0)
**Pfad:** `scripts/import_json_project.py`

**Neu in v2.0:**
- Generisches Script für beliebige Projekte
- Automatische WHK-Nummern-Erkennung aus Konfiguration
- Robuste Fehlerbehandlung mit `safe_int()`
- `--force` Flag zum Überschreiben existierender Projekte
- `--no-verify` Flag zum Überspringen der Verifizierung
- Unterstützung für nicht-sequenzielle WHK-Nummern (z.B. WHK 10, 20, 30)

### Verwendung

#### Einzelnes Projekt importieren
```bash
# Normaler Import
venv\Scripts\python.exe scripts\import_json_project.py "Alte Projekte/Sargans SA.json"

# Mit Force (überschreibt existierendes Projekt)
venv\Scripts\python.exe scripts\import_json_project.py "Alte Projekte/Sargans SA.json" --force

# Ohne Verifizierung (schneller)
venv\Scripts\python.exe scripts\import_json_project.py "Alte Projekte/Sargans SA.json" --no-verify
```

#### Batch-Import aller Projekte
```bash
# Alle Projekte nacheinander importieren
for %f in ("Alte Projekte\*.json") do venv\Scripts\python.exe scripts\import_json_project.py %f --no-verify
```

### Funktionen

#### 1. `parse_date(date_string)`
Konvertiert Datum-Strings in verschiedenen Formaten zu `datetime.date`.

**Unterstützte Formate:**
- `DD.MM.YYYY` (z.B. "09.04.2025")
- `YYYY-MM-DD` (z.B. "2025-04-09")
- `DD/MM/YYYY` (z.B. "09/04/2025")

#### 2. `standardize_result(ergebnis)`
Konvertiert JSON-Ergebnisse zu DB-Format.

**Mapping:**
- `"Richtig"` → `"richtig"`
- `"Falsch"` → `"falsch"`
- `"Nicht Testbar"` → `"nicht_testbar"`

#### 3. `safe_int(value, default=0)` **NEU in v2.0**
Konvertiert Werte sicher zu Integer, behandelt leere Strings und None.

```python
def safe_int(value, default=0):
    """Konvertiert einen Wert sicher zu Integer"""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
```

**Verwendung:**
```python
anzahl_abgaenge = safe_int(whk_data.get('abgang'), 0)
# Leerer String '' → 0
# None → 0
# "5" → 5
# 5 → 5
```

#### 4. `check_existing_project(projektname, didok)`
Prüft ob ein Projekt mit gleichem Namen oder DIDOK bereits existiert.

#### 5. `import_projekt(json_path, force=False)`
Hauptfunktion für den Import.

**Parameter:**
- `json_path` (str): Pfad zum JSON-File
- `force` (bool): Überschreibt existierendes Projekt ohne Nachfrage

**Rückgabe:** `True` bei Erfolg, `False` bei Fehler

#### 6. `verify(projektname=None)`
Verifiziert den Import und zeigt Statistiken.

**Parameter:**
- `projektname` (str, optional): Verifiziert nur spezifisches Projekt

### Script-Ablauf
```
1. JSON-Analyse
   ├─ Zeige Projektinfo
   ├─ Zeige WHK-Konfiguration
   └─ Zeige Anzahl Testergebnisse

2. Datenbank bereinigen
   └─ Lösche alle Projekte

3. Projekt-Import
   ├─ Projekt erstellen
   ├─ WHK-Configs erstellen
   └─ Testergebnisse importieren
       ├─ ANLAGE (spezielles Mapping)
       ├─ WHK
       ├─ ABG
       ├─ TS
       └─ MS (korrekter komponente_index)

4. Verifizierung
   ├─ Anzahl Projekte
   ├─ Anzahl WHK-Configs
   └─ Anzahl Testergebnisse pro Komponente
```

---

## Fehlerbehandlung

### Häufige Fehler

#### 1. Encoding-Fehler
**Problem:** Windows-Konsole kann UTF-8 nicht darstellen.

**Lösung:**
```python
import sys
import io
sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer,
    encoding='utf-8',
    errors='replace'
)
```

#### 2. Datum-Parsing-Fehler
**Problem:** Datum im falschen Format.

**Lösung:** Mehrere Formate versuchen.
```python
formats = ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']
for fmt in formats:
    try:
        return datetime.strptime(date_string, fmt).date()
    except ValueError:
        continue
```

#### 3. Constraint-Verletzungen
**Problem:** UNIQUE oder NOT NULL Constraints.

**Häufige Ursachen:**
- Duplikat: WHK mit gleicher Nummer im selben Projekt
- NULL: Pflichtfeld fehlt (z.B. `reihenfolge`)

**Lösung:** Daten vor Import validieren.

#### 4. Fehlende Testfragen
**Problem:** Testfrage mit bestimmter `reihenfolge` existiert nicht.

**Verhalten:**
```python
test_q = TestQuestion.query.filter_by(...).first()
if test_q:
    # Import durchführen
else:
    print(f"Warnung: Testfrage nicht gefunden")
    continue  # Überspringen
```

#### 5. Falscher komponente_index
**Problem:** Frontend findet Daten nicht (z.B. Meteostation).

**Symptom:** Buttons bleiben grau trotz vorhandener Daten.

**Ursache:** `komponente_index` stimmt nicht mit Frontend-Erwartung überein.

**Lösung:** Korrekte Werte verwenden:
- Anlage: `"Anlage"`
- WHK: `"WHK 01"`, `"WHK 02"`, ...
- MS: `"MS 01"` (NICHT `"WHK 01"`)

---

## Verifizierung

### 1. Schnell-Verifizierung (im Script)
```python
def verify():
    with app.app_context():
        projekte = Project.query.count()
        whks = WHKConfig.query.count()
        results = AbnahmeTestResult.query.count()

        print(f"Projekte: {projekte}")
        print(f"WHK-Konfigurationen: {whks}")
        print(f"Testergebnisse: {results}")
```

### 2. Detail-Verifizierung (separates Script)
**Pfad:** `scripts/verify_bowil_import.py`

**Prüft:**
- Projektinformationen vollständig
- WHK-Konfigurationen korrekt
- Anzahl Testergebnisse pro Komponente
- Beispiel-Ergebnisse je Komponente
- Statistik: Richtig/Falsch/Nicht Testbar

### 3. Komponenten-Analyse
**Pfad:** `scripts/analyze_ms_data.py`

**Prüft speziell für eine Komponente:**
- Alle Fragen haben Ergebnisse
- komponente_index ist korrekt
- spalte ist korrekt
- Fehlende Fragen identifizieren

### 4. Vollständiger Bericht
**Pfad:** `scripts/complete_import_report.py`

**Erstellt:**
- Übersicht aller Komponenten
- Anzahl Fragen vs. Anzahl Ergebnisse
- Statistik LSS-CH und WH-LTS
- Fehlende Daten

### Erwartete Werte (Bowil-Projekt)

| Komponente | Fragen | Ergebnisse | Multiplikator |
|---|---:|---:|---|
| Anlage | 16 | 16 | 1 × 1 |
| WHK | 23 | 23 | 1 × 1 |
| Abgang | 29 | 58 | 29 × 2 Abgänge |
| TS | 4 | 4 | 4 × 1 TS |
| MS | 13 | 13 | 13 × 1 MS |
| **TOTAL** | **85** | **114** | |

---

## Anhang

### A. Komponententypen-Mapping

| JSON-Key | DB komponente_typ | Beschreibung |
|---|---|---|
| `ANLAGE` | `Anlage` | WH-Anlage (allgemeine Anlage-Tests) |
| `WHK` | `WHK` | Weichenheizkabinen-Tests |
| `ABG` | `Abgang` | Heizabgänge |
| `TS` | `Temperatursonde` | Temperatursonden |
| `MS` | `Meteostation` | Meteostationen |
| `AH` | `Antriebsheizung` | Antriebsheizungen |

### B. Ergebnis-Werte

| Wert | Bedeutung | Icon | Farbe |
|---|---|---|---|
| `richtig` | Test erfolgreich | ✓ | Grün |
| `falsch` | Test fehlgeschlagen | ✗ | Rot |
| `nicht_testbar` | Nicht testbar | ○ | Gelb |
| `null` | Nicht getestet | - | Grau |

### C. Dateinamen (v2.0)

**Haupt-Scripts:**
- **Generisches Import-Script:** `scripts/import_json_project.py` ⭐ NEU
- **Projekt-Übersicht:** `scripts/show_all_projects.py` ⭐ NEU
- **Batch-Import:** `scripts/import_all_projects.py` ⭐ NEU

**Legacy-Scripts (v1.0):**
- **Bowil-Import (alt):** `scripts/import_bowil_v2.py`
- **Verifizierung:** `scripts/verify_bowil_import.py`

**Analyse-Scripts:**
- **GESE-Analyse:** `scripts/analyze_gese_import.py`
- **GESE-JSON:** `scripts/analyze_gese_json.py`
- **MS-Analyse:** `scripts/analyze_ms_data.py`
- **JSON-Analyse:** `scripts/analyze_json_complete.py`
- **Spalten-Test:** `scripts/test_spalten_mapping.py`

### D. Import-Statistiken (Stand: 20.11.2025)

**Importierte Projekte: 15**

| Nr | Projekt | DIDOK | WHKs | Ergebnisse | Besonderheit |
|---:|---|---|---:|---:|---|
| 1 | Bowil | BOW | 1 | 114 | Einfachste Struktur |
| 2 | Genève-Sécheron | GESE | 7 | 1842 | WHK 02-08 |
| 3 | Sargans | SA | 9 | 1619 | Nicht-sequenziell |
| 4 | Romanshorn | RH | 10 | 1639 | Mit Antriebsheizung |
| 5 | Chavornay | CHV | 3 | 434 | Leere Abgänge |
| 6 | St. Gallen St. Fiden | SGF | 6 | 958 | 2 Meteostationen |
| 7 | Ependes | EP | 1 | 214 | - |
| 8 | Biel Produktionsanlage | BIPO | 9 | 1635 | - |
| 9 | Düdingen | DUED | 3 | 632 | WHK 01A (Suffix) |
| 10 | Zäziwil | ZAE | 1 | 114 | - |
| 11 | Riddes | RID | 2 | 315 | - |
| 12 | Emmenmatt | EMM | 1 | 114 | - |
| 13 | Obermatt | OM | 1 | 114 | - |
| 14 | Signau | SIGN | 2 | 199 | - |
| 15 | Granges-Lens | GRAL | 1 | 0 | Keine Testdaten ⚠ |

**Gesamt-Statistik:**
- Projekte: **15**
- WHK-Konfigurationen: **57**
- Testergebnisse: **9943**

**Komponentenverteilung (gesamt):**
- Anlage: ~240 Ergebnisse (15 Projekte × 16 Fragen)
- WHK: ~1300 Ergebnisse
- Abgang: ~7000 Ergebnisse (größter Anteil)
- Temperatursonde: ~220 Ergebnisse
- Meteostation: ~180 Ergebnisse
- Antriebsheizung: ~6 Ergebnisse (nur Romanshorn)

### E. Wichtige Erkenntnisse

1. **ANLAGE hat spezielles Spalten-Mapping** (C→LSS-CH statt A→LSS-CH)
2. **Meteostation braucht komponente_index=MS-Name** (nicht WHK-Nr)
3. **WHK-Komponente hat mehrere WHK-Indizes** (in Spalten, ähnlich wie Abgänge) ⭐ NEU
4. **WHK-Nummern aus Konfiguration lesen** (nicht berechnen) ⭐ NEU
5. **safe_int() für robuste Datenverarbeitung** (leere Strings) ⭐ NEU
6. **Mehrere Instanzen erzeugen mehrere Datensätze** (1 Frage → n Results)
7. **Frage-Index (JSON) ≠ Reihenfolge (DB)** (0-basiert vs. 1-basiert)
8. **Spalte ist für Meteostation = Meteostation-Name** (nicht None)
9. **Nicht-sequenzielle WHK-Nummern möglich** (z.B. 10, 20, 30, 40, 51, 60, 70, 86, 90) ⭐ NEU
10. **Buchstaben-Suffixe in WHK-Nummern** (z.B. WHK 01A) ⭐ NEU

---

**Ende des Berichts**

*Dokumentation erstellt mit Claude Code. Version 2.0 - Stand: 20.11.2025*
