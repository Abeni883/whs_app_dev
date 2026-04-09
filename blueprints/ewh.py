"""
SBB Weichenheizung - EWH Blueprint
Elektroweichenheizung Abnahmetests
"""
import json
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required

from models import db, Project, TestQuestion, AbnahmeTestResult, WHKConfig, EWHMeteostation

ewh_bp = Blueprint('ewh', __name__)


# ==================== HELPER FUNCTIONS ====================

def normalize_komponente_nummer(nummer, prefix='WHK'):
    """
    Normalisiert eine Komponenten-Nummer auf das Standard-Format "PREFIX XX".

    Eingabe-Formate:
    - "01" → "PREFIX 01"
    - "PREFIX 01" → "PREFIX 01"
    - "PREFIX_01" → "PREFIX 01"

    Args:
        nummer: Die zu normalisierende Nummer
        prefix: Der Prefix (z.B. 'WHK', 'MS')

    Returns:
        str: Normalisierte Nummer im Format "PREFIX XX"
    """
    if not nummer:
        return nummer

    nummer = str(nummer).strip()

    # Ersetze Unterstriche durch Leerzeichen
    nummer = nummer.replace('_', ' ')

    # Wenn es nur eine Nummer ist (z.B. "01"), füge Prefix hinzu
    if not nummer.upper().startswith(prefix.upper()):
        nummer = f'{prefix} {nummer}'

    return nummer


def normalize_whk_nummer(whk_nummer):
    """Normalisiert eine WHK-Nummer auf das Standard-Format "WHK XX"."""
    return normalize_komponente_nummer(whk_nummer, 'WHK')


def normalize_ms_nummer(ms_nummer):
    """Normalisiert eine Meteostation-Nummer auf das Standard-Format "MS XX"."""
    return normalize_komponente_nummer(ms_nummer, 'MS')


def get_komponente_variants(nummer, prefix='WHK'):
    """
    Generiert alle möglichen Varianten einer Komponenten-Nummer für DB-Abfragen.

    Eingabe: "WHK 01" oder "01" oder "WHK_01" oder "WHK01"
    Ausgabe: ["WHK 01", "WHK_01", "WHK01", "01"]

    Args:
        nummer: Die Komponenten-Nummer
        prefix: Der Prefix (z.B. 'WHK', 'MS')

    Dies ermöglicht das Finden von Daten, die mit verschiedenen Formaten gespeichert wurden.
    """
    variants = set()

    # Normalisiere zuerst
    normalized = normalize_komponente_nummer(nummer, prefix)
    variants.add(normalized)

    # Variante mit Unterstrich
    variants.add(normalized.replace(' ', '_'))

    # Variante ohne Leerzeichen (z.B. "MS01")
    variants.add(normalized.replace(' ', ''))

    # Nur die Nummer (ohne Prefix)
    prefix_space = f'{prefix} '
    if normalized.upper().startswith(prefix_space.upper()):
        nummer_only = normalized[len(prefix_space):]
        variants.add(nummer_only)
        # Auch ohne führende Nullen (z.B. "1" statt "01")
        variants.add(nummer_only.lstrip('0') or '0')

    # Original auch hinzufügen
    variants.add(nummer)

    return list(variants)


def get_whk_spalte_variants(whk_nummer):
    """Generiert alle möglichen Varianten einer WHK-Nummer."""
    return get_komponente_variants(whk_nummer, 'WHK')


def get_ms_spalte_variants(ms_nummer):
    """Generiert alle möglichen Varianten einer Meteostation-Nummer."""
    return get_komponente_variants(ms_nummer, 'MS')


def apply_presets_to_ergebnisse(testfragen, ergebnisse, spalten=None):
    """
    Wendet Presets aus Testfragen als Default-Werte auf ergebnisse an.

    Wenn für eine Frage noch kein Ergebnis existiert und die Frage Presets hat,
    werden diese als Default-Werte gesetzt.

    Args:
        testfragen: Liste von TestQuestion-Objekten
        ergebnisse: Dict mit existierenden Ergebnissen (wird in-place modifiziert)
        spalten: Optional - Liste von Spalten für Multi-Spalten-Format
    """
    for frage in testfragen:
        preset = frage.preset_antworten or {}
        if not preset.get('lss_ch') and not preset.get('wh_lts'):
            continue  # Keine Presets definiert

        if spalten:
            # Multi-Spalten-Format (WHK, Abgänge, etc.)
            if frage.id not in ergebnisse:
                ergebnisse[frage.id] = {}
            for spalte in spalten:
                if spalte not in ergebnisse.get(frage.id, {}):
                    ergebnisse[frage.id][spalte] = {
                        'lss_ch': {
                            'result': preset.get('lss_ch'),
                            'bemerkung': None
                        },
                        'wh_lts': {
                            'result': preset.get('wh_lts'),
                            'bemerkung': None
                        }
                    }
        else:
            # Single-Spalten-Format (Anlage, Antriebsheizung, Meteostation)
            if frage.id not in ergebnisse:
                ergebnisse[frage.id] = {
                    'lss_ch': {
                        'result': preset.get('lss_ch'),
                        'bemerkung': None
                    },
                    'wh_lts': {
                        'result': preset.get('wh_lts'),
                        'bemerkung': None
                    }
                }


