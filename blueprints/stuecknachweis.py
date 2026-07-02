"""
Blueprint für Stücknachweis-Verwaltung (EWH).

Stücknachweis-Protokoll und Konformitätserklärung pro WHK ODER pro Steuerung (SHDSL),
inkl. Normen-Prüfung (EN 61439-1), Messungen und FI-Messungen.

Ein Stücknachweis gehört entweder zu einer WHK (whk_config_id) oder zu einer
Steuerung (steuerung_config_id). Formular und PDF werden für beide Typen
wiederverwendet; Unterschiede werden über das ist_steuerung-Flag gesteuert.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from datetime import datetime, date

from models import (
    db, Project, WHKConfig, Stuecknachweis, FiMessung,
    SteuerungConfig, generiere_fi_sicherungen, get_norm_name
)

stuecknachweis_bp = Blueprint('stuecknachweis', __name__)


# ==================== KONSTANTEN ====================

# Schutzgrad-Ableitung aus Preset (WHK + Steuerung)
SCHUTZGRAD_MAP = {
    # WHK Presets
    'kabine_16hz': 'IP55', 'kabine_50hz': 'IP55',
    'rahmen_16hz': 'IP2X', 'rahmen_50hz': 'IP2X',
    # Steuerung (SHDSL) Presets
    'schrank_mit_tuer': 'IP55',
    'schrank_ohne_tuer': 'IP2X',
}

# Checkbox-Felder (Grund/Schutz/Berührung + Normen EN 61439-1)
CHECKBOX_FELDER = [
    'grund_erstpruefung', 'grund_wiederholung', 'grund_aenderung', 'grund_instandsetzung',
    'schutz_tn_s', 'schutz_tn_c', 'schutz_tn_c_s', 'schutz_tt', 'schutz_it',
    'beruehr_nicht_instruiert', 'beruehr_instruiert',
    'check_11_2', 'check_11_3_kriech', 'check_11_3_luft_1',
    'check_11_3_luft_2', 'check_11_3_luft_3',
    'check_11_4_durch', 'check_11_4_geschr', 'check_11_5',
    'check_11_6_verb', 'check_11_6_verd', 'check_11_7',
    'check_11_8', 'check_11_1_kenn', 'check_11_1_doku', 'check_11_1_funk',
]

# Boolean-Felder für Auto-Save (JSON)
BOOL_FELDER_AUTOSAVE = CHECKBOX_FELDER + ['niederohm_status', 'spannung_status', 'isolation_status']


def _sn_status(sn):
    """Ermittelt den Auswahllisten-Status eines Stücknachweises.

    - 'vorhanden'      : beide PDFs (Stücknachweis + Konformität) exportiert
    - 'in_arbeit'      : SN existiert, aber noch nicht beide PDFs exportiert
    - 'nicht_erstellt' : noch kein SN (Formular nie geöffnet)
    """
    if sn and sn.pdf_stuecknachweis_exportiert and sn.pdf_konformitaet_exportiert:
        return 'vorhanden'
    if sn:
        return 'in_arbeit'
    return 'nicht_erstellt'


def _parse_num(value):
    """Parst einen mA/ms-Wert robust.

    Gibt float oder None zurück und wirft niemals — verhindert HTTP 500
    bei Dezimal-, Komma- oder ungültigen Eingaben.
    """
    if value is None:
        return None
    s = str(value).strip().replace(',', '.')
    if not s:
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


# ==================== SHARED HELPERS ====================

def _speichere_form(sn, config, ist_steuerung):
    """Speichert alle Formularfelder (request.form) in sn/config.

    Gemeinsam für WHK- und Steuerung-Stücknachweis.
    """
    # Kopfdaten
    sn.typbezeichnung = request.form.get('typbezeichnung', '').strip() or None
    sn.auftraggeber = request.form.get('auftraggeber', '').strip() or 'SBB AG'
    sn.hersteller = request.form.get('hersteller', '').strip() or 'Achermann & Co. AG'
    # Norm: leeres Feld → Fallback auf globalen Settings-Wert
    sn.norm_name = request.form.get('norm_name', '').strip() or get_norm_name()

    # Preset-Typ auf die Konfiguration (WHK oder Steuerung) speichern
    preset_typ = request.form.get('preset_typ', config.preset_typ)
    if preset_typ in SCHUTZGRAD_MAP:
        config.preset_typ = preset_typ

    # Herstellungsdatum: einheitlich Freitext (WHK + Steuerung)
    sn.herstellungsdatum_text = request.form.get('herstellungsdatum_text', '').strip() or None
    jahr_str = request.form.get('herstellungsjahr', '')
    if jahr_str:
        sn.herstellungsjahr = int(jahr_str)

    # Checkboxen
    for feld in CHECKBOX_FELDER:
        setattr(sn, feld, feld in request.form)

    # Messungen
    sn.messgeraet_messung = request.form.get('messgeraet_messung', '').strip() or 'HT FullTest 3'
    sn.messgeraet_fi = request.form.get('messgeraet_fi', '').strip() or 'HT FullTest 3'
    sn.niederohm_ergebnis = request.form.get('niederohm_ergebnis', '')
    sn.niederohm_status = 'niederohm_status' in request.form
    sn.spannung_ergebnis = request.form.get('spannung_ergebnis', '')
    sn.spannung_status = 'spannung_status' in request.form
    sn.isolation_ergebnis = request.form.get('isolation_ergebnis', '')
    sn.isolation_status = 'isolation_status' in request.form

    # FI-Messungen (frisch laden, inkl. manuell hinzugefügte)
    for fi in FiMessung.query.filter_by(stuecknachweis_id=sn.id).all():
        prefix = f'fi_{fi.id}'
        fi.sicherung = request.form.get(f'{prefix}_sicherung', fi.sicherung)
        fi.fehlerstrom_30 = f'fi_fehlerstrom_30_{fi.id}' in request.form
        fi.fehlerstrom_300 = f'fi_fehlerstrom_300_{fi.id}' in request.form
        fi.delta_i_ma = _parse_num(request.form.get(f'{prefix}_delta_i', ''))
        fi.delta_t_ms = _parse_num(request.form.get(f'{prefix}_delta_t', ''))
        fi.status = f'{prefix}_status' in request.form

    # Schutzgrad + Bemerkung
    sn.schutzgrad = request.form.get('schutzgrad', '').strip() or None
    sn.bemerkung = request.form.get('bemerkung', '')


def _render_formular(projekt, sn, config, ist_steuerung):
    """Rendert das Stücknachweis-Formular (gemeinsam für WHK/Steuerung)."""
    schutzgrad = SCHUTZGRAD_MAP.get(config.preset_typ, 'IP55')

    if ist_steuerung:
        objekt_bezeichnung = config.name or 'Steuerung'
        typbezeichnung = config.name or 'Steuerung'
    else:
        objekt_bezeichnung = config.whk_nummer
        typbezeichnung = config.whk_typ or config.whk_nummer

    return render_template(
        'stuecknachweis/formular.html',
        projekt=projekt,
        sn=sn,
        ist_steuerung=ist_steuerung,
        preset_typ_aktuell=config.preset_typ,
        objekt_bezeichnung=objekt_bezeichnung,
        typbezeichnung=typbezeichnung,
        schutzgrad=schutzgrad,
        autosave_url=url_for('stuecknachweis.stuecknachweis_autosave', sn_id=sn.id),
        fi_add_url=url_for('stuecknachweis.fi_hinzufuegen', sn_id=sn.id),
        fi_delete_base=f'/stuecknachweis/{sn.id}/fi/',
        pdf_sn_url=url_for('stuecknachweis.stuecknachweis_pdf', sn_id=sn.id),
        pdf_konf_url=url_for('stuecknachweis.konformitaet_pdf', sn_id=sn.id),
        auswahl_url=url_for('stuecknachweis.whk_auswahl', project_id=projekt.id),
    )


def _logo_base64():
    """Achermann-Logo als Base64 Data-URL (oder leerer String)."""
    import os
    import base64
    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(app_root, 'assets', 'logo.png')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
            return f'data:image/png;base64,{b64}'
    return ''


# ==================== AUSWAHLSEITE ====================

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
    preset_labels = {
        'kabine_16hz': 'Kabine 16.7Hz',
        'kabine_50hz': 'Kabine 50Hz',
        'rahmen_16hz': 'Rahmen 16.7Hz',
        'rahmen_50hz': 'Rahmen 50Hz',
    }
    whk_data = []
    for whk in whk_configs:
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        whk_data.append({
            'whk': whk,
            'preset_label': preset_labels.get(whk.preset_typ, whk.preset_typ),
            'status': _sn_status(sn),
        })

    # Steuerungen (SHDSL) laden — werden unter den WHKs angezeigt
    steuerungen = SteuerungConfig.query.filter_by(
        projekt_id=project_id
    ).order_by(SteuerungConfig.reihenfolge).all()

    steuerung_data = []
    for st in steuerungen:
        sn = Stuecknachweis.query.filter_by(steuerung_config_id=st.id).first()
        steuerung_data.append({
            'st': st,
            'status': _sn_status(sn),
        })

    return render_template('stuecknachweis/whk_auswahl.html',
                           projekt=projekt,
                           whk_data=whk_data,
                           steuerung_data=steuerung_data)


# ==================== FORMULAR: WHK ====================

@stuecknachweis_bp.route('/projekt/<int:project_id>/whk/<int:whk_id>/stuecknachweis', methods=['GET', 'POST'])
@login_required
def stuecknachweis_formular(project_id, whk_id):
    """Stücknachweis-Formular für eine WHK anzeigen und speichern."""
    projekt = Project.query.get(project_id)
    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    whk = WHKConfig.query.get(whk_id)
    if not whk or whk.projekt_id != project_id:
        flash('WHK-Konfiguration nicht gefunden!', 'error')
        return redirect(url_for('konfiguration.projekt_konfiguration', projekt_id=project_id))

    # Stücknachweis laden oder erstellen (inkl. FI-Auto-Generierung)
    sn = Stuecknachweis.query.filter_by(project_id=project_id, whk_config_id=whk_id).first()
    if not sn:
        sn = Stuecknachweis(
            project_id=project_id,
            whk_config_id=whk_id,
            typbezeichnung=whk.whk_typ or whk.whk_nummer,
            auftraggeber='SBB AG',
            hersteller='Achermann & Co. AG',
            norm_name=get_norm_name(),
            herstellungsdatum=date.today(),
            herstellungsdatum_text=datetime.now().strftime('%d.%m.%Y'),
            herstellungsjahr=datetime.now().year,
        )
        db.session.add(sn)
        db.session.flush()

        for idx, sicherung in enumerate(generiere_fi_sicherungen(whk.anzahl_abgaenge)):
            db.session.add(FiMessung(
                stuecknachweis_id=sn.id, sicherung=sicherung, status=True, reihenfolge=idx))
        db.session.commit()

    # FI-Messungen aktualisieren wenn Abgang-Anzahl geändert wurde (nur WHK, nur auto-generierte)
    auto_fi_anzahl = FiMessung.query.filter_by(stuecknachweis_id=sn.id, manuell=False).count()
    soll_anzahl = len(generiere_fi_sicherungen(whk.anzahl_abgaenge))
    if auto_fi_anzahl != soll_anzahl:
        FiMessung.query.filter_by(stuecknachweis_id=sn.id, manuell=False).delete()
        for idx, sicherung in enumerate(generiere_fi_sicherungen(whk.anzahl_abgaenge)):
            db.session.add(FiMessung(
                stuecknachweis_id=sn.id, sicherung=sicherung,
                fehlerstrom_300=True, fehlerstrom_30=False,
                status=True, reihenfolge=idx, manuell=False))
        db.session.commit()
        flash('Anzahl Abgänge wurde geändert — FI-Messungen wurden aktualisiert.', 'info')

    if request.method == 'POST':
        try:
            _speichere_form(sn, whk, ist_steuerung=False)
            db.session.commit()
            flash('Stücknachweis erfolgreich gespeichert.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Speichern: {str(e)}', 'error')
        return redirect(url_for('stuecknachweis.whk_auswahl', project_id=project_id))

    return _render_formular(projekt, sn, whk, ist_steuerung=False)


# ==================== FORMULAR: STEUERUNG (SHDSL) ====================

@stuecknachweis_bp.route('/projekt/<int:project_id>/steuerung/<int:steuerung_id>/stuecknachweis', methods=['GET', 'POST'])
@login_required
def steuerung_stuecknachweis_formular(project_id, steuerung_id):
    """Stücknachweis-Formular für eine Steuerung (SHDSL).

    Unterschiede zu WHK: Freitext-Herstellungsdatum, Steuerung-Presets,
    KEINE automatische FI-Generierung/Synchronisierung.
    """
    projekt = Project.query.get(project_id)
    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    st = SteuerungConfig.query.get(steuerung_id)
    if not st or st.projekt_id != project_id:
        flash('Steuerung nicht gefunden!', 'error')
        return redirect(url_for('stuecknachweis.whk_auswahl', project_id=project_id))

    # Stücknachweis laden oder erstellen — OHNE FI-Auto-Generierung
    sn = Stuecknachweis.query.filter_by(project_id=project_id, steuerung_config_id=steuerung_id).first()
    if not sn:
        sn = Stuecknachweis(
            project_id=project_id,
            steuerung_config_id=steuerung_id,
            typbezeichnung=st.name or 'Steuerung',
            auftraggeber='SBB AG',
            hersteller='Achermann & Co. AG',
            norm_name=get_norm_name(),
            herstellungsdatum_text=datetime.now().strftime('%d.%m.%Y'),
            herstellungsjahr=datetime.now().year,
        )
        db.session.add(sn)
        db.session.commit()

    if request.method == 'POST':
        try:
            _speichere_form(sn, st, ist_steuerung=True)
            db.session.commit()
            flash('Stücknachweis erfolgreich gespeichert.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Speichern: {str(e)}', 'error')
        return redirect(url_for('stuecknachweis.whk_auswahl', project_id=project_id))

    return _render_formular(projekt, sn, st, ist_steuerung=True)


# ==================== FI-ENDPUNKTE (sn_id-basiert, WHK + Steuerung) ====================

@stuecknachweis_bp.route('/stuecknachweis/<int:sn_id>/fi/add', methods=['POST'])
@login_required
def fi_hinzufuegen(sn_id):
    """Neue leere FI-Messung manuell hinzufügen."""
    sn = Stuecknachweis.query.get_or_404(sn_id)

    max_reihenfolge = db.session.query(
        db.func.max(FiMessung.reihenfolge)
    ).filter_by(stuecknachweis_id=sn.id).scalar() or 0

    fi = FiMessung(
        stuecknachweis_id=sn.id,
        sicherung='',
        fehlerstrom_30=False,
        fehlerstrom_300=False,
        status=True,
        reihenfolge=max_reihenfolge + 1,
        manuell=True
    )
    db.session.add(fi)
    db.session.commit()

    return jsonify({'success': True, 'fi_id': fi.id})


@stuecknachweis_bp.route('/stuecknachweis/<int:sn_id>/fi/<int:fi_id>/delete', methods=['POST'])
@login_required
def fi_loeschen(sn_id, fi_id):
    """FI-Messung löschen.

    Es gibt KEINE Mindestanzahl mehr — der Benutzer entscheidet selbst
    (Steuerungen können ohne FI sein).
    """
    sn = Stuecknachweis.query.get_or_404(sn_id)
    fi = FiMessung.query.get_or_404(fi_id)

    if fi.stuecknachweis_id != sn.id:
        return jsonify({'success': False}), 403

    db.session.delete(fi)
    db.session.commit()
    return jsonify({'success': True})


# ==================== AUTO-SAVE (sn_id-basiert) ====================

@stuecknachweis_bp.route('/stuecknachweis/<int:sn_id>/autosave', methods=['POST'])
@login_required
def stuecknachweis_autosave(sn_id):
    """Auto-Save für Stücknachweis-Formular (WHK + Steuerung)."""
    sn = Stuecknachweis.query.get_or_404(sn_id)
    config = sn.steuerung_config if sn.ist_steuerung else sn.whk_config
    data = request.get_json()
    if not data:
        return jsonify({'success': False}), 400

    try:
        # Kopfdaten (inkl. Freitext-Herstellungsdatum für Steuerungen)
        for f in ['typbezeichnung', 'auftraggeber', 'hersteller', 'schutzgrad',
                  'messgeraet_messung', 'messgeraet_fi', 'bemerkung', 'herstellungsdatum_text']:
            if f in data:
                setattr(sn, f, data[f] or None)

        # Norm: leeres Feld → Fallback auf globalen Settings-Wert
        if 'norm_name' in data:
            sn.norm_name = (data['norm_name'] or '').strip() or get_norm_name()

        if 'herstellungsdatum' in data and data['herstellungsdatum']:
            try:
                sn.herstellungsdatum = datetime.strptime(data['herstellungsdatum'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if 'herstellungsjahr' in data and data['herstellungsjahr']:
            try:
                sn.herstellungsjahr = int(data['herstellungsjahr'])
            except (ValueError, TypeError):
                pass

        if 'preset_typ' in data and config is not None and data['preset_typ'] in SCHUTZGRAD_MAP:
            config.preset_typ = data['preset_typ']

        # Boolean-Felder
        for f in BOOL_FELDER_AUTOSAVE:
            if f in data:
                setattr(sn, f, bool(data[f]))

        # Messungen Ergebnis (String)
        for f in ['niederohm_ergebnis', 'spannung_ergebnis', 'isolation_ergebnis']:
            if f in data:
                setattr(sn, f, data[f] or '')

        # FI-Messungen
        if 'fi_messungen' in data:
            for fi_data in data['fi_messungen']:
                fi_id = fi_data.get('id')
                if not fi_id:
                    continue
                fi = FiMessung.query.get(int(fi_id))
                if fi and fi.stuecknachweis_id == sn.id:
                    if 'sicherung' in fi_data:
                        fi.sicherung = fi_data['sicherung']
                    fi.delta_i_ma = _parse_num(fi_data.get('delta_i_ma'))
                    fi.delta_t_ms = _parse_num(fi_data.get('delta_t_ms'))
                    fi.fehlerstrom_30 = fi_data.get('fehlerstrom_30', False)
                    fi.fehlerstrom_300 = fi_data.get('fehlerstrom_300', False)
                    fi.status = fi_data.get('status', True)

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PDF: STÜCKNACHWEIS (sn_id-basiert) ====================

@stuecknachweis_bp.route('/stuecknachweis/<int:sn_id>/pdf')
@login_required
def stuecknachweis_pdf(sn_id):
    """PDF Stücknachweisprotokoll generieren (WHK + Steuerung)."""
    from io import BytesIO
    from xhtml2pdf import pisa
    from flask import send_file

    sn = Stuecknachweis.query.get_or_404(sn_id)
    projekt = Project.query.get_or_404(sn.project_id)
    ist_steuerung = sn.ist_steuerung
    config = sn.steuerung_config if ist_steuerung else sn.whk_config

    fi_messungen = FiMessung.query.filter_by(
        stuecknachweis_id=sn.id).order_by(FiMessung.reihenfolge).all()

    if ist_steuerung:
        typbezeichnung = config.name or 'Steuerung'
        produkt_art = 'Steuerung (SHDSL)'
    else:
        typbezeichnung = config.whk_typ or config.whk_nummer
        produkt_art = 'Weichenheizkabine'

    schutzgrad = SCHUTZGRAD_MAP.get(config.preset_typ, 'IP55')

    # Spacer-Höhe: Platz zwischen FI-Tabelle und Bemerkung.
    # Bei 0 FI-Messungen wird die FI-Tabelle NICHT gerendert → Höhe 0.
    fi_anzahl = len(fi_messungen)
    fi_hoehe_pt = (45 + fi_anzahl * 21) if fi_anzahl > 0 else 0
    unten_pt = 240
    verfuegbar_pt = 600
    spacer_pt = max(0, verfuegbar_pt - fi_hoehe_pt - unten_pt)
    spacer_mm = round(spacer_pt * 25.4 / 72)

    # Effektiver Norm-Name: SN-Wert oder Fallback auf globales Setting
    effektive_norm = sn.norm_name or get_norm_name()

    html = render_template(
        'stuecknachweis/pdf_stuecknachweis.html',
        stuecknachweis=sn,
        projekt=projekt,
        ist_steuerung=ist_steuerung,
        produkt_art=produkt_art,
        typbezeichnung=typbezeichnung,
        schutzgrad=schutzgrad,
        fi_messungen=fi_messungen,
        achermann_logo_base64=_logo_base64(),
        spacer_mm=spacer_mm,
        sn_norm=effektive_norm
    )

    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=pdf_buffer)
    if pisa_status.err:
        flash('Fehler bei der PDF-Generierung.', 'error')
        return redirect(url_for('stuecknachweis.whk_auswahl', project_id=sn.project_id))

    # Export-Zeitpunkt festhalten (für Status "Vorhanden" in der Auswahlliste)
    sn.pdf_stuecknachweis_exportiert = datetime.utcnow()
    db.session.commit()

    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer, mimetype='application/pdf', as_attachment=True,
        download_name=f'Stuecknachweis_{typbezeichnung}.pdf')


# ==================== PDF: KONFORMITÄTSERKLÄRUNG (sn_id-basiert) ====================

@stuecknachweis_bp.route('/stuecknachweis/<int:sn_id>/konformitaet/pdf')
@login_required
def konformitaet_pdf(sn_id):
    """PDF Konformitätserklärung generieren (WHK + Steuerung)."""
    from io import BytesIO
    from xhtml2pdf import pisa
    from flask import send_file

    sn = Stuecknachweis.query.get_or_404(sn_id)
    projekt = Project.query.get_or_404(sn.project_id)
    ist_steuerung = sn.ist_steuerung
    config = sn.steuerung_config if ist_steuerung else sn.whk_config

    if ist_steuerung:
        typbezeichnung = config.name or 'Steuerung'
        produkt_art = 'Steuerung (SHDSL)'
    else:
        typbezeichnung = config.whk_typ or config.whk_nummer
        produkt_art = 'Weichenheizkabine'

    # Effektiver Norm-Name: SN-Wert oder Fallback auf globales Setting
    effektive_norm = sn.norm_name or get_norm_name()

    html = render_template(
        'stuecknachweis/pdf_konformitaet.html',
        stuecknachweis=sn,
        projekt=projekt,
        ist_steuerung=ist_steuerung,
        produkt_art=produkt_art,
        typbezeichnung=typbezeichnung,
        achermann_logo_base64=_logo_base64(),
        sn_norm=effektive_norm
    )

    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=pdf_buffer)
    if pisa_status.err:
        flash('Fehler bei der PDF-Generierung.', 'error')
        return redirect(url_for('stuecknachweis.whk_auswahl', project_id=sn.project_id))

    # Export-Zeitpunkt festhalten (für Status "Vorhanden" in der Auswahlliste)
    sn.pdf_konformitaet_exportiert = datetime.utcnow()
    db.session.commit()

    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer, mimetype='application/pdf', as_attachment=True,
        download_name=f'Konformitaetserklaerung_{typbezeichnung}.pdf')
