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

    if request.method == 'POST':
        try:
            # Herstellung
            datum_str = request.form.get('herstellungsdatum', '')
            if datum_str:
                sn.herstellungsdatum = datetime.strptime(datum_str, '%Y-%m-%d').date()
            jahr_str = request.form.get('herstellungsjahr', '')
            if jahr_str:
                sn.herstellungsjahr = int(jahr_str)

            # Normen-Checkboxen
            checkbox_felder = [
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

            # Bemerkung
            sn.bemerkung = request.form.get('bemerkung', '')

            db.session.commit()
            flash('Stücknachweis erfolgreich gespeichert.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Speichern: {str(e)}', 'error')

        return redirect(url_for('stuecknachweis.stuecknachweis_formular',
                                project_id=project_id, whk_id=whk_id))

    # Schutzgrad aus preset_typ ableiten
    schutzgrad = 'IP55' if 'kabine' in whk.preset_typ else 'IP2X'

    return render_template('stuecknachweis/formular.html',
                           projekt=projekt,
                           whk=whk,
                           sn=sn,
                           schutzgrad=schutzgrad)


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
