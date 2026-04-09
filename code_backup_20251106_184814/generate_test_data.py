"""
Generiert Test-Daten fuer EWH-Anlage mit 3 WHK
Fuellt alle Tests zu 100% aus
"""
# -*- coding: utf-8 -*-

from flask import Flask
from models import db, Project, WHKConfig, TestQuestion, AbnahmeTestResult
from config import Config
from datetime import datetime, date
import random

# Flask App initialisieren
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def generate_test_data():
    """Generiert eine Test-EWH-Anlage mit 3 WHK und füllt alle Tests aus"""

    with app.app_context():
        print("=" * 80)
        print("GENERIERE TEST-DATEN: EWH-Anlage mit 3 WHK")
        print("=" * 80)

        # 1. PROJEKT ERSTELLEN
        print("\n[1/4] Erstelle Test-Projekt...")
        projekt = Project(
            energie='EWH',
            projektname='Test-Anlage Testikon',
            didok_betriebspunkt='8500123',
            baumappenversion=date(2025, 10, 15),
            projektleiter_sbb='Hans Müller',
            pruefer_achermann='Peter Schmidt',
            pruefdatum=date.today(),
            bemerkung='Automatisch generierte Testdaten für PDF/Excel Export'
        )
        db.session.add(projekt)
        db.session.commit()
        print(f"[OK] Projekt erstellt: {projekt.projektname} (ID: {projekt.id})")

        # 2. WHK-KONFIGURATIONEN ERSTELLEN
        print("\n[2/4] Erstelle WHK-Konfigurationen...")

        whk_configs = []

        # WHK 01: 4 Abgänge, 3 Temperatursonden, mit Antriebsheizung, Meteostation MS 01A
        whk1 = WHKConfig(
            projekt_id=projekt.id,
            whk_nummer='WHK 01',
            anzahl_abgaenge=4,
            anzahl_temperatursonden=3,
            hat_antriebsheizung=True,
            meteostation='MS 01A'
        )
        whk_configs.append(whk1)
        db.session.add(whk1)
        print(f"  [OK] WHK 01: 4 Abgaenge, 3 TS, Antriebsheizung, Meteostation MS 01A")

        # WHK 02: 6 Abgänge, 4 Temperatursonden, ohne Antriebsheizung, Meteostation MS 01A
        whk2 = WHKConfig(
            projekt_id=projekt.id,
            whk_nummer='WHK 02',
            anzahl_abgaenge=6,
            anzahl_temperatursonden=4,
            hat_antriebsheizung=False,
            meteostation='MS 01A'
        )
        whk_configs.append(whk2)
        db.session.add(whk2)
        print(f"  [OK] WHK 02: 6 Abgaenge, 4 TS, Meteostation MS 01A")

        # WHK 03: 3 Abgänge, 2 Temperatursonden, mit Antriebsheizung, keine Meteostation
        whk3 = WHKConfig(
            projekt_id=projekt.id,
            whk_nummer='WHK 03',
            anzahl_abgaenge=3,
            anzahl_temperatursonden=2,
            hat_antriebsheizung=True,
            meteostation=None
        )
        whk_configs.append(whk3)
        db.session.add(whk3)
        print(f"  [OK] WHK 03: 3 Abgaenge, 2 TS, Antriebsheizung")

        db.session.commit()
        print(f"[OK] {len(whk_configs)} WHK-Konfigurationen erstellt")

        # 3. ALLE TESTFRAGEN LADEN
        print("\n[3/4] Lade Testfragen...")
        all_questions = TestQuestion.query.order_by(TestQuestion.reihenfolge).all()
        print(f"[OK] {len(all_questions)} Testfragen geladen")

        # 4. TEST-ANTWORTEN GENERIEREN
        print("\n[4/4] Generiere Test-Antworten...")

        # Ergebnis-Optionen gewichtet (mehr "richtig" als "falsch")
        ergebnis_pool = ['richtig'] * 80 + ['falsch'] * 15 + ['nicht_testbar'] * 5

        antworten_count = 0

        for question in all_questions:
            komponente_typ = question.komponente_typ

            # Bestimme relevante WHK-Configs und Spalten basierend auf Komponente
            if komponente_typ == 'Anlage':
                # Anlage: Keine WHK-spezifische Spalte, nur WH-LTS und LSS-CH
                # Speichern ohne Spalte
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=question.id,
                    komponente_index='',  # Leer für Anlage
                    spalte='',  # Keine spezifische Spalte
                    lss_ch_result=random.choice(ergebnis_pool),
                    wh_lts_result=random.choice(ergebnis_pool),
                    lss_ch_bemerkung='',
                    wh_lts_bemerkung=''
                )
                db.session.add(result)
                antworten_count += 1

            elif komponente_typ == 'WHK':
                # WHK: Für jede WHK eine Zeile ohne spezifische Spalte
                for whk_config in whk_configs:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=question.id,
                        komponente_index=whk_config.whk_nummer,
                        spalte='',  # Keine spezifische Spalte
                        lss_ch_result=random.choice(ergebnis_pool),
                        wh_lts_result=random.choice(ergebnis_pool),
                        lss_ch_bemerkung='',
                        wh_lts_bemerkung=''
                    )
                    db.session.add(result)
                    antworten_count += 1

            elif komponente_typ == 'Abgang':
                # Abgang: Für jede WHK und jeden Abgang
                for whk_config in whk_configs:
                    for abgang_num in range(1, whk_config.anzahl_abgaenge + 1):
                        spalte = f"Abgang {abgang_num:02d}"
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=question.id,
                            komponente_index=whk_config.whk_nummer,
                            spalte=spalte,
                            lss_ch_result=random.choice(ergebnis_pool),
                            wh_lts_result=random.choice(ergebnis_pool),
                            lss_ch_bemerkung='',
                            wh_lts_bemerkung=''
                        )
                        db.session.add(result)
                        antworten_count += 1

            elif komponente_typ == 'Temperatursonde':
                # Temperatursonde: Für jede WHK und jede TS
                for whk_config in whk_configs:
                    for ts_num in range(1, whk_config.anzahl_temperatursonden + 1):
                        spalte = f"TS {ts_num:02d}"
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=question.id,
                            komponente_index=whk_config.whk_nummer,
                            spalte=spalte,
                            lss_ch_result=random.choice(ergebnis_pool),
                            wh_lts_result=random.choice(ergebnis_pool),
                            lss_ch_bemerkung='',
                            wh_lts_bemerkung=''
                        )
                        db.session.add(result)
                        antworten_count += 1

            elif komponente_typ == 'Antriebsheizung':
                # Antriebsheizung: Nur für WHK mit Antriebsheizung
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
                            wh_lts_bemerkung=''
                        )
                        db.session.add(result)
                        antworten_count += 1

            elif komponente_typ == 'Meteostation':
                # Meteostation: Gruppiert nach Meteostation-Name
                # Sammle eindeutige Meteostationen
                meteostationen = set()
                for whk_config in whk_configs:
                    if whk_config.meteostation:
                        meteostationen.add(whk_config.meteostation)

                for meteo in meteostationen:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=question.id,
                        komponente_index=meteo,  # z.B. "MS 01A"
                        spalte='',  # Keine spezifische Spalte
                        lss_ch_result=random.choice(ergebnis_pool),
                        wh_lts_result=random.choice(ergebnis_pool),
                        lss_ch_bemerkung='',
                        wh_lts_bemerkung=''
                    )
                    db.session.add(result)
                    antworten_count += 1

        # Commit aller Antworten
        db.session.commit()
        print(f"[OK] {antworten_count} Test-Antworten generiert und gespeichert")

        # ZUSAMMENFASSUNG
        print("\n" + "=" * 80)
        print("ZUSAMMENFASSUNG")
        print("=" * 80)
        print(f"Projekt-ID:          {projekt.id}")
        print(f"Projektname:         {projekt.projektname}")
        print(f"Energie:             {projekt.energie}")
        print(f"WHK-Konfigurationen: {len(whk_configs)}")
        print(f"  - WHK 01:          4 Abgaenge, 3 TS, Antriebsheizung, MS 01A")
        print(f"  - WHK 02:          6 Abgaenge, 4 TS, MS 01A")
        print(f"  - WHK 03:          3 Abgaenge, 2 TS, Antriebsheizung")
        print(f"Testfragen:          {len(all_questions)}")
        print(f"Generierte Antworten: {antworten_count}")
        print("\n[OK] ALLE TESTS ZU 100% AUSGEFUELLT")
        print("\nSie koennen jetzt:")
        print(f"  1. Zur Abnahmetest-Seite navigieren:")
        print(f"     http://localhost:5000/projekt/{projekt.id}/abnahmetest")
        print(f"  2. PDF exportieren:")
        print(f"     http://localhost:5000/projekt/{projekt.id}/export/pdf")
        print(f"  3. Excel exportieren:")
        print(f"     http://localhost:5000/projekt/{projekt.id}/export/excel")
        print("=" * 80)

if __name__ == '__main__':
    generate_test_data()
