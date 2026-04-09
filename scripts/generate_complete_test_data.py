"""
Script zum Generieren von vollständigen Testdaten:
- Testfragen für alle Komponententypen
- Testantworten für alle Projekte (100% Abdeckung)

Usage:
    python scripts/generate_complete_test_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Project, WHKConfig, TestQuestion, AbnahmeTestResult
import random

def create_test_questions():
    """Erstellt Testfragen für alle Komponententypen."""

    print("Erstelle Testfragen...")

    # Prüfe ob bereits Testfragen vorhanden sind
    if TestQuestion.query.count() > 0:
        print(f"  [WARNUNG] Es existieren bereits {TestQuestion.query.count()} Testfragen")
        print("  Loesche alte Testfragen und erstelle neue...")
        TestQuestion.query.delete()
        db.session.commit()
        print("  Alte Testfragen geloescht.")

    questions = []
    frage_nummer = 1

    # 1. ANLAGE-TESTS
    anlage_questions = [
        "Spannung Eingangsspeisung",
        "Gesamtstromaufnahme bei Vollast",
        "Schutzleiterverbindung",
        "Erdungswiderstand",
        "Isolationswiderstand",
    ]

    for idx, text in enumerate(anlage_questions, 1):
        questions.append(TestQuestion(
            komponente_typ='Anlage',
            testszenario='Elektrische Prüfung',
            frage_nummer=frage_nummer,
            frage_text=text,
            test_information=f'Messung: {text}',
            reihenfolge=frage_nummer,
            preset_antworten={'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        ))
        frage_nummer += 1

    # 2. WHK-TESTS
    whk_questions = [
        "Schaltschrank WHK - Sichtprüfung",
        "Verkabelung WHK - Anschlüsse",
        "Sicherungen WHK",
        "Relais-Funktion WHK",
        "Steuerungslogik WHK",
    ]

    for idx, text in enumerate(whk_questions, 1):
        questions.append(TestQuestion(
            komponente_typ='WHK',
            testszenario='WHK-Prüfung',
            frage_nummer=frage_nummer,
            frage_text=text,
            test_information=f'Prüfung: {text}',
            reihenfolge=frage_nummer,
            preset_antworten={'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        ))
        frage_nummer += 1

    # 3. ABGANG-TESTS
    abgang_questions = [
        "Heizleistung Abgang",
        "Isolationswiderstand Abgang",
        "Temperaturmessung Abgang",
        "Schaltzustand Abgang",
    ]

    for idx, text in enumerate(abgang_questions, 1):
        questions.append(TestQuestion(
            komponente_typ='Abgang',
            testszenario='Abgang-Prüfung',
            frage_nummer=frage_nummer,
            frage_text=text,
            test_information=f'Messung: {text}',
            reihenfolge=frage_nummer,
            preset_antworten={'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        ))
        frage_nummer += 1

    # 4. TEMPERATURSONDE-TESTS
    ts_questions = [
        "Temperatursonde - Verkabelung",
        "Temperatursonde - Messwert",
        "Temperatursonde - Kalibrierung",
    ]

    for idx, text in enumerate(ts_questions, 1):
        questions.append(TestQuestion(
            komponente_typ='Temperatursonde',
            testszenario='Temperatursonden-Prüfung',
            frage_nummer=frage_nummer,
            frage_text=text,
            test_information=f'Prüfung: {text}',
            reihenfolge=frage_nummer,
            preset_antworten={'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        ))
        frage_nummer += 1

    # 5. ANTRIEBSHEIZUNG-TESTS
    ah_questions = [
        "Antriebsheizung - Leistung",
        "Antriebsheizung - Temperatur",
        "Antriebsheizung - Isolation",
    ]

    for idx, text in enumerate(ah_questions, 1):
        questions.append(TestQuestion(
            komponente_typ='Antriebsheizung',
            testszenario='Antriebsheizung-Prüfung',
            frage_nummer=frage_nummer,
            frage_text=text,
            test_information=f'Messung: {text}',
            reihenfolge=frage_nummer,
            preset_antworten={'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        ))
        frage_nummer += 1

    # 6. METEOSTATION-TESTS
    meteo_questions = [
        "Meteostation - Kommunikation",
        "Meteostation - Temperatursensor",
        "Meteostation - Datenübertragung",
        "Meteostation - Konfiguration",
    ]

    for idx, text in enumerate(meteo_questions, 1):
        questions.append(TestQuestion(
            komponente_typ='Meteostation',
            testszenario='Meteostation-Prüfung',
            frage_nummer=frage_nummer,
            frage_text=text,
            test_information=f'Prüfung: {text}',
            reihenfolge=frage_nummer,
            preset_antworten={'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        ))
        frage_nummer += 1

    # In Datenbank speichern
    db.session.bulk_save_objects(questions)
    db.session.commit()

    print(f"  [OK] {len(questions)} Testfragen erstellt")
    print(f"     - Anlage: {len(anlage_questions)}")
    print(f"     - WHK: {len(whk_questions)}")
    print(f"     - Abgang: {len(abgang_questions)}")
    print(f"     - Temperatursonde: {len(ts_questions)}")
    print(f"     - Antriebsheizung: {len(ah_questions)}")
    print(f"     - Meteostation: {len(meteo_questions)}")


def create_test_results():
    """Erstellt Testantworten für alle Projekte (100% Abdeckung)."""

    print("\nErstelle Testantworten für alle Projekte...")

    # Prüfe ob bereits Testantworten vorhanden sind
    if AbnahmeTestResult.query.count() > 0:
        print(f"  [WARNUNG] Es existieren bereits {AbnahmeTestResult.query.count()} Testantworten")
        print("  Loesche alte Testantworten und erstelle neue...")
        AbnahmeTestResult.query.delete()
        db.session.commit()
        print("  Alte Testantworten geloescht.")

    projects = Project.query.all()
    test_questions = TestQuestion.query.all()

    results = []
    result_options = ['richtig', 'falsch', 'nicht_testbar']

    for projekt in projects:
        print(f"\n  Projekt {projekt.id}: {projekt.projektname}")

        whk_configs = WHKConfig.query.filter_by(projekt_id=projekt.id).all()

        # 1. ANLAGE-TESTS
        anlage_fragen = [q for q in test_questions if q.komponente_typ == 'Anlage']
        for frage in anlage_fragen:
            result = random.choice(['richtig'] * 8 + ['falsch'] + ['nicht_testbar'])
            results.append(AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=frage.id,
                komponente_index='Anlage',
                spalte='Anlage',
                lss_ch_result=result,
                wh_lts_result=result,
                lss_ch_bemerkung='Test OK' if result == 'richtig' else '',
                wh_lts_bemerkung='Test OK' if result == 'richtig' else '',
                tester='Automatisch generiert'
            ))
        print(f"    [OK] {len(anlage_fragen)} Anlage-Tests")

        # 2. WHK-TESTS
        whk_fragen = [q for q in test_questions if q.komponente_typ == 'WHK']
        for whk_config in whk_configs:
            for frage in whk_fragen:
                result = random.choice(['richtig'] * 8 + ['falsch'] + ['nicht_testbar'])
                results.append(AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=frage.id,
                    komponente_index=whk_config.whk_nummer,
                    spalte=whk_config.whk_nummer,
                    lss_ch_result=result,
                    wh_lts_result=result,
                    lss_ch_bemerkung='Test OK' if result == 'richtig' else '',
                    wh_lts_bemerkung='Test OK' if result == 'richtig' else '',
                    tester='Automatisch generiert'
                ))
            print(f"    [OK] {len(whk_fragen)} Tests fuer {whk_config.whk_nummer}")

            # 3. ABGANG-TESTS
            abgang_fragen = [q for q in test_questions if q.komponente_typ == 'Abgang']
            for abgang_num in range(1, whk_config.anzahl_abgaenge + 1):
                abgang_name = f"Abgang_{abgang_num:02d}"
                for frage in abgang_fragen:
                    result = random.choice(['richtig'] * 8 + ['falsch'] + ['nicht_testbar'])
                    results.append(AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=whk_config.whk_nummer,
                        spalte=abgang_name,
                        lss_ch_result=result,
                        wh_lts_result=result,
                        lss_ch_bemerkung='Test OK' if result == 'richtig' else '',
                        wh_lts_bemerkung='Test OK' if result == 'richtig' else '',
                        tester='Automatisch generiert'
                    ))
            print(f"       - {whk_config.anzahl_abgaenge} Abgänge mit je {len(abgang_fragen)} Tests")

            # 4. TEMPERATURSONDE-TESTS
            ts_fragen = [q for q in test_questions if q.komponente_typ == 'Temperatursonde']
            for ts_num in range(1, whk_config.anzahl_temperatursonden + 1):
                ts_name = f"TS_{ts_num:02d}"
                for frage in ts_fragen:
                    result = random.choice(['richtig'] * 8 + ['falsch'] + ['nicht_testbar'])
                    results.append(AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=whk_config.whk_nummer,
                        spalte=ts_name,
                        lss_ch_result=result,
                        wh_lts_result=result,
                        lss_ch_bemerkung='Messwert OK' if result == 'richtig' else '',
                        wh_lts_bemerkung='Messwert OK' if result == 'richtig' else '',
                        tester='Automatisch generiert'
                    ))
            print(f"       - {whk_config.anzahl_temperatursonden} Temperatursonden mit je {len(ts_fragen)} Tests")

            # 5. ANTRIEBSHEIZUNG-TESTS
            if whk_config.hat_antriebsheizung:
                ah_fragen = [q for q in test_questions if q.komponente_typ == 'Antriebsheizung']
                for frage in ah_fragen:
                    result = random.choice(['richtig'] * 8 + ['falsch'] + ['nicht_testbar'])
                    results.append(AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=whk_config.whk_nummer,
                        spalte='Antriebsheizung',
                        lss_ch_result=result,
                        wh_lts_result=result,
                        lss_ch_bemerkung='Heizung OK' if result == 'richtig' else '',
                        wh_lts_bemerkung='Heizung OK' if result == 'richtig' else '',
                        tester='Automatisch generiert'
                    ))
                print(f"       - Antriebsheizung mit {len(ah_fragen)} Tests")

        # 6. METEOSTATION-TESTS
        meteo_fragen = [q for q in test_questions if q.komponente_typ == 'Meteostation']
        meteostationen = set([whk.meteostation for whk in whk_configs if whk.meteostation])

        for meteostation in meteostationen:
            for frage in meteo_fragen:
                result = random.choice(['richtig'] * 8 + ['falsch'] + ['nicht_testbar'])
                results.append(AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=frage.id,
                    komponente_index=meteostation,
                    spalte=meteostation,
                    lss_ch_result=result,
                    wh_lts_result=result,
                    lss_ch_bemerkung='Kommunikation OK' if result == 'richtig' else '',
                    wh_lts_bemerkung='Kommunikation OK' if result == 'richtig' else '',
                    tester='Automatisch generiert'
                ))
            print(f"    [OK] {len(meteo_fragen)} Tests fuer Meteostation: {meteostation}")

    # In Datenbank speichern
    db.session.bulk_save_objects(results)
    db.session.commit()

    print(f"\n  [OK] {len(results)} Testantworten erstellt")


def main():
    """Hauptfunktion."""
    print("=" * 80)
    print("TESTDATEN-GENERATOR FÜR SBB WEICHENHEIZUNG ABNAHMETEST")
    print("=" * 80)

    with app.app_context():
        # 1. Testfragen erstellen
        create_test_questions()

        # 2. Testantworten erstellen
        create_test_results()

        print("\n" + "=" * 80)
        print("✅ TESTDATEN ERFOLGREICH GENERIERT!")
        print("=" * 80)

        # Statistik
        print("\nDatenbank-Statistik:")
        print(f"  Projekte: {Project.query.count()}")
        print(f"  WHK-Konfigurationen: {WHKConfig.query.count()}")
        print(f"  Testfragen: {TestQuestion.query.count()}")
        print(f"  Testantworten: {AbnahmeTestResult.query.count()}")

        print("\n✅ Export sollte nun vollständige Daten enthalten!")


if __name__ == '__main__':
    main()
