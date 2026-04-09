"""
Analysiert den GESE-Import und prüft fehlende Daten
"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import Project, WHKConfig, TestQuestion, AbnahmeTestResult

with app.app_context():
    # Projekt GESE holen
    projekt = Project.query.filter_by(didok_betriebspunkt='GESE').first()

    if not projekt:
        print("⚠ GESE Projekt nicht gefunden!")
        sys.exit(1)

    print("=" * 80)
    print(f"GESE-PROJEKT ANALYSE (ID: {projekt.id})")
    print("=" * 80)

    # WHK-Konfigurationen
    whks = WHKConfig.query.filter_by(projekt_id=projekt.id).order_by(WHKConfig.whk_nummer).all()
    print(f"\nWHK-Konfigurationen: {len(whks)}")
    for w in whks:
        ms_info = f", MS: {w.meteostation}" if w.meteostation else ""
        print(f"  {w.whk_nummer}: {w.anzahl_abgaenge} ABG, {w.anzahl_temperatursonden} TS{ms_info}")

    # WHK-Komponente Ergebnisse
    print("\n" + "=" * 80)
    print("WHK-KOMPONENTE ERGEBNISSE")
    print("=" * 80)

    whk_questions = TestQuestion.query.filter_by(komponente_typ='WHK').order_by(TestQuestion.reihenfolge).all()
    print(f"\nTotal WHK-Fragen in DB: {len(whk_questions)}")

    whk_results = db.session.query(AbnahmeTestResult).join(TestQuestion).filter(
        AbnahmeTestResult.projekt_id == projekt.id,
        TestQuestion.komponente_typ == 'WHK'
    ).all()

    print(f"Total WHK-Ergebnisse: {len(whk_results)}")

    # Gruppiere nach komponente_index
    from collections import defaultdict
    whk_by_index = defaultdict(list)
    for r in whk_results:
        whk_by_index[r.komponente_index].append(r)

    print(f"\nErgebnisse nach WHK:")
    for idx, results in sorted(whk_by_index.items()):
        print(f"  {idx}: {len(results)} Ergebnisse")

    # Prüfe welche WHKs fehlen
    expected_whks = [w.whk_nummer for w in whks]
    found_whks = list(whk_by_index.keys())
    missing_whks = [w for w in expected_whks if w not in found_whks]

    if missing_whks:
        print(f"\n⚠ FEHLENDE WHK-ERGEBNISSE: {missing_whks}")

    # Abgang-Ergebnisse pro WHK
    print("\n" + "=" * 80)
    print("ABGANG-ERGEBNISSE PRO WHK")
    print("=" * 80)

    abgang_results = db.session.query(AbnahmeTestResult).join(TestQuestion).filter(
        AbnahmeTestResult.projekt_id == projekt.id,
        TestQuestion.komponente_typ == 'Abgang'
    ).all()

    abg_by_whk = defaultdict(int)
    for r in abgang_results:
        abg_by_whk[r.komponente_index] += 1

    print(f"\nTotal Abgang-Ergebnisse: {len(abgang_results)}")
    for whk_idx in sorted(abg_by_whk.keys()):
        print(f"  {whk_idx}: {abg_by_whk[whk_idx]} Ergebnisse")

    # Erwartete Anzahl berechnen
    abgang_questions = TestQuestion.query.filter_by(komponente_typ='Abgang').all()
    print(f"\nAnzahl Abgang-Fragen in DB: {len(abgang_questions)}")

    for w in whks:
        expected = len(abgang_questions) * w.anzahl_abgaenge
        actual = abg_by_whk.get(w.whk_nummer, 0)
        status = "✓" if actual == expected else "⚠"
        print(f"  {status} {w.whk_nummer}: Erwartet {expected}, Aktuell {actual}")
