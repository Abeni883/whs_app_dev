# Changelog - Session 2025-11-03

## Zusammenfassung

Diese Session beinhaltete umfangreiche Bugfixes für den PDF-Export des Abnahmetest-Protokolls. Hauptprobleme waren:
1. Doppelte "WHK" in Titeln
2. Fehlende Test-Ergebnis-Icons im PDF
3. Layout-Anpassungen (WHK-Spalte entfernen, Icon-Größen)

---

## 🔧 Behobene Bugs

### Bug #1: Doppeltes "WHK" in Titeln

**Problem:**
- Titel zeigten "Abnahmetest WHK WHK 01" statt "Abnahmetest WHK 01"
- Betraf alle WHK-bezogenen Komponenten (WHK, Abgänge, TS, AH)

**Ursache:**
- Template fügte statisches "WHK" hinzu, obwohl `whk.whk_nummer` bereits "WHK 01" enthält

**Lösung:**
- **Datei:** `templates/pdf_abnahmetest.html`
- **Zeilen:** 397, 432, 464, 492
- **Änderung:**
  ```html
  <!-- VORHER: -->
  <h1>Abnahmetest WHK {{ whk.whk_nummer }}</h1>

  <!-- NACHHER: -->
  <h1>Abnahmetest {{ whk.whk_nummer }}</h1>
  ```

---

### Bug #2: Icons werden nicht im PDF angezeigt (KRITISCH)

**Problem:**
- Alle Test-Ergebnis-Icons (✓, ✗, ⊘) waren leer im PDF
- Betraf WHK-Tests, Abgang-Tests, TS-Tests, AH-Tests, Meteostation, Anlage

**Symptome:**
```
| Test | WHK | WH-LTS | LSS-CH | Bemerkung |
| F11  |     |        |        |           |  ❌ Alle Icons leer
```

**Debug-Prozess:**

1. **Datenbank-Analyse:**
   - ✅ 18 Test-Ergebnisse für WHK 01 vorhanden
   - ✅ Werte: 'richtig', 'falsch'
   - ✅ Icon-Generierung funktioniert

2. **Problem identifiziert - Key-Matching-Fehler:**

**Root Cause:**

Die `get_test_result()` Funktion erhielt falsche Parameter, wodurch nicht-existierende Keys in `results_dict` gesucht wurden.

**Beispiel WHK-Tests:**

```python
# Datenbank-Struktur:
komponente_index = 'WHK 01'
spalte = ''  # LEER!

# Resultierende Key in results_dict:
key = "3_wh_lts_WHK 01_"  # Mit leerem Suffix

# CODE VORHER (FALSCH):
get_test_result(frage.id, 'wh_lts', whk_nummer, whk_nummer)
#                                    ^^^^^^^^  ^^^^^^^^
#                                    'WHK 01'  'WHK 01'

# Gesuchter Key (EXISTIERT NICHT):
key = "3_wh_lts_WHK 01_WHK 01"  ❌

# CODE NACHHER (RICHTIG):
get_test_result(frage.id, 'wh_lts', whk_nummer, '')
#                                    ^^^^^^^^  ^^
#                                    'WHK 01'  leer

# Gesuchter Key (EXISTIERT):
key = "3_wh_lts_WHK 01_"  ✅
```

**Lösung:**

**Datei:** `app.py`

#### 1. Anlage-Tests (Zeilen 817-818)
```python
# VORHER:
wh_lts_result = get_test_result(frage.id, 'wh_lts', 'Anlage', 'Anlage')
lss_ch_result = get_test_result(frage.id, 'lss_ch', 'Anlage', 'Anlage')

# NACHHER:
wh_lts_result = get_test_result(frage.id, 'wh_lts', '', '')  # Beide leer für Anlage
lss_ch_result = get_test_result(frage.id, 'lss_ch', '', '')  # Beide leer für Anlage
```

#### 2. WHK-Tests (Zeilen 836-837)
```python
# VORHER:
wh_lts_result = get_test_result(frage.id, 'wh_lts', whk_nummer, whk_nummer)
lss_ch_result = get_test_result(frage.id, 'lss_ch', whk_nummer, whk_nummer)

# NACHHER:
wh_lts_result = get_test_result(frage.id, 'wh_lts', whk_nummer, '')  # Spalte leer
lss_ch_result = get_test_result(frage.id, 'lss_ch', whk_nummer, '')  # Spalte leer
```

