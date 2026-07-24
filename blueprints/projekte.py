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

    KANONISCHE Logik (Phase 2b / O-3): identisch zur EWH-Detailseite
    (blueprints/ewh.py calc_component_percent) und zu blueprints/gwh.py, damit
    Übersicht und Detailseite konsistent sind. Uebernommen aus dem PROD-Repo
    (sbb-weichenheizung, HEAD fd609f7); ersetzt die frühere DEV-Version, die
    ueberzaehlte (ODER-Logik + stale Results + keine Deckelung pro Komponente).

    - Pro Komponente: Total = Anzahl Fragen × Anzahl konfigurierter Spalten/Instanzen.
    - Beantwortet zählt nur Results, deren komponente_index zur AKTUELLEN
      Projektkonfiguration passt (stale Results gelöschter WHKs/ZSKs/MS werden
      ignoriert) UND deren beide System-Spalten (lss_ch_result, wh_lts_result)
      einen gültigen Wert in ['richtig','falsch','nicht_testbar'] haben (UND-Logik).
    - Beantwortet wird pro Komponente auf das jeweilige Total gedeckelt
      (entspricht dem `min(..., 100)` in der Detail-Logik).

    Keine Adaption gegenüber PROD nötig: die Funktion nutzt nur Modelle, die auch
    in DEV existieren; Steuerungen haben keine Abnahmetests und gehen nicht ein.

    Returns:
        dict: {projekt_id: progress_percent (0-100)}
    """
    progress_dict = {}

    projekte = Project.query.all()
    if not projekte:
        return progress_dict

    projekt_ids = [p.id for p in projekte]

    all_whk_configs = WHKConfig.query.filter(WHKConfig.projekt_id.in_(projekt_ids)).all()
    all_zsk_configs = ZSKConfig.query.filter(ZSKConfig.projekt_id.in_(projekt_ids)).all()
    all_hgls_configs = HGLSConfig.query.filter(HGLSConfig.projekt_id.in_(projekt_ids)).all()
    all_gwh_meteostations = GWHMeteostation.query.filter(GWHMeteostation.projekt_id.in_(projekt_ids)).all()
    all_ewh_meteostations = EWHMeteostation.query.filter(EWHMeteostation.projekt_id.in_(projekt_ids)).all()

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

    all_test_questions = TestQuestion.query.all()
    questions_by_type = {}
    for frage in all_test_questions:
        questions_by_type.setdefault(frage.komponente_typ, []).append(frage)
    fragen_by_id = {f.id: f for f in all_test_questions}

    all_results = AbnahmeTestResult.query.filter(
        AbnahmeTestResult.projekt_id.in_(projekt_ids)
    ).all()
    results_by_projekt = {}
    for result in all_results:
        results_by_projekt.setdefault(result.projekt_id, []).append(result)

    valid_values = ('richtig', 'falsch', 'nicht_testbar')

    def is_completed(r):
        return r.lss_ch_result in valid_values and r.wh_lts_result in valid_values

    for projekt in projekte:
        results = results_by_projekt.get(projekt.id, [])
        expected_tests = 0
        completed_tests = 0

        def add_component(komp_typ, anzahl_spalten, index_match):
            """
            Addiert Total und Beantwortet für eine Komponente.

            komp_typ: TestQuestion.komponente_typ (z.B. 'Anlage', 'WHK', 'Abgang')
            anzahl_spalten: Erwartete Anzahl Spalten/Instanzen (z.B. Anzahl WHKs,
                            Anzahl Abgänge pro WHK; 0 = Komponente nicht vorhanden)
            index_match: callable(komponente_index) -> bool
                         True wenn der Result-Index zur aktuellen Konfig passt.
            """
            nonlocal expected_tests, completed_tests
            n_fragen = len(questions_by_type.get(komp_typ, []))
            if n_fragen == 0 or anzahl_spalten <= 0:
                return
            total_comp = n_fragen * anzahl_spalten
            done_comp = sum(
                1 for r in results
                if fragen_by_id.get(r.test_question_id) is not None
                and fragen_by_id[r.test_question_id].komponente_typ == komp_typ
                and index_match(r.komponente_index)
                and is_completed(r)
            )
            expected_tests += total_comp
            completed_tests += min(done_comp, total_comp)

        if projekt.energie == 'EWH':
            whk_configs = whk_configs_by_projekt.get(projekt.id, [])
            ewh_meteostations = ewh_ms_by_projekt.get(projekt.id, [])

            if not whk_configs:
                progress_dict[projekt.id] = 0
                continue

            whk_nummern = {w.whk_nummer for w in whk_configs}
            ah_whk_nummern = {w.whk_nummer for w in whk_configs if w.hat_antriebsheizung}
            ms_nummern = {ms.ms_nummer for ms in ewh_meteostations}

            add_component('Anlage', 1, lambda ki: True)
            add_component('WHK', len(whk_configs), lambda ki: ki in whk_nummern)
            for whk in whk_configs:
                if whk.anzahl_abgaenge:
                    add_component('Abgang', whk.anzahl_abgaenge,
                                  lambda ki, n=whk.whk_nummer: ki == n)
            for whk in whk_configs:
                if whk.anzahl_temperatursonden:
                    add_component('Temperatursonde', whk.anzahl_temperatursonden,
                                  lambda ki, n=whk.whk_nummer: ki == n)
            add_component('Antriebsheizung', len(ah_whk_nummern),
                          lambda ki: ki in ah_whk_nummern)
            add_component('Meteostation', len(ewh_meteostations),
                          lambda ki: ki in ms_nummern)

        else:
            zsk_configs = zsk_configs_by_projekt.get(projekt.id, [])
            hgls_configs = hgls_configs_by_projekt.get(projekt.id, [])
            gwh_meteostations = gwh_ms_by_projekt.get(projekt.id, [])

            if not zsk_configs:
                progress_dict[projekt.id] = 0
                continue

            zsk_nummern = {z.zsk_nummer for z in zsk_configs}
            ts_zsk_nummern = {z.zsk_nummer for z in zsk_configs if z.hat_temperatursonde}
            gwh_ms_nummern = {ms.ms_nummer for ms in gwh_meteostations}

            add_component('GWH_Anlage', 1, lambda ki: True)
            if hgls_configs:
                add_component('HGLS', 1, lambda ki: True)
            add_component('ZSK', len(zsk_configs), lambda ki: ki in zsk_nummern)
            for zsk in zsk_configs:
                if zsk.anzahl_teile:
                    add_component('GWH_Teile', zsk.anzahl_teile,
                                  lambda ki, n=zsk.zsk_nummer: ki == n)
            add_component('GWH_Temperatursonde', len(ts_zsk_nummern),
                          lambda ki: ki in ts_zsk_nummern)
            add_component('GWH_Meteostation', len(gwh_meteostations),
                          lambda ki: ki in gwh_ms_nummern)

        if expected_tests == 0:
            progress_dict[projekt.id] = 0
            continue

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
        # Pruefdatum ist Freitext (Mehrfachdaten moeglich), kein Date-Parsing mehr
        pruefdatum_text = request.form.get('pruefdatum_text', '').strip() or None

        projekt = Project(
            energie=request.form['energie'],
            projektname=request.form['projektname'],
            didok_betriebspunkt=request.form.get('didok_betriebspunkt', ''),
            baumappenversion=baumappenversion,
            projektleiter_sbb=request.form.get('projektleiter_sbb', ''),
            pruefer_achermann=request.form.get('pruefer_achermann', ''),
            pruefdatum_text=pruefdatum_text,
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

        # Bestehende Projekt-Werte aktualisieren
        projekt.energie = request.form['energie']
        projekt.projektname = request.form['projektname']
        projekt.didok_betriebspunkt = request.form.get('didok_betriebspunkt', '')
        projekt.baumappenversion = baumappenversion
        projekt.projektleiter_sbb = request.form.get('projektleiter_sbb', '')
        projekt.pruefer_achermann = request.form.get('pruefer_achermann', '')
        # Pruefdatum ist Freitext (Mehrfachdaten moeglich), kein Date-Parsing mehr
        projekt.pruefdatum_text = request.form.get('pruefdatum_text', '').strip() or None
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