def get_first_unanswered_index(testfragen, ergebnisse, spalten=None):
    """
    Findet den Index der ersten unbeantworteten Frage.

    Unterstützt zwei Formate:
    - Single-Column: ergebnisse[frage_id] = {lss_ch: {result}, wh_lts: {result}}
    - Multi-Column:  ergebnisse[frage_id][spalte] = {lss_ch: {result}, wh_lts: {result}}

    Eine Frage gilt als vollständig beantwortet wenn ALLE Spalten
    für BEIDE Systeme (LSS-CH UND WH-LTS) einen gültigen Wert haben.

    Args:
        testfragen: Liste der TestQuestion-Objekte
        ergebnisse: Dict mit Ergebnissen
        spalten: Optional - Liste der Spalten für Multi-Column-Format

    Returns:
        int: Index der ersten unbeantworteten Frage (0-basiert), oder 0 wenn alle beantwortet
    """
    for index, frage in enumerate(testfragen):
        frage_id = frage.id
        frage_ergebnis = ergebnisse.get(frage_id, {})

        if spalten and len(spalten) > 1:
            # Multi-Column-Format (WHK, Abgänge, TS)
            for spalte in spalten:
                spalte_ergebnis = frage_ergebnis.get(spalte, {})
                lss_ch = spalte_ergebnis.get('lss_ch', {})
                lss_result = lss_ch.get('result') if lss_ch else None
                wh_lts = spalte_ergebnis.get('wh_lts', {})
                wh_result = wh_lts.get('result') if wh_lts else None

                if not lss_result or not wh_result:
                    return index
        else:
            # Single-Column-Format (Anlage, AH, MS)
            lss_ch = frage_ergebnis.get('lss_ch', {})
            lss_result = lss_ch.get('result') if lss_ch else None
            wh_lts = frage_ergebnis.get('wh_lts', {})
            wh_result = wh_lts.get('result') if wh_lts else None

            if not lss_result or not wh_result:
                return index

    return 0  # Alle beantwortet, starte bei 0


# ==================== EWH ABNAHMETEST ROUTES ====================

