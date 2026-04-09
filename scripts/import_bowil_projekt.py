"""
Script zum Importieren des Bowil-Projekts aus dem alten JSON-Format

Analysiert und importiert:
- Projektinformationen
- WHK-Konfigurationen
- Testergebnisse (ohne WHK-Spalte wie angefordert)
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

    # Versuche verschiedene Formate
    formats = ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    return None

def analyze_json_structure(json_path):
    """Analysiert die JSON-Struktur"""
    print(f"Analysiere JSON-File: {json_path}")
    print("=" * 80)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("\n### PROJEKTINFO ###")
    if 'projektinfo' in data:
        for key, value in data['projektinfo'].items():
            print(f"  {key}: {value}")

    print("\n### KONFIGURATION ###")
    print(f"  Anzahl WHK: {data.get('anzahl_whk', 0)}")
    if 'felder' in data:
        for i, whk in enumerate(data['felder']):
            print(f"\n  WHK {i+1}:")
            print(f"    Name: {whk.get('name')}")
            print(f"    Abgänge: {whk.get('abgang')}")
            print(f"    Temperatursonden: {whk.get('temp')}")
            print(f"    Antriebsheizung: {whk.get('ah')}")
            print(f"    Meteostation: {whk.get('meteo')}")

    print("\n### TESTERGEBNISSE ###")
    if 'abgaenge' in data:
        for komponente, inhalt in data['abgaenge'].items():
            if komponente == 'WHK':
                print(f"  {komponente}: {len(inhalt)} Einträge -> WIRD IGNORIERT")
            else:
                print(f"  {komponente}: {len(inhalt)} Einträge")

    print("\n" + "=" * 80)
    return data

def delete_all_projects():
    """Löscht alle Projekte aus der Datenbank"""
    with app.app_context():
        count = Project.query.count()
        print(f"\nAktuelle Anzahl Projekte in DB: {count}")

        if count > 0:
            print("Lösche alle Projekte (inkl. WHK-Configs und Testergebnisse durch CASCADE)...")
            Project.query.delete()
            db.session.commit()
            print("✓ Alle Projekte gelöscht!")
        else:
            print("Keine Projekte zum Löschen vorhanden.")

def import_bowil_project(json_path):
    """Importiert das Bowil-Projekt aus dem JSON"""
    print(f"\nImportiere Projekt Bowil aus: {json_path}")
    print("=" * 80)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with app.app_context():
        # 1. PROJEKT ERSTELLEN
        print("\n1. PROJEKT ERSTELLEN")
        projektinfo = data.get('projektinfo', {})

        projekt = Project(
            energie='EWH',  # Standard, kann angepasst werden
            projektname=projektinfo.get('projektname', 'Bowil'),
            didok_betriebspunkt=projektinfo.get('didok', 'BOW'),
            baumappenversion=parse_date(projektinfo.get('baumappe')),
            projektleiter_sbb=projektinfo.get('projektleiter', ''),
            pruefer_achermann=projektinfo.get('pruefer', ''),
            pruefdatum=parse_date(projektinfo.get('pruefdatum')),
            bemerkung=projektinfo.get('bemerkungen', '')
        )

        db.session.add(projekt)
        db.session.flush()  # Um die ID zu erhalten

        print(f"✓ Projekt erstellt: {projekt.projektname} (ID: {projekt.id})")
        print(f"  DIDOK: {projekt.didok_betriebspunkt}")
        print(f"  Projektleiter: {projekt.projektleiter_sbb}")
        print(f"  Prüfer: {projekt.pruefer_achermann}")

        # 2. WHK-KONFIGURATIONEN ERSTELLEN
        print("\n2. WHK-KONFIGURATIONEN ERSTELLEN")
        felder = data.get('felder', [])
        whk_configs = []

        for whk_data in felder:
            whk_config = WHKConfig(
                projekt_id=projekt.id,
                whk_nummer=whk_data.get('name', 'WHK 01'),
                anzahl_abgaenge=int(whk_data.get('abgang', 1)),
                anzahl_temperatursonden=int(whk_data.get('temp', 1)),
                hat_antriebsheizung=bool(whk_data.get('ah', False)),
                meteostation=whk_data.get('meteo', None)
            )

            db.session.add(whk_config)
            whk_configs.append(whk_config)

            print(f"✓ WHK konfiguriert: {whk_config.whk_nummer}")
            print(f"  Abgänge: {whk_config.anzahl_abgaenge}")
            print(f"  Temperatursonden: {whk_config.anzahl_temperatursonden}")
            print(f"  Antriebsheizung: {whk_config.hat_antriebsheizung}")
            print(f"  Meteostation: {whk_config.meteostation}")

        db.session.flush()

        # 3. TESTERGEBNISSE IMPORTIEREN
        print("\n3. TESTERGEBNISSE IMPORTIEREN")
        print("Mapping: A -> LSS-CH, B -> WH-LTS, C -> (zusätzlich)")

        abgaenge_data = data.get('abgaenge', {})
        imported_count = 0

        # Mapping zwischen JSON-Komponententyp und DB-Komponententyp
        komponenten_mapping = {
            'ANLAGE': 'Anlage',
            'ABG': 'Abgang',
            'TS': 'Temperatursonde',
            'MS': 'Meteostation',
            'AH': 'Antriebsheizung',
            'WHK': 'WHK'  # Wird ignoriert
        }

        # Mapping zwischen Spalten und Systemen
        spalten_mapping = {
            'A': 'lss_ch',
            'B': 'wh_lts',
            'C': None  # Wird nicht importiert (optional)
        }

        for json_komponente, db_komponente in komponenten_mapping.items():
            # WHK-Spalte ignorieren wie angefordert
            if json_komponente == 'WHK':
                print(f"\n  Überspringe Komponente: {json_komponente} (wie angefordert)")
                continue

            if json_komponente not in abgaenge_data:
                print(f"\n  Komponente {json_komponente} nicht im JSON vorhanden")
                continue

            komponente_data = abgaenge_data[json_komponente]
            if not komponente_data:
                print(f"\n  Komponente {json_komponente} ist leer")
                continue

            print(f"\n  Verarbeite Komponente: {json_komponente} -> {db_komponente}")

            # Für ANLAGE ist die Struktur anders (keine WHK-Ebene)
            if json_komponente == 'ANLAGE':
                # ANLAGE hat direkt die Fragen ohne WHK-Ebene
                komponente_index = "Anlage"

                # Für jede Frage (Index 0, 1, 2, ...)
                for frage_index_str, frage_data in komponente_data.items():
                    frage_index = int(frage_index_str)
                    reihenfolge = frage_index + 1  # Index + 1 = Reihenfolge

                    # TestQuestion aus DB holen
                    test_question = TestQuestion.query.filter_by(
                        komponente_typ=db_komponente,
                        reihenfolge=reihenfolge
                    ).first()

                    if not test_question:
                        print(f"    ! Warnung: Testfrage nicht gefunden: {db_komponente}, Reih: {reihenfolge}")
                        continue

                    # Auswahlen verarbeiten
                    auswahl = frage_data.get('auswahl', {})

                    # Für ANLAGE: keine Spalte, nur eine Instanz
                    lss_ch_result = None
                    wh_lts_result = None

                    for spalte_key, system in spalten_mapping.items():
                        if spalte_key in auswahl and system:
                            # Nimm den ersten Wert (Index 0)
                            if isinstance(auswahl[spalte_key], dict) and '0' in auswahl[spalte_key]:
                                ergebnis = auswahl[spalte_key]['0']
                            elif isinstance(auswahl[spalte_key], list) and len(auswahl[spalte_key]) > 0:
                                ergebnis = auswahl[spalte_key][0]
                            else:
                                continue

                            # Ergebnis standardisieren
                            if ergebnis == 'Richtig':
                                ergebnis = 'richtig'
                            elif ergebnis == 'Falsch':
                                ergebnis = 'falsch'
                            elif ergebnis == 'Nicht Testbar':
                                ergebnis = 'nicht_testbar'

                            if system == 'lss_ch':
                                lss_ch_result = ergebnis
                            elif system == 'wh_lts':
                                wh_lts_result = ergebnis

                    if lss_ch_result or wh_lts_result:
                        test_result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=test_question.id,
                            komponente_index='Anlage',
                            spalte=None,
                            lss_ch_result=lss_ch_result,
                            wh_lts_result=wh_lts_result,
                            lss_ch_bemerkung=None,
                            wh_lts_bemerkung=None
                        )

                        db.session.add(test_result)
                        imported_count += 1

            else:
                # Für ABG, TS, MS: Mit WHK-Ebene
                # Für jede WHK (Index 0, 1, 2, ...)
                for whk_index_str, whk_data in komponente_data.items():
                    whk_index = int(whk_index_str)
                    komponente_index = f"WHK {whk_index + 1:02d}"

                    # Für jede Frage (Index 0, 1, 2, ...)
                    for frage_index_str, frage_data in whk_data.items():
                        frage_index = int(frage_index_str)
                        reihenfolge = frage_index + 1  # Index + 1 = Reihenfolge

                        # TestQuestion aus DB holen
                        test_question = TestQuestion.query.filter_by(
                            komponente_typ=db_komponente,
                            reihenfolge=reihenfolge
                        ).first()

                        if not test_question:
                            print(f"    ! Warnung: Testfrage nicht gefunden: {db_komponente}, Reih: {reihenfolge}")
                            continue

                        # Auswahlen verarbeiten
                        auswahl = frage_data.get('auswahl', {})

                    # Herausfinden, wie viele Instanzen es gibt (z.B. 2 Abgänge)
                    # Wir nehmen die Anzahl aus dem ersten Spalten-Key
                    anzahl_instanzen = 0
                    for spalte_key in auswahl.keys():
                        if spalte_key in auswahl:
                            anzahl_instanzen = len(auswahl[spalte_key])
                            break

                    # Für ANLAGE, MS, TS: nur eine Spalte (kein Array)
                    # Für ABG: mehrere Spalten (Array mit 0, 1 für Abgang 01, 02)

                    if json_komponente in ['ABG']:
                        # Mehrere Instanzen (z.B. Abgang 01, Abgang 02)
                        for instanz_index in range(anzahl_instanzen):
                            spalte_name = f"Abgang {instanz_index + 1:02d}"

                            # Ergebnisse für diese Instanz sammeln
                            lss_ch_result = None
                            wh_lts_result = None

                            for spalte_key, system in spalten_mapping.items():
                                if spalte_key in auswahl and instanz_index < len(auswahl[spalte_key]):
                                    ergebnis = auswahl[spalte_key][instanz_index]

                                    # Ergebnis standardisieren
                                    if ergebnis == 'Richtig':
                                        ergebnis = 'richtig'
                                    elif ergebnis == 'Falsch':
                                        ergebnis = 'falsch'
                                    elif ergebnis == 'Nicht Testbar':
                                        ergebnis = 'nicht_testbar'

                                    if system == 'lss_ch':
                                        lss_ch_result = ergebnis
                                    elif system == 'wh_lts':
                                        wh_lts_result = ergebnis

                            # AbnahmeTestResult erstellen
                            if lss_ch_result or wh_lts_result:
                                test_result = AbnahmeTestResult(
                                    projekt_id=projekt.id,
                                    test_question_id=test_question.id,
                                    komponente_index=komponente_index,
                                    spalte=spalte_name,
                                    lss_ch_result=lss_ch_result,
                                    wh_lts_result=wh_lts_result,
                                    lss_ch_bemerkung=None,
                                    wh_lts_bemerkung=None
                                )

                                db.session.add(test_result)
                                imported_count += 1

                    elif json_komponente in ['TS']:
                        # Mehrere Temperatursonden
                        for instanz_index in range(anzahl_instanzen):
                            spalte_name = f"TS {instanz_index + 1:02d}"

                            lss_ch_result = None
                            wh_lts_result = None

                            for spalte_key, system in spalten_mapping.items():
                                if spalte_key in auswahl and instanz_index < len(auswahl[spalte_key]):
                                    ergebnis = auswahl[spalte_key][instanz_index]

                                    if ergebnis == 'Richtig':
                                        ergebnis = 'richtig'
                                    elif ergebnis == 'Falsch':
                                        ergebnis = 'falsch'
                                    elif ergebnis == 'Nicht Testbar':
                                        ergebnis = 'nicht_testbar'

                                    if system == 'lss_ch':
                                        lss_ch_result = ergebnis
                                    elif system == 'wh_lts':
                                        wh_lts_result = ergebnis

                            if lss_ch_result or wh_lts_result:
                                test_result = AbnahmeTestResult(
                                    projekt_id=projekt.id,
                                    test_question_id=test_question.id,
                                    komponente_index=komponente_index,
                                    spalte=spalte_name,
                                    lss_ch_result=lss_ch_result,
                                    wh_lts_result=wh_lts_result,
                                    lss_ch_bemerkung=None,
                                    wh_lts_bemerkung=None
                                )

                                db.session.add(test_result)
                                imported_count += 1

                    elif json_komponente in ['ANLAGE', 'MS']:
                        # Nur eine Instanz, aber Ergebnisse in Array mit Index 0
                        spalte_name = None  # Für ANLAGE/MS keine Spalte

                        lss_ch_result = None
                        wh_lts_result = None

                        for spalte_key, system in spalten_mapping.items():
                            if spalte_key in auswahl:
                                # Nimm den ersten Wert (Index 0)
                                if isinstance(auswahl[spalte_key], dict) and '0' in auswahl[spalte_key]:
                                    ergebnis = auswahl[spalte_key]['0']
                                elif isinstance(auswahl[spalte_key], list) and len(auswahl[spalte_key]) > 0:
                                    ergebnis = auswahl[spalte_key][0]
                                else:
                                    continue

                                if ergebnis == 'Richtig':
                                    ergebnis = 'richtig'
                                elif ergebnis == 'Falsch':
                                    ergebnis = 'falsch'
                                elif ergebnis == 'Nicht Testbar':
                                    ergebnis = 'nicht_testbar'

                                if system == 'lss_ch':
                                    lss_ch_result = ergebnis
                                elif system == 'wh_lts':
                                    wh_lts_result = ergebnis

                        if lss_ch_result or wh_lts_result:
                            if json_komponente == 'MS':
                                spalte_name = f"{whk_configs[whk_index].meteostation}"

                            test_result = AbnahmeTestResult(
                                projekt_id=projekt.id,
                                test_question_id=test_question.id,
                                komponente_index=komponente_index if json_komponente != 'ANLAGE' else 'Anlage',
                                spalte=spalte_name,
                                lss_ch_result=lss_ch_result,
                                wh_lts_result=wh_lts_result,
                                lss_ch_bemerkung=None,
                                wh_lts_bemerkung=None
                            )

                            db.session.add(test_result)
                            imported_count += 1

        # Alle Änderungen speichern
        db.session.commit()

        print(f"\n✓ Import abgeschlossen!")
        print(f"  Projekt: {projekt.projektname}")
        print(f"  WHK-Konfigurationen: {len(whk_configs)}")
        print(f"  Testergebnisse: {imported_count}")

def verify_import():
    """Verifiziert den Import"""
    with app.app_context():
        print("\n" + "=" * 80)
        print("VERIFIZIERUNG")
        print("=" * 80)

        # Projekt
        projekte = Project.query.all()
        print(f"\nProjekte in DB: {len(projekte)}")
        for p in projekte:
            print(f"  - {p.projektname} ({p.didok_betriebspunkt})")

        # WHK-Configs
        whk_configs = WHKConfig.query.all()
        print(f"\nWHK-Konfigurationen: {len(whk_configs)}")
        for whk in whk_configs:
            print(f"  - {whk.whk_nummer}: {whk.anzahl_abgaenge} Abgänge, {whk.anzahl_temperatursonden} TS")

        # Testergebnisse
        test_results = AbnahmeTestResult.query.all()
        print(f"\nTestergebnisse: {len(test_results)}")

        # Gruppierung nach Komponententyp
        from sqlalchemy import func
        komponenten = db.session.query(
            TestQuestion.komponente_typ,
            func.count(AbnahmeTestResult.id).label('anzahl')
        ).join(
            AbnahmeTestResult, TestQuestion.id == AbnahmeTestResult.test_question_id
        ).group_by(TestQuestion.komponente_typ).all()

        print("\n  Nach Komponententyp:")
        for komp, anzahl in komponenten:
            print(f"    {komp:20s}: {anzahl:3d} Ergebnisse")

        print("\n✓ Verifizierung abgeschlossen!")

if __name__ == '__main__':
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'Alte Projekte', 'Bowil BOW.json'
    )

    print("Bowil-Projekt Import-Script")
    print("=" * 80)

    # 1. JSON analysieren
    print("\n1. JSON-ANALYSE")
    data = analyze_json_structure(json_path)

    # 2. Alte Projekte löschen
    print("\n\n2. DATENBANK BEREINIGEN")
    print("=" * 80)
    delete_all_projects()

    # 3. Bowil-Projekt importieren
    print("\n\n3. PROJEKT IMPORT")
    print("=" * 80)
    import_bowil_project(json_path)

    # 4. Verifizierung
    verify_import()

    print("\n" + "=" * 80)
    print("✓ FERTIG!")
