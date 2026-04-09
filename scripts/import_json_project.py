"""
Generisches Script zum Importieren von Projekten aus dem alten JSON-Format
Verwendet: python import_json_project.py "Pfad/zum/projekt.json" [--force]
"""
import sys
import os
import io
import json
import argparse
from datetime import datetime

# UTF-8 Encoding für Windows-Konsole
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Project, WHKConfig, TestQuestion, AbnahmeTestResult

def parse_date(date_string):
    """Konvertiert Datum-String in verschiedenen Formaten zu datetime.date"""
    if not date_string:
        return None

    formats = ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    return None

def standardize_result(ergebnis):
    """Standardisiert Testergebnisse"""
    if ergebnis == 'Richtig':
        return 'richtig'
    elif ergebnis == 'Falsch':
        return 'falsch'
    elif ergebnis == 'Nicht Testbar':
        return 'nicht_testbar'
    return None

def safe_int(value, default=0):
    """Konvertiert einen Wert sicher zu Integer, behandelt leere Strings"""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def check_existing_project(projektname, didok):
    """Prüft ob Projekt bereits existiert"""
    with app.app_context():
        existing = Project.query.filter(
            (Project.projektname == projektname) |
            (Project.didok_betriebspunkt == didok)
        ).first()
        return existing

def import_projekt(json_path, force=False):
    """Importiert ein Projekt aus JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with app.app_context():
        # PROJEKT-INFO
        info = data.get('projektinfo', {})
        projektname = info.get('projektname', 'Unbekannt')
        didok = info.get('didok', 'XXX')

        # Prüfe ob Projekt existiert
        existing = check_existing_project(projektname, didok)
        if existing and not force:
            print(f"\n⚠ FEHLER: Projekt '{projektname}' ({didok}) existiert bereits (ID: {existing.id})")
            print("Verwende --force um es zu überschreiben")
            return False

        if existing and force:
            print(f"\n⚠ Lösche existierendes Projekt '{projektname}' (ID: {existing.id})")
            # Lösche abhängige Daten
            AbnahmeTestResult.query.filter_by(projekt_id=existing.id).delete()
            WHKConfig.query.filter_by(projekt_id=existing.id).delete()
            db.session.delete(existing)
            db.session.commit()

        # 1. PROJEKT ERSTELLEN
        print("\n### PROJEKT ERSTELLEN ###")

        projekt = Project(
            energie=info.get('energie', 'EWH'),
            projektname=projektname,
            didok_betriebspunkt=didok,
            baumappenversion=parse_date(info.get('baumappe')),
            projektleiter_sbb=info.get('projektleiter', ''),
            pruefer_achermann=info.get('pruefer', ''),
            pruefdatum=parse_date(info.get('pruefdatum')),
            bemerkung=info.get('bemerkungen', '')
        )

        db.session.add(projekt)
        db.session.flush()

        print(f"✓ Projekt: {projekt.projektname} (ID: {projekt.id})")

        # 2. WHK-KONFIGURATIONEN
        print("\n### WHK-KONFIGURATIONEN ###")
        whk_configs = []

        for whk_data in data.get('felder', []):
            whk = WHKConfig(
                projekt_id=projekt.id,
                whk_nummer=whk_data.get('name', 'WHK 01'),
                anzahl_abgaenge=safe_int(whk_data.get('abgang'), 0),
                anzahl_temperatursonden=safe_int(whk_data.get('temp'), 1),
                hat_antriebsheizung=bool(whk_data.get('ah', False)),
                meteostation=whk_data.get('meteo', None) if whk_data.get('meteo') else None
            )
            db.session.add(whk)
            whk_configs.append(whk)
            ms_info = f", MS: {whk.meteostation}" if whk.meteostation else ""
            print(f"✓ {whk.whk_nummer}: {whk.anzahl_abgaenge} ABG, {whk.anzahl_temperatursonden} TS{ms_info}")

        db.session.flush()

        # 3. TESTERGEBNISSE
        print("\n### TESTERGEBNISSE IMPORTIEREN ###")
        imported = 0

        abgaenge_data = data.get('abgaenge', {})

        # ANLAGE (keine WHK-Ebene)
        # WICHTIG: ANLAGE hat nur Spalte C und B (keine A)
        # Für ANLAGE: Spalte C = LSS-CH, Spalte B = WH-LTS
        if 'ANLAGE' in abgaenge_data:
            print("\nVerarbeite ANLAGE...")
            print("  Spezielles Mapping für ANLAGE: C->LSS-CH, B->WH-LTS")
            for frage_idx_str, frage_data in abgaenge_data['ANLAGE'].items():
                frage_idx = int(frage_idx_str)
                reihenfolge = frage_idx + 1

                test_q = TestQuestion.query.filter_by(
                    komponente_typ='Anlage',
                    reihenfolge=reihenfolge
                ).first()

                if test_q:
                    auswahl = frage_data.get('auswahl', {})

                    lss_ch_res = None
                    wh_lts_res = None

                    # Für ANLAGE: C -> LSS-CH, B -> WH-LTS
                    if 'C' in auswahl and '0' in auswahl['C']:
                        lss_ch_res = standardize_result(auswahl['C']['0'])
                    if 'B' in auswahl and '0' in auswahl['B']:
                        wh_lts_res = standardize_result(auswahl['B']['0'])

                    if lss_ch_res or wh_lts_res:
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=test_q.id,
                            komponente_index='Anlage',
                            spalte=None,
                            lss_ch_result=lss_ch_res,
                            wh_lts_result=wh_lts_res
                        )
                        db.session.add(result)
                        imported += 1

        # WHK (keine WHK-Ebene, direkt Fragen, aber mehrere WHKs in Spalten)
        if 'WHK' in abgaenge_data:
            print("\nVerarbeite WHK (Weichenheizkabinen)...")
            for frage_idx_str, frage_data in abgaenge_data['WHK'].items():
                frage_idx = int(frage_idx_str)
                reihenfolge = frage_idx + 1

                test_q = TestQuestion.query.filter_by(
                    komponente_typ='WHK',
                    reihenfolge=reihenfolge
                ).first()

                if test_q:
                    auswahl = frage_data.get('auswahl', {})

                    # Anzahl WHKs bestimmen (aus Spalte A)
                    anzahl_whks = 0
                    if 'A' in auswahl:
                        anzahl_whks = len(auswahl['A'])

                    # Falls keine WHKs in Spalte A, versuche Spalte B oder C
                    if anzahl_whks == 0 and 'B' in auswahl:
                        anzahl_whks = len(auswahl['B'])
                    if anzahl_whks == 0 and 'C' in auswahl:
                        anzahl_whks = len(auswahl['C'])

                    # Für jede WHK
                    for whk_idx in range(anzahl_whks):
                        # Prüfe ob dieser WHK-Index gültig ist
                        if whk_idx >= len(whk_configs):
                            continue

                        komp_idx = whk_configs[whk_idx].whk_nummer

                        lss_ch_res = None
                        wh_lts_res = None

                        if 'A' in auswahl and str(whk_idx) in auswahl['A']:
                            lss_ch_res = standardize_result(auswahl['A'][str(whk_idx)])
                        if 'B' in auswahl and str(whk_idx) in auswahl['B']:
                            wh_lts_res = standardize_result(auswahl['B'][str(whk_idx)])

                        if lss_ch_res or wh_lts_res:
                            result = AbnahmeTestResult(
                                projekt_id=projekt.id,
                                test_question_id=test_q.id,
                                komponente_index=komp_idx,
                                spalte=None,
                                lss_ch_result=lss_ch_res,
                                wh_lts_result=wh_lts_res
                            )
                            db.session.add(result)
                            imported += 1

        # ABG (mit WHK-Ebene, mehrere Abgänge)
        if 'ABG' in abgaenge_data:
            print("\nVerarbeite ABG (Abgänge)...")
            for whk_idx_str, whk_data in abgaenge_data['ABG'].items():
                whk_idx = int(whk_idx_str)
                # Prüfe ob WHK-Index gültig ist
                if whk_idx >= len(whk_configs):
                    continue
                komp_idx = whk_configs[whk_idx].whk_nummer

                for frage_idx_str, frage_data in whk_data.items():
                    frage_idx = int(frage_idx_str)
                    reihenfolge = frage_idx + 1

                    test_q = TestQuestion.query.filter_by(
                        komponente_typ='Abgang',
                        reihenfolge=reihenfolge
                    ).first()

                    if test_q:
                        auswahl = frage_data.get('auswahl', {})

                        # Anzahl Abgänge bestimmen
                        anzahl_abgaenge = 0
                        if 'A' in auswahl:
                            anzahl_abgaenge = len(auswahl['A'])

                        # Für jeden Abgang
                        for abg_idx in range(anzahl_abgaenge):
                            spalte = f"Abgang {abg_idx + 1:02d}"

                            lss_ch_res = None
                            wh_lts_res = None

                            if 'A' in auswahl and str(abg_idx) in auswahl['A']:
                                lss_ch_res = standardize_result(auswahl['A'][str(abg_idx)])
                            if 'B' in auswahl and str(abg_idx) in auswahl['B']:
                                wh_lts_res = standardize_result(auswahl['B'][str(abg_idx)])

                            if lss_ch_res or wh_lts_res:
                                result = AbnahmeTestResult(
                                    projekt_id=projekt.id,
                                    test_question_id=test_q.id,
                                    komponente_index=komp_idx,
                                    spalte=spalte,
                                    lss_ch_result=lss_ch_res,
                                    wh_lts_result=wh_lts_res
                                )
                                db.session.add(result)
                                imported += 1

        # TS (mit WHK-Ebene, mehrere Temperatursonden)
        if 'TS' in abgaenge_data:
            print("\nVerarbeite TS (Temperatursonden)...")
            for whk_idx_str, whk_data in abgaenge_data['TS'].items():
                whk_idx = int(whk_idx_str)
                # Prüfe ob WHK-Index gültig ist
                if whk_idx >= len(whk_configs):
                    continue
                komp_idx = whk_configs[whk_idx].whk_nummer

                for frage_idx_str, frage_data in whk_data.items():
                    frage_idx = int(frage_idx_str)
                    reihenfolge = frage_idx + 1

                    test_q = TestQuestion.query.filter_by(
                        komponente_typ='Temperatursonde',
                        reihenfolge=reihenfolge
                    ).first()

                    if test_q:
                        auswahl = frage_data.get('auswahl', {})

                        # Anzahl TS bestimmen
                        anzahl_ts = 0
                        if 'A' in auswahl:
                            anzahl_ts = len(auswahl['A'])

                        # Für jede TS
                        for ts_idx in range(anzahl_ts):
                            spalte = f"TS {ts_idx + 1:02d}"

                            lss_ch_res = None
                            wh_lts_res = None

                            if 'A' in auswahl and str(ts_idx) in auswahl['A']:
                                lss_ch_res = standardize_result(auswahl['A'][str(ts_idx)])
                            if 'B' in auswahl and str(ts_idx) in auswahl['B']:
                                wh_lts_res = standardize_result(auswahl['B'][str(ts_idx)])

                            if lss_ch_res or wh_lts_res:
                                result = AbnahmeTestResult(
                                    projekt_id=projekt.id,
                                    test_question_id=test_q.id,
                                    komponente_index=komp_idx,
                                    spalte=spalte,
                                    lss_ch_result=lss_ch_res,
                                    wh_lts_result=wh_lts_res
                                )
                                db.session.add(result)
                                imported += 1

        # MS (mit WHK-Ebene, eine Meteostation)
        if 'MS' in abgaenge_data:
            print("\nVerarbeite MS (Meteostationen)...")
            for whk_idx_str, whk_data in abgaenge_data['MS'].items():
                whk_idx = int(whk_idx_str)
                ms_name = whk_configs[whk_idx].meteostation if whk_idx < len(whk_configs) else "MS 01"

                for frage_idx_str, frage_data in whk_data.items():
                    frage_idx = int(frage_idx_str)
                    reihenfolge = frage_idx + 1

                    test_q = TestQuestion.query.filter_by(
                        komponente_typ='Meteostation',
                        reihenfolge=reihenfolge
                    ).first()

                    if test_q:
                        auswahl = frage_data.get('auswahl', {})

                        lss_ch_res = None
                        wh_lts_res = None

                        if 'A' in auswahl and '0' in auswahl['A']:
                            lss_ch_res = standardize_result(auswahl['A']['0'])
                        if 'B' in auswahl and '0' in auswahl['B']:
                            wh_lts_res = standardize_result(auswahl['B']['0'])

                        if lss_ch_res or wh_lts_res:
                            # WICHTIG: komponente_index = ms_name (nicht WHK-Nr)
                            result = AbnahmeTestResult(
                                projekt_id=projekt.id,
                                test_question_id=test_q.id,
                                komponente_index=ms_name,
                                spalte=ms_name,
                                lss_ch_result=lss_ch_res,
                                wh_lts_result=wh_lts_res
                            )
                            db.session.add(result)
                            imported += 1

        # AH (mit WHK-Ebene, Antriebsheizung)
        if 'AH' in abgaenge_data:
            print("\nVerarbeite AH (Antriebsheizung)...")
            for whk_idx_str, whk_data in abgaenge_data['AH'].items():
                whk_idx = int(whk_idx_str)
                # Prüfe ob WHK-Index gültig ist
                if whk_idx >= len(whk_configs):
                    continue
                komp_idx = whk_configs[whk_idx].whk_nummer

                for frage_idx_str, frage_data in whk_data.items():
                    frage_idx = int(frage_idx_str)
                    reihenfolge = frage_idx + 1

                    test_q = TestQuestion.query.filter_by(
                        komponente_typ='Antriebsheizung',
                        reihenfolge=reihenfolge
                    ).first()

                    if test_q:
                        auswahl = frage_data.get('auswahl', {})

                        lss_ch_res = None
                        wh_lts_res = None

                        if 'A' in auswahl and '0' in auswahl['A']:
                            lss_ch_res = standardize_result(auswahl['A']['0'])
                        if 'B' in auswahl and '0' in auswahl['B']:
                            wh_lts_res = standardize_result(auswahl['B']['0'])

                        if lss_ch_res or wh_lts_res:
                            result = AbnahmeTestResult(
                                projekt_id=projekt.id,
                                test_question_id=test_q.id,
                                komponente_index=komp_idx,
                                spalte='Antriebsheizung',
                                lss_ch_result=lss_ch_res,
                                wh_lts_result=wh_lts_res
                            )
                            db.session.add(result)
                            imported += 1

        # Speichern
        db.session.commit()

        print(f"\n✓ Import abgeschlossen: {imported} Testergebnisse")
        return True

def verify(projektname=None):
    """Verifiziert den Import"""
    with app.app_context():
        print("\n" + "=" * 80)
        print("VERIFIZIERUNG")
        print("=" * 80)

        if projektname:
            projekt = Project.query.filter_by(projektname=projektname).first()
            if not projekt:
                print(f"\n⚠ Projekt '{projektname}' nicht gefunden!")
                return

            projekte = [projekt]
        else:
            projekte = Project.query.all()

        print(f"\nProjekte: {len(projekte)}")
        for p in projekte:
            print(f"  - {p.projektname} ({p.didok_betriebspunkt})")

            # WHKs für dieses Projekt
            whks = WHKConfig.query.filter_by(projekt_id=p.id).all()
            print(f"    WHK-Konfigurationen: {len(whks)}")
            for w in whks:
                ms_info = f", MS: {w.meteostation}" if w.meteostation else ""
                print(f"      - {w.whk_nummer}: {w.anzahl_abgaenge} ABG, {w.anzahl_temperatursonden} TS{ms_info}")

            # Testergebnisse für dieses Projekt
            results = AbnahmeTestResult.query.filter_by(projekt_id=p.id).all()
            print(f"    Testergebnisse: {len(results)}")

            # Nach Komponententyp
            from sqlalchemy import func
            komponenten = db.session.query(
                TestQuestion.komponente_typ,
                func.count(AbnahmeTestResult.id).label('anzahl')
            ).join(
                AbnahmeTestResult
            ).filter(
                AbnahmeTestResult.projekt_id == p.id
            ).group_by(TestQuestion.komponente_typ).all()

            print("      Nach Komponententyp:")
            for k, a in komponenten:
                print(f"        {k:20s}: {a:3d}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Importiert ein Projekt aus JSON')
    parser.add_argument('json_file', help='Pfad zum JSON-File')
    parser.add_argument('--force', action='store_true', help='Überschreibt existierendes Projekt')
    parser.add_argument('--no-verify', action='store_true', help='Keine Verifizierung nach Import')

    args = parser.parse_args()

    # Absoluter Pfad
    if not os.path.isabs(args.json_file):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            args.json_file
        )
    else:
        json_path = args.json_file

    if not os.path.exists(json_path):
        print(f"\n⚠ FEHLER: Datei nicht gefunden: {json_path}")
        sys.exit(1)

    print("=" * 80)
    print("PROJEKT-IMPORT AUS JSON")
    print("=" * 80)
    print(f"\nQuelle: {json_path}")
    print(f"Force-Modus: {'Ja' if args.force else 'Nein'}")

    with app.app_context():
        success = import_projekt(json_path, force=args.force)

        if success and not args.no_verify:
            # Extrahiere Projektname aus JSON für Verifizierung
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                projektname = data.get('projektinfo', {}).get('projektname')
                verify(projektname)

        if success:
            print("\n✓ FERTIG!")
        else:
            print("\n⚠ ABGEBROCHEN!")
            sys.exit(1)
