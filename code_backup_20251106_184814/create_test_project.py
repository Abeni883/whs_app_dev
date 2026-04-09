"""
Erstellt ein vollständiges Test-Projekt mit 3 WHK und allen Tests abgeschlossen
"""

from app import app, db
from models import Project, WHKConfig, TestQuestion, AbnahmeTestResult
from datetime import datetime, date

def create_test_project():
    with app.app_context():
        # 1. Projekt erstellen
        print("=" * 60)
        print("ERSTELLE TEST-PROJEKT")
        print("=" * 60)

        projekt = Project(
            energie='EWH',
            projektname='Test-Projekt Bahnhof Musterstadt',
            didok_betriebspunkt='8500999',
            baumappenversion=date(2025, 1, 15),
            projektleiter_sbb='Max Mustermann',
            pruefer_achermann='Hans Tester',
            pruefdatum=date.today(),
            bemerkung='Vollständiges Test-Projekt mit 3 WHK - alle Tests abgeschlossen'
        )
        db.session.add(projekt)
        db.session.commit()

        print(f"[OK] Projekt erstellt: {projekt.projektname} (ID: {projekt.id})")

        # 2. WHK-Konfigurationen erstellen
        print("\n" + "-" * 60)
        print("ERSTELLE WHK-KONFIGURATIONEN")
        print("-" * 60)

        whk_configs = [
            {
                'whk_nummer': 'WHK 01',
                'anzahl_abgaenge': 4,
                'anzahl_temperatursonden': 3,
                'hat_antriebsheizung': True,
                'meteostation': 'MS 01'
            },
            {
                'whk_nummer': 'WHK 02',
                'anzahl_abgaenge': 6,
                'anzahl_temperatursonden': 4,
                'hat_antriebsheizung': False,
                'meteostation': 'MS 01'
            },
            {
                'whk_nummer': 'WHK 03',
                'anzahl_abgaenge': 3,
                'anzahl_temperatursonden': 2,
                'hat_antriebsheizung': True,
                'meteostation': 'MS 02'
            }
        ]

        whk_objects = []
        for config in whk_configs:
            whk = WHKConfig(
                projekt_id=projekt.id,
                whk_nummer=config['whk_nummer'],
                anzahl_abgaenge=config['anzahl_abgaenge'],
                anzahl_temperatursonden=config['anzahl_temperatursonden'],
                hat_antriebsheizung=config['hat_antriebsheizung'],
                meteostation=config['meteostation']
            )
            db.session.add(whk)
            whk_objects.append(whk)
            print(f"[OK] {config['whk_nummer']}: {config['anzahl_abgaenge']} Abgaenge, "
                  f"{config['anzahl_temperatursonden']} TS, "
                  f"Antrieb: {config['hat_antriebsheizung']}, "
                  f"MS: {config['meteostation']}")

        db.session.commit()

        # 3. Alle Testfragen laden
        print("\n" + "-" * 60)
        print("LADE TESTFRAGEN")
        print("-" * 60)

        test_questions = TestQuestion.query.order_by(
            TestQuestion.komponente_typ,
            TestQuestion.reihenfolge
        ).all()

        print(f"[OK] {len(test_questions)} Testfragen gefunden")

        # 4. Test-Ergebnisse erstellen
        print("\n" + "-" * 60)
        print("ERSTELLE TEST-ERGEBNISSE (100% ABGESCHLOSSEN)")
        print("-" * 60)

        results_count = 0

        for frage in test_questions:
            if frage.komponente_typ == "Anlage":
                # Anlage-Tests: Eine Spalte "Anlage"
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=frage.id,
                    komponente_index='Anlage',
                    spalte='Anlage',
                    lss_ch_result='richtig',
                    wh_lts_result='richtig',
                    getestet_am=datetime.now(),
                    tester='Hans Tester'
                )
                db.session.add(result)
                results_count += 1

            elif frage.komponente_typ == "WHK":
                # WHK-Tests: Für jeden WHK
                for whk in whk_objects:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=whk.whk_nummer,
                        spalte=whk.whk_nummer,
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        getestet_am=datetime.now(),
                        tester='Hans Tester'
                    )
                    db.session.add(result)
                    results_count += 1

            elif frage.komponente_typ == "Abgang":
                # Abgang-Tests: Für jeden Abgang in jedem WHK
                for whk in whk_objects:
                    for abgang_nr in range(1, whk.anzahl_abgaenge + 1):
                        spalte = f"Abgang {abgang_nr:02d}"
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=whk.whk_nummer,
                            spalte=spalte,
                            lss_ch_result='richtig',
                            wh_lts_result='richtig',
                            getestet_am=datetime.now(),
                            tester='Hans Tester'
                        )
                        db.session.add(result)
                        results_count += 1

            elif frage.komponente_typ == "Temperatursonde":
                # TS-Tests: Für jede TS in jedem WHK
                for whk in whk_objects:
                    for ts_nr in range(1, whk.anzahl_temperatursonden + 1):
                        spalte = f"TS {ts_nr:02d}"
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=whk.whk_nummer,
                            spalte=spalte,
                            lss_ch_result='richtig',
                            wh_lts_result='richtig',
                            getestet_am=datetime.now(),
                            tester='Hans Tester'
                        )
                        db.session.add(result)
                        results_count += 1

            elif frage.komponente_typ == "Antriebsheizung":
                # Antriebsheizung-Tests: Nur für WHK mit Antriebsheizung
                for whk in whk_objects:
                    if whk.hat_antriebsheizung:
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=whk.whk_nummer,
                            spalte='Antriebsheizung',
                            lss_ch_result='richtig',
                            wh_lts_result='richtig',
                            getestet_am=datetime.now(),
                            tester='Hans Tester'
                        )
                        db.session.add(result)
                        results_count += 1

            elif frage.komponente_typ == "Meteostation":
                # Meteostation-Tests: Für jede eindeutige MS
                meteostationen = list(set([whk.meteostation for whk in whk_objects if whk.meteostation]))
                for ms_name in meteostationen:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=ms_name,
                        spalte=ms_name,
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        getestet_am=datetime.now(),
                        tester='Hans Tester'
                    )
                    db.session.add(result)
                    results_count += 1

        db.session.commit()

        print(f"[OK] {results_count} Test-Ergebnisse erstellt (alle RICHTIG)")

        # 5. Zusammenfassung
        print("\n" + "=" * 60)
        print("ZUSAMMENFASSUNG")
        print("=" * 60)
        print(f"Projekt:           {projekt.projektname}")
        print(f"Projekt-ID:        {projekt.id}")
        print(f"DIDOK:             {projekt.didok_betriebspunkt}")
        print(f"Energie-Typ:       {projekt.energie}")
        print(f"")
        print(f"WHK-Anzahl:        {len(whk_objects)}")
        print(f"  - WHK 01:        4 Abgaenge, 3 TS, mit Antrieb, MS 01")
        print(f"  - WHK 02:        6 Abgaenge, 4 TS, ohne Antrieb, MS 01")
        print(f"  - WHK 03:        3 Abgaenge, 2 TS, mit Antrieb, MS 02")
        print(f"")
        print(f"Testfragen:        {len(test_questions)}")
        print(f"Test-Ergebnisse:   {results_count}")
        print(f"Abschlussgrad:     100% (alle Tests RICHTIG)")
        print(f"")
        print(f"Prüfer:            {projekt.pruefer_achermann}")
        print(f"Prüfdatum:         {projekt.pruefdatum}")
        print("=" * 60)
        print("")
        print("[ERFOLG] TEST-PROJEKT ERFOLGREICH ERSTELLT!")
        print("")
        print(f"Oeffne die Anwendung und gehe zu:")
        print(f"  -> http://127.0.0.1:8080/projekte")
        print(f"  -> Projekt-ID: {projekt.id}")
        print(f"  -> Abnahmetest: http://127.0.0.1:8080/projekt/abnahmetest/{projekt.id}")
        print("=" * 60)

if __name__ == '__main__':
    create_test_project()
