# Export-System Dokumentation

## Übersicht

Das Export-System ermöglicht strukturierte PDF- und Excel-Exporte von Abnahmetest-Protokollen mit flexibler Sektion-Auswahl.

### Architektur: 3-Stufen-Workflow

```
┌──────────────────┐
│  /export         │  Stufe 1: Projektauswahl
│  (Übersicht)     │  - Alle Projekte mit Live-Suche
└────────┬─────────┘  - "Exportieren" Button pro Projekt
         │
         ▼
┌──────────────────┐
│  /export/projekt │  Stufe 2: Konfiguration
│  /<id>           │  - Sektion-Auswahl (Deckblatt, WHKs, Meteostationen)
└────────┬─────────┘  - Format-Wahl (PDF/Excel)
         │
         ▼
┌──────────────────┐
│  /export/generate│  Stufe 3: Generierung
│  (POST)          │  - Export-Erstellung basierend auf Auswahl
└──────────────────┘  - Download-Datei mit intelligentem Namen
```

## Routen

### GET `/export` - Export-Übersicht

**Zweck:** Zeigt alle Projekte mit Export-Option

**Parameter:** Keine

**Template:** `templates/export.html`

**Features:**
- Clientseitige Live-Suche (JavaScript)
- Tabelle: Energie, Projektname, DIDOK, Exportieren-Button
- Dark Mode optimiert

**Code:**
```python
@app.route('/export')
def export():
    """Export-Übersichtsseite mit allen Projekten."""
    projekte = Project.query.order_by(Project.erstellt_am.desc()).all()
    return render_template('export.html', projekte=projekte)
```

---

### GET `/export/projekt/<int:projekt_id>` - Export-Konfiguration

**Zweck:** Sektion-Auswahl für spezifisches Projekt

**Parameter:**
- `projekt_id` (int): Projekt-ID

**Template:** `templates/export_config.html`

**Features:**
- Flexible Sektion-Auswahl:
  - ☐ Deckblatt (optional)
  - ☐ WH-Anlage (optional)
  - ☐ Einzelne WHKs (individuell)
  - ☐ Einzelne Meteostationen (individuell)
- "Alle auswählen" / "Alle abwählen" Buttons
- Format-Wahl: PDF oder Excel
- Validierung: Mindestens 1 Sektion erforderlich

**Code:**
```python
@app.route('/export/projekt/<int:projekt_id>')
def export_config(projekt_id):
    """Export-Konfiguration für Projekt."""
    projekt = Project.query.get_or_404(projekt_id)
    whk_configs = WHKConfig.query.filter_by(projekt_id=projekt_id).order_by(WHKConfig.whk_nummer).all()

    # Ermittle eindeutige Meteostationen
    meteostation_dict = {}
    for whk in whk_configs:
        if whk.meteostation:
            meteostation_name = whk.meteostation.strip()
            if meteostation_name:
                if meteostation_name not in meteostation_dict:
                    meteostation_dict[meteostation_name] = []
                meteostation_dict[meteostation_name].append(whk.whk_nummer)

    # Erstelle Liste mit Meteostation-Informationen
    meteo_stations = [
        {
            'name': name,
            'whk_count': len(whk_list),
            'whk_numbers': whk_list
        }
        for name, whk_list in sorted(meteostation_dict.items())
    ]

    return render_template('export_config.html',
                         projekt=projekt,
                         whk_configs=whk_configs,
                         meteo_stations=meteo_stations,
                         has_meteostationen=len(meteo_stations) > 0)
```

---

### POST `/export/generate` - Export-Generierung

**Zweck:** Generiert PDF oder Excel basierend auf Auswahl

**Parameter (Form Data):**
- `projekt_id` (int): Projekt-ID
- `export_format` (str): 'pdf' oder 'excel'
- `selected_sections` (list): Liste gewählter Sektionen
  - `'deckblatt'`
  - `'wh_anlage'`
  - `'whk_WHK_01'`, `'whk_WHK_02'`, ...
  - `'meteostation_MS 01'`, `'meteostation_MS 02'`, ...

**Rückgabe:** Datei-Download (PDF oder XLSX)

