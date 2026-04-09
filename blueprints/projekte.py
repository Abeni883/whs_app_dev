"""
SBB Weichenheizung - Projekte Blueprint
Projekt-Verwaltung (CRUD) und Übersicht
"""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from models import db, Project, WHKConfig, ZSKConfig, HGLSConfig, GWHMeteostation, EWHMeteostation, TestQuestion, AbnahmeTestResult

projekte_bp = Blueprint('projekte', __name__)


# ==================== HELPER FUNCTIONS ====================

def parse_date_from_form(date_string, date_format='%d.%m.%Y'):
    """
    Konvertiert Datumsstring aus Formular in date-Objekt.

    Args:
        date_string: Datumsstring aus Formular (kann None oder leer sein)
        date_format: Erwartetes Datumsformat (Standard: '%d.%m.%Y')

    Returns:
        date-Objekt oder None bei leerem/ungültigem Input

    Example:
        >>> parse_date_from_form('31.12.2024')
        datetime.date(2024, 12, 31)
    """
    if not date_string or not date_string.strip():
        return None
    try:
        return datetime.strptime(date_string, date_format).date()
    except ValueError:
        return None


def calculate_all_projects_test_progress():
    """
    Berechnet den Testfortschritt für alle Projekte effizient.

    Logik:
    - Total = THEORETISCH (Testfragen × Komponenten basierend auf Projektkonfiguration)
    - Beantwortet = DB-Einträge mit mindestens einem gültigen Wert (ODER-Logik)
    - Ein Wert ist gültig wenn: NOT NULL, != 'None', != ''

    Returns:
        dict: {projekt_id: progress_percent (0-100)}
    """
    progress_dict = {}

    # 1. Alle Projekte laden
    projekte = Project.query.all()
    if not projekte:
        return progress_dict

    projekt_ids = [p.id for p in projekte]

    # 2. Alle Konfigurationen laden (EWH und GWH)
    all_whk_configs = WHKConfig.query.filter(WHKConfig.projekt_id.in_(projekt_ids)).all()
    all_zsk_configs = ZSKConfig.query.filter(ZSKConfig.projekt_id.in_(projekt_ids)).all()
    all_hgls_configs = HGLSConfig.query.filter(HGLSConfig.projekt_id.in_(projekt_ids)).all()
    all_gwh_meteostations = GWHMeteostation.query.filter(GWHMeteostation.projekt_id.in_(projekt_ids)).all()
    all_ewh_meteostations = EWHMeteostation.query.filter(EWHMeteostation.projekt_id.in_(projekt_ids)).all()

    # Gruppiere nach projekt_id
    whk_configs_by_projekt = {}
    for whk in all_whk_configs:
        whk_configs_by_projekt.setdefault(whk.projekt_id, []).append(whk)

    zsk_configs_by_projekt = {}
    for zsk in all_zsk_configs:
        zsk_configs_by_projekt.setdefault(zsk.projekt_id, []).append(zsk)

    hgls_configs_by_projekt = {}
    for hgls in all_hgls_configs:
        hgls_configs_by_projekt.setdefault(hgls.projekt_id, []).append(hgls)

    gwh_ms_by_projekt = {}
    for ms in all_gwh_meteostations:
        gwh_ms_by_projekt.setdefault(ms.projekt_id, []).append(ms)

    ewh_ms_by_projekt = {}
    for ms in all_ewh_meteostations:
        ewh_ms_by_projekt.setdefault(ms.projekt_id, []).append(ms)

    # 3. Alle TestQuestions laden und nach Komponente gruppieren
    all_test_questions = TestQuestion.query.all()
    questions_by_type = {}
    for frage in all_test_questions:
        questions_by_type.setdefault(frage.komponente_typ, []).append(frage)

    # 4. Alle AbnahmeTestResults laden
    all_results = AbnahmeTestResult.query.filter(
        AbnahmeTestResult.projekt_id.in_(projekt_ids)
    ).all()

    results_by_projekt = {}
    for result in all_results:
        results_by_projekt.setdefault(result.projekt_id, []).append(result)

    # Hilfsfunktion: Prüft ob ein Wert gültig ist (nicht NULL, nicht 'None', nicht leer)
    def ist_gueltig(wert):
        return wert is not None and wert != 'None' and wert != ''

    # 5. Berechne Fortschritt für jedes Projekt
    for projekt in projekte:
        results = results_by_projekt.get(projekt.id, [])

        if projekt.energie == 'EWH':
            # EWH-Projekt: WHKConfigs verwenden
            whk_configs = whk_configs_by_projekt.get(projekt.id, [])
            ewh_meteostations = ewh_ms_by_projekt.get(projekt.id, [])

            if not whk_configs:
                progress_dict[projekt.id] = 0
                continue

            # TOTAL = Theoretische Anzahl (Testfragen × Komponenten)
            expected_tests = 0

            # Anlage: 1 Test pro Frage
            expected_tests += len(questions_by_type.get('Anlage', []))

            # WHK: 1 Test pro WHK pro Frage
            expected_tests += len(questions_by_type.get('WHK', [])) * len(whk_configs)

            # Abgang: pro WHK pro Abgang pro Frage
            for whk in whk_configs:
                if whk.anzahl_abgaenge:
                    expected_tests += len(questions_by_type.get('Abgang', [])) * whk.anzahl_abgaenge

            # Temperatursonde: pro WHK pro Sonde pro Frage
            for whk in whk_configs:
                if whk.anzahl_temperatursonden:
                    expected_tests += len(questions_by_type.get('Temperatursonde', [])) * whk.anzahl_temperatursonden

            # Antriebsheizung: pro WHK mit AH pro Frage
            ah_count = sum(1 for whk in whk_configs if whk.hat_antriebsheizung)
            expected_tests += len(questions_by_type.get('Antriebsheizung', [])) * ah_count

            # Meteostation: pro EWH-Meteostation pro Frage
            expected_tests += len(questions_by_type.get('Meteostation', [])) * len(ewh_meteostations)

        else:
            # GWH-Projekt: ZSKConfigs verwenden
            zsk_configs = zsk_configs_by_projekt.get(projekt.id, [])
            hgls_configs = hgls_configs_by_projekt.get(projekt.id, [])
            gwh_meteostations = gwh_ms_by_projekt.get(projekt.id, [])

            if not zsk_configs:
                progress_dict[projekt.id] = 0
                continue

            # TOTAL = Theoretische Anzahl (Testfragen × Komponenten)
            expected_tests = 0

            # GWH_Anlage: 1 Test pro Frage
            expected_tests += len(questions_by_type.get('GWH_Anlage', []))

            # HGLS: 1 Test pro Frage (wenn HGLS konfiguriert)
            if hgls_configs:
                expected_tests += len(questions_by_type.get('HGLS', []))

            # ZSK: 1 Test pro ZSK pro Frage
            expected_tests += len(questions_by_type.get('ZSK', [])) * len(zsk_configs)

            # GWH_Teile: pro ZSK pro Teil pro Frage
            for zsk in zsk_configs:
                if zsk.anzahl_teile:
                    expected_tests += len(questions_by_type.get('GWH_Teile', [])) * zsk.anzahl_teile

            # GWH_Temperatursonde: pro ZSK mit TS pro Frage
            ts_count = sum(1 for zsk in zsk_configs if zsk.hat_temperatursonde)
            expected_tests += len(questions_by_type.get('GWH_Temperatursonde', [])) * ts_count

            # GWH_Meteostation: pro Meteostation pro Frage
            expected_tests += len(questions_by_type.get('GWH_Meteostation', [])) * len(gwh_meteostations)

        # Keine erwarteten Tests = 0%
        if expected_tests == 0:
            progress_dict[projekt.id] = 0
            continue

        # BEANTWORTET = DB-Einträge mit mindestens einem gültigen Wert (ODER-Logik)
        completed_tests = sum(1 for r in results if ist_gueltig(r.lss_ch_result) or ist_gueltig(r.wh_lts_result))

        # Berechne Prozentsatz (int statt round, damit 99.5% → 99% wird)
        # 100% nur wenn wirklich ALLE Tests beantwortet sind
        progress = int((completed_tests / expected_tests) * 100)
        progress_dict[projekt.id] = min(100, max(0, progress))

    return progress_dict


