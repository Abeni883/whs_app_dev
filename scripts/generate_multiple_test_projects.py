"""
Generiert mehrere Test-Projekte mit verschiedenen Konfigurationen.

Erstellt:
1. EWH-Projekt mit 2 WHK (klein)
2. EWH-Projekt mit 5 WHK (groß)
3. GWH-Projekt mit 3 WHK (mittel)
4. EWH-Projekt mit 1 WHK (minimal)
5. EWH-Projekt mit 4 WHK (verschiedene Meteostationen)
6. GWH-Projekt mit 2 WHK (ohne Antriebsheizung)

Verschiedene Ausfüllgrade: 0%, 50%, 100%
"""

import sys
import os

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from models import db, Project, WHKConfig, TestQuestion, AbnahmeTestResult
from config import Config
from datetime import datetime, date
import random

# Flask App initialisieren
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def generate_projekt_mit_antworten(projekt, whk_configs, ausfuellgrad=100):
    """
    Generiert Testantworten für ein Projekt.

    Args:
        projekt: Project-Objekt
        whk_configs: Liste von WHKConfig-Objekten
        ausfuellgrad: Prozentsatz der auszufüllenden Tests (0-100)

    Returns:
        Anzahl generierter Antworten
    """
    all_questions = TestQuestion.query.order_by(TestQuestion.reihenfolge).all()

    # Ergebnis-Optionen gewichtet (mehr "richtig" als "falsch")
    ergebnis_pool = ['richtig'] * 70 + ['falsch'] * 20 + ['nicht_testbar'] * 10

    antworten_count = 0

    for question in all_questions:
        # Überspringen basierend auf Ausfüllgrad
        if random.randint(1, 100) > ausfuellgrad:
            continue

        komponente_typ = question.komponente_typ

        if komponente_typ == 'Anlage':
            result = AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=question.id,
                komponente_index='Anlage',
                spalte='Anlage',
                lss_ch_result=random.choice(ergebnis_pool),
                wh_lts_result=random.choice(ergebnis_pool),
                lss_ch_bemerkung='',
                wh_lts_bemerkung='',
                getestet_am=datetime.now(),
                tester=projekt.pruefer_achermann
            )
            db.session.add(result)
            antworten_count += 1

        elif komponente_typ == 'WHK':
            for whk_config in whk_configs:
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=question.id,
                    komponente_index=whk_config.whk_nummer,
                    spalte=whk_config.whk_nummer,
                    lss_ch_result=random.choice(ergebnis_pool),
                    wh_lts_result=random.choice(ergebnis_pool),
                    lss_ch_bemerkung='',
                    wh_lts_bemerkung='',
                    getestet_am=datetime.now(),
                    tester=projekt.pruefer_achermann
                )
                db.session.add(result)
                antworten_count += 1

        elif komponente_typ == 'Abgang':
            for whk_config in whk_configs:
                for abgang_num in range(1, whk_config.anzahl_abgaenge + 1):
                    spalte = f"Abgang_{abgang_num:02d}"
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=question.id,
                        komponente_index=whk_config.whk_nummer,
                        spalte=spalte,
                        lss_ch_result=random.choice(ergebnis_pool),
                        wh_lts_result=random.choice(ergebnis_pool),
                        lss_ch_bemerkung='',
                        wh_lts_bemerkung='',
                        getestet_am=datetime.now(),
                        tester=projekt.pruefer_achermann
                    )
                    db.session.add(result)
                    antworten_count += 1

        elif komponente_typ == 'Temperatursonde':
            for whk_config in whk_configs:
                for ts_num in range(1, whk_config.anzahl_temperatursonden + 1):
                    spalte = f"TS_{ts_num:02d}"
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=question.id,
                        komponente_index=whk_config.whk_nummer,
                        spalte=spalte,
                        lss_ch_result=random.choice(ergebnis_pool),
                        wh_lts_result=random.choice(ergebnis_pool),
                        lss_ch_bemerkung='',
                        wh_lts_bemerkung='',
                        getestet_am=datetime.now(),
                        tester=projekt.pruefer_achermann
                    )
                    db.session.add(result)
                    antworten_count += 1

        elif komponente_typ == 'Antriebsheizung':
            for whk_config in whk_configs:
                if whk_config.hat_antriebsheizung:
                    spalte = 'Antriebsheizung'
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=question.id,
                        komponente_index=whk_config.whk_nummer,
                        spalte=spalte,
                        lss_ch_result=random.choice(ergebnis_pool),
                        wh_lts_result=random.choice(ergebnis_pool),
                        lss_ch_bemerkung='',
                        wh_lts_bemerkung='',
                        getestet_am=datetime.now(),
                        tester=projekt.pruefer_achermann
                    )
                    db.session.add(result)
                    antworten_count += 1

        elif komponente_typ == 'Meteostation':
            meteostationen = set()
            for whk_config in whk_configs:
                if whk_config.meteostation:
                    meteostationen.add(whk_config.meteostation)

            for meteo in meteostationen:
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=question.id,
                    komponente_index=meteo,
                    spalte=meteo,
                    lss_ch_result=random.choice(ergebnis_pool),
                    wh_lts_result=random.choice(ergebnis_pool),
                    lss_ch_bemerkung='',
                    wh_lts_bemerkung='',
                    getestet_am=datetime.now(),
                    tester=projekt.pruefer_achermann
                )
                db.session.add(result)
                antworten_count += 1

    return antworten_count