**Validierung:**
- Projekt muss existieren
- Mindestens 1 Sektion ausgewählt
- Format muss 'pdf' oder 'excel' sein

**Code:**
```python
@app.route('/export/generate', methods=['POST'])
def export_generate():
    """Generiert Export basierend auf Auswahl."""
    projekt_id = request.form.get('projekt_id')
    export_format = request.form.get('export_format', 'pdf')
    selected_sections = request.form.getlist('selected_sections')

    # Validierung
    if not selected_sections:
        flash('Bitte wählen Sie mindestens eine Sektion aus.', 'error')
        return redirect(url_for('export_config', projekt_id=projekt_id))

    if export_format == 'pdf':
        return generate_pdf_export(projekt_id, selected_sections)
    elif export_format == 'excel':
        return generate_excel_export(projekt_id, selected_sections)
```

**Dateinamen-Generierung:**
```python
def generate_filename(projekt, selected_sections, format_ext):
    """Intelligente Dateinamen basierend auf Auswahl."""
    # Basis: Projektname_Datum
    base = f"{projekt.projektname.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"

    # Füge Sektion-Info hinzu
    section_names = []
    if 'deckblatt' in selected_sections:
        section_names.append('Deckblatt')
    if 'wh_anlage' in selected_sections:
        section_names.append('WH-Anlage')

    # WHKs
    whk_names = [s.replace('whk_', '') for s in selected_sections if s.startswith('whk_')]
    if whk_names:
        section_names.append(f"{len(whk_names)}-WHKs")

    # Meteostationen
    meteo_names = [s.replace('meteostation_', '') for s in selected_sections if s.startswith('meteostation_')]
    if meteo_names:
        section_names.extend([f'Meteo-{name}' for name in meteo_names])

    # Kombiniere alles
    if section_names:
        return f"{base}_{'-'.join(section_names)}.{format_ext}"
    return f"{base}_Abnahmetest.{format_ext}"
```

## PDF-Export

### Template: `templates/pdf_abnahmetest.html`

**Bedingte Sektion-Filterung:**
```html
<!-- Deckblatt nur wenn ausgewählt -->
{% if 'deckblatt' in selected_sections %}
<h1>Abnahmetest Elektroweichenheizung</h1>
<!-- Deckblatt-Inhalt -->
<div class="page-break"></div>
{% endif %}

<!-- WHKs nur wenn ausgewählt -->
{% for whk in whk_data %}
    {% if ('whk_' + whk.whk_nummer|replace(' ', '_')) in selected_sections %}
    <!-- WHK-Inhalt -->
    {% endif %}
{% endfor %}

<!-- Meteostationen nur wenn ausgewählt -->
{% for meteo in meteo_data %}
    {% if ('meteostation_' + meteo.meteostation) in selected_sections %}
    <!-- Meteostation-Inhalt -->
    {% endif %}
{% endfor %}
```

### WeasyPrint-Integration

**Dependencies:**
- WeasyPrint 66.0
- GTK3-Runtime (Windows)

**Code:**
```python
from weasyprint import HTML

def generate_pdf_export(projekt_id, selected_sections):
    # Daten laden
    projekt = Project.query.get_or_404(projekt_id)

    # Template rendern mit selected_sections
    html_string = render_template('pdf_abnahmetest.html',
                                 projekt=projekt,
                                 selected_sections=selected_sections,
                                 # ... weitere Daten)

    # PDF generieren
    pdf = HTML(string=html_string).write_pdf()

    # Dateinamen generieren
    filename = generate_filename(projekt, selected_sections, 'pdf')

    # Download
    return send_file(BytesIO(pdf),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=filename)
```

## Excel-Export

### openpyxl-Integration

**Sheet-Struktur:**
- **Deckblatt** (falls `'deckblatt'` in selected_sections)
- **WH-Anlage** (falls `'wh_anlage'` in selected_sections)
- **WHK 01**, **WHK 02**, ... (individuell)
- **Meteo MS 01**, **Meteo MS 02**, ... (individuell)