# ==================== ROUTES ====================

@projekte_bp.route('/')
def index():
    """Root-Route - Leitet zur Projektübersicht weiter."""
    return redirect(url_for('projekte.projekte'))


@projekte_bp.route('/projekte')
@login_required
def projekte():
    """
    Projektübersicht mit clientseitiger Live-Suche und Testfortschritt.

    Lädt alle Projekte mit berechnetem Testfortschritt.
    Filterung erfolgt clientseitig über JavaScript.

    Returns:
        HTML-Seite mit Projektliste und Fortschrittsanzeige (projekte.html)
    """
    # Alle Projekte laden, sortiert nach Erstellungsdatum (neueste zuerst)
    # Filterung erfolgt komplett clientseitig (JavaScript Live-Filter)
    alle_projekte = Project.query.order_by(Project.erstellt_am.desc()).all()

    # Testfortschritt für alle Projekte berechnen (effizient mit Bulk-Queries)
    progress_dict = calculate_all_projects_test_progress()

    return render_template('projekte.html', projekte=alle_projekte, progress_dict=progress_dict)


@projekte_bp.route('/projekt/neu', methods=['GET', 'POST'])
@login_required
def neues_projekt():
    """Neues Weichenheizungsprojekt anlegen (EWH oder GWH)."""
    if request.method == 'POST':
        # Datums-Felder konvertieren
        baumappenversion = parse_date_from_form(request.form.get('baumappenversion'), '%d.%m.%Y')
        pruefdatum = parse_date_from_form(request.form.get('pruefdatum'), '%Y-%m-%d')

        projekt = Project(
            energie=request.form['energie'],
            projektname=request.form['projektname'],
            didok_betriebspunkt=request.form.get('didok_betriebspunkt', ''),
            baumappenversion=baumappenversion,
            projektleiter_sbb=request.form.get('projektleiter_sbb', ''),
            pruefer_achermann=request.form.get('pruefer_achermann', ''),
            pruefdatum=pruefdatum,
            ibn_inbetriebnahme_jahre=request.form.get('ibn_inbetriebnahme_jahre', '').strip() or None,
            bemerkung=request.form.get('bemerkung', '')
        )
        db.session.add(projekt)
        db.session.commit()

        # Automatisch eine Standard-Meteostation anlegen
        if projekt.energie == 'EWH':
            ms = EWHMeteostation(
                projekt_id=projekt.id,
                ms_nummer='MS 01',
                reihenfolge=0
            )
            db.session.add(ms)
            db.session.commit()
        elif projekt.energie == 'GWH':
            ms = GWHMeteostation(
                projekt_id=projekt.id,
                ms_nummer='01',
                name='MS 01',
                reihenfolge=0
            )
            db.session.add(ms)
            db.session.commit()

        flash('Projekt erfolgreich angelegt!', 'success')
        return redirect(url_for('projekte.projekte'))
    return render_template('projekt_form.html', projekt=None, edit_mode=False)


