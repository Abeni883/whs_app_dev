"""
SBB Weichenheizung - Testfragen Blueprint
Verwaltung der Testfragen für EWH und GWH
"""
import os
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_from_directory, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename

from models import db, TestQuestion, AbnahmeTestResult

testfragen_bp = Blueprint('testfragen', __name__)


# ==================== HELPER FUNCTIONS ====================

def allowed_file(filename):
    """Prüft ob die Dateiendung erlaubt ist."""
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def is_gwh_komponente(komponente_typ):
    """Prüft ob der Komponententyp zu GWH gehört."""
    gwh_komponenten = ['GWH_Anlage', 'HGLS', 'ZSK', 'GWH_Teile', 'GWH_Temperatursonde', 'GWH_Meteostation']
    return komponente_typ in gwh_komponenten


def create_test_results_for_new_question(neue_frage):
    """
    Platzhalter - Ergebnisse werden beim Testen automatisch erstellt.

    Neue Testfragen erscheinen automatisch auf den Testseiten.
    Ergebnisse werden erst beim Beantworten in der Datenbank angelegt.
    Das Preset-System sorgt für korrekte Vorbelegung.
    """
    return 0


# ==================== ROUTES ====================

@testfragen_bp.route('/testfragen')
@login_required
def testfragen_verwaltung():
    """
    Verwaltung aller EWH-Testfragen-Vorlagen.

    Zeigt EWH-Testfragen gruppiert nach Komponententyp.

    Returns:
        HTML-Seite mit EWH-Testfragen-Übersicht (testfragen_verwaltung.html)
    """
    ewh_komponenten = ['Anlage', 'WHK', 'Abgang', 'Temperatursonde', 'Antriebsheizung', 'Meteostation']
    test_questions = TestQuestion.query.filter(
        TestQuestion.komponente_typ.in_(ewh_komponenten)
    ).order_by(TestQuestion.komponente_typ, TestQuestion.reihenfolge).all()
    return render_template('testfragen_verwaltung.html', test_questions=test_questions)


@testfragen_bp.route('/gwh-testfragen')
@login_required
def gwh_testfragen_verwaltung():
    """
    Verwaltung aller GWH-Testfragen-Vorlagen.

    Zeigt GWH-Testfragen gruppiert nach Komponententyp.

    Returns:
        HTML-Seite mit GWH-Testfragen-Übersicht (gwh_testfragen_verwaltung.html)
    """
    gwh_komponenten = ['GWH_Anlage', 'HGLS', 'ZSK', 'GWH_Teile', 'GWH_Temperatursonde', 'GWH_Meteostation']
    test_questions = TestQuestion.query.filter(
        TestQuestion.komponente_typ.in_(gwh_komponenten)
    ).order_by(TestQuestion.komponente_typ, TestQuestion.reihenfolge).all()
    return render_template('gwh_testfragen_verwaltung.html', test_questions=test_questions)