**Code:**
```python
from openpyxl import Workbook

def generate_excel_export(projekt_id, selected_sections):
    projekt = Project.query.get_or_404(projekt_id)
    wb = Workbook()
    wb.remove(wb.active)  # Entferne Default-Sheet

    # Sheet 1: Deckblatt (konditional)
    if 'deckblatt' in selected_sections:
        ws = wb.create_sheet("Deckblatt")
        ws['A1'] = f"Abnahmetest {projekt.energie}"
        ws['A3'] = "Projektname:"
        ws['B3'] = projekt.projektname
        # ... weitere Felder

    # WHK-Sheets (konditional)
    whk_configs = WHKConfig.query.filter_by(projekt_id=projekt_id).all()
    for whk in whk_configs:
        whk_key = f"whk_{whk.whk_nummer.replace(' ', '_')}"
        if whk_key in selected_sections:
            ws = wb.create_sheet(f"WHK {whk.whk_nummer[:23]}")
            # ... WHK-Daten

    # Meteostation-Sheets (konditional)
    meteostationen = set([whk.meteostation for whk in whk_configs if whk.meteostation])
    for meteo_name in sorted(meteostationen):
        meteo_key = f"meteostation_{meteo_name}"
        if meteo_key in selected_sections:
            ws = wb.create_sheet(f"Meteo {meteo_name[:23]}")
            # ... Meteo-Daten

    # In Memory speichern
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # Dateinamen generieren
    filename = generate_filename(projekt, selected_sections, 'xlsx')

    # Download
    return send_file(output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=filename)
```

## JavaScript-Komponenten

### Live-Suche (export.html)

**Features:**
- `input`-Event-Listener für Echtzeit-Filterung
- DOM-Manipulation (display: none/block)
- Ergebnis-Zähler
- Zurücksetzen-Button (dynamisch einblenden)

**Code:**
```javascript
const searchInput = document.getElementById('searchInput');
const projectRows = document.querySelectorAll('.project-table tbody tr');

searchInput.addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase().trim();
    let visibleCount = 0;

    projectRows.forEach(row => {
        const projektname = row.cells[1]?.textContent.toLowerCase() || '';
        const didok = row.cells[2]?.textContent.toLowerCase() || '';
        const matches = projektname.includes(searchTerm) || didok.includes(searchTerm);

        row.style.display = matches || searchTerm === '' ? '' : 'none';
        if (matches || searchTerm === '') visibleCount++;
    });

    // Update Ergebnis-Zähler
    searchInfo.textContent = searchTerm ?
        `${visibleCount} Projekt${visibleCount !== 1 ? 'e' : ''} gefunden` : '';
});
```

### Sektion-Auswahl (export_config.html)

**Features:**
- "Alle auswählen" / "Alle abwählen" Buttons
- Validierung (mindestens 1 Sektion)
- Export-Button Enable/Disable

**Code:**
```javascript
const checkboxes = document.querySelectorAll('input[name="selected_sections"]');
const exportBtn = document.getElementById('export-btn');
const validationMessage = document.getElementById('validation-message');

// Alle auswählen
document.getElementById('select-all-btn').addEventListener('click', function() {
    checkboxes.forEach(cb => cb.checked = true);
    updateExportButton();
});

// Alle abwählen
document.getElementById('deselect-all-btn').addEventListener('click', function() {
    checkboxes.forEach(cb => cb.checked = false);
    updateExportButton();
});

// Export-Button Status
function updateExportButton() {
    const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
    exportBtn.disabled = !anyChecked;
    validationMessage.style.display = anyChecked ? 'none' : 'block';
}

checkboxes.forEach(cb => cb.addEventListener('change', updateExportButton));

// Form-Validierung
document.getElementById('export-form').addEventListener('submit', function(e) {
    const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
    if (!anyChecked) {
        e.preventDefault();
        validationMessage.style.display = 'block';
        return false;
    }
    return true;
});
```

## Fehlerbehandlung

### Validierung

```python
# Projekt existiert?
projekt = Project.query.get_or_404(projekt_id)

# Mindestens 1 Sektion?
if not selected_sections:
    flash('Bitte wählen Sie mindestens eine Sektion aus.', 'error')
    return redirect(url_for('export_config', projekt_id=projekt_id))

# Gültiges Format?
if export_format not in ['pdf', 'excel']:
    flash('Ungültiges Export-Format.', 'error')
    return redirect(url_for('export_config', projekt_id=projekt_id))
```

