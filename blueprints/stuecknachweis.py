"""
Blueprint für Stücknachweis-Verwaltung (EWH).

Stücknachweis-Protokoll und Konformitätserklärung pro WHK,
inkl. Normen-Prüfung (EN 61439-1), Messungen und FI-Messungen.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from datetime import datetime, date

from models import (
    db, Project, WHKConfig, Stuecknachweis, FiMessung,
    generiere_fi_sicherungen
)

stuecknachweis_bp = Blueprint('stuecknachweis', __name__)


@stuecknachweis_bp.route('/projekt/<int:project_id>/stuecknachweis/whk-auswahl')
@login_required
def whk_auswahl(project_id):
    """WHK-Auswahl für Stücknachweis (EN 61439) anzeigen."""
    projekt = Project.query.get(project_id)
    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    whk_configs = WHKConfig.query.filter_by(projekt_id=project_id).order_by(WHKConfig.whk_nummer).all()

    # Prüfe pro WHK ob ein Stücknachweis existiert
    whk_data = []
    for whk in whk_configs:
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        # Preset-Typ lesbar formatieren
        preset_labels = {
            'kabine_16hz': 'Kabine 16.7Hz',
            'kabine_50hz': 'Kabine 50Hz',
            'rahmen_16hz': 'Rahmen 16.7Hz',
            'rahmen_50hz': 'Rahmen 50Hz',
        }
        whk_data.append({
            'whk': whk,
            'preset_label': preset_labels.get(whk.preset_typ, whk.preset_typ),
            'has_stuecknachweis': sn is not None,
        })

    return render_template('stuecknachweis/whk_auswahl.html',
                           projekt=projekt,
                           whk_data=whk_data)


@stuecknachweis_bp.route('/projekt/<int:project_id>/whk/<int:whk_id>/stuecknachweis', methods=['GET', 'POST'])
@login_required
def stuecknachweis_formular(project_id, whk_id):
    """
    Stücknachweis-Formular anzeigen und speichern.

    GET: Formular anzeigen (bei erstem Aufruf auto-initialisieren)
    POST: Alle Felder speichern inkl. FI-Messungen
    """
    projekt = Project.query.get(project_id)
    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    whk = WHKConfig.query.get(whk_id)
    if not whk or whk.projekt_id != project_id:
        flash('WHK-Konfiguration nicht gefunden!', 'error')
        return redirect(url_for('konfiguration.projekt_konfiguration', projekt_id=project_id))

    # Stücknachweis laden oder erstellen
    sn = Stuecknachweis.query.filter_by(project_id=project_id, whk_config_id=whk_id).first()

    if not sn:
        # Erste Öffnung: Auto-Initialisierung
        sn = Stuecknachweis(
            project_id=project_id,
            whk_config_id=whk_id,
            typbezeichnung=whk.whk_typ or whk.whk_nummer,
            auftraggeber='SBB AG',
            hersteller='Achermann & Co. AG',
            herstellungsdatum=date.today(),
            herstellungsjahr=datetime.now().year,
        )
        db.session.add(sn)
        db.session.flush()  # ID generieren für FI-Messungen

        # FI-Messungen automatisch generieren
        sicherungen = generiere_fi_sicherungen(whk.anzahl_abgaenge)
        for idx, sicherung in enumerate(sicherungen):
            fi = FiMessung(
                stuecknachweis_id=sn.id,
                sicherung=sicherung,
                status=True,
                reihenfolge=idx
            )
            db.session.add(fi)

        db.session.commit()

    # Schutzgrad-Map
    schutzgrad_map = {
        'kabine_16hz': 'IP55', 'kabine_50hz': 'IP55',
        'rahmen_16hz': 'IP2X', 'rahmen_50hz': 'IP2X'
    }

    if request.method == 'POST':
        try:
            # Kopfdaten
            sn.typbezeichnung = request.form.get('typbezeichnung', '').strip() or None
            sn.auftraggeber = request.form.get('auftraggeber', '').strip() or 'SBB AG'
            sn.hersteller = request.form.get('hersteller', '').strip() or 'Achermann & Co. AG'

            # Preset-Typ aus Formular lesen und auf WHK speichern
            preset_typ = request.form.get('preset_typ', whk.preset_typ)
            if preset_typ in schutzgrad_map:
                whk.preset_typ = preset_typ

            # Herstellung
            datum_str = request.form.get('herstellungsdatum', '')
            if datum_str:
                sn.herstellungsdatum = datetime.strptime(datum_str, '%Y-%m-%d').date()
            jahr_str = request.form.get('herstellungsjahr', '')
            if jahr_str:
                sn.herstellungsjahr = int(jahr_str)

            # Normen-Checkboxen
            checkbox_felder = [
                # Grund der Prüfung / Schutzmassnahme / Berührungsschutz
                'grund_erstpruefung', 'grund_wiederholung',
                'grund_aenderung', 'grund_instandsetzung',
                'schutz_tn_s', 'schutz_tn_c', 'schutz_tn_c_s',
                'schutz_tt', 'schutz_it',
                'beruehr_nicht_instruiert', 'beruehr_instruiert',
                # Normen EN 61439-1
                'check_11_2', 'check_11_3_kriech', 'check_11_3_luft_1',
                'check_11_3_luft_2', 'check_11_3_luft_3', 'check_11_4_schutz',
                'check_11_4_durch', 'check_11_4_geschr', 'check_11_5',
                'check_11_6_verb', 'check_11_6_verd', 'check_11_7',
                'check_11_8', 'check_11_1_kenn', 'check_11_1_doku',
                'check_11_1_funk'
            ]
            for feld in checkbox_felder:
                setattr(sn, feld, feld in request.form)

            # Messungen
            sn.niederohm_ergebnis = request.form.get('niederohm_ergebnis', '')
            sn.niederohm_status = 'niederohm_status' in request.form
            sn.spannung_ergebnis = request.form.get('spannung_ergebnis', '')
            sn.spannung_status = 'spannung_status' in request.form
            sn.isolation_ergebnis = request.form.get('isolation_ergebnis', '')
            sn.isolation_status = 'isolation_status' in request.form

            # FI-Messungen aktualisieren
            for fi in sn.fi_messungen:
                prefix = f'fi_{fi.id}'
                fi.sicherung = request.form.get(f'{prefix}_sicherung', fi.sicherung)
                delta_i = request.form.get(f'{prefix}_delta_i', '')
                fi.delta_i_ma = int(delta_i) if delta_i else None
                delta_t = request.form.get(f'{prefix}_delta_t', '')
                fi.delta_t_ms = int(delta_t) if delta_t else None
                fi.status = f'{prefix}_status' in request.form

            # Schutzgrad (editierbares Feld)
            sn.schutzgrad = request.form.get('schutzgrad', '').strip() or None

            # Bemerkung
            sn.bemerkung = request.form.get('bemerkung', '')

            db.session.commit()
            flash('Stücknachweis erfolgreich gespeichert.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Speichern: {str(e)}', 'error')

        return redirect(url_for('stuecknachweis.stuecknachweis_formular',
                                project_id=project_id, whk_id=whk_id))

    # Schutzgrad serverseitig ableiten
    schutzgrad = schutzgrad_map.get(whk.preset_typ, 'IP55')

    # Typbezeichnung: whk_typ falls vorhanden, sonst whk_nummer
    typbezeichnung = whk.whk_typ or whk.whk_nummer

    return render_template('stuecknachweis/formular.html',
                           projekt=projekt,
                           whk=whk,
                           sn=sn,
                           schutzgrad=schutzgrad,
                           typbezeichnung=typbezeichnung)


@stuecknachweis_bp.route('/projekt/<int:project_id>/whk/<int:whk_id>/stuecknachweis/pdf')
@login_required
def stuecknachweis_pdf(project_id, whk_id):
    """PDF Stücknachweisprotokoll generieren (Phase 2)."""
    flash('PDF-Export wird in Phase 2 implementiert.', 'info')
    return redirect(url_for('stuecknachweis.stuecknachweis_formular',
                            project_id=project_id, whk_id=whk_id))


@stuecknachweis_bp.route('/projekt/<int:project_id>/whk/<int:whk_id>/konformitaet/pdf')
@login_required
def konformitaet_pdf(project_id, whk_id):
    """PDF Konformitätserklärung generieren (Phase 2)."""
    flash('PDF-Export wird in Phase 2 implementiert.', 'info')
    return redirect(url_for('stuecknachweis.stuecknachweis_formular',
                            project_id=project_id, whk_id=whk_id))