#### 3. Meteostation-Tests (Zeilen 916-917)
```python
# VORHER:
wh_lts_result = get_test_result(frage.id, 'wh_lts', meteo_station, meteo_station)
lss_ch_result = get_test_result(frage.id, 'lss_ch', meteo_station, meteo_station)

# NACHHER:
wh_lts_result = get_test_result(frage.id, 'wh_lts', meteo_station, '')  # Spalte leer
lss_ch_result = get_test_result(frage.id, 'lss_ch', meteo_station, '')  # Spalte leer
```

**Nicht geändert (waren bereits korrekt):**
- ✅ Abgang-Tests: `get_test_result(..., whk_nummer, abgang_name)`
- ✅ Temperatursonden: `get_test_result(..., whk_nummer, ts_name)`
- ✅ Antriebsheizung: `get_test_result(..., whk_nummer, 'Antriebsheizung')`

---

### Bug #3: WHK-Icon-Spalte ohne Datenquelle

**Problem:**
- Template hatte 5 Spalten (Test, WHK, WH-LTS, LSS-CH, Bemerkung)
- Datenbank hat nur `wh_lts_result` und `lss_ch_result` Spalten
- **KEINE** `whk_result` Spalte in DB vorhanden

**Temporäre Lösung (während Debug):**
```python
# app.py - WHK-Icons zeigten WH-LTS Werte
'whk_icon': wh_lts_result['icon']  # WHK = WH-LTS Duplikat
```

**Finale Lösung:**
- User entschied: WHK-Spalte komplett entfernen
- Siehe Feature #1 unten

---

## ✨ Neue Features / Änderungen

### Feature #1: WHK-Spalte entfernt

**Anforderung:**
- User Request: "Die WHK Spalte muss entfernt werden"

**Implementierung:**

**Datei:** `templates/pdf_abnahmetest.html`

#### Template-Änderung (Zeilen 402-420)
```html
<!-- VORHER (5 Spalten): -->
<table class="test-table">
    <thead>
        <tr>
            <th class="col-test">Test</th>
            <th class="col-system">WHK</th>
            <th class="col-system">WH-LTS</th>
            <th class="col-system">LSS-CH</th>
            <th class="col-bemerkung">Bemerkung</th>
        </tr>
    </thead>
    <tbody>
        {% for test in whk.whk_tests %}
        <tr>
            <td>{{ test.frage_text }}</td>
            <td style="text-align: center;">{{ test.whk_icon|safe }}</td>
            <td style="text-align: center;">{{ test.wh_lts_icon|safe }}</td>
            <td style="text-align: center;">{{ test.lss_ch_icon|safe }}</td>
            <td>{{ test.bemerkung }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<!-- NACHHER (4 Spalten): -->
<table class="test-table">
    <thead>
        <tr>
            <th class="col-test">Test</th>
            <th class="col-system">WH-LTS</th>
            <th class="col-system">LSS-CH</th>
            <th class="col-bemerkung">Bemerkung</th>
        </tr>
    </thead>
    <tbody>
        {% for test in whk.whk_tests %}
        <tr>
            <td>{{ test.frage_text }}</td>
            <td style="text-align: center;">{{ test.wh_lts_icon|safe }}</td>
            <td style="text-align: center;">{{ test.lss_ch_icon|safe }}</td>
            <td>{{ test.bemerkung }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

#### CSS-Anpassung (Zeilen 247-259)
```css
/* VORHER (5-Spalten-Layout): */
.col-test {
    width: 45%;
}

.col-system {
    width: 11%;
    text-align: center;
}

.col-bemerkung {
    width: 22%;
}
/* Gesamt: 45% + 11% + 11% + 11% + 22% = 100% */

/* NACHHER (4-Spalten-Layout): */
.col-test {
    width: 50%;      /* +5% mehr Platz */
}

.col-system {
    width: 13%;      /* +2% mehr Platz */
    text-align: center;
}

.col-bemerkung {
    width: 24%;      /* +2% mehr Platz */
}
/* Gesamt: 50% + 13% + 13% + 24% = 100% */
```

---

### Feature #2: Icon-Größen reduziert

**Anforderung:**
- User Request: "Checkboxen um 50% reduzieren, wie auf der Titelseite"

**Implementierung:**

**Datei:** `templates/pdf_abnahmetest.html`
**Zeilen:** 205-215

```css
/* VORHER: */
.check-icon {
    width: 28px;
    height: 28px;
    vertical-align: middle;
}