@testfragen_bp.route('/testfragen/neu', methods=['GET', 'POST'])
@login_required
def testfrage_neu():
    """
    Neue Testfrage anlegen.

    GET: Zeigt Formular für neue Testfrage
    POST: Speichert neue Testfrage mit automatischer Fragenummer

    Query-Parameter:
        tab (optional): Aktiver Tab (Komponententyp)

    Returns:
        GET: HTML-Formular (testfrage_form.html)
        POST: Redirect zur Testfragen-Verwaltung
    """
    if request.method == 'POST':
        # Build preset_antworten JSON
        preset_antworten = {}
        preset_lss_ch = request.form.get('preset_lss_ch', '')
        preset_wh_lts = request.form.get('preset_wh_lts', '')

        if preset_lss_ch:
            preset_antworten['lss_ch'] = preset_lss_ch
        if preset_wh_lts:
            preset_antworten['wh_lts'] = preset_wh_lts

        komponente_typ = request.form['komponente_typ']

        # Automatische Generierung von frage_nummer (höchste + 1)
        max_frage_nummer = db.session.query(db.func.max(TestQuestion.frage_nummer)).scalar() or 0
        neue_frage_nummer = max_frage_nummer + 1

        # Automatische Generierung von reihenfolge (höchste für diesen Typ + 1)
        max_reihenfolge = db.session.query(db.func.max(TestQuestion.reihenfolge))\
            .filter(TestQuestion.komponente_typ == komponente_typ).scalar() or 0
        neue_reihenfolge = max_reihenfolge + 1

        # Screenshot-Upload verarbeiten
        screenshot_pfad = None
        if 'screenshot' in request.files:
            file = request.files['screenshot']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Füge Timestamp hinzu um Duplikate zu vermeiden
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                screenshot_pfad = filename

        neue_frage = TestQuestion(
            komponente_typ=komponente_typ,
            testszenario=request.form.get('testszenario', ''),
            frage_nummer=neue_frage_nummer,
            frage_text=request.form['frage_text'],
            test_information=request.form.get('test_information', ''),
            erwartetes_ergebnis=request.form.get('erwartetes_ergebnis', ''),
            screenshot_pfad=screenshot_pfad,
            reihenfolge=neue_reihenfolge,
            preset_antworten=preset_antworten if preset_antworten else None
        )
        db.session.add(neue_frage)
        db.session.flush()  # Flushen um die ID zu erhalten

        # Erstelle automatisch Abnahmetest-Ergebnisse für alle bestehenden Projekte
        # Damit zeigen die Fortschritts-Buttons weiterhin 100% an
        created_results = create_test_results_for_new_question(neue_frage)

        db.session.commit()

        if created_results > 0:
            flash(f'Testfrage erfolgreich hinzugefügt! ({created_results} Testergebnisse für bestehende Projekte erstellt)', 'success')
        else:
            flash('Testfrage erfolgreich hinzugefügt!', 'success')

        # Redirect zur richtigen Verwaltungsseite (EWH oder GWH)
        if is_gwh_komponente(komponente_typ):
            return redirect(url_for('testfragen.gwh_testfragen_verwaltung', tab=komponente_typ))
        else:
            return redirect(url_for('testfragen.testfragen_verwaltung', tab=komponente_typ))

    # GET: Hole tab aus Query-Parameter
    tab = request.args.get('tab', 'Anlage')
    return render_template('testfrage_form.html', frage=None, tab=tab)