### PDF-spezifische Fehler

```python
try:
    pdf = HTML(string=html_string).write_pdf()
except ImportError:
    flash('WeasyPrint ist nicht installiert. Nutzen Sie den Excel-Export.', 'error')
    return redirect(url_for('export_config', projekt_id=projekt_id))
except Exception as e:
    flash(f'PDF-Generierung fehlgeschlagen: {str(e)}', 'error')
    return redirect(url_for('export_config', projekt_id=projekt_id))
```

## Customization

### Neue Sektion hinzufügen

1. **Checkbox in export_config.html:**
```html
<label class="checkbox-item">
    <input type="checkbox" name="selected_sections" value="neue_sektion" checked>
    <span class="checkbox-label">
        <strong>Neue Sektion</strong>
        <small>Beschreibung</small>
    </span>
</label>
```

2. **Bedingte Logik in generate_pdf_export():**
```python
if 'neue_sektion' in selected_sections:
    # Daten laden
    neue_daten = NeuesDatenModell.query.filter_by(projekt_id=projekt_id).all()
    # An Template übergeben
```

3. **Template-Block in pdf_abnahmetest.html:**
```html
{% if 'neue_sektion' in selected_sections %}
<h2>Neue Sektion</h2>
<!-- Inhalt -->
{% endif %}
```

### Export-Format erweitern

1. **Neue Option in export_config.html:**
```html
<label class="radio-item">
    <input type="radio" name="export_format" value="csv">
    <span class="radio-label">
        <strong>CSV-Export</strong>
        <small>Komma-getrennte Werte</small>
    </span>
</label>
```

2. **Route erweitern:**
```python
@app.route('/export/generate', methods=['POST'])
def export_generate():
    # ...
    elif export_format == 'csv':
        return generate_csv_export(projekt_id, selected_sections)
```

3. **Generator-Funktion:**
```python
def generate_csv_export(projekt_id, selected_sections):
    import csv
    # CSV-Logik
    return send_file(output, mimetype='text/csv', ...)
```

## Testing

### Manuelle Test-Szenarien

1. **Export mit allen Sektionen**
   - Alle Checkboxen auswählen
   - PDF exportieren → Alle Sektionen vorhanden?
   - Excel exportieren → Alle Sheets vorhanden?

2. **Export nur Deckblatt**
   - Nur Deckblatt auswählen
   - Export → Nur Deckblatt im Dokument?

3. **Export einzelne WHKs**
   - WHK 01 und WHK 03 auswählen (nicht WHK 02)
   - Export → Nur ausgewählte WHKs vorhanden?

4. **Export einzelne Meteostationen**
   - Meteostation MS 01 auswählen
   - Export → Nur MS 01 vorhanden?

5. **Validierung: Keine Sektion**
   - Alle Checkboxen abwählen
   - Export-Button disabled?
   - Submit verhindert?

6. **Live-Suche**
   - Begriff eingeben → Sofortige Filterung?
   - Zurücksetzen-Button → Löscht Suche?
   - Escape-Taste → Löscht Suche?

7. **Dateinamen**
   - Verschiedene Sektion-Kombinationen
   - Dateiname korrekt generiert?
   - Keine Sonderzeichen-Probleme?

### Edge Cases

- **Projekt ohne WHKs:** Export sollte nur Deckblatt/WH-Anlage anbieten
- **Projekt ohne Meteostationen:** Meteostation-Sektion nicht anzeigen
- **Sehr lange Projektnamen:** Dateiname-Truncating testen
- **Sonderzeichen in Namen:** Sanitizing testen
- **Keine Testdaten:** Leere Tabellen korrekt darstellen

### Performance

- **100+ Projekte:** Live-Suche performant?
- **Projekt mit 10 WHKs:** Export-Generierung < 5 Sekunden?
- **Excel mit allen Sheets:** Datei < 5 MB?
- **Concurrent Exports:** Mehrere User gleichzeitig?

---

**Version:** 1.0
**Letzte Aktualisierung:** 2025-01-12
**Autor:** Development Team