@ewh_bp.route('/projekt/abnahmetest/<int:projekt_id>', methods=['GET'])
@login_required
def projekt_abnahmetest(projekt_id):
    """
    EWH-Abnahmetest Übersichtsseite (Elektrische Weichenheizung) für ein Projekt.

    Zeigt eine Navigations-Übersicht mit Links zu allen Test-Seiten.
    Alle Tests werden auf separaten Seiten durchgeführt.

    Args:
        projekt_id: ID des Projekts

    Returns:
        HTML-Seite (abnahmetest.html) mit Navigations-Übersicht
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein EWH-Projekt ist
    if projekt.energie != 'EWH':
        flash('Diese Seite ist nur für EWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Lade WHK-Konfigurationen für dieses Projekt
    whk_configs = WHKConfig.query.filter_by(projekt_id=projekt_id).order_by(WHKConfig.whk_nummer).all()

    # Lade EWH-Meteostationen für dieses Projekt
    ewh_meteostationen = EWHMeteostation.query.filter_by(projekt_id=projekt_id).order_by(EWHMeteostation.reihenfolge).all()

    # Erstelle Dictionary: WHK-ID -> EWHMeteostation (für Template-Zugriff)
    whk_meteostation_map = {}
    for ms in ewh_meteostationen:
        if ms.zugeordnete_whk_id:
            whk_meteostation_map[ms.zugeordnete_whk_id] = ms

    # ==================== FORTSCHRITTSBERECHNUNG (PROZENT) ====================

    # Gültige Antwort-Werte (alles andere gilt als "nicht beantwortet")
    valid_values = ['richtig', 'falsch', 'nicht_testbar']

    def calc_component_percent(komponente_typ, komponente_index=None, anzahl_spalten=1):
        """Berechnet den Fortschritt in Prozent für eine Komponente.

        Logik:
        - Total = Anzahl Testfragen × Anzahl Spalten (erwartete Gesamtzahl)
        - Beantwortet = DB-Einträge mit mindestens einem gültigen Wert (lss_ch ODER wh_lts)
        - Ein Wert ist gültig wenn: IN ['richtig', 'falsch', 'nicht_testbar']
        - NULL, 'None', '' werden als ungültig behandelt

        Args:
            komponente_typ: Typ der Komponente ('Anlage', 'WHK', 'Abgang', etc.)
            komponente_index: Optional - Index für Multi-Instanz-Komponenten (z.B. WHK-Nummer)
            anzahl_spalten: Anzahl der Spalten/Instanzen (z.B. Anzahl Abgänge, Temperatursonden)

        Returns:
            int: Fortschritt in Prozent (0-100)
        """
        # Anzahl Testfragen für diesen Komponenten-Typ
        anzahl_fragen = TestQuestion.query.filter_by(
            komponente_typ=komponente_typ
        ).count()

        if anzahl_fragen == 0:
            return 0

        # Total = Erwartete Gesamtzahl (Fragen × Spalten)
        total = anzahl_fragen * anzahl_spalten

        # Basis-Query für beantwortete Ergebnisse dieser Komponente
        base_query = AbnahmeTestResult.query.filter_by(
            projekt_id=projekt_id
        ).join(TestQuestion).filter(
            TestQuestion.komponente_typ == komponente_typ
        )
        if komponente_index:
            base_query = base_query.filter(AbnahmeTestResult.komponente_index == komponente_index)

        # Beantwortet = Einträge bei denen BEIDE Systeme einen gültigen Wert haben (UND-Logik)
        beantwortet = base_query.filter(
            AbnahmeTestResult.lss_ch_result.in_(valid_values),
            AbnahmeTestResult.wh_lts_result.in_(valid_values)
        ).count()

        if beantwortet == 0:
            return 0

        # Prozent berechnen (max 100%)
        return min(int((beantwortet / total) * 100), 100)

    # Berechne Fortschritt für jede Komponente (in Prozent)
    fortschritt = {
        'anlage': {'percent': calc_component_percent('Anlage')},
        'whk': {'percent': calc_component_percent('WHK', anzahl_spalten=len(whk_configs))},
        'abgaenge': {},
        'temperatursonden': {},
        'antriebsheizung': {},
        'meteostationen': {}
    }

    # Pro-WHK Fortschritt
    for whk in whk_configs:
        whk_nummer = whk.whk_nummer

        # Abgänge - Anzahl Spalten = Anzahl Abgänge
        if whk.anzahl_abgaenge and whk.anzahl_abgaenge > 0:
            fortschritt['abgaenge'][whk_nummer] = {
                'percent': calc_component_percent('Abgang', komponente_index=whk_nummer, anzahl_spalten=whk.anzahl_abgaenge)
            }
        else:
            fortschritt['abgaenge'][whk_nummer] = {'percent': 0}

        # Temperatursonden - Anzahl Spalten = Anzahl Temperatursonden
        if whk.anzahl_temperatursonden and whk.anzahl_temperatursonden > 0:
            fortschritt['temperatursonden'][whk_nummer] = {
                'percent': calc_component_percent('Temperatursonde', komponente_index=whk_nummer, anzahl_spalten=whk.anzahl_temperatursonden)
            }
        else:
            fortschritt['temperatursonden'][whk_nummer] = {'percent': 0}

        # Antriebsheizung - Einzelne Spalte
        if whk.hat_antriebsheizung:
            fortschritt['antriebsheizung'][whk_nummer] = {
                'percent': calc_component_percent('Antriebsheizung', komponente_index=whk_nummer)
            }
        else:
            fortschritt['antriebsheizung'][whk_nummer] = {'percent': 0}

        # Meteostation (über EWHMeteostation-Zuordnung)
        zugeordnete_ms = whk_meteostation_map.get(whk.id)
        if zugeordnete_ms:
            ms_nummer = zugeordnete_ms.ms_nummer
            # Normalisiere ms_nummer für Fortschrittsberechnung
            normalized_ms = normalize_ms_nummer(ms_nummer)
            if normalized_ms not in fortschritt['meteostationen']:
                fortschritt['meteostationen'][normalized_ms] = {
                    'percent': calc_component_percent('Meteostation', komponente_index=normalized_ms)
                }

    return render_template('abnahmetest.html',
                         projekt=projekt,
                         whk_configs=whk_configs,
                         whk_meteostation_map=whk_meteostation_map,
                         fortschritt=fortschritt)

@ewh_bp.route('/projekt/abnahmetest/save-answer', methods=['POST'])
@login_required
def save_test_answer():
    """Auto-Save Route für einzelne Test-Antworten"""
    try:
        data = request.get_json()

        projekt_id = data.get('projekt_id')
        question_id_str = data.get('question_id')  # Kann "1" oder "3_WHK_01" sein
        spalte = data.get('spalte')  # z.B. "WHK_01", "Abgang_01"
        system = data.get('system')  # 'lss-ch' oder 'wh-lts'
        ergebnis = data.get('ergebnis')  # 'richtig', 'falsch', 'nicht_testbar' oder None
        bemerkung = data.get('bemerkung')  # Optional: Bemerkungstext


        # Validierung
        if not all([projekt_id, question_id_str, spalte, system]):
            return jsonify({'success': False, 'error': 'Fehlende Daten'}), 400


        # Prüfe ob Projekt existiert
        projekt = Project.query.get(projekt_id)
        if not projekt:
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404

        # Extrahiere numerische test_question_id und komponente_index
        # question_id_str kann "1" oder "3_WHK_01" oder "23_MS_01" sein
        # Konvertiere zu String falls es als Integer kommt
        parts = str(question_id_str).split('_')
        numeric_id_str = parts[0]

        try:
            test_question_id = int(numeric_id_str)
        except (ValueError, IndexError):
            return jsonify({'success': False, 'error': f'Ungültige Question ID: {question_id_str}'}), 400

        # Komponente_index: Für "3_WHK_01" -> "WHK 01", für "1" -> spalte
        if len(parts) > 1:
            # Frage hat komponente_index in der ID (z.B. "3_WHK_01", "23_MS_01")
            komponente_index = '_'.join(parts[1:]).replace('_', ' ')
        else:
            # Frage hat keinen komponente_index in der ID (Anlage/WHK)
            # In diesem Fall ist spalte der komponente_index
            komponente_index = spalte.replace('_', ' ')

        # Konvertiere system von lss-ch/wh-lts zu lss_ch/wh_lts
        system_db = system.replace('-', '_')

        # Spalte mit Spaces (für Anzeige und Speicherung)
        spalte_display = spalte.replace('_', ' ')

        # Suche nach bestehendem Eintrag (prüfe komponente_index UND spalte)
        existing_result = AbnahmeTestResult.query.filter_by(
            projekt_id=projekt_id,
            test_question_id=test_question_id,
            komponente_index=komponente_index,
            spalte=spalte_display
        ).first()

        if existing_result:
            # Update bestehenden Eintrag
            if system_db == 'lss_ch':
                existing_result.lss_ch_result = ergebnis
                # Bemerkung nur setzen wenn explizit übergeben (auch wenn leer zum Löschen)
                if bemerkung is not None:
                    old_bemerkung = existing_result.lss_ch_bemerkung
                    existing_result.lss_ch_bemerkung = bemerkung if bemerkung.strip() else None
            elif system_db == 'wh_lts':
                existing_result.wh_lts_result = ergebnis
                # Bemerkung nur setzen wenn explizit übergeben (auch wenn leer zum Löschen)
                if bemerkung is not None:
                    old_bemerkung = existing_result.wh_lts_bemerkung
                    existing_result.wh_lts_bemerkung = bemerkung if bemerkung.strip() else None

            existing_result.getestet_am = datetime.utcnow()
            if projekt.pruefer_achermann:
                existing_result.tester = projekt.pruefer_achermann
        else:
            # Erstelle neuen Eintrag
            new_result = AbnahmeTestResult(
                projekt_id=projekt_id,
                test_question_id=test_question_id,
                komponente_index=komponente_index,
                spalte=spalte_display,
                lss_ch_result=ergebnis if system_db == 'lss_ch' else None,
                wh_lts_result=ergebnis if system_db == 'wh_lts' else None,
                lss_ch_bemerkung=bemerkung if system_db == 'lss_ch' and bemerkung else None,
                wh_lts_bemerkung=bemerkung if system_db == 'wh_lts' and bemerkung else None,
                getestet_am=datetime.utcnow(),
                tester=projekt.pruefer_achermann or 'Unbekannt'
            )
            db.session.add(new_result)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Antwort gespeichert',
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== EWH TEST-ROUTEN (NEUE STRUKTUR) ====================

@ewh_bp.route('/projekt/<int:projekt_id>/ewh-test/anlage', methods=['GET', 'POST'])
@login_required
def ewh_test_anlage(projekt_id):
    """
    EWH-Anlage Test-Seite.

    GET: Zeigt Test-Seite für EWH-Anlage Tests
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts

    Returns:
        GET: HTML-Seite (ewh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein EWH-Projekt ist
    if projekt.energie != 'EWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein EWH-Projekt'}), 400
        flash('Diese Testseite ist nur für EWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        try:
            data = request.get_json()

            # Speichere die Ergebnisse in der Datenbank
            # Format: { question_id: { lss_ch: {result, bemerkung}, wh_lts: {result, bemerkung} } }
            for question_id_str, systems in data.items():
                question_id = int(question_id_str)

                # Lösche alte Einträge für diese Frage
                AbnahmeTestResult.query.filter_by(
                    projekt_id=projekt_id,
                    test_question_id=question_id,
                    komponente_index='',
                    spalte='Anlage'
                ).delete()

                # Erstelle neue Einträge
                result = AbnahmeTestResult(
                    projekt_id=projekt_id,
                    test_question_id=question_id,
                    komponente_index='',
                    spalte='Anlage',
                    lss_ch_result=systems.get('lss_ch', {}).get('result'),
                    lss_ch_bemerkung=systems.get('lss_ch', {}).get('bemerkung'),
                    wh_lts_result=systems.get('wh_lts', {}).get('result'),
                    wh_lts_bemerkung=systems.get('wh_lts', {}).get('bemerkung'),
                    getestet_am=datetime.utcnow()
                )
                db.session.add(result)

            db.session.commit()
            return jsonify({'success': True})

        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET: Lade Testfragen und Ergebnisse
    komponente_typ = 'Anlage'

    # Lade alle Testfragen für Anlage
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id,
        spalte='Anlage'
    ).filter(
        AbnahmeTestResult.test_question_id.in_([f.id for f in testfragen])
    ).all()

    for result in results:
        ergebnisse[result.test_question_id] = {
            'lss_ch': {
                'result': result.lss_ch_result,
                'bemerkung': result.lss_ch_bemerkung
            },
            'wh_lts': {
                'result': result.wh_lts_result,
                'bemerkung': result.wh_lts_bemerkung
            }
        }

    # Wenn kein Ergebnis existiert, verwende Presets als Default-Werte
    apply_presets_to_ergebnisse(testfragen, ergebnisse)

    # Konvertiere Testfragen zu JSON für JavaScript
    fragen_json = json.dumps([{
        'id': f.id,
        'frage_text': f.frage_text,
        'test_information': f.test_information or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse)

    return render_template('ewh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label='Anlage Test',
                         fragen=testfragen,
                         spalten=['Anlage'],
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id),
                         save_url=url_for('ewh.ewh_test_anlage', projekt_id=projekt_id))


@ewh_bp.route('/projekt/<int:projekt_id>/ewh-test/whk', methods=['GET', 'POST'])
@login_required
def ewh_test_whk(projekt_id):
    """
    WHK Test-Seite - zeigt alle WHKs als Spalten.

    GET: Zeigt Test-Seite für WHK Tests (alle WHKs als Spalten)
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts

    Returns:
        GET: HTML-Seite (ewh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein EWH-Projekt ist
    if projekt.energie != 'EWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein EWH-Projekt'}), 400
        flash('Diese Testseite ist nur für EWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Lade WHK-Konfigurationen
    whk_configs = WHKConfig.query.filter_by(projekt_id=projekt_id).order_by(WHKConfig.whk_nummer).all()

    if not whk_configs:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Keine WHKs konfiguriert'}), 400
        flash('Für dieses Projekt sind keine WHKs konfiguriert!', 'warning')
        return redirect(url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id))

    # Normalisiere alle WHK-Nummern auf das Format "WHK XX"
    spalten = [normalize_whk_nummer(whk.whk_nummer) for whk in whk_configs]

    # Generiere alle möglichen Varianten für DB-Abfragen (für Rückwärtskompatibilität)
    all_spalte_variants = []
    spalte_to_normalized = {}
    for spalte in spalten:
        variants = get_whk_spalte_variants(spalte)
        all_spalte_variants.extend(variants)
        for v in variants:
            spalte_to_normalized[v] = spalte


    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        # Format: { question_id: { spalte: { lss_ch: {result, bemerkung}, wh_lts: {result, bemerkung} } } }
        try:
            data = request.get_json()

            for question_id_str, spalten_data in data.items():
                question_id = int(question_id_str)

                # Iteriere über alle Spalten (WHK 01, WHK 02, etc.)
                for spalte, systems in spalten_data.items():

                    # Lösche alte Einträge für diese Frage und Spalte (alle möglichen Formate)
                    spalte_variants = get_whk_spalte_variants(spalte)

                    deleted_total = 0
                    for variant in spalte_variants:
                        # Lösche mit verschiedenen komponente_index Varianten
                        for ki_variant in spalte_variants + ['', 'WHK']:
                            deleted = AbnahmeTestResult.query.filter_by(
                                projekt_id=projekt_id,
                                test_question_id=question_id,
                                komponente_index=ki_variant,
                                spalte=variant
                            ).delete()
                            deleted_total += deleted

                    # Prüfe ob überhaupt Daten vorhanden
                    lss_result = systems.get('lss_ch', {}).get('result')
                    wh_result = systems.get('wh_lts', {}).get('result')
                    lss_bemerkung = systems.get('lss_ch', {}).get('bemerkung')
                    wh_bemerkung = systems.get('wh_lts', {}).get('bemerkung')

                    # Nur speichern wenn mindestens ein Wert vorhanden
                    if lss_result or wh_result or lss_bemerkung or wh_bemerkung:
                        result = AbnahmeTestResult(
                            projekt_id=projekt_id,
                            test_question_id=question_id,
                            komponente_index=spalte,
                            spalte=spalte,
                            lss_ch_result=lss_result,
                            lss_ch_bemerkung=lss_bemerkung,
                            wh_lts_result=wh_result,
                            wh_lts_bemerkung=wh_bemerkung,
                            getestet_am=datetime.utcnow()
                        )
                        db.session.add(result)

            db.session.commit()
            return jsonify({'success': True})

        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET: Lade Testfragen und Ergebnisse
    komponente_typ = 'WHK'

    # Lade alle Testfragen für WHK
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse - pro Frage und pro Spalte
    # Verwende alle Varianten für Rückwärtskompatibilität
    # Struktur: ergebnisse[frage_id][normalized_spalte] = {lss_ch: {...}, wh_lts: {...}}
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id
    ).filter(
        AbnahmeTestResult.test_question_id.in_([f.id for f in testfragen]),
        AbnahmeTestResult.spalte.in_(all_spalte_variants)
    ).all()

    for result in results:
        frage_id = result.test_question_id
        db_spalte = result.spalte

        # Mappe die DB-Spalte auf die normalisierte Spalte
        normalized_spalte = spalte_to_normalized.get(db_spalte, db_spalte)

        if frage_id not in ergebnisse:
            ergebnisse[frage_id] = {}

        # Speichere unter der normalisierten Spalte (Frontend erwartet "WHK 01" etc.)
        ergebnisse[frage_id][normalized_spalte] = {
            'lss_ch': {
                'result': result.lss_ch_result,
                'bemerkung': result.lss_ch_bemerkung
            },
            'wh_lts': {
                'result': result.wh_lts_result,
                'bemerkung': result.wh_lts_bemerkung
            }
        }

    # Wenn kein Ergebnis existiert, verwende Presets als Default-Werte
    apply_presets_to_ergebnisse(testfragen, ergebnisse, spalten=spalten)

    # Konvertiere Testfragen zu JSON für JavaScript
    fragen_json = json.dumps([{
        'id': f.id,
        'frage_text': f.frage_text,
        'test_information': f.test_information or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse, spalten=spalten)

    return render_template('ewh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label='WHK Test',
                         fragen=testfragen,
                         spalten=spalten,
                         multi_spalten=True,  # WHK-Test verwendet Multi-Spalten-Format
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id),
                         save_url=url_for('ewh.ewh_test_whk', projekt_id=projekt_id))


@ewh_bp.route('/projekt/<int:projekt_id>/ewh-test/abgaenge/<whk_nummer>', methods=['GET', 'POST'])
@login_required
def ewh_test_abgaenge(projekt_id, whk_nummer):
    """
    Abgänge Test-Seite - zeigt alle Abgänge eines WHK als Spalten.

    GET: Zeigt Test-Seite für Abgänge Tests (alle Abgänge eines WHK als Spalten)
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts
        whk_nummer: WHK-Nummer (z.B. "WHK 01", "WHK 02")

    Returns:
        GET: HTML-Seite (ewh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein EWH-Projekt ist
    if projekt.energie != 'EWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein EWH-Projekt'}), 400
        flash('Diese Testseite ist nur für EWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Lade WHK-Konfiguration für die angegebene WHK-Nummer (versuche alle Varianten)
    whk_variants = get_whk_spalte_variants(whk_nummer)
    whk_config = None
    for variant in whk_variants:
        whk_config = WHKConfig.query.filter_by(projekt_id=projekt_id, whk_nummer=variant).first()
        if whk_config:
            break

    if not whk_config:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'{whk_nummer} nicht konfiguriert'}), 400
        flash(f'{whk_nummer} ist für dieses Projekt nicht konfiguriert!', 'warning')
        return redirect(url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id))

    # Normalisiere whk_nummer auf das Standard-Format
    normalized_whk = normalize_whk_nummer(whk_nummer)

    # Spalten aus Anzahl Abgänge erstellen (Abgang 01, Abgang 02, ...)
    anzahl_abgaenge = whk_config.anzahl_abgaenge or 0
    if anzahl_abgaenge == 0:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'{whk_nummer} hat keine Abgänge konfiguriert'}), 400
        flash(f'{whk_nummer} hat keine Abgänge konfiguriert!', 'warning')
        return redirect(url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id))

    spalten = [f"Abgang {str(i).zfill(2)}" for i in range(1, anzahl_abgaenge + 1)]
    komponente_index = normalized_whk
    komponente_index_variants = get_whk_spalte_variants(normalized_whk)

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        # Format: { question_id: { spalte: { lss_ch: {result, bemerkung}, wh_lts: {result, bemerkung} } } }
        try:
            data = request.get_json()

            for question_id_str, spalten_data in data.items():
                question_id = int(question_id_str)

                # Iteriere über alle Spalten (Abgang 01, Abgang 02, etc.)
                for spalte, systems in spalten_data.items():

                    # Lösche alte Einträge für diese Frage und Spalte (alle möglichen Formate)
                    deleted_total = 0
                    for ki_variant in komponente_index_variants:
                        deleted = AbnahmeTestResult.query.filter_by(
                            projekt_id=projekt_id,
                            test_question_id=question_id,
                            komponente_index=ki_variant,
                            spalte=spalte
                        ).delete()
                        deleted_total += deleted

                    # Prüfe ob überhaupt Daten vorhanden
                    lss_result = systems.get('lss_ch', {}).get('result')
                    wh_result = systems.get('wh_lts', {}).get('result')
                    lss_bemerkung = systems.get('lss_ch', {}).get('bemerkung')
                    wh_bemerkung = systems.get('wh_lts', {}).get('bemerkung')

                    # Nur speichern wenn mindestens ein Wert vorhanden
                    if lss_result or wh_result or lss_bemerkung or wh_bemerkung:
                        result = AbnahmeTestResult(
                            projekt_id=projekt_id,
                            test_question_id=question_id,
                            komponente_index=komponente_index,
                            spalte=spalte,
                            lss_ch_result=lss_result,
                            lss_ch_bemerkung=lss_bemerkung,
                            wh_lts_result=wh_result,
                            wh_lts_bemerkung=wh_bemerkung,
                            getestet_am=datetime.utcnow()
                        )
                        db.session.add(result)

            db.session.commit()
            return jsonify({'success': True})

        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET: Lade Testfragen und Ergebnisse
    komponente_typ = 'Abgang'

    # Lade alle Testfragen für Abgang
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse für diesen WHK (alle möglichen Formate)
    # Struktur: ergebnisse[frage_id][spalte] = {lss_ch: {...}, wh_lts: {...}}
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id
    ).filter(
        AbnahmeTestResult.komponente_index.in_(komponente_index_variants),
        AbnahmeTestResult.test_question_id.in_([f.id for f in testfragen]),
        AbnahmeTestResult.spalte.in_(spalten)
    ).all()

    for result in results:
        frage_id = result.test_question_id
        spalte = result.spalte

        if frage_id not in ergebnisse:
            ergebnisse[frage_id] = {}

        ergebnisse[frage_id][spalte] = {
            'lss_ch': {
                'result': result.lss_ch_result,
                'bemerkung': result.lss_ch_bemerkung
            },
            'wh_lts': {
                'result': result.wh_lts_result,
                'bemerkung': result.wh_lts_bemerkung
            }
        }

    # Wenn kein Ergebnis existiert, verwende Presets als Default-Werte
    apply_presets_to_ergebnisse(testfragen, ergebnisse, spalten=spalten)

    # Konvertiere Testfragen zu JSON für JavaScript
    fragen_json = json.dumps([{
        'id': f.id,
        'frage_text': f.frage_text,
        'test_information': f.test_information or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse, spalten=spalten)

    return render_template('ewh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label=f'Abgänge - {normalized_whk}',
                         fragen=testfragen,
                         spalten=spalten,
                         multi_spalten=True,  # Multi-Spalten-Format für Abgang 01, Abgang 02, etc.
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id),
                         save_url=url_for('ewh.ewh_test_abgaenge', projekt_id=projekt_id, whk_nummer=whk_nummer))


@ewh_bp.route('/projekt/<int:projekt_id>/ewh-test/temperatursonde/<whk_nummer>', methods=['GET', 'POST'])
@login_required
def ewh_test_temperatursonde(projekt_id, whk_nummer):
    """
    Temperatursonde Test-Seite - zeigt Temperatursonde-Tests für einen WHK.

    GET: Zeigt Test-Seite für Temperatursonde Tests (Multi-Spalten: TS 01, TS 02, ...)
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts
        whk_nummer: WHK-Nummer (z.B. "WHK 01", "WHK 02")

    Returns:
        GET: HTML-Seite (ewh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein EWH-Projekt ist
    if projekt.energie != 'EWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein EWH-Projekt'}), 400
        flash('Diese Testseite ist nur für EWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Lade WHK-Konfiguration für die angegebene WHK-Nummer (versuche alle Varianten)
    whk_variants = get_whk_spalte_variants(whk_nummer)
    whk_config = None
    for variant in whk_variants:
        whk_config = WHKConfig.query.filter_by(projekt_id=projekt_id, whk_nummer=variant).first()
        if whk_config:
            break

    if not whk_config:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'{whk_nummer} nicht konfiguriert'}), 400
        flash(f'{whk_nummer} ist für dieses Projekt nicht konfiguriert!', 'warning')
        return redirect(url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id))

    # Prüfen ob WHK Temperatursonden hat
    anzahl_ts = whk_config.anzahl_temperatursonden or 0
    if anzahl_ts == 0:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'{whk_nummer} hat keine Temperatursonden konfiguriert'}), 400
        flash(f'{whk_nummer} hat keine Temperatursonden konfiguriert!', 'warning')
        return redirect(url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id))

    # Normalisiere whk_nummer auf das Standard-Format
    normalized_whk = normalize_whk_nummer(whk_nummer)

    # Spalten für Temperatursonden erstellen (TS 01, TS 02, ...)
    spalten = [f"TS {str(i).zfill(2)}" for i in range(1, anzahl_ts + 1)]
    komponente_index = normalized_whk
    komponente_index_variants = get_whk_spalte_variants(normalized_whk)

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        # Format: { question_id: { spalte: { lss_ch: {result, bemerkung}, wh_lts: {result, bemerkung} } } }
        try:
            data = request.get_json()

            for question_id_str, spalten_data in data.items():
                question_id = int(question_id_str)

                # Iteriere über alle Spalten (TS 01, TS 02, etc.)
                for spalte, systems in spalten_data.items():

                    # Lösche alte Einträge für diese Frage und Spalte (alle möglichen komponente_index Formate)
                    deleted_total = 0
                    for ki_variant in komponente_index_variants:
                        deleted = AbnahmeTestResult.query.filter_by(
                            projekt_id=projekt_id,
                            test_question_id=question_id,
                            komponente_index=ki_variant,
                            spalte=spalte
                        ).delete()
                        deleted_total += deleted

                    # Prüfe ob überhaupt Daten vorhanden
                    lss_result = systems.get('lss_ch', {}).get('result')
                    wh_result = systems.get('wh_lts', {}).get('result')
                    lss_bemerkung = systems.get('lss_ch', {}).get('bemerkung')
                    wh_bemerkung = systems.get('wh_lts', {}).get('bemerkung')

                    # Nur speichern wenn mindestens ein Wert vorhanden
                    if lss_result or wh_result or lss_bemerkung or wh_bemerkung:
                        result = AbnahmeTestResult(
                            projekt_id=projekt_id,
                            test_question_id=question_id,
                            komponente_index=komponente_index,
                            spalte=spalte,
                            lss_ch_result=lss_result,
                            lss_ch_bemerkung=lss_bemerkung,
                            wh_lts_result=wh_result,
                            wh_lts_bemerkung=wh_bemerkung,
                            getestet_am=datetime.utcnow()
                        )
                        db.session.add(result)

            db.session.commit()
            return jsonify({'success': True})

        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET: Lade Testfragen und Ergebnisse
    komponente_typ = 'Temperatursonde'

    # Lade alle Testfragen für Temperatursonde
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse für diesen WHK (alle möglichen Formate)
    # Struktur: ergebnisse[frage_id][spalte] = {lss_ch: {...}, wh_lts: {...}}
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id
    ).filter(
        AbnahmeTestResult.komponente_index.in_(komponente_index_variants),
        AbnahmeTestResult.test_question_id.in_([f.id for f in testfragen]),
        AbnahmeTestResult.spalte.in_(spalten)
    ).all()

    for result in results:
        frage_id = result.test_question_id
        spalte = result.spalte

        if frage_id not in ergebnisse:
            ergebnisse[frage_id] = {}

        ergebnisse[frage_id][spalte] = {
            'lss_ch': {
                'result': result.lss_ch_result,
                'bemerkung': result.lss_ch_bemerkung
            },
            'wh_lts': {
                'result': result.wh_lts_result,
                'bemerkung': result.wh_lts_bemerkung
            }
        }

    # Wenn kein Ergebnis existiert, verwende Presets als Default-Werte
    apply_presets_to_ergebnisse(testfragen, ergebnisse, spalten=spalten)

    # Konvertiere Testfragen zu JSON für JavaScript
    fragen_json = json.dumps([{
        'id': f.id,
        'frage_text': f.frage_text,
        'test_information': f.test_information or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse, spalten=spalten)

    return render_template('ewh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label=f'Temperatursonde - {normalized_whk}',
                         fragen=testfragen,
                         spalten=spalten,
                         multi_spalten=True,  # Multi-Spalten-Format für TS 01, TS 02, etc.
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id),
                         save_url=url_for('ewh.ewh_test_temperatursonde', projekt_id=projekt_id, whk_nummer=whk_nummer))


@ewh_bp.route('/projekt/<int:projekt_id>/ewh-test/antriebsheizung/<whk_nummer>', methods=['GET', 'POST'])
@login_required
def ewh_test_antriebsheizung(projekt_id, whk_nummer):
    """
    Antriebsheizung Test-Seite - zeigt Antriebsheizung-Tests für einen WHK.

    GET: Zeigt Test-Seite für Antriebsheizung Tests (eine Spalte: AH)
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts
        whk_nummer: WHK-Nummer (z.B. "WHK 01", "WHK 02")

    Returns:
        GET: HTML-Seite (ewh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein EWH-Projekt ist
    if projekt.energie != 'EWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein EWH-Projekt'}), 400
        flash('Diese Testseite ist nur für EWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Lade WHK-Konfiguration für die angegebene WHK-Nummer (versuche alle Varianten)
    whk_variants = get_whk_spalte_variants(whk_nummer)
    whk_config = None
    for variant in whk_variants:
        whk_config = WHKConfig.query.filter_by(projekt_id=projekt_id, whk_nummer=variant).first()
        if whk_config:
            break

    if not whk_config:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'{whk_nummer} nicht konfiguriert'}), 400
        flash(f'{whk_nummer} ist für dieses Projekt nicht konfiguriert!', 'warning')
        return redirect(url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id))

    # Prüfen ob WHK eine Antriebsheizung hat
    if not whk_config.hat_antriebsheizung:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'{whk_nummer} hat keine Antriebsheizung konfiguriert'}), 400
        flash(f'{whk_nummer} hat keine Antriebsheizung konfiguriert!', 'warning')
        return redirect(url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id))

    # Normalisiere whk_nummer auf das Standard-Format
    normalized_whk = normalize_whk_nummer(whk_nummer)

    # Spalte für Antriebsheizung (Boolean, daher nur eine Spalte)
    spalten = ['AH']
    komponente_index = normalized_whk
    komponente_index_variants = get_whk_spalte_variants(normalized_whk)

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        # Format: { question_id: { lss_ch: {result, bemerkung}, wh_lts: {result, bemerkung} } }
        try:
            data = request.get_json()

            # Speichere die Ergebnisse in der Datenbank
            for question_id_str, systems in data.items():
                question_id = int(question_id_str)

                # Lösche alte Einträge für diese Frage (alle möglichen komponente_index Formate)
                deleted_total = 0
                for ki_variant in komponente_index_variants:
                    deleted = AbnahmeTestResult.query.filter_by(
                        projekt_id=projekt_id,
                        test_question_id=question_id,
                        komponente_index=ki_variant,
                        spalte='AH'
                    ).delete()
                    deleted_total += deleted

                # Prüfe ob überhaupt Daten vorhanden
                lss_result = systems.get('lss_ch', {}).get('result')
                wh_result = systems.get('wh_lts', {}).get('result')
                lss_bemerkung = systems.get('lss_ch', {}).get('bemerkung')
                wh_bemerkung = systems.get('wh_lts', {}).get('bemerkung')

                # Nur speichern wenn mindestens ein Wert vorhanden
                if lss_result or wh_result or lss_bemerkung or wh_bemerkung:
                    result = AbnahmeTestResult(
                        projekt_id=projekt_id,
                        test_question_id=question_id,
                        komponente_index=komponente_index,
                        spalte='AH',
                        lss_ch_result=lss_result,
                        lss_ch_bemerkung=lss_bemerkung,
                        wh_lts_result=wh_result,
                        wh_lts_bemerkung=wh_bemerkung,
                        getestet_am=datetime.utcnow()
                    )
                    db.session.add(result)

            db.session.commit()
            return jsonify({'success': True})

        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET: Lade Testfragen und Ergebnisse
    komponente_typ = 'Antriebsheizung'

    # Lade alle Testfragen für Antriebsheizung
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse für diesen WHK (alle möglichen Formate)
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id,
        spalte='AH'
    ).filter(
        AbnahmeTestResult.komponente_index.in_(komponente_index_variants),
        AbnahmeTestResult.test_question_id.in_([f.id for f in testfragen])
    ).all()

    for result in results:
        ergebnisse[result.test_question_id] = {
            'lss_ch': {
                'result': result.lss_ch_result,
                'bemerkung': result.lss_ch_bemerkung
            },
            'wh_lts': {
                'result': result.wh_lts_result,
                'bemerkung': result.wh_lts_bemerkung
            }
        }

    # Wenn kein Ergebnis existiert, verwende Presets als Default-Werte
    apply_presets_to_ergebnisse(testfragen, ergebnisse)

    # Konvertiere Testfragen zu JSON für JavaScript
    fragen_json = json.dumps([{
        'id': f.id,
        'frage_text': f.frage_text,
        'test_information': f.test_information or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse)

    return render_template('ewh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label=f'Antriebsheizung - {normalized_whk}',
                         fragen=testfragen,
                         spalten=spalten,
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id),
                         save_url=url_for('ewh.ewh_test_antriebsheizung', projekt_id=projekt_id, whk_nummer=whk_nummer))


@ewh_bp.route('/projekt/<int:projekt_id>/ewh-test/meteostation/<ms_name>', methods=['GET', 'POST'])
@login_required
def ewh_test_meteostation(projekt_id, ms_name):
    """
    Meteostation Test-Seite - zeigt Meteostation-Tests für eine EWH-Meteostation.

    GET: Zeigt Test-Seite für Meteostation Tests (eine Spalte: MS-Name)
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts
        ms_name: Name der Meteostation (z.B. "MS 01", "MS 02")

    Returns:
        GET: HTML-Seite (ewh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein EWH-Projekt ist
    if projekt.energie != 'EWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein EWH-Projekt'}), 400
        flash('Diese Testseite ist nur für EWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Generiere alle möglichen Varianten für die Meteostation-Suche
    ms_variants = get_ms_spalte_variants(ms_name)

    # Prüfe ob diese Meteostation im Projekt existiert (in EWHMeteostation-Tabelle)
    ewh_ms = None
    for variant in ms_variants:
        ewh_ms = EWHMeteostation.query.filter_by(projekt_id=projekt_id, ms_nummer=variant).first()
        if ewh_ms:
            break

    if not ewh_ms:
        # Debug: Zeige alle MS für dieses Projekt
        alle_ms = EWHMeteostation.query.filter_by(projekt_id=projekt_id).all()

        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'Meteostation {ms_name} nicht konfiguriert'}), 400
        flash(f'Meteostation {ms_name} ist für dieses Projekt nicht konfiguriert!', 'warning')
        return redirect(url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id))

    # Normalisiere ms_name auf das Standard-Format
    normalized_ms = normalize_ms_nummer(ms_name)

    # Spalte für Meteostation
    spalten = [normalized_ms]
    komponente_index = normalized_ms
    komponente_index_variants = get_ms_spalte_variants(normalized_ms)

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        # Format: { question_id: { lss_ch: {result, bemerkung}, wh_lts: {result, bemerkung} } }
        try:
            data = request.get_json()

            # Speichere die Ergebnisse in der Datenbank
            for question_id_str, systems in data.items():
                question_id = int(question_id_str)

                # Lösche alte Einträge für diese Frage (alle möglichen komponente_index und spalte Formate)
                deleted_total = 0
                for ki_variant in komponente_index_variants:
                    for spalte_variant in komponente_index_variants:
                        deleted = AbnahmeTestResult.query.filter_by(
                            projekt_id=projekt_id,
                            test_question_id=question_id,
                            komponente_index=ki_variant,
                            spalte=spalte_variant
                        ).delete()
                        deleted_total += deleted

                # Prüfe ob überhaupt Daten vorhanden
                lss_result = systems.get('lss_ch', {}).get('result')
                wh_result = systems.get('wh_lts', {}).get('result')
                lss_bemerkung = systems.get('lss_ch', {}).get('bemerkung')
                wh_bemerkung = systems.get('wh_lts', {}).get('bemerkung')

                # Nur speichern wenn mindestens ein Wert vorhanden
                if lss_result or wh_result or lss_bemerkung or wh_bemerkung:
                    result = AbnahmeTestResult(
                        projekt_id=projekt_id,
                        test_question_id=question_id,
                        komponente_index=komponente_index,
                        spalte=normalized_ms,
                        lss_ch_result=lss_result,
                        lss_ch_bemerkung=lss_bemerkung,
                        wh_lts_result=wh_result,
                        wh_lts_bemerkung=wh_bemerkung,
                        getestet_am=datetime.utcnow()
                    )
                    db.session.add(result)

            db.session.commit()
            return jsonify({'success': True})

        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET: Lade Testfragen und Ergebnisse
    komponente_typ = 'Meteostation'

    # Lade alle Testfragen für Meteostation
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse für diese Meteostation (alle möglichen Formate)
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id
    ).filter(
        AbnahmeTestResult.komponente_index.in_(komponente_index_variants),
        AbnahmeTestResult.spalte.in_(komponente_index_variants),
        AbnahmeTestResult.test_question_id.in_([f.id for f in testfragen])
    ).all()

    for result in results:
        ergebnisse[result.test_question_id] = {
            'lss_ch': {
                'result': result.lss_ch_result,
                'bemerkung': result.lss_ch_bemerkung
            },
            'wh_lts': {
                'result': result.wh_lts_result,
                'bemerkung': result.wh_lts_bemerkung
            }
        }

    # Wenn kein Ergebnis existiert, verwende Presets als Default-Werte
    apply_presets_to_ergebnisse(testfragen, ergebnisse)

    # Konvertiere Testfragen zu JSON für JavaScript
    fragen_json = json.dumps([{
        'id': f.id,
        'frage_text': f.frage_text,
        'test_information': f.test_information or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse)

    return render_template('ewh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label=f'Meteostation - {normalized_ms}',
                         fragen=testfragen,
                         spalten=spalten,
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id),
                         save_url=url_for('ewh.ewh_test_meteostation', projekt_id=projekt_id, ms_name=ms_name))

