"""
SBB Weichenheizung - GWH Blueprint
Gasweichenheizung Abnahmetests und Parameter-Prüfung
"""
import json
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from models import (db, Project, TestQuestion, TestResult, AbnahmeTestResult,
                   ZSKConfig, HGLSConfig, GWHMeteostation,
                   ZSKParameterPruefung, HGLSParameterPruefung)

gwh_bp = Blueprint('gwh', __name__)


# ==================== HELPER FUNCTIONS ====================

def normalize_komponente_nummer(nummer, prefix='ZSK'):
    """
    Normalisiert eine Komponenten-Nummer auf das Standard-Format "PREFIX XX".

    Eingabe-Formate:
    - "01" → "PREFIX 01"
    - "PREFIX 01" → "PREFIX 01"
    - "PREFIX_01" → "PREFIX 01"

    Args:
        nummer: Die zu normalisierende Nummer
        prefix: Der Prefix (z.B. 'ZSK', 'MS')

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


def normalize_zsk_nummer(zsk_nummer):
    """Normalisiert eine ZSK-Nummer auf das Standard-Format "ZSK XX"."""
    return normalize_komponente_nummer(zsk_nummer, 'ZSK')


def normalize_ms_nummer(ms_nummer):
    """Normalisiert eine Meteostation-Nummer auf das Standard-Format "MS XX"."""
    return normalize_komponente_nummer(ms_nummer, 'MS')


def get_komponente_variants(nummer, prefix='ZSK'):
    """
    Generiert alle möglichen Varianten einer Komponenten-Nummer für DB-Abfragen.

    Eingabe: "ZSK 01" oder "01" oder "ZSK_01"
    Ausgabe: ["ZSK 01", "ZSK_01", "01"]

    Args:
        nummer: Die Komponenten-Nummer
        prefix: Der Prefix (z.B. 'ZSK', 'MS')

    Dies ermöglicht das Finden von Daten, die mit verschiedenen Formaten gespeichert wurden.
    """
    variants = set()

    # Normalisiere zuerst
    normalized = normalize_komponente_nummer(nummer, prefix)
    variants.add(normalized)

    # Variante mit Unterstrich
    variants.add(normalized.replace(' ', '_'))

    # Nur die Nummer (ohne Prefix)
    prefix_space = f'{prefix} '
    if normalized.upper().startswith(prefix_space.upper()):
        nummer_only = normalized[len(prefix_space):]
        variants.add(nummer_only)

    # Original auch hinzufügen
    variants.add(nummer)

    return list(variants)


def get_zsk_spalte_variants(zsk_nummer):
    """Generiert alle möglichen Varianten einer ZSK-Nummer."""
    return get_komponente_variants(zsk_nummer, 'ZSK')


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
            # Multi-Spalten-Format (ZSK, Teile, etc.)
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
            # Single-Spalten-Format (Anlage, HGLS, Meteostation)
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


def get_first_unanswered_index(testfragen, ergebnisse):
    """
    Findet den Index der ersten unbeantworteten Frage.

    Eine Frage gilt als unbeantwortet wenn:
    - LSS-CH: Keine Auswahl (result ist None oder leer)
    - ODER WH-LTS: Keine Auswahl (result ist None oder leer)

    Args:
        testfragen: Liste der TestQuestion-Objekte
        ergebnisse: Dict mit {frage_id: {lss_ch: {result, bemerkung}, wh_lts: {result, bemerkung}}}

    Returns:
        int: Index der ersten unbeantworteten Frage (0-basiert), oder 0 wenn alle beantwortet
    """
    for index, frage in enumerate(testfragen):
        frage_id = frage.id
        frage_ergebnis = ergebnisse.get(frage_id, {})

        # Prüfe LSS-CH
        lss_ch = frage_ergebnis.get('lss_ch', {})
        lss_result = lss_ch.get('result') if lss_ch else None

        # Prüfe WH-LTS
        wh_lts = frage_ergebnis.get('wh_lts', {})
        wh_result = wh_lts.get('result') if wh_lts else None

        # Frage ist unbeantwortet wenn EINES der Systeme keine Auswahl hat
        if not lss_result or not wh_result:
            return index

    return 0  # Alle beantwortet, starte bei 0


# ==================== GWH ABNAHMETEST ROUTES ====================

@gwh_bp.route('/projekt/<int:projekt_id>/gwh-abnahmetest', methods=['GET'])
@login_required
def gwh_abnahmetest(projekt_id):
    """
    GWH-Abnahmetest Übersichtsseite (Gasweichenheizung) für ein Projekt.

    Zeigt eine Navigations-Übersicht mit Links zu allen Test-Seiten.
    Alle Tests werden auf separaten Seiten durchgeführt.

    Args:
        projekt_id: ID des Projekts

    Returns:
        HTML-Seite (gwh_abnahmetest.html) mit Navigations-Übersicht
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein GWH-Projekt ist
    if projekt.energie != 'GWH':
        flash('Diese Testseite ist nur für GWH-Projekte verfügbar!', 'error')
        return redirect(url_for('ewh.projekt_abnahmetest', projekt_id=projekt_id))

    # Lade GWH-Konfigurationen
    hgls_config = HGLSConfig.query.filter_by(projekt_id=projekt_id).first()
    zsk_configs = ZSKConfig.query.filter_by(projekt_id=projekt_id).order_by(ZSKConfig.reihenfolge).all()
    gwh_meteostationen = GWHMeteostation.query.filter_by(projekt_id=projekt_id).order_by(GWHMeteostation.reihenfolge).all()

    # Info-Meldung wenn keine ZSK konfiguriert
    if not zsk_configs:
        flash('Hinweis: Für dieses Projekt sind noch keine ZSK konfiguriert. Bitte konfigurieren Sie zunächst ZSK in der Konfiguration.', 'info')

    # Fortschrittsberechnung für Parameter-Prüfungen
    from parameter_definitionen import ZSK_PARAMETER, HGLS_PARAMETER
    from models import ZSKParameterPruefung, HGLSParameterPruefung
    from sqlalchemy import or_

    # ==================== FORTSCHRITTSBERECHNUNG (PROZENT) ====================

    def calc_percent(beantwortet, gesamt):
        """Berechnet Prozent, gibt 0 zurück wenn gesamt=0"""
        return int((beantwortet / gesamt) * 100) if gesamt > 0 else 0

    # GWH-Anlage Fortschritt
    anlage_fragen_count = TestQuestion.query.filter_by(komponente_typ='GWH_Anlage').count()
    anlage_beantwortet = db.session.query(AbnahmeTestResult.test_question_id).filter_by(
        projekt_id=projekt_id
    ).join(TestQuestion).filter(
        TestQuestion.komponente_typ == 'GWH_Anlage'
    ).distinct().count()
    anlage_percent = calc_percent(anlage_beantwortet, anlage_fragen_count)

    # HGLS Fortschritt
    hgls_fragen_count = TestQuestion.query.filter_by(komponente_typ='HGLS').count() if hgls_config else 0
    hgls_beantwortet = 0
    hgls_percent = 0
    if hgls_config and hgls_fragen_count > 0:
        hgls_beantwortet = db.session.query(AbnahmeTestResult.test_question_id).filter_by(
            projekt_id=projekt_id
        ).join(TestQuestion).filter(
            TestQuestion.komponente_typ == 'HGLS'
        ).distinct().count()
        hgls_percent = calc_percent(hgls_beantwortet, hgls_fragen_count)

    # HGLS-Parameter-Fortschritt
    hgls_param_percent = 0
    if hgls_config:
        hgls_param_count = HGLSParameterPruefung.query.filter_by(
            projekt_id=projekt_id
        ).filter(
            or_(
                HGLSParameterPruefung.geprueft == True,
                HGLSParameterPruefung.nicht_testbar == True
            )
        ).count()
        hgls_param_percent = calc_percent(hgls_param_count, len(HGLS_PARAMETER))

    # ZSK Fragen zählen (für Allgemein-Fortschritt)
    zsk_fragen_count = TestQuestion.query.filter_by(komponente_typ='ZSK').count()

    # ZSK-Parameter-Fortschritt für jeden ZSK
    zsk_param_fortschritt = {}
    for zsk in zsk_configs:
        geprueft_count = ZSKParameterPruefung.query.filter_by(
            projekt_id=projekt_id,
            zsk_nummer=zsk.zsk_nummer
        ).filter(
            or_(
                ZSKParameterPruefung.geprueft == True,
                ZSKParameterPruefung.nicht_testbar == True
            )
        ).count()
        percent = calc_percent(geprueft_count, len(ZSK_PARAMETER))
        zsk_param_fortschritt[zsk.zsk_nummer] = {'percent': percent}

    # Teile-Fortschritt pro ZSK (Multi-Spalten: Fragen × Teile)
    teile_fragen_count = TestQuestion.query.filter_by(komponente_typ='GWH_Teile').count()
    teile_fortschritt = {}
    for zsk in zsk_configs:
        anzahl_teile = zsk.anzahl_teile or 0
        if teile_fragen_count > 0 and anzahl_teile > 0:
            # Total = Anzahl Fragen × Anzahl Teile
            teile_total = teile_fragen_count * anzahl_teile
            # Spalten für diese ZSK
            teil_spalten = [f'Teil {str(i).zfill(2)}' for i in range(1, anzahl_teile + 1)]
            # Zähle alle Ergebnisse für diese ZSK und diese Spalten
            teile_beantwortet = AbnahmeTestResult.query.filter_by(
                projekt_id=projekt_id,
                komponente_index=zsk.zsk_nummer
            ).join(TestQuestion).filter(
                TestQuestion.komponente_typ == 'GWH_Teile',
                AbnahmeTestResult.spalte.in_(teil_spalten)
            ).count()
            percent = calc_percent(teile_beantwortet, teile_total)
            teile_fortschritt[zsk.zsk_nummer] = {'percent': percent}
        else:
            teile_fortschritt[zsk.zsk_nummer] = {'percent': 0}

    # Temperatursonde-Fortschritt pro ZSK (JEDER ZSK hat eine Temperatursonde)
    ts_fragen_count = TestQuestion.query.filter_by(komponente_typ='GWH_Temperatursonde').count()
    ts_fortschritt = {}
    for zsk in zsk_configs:
        if ts_fragen_count > 0:
            # Zähle Ergebnisse mit spalte='TS' (Single-Spalte pro ZSK)
            ts_beantwortet = AbnahmeTestResult.query.filter_by(
                projekt_id=projekt_id,
                komponente_index=zsk.zsk_nummer,
                spalte='TS'
            ).join(TestQuestion).filter(
                TestQuestion.komponente_typ == 'GWH_Temperatursonde'
            ).count()
            percent = calc_percent(ts_beantwortet, ts_fragen_count)
            ts_fortschritt[zsk.zsk_nummer] = {'percent': percent}
        else:
            ts_fortschritt[zsk.zsk_nummer] = {'percent': 0}

    # Meteostation-Fortschritt pro Meteostation
    ms_fragen_count = TestQuestion.query.filter_by(komponente_typ='GWH_Meteostation').count()
    ms_fortschritt = {}
    for ms in gwh_meteostationen:
        if ms_fragen_count > 0:
            # Alle Varianten der ms_nummer prüfen (z.B. "01", "MS 01", "MS_01")
            ms_variants = get_ms_spalte_variants(ms.ms_nummer)
            ms_beantwortet = db.session.query(AbnahmeTestResult.test_question_id).filter(
                AbnahmeTestResult.projekt_id == projekt_id,
                AbnahmeTestResult.komponente_index.in_(ms_variants)
            ).join(TestQuestion).filter(
                TestQuestion.komponente_typ == 'GWH_Meteostation'
            ).distinct().count()
            percent = calc_percent(ms_beantwortet, ms_fragen_count)
            ms_fortschritt[ms.ms_nummer] = {'percent': percent}
        else:
            ms_fortschritt[ms.ms_nummer] = {'percent': 0}

    # ZSK Allgemein-Fortschritt (Multi-Spalten: alle Fragen x alle ZSKs)
    # Fortschritt = (beantwortete Frage/ZSK-Kombinationen) / (Fragen * ZSKs)
    zsk_allgemein_percent = 0
    if zsk_fragen_count > 0 and zsk_configs:
        zsk_spalten = [zsk.zsk_nummer for zsk in zsk_configs]
        zsk_total = zsk_fragen_count * len(zsk_configs)

        # Zähle alle Ergebnisse für ZSK-Fragen mit ZSK-Spalten
        zsk_beantwortet = AbnahmeTestResult.query.filter_by(
            projekt_id=projekt_id
        ).join(TestQuestion).filter(
            TestQuestion.komponente_typ == 'ZSK',
            AbnahmeTestResult.spalte.in_(zsk_spalten)
        ).count()

        zsk_allgemein_percent = calc_percent(zsk_beantwortet, zsk_total)

    return render_template('gwh_abnahmetest.html',
                         projekt=projekt,
                         hgls_config=hgls_config,
                         zsk_configs=zsk_configs,
                         gwh_meteostationen=gwh_meteostationen,
                         # Fortschritt Allgemein (Prozent)
                         anlage_percent=anlage_percent,
                         hgls_percent=hgls_percent,
                         hgls_param_percent=hgls_param_percent,
                         zsk_allgemein_percent=zsk_allgemein_percent,
                         # Fortschritt pro ZSK (Prozent)
                         zsk_param_fortschritt=zsk_param_fortschritt,
                         teile_fortschritt=teile_fortschritt,
                         ts_fortschritt=ts_fortschritt,
                         ms_fortschritt=ms_fortschritt)