def generate_multiple_test_projects():
    """Generiert mehrere Test-Projekte mit verschiedenen Konfigurationen"""

    with app.app_context():
        print("=" * 80)
        print("GENERIERE MEHRERE TEST-PROJEKTE MIT VERSCHIEDENEN KONFIGURATIONEN")
        print("=" * 80)

        projekte_config = [
            # 1. EWH Klein (2 WHK, 100% ausgefüllt)
            {
                'energie': 'EWH',
                'projektname': 'EWH Zürich Hauptbahnhof',
                'didok': '8503000',
                'projektleiter': 'Anna Müller',
                'pruefer': 'Thomas Schmidt',
                'whks': [
                    {'nr': 'WHK 01', 'abgaenge': 4, 'ts': 3, 'antrieb': True, 'meteo': 'MS 01A'},
                    {'nr': 'WHK 02', 'abgaenge': 6, 'ts': 4, 'antrieb': False, 'meteo': 'MS 01A'},
                ],
                'ausfuellgrad': 100
            },
            # 2. EWH Groß (5 WHK, 80% ausgefüllt)
            {
                'energie': 'EWH',
                'projektname': 'EWH Bern Bahnhof',
                'didok': '8507000',
                'projektleiter': 'Peter Meier',
                'pruefer': 'Maria Weber',
                'whks': [
                    {'nr': 'WHK 01', 'abgaenge': 3, 'ts': 2, 'antrieb': True, 'meteo': 'MS 01'},
                    {'nr': 'WHK 02', 'abgaenge': 5, 'ts': 3, 'antrieb': True, 'meteo': 'MS 01'},
                    {'nr': 'WHK 03', 'abgaenge': 4, 'ts': 3, 'antrieb': False, 'meteo': 'MS 02'},
                    {'nr': 'WHK 04', 'abgaenge': 6, 'ts': 4, 'antrieb': True, 'meteo': 'MS 02'},
                    {'nr': 'WHK 05', 'abgaenge': 8, 'ts': 5, 'antrieb': True, 'meteo': 'MS 03'},
                ],
                'ausfuellgrad': 80
            },
            # 3. GWH Mittel (3 WHK, 100% ausgefüllt)
            {
                'energie': 'GWH',
                'projektname': 'GWH Luzern Station',
                'didok': '8505000',
                'projektleiter': 'Hans Fischer',
                'pruefer': 'Julia Keller',
                'whks': [
                    {'nr': 'WHK 01', 'abgaenge': 4, 'ts': 3, 'antrieb': True, 'meteo': 'MS 01'},
                    {'nr': 'WHK 02', 'abgaenge': 5, 'ts': 4, 'antrieb': True, 'meteo': 'MS 01'},
                    {'nr': 'WHK 03', 'abgaenge': 3, 'ts': 2, 'antrieb': False, 'meteo': 'MS 02'},
                ],
                'ausfuellgrad': 100
            },
            # 4. EWH Minimal (1 WHK, 50% ausgefüllt)
            {
                'energie': 'EWH',
                'projektname': 'EWH Genève Cornavin',
                'didok': '8501008',
                'projektleiter': 'Sophie Dubois',
                'pruefer': 'Marc Laurent',
                'whks': [
                    {'nr': 'WHK 01', 'abgaenge': 2, 'ts': 1, 'antrieb': False, 'meteo': 'MS 01'},
                ],
                'ausfuellgrad': 50
            },
            # 5. EWH Komplex (4 WHK, verschiedene Meteostationen, 90% ausgefüllt)
            {
                'energie': 'EWH',
                'projektname': 'EWH Basel SBB',
                'didok': '8500010',
                'projektleiter': 'Michael Baumann',
                'pruefer': 'Sandra Huber',
                'whks': [
                    {'nr': 'WHK 01', 'abgaenge': 5, 'ts': 3, 'antrieb': True, 'meteo': 'MS 01A'},
                    {'nr': 'WHK 02', 'abgaenge': 6, 'ts': 4, 'antrieb': True, 'meteo': 'MS 01B'},
                    {'nr': 'WHK 03', 'abgaenge': 4, 'ts': 3, 'antrieb': False, 'meteo': 'MS 02A'},
                    {'nr': 'WHK 04', 'abgaenge': 7, 'ts': 5, 'antrieb': True, 'meteo': 'MS 02B'},
                ],
                'ausfuellgrad': 90
            },
            # 6. GWH Ohne Antriebe (2 WHK, keine Antriebsheizungen, 100% ausgefüllt)
            {
                'energie': 'GWH',
                'projektname': 'GWH Lausanne Gare',
                'didok': '8501120',
                'projektleiter': 'Claude Martin',
                'pruefer': 'Isabelle Renaud',
                'whks': [
                    {'nr': 'WHK 01', 'abgaenge': 3, 'ts': 2, 'antrieb': False, 'meteo': 'MS 01'},
                    {'nr': 'WHK 02', 'abgaenge': 4, 'ts': 3, 'antrieb': False, 'meteo': 'MS 01'},
                ],
                'ausfuellgrad': 100
            },
            # 7. EWH Ohne Meteostationen (3 WHK, 70% ausgefüllt)
            {
                'energie': 'EWH',
                'projektname': 'EWH St. Gallen',
                'didok': '8506302',
                'projektleiter': 'Stefan Graf',
                'pruefer': 'Andreas Brun',
                'whks': [
                    {'nr': 'WHK 01', 'abgaenge': 4, 'ts': 3, 'antrieb': True, 'meteo': None},
                    {'nr': 'WHK 02', 'abgaenge': 5, 'ts': 4, 'antrieb': True, 'meteo': None},
                    {'nr': 'WHK 03', 'abgaenge': 3, 'ts': 2, 'antrieb': False, 'meteo': None},
                ],
                'ausfuellgrad': 70
            },
            # 8. EWH Leer (2 WHK, 0% ausgefüllt - nur Struktur)
            {
                'energie': 'EWH',
                'projektname': 'EWH Winterthur',
                'didok': '8506000',
                'projektleiter': 'Robert Vogel',
                'pruefer': 'Petra Zimmermann',
                'whks': [
                    {'nr': 'WHK 01', 'abgaenge': 3, 'ts': 2, 'antrieb': True, 'meteo': 'MS 01'},
                    {'nr': 'WHK 02', 'abgaenge': 4, 'ts': 3, 'antrieb': False, 'meteo': 'MS 01'},
                ],
                'ausfuellgrad': 0
            },
        ]

        projekt_ids = []

        for i, config in enumerate(projekte_config, 1):
            print(f"\n{'=' * 80}")
            print(f"[{i}/{len(projekte_config)}] Erstelle Projekt: {config['projektname']}")
            print(f"{'=' * 80}")

            # Projekt erstellen
            projekt = Project(
                energie=config['energie'],
                projektname=config['projektname'],
                didok_betriebspunkt=config['didok'],
                baumappenversion=date(2025, 1, 15),
                projektleiter_sbb=config['projektleiter'],
                pruefer_achermann=config['pruefer'],
                pruefdatum=date.today(),
                bemerkung=f"Testprojekt mit {len(config['whks'])} WHK - {config['ausfuellgrad']}% ausgefüllt"
            )
            db.session.add(projekt)
            db.session.commit()

            print(f"[OK] Projekt erstellt (ID: {projekt.id})")
            print(f"     Energie: {projekt.energie}")
            print(f"     DIDOK: {projekt.didok_betriebspunkt}")
            print(f"     Ausfüllgrad: {config['ausfuellgrad']}%")

            # WHK-Konfigurationen erstellen
            whk_objects = []
            for whk_cfg in config['whks']:
                whk = WHKConfig(
                    projekt_id=projekt.id,
                    whk_nummer=whk_cfg['nr'],
                    anzahl_abgaenge=whk_cfg['abgaenge'],
                    anzahl_temperatursonden=whk_cfg['ts'],
                    hat_antriebsheizung=whk_cfg['antrieb'],
                    meteostation=whk_cfg['meteo']
                )
                db.session.add(whk)
                whk_objects.append(whk)

                antrieb_str = "mit Antrieb" if whk_cfg['antrieb'] else "ohne Antrieb"
                meteo_str = f"MS: {whk_cfg['meteo']}" if whk_cfg['meteo'] else "ohne MS"
                print(f"     - {whk_cfg['nr']}: {whk_cfg['abgaenge']} Abgänge, "
                      f"{whk_cfg['ts']} TS, {antrieb_str}, {meteo_str}")

            db.session.commit()

            # Testantworten generieren
            if config['ausfuellgrad'] > 0:
                antworten = generate_projekt_mit_antworten(
                    projekt,
                    whk_objects,
                    config['ausfuellgrad']
                )
                db.session.commit()
                print(f"[OK] {antworten} Testantworten generiert ({config['ausfuellgrad']}% ausgefüllt)")
            else:
                print(f"[INFO] Keine Testantworten generiert (0% Ausfüllgrad)")

            projekt_ids.append(projekt.id)

        # Gesamtzusammenfassung
        print("\n" + "=" * 80)
        print("ZUSAMMENFASSUNG")
        print("=" * 80)
        print(f"\n{len(projekt_ids)} Test-Projekte erfolgreich erstellt:\n")

        for i, (projekt_id, config) in enumerate(zip(projekt_ids, projekte_config), 1):
            whk_count = len(config['whks'])
            print(f"{i}. {config['projektname']}")
            print(f"   ID: {projekt_id} | Typ: {config['energie']} | "
                  f"WHK: {whk_count} | Ausfüllgrad: {config['ausfuellgrad']}%")

        print("\n" + "=" * 80)
        print("\n[ERFOLG] Alle Test-Projekte wurden erfolgreich generiert!")
        print("\nSie können jetzt:")
        print("  1. Zur Projektübersicht navigieren: http://127.0.0.1:8080/projekte")
        print("  2. Zur Export-Seite navigieren: http://127.0.0.1:8080/export")
        print("  3. Einzelne Projekte testen und exportieren")
        print("=" * 80 + "\n")

if __name__ == '__main__':
    generate_multiple_test_projects()
