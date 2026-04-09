"""
Testdaten-Generator fuer WHS Testprotokoll
Erstellt EWH und GWH Projekte mit verschiedenen Testfortschritten
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from app import app
from models import (db, Project, TestQuestion, AbnahmeTestResult, WHKConfig,
                   ZSKConfig, HGLSConfig, GWHMeteostation, TestResult)


# ==================== TESTFRAGEN DEFINITIONEN ====================

# EWH Testfragen (max 4 pro Komponente)
EWH_TESTFRAGEN = [
    # Anlage (4 Fragen)
    {'komponente_typ': 'Anlage', 'testszenario': 'Identifikation', 'frage_nummer': 1001,
     'frage_text': 'Anlagenname korrekt?', 'test_information': 'Pruefen Sie den Namen der Anlage im System.',
     'erwartetes_ergebnis': 'Name entspricht Projektdokumentation', 'reihenfolge': 1},
    {'komponente_typ': 'Anlage', 'testszenario': 'Kommunikation', 'frage_nummer': 1002,
     'frage_text': 'Kommunikation zur Zentrale aktiv?', 'test_information': 'Status der Verbindung pruefen.',
     'erwartetes_ergebnis': 'Verbindung aktiv, gruene LED', 'reihenfolge': 2},
    {'komponente_typ': 'Anlage', 'testszenario': 'Spannungsversorgung', 'frage_nummer': 1003,
     'frage_text': 'Betriebsspannung im Normbereich?', 'test_information': 'Spannung messen (230V ±10%).',
     'erwartetes_ergebnis': '207V - 253V', 'reihenfolge': 3},
    {'komponente_typ': 'Anlage', 'testszenario': 'Alarme', 'frage_nummer': 1004,
     'frage_text': 'Keine aktiven Stoermeldungen?', 'test_information': 'Alarmuebersicht pruefen.',
     'erwartetes_ergebnis': 'Keine aktiven Alarme', 'reihenfolge': 4},

    # WHK (4 Fragen)
    {'komponente_typ': 'WHK', 'testszenario': 'Identifikation', 'frage_nummer': 2001,
     'frage_text': 'WHK-Bezeichnung korrekt?', 'test_information': 'WHK-Nummer am Schrank und im System vergleichen.',
     'erwartetes_ergebnis': 'Bezeichnung stimmt ueberein', 'reihenfolge': 1},
    {'komponente_typ': 'WHK', 'testszenario': 'Tuerkontakt', 'frage_nummer': 2002,
     'frage_text': 'Tuerkontakt funktioniert?', 'test_information': 'Tuer oeffnen und Signal pruefen.',
     'erwartetes_ergebnis': 'Meldung bei offener Tuer', 'reihenfolge': 2},
    {'komponente_typ': 'WHK', 'testszenario': 'Temperatur', 'frage_nummer': 2003,
     'frage_text': 'Innentemperatur plausibel?', 'test_information': 'Temperaturanzeige mit Handmessgeraet vergleichen.',
     'erwartetes_ergebnis': 'Abweichung < 2°C', 'reihenfolge': 3},
    {'komponente_typ': 'WHK', 'testszenario': 'Heizung', 'frage_nummer': 2004,
     'frage_text': 'Schaltschrankheizung funktioniert?', 'test_information': 'Bei Unterschreitung Sollwert aktivieren.',
     'erwartetes_ergebnis': 'Heizung schaltet ein', 'reihenfolge': 4},

    # Abgang (4 Fragen)
    {'komponente_typ': 'Abgang', 'testszenario': 'Identifikation', 'frage_nummer': 3001,
     'frage_text': 'Abgangsbezeichnung korrekt?', 'test_information': 'Abgangsnummer pruefen.',
     'erwartetes_ergebnis': 'Bezeichnung korrekt', 'reihenfolge': 1},
    {'komponente_typ': 'Abgang', 'testszenario': 'Stromaufnahme', 'frage_nummer': 3002,
     'frage_text': 'Stromaufnahme im Normbereich?', 'test_information': 'Strom bei aktivem Heizelement messen.',
     'erwartetes_ergebnis': 'Strom gemaess Datenblatt', 'reihenfolge': 2},
    {'komponente_typ': 'Abgang', 'testszenario': 'Schaltfunktion', 'frage_nummer': 3003,
     'frage_text': 'Ein-/Ausschaltung funktioniert?', 'test_information': 'Manuelles Schalten testen.',
     'erwartetes_ergebnis': 'Schaltet korrekt', 'reihenfolge': 3},
    {'komponente_typ': 'Abgang', 'testszenario': 'Isolationswiderstand', 'frage_nummer': 3004,
     'frage_text': 'Isolationswiderstand OK?', 'test_information': 'Messung mit Isolationspruefer.',
     'erwartetes_ergebnis': '> 1 MOhm', 'reihenfolge': 4},

    # Temperatursonde (4 Fragen)
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Identifikation', 'frage_nummer': 4001,
     'frage_text': 'Sondenbezeichnung korrekt?', 'test_information': 'Sondennummer pruefen.',
     'erwartetes_ergebnis': 'Bezeichnung stimmt', 'reihenfolge': 1},
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Messwert', 'frage_nummer': 4002,
     'frage_text': 'Temperaturwert plausibel?', 'test_information': 'Mit Referenzthermometer vergleichen.',
     'erwartetes_ergebnis': 'Abweichung < 1°C', 'reihenfolge': 2},
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Kabelfuehrung', 'frage_nummer': 4003,
     'frage_text': 'Kabelfuehrung ordnungsgemaess?', 'test_information': 'Sichtpruefung der Kabelinstallation.',
     'erwartetes_ergebnis': 'Kabel geschuetzt verlegt', 'reihenfolge': 3},
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Grenzwerte', 'frage_nummer': 4004,
     'frage_text': 'Grenzwerte konfiguriert?', 'test_information': 'Ober- und Untergrenze pruefen.',
     'erwartetes_ergebnis': 'Grenzwerte gemaess Spec', 'reihenfolge': 4},

    # Meteostation (4 Fragen)
    {'komponente_typ': 'Meteostation', 'testszenario': 'Identifikation', 'frage_nummer': 5001,
     'frage_text': 'Meteostationsname korrekt?', 'test_information': 'Bezeichnung im System pruefen.',
     'erwartetes_ergebnis': 'Name korrekt', 'reihenfolge': 1},
    {'komponente_typ': 'Meteostation', 'testszenario': 'Niederschlag', 'frage_nummer': 5002,
     'frage_text': 'Niederschlagssensor funktioniert?', 'test_information': 'Sensor mit Wasser testen.',
     'erwartetes_ergebnis': 'Erkennt Niederschlag', 'reihenfolge': 2},
    {'komponente_typ': 'Meteostation', 'testszenario': 'Temperatur', 'frage_nummer': 5003,
     'frage_text': 'Aussentemperatur plausibel?', 'test_information': 'Mit lokalem Thermometer vergleichen.',
     'erwartetes_ergebnis': 'Abweichung < 2°C', 'reihenfolge': 3},
    {'komponente_typ': 'Meteostation', 'testszenario': 'Wind', 'frage_nummer': 5004,
     'frage_text': 'Windsensor funktioniert?', 'test_information': 'Sensor drehen und pruefen.',
     'erwartetes_ergebnis': 'Zeigt Windgeschwindigkeit', 'reihenfolge': 4},

    # Antriebsheizung (4 Fragen)
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Identifikation', 'frage_nummer': 6001,
     'frage_text': 'Antriebsheizung bezeichnet?', 'test_information': 'Bezeichnung pruefen.',
     'erwartetes_ergebnis': 'Bezeichnung korrekt', 'reihenfolge': 1},
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Heizfunktion', 'frage_nummer': 6002,
     'frage_text': 'Heizung funktioniert?', 'test_information': 'Einschalten und Erwaermung pruefen.',
     'erwartetes_ergebnis': 'Erwaermung spuerbar', 'reihenfolge': 2},
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Stromaufnahme', 'frage_nummer': 6003,
     'frage_text': 'Stromaufnahme OK?', 'test_information': 'Stromwert bei Betrieb messen.',
     'erwartetes_ergebnis': 'Im Sollbereich', 'reihenfolge': 3},
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Thermostat', 'frage_nummer': 6004,
     'frage_text': 'Thermostat regelt korrekt?', 'test_information': 'Abschaltung bei Erreichen Sollwert pruefen.',
     'erwartetes_ergebnis': 'Schaltet bei Sollwert ab', 'reihenfolge': 4},
]

# GWH Testfragen (max 4 pro Komponente)
GWH_TESTFRAGEN = [
    # GWH_Anlage (4 Fragen)
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Identifikation', 'frage_nummer': 7001,
     'frage_text': 'GWH-Anlagenname korrekt?', 'test_information': 'Bezeichnung im Leitsystem pruefen.',
     'erwartetes_ergebnis': 'Name entspricht Projekt', 'reihenfolge': 1},
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Gasversorgung', 'frage_nummer': 7002,
     'frage_text': 'Gasdruck im Normbereich?', 'test_information': 'Manometer am Hauptanschluss pruefen.',
     'erwartetes_ergebnis': '20-50 mbar', 'reihenfolge': 2},
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Notabschaltung', 'frage_nummer': 7003,
     'frage_text': 'Not-Aus funktioniert?', 'test_information': 'Not-Aus-Schalter betaetigen.',
     'erwartetes_ergebnis': 'Anlage schaltet ab', 'reihenfolge': 3},
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Alarme', 'frage_nummer': 7004,
     'frage_text': 'Keine Gasalarme aktiv?', 'test_information': 'Alarmliste pruefen.',
     'erwartetes_ergebnis': 'Keine aktiven Gasalarme', 'reihenfolge': 4},

    # GWH_ZSK (4 Fragen)
    {'komponente_typ': 'ZSK', 'testszenario': 'Identifikation', 'frage_nummer': 8001,
     'frage_text': 'ZSK-Bezeichnung korrekt?', 'test_information': 'Nummer am Schrank pruefen.',
     'erwartetes_ergebnis': 'Bezeichnung stimmt', 'reihenfolge': 1},
    {'komponente_typ': 'ZSK', 'testszenario': 'Zuendung', 'frage_nummer': 8002,
     'frage_text': 'Zuendung funktioniert?', 'test_information': 'Zuendvorgang starten und beobachten.',
     'erwartetes_ergebnis': 'Brenner zuendet', 'reihenfolge': 2},
    {'komponente_typ': 'ZSK', 'testszenario': 'Flammenueberwachung', 'frage_nummer': 8003,
     'frage_text': 'Flammenwaechter OK?', 'test_information': 'Flammensignal im System pruefen.',
     'erwartetes_ergebnis': 'Signal vorhanden', 'reihenfolge': 3},
    {'komponente_typ': 'ZSK', 'testszenario': 'Abgastemperatur', 'frage_nummer': 8004,
     'frage_text': 'Abgastemperatur plausibel?', 'test_information': 'Temperatur bei Betrieb messen.',
     'erwartetes_ergebnis': '150-250°C', 'reihenfolge': 4},

    # GWH_HGLS (4 Fragen)
    {'komponente_typ': 'HGLS', 'testszenario': 'Identifikation', 'frage_nummer': 9001,
     'frage_text': 'HGLS-Bezeichnung korrekt?', 'test_information': 'Bezeichnung pruefen.',
     'erwartetes_ergebnis': 'Bezeichnung stimmt', 'reihenfolge': 1},
    {'komponente_typ': 'HGLS', 'testszenario': 'Gasleitung', 'frage_nummer': 9002,
     'frage_text': 'Hauptgasleitung dicht?', 'test_information': 'Leckpruefung durchfuehren.',
     'erwartetes_ergebnis': 'Keine Leckage', 'reihenfolge': 2},
    {'komponente_typ': 'HGLS', 'testszenario': 'Druckregler', 'frage_nummer': 9003,
     'frage_text': 'Druckregler funktioniert?', 'test_information': 'Ausgangsdruck pruefen.',
     'erwartetes_ergebnis': 'Druck stabil', 'reihenfolge': 3},
    {'komponente_typ': 'HGLS', 'testszenario': 'Absperrventil', 'frage_nummer': 9004,
     'frage_text': 'Hauptabsperrventil gaengig?', 'test_information': 'Ventil betaetigen.',
     'erwartetes_ergebnis': 'Ventil schliesst/oeffnet', 'reihenfolge': 4},

    # GWH_Teile (4 Fragen)
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Brenner', 'frage_nummer': 10001,
     'frage_text': 'Brenner sauber?', 'test_information': 'Sichtpruefung Brennerkopf.',
     'erwartetes_ergebnis': 'Keine Verschmutzung', 'reihenfolge': 1},
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Duese', 'frage_nummer': 10002,
     'frage_text': 'Gasduese frei?', 'test_information': 'Duese auf Verstopfung pruefen.',
     'erwartetes_ergebnis': 'Duese frei', 'reihenfolge': 2},
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Zuendelektrode', 'frage_nummer': 10003,
     'frage_text': 'Zuendelektrode OK?', 'test_information': 'Abstand und Zustand pruefen.',
     'erwartetes_ergebnis': 'Elektrode intakt', 'reihenfolge': 3},
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Ionisationselektrode', 'frage_nummer': 10004,
     'frage_text': 'Ionisationselektrode OK?', 'test_information': 'Signal bei Betrieb pruefen.',
     'erwartetes_ergebnis': 'Signal vorhanden', 'reihenfolge': 4},

    # GWH_Temperatursonde (4 Fragen)
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Identifikation', 'frage_nummer': 11001,
     'frage_text': 'GWH-Sonde bezeichnet?', 'test_information': 'Bezeichnung pruefen.',
     'erwartetes_ergebnis': 'Bezeichnung korrekt', 'reihenfolge': 1},
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Messwert', 'frage_nummer': 11002,
     'frage_text': 'Schienentemperatur plausibel?', 'test_information': 'Mit Referenz vergleichen.',
     'erwartetes_ergebnis': 'Abweichung < 2°C', 'reihenfolge': 2},
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Montage', 'frage_nummer': 11003,
     'frage_text': 'Sonde korrekt montiert?', 'test_information': 'Befestigung an Schiene pruefen.',
     'erwartetes_ergebnis': 'Fest montiert', 'reihenfolge': 3},
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Kabel', 'frage_nummer': 11004,
     'frage_text': 'Kabel unbeschaedigt?', 'test_information': 'Sichtpruefung Kabel.',
     'erwartetes_ergebnis': 'Keine Beschaedigung', 'reihenfolge': 4},

    # GWH_Meteostation (4 Fragen)
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Identifikation', 'frage_nummer': 12001,
     'frage_text': 'GWH-Meteostation bezeichnet?', 'test_information': 'Bezeichnung pruefen.',
     'erwartetes_ergebnis': 'Name korrekt', 'reihenfolge': 1},
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Niederschlag', 'frage_nummer': 12002,
     'frage_text': 'Niederschlagserkennung OK?', 'test_information': 'Sensor testen.',
     'erwartetes_ergebnis': 'Erkennt Naesse', 'reihenfolge': 2},
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Kommunikation', 'frage_nummer': 12003,
     'frage_text': 'Datenuebertragung OK?', 'test_information': 'Aktualitaet der Daten pruefen.',
     'erwartetes_ergebnis': 'Daten aktuell', 'reihenfolge': 3},
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Stromversorgung', 'frage_nummer': 12004,
     'frage_text': 'Stromversorgung stabil?', 'test_information': 'Spannung pruefen.',
     'erwartetes_ergebnis': 'Spannung OK', 'reihenfolge': 4},
]


# ==================== TESTPROJEKTE DEFINITIONEN ====================

TESTPROJEKTE = [
    # EWH Projekte
    {'energie': 'EWH', 'projektname': 'EWH Zuerich HB - 100%', 'didok': '8503000',
     'projektleiter': 'Max Muster', 'fortschritt': 100, 'whk_count': 2, 'abgaenge': 4, 'ts': 2},
    {'energie': 'EWH', 'projektname': 'EWH Bern - 60%', 'didok': '8507000',
     'projektleiter': 'Anna Schmidt', 'fortschritt': 60, 'whk_count': 3, 'abgaenge': 6, 'ts': 3},
    {'energie': 'EWH', 'projektname': 'EWH Basel SBB - 30%', 'didok': '8500010',
     'projektleiter': 'Peter Mueller', 'fortschritt': 30, 'whk_count': 2, 'abgaenge': 3, 'ts': 2},
    {'energie': 'EWH', 'projektname': 'EWH Luzern - 0%', 'didok': '8505000',
     'projektleiter': 'Sarah Weber', 'fortschritt': 0, 'whk_count': 1, 'abgaenge': 2, 'ts': 1},

    # GWH Projekte
    {'energie': 'GWH', 'projektname': 'GWH Winterthur - 100%', 'didok': '8506000',
     'projektleiter': 'Thomas Keller', 'fortschritt': 100, 'zsk_count': 2},
    {'energie': 'GWH', 'projektname': 'GWH Olten - 60%', 'didok': '8500218',
     'projektleiter': 'Lisa Meier', 'fortschritt': 60, 'zsk_count': 3},
    {'energie': 'GWH', 'projektname': 'GWH St. Gallen - 30%', 'didok': '8506302',
     'projektleiter': 'Marco Huber', 'fortschritt': 30, 'zsk_count': 2},
    {'energie': 'GWH', 'projektname': 'GWH Thun - 0%', 'didok': '8507100',
     'projektleiter': 'Julia Brunner', 'fortschritt': 0, 'zsk_count': 1},
]


def clear_test_data():
    """Loescht alle bestehenden Testdaten."""
    print("Loesche bestehende Testdaten...")

    # Loesche in korrekter Reihenfolge (Foreign Keys beachten)
    AbnahmeTestResult.query.delete()
    WHKConfig.query.delete()
    ZSKConfig.query.delete()
    HGLSConfig.query.delete()
    GWHMeteostation.query.delete()
    TestQuestion.query.delete()
    TestResult.query.delete()
    Project.query.delete()

    db.session.commit()
    print("[OK] Alle Testdaten geloescht")


def create_test_questions():
    """Erstellt alle Testfragen fuer EWH und GWH."""
    print("\nErstelle Testfragen...")

    all_questions = EWH_TESTFRAGEN + GWH_TESTFRAGEN

    for q in all_questions:
        question = TestQuestion(
            komponente_typ=q['komponente_typ'],
            testszenario=q['testszenario'],
            frage_nummer=q['frage_nummer'],
            frage_text=q['frage_text'],
            test_information=q.get('test_information', ''),
            erwartetes_ergebnis=q.get('erwartetes_ergebnis', ''),
            reihenfolge=q['reihenfolge']
        )
        db.session.add(question)

    db.session.commit()
    print(f"[OK] {len(all_questions)} Testfragen erstellt (EWH: {len(EWH_TESTFRAGEN)}, GWH: {len(GWH_TESTFRAGEN)})")


def create_projects_and_configs():
    """Erstellt Testprojekte mit Konfigurationen."""
    print("\nErstelle Testprojekte...")

    projects = []

    for p in TESTPROJEKTE:
        projekt = Project(
            energie=p['energie'],
            projektname=p['projektname'],
            didok_betriebspunkt=p['didok'],
            projektleiter_sbb=p['projektleiter'],
            pruefer_achermann='Achermann Engineering',
            pruefdatum=date.today(),
            ibn_inbetriebnahme_jahre='2024, 2025',
            bemerkung=f"Testprojekt mit {p['fortschritt']}% Fortschritt"
        )
        db.session.add(projekt)
        db.session.flush()  # Um die ID zu bekommen

        if p['energie'] == 'EWH':
            # WHK Configs erstellen
            for i in range(p['whk_count']):
                whk = WHKConfig(
                    projekt_id=projekt.id,
                    whk_nummer=f"WHK {i+1:02d}",
                    anzahl_abgaenge=p['abgaenge'],
                    anzahl_temperatursonden=p['ts'],
                    hat_antriebsheizung=(i == 0),  # Erste WHK hat Antriebsheizung
                    meteostation=f"MS {i+1:02d}A"
                )
                db.session.add(whk)
        else:
            # GWH Configs erstellen
            # HGLS Config
            hgls = HGLSConfig(
                projekt_id=projekt.id,
                hgls_typ='Fluessiggas',
                hat_fuellventil=True,
                hat_bypassventil=True
            )
            db.session.add(hgls)

            # ZSK Configs
            for i in range(p['zsk_count']):
                zsk = ZSKConfig(
                    projekt_id=projekt.id,
                    zsk_nummer=f"ZSK {i+1:02d}",
                    anzahl_teile=4,
                    hat_temperatursonde=True,
                    reihenfolge=i+1
                )
                db.session.add(zsk)

            # GWH Meteostation
            meteo = GWHMeteostation(
                projekt_id=projekt.id,
                ms_nummer="MS 01",
                name="Meteostation Hauptgleis",
                reihenfolge=1
            )
            db.session.add(meteo)

        projects.append((projekt, p['fortschritt']))

    db.session.commit()
    print(f"[OK] {len(TESTPROJEKTE)} Projekte erstellt")

    return projects


def create_test_results(projects):
    """Erstellt Testergebnisse basierend auf Fortschritt."""
    print("\nErstelle Testergebnisse...")

    for projekt, fortschritt in projects:
        if fortschritt == 0:
            continue  # Keine Ergebnisse fuer 0% Projekte

        if projekt.energie == 'EWH':
            create_ewh_results(projekt, fortschritt)
        else:
            create_gwh_results(projekt, fortschritt)

    db.session.commit()
    print("[OK] Testergebnisse erstellt")


def create_ewh_results(projekt, fortschritt):
    """Erstellt EWH Testergebnisse."""
    # Hole alle EWH-Fragen
    komponenten = ['Anlage', 'WHK', 'Abgang', 'Temperatursonde', 'Meteostation', 'Antriebsheizung']

    for komp in komponenten:
        fragen = TestQuestion.query.filter_by(komponente_typ=komp).all()

        # Bestimme wie viele Fragen beantwortet werden sollen
        anzahl_zu_beantworten = int(len(fragen) * fortschritt / 100)

        for i, frage in enumerate(fragen[:anzahl_zu_beantworten]):
            # Komponenten-Index basierend auf Typ
            if komp == 'Anlage':
                komponente_index = 'Anlage'
                spalte = None
            elif komp == 'WHK':
                for whk in projekt.whk_configs:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=whk.whk_nummer,
                        spalte=None,
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        tester='Test-User'
                    )
                    db.session.add(result)
                continue
            elif komp == 'Abgang':
                for whk in projekt.whk_configs:
                    for j in range(whk.anzahl_abgaenge):
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=whk.whk_nummer,
                            spalte=f"Abgang {j+1:02d}",
                            lss_ch_result='richtig',
                            wh_lts_result='richtig',
                            tester='Test-User'
                        )
                        db.session.add(result)
                continue
            elif komp == 'Temperatursonde':
                for whk in projekt.whk_configs:
                    for j in range(whk.anzahl_temperatursonden):
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=whk.whk_nummer,
                            spalte=f"TS {j+1:02d}",
                            lss_ch_result='richtig',
                            wh_lts_result='richtig',
                            tester='Test-User'
                        )
                        db.session.add(result)
                continue
            elif komp == 'Meteostation':
                meteostations = set(whk.meteostation for whk in projekt.whk_configs if whk.meteostation)
                for ms in meteostations:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=ms,
                        spalte=None,
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        tester='Test-User'
                    )
                    db.session.add(result)
                continue
            elif komp == 'Antriebsheizung':
                for whk in projekt.whk_configs:
                    if whk.hat_antriebsheizung:
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=whk.whk_nummer,
                            spalte='Antriebsheizung',
                            lss_ch_result='richtig',
                            wh_lts_result='richtig',
                            tester='Test-User'
                        )
                        db.session.add(result)
                continue

            # Fuer Anlage
            result = AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=frage.id,
                komponente_index=komponente_index,
                spalte=spalte,
                lss_ch_result='richtig',
                wh_lts_result='richtig',
                tester='Test-User'
            )
            db.session.add(result)


def create_gwh_results(projekt, fortschritt):
    """Erstellt GWH Testergebnisse."""
    komponenten = ['GWH_Anlage', 'ZSK', 'HGLS', 'GWH_Teile', 'GWH_Temperatursonde', 'GWH_Meteostation']

    for komp in komponenten:
        fragen = TestQuestion.query.filter_by(komponente_typ=komp).all()

        # Bestimme wie viele Fragen beantwortet werden sollen
        anzahl_zu_beantworten = int(len(fragen) * fortschritt / 100)

        for frage in fragen[:anzahl_zu_beantworten]:
            if komp == 'GWH_Anlage':
                # GWH_Anlage: komponente_index ist leer, spalte ist 'Anlage'
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=frage.id,
                    komponente_index='',    # Leer wie in Route
                    spalte='Anlage',        # 'Anlage' als Spalte
                    lss_ch_result='richtig',
                    wh_lts_result='richtig',
                    tester='Test-User'
                )
                db.session.add(result)
            elif komp == 'ZSK':
                for zsk in projekt.zsk_configs:
                    # ZSK-Allgemein: komponente_index und spalte sind beide zsk_nummer
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=zsk.zsk_nummer,
                        spalte=zsk.zsk_nummer,  # Multi-Spalten-Format
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        tester='Test-User'
                    )
                    db.session.add(result)
            elif komp == 'HGLS':
                if projekt.hgls_config:
                    # HGLS: komponente_index ist leer, spalte ist 'HGLS'
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index='',  # Leer wie in Route
                        spalte='HGLS',        # 'HGLS' als Spalte
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        tester='Test-User'
                    )
                    db.session.add(result)
            elif komp == 'GWH_Teile':
                for zsk in projekt.zsk_configs:
                    # Für jedes Teil eine separate Zeile erstellen
                    for teil_nr in range(1, (zsk.anzahl_teile or 1) + 1):
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=zsk.zsk_nummer,
                            spalte=f'Teil {str(teil_nr).zfill(2)}',
                            lss_ch_result='richtig',
                            wh_lts_result='richtig',
                            tester='Test-User'
                        )
                        db.session.add(result)
            elif komp == 'GWH_Temperatursonde':
                for zsk in projekt.zsk_configs:
                    if zsk.hat_temperatursonde:  # Nur für ZSKs mit Temperatursonde
                        result = AbnahmeTestResult(
                            projekt_id=projekt.id,
                            test_question_id=frage.id,
                            komponente_index=zsk.zsk_nummer,
                            spalte='TS',  # Route verwendet 'TS' als Spalte
                            lss_ch_result='richtig',
                            wh_lts_result='richtig',
                            tester='Test-User'
                        )
                        db.session.add(result)
            elif komp == 'GWH_Meteostation':
                for ms in projekt.gwh_meteostations:
                    # Meteostation: spalte ist der Name der Meteostation
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=ms.ms_nummer,
                        spalte=ms.name,  # Name der Meteostation als Spalte
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        tester='Test-User'
                    )
                    db.session.add(result)


def main():
    """Hauptfunktion."""
    print("=" * 60)
    print("WHS Testdaten-Generator")
    print("=" * 60)

    with app.app_context():
        # 1. Bestehende Daten loeschen
        clear_test_data()

        # 2. Testfragen erstellen
        create_test_questions()

        # 3. Projekte und Configs erstellen
        projects = create_projects_and_configs()

        # 4. Testergebnisse erstellen
        create_test_results(projects)

        # Zusammenfassung
        print("\n" + "=" * 60)
        print("ZUSAMMENFASSUNG")
        print("=" * 60)
        print(f"Testfragen EWH:  {TestQuestion.query.filter(TestQuestion.komponente_typ.notlike('GWH%')).count()}")
        print(f"Testfragen GWH:  {TestQuestion.query.filter(TestQuestion.komponente_typ.like('GWH%')).count()}")
        print(f"Projekte EWH:    {Project.query.filter_by(energie='EWH').count()}")
        print(f"Projekte GWH:    {Project.query.filter_by(energie='GWH').count()}")
        print(f"Testergebnisse:  {AbnahmeTestResult.query.count()}")
        print("=" * 60)
        print("[OK] Testdaten erfolgreich erstellt!")


if __name__ == '__main__':
    main()