# ==================== GWH PDF-EXPORT ====================
@gwh_bp.route('/projekt/<int:projekt_id>/gwh-test/anlage', methods=['GET', 'POST'])
@login_required
def gwh_test_anlage(projekt_id):
    """
    GWH-Anlage Test-Seite.

    GET: Zeigt Test-Seite für GWH-Anlage Tests
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts

    Returns:
        GET: HTML-Seite (gwh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein GWH-Projekt ist
    if projekt.energie != 'GWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein GWH-Projekt'}), 400
        flash('Diese Testseite ist nur für GWH-Projekte verfügbar!', 'error')
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
    komponente_typ = 'GWH_Anlage'

    # Lade alle Testfragen für GWH_Anlage
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse (WICHTIG: Filter muss mit POST übereinstimmen!)
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id,
        komponente_index='',
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
        'erwartetes_ergebnis': f.erwartetes_ergebnis or '',
        'screenshot_pfad': f.screenshot_pfad or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse)

    return render_template('gwh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label='GWH-Anlage',
                         fragen=testfragen,
                         spalten=['Anlage'],
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))


@gwh_bp.route('/projekt/<int:projekt_id>/gwh-test/hgls', methods=['GET', 'POST'])
@login_required
def gwh_test_hgls(projekt_id):
    """
    HGLS Test-Seite.

    GET: Zeigt Test-Seite für HGLS Tests
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts

    Returns:
        GET: HTML-Seite (gwh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein GWH-Projekt ist
    if projekt.energie != 'GWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein GWH-Projekt'}), 400
        flash('Diese Testseite ist nur für GWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob HGLS konfiguriert ist
    hgls_config = HGLSConfig.query.filter_by(projekt_id=projekt_id).first()
    if not hgls_config:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Keine HGLS konfiguriert'}), 400
        flash('Für dieses Projekt ist keine HGLS konfiguriert!', 'warning')
        return redirect(url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        try:
            data = request.get_json()

            # Speichere die Ergebnisse in der Datenbank
            for question_id_str, systems in data.items():
                question_id = int(question_id_str)

                # Lösche alte Einträge für diese Frage
                AbnahmeTestResult.query.filter_by(
                    projekt_id=projekt_id,
                    test_question_id=question_id,
                    komponente_index='',
                    spalte='HGLS'
                ).delete()

                # Erstelle neue Einträge
                result = AbnahmeTestResult(
                    projekt_id=projekt_id,
                    test_question_id=question_id,
                    komponente_index='',
                    spalte='HGLS',
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
    komponente_typ = 'HGLS'

    # Lade alle Testfragen für HGLS
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse (WICHTIG: Filter muss mit POST übereinstimmen!)
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id,
        komponente_index='',
        spalte='HGLS'
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
        'erwartetes_ergebnis': f.erwartetes_ergebnis or '',
        'screenshot_pfad': f.screenshot_pfad or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse)

    return render_template('gwh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label='HGLS',
                         fragen=testfragen,
                         spalten=['HGLS'],
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))


@gwh_bp.route('/projekt/<int:projekt_id>/gwh-test/zsk', methods=['GET', 'POST'])
@login_required
def gwh_test_zsk_allgemein(projekt_id):
    """
    ZSK Allgemein Test-Seite - Multi-Spalten-Design.

    Zeigt alle ZSK-Tests auf einer Seite mit allen ZSKs als Spalten
    (ZSK 01, ZSK 02, etc.).

    GET: Zeigt Test-Seite für ZSK Tests
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts

    Returns:
        GET: HTML-Seite (gwh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein GWH-Projekt ist
    if projekt.energie != 'GWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein GWH-Projekt'}), 400
        flash('Diese Testseite ist nur für GWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Alle ZSKs für dieses Projekt laden
    zsk_configs = ZSKConfig.query.filter_by(projekt_id=projekt_id).order_by(ZSKConfig.reihenfolge).all()

    # Normalisiere alle ZSK-Nummern auf das Format "ZSK XX"
    spalten = [normalize_zsk_nummer(zsk.zsk_nummer) for zsk in zsk_configs]  # ['ZSK 01', 'ZSK 02', ...]

    # Generiere alle möglichen Varianten für DB-Abfragen (für Rückwärtskompatibilität)
    all_spalte_variants = []
    spalte_to_normalized = {}  # Mapping von Variante → normalisierte Spalte
    for spalte in spalten:
        variants = get_zsk_spalte_variants(spalte)
        all_spalte_variants.extend(variants)
        for v in variants:
            spalte_to_normalized[v] = spalte


    if not spalten:
        flash('Keine ZSK konfiguriert. Bitte konfigurieren Sie zunächst ZSK.', 'warning')
        return redirect(url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        # Format: { question_id: { spalte: { lss_ch: {result, bemerkung}, wh_lts: {result, bemerkung} } } }
        try:
            data = request.get_json()

            for question_id_str, spalten_data in data.items():
                question_id = int(question_id_str)

                # Iteriere über alle Spalten (ZSK 01, ZSK 02, etc.)
                for spalte, systems in spalten_data.items():

                    # Lösche alte Einträge für diese Frage und Spalte (alle möglichen Formate)
                    spalte_variants = get_zsk_spalte_variants(spalte)

                    deleted_total = 0
                    for variant in spalte_variants:
                        # Lösche mit verschiedenen komponente_index Varianten
                        for ki_variant in spalte_variants + ['', 'ZSK']:
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
    komponente_typ = 'ZSK'

    # Lade alle Testfragen für ZSK
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
        AbnahmeTestResult.spalte.in_(all_spalte_variants)  # Alle Varianten suchen
    ).all()

    for result in results:
        frage_id = result.test_question_id
        db_spalte = result.spalte

        # Mappe die DB-Spalte auf die normalisierte Spalte
        normalized_spalte = spalte_to_normalized.get(db_spalte, db_spalte)

        if frage_id not in ergebnisse:
            ergebnisse[frage_id] = {}

        # Speichere unter der normalisierten Spalte (Frontend erwartet "ZSK 01" etc.)
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
        'erwartetes_ergebnis': f.erwartetes_ergebnis or '',
        'screenshot_pfad': f.screenshot_pfad or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage (für Multi-Spalten)
    first_unanswered = 0
    for i, frage in enumerate(testfragen):
        frage_id = frage.id
        if frage_id not in ergebnisse:
            first_unanswered = i
            break
        # Prüfe ob mindestens eine Spalte beantwortet ist
        has_answer = False
        for spalte in spalten:
            if spalte in ergebnisse.get(frage_id, {}):
                erg = ergebnisse[frage_id][spalte]
                if erg.get('lss_ch', {}).get('result') or erg.get('wh_lts', {}).get('result'):
                    has_answer = True
                    break
        if not has_answer:
            first_unanswered = i
            break
    else:
        # Alle Fragen haben mindestens eine Antwort
        first_unanswered = 0

    return render_template('gwh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label='ZSK',
                         fragen=testfragen,
                         spalten=spalten,
                         multi_spalten=True,  # ZSK-Allgemein verwendet immer Multi-Spalten-Format
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))


@gwh_bp.route('/projekt/<int:projekt_id>/gwh-test/zsk/<zsk_nummer>', methods=['GET', 'POST'])
@login_required
def gwh_test_zsk(projekt_id, zsk_nummer):
    """
    ZSK Test-Seite - zeigt Tests für eine spezifische ZSK.

    GET: Zeigt Test-Seite für ZSK Tests (eine Spalte: ZSK-Name)
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts
        zsk_nummer: ZSK-Nummer (z.B. "ZSK 01", "ZSK 02")

    Returns:
        GET: HTML-Seite (gwh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein GWH-Projekt ist
    if projekt.energie != 'GWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein GWH-Projekt'}), 400
        flash('Diese Testseite ist nur für GWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfe ob ZSK existiert
    zsk_config = ZSKConfig.query.filter_by(projekt_id=projekt_id, zsk_nummer=zsk_nummer).first()

    if not zsk_config:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'ZSK {zsk_nummer} nicht konfiguriert'}), 400
        flash(f'ZSK {zsk_nummer} ist für dieses Projekt nicht konfiguriert!', 'warning')
        return redirect(url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))

    # Eine Spalte für diese ZSK
    spalten = [zsk_nummer]
    # komponente_index ist die ZSK-Nummer (z.B. "ZSK 01")
    komponente_index = zsk_nummer

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        try:
            data = request.get_json()

            # Speichere die Ergebnisse in der Datenbank
            for question_id_str, systems in data.items():
                question_id = int(question_id_str)

                # Lösche alte Einträge für diese Frage und diese ZSK
                deleted = AbnahmeTestResult.query.filter_by(
                    projekt_id=projekt_id,
                    test_question_id=question_id,
                    komponente_index=komponente_index,
                    spalte=zsk_nummer
                ).delete()

                # Erstelle neuen Eintrag
                result = AbnahmeTestResult(
                    projekt_id=projekt_id,
                    test_question_id=question_id,
                    komponente_index=komponente_index,
                    spalte=zsk_nummer,
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
    komponente_typ = 'ZSK'

    # Lade alle Testfragen für ZSK
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse für diese ZSK
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id,
        komponente_index=komponente_index,
        spalte=zsk_nummer
    ).filter(
        AbnahmeTestResult.test_question_id.in_([f.id for f in testfragen]) if testfragen else False
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
        'erwartetes_ergebnis': f.erwartetes_ergebnis or '',
        'screenshot_pfad': f.screenshot_pfad or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse)

    return render_template('gwh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label=f'ZSK (allgemein) - {zsk_nummer}',
                         fragen=testfragen,
                         spalten=spalten,
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))


