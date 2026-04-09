"""
SBB Weichenheizung - Konfiguration Blueprint
WHK/ZSK Konfiguration für EWH und GWH Projekte
"""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required

from models import db, Project, WHKConfig, ZSKConfig, HGLSConfig, GWHMeteostation, EWHMeteostation

konfiguration_bp = Blueprint('konfiguration', __name__)


# ==================== EWH KONFIGURATION ====================

@konfiguration_bp.route('/projekt/konfiguration/<int:projekt_id>', methods=['GET', 'POST'])
@login_required
def projekt_konfiguration(projekt_id):
    """
    WHK-Konfiguration (Weichenheizungskästen) für ein Projekt.

    GET: Zeigt Konfigurationsformular mit bestehenden WHK-Einträgen
    POST: Speichert alle WHK-Konfigurationen (überschreibt bestehende)

    Args:
        projekt_id: ID des Projekts

    Returns:
        GET: HTML-Formular (konfiguration.html)
        POST: Redirect zur Konfigurationsseite mit Flash-Message
    """
    projekt = Project.query.get(projekt_id)

    if not projekt:
        flash('Projekt nicht gefunden!', 'error')
        return redirect(url_for('projekte.projekte'))

    if request.method == 'POST':
        # Lösche alle bestehenden WHK-Konfigurationen für dieses Projekt
        WHKConfig.query.filter_by(projekt_id=projekt_id).delete()

        # Verarbeite die Formular-Daten
        # Durchlaufe alle whk_nr_* Felder im Formular
        whk_count = 0
        for key in request.form.keys():
            if key.startswith('whk_nr_'):
                # Extrahiere die Nummer (z.B. whk_nr_1 -> 1)
                index = key.split('_')[-1]

                whk_nummer = request.form.get(f'whk_nr_{index}')
                preset_typ = request.form.get(f'preset_typ_{index}', 'kabine_16hz')
                anzahl_abgaenge = int(request.form.get(f'abgaenge_{index}', 1))
                anzahl_temperatursonden = int(request.form.get(f'temperatursonden_{index}', 1))
                hat_antriebsheizung = f'antriebsheizung_{index}' in request.form

                # Erstelle neuen WHKConfig-Eintrag
                whk_config = WHKConfig(
                    projekt_id=projekt_id,
                    whk_nummer=whk_nummer,
                    preset_typ=preset_typ,
                    anzahl_abgaenge=anzahl_abgaenge,
                    anzahl_temperatursonden=anzahl_temperatursonden,
                    hat_antriebsheizung=hat_antriebsheizung
                )
                db.session.add(whk_config)
                whk_count += 1

        db.session.commit()
        flash(f'Konfiguration erfolgreich gespeichert! ({whk_count} WHK konfiguriert)', 'success')
        return redirect(url_for('konfiguration.projekt_konfiguration', projekt_id=projekt_id))

    # GET-Request: Lade bestehende Konfigurationen
    whk_configs = WHKConfig.query.filter_by(projekt_id=projekt_id).order_by(WHKConfig.whk_nummer).all()
    ewh_meteostationen = EWHMeteostation.query.filter_by(projekt_id=projekt_id).order_by(EWHMeteostation.reihenfolge).all()

    # Falls keine Meteostation vorhanden, automatisch eine erstellen
    if not ewh_meteostationen:
        default_ms = EWHMeteostation(
            projekt_id=projekt_id,
            ms_nummer='MS 01',
            reihenfolge=0
        )
        db.session.add(default_ms)
        db.session.commit()
        ewh_meteostationen = [default_ms]

    return render_template('konfiguration.html', projekt=projekt, whk_configs=whk_configs, ewh_meteostationen=ewh_meteostationen)


