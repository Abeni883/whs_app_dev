"""
Script zur Verifizierung der importierten Testfragen
"""
import sys
import os
import io

# UTF-8 Encoding für Windows-Konsole
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import TestQuestion
from sqlalchemy import func

def verify_testfragen():
    """Überprüft die importierten Testfragen"""
    with app.app_context():
        print("Verifizierung der importierten Testfragen")
        print("=" * 80)

        # Gesamtanzahl
        total = TestQuestion.query.count()
        print(f"\nGesamtanzahl Testfragen: {total}")

        # Gruppierung nach Komponententyp
        print("\n--- Verteilung nach Komponententyp ---")
        komponenten = db.session.query(
            TestQuestion.komponente_typ,
            func.count(TestQuestion.id).label('anzahl')
        ).group_by(TestQuestion.komponente_typ).all()

        for komp, anzahl in komponenten:
            print(f"  {komp:20s}: {anzahl:3d} Fragen")

        # Beispiele pro Komponententyp
        print("\n--- Beispiele pro Komponententyp ---")
        for komp, _ in komponenten:
            print(f"\n{komp}:")
            beispiele = TestQuestion.query.filter_by(
                komponente_typ=komp
            ).order_by(TestQuestion.reihenfolge).limit(3).all()

            for frage in beispiele:
                print(f"  [{frage.frage_nummer:3d}] Reih: {frage.reihenfolge:2d} - {frage.frage_text[:60]}")
                if frage.preset_antworten:
                    print(f"       Presets: {frage.preset_antworten}")

        # Überprüfung auf fehlende Pflichtfelder
        print("\n--- Qualitätsprüfung ---")
        missing_testszenario = TestQuestion.query.filter(
            (TestQuestion.testszenario == None) | (TestQuestion.testszenario == '')
        ).count()
        missing_komponente = TestQuestion.query.filter(
            (TestQuestion.komponente_typ == None) | (TestQuestion.komponente_typ == '')
        ).count()

        print(f"  Fragen ohne Testszenario: {missing_testszenario}")
        print(f"  Fragen ohne Komponententyp: {missing_komponente}")

        # Presets-Statistik
        with_presets = TestQuestion.query.filter(
            TestQuestion.preset_antworten != None
        ).count()
        print(f"  Fragen mit Preset-Antworten: {with_presets} von {total}")

        print("\n" + "=" * 80)
        print("✓ Verifizierung abgeschlossen!")

if __name__ == '__main__':
    verify_testfragen()