@gwh_bp.route('/projekt/<int:projekt_id>/gwh-test/teile/<zsk_nummer>', methods=['GET', 'POST'])
@login_required
def gwh_test_teile(projekt_id, zsk_nummer):
    """
    Teile Test-Seite - Multi-Spalten-Design.

    Zeigt alle Teile einer ZSK als Spalten (Teil 01, Teil 02, ...).

    GET: Zeigt Test-Seite für Teile Tests
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts
        zsk_nummer: ZSK-Nummer (z.B. "ZSK 01", "ZSK 02")

    Returns:
        GET: HTML-Seite (gwh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein GWH-Projekt ist
    if projekt.energie != 'GWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein GWH-Projekt'}), 400
        flash('Diese Testseite ist nur für GWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Lade ZSK-Konfiguration für die angegebene ZSK-Nummer (versuche alle Varianten)
    zsk_variants = get_zsk_spalte_variants(zsk_nummer)
    zsk_config = None
    for variant in zsk_variants:
        zsk_config = ZSKConfig.query.filter_by(projekt_id=projekt_id, zsk_nummer=variant).first()
        if zsk_config:
            break

    if not zsk_config:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'ZSK {zsk_nummer} nicht konfiguriert'}), 400
        flash(f'ZSK {zsk_nummer} ist für dieses Projekt nicht konfiguriert!', 'warning')
        return redirect(url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))

    # Normalisiere zsk_nummer auf das Standard-Format
    normalized_zsk = normalize_zsk_nummer(zsk_nummer)

    # Spalten aus Anzahl Teile erstellen (Teil 01, Teil 02, ...)
    anzahl_teile = zsk_config.anzahl_teile or 0
    if anzahl_teile == 0:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'ZSK {zsk_nummer} hat keine Teile konfiguriert'}), 400
        flash(f'ZSK {zsk_nummer} hat keine Teile konfiguriert!', 'warning')
        return redirect(url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))

    spalten = [f"Teil {str(i).zfill(2)}" for i in range(1, anzahl_teile + 1)]
    # komponente_index identifiziert die ZSK (normalisiert), spalte identifiziert das Teil
    komponente_index = normalized_zsk

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        # Format: { question_id: { spalte: { lss_ch: {result, bemerkung}, wh_lts: {result, bemerkung} } } }
        try:
            data = request.get_json()

            for question_id_str, spalten_data in data.items():
                question_id = int(question_id_str)

                # Iteriere über alle Spalten (Teil 01, Teil 02, etc.)
                for spalte, systems in spalten_data.items():
                    # Lösche alte Einträge für diese Frage und Spalte (alle möglichen Formate)
                    ki_variants = get_zsk_spalte_variants(normalized_zsk)
                    for ki_variant in ki_variants:
                        AbnahmeTestResult.query.filter_by(
                            projekt_id=projekt_id,
                            test_question_id=question_id,
                            komponente_index=ki_variant,
                            spalte=spalte
                        ).delete()

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
    komponente_typ = 'GWH_Teile'

    # Lade alle Testfragen für GWH_Teile
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Generiere alle möglichen komponente_index Varianten für Rückwärtskompatibilität
    komponente_index_variants = get_zsk_spalte_variants(normalized_zsk)

    # Lade bestehende Ergebnisse - pro Frage und pro Spalte (Teil)
    # Struktur: ergebnisse[frage_id][spalte] = {lss_ch: {...}, wh_lts: {...}}
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id
    ).filter(
        AbnahmeTestResult.komponente_index.in_(komponente_index_variants),
        AbnahmeTestResult.test_question_id.in_([f.id for f in testfragen]) if testfragen else False,
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
        'erwartetes_ergebnis': f.erwartetes_ergebnis or '',
        'screenshot_pfad': f.screenshot_pfad or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage (für Multi-Spalten)
    first_unanswered = 0
    for i, frage in enumerate(testfragen):
        frage_id = frage.id
        if frage_id not in ergebnisse:
            first_unanswered = i
            break
        # Prüfe ob mindestens eine Spalte beantwortet ist
        has_answer = False
        for spalte in spalten:
            if spalte in ergebnisse.get(frage_id, {}):
                erg = ergebnisse[frage_id][spalte]
                if erg.get('lss_ch', {}).get('result') or erg.get('wh_lts', {}).get('result'):
                    has_answer = True
                    break
        if not has_answer:
            first_unanswered = i
            break
    else:
        first_unanswered = 0

    return render_template('gwh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label=f'Teile - {zsk_nummer}',
                         fragen=testfragen,
                         spalten=spalten,
                         multi_spalten=True,  # Teile verwendet immer Multi-Spalten-Format
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))


@gwh_bp.route('/projekt/<int:projekt_id>/gwh-test/temperatursonde/<zsk_nummer>', methods=['GET', 'POST'])
@login_required
def gwh_test_temperatursonde(projekt_id, zsk_nummer):
    """
    Temperatursonde Test-Seite - zeigt Temperatursonde-Tests für eine ZSK.

    GET: Zeigt Test-Seite für Temperatursonde Tests (eine Spalte: TS)
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts
        zsk_nummer: ZSK-Nummer (z.B. "01", "02")

    Returns:
        GET: HTML-Seite (gwh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein GWH-Projekt ist
    if projekt.energie != 'GWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein GWH-Projekt'}), 400
        flash('Diese Testseite ist nur für GWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Lade ZSK-Konfiguration für die angegebene ZSK-Nummer (versuche alle Varianten)
    zsk_variants = get_zsk_spalte_variants(zsk_nummer)
    zsk_config = None
    for variant in zsk_variants:
        zsk_config = ZSKConfig.query.filter_by(projekt_id=projekt_id, zsk_nummer=variant).first()
        if zsk_config:
            break

    if not zsk_config:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'ZSK {zsk_nummer} nicht konfiguriert'}), 400
        flash(f'ZSK {zsk_nummer} ist für dieses Projekt nicht konfiguriert!', 'warning')
        return redirect(url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))

    # Jeder ZSK hat immer eine Temperatursonde (keine Prüfung nötig)

    # Spalte für Temperatursonde
    spalten = ['TS']
    # Normalisiere zsk_nummer auf das Standard-Format
    normalized_zsk = normalize_zsk_nummer(zsk_nummer)
    komponente_index = normalized_zsk
    komponente_index_variants = get_zsk_spalte_variants(normalized_zsk)

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        try:
            data = request.get_json()

            # Speichere die Ergebnisse in der Datenbank
            for question_id_str, systems in data.items():
                question_id = int(question_id_str)

                # Lösche alte Einträge für diese Frage (alle möglichen Formate)
                deleted_total = 0
                for ki_variant in komponente_index_variants:
                    deleted = AbnahmeTestResult.query.filter_by(
                        projekt_id=projekt_id,
                        test_question_id=question_id,
                        komponente_index=ki_variant,
                        spalte='TS'
                    ).delete()
                    deleted_total += deleted

                # Erstelle neuen Eintrag
                result = AbnahmeTestResult(
                    projekt_id=projekt_id,
                    test_question_id=question_id,
                    komponente_index=komponente_index,
                    spalte='TS',
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
    komponente_typ = 'GWH_Temperatursonde'

    # Lade alle Testfragen für GWH_Temperatursonde
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse für diese ZSK (alle möglichen Formate)
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id,
        spalte='TS'
    ).filter(
        AbnahmeTestResult.komponente_index.in_(komponente_index_variants),
        AbnahmeTestResult.test_question_id.in_([f.id for f in testfragen]) if testfragen else False
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
        'erwartetes_ergebnis': f.erwartetes_ergebnis or '',
        'screenshot_pfad': f.screenshot_pfad or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Berechne erste unbeantwortete Frage
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse)

    return render_template('gwh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label=f'Temperatursonde - ZSK {zsk_nummer}',
                         fragen=testfragen,
                         spalten=spalten,
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))