@testfragen_bp.route('/testfragen/bearbeiten/<int:frage_id>', methods=['GET', 'POST'])
@login_required
def testfrage_bearbeiten(frage_id):
    """
    Bestehende Testfrage bearbeiten.

    Args:
        frage_id: ID der zu bearbeitenden Testfrage

    Returns:
        GET: HTML-Formular mit vorausgefüllten Werten (testfrage_form.html)
        POST: Redirect zur Testfragen-Verwaltung
    """
    frage = TestQuestion.query.get_or_404(frage_id)

    if request.method == 'POST':
        # Build preset_antworten JSON
        preset_antworten = {}
        preset_lss_ch = request.form.get('preset_lss_ch', '')
        preset_wh_lts = request.form.get('preset_wh_lts', '')

        if preset_lss_ch:
            preset_antworten['lss_ch'] = preset_lss_ch
        if preset_wh_lts:
            preset_antworten['wh_lts'] = preset_wh_lts

        komponente_typ = request.form['komponente_typ']
        frage.komponente_typ = komponente_typ
        frage.testszenario = request.form.get('testszenario', '')
        # frage_nummer bleibt unverändert (wird nicht mehr bearbeitet)
        frage.frage_text = request.form['frage_text']
        frage.test_information = request.form.get('test_information', '')
        frage.erwartetes_ergebnis = request.form.get('erwartetes_ergebnis', '')
        # reihenfolge bleibt unverändert (kann über Drag & Drop geändert werden)
        frage.preset_antworten = preset_antworten if preset_antworten else None

        # Screenshot löschen wenn angefordert
        if request.form.get('screenshot_loeschen') and frage.screenshot_pfad:
            alter_pfad = os.path.join(current_app.config['UPLOAD_FOLDER'], frage.screenshot_pfad)
            if os.path.exists(alter_pfad):
                os.remove(alter_pfad)
            frage.screenshot_pfad = None

        # Screenshot-Upload verarbeiten
        if 'screenshot' in request.files:
            file = request.files['screenshot']
            if file and file.filename and allowed_file(file.filename):
                # Lösche alten Screenshot falls vorhanden
                if frage.screenshot_pfad:
                    alter_pfad = os.path.join(current_app.config['UPLOAD_FOLDER'], frage.screenshot_pfad)
                    if os.path.exists(alter_pfad):
                        os.remove(alter_pfad)

                # Speichere neuen Screenshot
                filename = secure_filename(file.filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                frage.screenshot_pfad = filename

        db.session.commit()
        flash('Testfrage erfolgreich aktualisiert!', 'success')

        # Redirect zur richtigen Verwaltungsseite (EWH oder GWH)
        if is_gwh_komponente(komponente_typ):
            return redirect(url_for('testfragen.gwh_testfragen_verwaltung', tab=komponente_typ))
        else:
            return redirect(url_for('testfragen.testfragen_verwaltung', tab=komponente_typ))

    # GET: Hole tab aus Query-Parameter (oder verwende komponente_typ der Frage)
    tab = request.args.get('tab', frage.komponente_typ)
    return render_template('testfrage_form.html', frage=frage, tab=tab)


@testfragen_bp.route('/testfragen/loeschen/<int:frage_id>', methods=['POST'])
@login_required
def testfrage_loeschen(frage_id):
    """
    Testfrage löschen.

    Löscht auch automatisch alle zugehörigen Abnahmetest-Ergebnisse
    (über SQLAlchemy Cascade oder explizit).

    Args:
        frage_id: ID der zu löschenden Testfrage

    Returns:
        Redirect zur Testfragen-Verwaltung mit Flash-Message
    """
    frage = TestQuestion.query.get_or_404(frage_id)
    komponente_typ = frage.komponente_typ  # Merke den Tab vor dem Löschen

    # Zähle zugehörige Testergebnisse vor dem Löschen
    deleted_results = AbnahmeTestResult.query.filter_by(test_question_id=frage_id).count()

    # Lösche explizit alle zugehörigen Testergebnisse (zusätzlich zur Cascade)
    AbnahmeTestResult.query.filter_by(test_question_id=frage_id).delete()

    # Lösche die Testfrage
    db.session.delete(frage)
    db.session.commit()

    if deleted_results > 0:
        flash(f'Testfrage und {deleted_results} zugehörige Testergebnisse erfolgreich gelöscht!', 'success')
    else:
        flash('Testfrage erfolgreich gelöscht!', 'success')

    # Redirect zur richtigen Verwaltungsseite (EWH oder GWH)
    if is_gwh_komponente(komponente_typ):
        return redirect(url_for('testfragen.gwh_testfragen_verwaltung', tab=komponente_typ))
    else:
        return redirect(url_for('testfragen.testfragen_verwaltung', tab=komponente_typ))


@testfragen_bp.route('/uploads/screenshots/<filename>')
@login_required
def uploaded_screenshot(filename):
    """
    Liefert hochgeladene Screenshots aus.

    Args:
        filename: Name der Screenshot-Datei

    Returns:
        Die angeforderte Bilddatei
    """
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@testfragen_bp.route('/testfragen/reihenfolge', methods=['POST'])
@login_required
def testfragen_reihenfolge():
    """
    Reihenfolge von Testfragen ändern (Drag & Drop, AJAX).

    JSON Body:
        {
            "order": [
                {"id": 1, "reihenfolge": 1},
                {"id": 2, "reihenfolge": 2},
                ...
            ]
        }

    Returns:
        JSON: {"success": bool, "error": str (optional)}
    """
    data = request.get_json()

    try:
        for item in data['order']:
            frage = TestQuestion.query.get(int(item['id']))
            if frage:
                frage.reihenfolge = int(item['reihenfolge'])

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
