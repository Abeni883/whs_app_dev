"""
SBB Weichenheizung - API Blueprint
AJAX Endpoints für Time-Logging etc.
"""
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_login import current_user

from models import db, ProjectTimeLog, AppSettings

api_bp = Blueprint('api', __name__, url_prefix='/api')


# ==================== HELPER FUNCTIONS ====================

def cleanup_stale_sessions():
    """
    Bereinigt abgebrochene Sessions (älter als konfigurierter Timeout ohne end_time).
    Timeout ist in den App-Einstellungen konfigurierbar.
    """
    # Timeout aus Einstellungen laden (Fallback: 60 Minuten)
    settings = AppSettings.query.first()
    timeout_minuten = settings.zeiterfassung_timeout_minuten if settings else 60

    cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minuten)

    stale_logs = ProjectTimeLog.query.filter(
        ProjectTimeLog.status == 'aktiv',
        ProjectTimeLog.start_time < cutoff_time
    ).all()

    for log in stale_logs:
        log.end_time = log.start_time + timedelta(minutes=timeout_minuten)
        log.calculate_duration()
        log.status = 'abgebrochen'

    if stale_logs:
        db.session.commit()


# ==================== TIME-LOG API ====================

@api_bp.route('/time-log/start', methods=['POST'])
def time_log_start():
    """
    Startet einen neuen Zeiterfassungs-Eintrag.

    JSON Body:
        - projekt_id: Optional, ID des Projekts
        - activity_type: Art der Aktivität (konfiguration, abnahmetest, export, etc.)
        - page_url: URL der besuchten Seite

    Returns:
        JSON mit log_id bei Erfolg
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine Daten erhalten'}), 400

        activity_type = data.get('activity_type')
        if not activity_type:
            return jsonify({'error': 'activity_type ist erforderlich'}), 400

        # Alte aktive Sessions für gleiche Aktivität beenden
        cleanup_stale_sessions()

        # Neuen Log-Eintrag erstellen
        time_log = ProjectTimeLog(
            projekt_id=data.get('projekt_id'),
            user_id=current_user.id if current_user.is_authenticated else None,
            activity_type=activity_type,
            page_url=data.get('page_url'),
            start_time=datetime.utcnow(),
            status='aktiv'
        )
        db.session.add(time_log)
        db.session.commit()

        return jsonify({
            'success': True,
            'log_id': time_log.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/time-log/stop', methods=['POST'])
def time_log_stop():
    """
    Beendet einen laufenden Zeiterfassungs-Eintrag.

    JSON Body:
        - log_id: ID des zu beendenden Logs

    Returns:
        JSON mit duration_seconds bei Erfolg
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine Daten erhalten'}), 400

        log_id = data.get('log_id')
        if not log_id:
            return jsonify({'error': 'log_id ist erforderlich'}), 400

        time_log = ProjectTimeLog.query.get(log_id)
        if not time_log:
            return jsonify({'error': 'Log nicht gefunden'}), 404

        if time_log.status != 'aktiv':
            return jsonify({'error': 'Log ist bereits beendet'}), 400

        # Log beenden
        time_log.end_time = datetime.utcnow()
        time_log.calculate_duration()
        time_log.status = 'beendet'
        db.session.commit()

        return jsonify({
            'success': True,
            'duration_seconds': time_log.duration_seconds,
            'duration_formatted': time_log.format_duration()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/time-log/heartbeat', methods=['POST'])
def time_log_heartbeat():
    """
    Heartbeat um aktive Session am Leben zu halten.

    JSON Body:
        - log_id: ID des aktiven Logs

    Returns:
        JSON mit success=True bei Erfolg
    """
    try:
        data = request.get_json()
        log_id = data.get('log_id') if data else None

        if log_id:
            time_log = ProjectTimeLog.query.get(log_id)
            if time_log and time_log.status == 'aktiv':
                # Nur Status aktualisieren um Timeout zu verhindern
                db.session.commit()
                return jsonify({'success': True, 'status': 'aktiv'})

        return jsonify({'success': False, 'status': 'nicht_gefunden'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