@gwh_bp.route('/projekt/<int:projekt_id>/gwh-test/meteostation/<ms_nummer>', methods=['GET', 'POST'])
@login_required
def gwh_test_meteostation(projekt_id, ms_nummer):
    """
    Meteostation Test-Seite - zeigt Meteostation-Tests für eine spezifische Meteostation.

    GET: Zeigt Test-Seite für Meteostation Tests (eine Spalte: MS-Name)
    POST: Speichert Testergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts
        ms_nummer: Meteostation-Nummer (z.B. "01", "02")

    Returns:
        GET: HTML-Seite (gwh_test_seite.html)
        POST: JSON-Response mit success/error
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein GWH-Projekt ist
    if projekt.energie != 'GWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein GWH-Projekt'}), 400
        flash('Diese Testseite ist nur für GWH-Projekte verfügbar!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Lade Meteostation für die angegebene Nummer (versuche alle Varianten)
    ms_variants = get_ms_spalte_variants(ms_nummer)
    meteostation = None
    for variant in ms_variants:
        meteostation = GWHMeteostation.query.filter_by(projekt_id=projekt_id, ms_nummer=variant).first()
        if meteostation:
            break

    if not meteostation:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'Meteostation {ms_nummer} nicht konfiguriert'}), 400
        flash(f'Meteostation {ms_nummer} ist für dieses Projekt nicht konfiguriert!', 'warning')
        return redirect(url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))

    # Spalte mit Meteostation-Name
    spalten = [meteostation.name]
    # Normalisiere ms_nummer auf das Standard-Format
    normalized_ms = normalize_ms_nummer(ms_nummer)
    komponente_index = normalized_ms
    komponente_index_variants = get_ms_spalte_variants(normalized_ms)

    if request.method == 'POST':
        # POST-Handler für Speichern der Test-Ergebnisse (AJAX)
        try:
            data = request.get_json()

            # Speichere die Ergebnisse in der Datenbank
            for question_id_str, systems in data.items():
                question_id = int(question_id_str)

                # Lösche alte Einträge für diese Frage (alle möglichen Formate)
                deleted_total = 0
                for ki_variant in komponente_index_variants:
                    deleted = AbnahmeTestResult.query.filter_by(
                        projekt_id=projekt_id,
                        test_question_id=question_id,
                        komponente_index=ki_variant,
                        spalte=meteostation.name
                    ).delete()
                    deleted_total += deleted

                # Erstelle neuen Eintrag
                result = AbnahmeTestResult(
                    projekt_id=projekt_id,
                    test_question_id=question_id,
                    komponente_index=komponente_index,
                    spalte=meteostation.name,
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
    komponente_typ = 'GWH_Meteostation'

    # Lade alle Testfragen für GWH_Meteostation
    testfragen = TestQuestion.query.filter_by(
        komponente_typ=komponente_typ
    ).order_by(TestQuestion.reihenfolge).all()

    # Lade bestehende Ergebnisse für diese Meteostation (alle möglichen Formate)
    ergebnisse = {}
    results = AbnahmeTestResult.query.filter_by(
        projekt_id=projekt_id,
        spalte=meteostation.name
    ).filter(
        AbnahmeTestResult.komponente_index.in_(komponente_index_variants),
        AbnahmeTestResult.test_question_id.in_([f.id for f in testfragen]) if testfragen else False
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
        'erwartetes_ergebnis': f.erwartetes_ergebnis or '',
        'screenshot_pfad': f.screenshot_pfad or '',
        'preset_antworten': f.preset_antworten or {}
    } for f in testfragen], ensure_ascii=False)

    ergebnisse_json = json.dumps(ergebnisse, ensure_ascii=False)

    # Erste unbeantwortete Frage finden
    first_unanswered = get_first_unanswered_index(testfragen, ergebnisse)

    return render_template('gwh_test_seite.html',
                         projekt=projekt,
                         komponente_typ=komponente_typ,
                         komponente_label=f'Meteostation - {meteostation.name}',
                         fragen=testfragen,
                         spalten=spalten,
                         fragen_json=fragen_json,
                         ergebnisse_json=ergebnisse_json,
                         first_unanswered_index=first_unanswered,
                         zurueck_url=url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))


@gwh_bp.route('/projekt/<int:projekt_id>/zsk-parameter/<zsk_nummer>', methods=['GET', 'POST'])
@login_required
def zsk_parameter(projekt_id, zsk_nummer):
    """
    ZSK Parameter-Prüfung für ein GWH-Projekt.

    GET: Zeigt Parameter-Prüfungsformular für einen spezifischen ZSK
    POST: Speichert Parameter-Prüfungsergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts
        zsk_nummer: ZSK-Nummer (z.B. "01", "02")

    Returns:
        GET: HTML-Formular (zsk_parameter.html)
        POST: JSON-Response mit success/error
    """
    from parameter_definitionen import ZSK_PARAMETER
    from models import ZSKParameterPruefung, ZSKConfig

    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein GWH-Projekt ist
    if projekt.energie != 'GWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein GWH-Projekt'}), 400
        flash('Diese Seite ist nur für GWH-Projekte verfügbar!', 'error')
        return redirect(url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))

    # Prüfen ob ZSK mit dieser Nummer existiert
    zsk_config = ZSKConfig.query.filter_by(projekt_id=projekt_id, zsk_nummer=zsk_nummer).first()

    if not zsk_config:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': f'ZSK {zsk_nummer} nicht gefunden'}), 404
        flash(f'ZSK {zsk_nummer} nicht in diesem Projekt konfiguriert!', 'error')
        return redirect(url_for('konfiguration.gwh_konfiguration', projekt_id=projekt_id))

    if request.method == 'POST':
        # POST-Handler: Speichere Parameter-Prüfungsergebnisse
        try:
            parameter_data = request.get_json()

            if not parameter_data:
                return jsonify({'success': False, 'error': 'Keine Daten empfangen'}), 400

            # Für jeden Parameter
            for param_name, param_values in parameter_data.items():
                ist_wert = param_values.get('ist_wert', '').strip() if param_values.get('ist_wert') else ''

                # Explizite Boolean-Konvertierung (robust gegen String-Werte)
                geprueft_raw = param_values.get('geprueft', False)
                nicht_testbar_raw = param_values.get('nicht_testbar', False)

                # Konvertiere zu echten Booleans (für den Fall dass Strings ankommen)
                if isinstance(geprueft_raw, bool):
                    geprueft = geprueft_raw
                else:
                    geprueft = str(geprueft_raw).lower() in ('true', '1', 'yes')

                if isinstance(nicht_testbar_raw, bool):
                    nicht_testbar = nicht_testbar_raw
                else:
                    nicht_testbar = str(nicht_testbar_raw).lower() in ('true', '1', 'yes')

                # Suche bestehenden Eintrag oder erstelle neuen
                pruefung = ZSKParameterPruefung.query.filter_by(
                    projekt_id=projekt_id,
                    zsk_nummer=zsk_nummer,
                    parameter_name=param_name
                ).first()

                if not pruefung:
                    pruefung = ZSKParameterPruefung(
                        projekt_id=projekt_id,
                        zsk_nummer=zsk_nummer,
                        parameter_name=param_name
                    )
                    db.session.add(pruefung)

                # Update Werte
                pruefung.ist_wert = ist_wert if ist_wert else None
                pruefung.geprueft = geprueft
                pruefung.nicht_testbar = nicht_testbar

                if geprueft:
                    pruefung.geprueft_am = datetime.utcnow()
                    pruefung.geprueft_von = current_user.username
                else:
                    pruefung.geprueft_am = None
                    pruefung.geprueft_von = None

            db.session.commit()

            # Zähle erledigte Parameter (geprüft ODER nicht testbar)
            from sqlalchemy import or_
            geprueft_count = ZSKParameterPruefung.query.filter_by(
                projekt_id=projekt_id,
                zsk_nummer=zsk_nummer
            ).filter(
                or_(
                    ZSKParameterPruefung.geprueft == True,
                    ZSKParameterPruefung.nicht_testbar == True
                )
            ).count()

            return jsonify({
                'success': True,
                'message': 'Parameter gespeichert',
                'geprueft_count': geprueft_count,
                'total_count': len(ZSK_PARAMETER)
            })

        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Fehler beim Speichern: {str(e)}'}), 500

    # GET-Request: Lade bestehende Prüfungen
    bestehende_pruefungen = {}
    pruefungen = ZSKParameterPruefung.query.filter_by(
        projekt_id=projekt_id,
        zsk_nummer=zsk_nummer
    ).all()

    for pruefung in pruefungen:
        bestehende_pruefungen[pruefung.parameter_name] = {
            'ist_wert': pruefung.ist_wert or '',
            # Explizite Boolean-Konvertierung (None → False)
            'geprueft': bool(pruefung.geprueft) if pruefung.geprueft is not None else False,
            'nicht_testbar': bool(pruefung.nicht_testbar) if pruefung.nicht_testbar is not None else False,
            'geprueft_am': pruefung.geprueft_am.strftime('%d.%m.%Y %H:%M') if pruefung.geprueft_am else None,
            'geprueft_von': pruefung.geprueft_von
        }

    # Lade alle ZSKs für Navigation
    alle_zsks = ZSKConfig.query.filter_by(projekt_id=projekt_id).order_by(ZSKConfig.reihenfolge).all()

    # Finde vorherigen und nächsten ZSK
    zsk_nummern = [zsk.zsk_nummer for zsk in alle_zsks]
    current_index = zsk_nummern.index(zsk_nummer) if zsk_nummer in zsk_nummern else -1

    vorheriger_zsk = zsk_nummern[current_index - 1] if current_index > 0 else None
    naechster_zsk = zsk_nummern[current_index + 1] if current_index < len(zsk_nummern) - 1 else None

    # Zähle erledigte Parameter (geprüft ODER nicht testbar)
    geprueft_count = len([p for p in bestehende_pruefungen.values() if p['geprueft'] or p['nicht_testbar']])

    return render_template('zsk_parameter.html',
                         projekt=projekt,
                         zsk_config=zsk_config,
                         zsk_nummer=zsk_nummer,
                         parameter_liste=ZSK_PARAMETER,
                         bestehende_pruefungen=bestehende_pruefungen,
                         geprueft_count=geprueft_count,
                         total_count=len(ZSK_PARAMETER),
                         vorheriger_zsk=vorheriger_zsk,
                         naechster_zsk=naechster_zsk)


@gwh_bp.route('/projekt/<int:projekt_id>/hgls-parameter', methods=['GET', 'POST'])
@login_required
def hgls_parameter(projekt_id):
    """
    HGLS Parameter-Prüfung für ein GWH-Projekt.

    GET: Zeigt Parameter-Prüfungsformular für HGLS
    POST: Speichert Parameter-Prüfungsergebnisse (AJAX, JSON)

    Args:
        projekt_id: ID des Projekts

    Returns:
        GET: HTML-Formular (hgls_parameter.html)
        POST: JSON-Response mit success/error
    """
    from parameter_definitionen import HGLS_PARAMETER
    from models import HGLSParameterPruefung, HGLSConfig

    projekt = Project.query.get(projekt_id)

    if not projekt:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen ob es ein GWH-Projekt ist
    if projekt.energie != 'GWH':
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Dieses Projekt ist kein GWH-Projekt'}), 400
        flash('Diese Seite ist nur für GWH-Projekte verfügbar!', 'error')
        return redirect(url_for('gwh.gwh_abnahmetest', projekt_id=projekt_id))

    # Prüfen ob HGLS konfiguriert ist
    hgls_config = HGLSConfig.query.filter_by(projekt_id=projekt_id).first()

    if not hgls_config:
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'HGLS nicht konfiguriert'}), 404
        flash('Für dieses Projekt ist keine HGLS konfiguriert!', 'error')
        return redirect(url_for('konfiguration.gwh_konfiguration', projekt_id=projekt_id))

    if request.method == 'POST':
        # POST-Handler: Speichere Parameter-Prüfungsergebnisse
        try:
            parameter_data = request.get_json()

            if not parameter_data:
                return jsonify({'success': False, 'error': 'Keine Daten empfangen'}), 400

            # Für jeden Parameter
            for param_name, param_values in parameter_data.items():
                ist_wert = param_values.get('ist_wert', '').strip() if param_values.get('ist_wert') else ''

                # Explizite Boolean-Konvertierung (robust gegen String-Werte)
                geprueft_raw = param_values.get('geprueft', False)
                nicht_testbar_raw = param_values.get('nicht_testbar', False)

                # Konvertiere zu echten Booleans (für den Fall dass Strings ankommen)
                if isinstance(geprueft_raw, bool):
                    geprueft = geprueft_raw
                else:
                    geprueft = str(geprueft_raw).lower() in ('true', '1', 'yes')

                if isinstance(nicht_testbar_raw, bool):
                    nicht_testbar = nicht_testbar_raw
                else:
                    nicht_testbar = str(nicht_testbar_raw).lower() in ('true', '1', 'yes')

                # Suche bestehenden Eintrag oder erstelle neuen
                pruefung = HGLSParameterPruefung.query.filter_by(
                    projekt_id=projekt_id,
                    parameter_name=param_name
                ).first()

                if not pruefung:
                    pruefung = HGLSParameterPruefung(
                        projekt_id=projekt_id,
                        parameter_name=param_name
                    )
                    db.session.add(pruefung)

                # Update Werte
                pruefung.ist_wert = ist_wert if ist_wert else None
                pruefung.geprueft = geprueft
                pruefung.nicht_testbar = nicht_testbar

                if geprueft:
                    pruefung.geprueft_am = datetime.utcnow()
                    pruefung.geprueft_von = current_user.username
                else:
                    pruefung.geprueft_am = None
                    pruefung.geprueft_von = None

            db.session.commit()

            # Zähle erledigte Parameter (geprüft ODER nicht testbar)
            from sqlalchemy import or_
            geprueft_count = HGLSParameterPruefung.query.filter_by(
                projekt_id=projekt_id
            ).filter(
                or_(
                    HGLSParameterPruefung.geprueft == True,
                    HGLSParameterPruefung.nicht_testbar == True
                )
            ).count()

            return jsonify({
                'success': True,
                'message': 'Parameter gespeichert',
                'geprueft_count': geprueft_count,
                'total_count': len(HGLS_PARAMETER)
            })

        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Fehler beim Speichern: {str(e)}'}), 500

    # GET-Request: Lade bestehende Prüfungen
    bestehende_pruefungen = {}
    pruefungen = HGLSParameterPruefung.query.filter_by(projekt_id=projekt_id).all()

    for pruefung in pruefungen:
        bestehende_pruefungen[pruefung.parameter_name] = {
            'ist_wert': pruefung.ist_wert or '',
            # Explizite Boolean-Konvertierung (None → False)
            'geprueft': bool(pruefung.geprueft) if pruefung.geprueft is not None else False,
            'nicht_testbar': bool(pruefung.nicht_testbar) if pruefung.nicht_testbar is not None else False,
            'geprueft_am': pruefung.geprueft_am.strftime('%d.%m.%Y %H:%M') if pruefung.geprueft_am else None,
            'geprueft_von': pruefung.geprueft_von
        }

    # Zähle erledigte Parameter (geprüft ODER nicht testbar)
    geprueft_count = len([p for p in bestehende_pruefungen.values() if p['geprueft'] or p['nicht_testbar']])

    return render_template('hgls_parameter.html',
                         projekt=projekt,
                         hgls_config=hgls_config,
                         parameter_liste=HGLS_PARAMETER,
                         bestehende_pruefungen=bestehende_pruefungen,
                         geprueft_count=geprueft_count,
                         total_count=len(HGLS_PARAMETER))