@projekte_bp.route('/projekt/bearbeiten/<int:projekt_id>', methods=['GET', 'POST'])
@login_required
def projekt_bearbeiten(projekt_id):
    """Bestehendes Weichenheizungsprojekt bearbeiten."""
    projekt = Project.query.get(projekt_id)

    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    if request.method == 'POST':
        # Datums-Felder konvertieren
        baumappenversion = parse_date_from_form(request.form.get('baumappenversion'), '%d.%m.%Y')
        pruefdatum = parse_date_from_form(request.form.get('pruefdatum'), '%Y-%m-%d')

        # Bestehende Projekt-Werte aktualisieren
        projekt.energie = request.form['energie']
        projekt.projektname = request.form['projektname']
        projekt.didok_betriebspunkt = request.form.get('didok_betriebspunkt', '')
        projekt.baumappenversion = baumappenversion
        projekt.projektleiter_sbb = request.form.get('projektleiter_sbb', '')
        projekt.pruefer_achermann = request.form.get('pruefer_achermann', '')
        projekt.pruefdatum = pruefdatum
        projekt.ibn_inbetriebnahme_jahre = request.form.get('ibn_inbetriebnahme_jahre', '').strip() or None
        projekt.bemerkung = request.form.get('bemerkung', '')

        db.session.commit()
        flash('Projekt erfolgreich aktualisiert!', 'success')
        return redirect(url_for('projekte.projekte'))

    return render_template('projekt_form.html', projekt=projekt, edit_mode=True)


@projekte_bp.route('/projekt/loeschen/<int:projekt_id>')
@login_required
def projekt_loeschen(projekt_id):
    """
    Projekt löschen (mit Schutz vor zugeordneten Tests).

    Args:
        projekt_id: ID des zu löschenden Projekts

    Returns:
        Redirect zur Projektübersicht mit Flash-Message
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    # Prüfen, ob dem Projekt noch Tests zugeordnet sind
    if projekt.tests and len(projekt.tests) > 0:
        flash(f'Projekt kann nicht gelöscht werden, da noch {len(projekt.tests)} Test(s) zugeordnet sind. Bitte löschen Sie zuerst die zugehörigen Tests.', 'warning')
        return redirect(url_for('projekte.projekte'))

    # Projekt löschen
    projektname = projekt.projektname
    db.session.delete(projekt)
    db.session.commit()
    flash(f'Projekt "{projektname}" erfolgreich gelöscht!', 'success')
    return redirect(url_for('projekte.projekte'))