@konfiguration_bp.route('/projekt/konfiguration/auto-save/<int:projekt_id>', methods=['POST'])
@login_required
def konfiguration_auto_save(projekt_id):
    """
    Auto-Save API für WHK- und Meteostation-Konfiguration (AJAX).

    Empfängt JSON mit WHK- und Meteostation-Daten und speichert sie automatisch.

    Args:
        projekt_id: ID des Projekts

    JSON Body:
        {
            "whk_rows": [
                {
                    "whk_nummer": "WHK 01",
                    "anzahl_abgaenge": 4,
                    "anzahl_temperatursonden": 2,
                    "hat_antriebsheizung": true
                },
                ...
            ],
            "meteostationen": [
                {
                    "ms_nummer": "MS 01",
                    "zugeordnete_whk": "WHK 01"
                },
                ...
            ]
        }

    Returns:
        JSON: {"success": bool, "message": str, "counts": dict, "timestamp": str}
    """
    try:
        data = request.get_json()

        # Prüfe ob Projekt existiert
        projekt = Project.query.get(projekt_id)
        if not projekt:
            return jsonify({'success': False, 'error': 'Projekt nicht gefunden'}), 404

        # ========== WHK-Konfigurationen verarbeiten ==========
        # Lösche alle bestehenden WHK-Konfigs für dieses Projekt
        WHKConfig.query.filter_by(projekt_id=projekt_id).delete()
        db.session.flush()  # Sicherstellen dass Löschung vor Insert ausgeführt wird

        # Erstelle neue WHK-Konfigs aus den übermittelten Daten
        whk_rows = data.get('whk_rows', [])
        whk_count = 0

        for row_data in whk_rows:
            # Validierung: WHK-Nummer muss vorhanden sein
            whk_nummer = row_data.get('whk_nummer', '').strip()
            if not whk_nummer:
                continue  # Überspringe unvollständige Zeilen

            new_config = WHKConfig(
                projekt_id=projekt_id,
                whk_nummer=whk_nummer,
                preset_typ=row_data.get('preset_typ', 'kabine_16hz'),
                anzahl_abgaenge=int(row_data.get('anzahl_abgaenge', 1)),
                anzahl_temperatursonden=int(row_data.get('anzahl_temperatursonden', 1)),
                hat_antriebsheizung=row_data.get('hat_antriebsheizung', False)
            )
            db.session.add(new_config)
            whk_count += 1

        # Flush um WHK IDs zu erhalten (für Meteostation-Zuordnung)
        db.session.flush()

        # ========== EWH-Meteostationen verarbeiten ==========
        # Lösche alle bestehenden EWH-Meteostationen für dieses Projekt
        EWHMeteostation.query.filter_by(projekt_id=projekt_id).delete()
        db.session.flush()  # Sicherstellen dass Löschung vor Insert ausgeführt wird

        meteostationen = data.get('meteostationen', [])
        ms_count = 0

        for idx, ms_data in enumerate(meteostationen):
            ms_nummer = ms_data.get('ms_nummer', '').strip()
            if not ms_nummer:
                continue  # Überspringe unvollständige Einträge

            # WHK-Zuordnung finden (falls angegeben)
            zugeordnete_whk_nummer = ms_data.get('zugeordnete_whk', '').strip()
            zugeordnete_whk_id = None

            if zugeordnete_whk_nummer:
                # Suche den WHK in der gerade erstellten Liste
                whk = WHKConfig.query.filter_by(
                    projekt_id=projekt_id,
                    whk_nummer=zugeordnete_whk_nummer
                ).first()
                if whk:
                    zugeordnete_whk_id = whk.id

            new_ms = EWHMeteostation(
                projekt_id=projekt_id,
                ms_nummer=ms_nummer,
                zugeordnete_whk_id=zugeordnete_whk_id,
                reihenfolge=idx + 1
            )
            db.session.add(new_ms)
            ms_count += 1

        # Mindestens 1 Meteostation sicherstellen
        if ms_count == 0:
            default_ms = EWHMeteostation(
                projekt_id=projekt_id,
                ms_nummer='MS 01',
                reihenfolge=0
            )
            db.session.add(default_ms)
            ms_count = 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Konfiguration gespeichert',
            'timestamp': datetime.utcnow().isoformat(),
            'counts': {
                'whk': whk_count,
                'meteostationen': ms_count
            }
        })

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== GWH KONFIGURATION ====================

