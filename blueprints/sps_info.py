"""
Blueprint für das IT-Inventar (EWH): SPS-Daten pro WHK.

Pro WHK werden die IT-Daten der verbauten SPS erfasst (Hostname, MAC-Adresse,
IP-Adresse, SPS-Typ, Seriennummer, TwinCAT-/Image-Version, Bemerkung).

Struktur analog zum Stücknachweis (EN 61439):
    Projektübersicht-Button → WHK-Auswahl (aus Konfiguration) → Formular mit Auto-Save.
Zusätzlich eine eigene Einstiegsseite /it-inventar (Menüpunkt) mit allen EWH-Projekten
und Live-Projektsuche.

Hostname = Sys-ID der SBB (z.B. lu-wh-01); daraus werden Webvisu-/Config-Links abgeleitet
(URL-Muster zentral in models.SpsInfo.URL_MUSTER).

Auto-Init: Beim ersten Öffnen des Formulars wird ein leeres SpsInfo-Objekt angelegt.
Der Status in der Auswahlliste wechselt erst auf "Erfasst", sobald Hostname oder
MAC-Adresse gefüllt ist (SpsInfo.ist_erfasst).
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required

from models import db, Project, WHKConfig, SpsInfo

sps_info_bp = Blueprint('sps_info', __name__)


# ==================== HELPERS ====================

def _lade_projekt_und_whk(project_id, whk_id):
    """Lädt Projekt + WHK; gibt (projekt, whk, redirect_response) zurück.

    Bei Fehler ist redirect_response gesetzt und die Route gibt ihn direkt zurück.
    """
    projekt = Project.query.get(project_id)
    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return None, None, redirect(url_for('projekte.projekte'))

    whk = WHKConfig.query.get(whk_id)
    if not whk or whk.projekt_id != project_id:
        flash('WHK-Konfiguration nicht gefunden!', 'error')
        return projekt, None, redirect(url_for('sps_info.whk_auswahl', project_id=project_id))

    return projekt, whk, None


def _normalisiere(wert):
    """Freitext trimmen; leer → None (Feld zählt dann als nicht erfasst)."""
    if wert is None:
        return None
    return str(wert).strip() or None


# ==================== EINSTIEGSSEITE (alle EWH-Projekte) ====================

def _projekt_uebersicht_daten():
    """Liefert pro EWH-Projekt: WHK-Anzahl und Anzahl erfasster SPS (Sys-ID oder MAC).

    Zwei Abfragen statt N+1: alle WHKs der EWH-Projekte + alle SpsInfos, dann in Python
    gruppiert. ist_erfasst wird auf dem Objekt ausgewertet (eine Definition, s. Modell).
    """
    projekte = Project.query.filter_by(energie='EWH').order_by(Project.projektname).all()
    projekt_ids = [p.id for p in projekte]
    whk_anzahl = {}
    erfasst = {}
    if projekt_ids:
        for (pid,) in db.session.query(WHKConfig.projekt_id).filter(
                WHKConfig.projekt_id.in_(projekt_ids)).all():
            whk_anzahl[pid] = whk_anzahl.get(pid, 0) + 1
        for sps in SpsInfo.query.filter(SpsInfo.project_id.in_(projekt_ids)).all():
            if sps.ist_erfasst:
                erfasst[sps.project_id] = erfasst.get(sps.project_id, 0) + 1
    return [{
        'projekt': p,
        'whk_anzahl': whk_anzahl.get(p.id, 0),
        'erfasst_anzahl': erfasst.get(p.id, 0),
    } for p in projekte]


@sps_info_bp.route('/it-inventar')
@login_required
def uebersicht():
    """Einstiegsseite IT-Inventar: alle EWH-Projekte mit SPS-Zähler und Projektsuche."""
    return render_template('sps_info/uebersicht.html',
                           projekt_data=_projekt_uebersicht_daten())


# ==================== AUSWAHLSEITE ====================

@sps_info_bp.route('/projekt/<int:project_id>/it-inventar')
@login_required
def whk_auswahl(project_id):
    """WHK-Auswahl für das IT-Inventar: alle WHKs aus der Konfiguration mit Status."""
    projekt = Project.query.get(project_id)
    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    whk_configs = WHKConfig.query.filter_by(projekt_id=project_id).order_by(WHKConfig.whk_nummer).all()

    whk_data = []
    for whk in whk_configs:
        sps = SpsInfo.query.filter_by(whk_config_id=whk.id).first()
        whk_data.append({
            'whk': whk,
            'sps': sps,
            'erfasst': bool(sps and sps.ist_erfasst),
        })

    return render_template('sps_info/whk_auswahl.html',
                           projekt=projekt,
                           whk_data=whk_data)


# ==================== FORMULAR ====================

@sps_info_bp.route('/projekt/<int:project_id>/whk/<int:whk_id>/sps')
@login_required
def sps_formular(project_id, whk_id):
    """SPS-Formular für eine WHK anzeigen (Auto-Init beim ersten Öffnen)."""
    projekt, whk, fehler = _lade_projekt_und_whk(project_id, whk_id)
    if fehler:
        return fehler

    sps = SpsInfo.query.filter_by(whk_config_id=whk_id).first()
    if not sps:
        sps = SpsInfo(project_id=project_id, whk_config_id=whk_id)
        db.session.add(sps)
        db.session.commit()

    return render_template(
        'sps_info/formular.html',
        projekt=projekt,
        whk=whk,
        sps=sps,
        url_muster=SpsInfo.URL_MUSTER,
        autosave_url=url_for('sps_info.sps_autosave', project_id=project_id, whk_id=whk_id),
        auswahl_url=url_for('sps_info.whk_auswahl', project_id=project_id),
    )


# ==================== AUTO-SAVE ====================

@sps_info_bp.route('/projekt/<int:project_id>/whk/<int:whk_id>/sps/autosave', methods=['POST'])
@login_required
def sps_autosave(project_id, whk_id):
    """Auto-Save für das SPS-Formular (JSON, feldweise).

    Nur Felder aus SpsInfo.DATEN_FELDER werden übernommen; fehlende Keys bleiben
    unverändert. Leere Strings werden zu NULL normalisiert.
    """
    whk = WHKConfig.query.get(whk_id)
    if not whk or whk.projekt_id != project_id:
        return jsonify({'success': False, 'error': 'WHK nicht gefunden'}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'Keine Daten'}), 400

    try:
        sps = SpsInfo.query.filter_by(whk_config_id=whk_id).first()
        if not sps:
            sps = SpsInfo(project_id=project_id, whk_config_id=whk_id)
            db.session.add(sps)

        for feld in SpsInfo.DATEN_FELDER:
            if feld in data:
                setattr(sps, feld, _normalisiere(data[feld]))

        db.session.commit()
        return jsonify({'success': True, 'erfasst': sps.ist_erfasst})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
