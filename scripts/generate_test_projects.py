#!/usr/bin/env python
"""
Generiert Testprojekte mit vollständigen Testergebnissen.

Erstellt:
- 2 Projekte (EWH und GWH)
- WHK-Konfigurationen mit allen Komponenten
- 100% beantwortete Tests mit Richtig/Falsch/Nicht testbar

Ausführen mit:
    python scripts/generate_test_projects.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import Project, WHKConfig, TestQuestion, AbnahmeTestResult
from datetime import datetime, date
import random

def generate_test_data():
    with app.app_context():
        # 1. Alle Projekte löschen (CASCADE löscht auch WHKConfigs und AbnahmeTestResults)
        print('=== LOESCHE ALLE PROJEKTE ===')
        deleted = Project.query.delete()
        db.session.commit()
        print(f'Geloescht: {deleted} Projekte')

        # 2. Testprojekte anlegen
        print('\n=== ERSTELLE TESTPROJEKTE ===')

        # Projekt 1: EWH mit 2 WHKs
        projekt1 = Project(
            energie='EWH',
            projektname='Testanlage Muster',
            didok_betriebspunkt='TM',
            baumappenversion=date(2024, 6, 15),
            projektleiter_sbb='Max Mustermann',
            pruefer_achermann='Anna Beispiel',
            pruefdatum=date(2024, 11, 20),
            ibn_inbetriebnahme_jahre='2024, 2025',
            bemerkung='Testprojekt 1 fuer Entwicklung'
        )
        db.session.add(projekt1)
        db.session.flush()
        print(f'Projekt 1 erstellt: {projekt1.projektname} (ID: {projekt1.id})')

        # WHK-Konfigurationen für Projekt 1
        whk1_1 = WHKConfig(
            projekt_id=projekt1.id,
            whk_nummer='WHK 01',
            anzahl_abgaenge=3,
            anzahl_temperatursonden=2,
            hat_antriebsheizung=True,
            meteostation='MS 01A'
        )
        whk1_2 = WHKConfig(
            projekt_id=projekt1.id,
            whk_nummer='WHK 02',
            anzahl_abgaenge=2,
            anzahl_temperatursonden=1,
            hat_antriebsheizung=False,
            meteostation='MS 01A'  # Gleiche Meteostation
        )
        db.session.add_all([whk1_1, whk1_2])
        print(f'  - WHK 01: 3 Abgaenge, 2 TS, Antriebsheizung, MS 01A')
        print(f'  - WHK 02: 2 Abgaenge, 1 TS, keine AH, MS 01A')

        # Projekt 2: GWH mit 1 WHK
        projekt2 = Project(
            energie='GWH',
            projektname='Bahnhof Beispiel',
            didok_betriebspunkt='BB',
            baumappenversion=date(2024, 8, 1),
            projektleiter_sbb='Peter Schmidt',
            pruefer_achermann='Lisa Mueller',
            pruefdatum=date(2024, 12, 1),
            ibn_inbetriebnahme_jahre='2025',
            bemerkung='Testprojekt 2 fuer Entwicklung'
        )
        db.session.add(projekt2)
        db.session.flush()
        print(f'Projekt 2 erstellt: {projekt2.projektname} (ID: {projekt2.id})')

        # WHK-Konfiguration für Projekt 2
        whk2_1 = WHKConfig(
            projekt_id=projekt2.id,
            whk_nummer='WHK 01',
            anzahl_abgaenge=2,
            anzahl_temperatursonden=2,
            hat_antriebsheizung=True,
            meteostation='MS 02B'
        )
        db.session.add(whk2_1)
        print(f'  - WHK 01: 2 Abgaenge, 2 TS, Antriebsheizung, MS 02B')

        db.session.commit()

        # 3. Testfragen laden
        print('\n=== ERSTELLE TESTERGEBNISSE ===')
        test_questions = TestQuestion.query.all()

        # Ergebnis-Verteilung: 70% richtig, 20% falsch, 10% nicht_testbar
        def get_random_result():
            r = random.random()
            if r < 0.7:
                return 'richtig'
            elif r < 0.9:
                return 'falsch'
            else:
                return 'nicht_testbar'

        results_count = 0

        for projekt in [projekt1, projekt2]:
            whk_configs = WHKConfig.query.filter_by(projekt_id=projekt.id).all()

            for frage in test_questions:
                komponente_typ = frage.komponente_typ

                if komponente_typ == 'Anlage':
                    # Anlage-Test
                    # WICHTIG: spalte muss "Anlage" sein (wie Frontend sendet)
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index='Anlage',
                        spalte='Anlage',
                        lss_ch_result=get_random_result(),
                        wh_lts_result=get_random_result(),
                        lss_ch_bemerkung='',
                        wh_lts_bemerkung='',
                        tester='Test-User'
                    )
                    db.session.add(result)
                    results_count += 1

                elif komponente_typ == 'WHK':
                    # WHK-Tests für jede WHK
                    # WICHTIG: komponente_index und spalte mit Leerzeichen (wie Frontend sendet)
                    for whk in whk_configs:
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=whk.whk_nummer,  # Mit Leerzeichen: "WHK 01"
                            spalte=whk.whk_nummer,  # Mit Leerzeichen: "WHK 01"
                            lss_ch_result=get_random_result(),
                            wh_lts_result=get_random_result(),
                            tester='Test-User'
                        )
                        db.session.add(result)
                        results_count += 1

                elif komponente_typ == 'Abgang':
                    # Abgang-Tests für jeden Abgang jeder WHK
                    # WICHTIG: Mit Leerzeichen speichern (wie Frontend erwartet)
                    for whk in whk_configs:
                        for abgang_num in range(1, whk.anzahl_abgaenge + 1):
                            abgang_name = f'Abgang {abgang_num:02d}'  # Mit Leerzeichen
                            result = AbnahmeTestResult(
                                projekt_id=projekt.id,
                                test_question_id=frage.id,
                                komponente_index=whk.whk_nummer,  # Mit Leerzeichen
                                spalte=abgang_name,
                                lss_ch_result=get_random_result(),
                                wh_lts_result=get_random_result(),
                                tester='Test-User'
                            )
                            db.session.add(result)
                            results_count += 1

                elif komponente_typ == 'Temperatursonde':
                    # TS-Tests für jede Temperatursonde jeder WHK
                    # WICHTIG: Mit Leerzeichen speichern (wie Frontend erwartet)
                    for whk in whk_configs:
                        for ts_num in range(1, whk.anzahl_temperatursonden + 1):
                            ts_name = f'TS {ts_num:02d}'  # Mit Leerzeichen
                            result = AbnahmeTestResult(
                                projekt_id=projekt.id,
                                test_question_id=frage.id,
                                komponente_index=whk.whk_nummer,  # Mit Leerzeichen
                                spalte=ts_name,
                                lss_ch_result=get_random_result(),
                                wh_lts_result=get_random_result(),
                                tester='Test-User'
                            )
                            db.session.add(result)
                            results_count += 1

                elif komponente_typ == 'Antriebsheizung':
                    # AH-Tests nur für WHKs mit Antriebsheizung
                    for whk in whk_configs:
                        if whk.hat_antriebsheizung:
                            result = AbnahmeTestResult(
                                projekt_id=projekt.id,
                                test_question_id=frage.id,
                                komponente_index=whk.whk_nummer,  # Mit Leerzeichen
                                spalte='Antriebsheizung',
                                lss_ch_result=get_random_result(),
                                wh_lts_result=get_random_result(),
                                tester='Test-User'
                            )
                            db.session.add(result)
                            results_count += 1

                elif komponente_typ == 'Meteostation':
                    # MS-Tests für jede eindeutige Meteostation
                    # WICHTIG: Mit Leerzeichen speichern (wie Frontend erwartet)
                    meteostationen = set()
                    for whk in whk_configs:
                        if whk.meteostation:
                            meteostationen.add(whk.meteostation)

                    for ms_name in meteostationen:
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=ms_name,  # Mit Leerzeichen
                            spalte=ms_name,  # Mit Leerzeichen
                            lss_ch_result=get_random_result(),
                            wh_lts_result=get_random_result(),
                            tester='Test-User'
                        )
                        db.session.add(result)
                        results_count += 1

        db.session.commit()
        print(f'Erstellt: {results_count} Testergebnisse')

        # 4. Statistik
        print('\n=== STATISTIK ===')
        all_results = AbnahmeTestResult.query.all()

        lss_richtig = sum(1 for r in all_results if r.lss_ch_result == 'richtig')
        lss_falsch = sum(1 for r in all_results if r.lss_ch_result == 'falsch')
        lss_nt = sum(1 for r in all_results if r.lss_ch_result == 'nicht_testbar')

        wh_richtig = sum(1 for r in all_results if r.wh_lts_result == 'richtig')
        wh_falsch = sum(1 for r in all_results if r.wh_lts_result == 'falsch')
        wh_nt = sum(1 for r in all_results if r.wh_lts_result == 'nicht_testbar')

        print(f'Gesamt Ergebnisse: {len(all_results)}')
        print(f'\nLSS-CH:')
        print(f'  Richtig: {lss_richtig}')
        print(f'  Falsch: {lss_falsch}')
        print(f'  Nicht testbar: {lss_nt}')
        print(f'\nWH-LTS:')
        print(f'  Richtig: {wh_richtig}')
        print(f'  Falsch: {wh_falsch}')
        print(f'  Nicht testbar: {wh_nt}')

        print('\n=== FERTIG ===')
        print(f'\nProjekt 1: {projekt1.projektname} ({projekt1.energie})')
        print(f'  - 2 WHKs, 5 Abgaenge total, 3 TS total, 1 AH, 1 MS')
        print(f'\nProjekt 2: {projekt2.projektname} ({projekt2.energie})')
        print(f'  - 1 WHK, 2 Abgaenge, 2 TS, 1 AH, 1 MS')


if __name__ == '__main__':
    generate_test_data()
