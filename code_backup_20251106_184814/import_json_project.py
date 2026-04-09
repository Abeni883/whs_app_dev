"""
Migrationsskript zum Import eines Projekts aus einer JSON-Datei
aus der früheren Software in die neue Datenbank.

Usage: python import_json_project.py "Pfad/zur/datei.json"
"""

import json
import sys
import io
from datetime import datetime
from app import app, db
from models import Project, WHKConfig, AbnahmeTestResult, TestQuestion

# UTF-8 Ausgabe für Windows-Konsole
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def parse_date(date_string):
    """Konvertiert verschiedene Datumsformate in datetime.date"""
    if not date_string:
        return None

    # Format: "DD.MM.YYYY"
    try:
        return datetime.strptime(date_string, "%d.%m.%Y").date()
    except ValueError:
        pass

    # Format: "YYYY-MM-DD"
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        pass

    print(f"Warnung: Datum '{date_string}' konnte nicht geparst werden")
    return None


def map_result_value(value_str):
    """Mappt alte Ergebnis-Strings auf neue Werte"""
    if not value_str:
        return None

    mapping = {
        "Richtig": "richtig",
        "richtig": "richtig",
        "Falsch": "falsch",
        "falsch": "falsch",
        "Nicht Testbar": "nicht_testbar",
        "nicht_testbar": "nicht_testbar",
        "nicht testbar": "nicht_testbar"
    }

    return mapping.get(value_str, None)


def get_komponente_index_name(komponente_typ, whk_index, whk_config):
    """
    Erzeugt den komponente_index basierend auf dem Typ und WHK-Index

    komponente_typ: 'Anlage', 'WHK', 'Abgang', 'Temperatursonde', 'Antriebsheizung', 'Meteostation'
    whk_index: Index der WHK (0-8)
    whk_config: WHKConfig-Objekt
    """
    if komponente_typ == 'Anlage':
        return "Anlage"
    elif komponente_typ == 'WHK':
        return whk_config.whk_nummer
    elif komponente_typ == 'Abgang':
        return whk_config.whk_nummer
    elif komponente_typ == 'Temperatursonde':
        return whk_config.whk_nummer
    elif komponente_typ == 'Antriebsheizung':
        return whk_config.whk_nummer
    elif komponente_typ == 'Meteostation':
        # Meteostation-Name aus WHK-Config holen
        return whk_config.meteostation if whk_config.meteostation else f"MS {whk_index+1:02d}"

    return f"Komponente {whk_index}"


def get_spalte_name(komponente_typ, spalte_index, whk_config):
    """
    Erzeugt den Spaltennamen basierend auf dem Typ und Spalten-Index

    Spalten-Index in JSON:
    - A: Index 0 (meist LSS-CH/WH-LTS Ergebnisse für erste Komponente)
    - B: Index 1
    - C: Index 2
    usw.
    """
    if komponente_typ == 'Anlage':
        return None  # Anlage hat keine Spalten
    elif komponente_typ == 'WHK':
        return None  # WHK hat keine Spalten
    elif komponente_typ == 'Abgang':
        # Spalten sind die Abgänge: "Abgang 01", "Abgang 02", etc.
        spalte_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6,
                      'G': 7, 'H': 8, 'I': 9, 'J': 10, 'K': 11, 'L': 12}
        abgang_nr = spalte_map.get(spalte_index, 1)
        return f"Abgang {abgang_nr:02d}"
    elif komponente_typ == 'Temperatursonde':
        # Spalten sind die Temperatursonden: "TS 01", "TS 02", etc.
        spalte_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6,
                      'G': 7, 'H': 8, 'I': 9, 'J': 10, 'K': 11, 'L': 12}
        ts_nr = spalte_map.get(spalte_index, 1)
        return f"TS {ts_nr:02d}"
    elif komponente_typ == 'Antriebsheizung':
        return "Antriebsheizung"
    elif komponente_typ == 'Meteostation':
        return None  # Meteostation hat keine Spalten

    return None


