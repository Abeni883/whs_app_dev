"""Verifiziert den Import eines Projekts"""

from app import app, db
from models import Project, WHKConfig, AbnahmeTestResult
from collections import Counter

with app.app_context():
    projekt = Project.query.filter_by(projektname='Sargans').first()

    if not projekt:
        print("Projekt 'Sargans' nicht gefunden!")
        exit(1)

    print(f"\n=== Projekt Details ===")
    print(f"Projekt: {projekt.projektname}")
    print(f"DIDOK: {projekt.didok_betriebspunkt}")
    print(f"Energie: {projekt.energie}")
    print(f"Projektleiter: {projekt.projektleiter_sbb}")
    print(f"Pruefer: {projekt.pruefer_achermann}")
    print(f"Pruefdatum: {projekt.pruefdatum}")
    print(f"Baumappe: {projekt.baumappenversion}")
    print(f"Bemerkung: {projekt.bemerkung[:100]}..." if len(projekt.bemerkung or '') > 100 else f"Bemerkung: {projekt.bemerkung}")

    print(f"\n=== WHK-Konfigurationen ({len(projekt.whk_configs)}) ===")
    for whk in sorted(projekt.whk_configs, key=lambda x: x.whk_nummer):
        print(f"  - {whk.whk_nummer}: {whk.anzahl_abgaenge} Abgaenge, {whk.anzahl_temperatursonden} TS, AH={whk.hat_antriebsheizung}, MS={whk.meteostation or 'Keine'}")

    print(f"\n=== Testergebnisse ({len(projekt.abnahme_results)}) ===")
    typen = Counter([r.test_question.komponente_typ for r in projekt.abnahme_results])
    print("Nach Komponententyp:")
    for typ, count in sorted(typen.items()):
        print(f"  - {typ}: {count}")

    # Ergebnis-Statistik
    lss_results = Counter([r.lss_ch_result for r in projekt.abnahme_results if r.lss_ch_result])
    wh_lts_results = Counter([r.wh_lts_result for r in projekt.abnahme_results if r.wh_lts_result])

    print(f"\n=== LSS-CH Ergebnisse ===")
    for result, count in sorted(lss_results.items()):
        print(f"  - {result}: {count}")

    print(f"\n=== WH-LTS Ergebnisse ===")
    for result, count in sorted(wh_lts_results.items()):
        print(f"  - {result}: {count}")

    # Beispiel: Erste 5 Abgang-Ergebnisse
    print(f"\n=== Beispiel: Erste 5 Abgang-Ergebnisse ===")
    abgang_results = [r for r in projekt.abnahme_results if r.test_question.komponente_typ == 'Abgang'][:5]
    for r in abgang_results:
        print(f"  - {r.komponente_index} / {r.spalte}: LSS-CH={r.lss_ch_result}, WH-LTS={r.wh_lts_result}")

    print("\n✓ Verifikation abgeschlossen!\n")
