"""
SBB Weichenheizung - Zeiterfassung Blueprint
Zeit-Tracking und Auswertungen
"""
from datetime import datetime
from io import BytesIO

from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required
from xhtml2pdf import pisa

from models import db, Project, ProjectTimeLog
from blueprints.api import cleanup_stale_sessions

zeiterfassung_bp = Blueprint('zeiterfassung', __name__)


def convert_html_to_pdf(html_string):
    """
    Konvertiert HTML-String zu PDF mit xhtml2pdf.

    Args:
        html_string: HTML-Inhalt als String

    Returns:
        bytes: PDF als Bytes oder None bei Fehler
    """
    result = BytesIO()
    pdf = pisa.CreatePDF(BytesIO(html_string.encode('utf-8')), dest=result)

    if pdf.err:
        return None

    return result.getvalue()


# ==================== HELPER FUNCTIONS ====================

def format_seconds(seconds):
    """Formatiert Sekunden zu lesbarem Format (h:mm oder min)."""
    if seconds == 0:
        return '-'
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f'{hours}:{minutes:02d} h'
    if minutes == 0:
        return '< 1 min'
    return f'{minutes} min'


def format_minutes(seconds):
    """Formatiert Sekunden zu Minuten."""
    if seconds == 0:
        return '-'
    minutes = seconds // 60
    if minutes == 0:
        return '< 1 min'
    return f'{minutes} min'


# ==================== ROUTES ====================

@zeiterfassung_bp.route('/zeiterfassung')
@login_required
def zeiterfassung():
    """
    Zeiterfassungs-Übersicht mit Statistiken pro Projekt.
    """
    # Bereinige alte Sessions
    cleanup_stale_sessions()

    # Alle abgeschlossenen Logs laden
    logs = ProjectTimeLog.query.filter(
        ProjectTimeLog.status.in_(['beendet', 'abgebrochen'])
    ).all()

    # Projekte laden
    projekte = Project.query.order_by(Project.projektname).all()

    # Statistiken berechnen
    projekt_stats = {}

    # Projekt Eröffnung: Einmalig 15 Minuten (900 Sekunden) pro Projekt
    projekt_eroeffnung_sekunden = 900

    # Für jedes Projekt initialisieren (inkl. 15 min Projekt Eröffnung)
    for projekt in projekte:
        projekt_stats[projekt.id] = {
            'projekt': projekt,
            'konfiguration': 0,
            'abnahmetest': 0,
            'export': 0,
            'testabschluss': 0,
            'gesamt': projekt_eroeffnung_sekunden  # Startet mit 15 min Projekt Eröffnung
        }

    # Logs durchgehen und summieren (nur projektbezogene Aktivitäten)
    for log in logs:
        duration = log.duration_seconds or 0

        if log.projekt_id and log.projekt_id in projekt_stats:
            if log.activity_type in projekt_stats[log.projekt_id]:
                projekt_stats[log.projekt_id][log.activity_type] += duration
            projekt_stats[log.projekt_id]['gesamt'] += duration

    # Statistiken für Template vorbereiten
    stats_list = []
    for projekt_id, stats in projekt_stats.items():
        if stats['gesamt'] > 0:
            stats_list.append({
                'projekt': stats['projekt'],
                'konfiguration': format_seconds(stats['konfiguration']),
                'abnahmetest': format_seconds(stats['abnahmetest']),
                'export': format_seconds(stats['export']),
                'testabschluss': format_seconds(stats['testabschluss']),
                'gesamt': format_seconds(stats['gesamt']),
                'gesamt_seconds': stats['gesamt']
            })

    # Nach Gesamtzeit sortieren (absteigend)
    stats_list.sort(key=lambda x: x['gesamt_seconds'], reverse=True)

    return render_template('zeiterfassung.html', stats_list=stats_list)


