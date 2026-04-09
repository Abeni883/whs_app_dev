"""
Script zum Importieren des Granges-Lens Projekts aus dem JSON-Format

Importiert:
- Projektinformationen (inkl. IBN Jahr 2025)
- WHK-Konfigurationen
- Erstellt leere Testergebnisse für alle Testfragen
"""
import sys
import os
import io
import json
from datetime import datetime

# UTF-8 Encoding für Windows-Konsole
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Project, WHKConfig, TestQuestion, AbnahmeTestResult

def parse_date(date_string):
    """Konvertiert Datum-String in verschiedenen Formaten zu datetime.date"""
    if not date_string:
        return None

    formats = ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    return None

def import_granges_lens():
    """Importiert das Granges-Lens Projekt"""
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'Alte Projekte', 'Granmges-Lens GRAL.json'
    )

    print(f"Importiere Projekt aus: {json_path}")
    print("=" * 80)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with app.app_context():
        # Prüfen ob Projekt bereits existiert
        existing = Project.query.filter_by(didok_betriebspunkt='GRAL').first()
        if existing:
            print(f"! Projekt Granges-Lens (GRAL) existiert bereits (ID: {existing.id})")
            print("  Lösche bestehendes Projekt...")
            db.session.delete(existing)
            db.session.commit()
            print("  ✓ Gelöscht")

        # 1. PROJEKT ERSTELLEN
        print("\n1. PROJEKT ERSTELLEN")
        projektinfo = data.get('projektinfo', {})

        # IBN Jahr aus Prüfdatum extrahieren (2025)
        pruefdatum = projektinfo.get('pruefdatum', '')
        ibn_jahr = None
        if pruefdatum:
            try:
                jahr = pruefdatum.split('.')[-1]
                ibn_jahr = jahr
            except:
                pass

        projekt = Project(
            energie='EWH',
            projektname=projektinfo.get('projektname', 'Granges-Lens'),
            didok_betriebspunkt=projektinfo.get('didok', 'GRAL'),
            baumappenversion=parse_date(projektinfo.get('baumappe')),
            projektleiter_sbb=projektinfo.get('projektleiter', ''),
            pruefer_achermann=projektinfo.get('pruefer', ''),
            pruefdatum=parse_date(projektinfo.get('pruefdatum')),
            ibn_inbetriebnahme_jahre=ibn_jahr,  # IBN Jahr 2025
            bemerkung=projektinfo.get('bemerkungen', '')
        )

        db.session.add(projekt)
        db.session.flush()

        print(f"✓ Projekt erstellt: {projekt.projektname} (ID: {projekt.id})")
        print(f"  DIDOK: {projekt.didok_betriebspunkt}")
        print(f"  Projektleiter: {projekt.projektleiter_sbb}")
        print(f"  Prüfer: {projekt.pruefer_achermann}")
        print(f"  IBN Jahr: {projekt.ibn_inbetriebnahme_jahre}")

        # 2. WHK-KONFIGURATIONEN ERSTELLEN
        print("\n2. WHK-KONFIGURATIONEN ERSTELLEN")
        felder = data.get('felder', [])
        whk_configs = []

        for whk_data in felder:
            whk_config = WHKConfig(
                projekt_id=projekt.id,
                whk_nummer=whk_data.get('name', 'WHK 01'),
                anzahl_abgaenge=int(whk_data.get('abgang', 1)),
                anzahl_temperatursonden=int(whk_data.get('temp', 1)),
                hat_antriebsheizung=bool(whk_data.get('ah', False)),
                meteostation=whk_data.get('meteo', None)
            )

            db.session.add(whk_config)
            whk_configs.append(whk_config)

            print(f"✓ WHK konfiguriert: {whk_config.whk_nummer}")
            print(f"  Abgänge: {whk_config.anzahl_abgaenge}")
            print(f"  Temperatursonden: {whk_config.anzahl_temperatursonden}")
            print(f"  Antriebsheizung: {whk_config.hat_antriebsheizung}")
            print(f"  Meteostation: {whk_config.meteostation}")

        db.session.flush()

        # 3. TESTERGEBNISSE ERSTELLEN (alle als "nicht getestet")
        print("\n3. TESTERGEBNISSE ERSTELLEN")

        # Alle Testfragen holen
        test_questions = TestQuestion.query.all()
        created_count = 0

        for frage in test_questions:
            if frage.komponente_typ == "Anlage":
                # Eine Instanz pro Projekt
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=frage.id,
                    komponente_index="Anlage",
                    spalte=None,
                    lss_ch_result=None,
                    wh_lts_result=None
                )
                db.session.add(result)
                created_count += 1

            elif frage.komponente_typ == "WHK":
                # Eine Instanz pro WHK
                for whk in whk_configs:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=whk.whk_nummer,
                        spalte=None,
                        lss_ch_result=None,
                        wh_lts_result=None
                    )
                    db.session.add(result)
                    created_count += 1

            elif frage.komponente_typ == "Abgang":
                # Eine Instanz pro Abgang pro WHK
                for whk in whk_configs:
                    for i in range(1, whk.anzahl_abgaenge + 1):
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=whk.whk_nummer,
                            spalte=f"Abgang {i:02d}",
                            lss_ch_result=None,
                            wh_lts_result=None
                        )
                        db.session.add(result)
                        created_count += 1

            elif frage.komponente_typ == "Temperatursonde":
                # Eine Instanz pro TS pro WHK
                for whk in whk_configs:
                    for i in range(1, whk.anzahl_temperatursonden + 1):
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=whk.whk_nummer,
                            spalte=f"TS {i:02d}",
                            lss_ch_result=None,
                            wh_lts_result=None
                        )
                        db.session.add(result)
                        created_count += 1

            elif frage.komponente_typ == "Antriebsheizung":
                # Eine Instanz pro WHK mit Antriebsheizung
                for whk in whk_configs:
                    if whk.hat_antriebsheizung:
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=whk.whk_nummer,
                            spalte="Antriebsheizung",
                            lss_ch_result=None,
                            wh_lts_result=None
                        )
                        db.session.add(result)
                        created_count += 1

            elif frage.komponente_typ == "Meteostation":
                # Eine Instanz pro einzigartiger Meteostation
                meteostationen = set()
                for whk in whk_configs:
                    if whk.meteostation:
                        meteostationen.add(whk.meteostation)

                for ms_name in meteostationen:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=ms_name,
                        spalte=None,
                        lss_ch_result=None,
                        wh_lts_result=None
                    )
                    db.session.add(result)
                    created_count += 1

        db.session.commit()

        print(f"✓ {created_count} Testergebnis-Einträge erstellt")

        # 4. VERIFIZIERUNG
        print("\n" + "=" * 80)
        print("VERIFIZIERUNG")
        print("=" * 80)

        projekt_check = Project.query.filter_by(didok_betriebspunkt='GRAL').first()
        print(f"\nProjekt: {projekt_check.projektname}")
        print(f"  ID: {projekt_check.id}")
        print(f"  DIDOK: {projekt_check.didok_betriebspunkt}")
        print(f"  IBN Jahr: {projekt_check.ibn_inbetriebnahme_jahre}")

        whk_count = WHKConfig.query.filter_by(projekt_id=projekt_check.id).count()
        print(f"  WHK-Konfigurationen: {whk_count}")

        result_count = AbnahmeTestResult.query.filter_by(projekt_id=projekt_check.id).count()
        print(f"  Testergebnisse: {result_count}")

        print("\n✓ Import abgeschlossen!")

if __name__ == '__main__':
    print("Granges-Lens Projekt Import-Script")
    print("=" * 80)
    import_granges_lens()
    print("\n" + "=" * 80)
    print("✓ FERTIG!")