@konfiguration_bp.route('/projekt/<int:projekt_id>/gwh-konfiguration', methods=['GET', 'POST'])
@login_required
def gwh_konfiguration(projekt_id):
    """
    GWH-Konfiguration (Gasweichenheizung) für ein Projekt.

    GET: Zeigt Konfigurationsformular mit bestehenden ZSK, HGLS und Meteostation-Einträgen
    POST: Speichert alle GWH-Konfigurationen (überschreibt bestehende, JSON-basiert)

    Args:
        projekt_id: ID des Projekts

    Returns:
        GET: HTML-Formular (gwh_konfiguration.html)
        POST: JSON-Response mit success/error

    JSON Structure (POST):
        {
            "hgls": {
                "aktiv": bool,
                "typ": "Propan" | "Erdgas",
                "fuellventil": bool,
                "bypassventil": bool,
                "gaswarnanlage": bool,
                "lueftungsanlage": bool,
                "mengenmesser_blockade": bool,
                "elektroverdampfer": bool,
                "gasverdampfer_anzahl": 0-2,
                "tankdruckueberwachung": bool,
                "tankberieselung": bool,
                "kathodenschutz": bool
            },
            "zsk_liste": [
                {
                    "zsk_nummer": "01",
                    "anzahl_teile": 1-12,
                    "hat_temperatursonde": bool,
                    "gasversorgung": "zentral" | "dezentral",
                    "kathodenschutz": bool
                }
            ],
            "meteostationen": [
                {
                    "ms_nummer": "01",
                    "name": "MS 01",
                    "zugeordneter_zsk": "01",
                    "modbus_adresse": 50
                }
            ]
        }
    """
    # Projekt laden
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
        flash('Diese Konfiguration ist nur für GWH-Projekte verfügbar!', 'error')
        return redirect(url_for('konfiguration.projekt_konfiguration', projekt_id=projekt_id))

    if request.method == 'POST':
        try:
            data = request.get_json()

            if not data:
                return jsonify({'success': False, 'error': 'Keine Daten empfangen'}), 400

            # ========== HGLS-Konfiguration verarbeiten ==========
            hgls_data = data.get('hgls', {})
            hgls_aktiv = hgls_data.get('aktiv', False)

            if hgls_aktiv:
                # HGLS erstellen oder aktualisieren
                hgls = HGLSConfig.query.filter_by(projekt_id=projekt_id).first()
                if not hgls:
                    hgls = HGLSConfig(projekt_id=projekt_id)

                hgls.hgls_typ = hgls_data.get('typ')
                hgls.hat_fuellventil = hgls_data.get('fuellventil', False)
                hgls.hat_bypassventil = hgls_data.get('bypassventil', False)
                hgls.hat_gaswarnanlage = hgls_data.get('gaswarnanlage', False)
                hgls.hat_lueftungsanlage = hgls_data.get('lueftungsanlage', False)
                hgls.hat_mengenmesser_blockade = hgls_data.get('mengenmesser_blockade', False)
                hgls.hat_elektroverdampfer = hgls_data.get('elektroverdampfer', False)
                hgls.gasverdampfer_anzahl = int(hgls_data.get('gasverdampfer_anzahl', 0))
                hgls.hat_tankdruckueberwachung = hgls_data.get('tankdruckueberwachung', False)
                hgls.hat_tankberieselung = hgls_data.get('tankberieselung', False)
                hgls.hat_kathodenschutz = hgls_data.get('kathodenschutz', False)

                db.session.add(hgls)
            else:
                # HGLS löschen falls vorhanden
                HGLSConfig.query.filter_by(projekt_id=projekt_id).delete()

            # ========== ZSK-Konfigurationen verarbeiten ==========
            # Alle bestehenden ZSKs löschen
            ZSKConfig.query.filter_by(projekt_id=projekt_id).delete()
            db.session.flush()  # Sicherstellen dass Löschung vor Insert ausgeführt wird

            zsk_liste = data.get('zsk_liste', [])
            zsk_count = 0

            for idx, zsk_data in enumerate(zsk_liste):
                zsk_nummer = zsk_data.get('zsk_nummer', '').strip()
                if not zsk_nummer:
                    continue  # Überspringe unvollständige Einträge

                new_zsk = ZSKConfig(
                    projekt_id=projekt_id,
                    zsk_nummer=zsk_nummer,
                    anzahl_teile=int(zsk_data.get('anzahl_teile', 1)),
                    hat_temperatursonde=zsk_data.get('hat_temperatursonde', False),
                    gasversorgung=zsk_data.get('gasversorgung', 'zentral'),
                    kathodenschutz=zsk_data.get('kathodenschutz', False),
                    reihenfolge=idx + 1
                )
                db.session.add(new_zsk)
                zsk_count += 1

            # Mindestens 1 ZSK sicherstellen
            if zsk_count == 0:
                default_zsk = ZSKConfig(
                    projekt_id=projekt_id,
                    zsk_nummer='ZSK 01',
                    anzahl_teile=1,
                    hat_temperatursonde=False,
                    gasversorgung='zentral',
                    kathodenschutz=False,
                    reihenfolge=0
                )
                db.session.add(default_zsk)
                zsk_count = 1

            # ========== Meteostationen verarbeiten ==========
            # Alle bestehenden Meteostationen löschen
            GWHMeteostation.query.filter_by(projekt_id=projekt_id).delete()
            db.session.flush()  # Sicherstellen dass Löschung vor Insert ausgeführt wird

            meteostationen = data.get('meteostationen', [])
            ms_count = 0

            for idx, ms_data in enumerate(meteostationen):
                ms_nummer = ms_data.get('ms_nummer', '').strip()
                if not ms_nummer:
                    continue  # Überspringe unvollständige Einträge

                # ZSK-Zuordnung finden (falls angegeben)
                zugeordneter_zsk_nummer = ms_data.get('zugeordneter_zsk', '').strip()
                zugeordneter_zsk_id = None

                if zugeordneter_zsk_nummer:
                    # Suche den ZSK in der gerade erstellten Liste
                    zsk = ZSKConfig.query.filter_by(
                        projekt_id=projekt_id,
                        zsk_nummer=zugeordneter_zsk_nummer
                    ).first()
                    if zsk:
                        zugeordneter_zsk_id = zsk.id

                new_ms = GWHMeteostation(
                    projekt_id=projekt_id,
                    ms_nummer=ms_nummer,
                    # ms_nummer enthält bereits "MS 01" etc., daher direkt verwenden
                    name=ms_data.get('name', ms_nummer)[:12],  # Max. 12 Zeichen
                    zugeordneter_zsk_id=zugeordneter_zsk_id,
                    modbus_adresse=int(ms_data.get('modbus_adresse', 50)),
                    reihenfolge=idx + 1
                )
                db.session.add(new_ms)
                ms_count += 1

            # Mindestens 1 Meteostation sicherstellen
            if ms_count == 0:
                default_ms = GWHMeteostation(
                    projekt_id=projekt_id,
                    ms_nummer='MS 01',
                    name='MS 01',
                    reihenfolge=0
                )
                db.session.add(default_ms)
                ms_count = 1

            # Alle Änderungen committen
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'GWH-Konfiguration erfolgreich gespeichert',
                'timestamp': datetime.utcnow().isoformat(),
                'counts': {
                    'hgls': 1 if hgls_aktiv else 0,
                    'zsk': zsk_count,
                    'meteostationen': ms_count
                }
            })

        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET-Request: Lade bestehende Konfigurationen
    hgls_config = HGLSConfig.query.filter_by(projekt_id=projekt_id).first()
    zsk_configs = ZSKConfig.query.filter_by(projekt_id=projekt_id).order_by(ZSKConfig.reihenfolge).all()
    gwh_meteostationen = GWHMeteostation.query.filter_by(projekt_id=projekt_id).order_by(GWHMeteostation.reihenfolge).all()

    # Falls kein ZSK vorhanden, automatisch einen erstellen
    if not zsk_configs:
        default_zsk = ZSKConfig(
            projekt_id=projekt_id,
            zsk_nummer='ZSK 01',
            anzahl_teile=1,
            hat_temperatursonde=False,
            gasversorgung='zentral',
            kathodenschutz=False,
            reihenfolge=0
        )
        db.session.add(default_zsk)
        db.session.commit()
        zsk_configs = [default_zsk]

    # Falls keine Meteostation vorhanden, automatisch eine erstellen
    if not gwh_meteostationen:
        default_ms = GWHMeteostation(
            projekt_id=projekt_id,
            ms_nummer='MS 01',
            name='MS 01',
            reihenfolge=0
        )
        db.session.add(default_ms)
        db.session.commit()
        gwh_meteostationen = [default_ms]

    return render_template(
        'gwh_konfiguration.html',
        projekt=projekt,
        hgls_config=hgls_config,
        zsk_configs=zsk_configs,
        gwh_meteostationen=gwh_meteostationen
    )