@zeiterfassung_bp.route('/zeiterfassung/projekt/<int:projekt_id>')
@login_required
def zeiterfassung_detail(projekt_id):
    """
    Detail-Ansicht der Zeiterfassung für ein spezifisches Projekt.
    Gruppiert nach Datum und Benutzer.
    """
    projekt = Project.query.get_or_404(projekt_id)

    # Alle Logs für dieses Projekt laden
    logs = ProjectTimeLog.query.filter(
        ProjectTimeLog.projekt_id == projekt_id,
        ProjectTimeLog.status.in_(['beendet', 'abgebrochen'])
    ).order_by(ProjectTimeLog.start_time.desc()).all()

    # Gruppiere nach Datum und User
    grouped_data = {}
    for log in logs:
        # Datum extrahieren
        datum = log.start_time.strftime('%Y-%m-%d') if log.start_time else 'Unbekannt'
        # Username holen (oder 'Unbekannt' wenn kein User)
        username = log.user.username if log.user else 'Unbekannt'

        key = (datum, username)
        if key not in grouped_data:
            grouped_data[key] = {
                'datum': log.start_time.strftime('%d.%m.%Y') if log.start_time else 'Unbekannt',
                'datum_sort': datum,
                'user': username,
                'konfiguration': 0,
                'abnahmetest': 0,
                'export': 0,
                'gesamt': 0
            }

        # Zeit addieren (in Sekunden)
        duration = log.duration_seconds or 0
        if log.activity_type == 'konfiguration':
            grouped_data[key]['konfiguration'] += duration
        elif log.activity_type == 'abnahmetest':
            grouped_data[key]['abnahmetest'] += duration
        elif log.activity_type == 'export':
            grouped_data[key]['export'] += duration
        grouped_data[key]['gesamt'] += duration

    # In Liste umwandeln und nach Datum sortieren (neueste zuerst)
    detail_list = list(grouped_data.values())
    detail_list.sort(key=lambda x: x['datum_sort'], reverse=True)

    # Zeiten formatieren
    for item in detail_list:
        item['konfiguration_fmt'] = format_seconds(item['konfiguration'])
        item['abnahmetest_fmt'] = format_seconds(item['abnahmetest'])
        item['export_fmt'] = format_seconds(item['export'])
        item['gesamt_fmt'] = format_seconds(item['gesamt'])

    # Projekt Eröffnung: Einmalig 15 Minuten (900 Sekunden)
    projekt_eroeffnung_sekunden = 900  # 15 Minuten

    # Erste Zeile für Projekt Eröffnung erstellen
    projekt_eroeffnung_row = {
        'datum': projekt.erstellt_am.strftime('%d.%m.%Y') if projekt.erstellt_am else 'Unbekannt',
        'datum_sort': projekt.erstellt_am.strftime('%Y-%m-%d') if projekt.erstellt_am else '0000-00-00',
        'user': '-',
        'projekt_eroeffnung': projekt_eroeffnung_sekunden,
        'projekt_eroeffnung_fmt': format_seconds(projekt_eroeffnung_sekunden),
        'konfiguration': 0,
        'konfiguration_fmt': '-',
        'abnahmetest': 0,
        'abnahmetest_fmt': '-',
        'export': 0,
        'export_fmt': '-',
        'gesamt': projekt_eroeffnung_sekunden,
        'gesamt_fmt': format_seconds(projekt_eroeffnung_sekunden),
        'is_eroeffnung': True
    }

    # Markiere alle anderen Zeilen als nicht-Eröffnung
    for item in detail_list:
        item['projekt_eroeffnung'] = 0
        item['projekt_eroeffnung_fmt'] = '-'
        item['is_eroeffnung'] = False

    # Projekt Eröffnung am Anfang der Liste einfügen
    detail_list.insert(0, projekt_eroeffnung_row)

    # Summen berechnen (inkl. Projekt Eröffnung)
    summen = {
        'projekt_eroeffnung': projekt_eroeffnung_sekunden,
        'konfiguration': sum(d['konfiguration'] for d in detail_list),
        'abnahmetest': sum(d['abnahmetest'] for d in detail_list),
        'export': sum(d['export'] for d in detail_list),
        'gesamt': sum(d['gesamt'] for d in detail_list)
    }
    summen['projekt_eroeffnung_fmt'] = format_seconds(summen['projekt_eroeffnung'])
    summen['konfiguration_fmt'] = format_seconds(summen['konfiguration'])
    summen['abnahmetest_fmt'] = format_seconds(summen['abnahmetest'])
    summen['export_fmt'] = format_seconds(summen['export'])
    summen['gesamt_fmt'] = format_seconds(summen['gesamt'])

    return render_template('zeiterfassung_detail.html',
                          projekt=projekt,
                          detail_list=detail_list,
                          summen=summen)


