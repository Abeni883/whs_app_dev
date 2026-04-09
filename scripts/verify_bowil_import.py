"""
Detaillierte Verifizierung des Bowil-Projekt-Imports
"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Project, WHKConfig, TestQuestion, AbnahmeTestResult
from sqlalchemy import func

with app.app_context():
    print("=" * 80)
    print("DETAILLIERTE VERIFIZIERUNG: BOWIL-PROJEKT")
    print("=" * 80)

    # Projekt
    projekt = Project.query.first()
    if projekt:
        print(f"\n### PROJEKT ###")
        print(f"Name: {projekt.projektname}")
        print(f"DIDOK: {projekt.didok_betriebspunkt}")
        print(f"Projektleiter: {projekt.projektleiter_sbb}")
        print(f"Prüfer: {projekt.pruefer_achermann}")
        print(f"Prüfdatum: {projekt.pruefdatum}")
        print(f"Baumappenversion: {projekt.baumappenversion}")

    # WHK-Konfigurationen
    whks = WHKConfig.query.all()
    print(f"\n### WHK-KONFIGURATIONEN ({len(whks)}) ###")
    for whk in whks:
        print(f"{whk.whk_nummer}:")
        print(f"  - Abgänge: {whk.anzahl_abgaenge}")
        print(f"  - Temperatursonden: {whk.anzahl_temperatursonden}")
        print(f"  - Antriebsheizung: {whk.hat_antriebsheizung}")
        print(f"  - Meteostation: {whk.meteostation}")

    # Testergebnisse Summary
    print(f"\n### TESTERGEBNISSE ÜBERSICHT ###")
    total = AbnahmeTestResult.query.count()
    print(f"Total: {total}")

    # Nach Komponententyp
    komp_stats = db.session.query(
        TestQuestion.komponente_typ,
        func.count(AbnahmeTestResult.id).label('anzahl')
    ).join(AbnahmeTestResult).group_by(TestQuestion.komponente_typ).all()

    print("\nNach Komponententyp:")
    for komp, anzahl in komp_stats:
        print(f"  {komp:20s}: {anzahl:3d}")

    # Beispiele pro Komponententyp
    print(f"\n### BEISPIELE PRO KOMPONENTENTYP ###")

    # Anlage
    anlage_results = AbnahmeTestResult.query.join(
        TestQuestion
    ).filter(
        TestQuestion.komponente_typ == 'Anlage'
    ).limit(3).all()

    print("\nAnlage (erste 3):")
    for r in anlage_results:
        print(f"  Frage {r.test_question.reihenfolge}: {r.test_question.frage_text[:40]}...")
        print(f"    LSS-CH: {r.lss_ch_result}, WH-LTS: {r.wh_lts_result}")

    # Abgänge
    abgang_results = AbnahmeTestResult.query.join(
        TestQuestion
    ).filter(
        TestQuestion.komponente_typ == 'Abgang'
    ).limit(6).all()

    print("\nAbgang (erste 6):")
    for r in abgang_results:
        print(f"  {r.komponente_index} / {r.spalte} - Frage {r.test_question.reihenfolge}")
        print(f"    {r.test_question.frage_text[:40]}...")
        print(f"    LSS-CH: {r.lss_ch_result}, WH-LTS: {r.wh_lts_result}")

    # Temperatursonden
    ts_results = AbnahmeTestResult.query.join(
        TestQuestion
    ).filter(
        TestQuestion.komponente_typ == 'Temperatursonde'
    ).all()

    print(f"\nTemperatursonde (alle {len(ts_results)}):")
    for r in ts_results:
        print(f"  {r.komponente_index} / {r.spalte} - Frage {r.test_question.reihenfolge}")
        print(f"    {r.test_question.frage_text[:40]}...")
        print(f"    LSS-CH: {r.lss_ch_result}, WH-LTS: {r.wh_lts_result}")

    # Meteostation
    ms_results = AbnahmeTestResult.query.join(
        TestQuestion
    ).filter(
        TestQuestion.komponente_typ == 'Meteostation'
    ).limit(5).all()

    print(f"\nMeteostation (erste 5):")
    for r in ms_results:
        print(f"  {r.komponente_index} / {r.spalte} - Frage {r.test_question.reihenfolge}")
        print(f"    {r.test_question.frage_text[:40]}...")
        print(f"    LSS-CH: {r.lss_ch_result}, WH-LTS: {r.wh_lts_result}")

    # Statistik: Richtig/Falsch/Nicht Testbar
    print(f"\n### ERGEBNISSTATISTIK ###")

    # LSS-CH
    lss_ch_stats = db.session.query(
        AbnahmeTestResult.lss_ch_result,
        func.count(AbnahmeTestResult.id)
    ).group_by(AbnahmeTestResult.lss_ch_result).all()

    print("\nLSS-CH:")
    for ergebnis, anzahl in lss_ch_stats:
        print(f"  {ergebnis if ergebnis else 'None':15s}: {anzahl:3d}")

    # WH-LTS
    wh_lts_stats = db.session.query(
        AbnahmeTestResult.wh_lts_result,
        func.count(AbnahmeTestResult.id)
    ).group_by(AbnahmeTestResult.wh_lts_result).all()

    print("\nWH-LTS:")
    for ergebnis, anzahl in wh_lts_stats:
        print(f"  {ergebnis if ergebnis else 'None':15s}: {anzahl:3d}")

    print("\n" + "=" * 80)
    print("✓ VERIFIZIERUNG ABGESCHLOSSEN")