table.legend-table .check-icon {
    width: 32px;
    height: 32px;
}

/* NACHHER: */
.check-icon {
    width: 14px;     /* 50% Reduktion von 28px */
    height: 14px;    /* 50% Reduktion von 28px */
    vertical-align: middle;
}

table.legend-table .check-icon {
    width: 16px;     /* Konsistent mit inline styles */
    height: 16px;    /* Konsistent mit inline styles */
}
```

**Icon-Größen Übersicht:**

| Ort | Vorher | Nachher | Änderung |
|-----|--------|---------|----------|
| Test-Tabellen | 28px | 14px | -50% |
| Legende | 32px (CSS) / 16px (inline) | 16px | Vereinheitlicht |

---

## 📁 Geänderte Dateien

### 1. `app.py`

**Funktion:** `export_pdf(projekt_id)`

**Zeilen:**
- 817-818: Anlage-Tests Key-Parameter korrigiert
- 836-837: WHK-Tests Key-Parameter korrigiert
- 916-917: Meteostation-Tests Key-Parameter korrigiert

**Änderungen:**
- ❌ Entfernt: Doppelte/falsche Parameter in `get_test_result()`
- ✅ Hinzugefügt: Korrekte leere Spalten-Parameter

---

### 2. `templates/pdf_abnahmetest.html`

**Zeilen:**
- 205-215: CSS - Icon-Größen reduziert
- 247-259: CSS - Spaltenbreiten für 4-Spalten-Layout angepasst
- 397: Titel - Doppeltes "WHK" entfernt (WHK-Tests Hauptseite)
- 402-420: Template - WHK-Spalte aus Tabelle entfernt
- 432: Titel - Doppeltes "WHK" entfernt (Abgänge)
- 464: Titel - Doppeltes "WHK" entfernt (Temperatursonden)
- 492: Titel - Doppeltes "WHK" entfernt (Antriebsheizung)

**Änderungen:**
- ❌ Entfernt: WHK-Spalte aus WHK-Tests Tabelle
- ❌ Entfernt: Statisches "WHK" aus Titeln
- ✅ Hinzugefügt: Optimierte CSS-Spaltenbreiten
- ✅ Hinzugefügt: Kleinere Icon-Größen (50% Reduktion)

---

## 🧪 Debug-Scripts (temporär erstellt & gelöscht)

### 1. `debug_pdf_icons.py`
- **Zweck:** MySQL Datenbank-Analyse
- **Ergebnis:** 18 Test-Ergebnisse für WHK 01 gefunden
- **Status:** Gelöscht nach erfolgreicher Analyse

### 2. `debug_test_data.py`
- **Zweck:** Systematische DB-Prüfung mit Icon-Simulation
- **Ergebnis:** Key-Matching-Problem identifiziert
- **Status:** Gelöscht nach erfolgreicher Diagnose

---

## 📊 Datenbank-Schema (Referenz)

### `abnahme_test_results` Tabelle

**Relevante Spalten:**
```sql
id                   INT PRIMARY KEY
projekt_id           INT
test_question_id     INT
komponente_index     VARCHAR(50)   -- z.B. 'WHK 01', 'MS 01A', ''
spalte               VARCHAR(100)  -- z.B. 'Abgang 01', 'TS 02', ''
lss_ch_result        VARCHAR(20)   -- 'richtig', 'falsch', 'nicht_testbar'
wh_lts_result        VARCHAR(20)   -- 'richtig', 'falsch', 'nicht_testbar'
lss_ch_bemerkung     TEXT
wh_lts_bemerkung     TEXT
```

**WICHTIG:** Es gibt **KEINE** `whk_result` Spalte!

---

## 🔑 Key-Format in results_dict

**Format:**
```
{question_id}_{system}_{komponente_index}_{spalte}
```

**Beispiele:**

| Komponente | komponente_index | spalte | Key |
|------------|-----------------|--------|-----|
| Anlage | '' | '' | `1_wh_lts__` |
| WHK | 'WHK 01' | '' | `3_wh_lts_WHK 01_` |
| Abgang | 'WHK 01' | 'Abgang 01' | `5_wh_lts_WHK 01_Abgang 01` |
| TS | 'WHK 01' | 'TS 02' | `7_wh_lts_WHK 01_TS 02` |
| AH | 'WHK 01' | 'Antriebsheizung' | `9_wh_lts_WHK 01_Antriebsheizung` |
| Meteostation | 'MS 01A' | '' | `11_wh_lts_MS 01A_` |

---

## 🎯 Testing

### Test-Daten
- **Projekt ID:** 4
- **Projektname:** Test-Anlage Testikon
- **WHK-Konfigurationen:** 3 (WHK 01, WHK 02, WHK 03)
- **Test-Ergebnisse:** 58 Datensätze

### Test-URLs
```
http://localhost:5000/projekt/4/abnahmetest
http://localhost:5000/projekt/4/export/pdf
http://localhost:5000/projekt/4/export/excel
```

### Verifizierte Funktionalität
- ✅ Icons werden in allen Tabellen angezeigt
- ✅ Korrekte Titel ohne doppeltes "WHK"
- ✅ 4-Spalten-Layout (ohne WHK-Spalte)
- ✅ Icons in korrekter Größe (14px in Tabellen)
- ✅ Seiten-Struktur: Jede Komponente auf eigener Seite
- ✅ Header/Footer auf allen Seiten

---

## 📈 Performance

**Keine Performance-Änderungen:**
- Logik-Änderungen haben keinen Einfluss auf Ausführungszeit
- Template-Änderungen minimal (CSS, HTML-Struktur)

---

## 🔄 Migrations-Status

**Keine Migrations erforderlich:**
- Alle Änderungen betreffen nur Code/Templates
- Datenbank-Schema unverändert
- Bestehende Daten kompatibel

---

## 🐛 Bekannte Einschränkungen

### SQLAlchemy Warnings
```python
LegacyAPIWarning: The Query.get() method is considered legacy
```
- **Status:** Warnung (kein Fehler)
- **Empfehlung:** Migration zu `Session.get()` (SQLAlchemy 2.0)
- **Priorität:** Niedrig (funktioniert weiterhin)

### WeasyPrint Windows-Spezifisch
```
GLib-GIO-WARNING: Unexpectedly, UWP app ... supports extensions but has no verbs
```
- **Status:** Windows-spezifische Warnung
- **Auswirkung:** Keine (PDF wird korrekt generiert)

---

## 📝 Lessons Learned

1. **Debug-First Approach:**
   - Systematische DB-Analyse bevor Code-Änderungen
   - Keys in Dictionary müssen exakt mit DB-Struktur übereinstimmen

2. **Template vs. Backend:**
   - Template kann keine Daten erfinden
   - Backend muss korrekte Daten liefern (Icons als HTML)

3. **Key-Matching:**
   - Trailing Underscores sind signifikant
   - `'WHK 01_'` ≠ `'WHK 01_WHK 01'`

4. **CSS Specificity:**
   - Inline styles überschreiben CSS-Klassen
   - Beide müssen konsistent sein

---

## 🚀 Nächste Schritte (Optional)

### Refactoring-Vorschläge:

1. **Icon-Generierung vereinheitlichen:**
   ```python
   # Zentralisierte Icon-Funktion
   def generate_icon_html(result_value, size='normal'):
       sizes = {'small': 14, 'normal': 16, 'large': 28}
       icon_size = sizes.get(size, 16)
       # ... Icon-HTML generieren
   ```

2. **Key-Generierung abstrahieren:**
   ```python
   def generate_result_key(question_id, system, komponente_index, spalte=''):
       return f"{question_id}_{system}_{komponente_index}_{spalte}"
   ```

3. **SQLAlchemy 2.0 Migration:**
   ```python
   # Ersetze:
   projekt = Project.query.get(projekt_id)

   # Mit:
   projekt = db.session.get(Project, projekt_id)
   ```

---

## 👥 Credits

**Session-Datum:** 2025-11-03
**Entwickler:** Claude Code (Anthropic)
**Reviewer:** Nicolas Abé

---

## 📌 Version

**App-Version:** Unverändert
**DB-Version:** Unverändert
**Template-Version:** 3.1 (inoffiziell)

---

## 🔗 Referenzen

- **Original PDF:** Obermatt-Referenz (Screenshot-basiert)
- **Datenmodell:** `models.py` - `AbnahmeTestResult`
- **Test-Generator:** `generate_test_data.py`
- **Flask-Version:** 3.1.2
- **WeasyPrint-Version:** (siehe requirements.txt)

---

**Ende des Changelogs**
