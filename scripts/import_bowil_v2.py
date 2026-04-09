"""
Script zum Importieren des Bowil-Projekts aus dem alten JSON-Format - Version 2
"""
import sys
import os
import io
import json
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

def delete_all_projects():
    """Löscht alle Projekte"""
    with app.app_context():
        count = Project.query.count()
        print(f"\nAktuelle Anzahl Projekte: {count}")
        if count > 0:
            Project.query.delete()
            db.session.commit()
            print("✓ Alle Projekte gelöscht!")

def import_projekt(json_path):
    """Importiert das Bowil-Projekt"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with app.app_context():
        # 1. PROJEKT ERSTELLEN
        print("\n### PROJEKT ERSTELLEN ###")
        info = data.get('projektinfo', {})

        projekt = Project(
            energie='EWH',
            projektname=info.get('projektname', 'Bowil'),
            didok_betriebspunkt=info.get('didok', 'BOW'),
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
                anzahl_abgaenge=int(whk_data.get('abgang', 1)),
                anzahl_temperatursonden=int(whk_data.get('temp', 1)),
                hat_antriebsheizung=bool(whk_data.get('ah', False)),
                meteostation=whk_data.get('meteo', None)
            )
            db.session.add(whk)
            whk_configs.append(whk)
            print(f"✓ {whk.whk_nummer}: {whk.anzahl_abgaenge} Abgänge, {whk.anzahl_temperatursonden} TS")

        db.session.flush()

        # 3. TESTERGEBNISSE
        print("\n### TESTERGEBNISSE IMPORTIEREN ###")
        print("Mapping: A->LSS-CH, B->WH-LTS")
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

        # WHK (keine WHK-Ebene, direkt Fragen)
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

                    lss_ch_res = None
                    wh_lts_res = None

                    if 'A' in auswahl and '0' in auswahl['A']:
                        lss_ch_res = standardize_result(auswahl['A']['0'])
                    if 'B' in auswahl and '0' in auswahl['B']:
                        wh_lts_res = standardize_result(auswahl['B']['0'])

                    if lss_ch_res or wh_lts_res:
                        # Für WHK: komponente_index ist "WHK 01" (erste WHK)
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=test_q.id,
                            komponente_index='WHK 01',
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
                komp_idx = f"WHK {whk_idx + 1:02d}"

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
                komp_idx = f"WHK {whk_idx + 1:02d}"

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

        # Speichern
        db.session.commit()

        print(f"\n✓ Import abgeschlossen: {imported} Testergebnisse")

def verify():
    """Verifiziert den Import"""
    with app.app_context():
        print("\n" + "=" * 80)
        print("VERIFIZIERUNG")
        print("=" * 80)

        projekte = Project.query.all()
        print(f"\nProjekte: {len(projekte)}")
        for p in projekte:
            print(f"  - {p.projektname} ({p.didok_betriebspunkt})")

        whks = WHKConfig.query.all()
        print(f"\nWHK-Konfigurationen: {len(whks)}")
        for w in whks:
            print(f"  - {w.whk_nummer}: {w.anzahl_abgaenge} ABG, {w.anzahl_temperatursonden} TS, MS: {w.meteostation}")

        results = AbnahmeTestResult.query.all()
        print(f"\nTestergebnisse: {len(results)}")

        from sqlalchemy import func
        komponenten = db.session.query(
            TestQuestion.komponente_typ,
            func.count(AbnahmeTestResult.id).label('anzahl')
        ).join(
            AbnahmeTestResult
        ).group_by(TestQuestion.komponente_typ).all()

        print("\nNach Komponententyp:")
        for k, a in komponenten:
            print(f"  {k:20s}: {a:3d}")

if __name__ == '__main__':
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'Alte Projekte', 'Bowil BOW.json'
    )

    print("=" * 80)
    print("BOWIL-PROJEKT IMPORT")
    print("=" * 80)

    delete_all_projects()
    import_projekt(json_path)
    verify()

    print("\n✓ FERTIG!")
