"""
Analysiert alle Meteostation-Daten in der Datenbank
"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import TestQuestion, AbnahmeTestResult, WHKConfig

with app.app_context():
    print("=" * 80)
    print("METEOSTATION - DETAILLIERTE ANALYSE")
    print("=" * 80)

    # Alle MS-Fragen
    ms_questions = TestQuestion.query.filter_by(
        komponente_typ='Meteostation'
    ).order_by(TestQuestion.reihenfolge).all()

    print(f"\nTotal Fragen: {len(ms_questions)}")

    # WHK-Konfiguration prüfen
    whk = WHKConfig.query.first()
    print(f"Meteostation in WHK-Config: {whk.meteostation if whk else 'KEINE'}")

    print("\n" + "-" * 80)
    print("FRAGE-BY-FRAGE ANALYSE:")
    print("-" * 80)

    fehlende_fragen = []

    for q in ms_questions:
        results = AbnahmeTestResult.query.filter_by(
            test_question_id=q.id
        ).all()

        print(f"\nFrage {q.reihenfolge:2d}: {q.frage_text[:60]}")

        if results:
            print(f"  Ergebnisse: {len(results)}")
            for r in results:
                lss = r.lss_ch_result if r.lss_ch_result else "None"
                wh = r.wh_lts_result if r.wh_lts_result else "None"
                print(f"    {r.komponente_index} / {r.spalte}")
                print(f"      LSS-CH: {lss:15s} | WH-LTS: {wh}")
        else:
            print("  ⚠ KEINE ERGEBNISSE!")
            fehlende_fragen.append(q.reihenfolge)

    print("\n" + "=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)

    if fehlende_fragen:
        print(f"\n⚠ FEHLENDE FRAGEN: {fehlende_fragen}")
        print(f"  Anzahl: {len(fehlende_fragen)} von {len(ms_questions)}")
    else:
        print("\n✓ Alle Fragen haben Ergebnisse")

    # Prüfe ob es mehrere MS gibt oder nur eine
    all_ms_results = AbnahmeTestResult.query.join(TestQuestion).filter(
        TestQuestion.komponente_typ == 'Meteostation'
    ).all()

    print(f"\nTotal Ergebnisse: {len(all_ms_results)}")

    # Eindeutige Spalten
    spalten = set()
    for r in all_ms_results:
        if r.spalte:
            spalten.add(r.spalte)

    print(f"Eindeutige Spalten: {spalten}")