@zeiterfassung_bp.route('/zeiterfassung/projekt/<int:projekt_id>/pdf')
@login_required
def zeiterfassung_detail_pdf(projekt_id):
    """
    PDF-Export der Zeiterfassung für ein spezifisches Projekt.
    """
    projekt = Project.query.get_or_404(projekt_id)

    # Alle Logs für dieses Projekt laden
    logs = ProjectTimeLog.query.filter(
        ProjectTimeLog.projekt_id == projekt_id,
        ProjectTimeLog.status.in_(['beendet', 'abgebrochen'])
    ).order_by(ProjectTimeLog.start_time.desc()).all()

    # Gruppiere nach Datum und User
    grouped_data = {}
    for log in logs:
        datum = log.start_time.strftime('%Y-%m-%d') if log.start_time else 'Unbekannt'
        username = log.user.username if log.user else 'Unbekannt'

        key = (datum, username)
        if key not in grouped_data:
            grouped_data[key] = {
                'datum': log.start_time.strftime('%d.%m.%Y') if log.start_time else 'Unbekannt',
                'datum_sort': datum,
                'user': username,
                'konfiguration': 0,
                'abnahmetest': 0,
                'export': 0,
                'gesamt': 0
            }

        duration = log.duration_seconds or 0
        if log.activity_type == 'konfiguration':
            grouped_data[key]['konfiguration'] += duration
        elif log.activity_type == 'abnahmetest':
            grouped_data[key]['abnahmetest'] += duration
        elif log.activity_type == 'export':
            grouped_data[key]['export'] += duration
        grouped_data[key]['gesamt'] += duration

    detail_list = list(grouped_data.values())
    detail_list.sort(key=lambda x: x['datum_sort'], reverse=True)

    # Zeiten formatieren
    for item in detail_list:
        item['konfiguration_fmt'] = format_seconds(item['konfiguration'])
        item['abnahmetest_fmt'] = format_seconds(item['abnahmetest'])
        item['export_fmt'] = format_seconds(item['export'])
        item['gesamt_fmt'] = format_seconds(item['gesamt'])

    # Projekt Eröffnung
    projekt_eroeffnung_sekunden = 900
    projekt_eroeffnung_row = {
        'datum': projekt.erstellt_am.strftime('%d.%m.%Y') if projekt.erstellt_am else 'Unbekannt',
        'datum_sort': projekt.erstellt_am.strftime('%Y-%m-%d') if projekt.erstellt_am else '0000-00-00',
        'user': '-',
        'projekt_eroeffnung': projekt_eroeffnung_sekunden,
        'projekt_eroeffnung_fmt': format_seconds(projekt_eroeffnung_sekunden),
        'konfiguration': 0,
        'konfiguration_fmt': '-',
        'abnahmetest': 0,
        'abnahmetest_fmt': '-',
        'export': 0,
        'export_fmt': '-',
        'gesamt': projekt_eroeffnung_sekunden,
        'gesamt_fmt': format_seconds(projekt_eroeffnung_sekunden),
        'is_eroeffnung': True
    }

    for item in detail_list:
        item['projekt_eroeffnung'] = 0
        item['projekt_eroeffnung_fmt'] = '-'
        item['is_eroeffnung'] = False

    detail_list.insert(0, projekt_eroeffnung_row)

    # Summen berechnen
    summen = {
        'projekt_eroeffnung': projekt_eroeffnung_sekunden,
        'konfiguration': sum(d['konfiguration'] for d in detail_list),
        'abnahmetest': sum(d['abnahmetest'] for d in detail_list),
        'export': sum(d['export'] for d in detail_list),
        'gesamt': sum(d['gesamt'] for d in detail_list)
    }
    summen['projekt_eroeffnung_fmt'] = format_seconds(summen['projekt_eroeffnung'])
    summen['konfiguration_fmt'] = format_seconds(summen['konfiguration'])
    summen['abnahmetest_fmt'] = format_seconds(summen['abnahmetest'])
    summen['export_fmt'] = format_seconds(summen['export'])
    summen['gesamt_fmt'] = format_seconds(summen['gesamt'])

    # Export-Datum
    export_datum = datetime.now().strftime('%d.%m.%Y %H:%M')

    # PDF Template rendern
    html_content = render_template('zeiterfassung_detail_pdf.html',
                                   projekt=projekt,
                                   detail_list=detail_list,
                                   summen=summen,
                                   export_datum=export_datum)

    try:
        # PDF generieren mit xhtml2pdf
        pdf_bytes = convert_html_to_pdf(html_content)

        if pdf_bytes is None:
            flash('Fehler bei der PDF-Generierung.', 'error')
            return redirect(url_for('zeiterfassung.zeiterfassung_detail', projekt_id=projekt_id))

        # Dateiname
        projektname_clean = projekt.projektname.replace(' ', '_').replace('/', '-')
        datum_str = datetime.now().strftime('%Y-%m-%d')
        filename = f'Zeiterfassung_{projektname_clean}_{datum_str}.pdf'

        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        flash(f'Fehler beim PDF-Export: {str(e)}', 'error')
        return redirect(url_for('zeiterfassung.zeiterfassung_detail', projekt_id=projekt_id))