def import_projekt(json_file_path, force=False):
    """Importiert ein Projekt aus einer JSON-Datei

    force: Überschreibt bestehendes Projekt ohne Nachfrage
    """

    print(f"\n=== Import von Projekt aus {json_file_path} ===\n")

    # JSON-Datei laden
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"FEHLER beim Laden der JSON-Datei: {e}")
        return False

    # Projektinfo extrahieren
    projektinfo = data.get('projektinfo', {})
    projektname = projektinfo.get('projektname', 'Unbekannt')

    # Prüfen ob Projekt bereits existiert
    existing_project = Project.query.filter_by(
        projektname=projektname,
        didok_betriebspunkt=projektinfo.get('didok', '')
    ).first()

    if existing_project:
        print(f"WARNUNG: Projekt '{projektname}' mit DIDOK '{projektinfo.get('didok')}' existiert bereits!")
        if not force:
            try:
                response = input("Möchten Sie es überschreiben? (j/n): ")
                if response.lower() != 'j':
                    print("Import abgebrochen.")
                    return False
            except EOFError:
                print("Keine interaktive Eingabe möglich. Verwenden Sie --force zum Überschreiben.")
                return False
        else:
            print("--force aktiviert: Überschreibe bestehendes Projekt")

        # Projekt löschen (Cascade delete löscht auch WHK-Configs und Test-Results)
        db.session.delete(existing_project)
        db.session.commit()
        print(f"Bestehendes Projekt gelöscht.\n")

    # 1. Projekt erstellen
    print("1. Erstelle Projekt...")
    projekt = Project(
        energie="EWH",  # Standard, kann angepasst werden
        projektname=projektname,
        didok_betriebspunkt=projektinfo.get('didok', ''),
        baumappenversion=parse_date(projektinfo.get('baumappe')),
        projektleiter_sbb=projektinfo.get('projektleiter', ''),
        pruefer_achermann=projektinfo.get('pruefer', ''),
        pruefdatum=parse_date(projektinfo.get('pruefdatum')),
        bemerkung=projektinfo.get('bemerkungen', '')
    )
    db.session.add(projekt)
    db.session.commit()
    print(f"   ✓ Projekt '{projektname}' erstellt (ID: {projekt.id})")

    # 2. WHK-Konfigurationen erstellen
    print("\n2. Erstelle WHK-Konfigurationen...")
    felder = data.get('felder', [])
    whk_configs = []

    for feld in felder:
        whk_config = WHKConfig(
            projekt_id=projekt.id,
            whk_nummer=feld.get('name', ''),
            anzahl_abgaenge=int(feld.get('abgang', 0)),
            anzahl_temperatursonden=int(feld.get('temp', 0)),
            hat_antriebsheizung=feld.get('ah', False),
            meteostation=feld.get('meteo', '') if feld.get('meteo') else None
        )
        db.session.add(whk_config)
        whk_configs.append(whk_config)

    db.session.commit()
    print(f"   ✓ {len(whk_configs)} WHK-Konfigurationen erstellt")

    # 3. Testergebnisse importieren
    print("\n3. Importiere Testergebnisse...")

    komponente_mapping = {
        'ANLAGE': 'Anlage',
        'WHK': 'WHK',
        'ABG': 'Abgang',
        'TS': 'Temperatursonde',
        'AH': 'Antriebsheizung',
        'MS': 'Meteostation'
    }

    abgaenge_data = data.get('abgaenge', {})
    total_results = 0

    for json_typ, db_typ in komponente_mapping.items():
        if json_typ not in abgaenge_data:
            continue

        print(f"\n   Importiere {db_typ} Daten...")
        typ_data = abgaenge_data[json_typ]
        typ_count = 0

        # Alle Test-Fragen für diesen Komponententyp abrufen
        test_questions = TestQuestion.query.filter_by(
            komponente_typ=db_typ
        ).order_by(TestQuestion.reihenfolge).all()

        if not test_questions:
            print(f"   ⚠ Keine Test-Fragen für {db_typ} gefunden - Überspringe")
            continue

        # Für ANLAGE: keine WHK-Ebene, direkt Fragen
        if db_typ == 'Anlage':
            for frage_index_str, frage_data in typ_data.items():
                # Überspringe nicht-numerische Keys
                if not frage_index_str.isdigit():
                    continue

                frage_index = int(frage_index_str)

                # Prüfe ob Frage-Index gültig ist
                if frage_index >= len(test_questions):
                    continue

                test_question = test_questions[frage_index]
                auswahl = frage_data.get('auswahl', {})
                bemerkungen = frage_data.get('bemerkungen', {})

                # Nimm die erste verfügbare Spalte
                spalten_keys = list(auswahl.keys())
                if not spalten_keys:
                    continue

                erste_spalte = spalten_keys[0]
                spalte_data = auswahl[erste_spalte]

                if not spalte_data or '0' not in spalte_data:
                    continue

                # Index 0 = LSS-CH, Index 1 = WH-LTS (falls vorhanden)
                lss_result = map_result_value(spalte_data.get('0'))
                wh_lts_result = map_result_value(spalte_data.get('1'))

                # Bemerkungen extrahieren
                lss_bemerkung = bemerkungen.get(erste_spalte, {}).get('0', '') if isinstance(bemerkungen.get(erste_spalte), dict) else ''
                wh_lts_bemerkung = bemerkungen.get(erste_spalte, {}).get('1', '') if isinstance(bemerkungen.get(erste_spalte), dict) else ''

                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=test_question.id,
                    komponente_index="Anlage",
                    spalte=None,
                    lss_ch_result=lss_result,
                    wh_lts_result=wh_lts_result,
                    lss_ch_bemerkung=lss_bemerkung if lss_bemerkung else None,
                    wh_lts_bemerkung=wh_lts_bemerkung if wh_lts_bemerkung else None,
                    tester=projekt.pruefer_achermann
                )
                db.session.add(result)
                typ_count += 1

            db.session.commit()
            print(f"   ✓ {typ_count} {db_typ} Ergebnisse importiert")
            total_results += typ_count
            continue

        # Für andere Typen: WHK-Ebene vorhanden
        for whk_index_str, whk_data in typ_data.items():
            # Überspringe nicht-numerische Keys
            if not whk_index_str.isdigit():
                continue

            whk_index = int(whk_index_str)

            # Prüfe ob WHK-Index gültig ist
            if whk_index >= len(whk_configs):
                continue

            whk_config = whk_configs[whk_index]

            # Iteriere über Fragen
            for frage_index_str, frage_data in whk_data.items():
                # Überspringe nicht-numerische Keys
                if not frage_index_str.isdigit():
                    continue

                frage_index = int(frage_index_str)

                # Prüfe ob Frage-Index gültig ist
                if frage_index >= len(test_questions):
                    continue

                test_question = test_questions[frage_index]
                auswahl = frage_data.get('auswahl', {})
                bemerkungen = frage_data.get('bemerkungen', {})

                # Für Anlage und WHK: Nur ein Eintrag ohne Spalten
                if db_typ in ['Anlage', 'WHK', 'Meteostation']:
                    # Nimm die erste verfügbare Spalte (meist 'A', 'B' oder 'C')
                    spalten_keys = list(auswahl.keys())
                    if not spalten_keys:
                        continue

                    erste_spalte = spalten_keys[0]
                    spalte_data = auswahl[erste_spalte]

                    if not spalte_data or '0' not in spalte_data:
                        continue

                    # Index 0 = LSS-CH, Index 1 = WH-LTS
                    lss_result = map_result_value(spalte_data.get('0'))
                    wh_lts_result = map_result_value(spalte_data.get('1'))

                    # Bemerkungen extrahieren (falls vorhanden)
                    lss_bemerkung = bemerkungen.get(erste_spalte, {}).get('0', '') if isinstance(bemerkungen.get(erste_spalte), dict) else ''
                    wh_lts_bemerkung = bemerkungen.get(erste_spalte, {}).get('1', '') if isinstance(bemerkungen.get(erste_spalte), dict) else ''

                    komponente_index = get_komponente_index_name(db_typ, whk_index, whk_config)

                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=test_question.id,
                        komponente_index=komponente_index,
                        spalte=None,
                        lss_ch_result=lss_result,
                        wh_lts_result=wh_lts_result,
                        lss_ch_bemerkung=lss_bemerkung if lss_bemerkung else None,
                        wh_lts_bemerkung=wh_lts_bemerkung if wh_lts_bemerkung else None,
                        tester=projekt.pruefer_achermann
                    )
                    db.session.add(result)
                    typ_count += 1

                # Für Abgang, Temperatursonde, Antriebsheizung: Mehrere Spalten
                else:
                    komponente_index = get_komponente_index_name(db_typ, whk_index, whk_config)

                    # Iteriere über alle Spalten (A, B, C, ...)
                    for spalte_key, spalte_data in auswahl.items():
                        if not spalte_data or '0' not in spalte_data:
                            continue

                        # Prüfe ob diese Spalte für diese WHK relevant ist
                        if db_typ == 'Abgang':
                            spalte_nr = ord(spalte_key) - ord('A') + 1
                            if spalte_nr > whk_config.anzahl_abgaenge:
                                continue
                        elif db_typ == 'Temperatursonde':
                            spalte_nr = ord(spalte_key) - ord('A') + 1
                            if spalte_nr > whk_config.anzahl_temperatursonden:
                                continue
                        elif db_typ == 'Antriebsheizung':
                            if not whk_config.hat_antriebsheizung:
                                continue

                        # Index 0 = LSS-CH, Index 1 = WH-LTS
                        lss_result = map_result_value(spalte_data.get('0'))
                        wh_lts_result = map_result_value(spalte_data.get('1'))

                        # Bemerkungen extrahieren
                        lss_bemerkung = bemerkungen.get(spalte_key, {}).get('0', '') if isinstance(bemerkungen.get(spalte_key), dict) else ''
                        wh_lts_bemerkung = bemerkungen.get(spalte_key, {}).get('1', '') if isinstance(bemerkungen.get(spalte_key), dict) else ''

                        spalte_name = get_spalte_name(db_typ, spalte_key, whk_config)

                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=test_question.id,
                            komponente_index=komponente_index,
                            spalte=spalte_name,
                            lss_ch_result=lss_result,
                            wh_lts_result=wh_lts_result,
                            lss_ch_bemerkung=lss_bemerkung if lss_bemerkung else None,
                            wh_lts_bemerkung=wh_lts_bemerkung if wh_lts_bemerkung else None,
                            tester=projekt.pruefer_achermann
                        )
                        db.session.add(result)
                        typ_count += 1

        db.session.commit()
        print(f"   ✓ {typ_count} {db_typ} Ergebnisse importiert")
        total_results += typ_count

    print(f"\n=== Import abgeschlossen ===")
    print(f"Projekt: {projektname} (ID: {projekt.id})")
    print(f"WHK-Konfigurationen: {len(whk_configs)}")
    print(f"Testergebnisse: {total_results}")
    print(f"\n✓ Erfolgreich importiert!\n")

    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_json_project.py <pfad_zur_json_datei> [--force]")
        print("\nOptionen:")
        print("  --force    Überschreibt bestehendes Projekt ohne Nachfrage")
        print("\nBeispiel:")
        print('  python import_json_project.py "Projekte\\Sargans SA.json"')
        print('  python import_json_project.py "Projekte\\Sargans SA.json" --force')
        sys.exit(1)

    json_file = sys.argv[1]
    force = '--force' in sys.argv

    with app.app_context():
        success = import_projekt(json_file, force=force)
        sys.exit(0 if success else 1)
