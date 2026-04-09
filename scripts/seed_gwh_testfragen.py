"""
Seed-Script für GWH-Testfragen

Erstellt initiale Testfragen für alle GWH-Komponententypen.
Kann direkt ausgeführt werden oder über Flask-Shell importiert werden.

Ausführung:
    python scripts/seed_gwh_testfragen.py

    Oder in Flask-Shell:
    from scripts.seed_gwh_testfragen import seed_gwh_testfragen
    seed_gwh_testfragen()
"""

import sys
import os

# Add parent directory to path so we can import app and models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import TestQuestion


def create_gwh_question(komponente_typ, frage_nummer, frage_text, test_information, reihenfolge, preset_antworten=None):
    """Hilfsfunktion zum Erstellen einer GWH-Testfrage mit testszenario."""
    return TestQuestion(
        komponente_typ=komponente_typ,
        testszenario='GWH Abnahmetest',
        frage_nummer=frage_nummer,
        frage_text=frage_text,
        test_information=test_information,
        reihenfolge=reihenfolge,
        preset_antworten=preset_antworten
    )


def seed_gwh_testfragen():
    """Erstellt initiale GWH-Testfragen in der Datenbank."""

    with app.app_context():
        # Prüfe ob bereits GWH-Fragen existieren
        existing_gwh = TestQuestion.query.filter(
            TestQuestion.komponente_typ.in_([
                'GWH_Anlage', 'HGLS', 'ZSK', 'GWH_Teile',
                'GWH_Temperatursonde', 'GWH_Meteostation'
            ])
        ).first()

        if existing_gwh:
            print("[!] GWH-Testfragen existieren bereits!")
            print("    Bitte loeschen Sie existierende GWH-Fragen manuell, falls Sie neu erstellen moechten.")
            return

        print("[*] Erstelle GWH-Testfragen...")

        fragen = []

        # =============================================================================
        # GWH_ANLAGE TESTFRAGEN (1001-1020)
        # =============================================================================
        print("   > GWH_Anlage Fragen...")
        fragen.extend([
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1001,
                frage_text='Name der Anlage',
                test_information='Name gemäss Konfiguration prüfen',
                reihenfolge=1,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1002,
                frage_text='DIDOK Bezeichnung',
                test_information='DIDOK-Betriebspunkt korrekt',
                reihenfolge=2,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1003,
                frage_text='DDC Station',
                test_information='DDC-Stationsnummer prüfen',
                reihenfolge=3,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1004,
                frage_text='Anzahl ZSK (Zündschaltkästen)',
                test_information='Anzahl gemäss Konfiguration',
                reihenfolge=4,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1005,
                frage_text='Anzahl Meteostationen',
                test_information='Anzahl gemäss Konfiguration',
                reihenfolge=5,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1006,
                frage_text='Anlage aktiviert',
                test_information='Anlage im System aktiviert',
                reihenfolge=6,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1007,
                frage_text='Freigabe Ein/Aus',
                test_information='Freigabefunktion prüfen',
                reihenfolge=7,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1008,
                frage_text='Meldung an LSS-CH',
                test_information='Meldungen werden korrekt an LSS-CH übertragen',
                reihenfolge=8,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1009,
                frage_text='Heizbetrieb',
                test_information='Heizbetrieb Ein/Aus funktioniert',
                reihenfolge=9,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1010,
                frage_text='Gasversorgung Typ',
                test_information='Propan oder Erdgas gemäss Konfiguration',
                reihenfolge=10,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1011,
                frage_text='Notbetrieb Konfiguration',
                test_information='Notbetrieb-Parameter konfiguriert',
                reihenfolge=11,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1012,
                frage_text='Link auf Website',
                test_information='Weblink zur Anlagenübersicht funktioniert',
                reihenfolge=12,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='GWH_Anlage',
                testszenario='GWH Abnahmetest',
                frage_nummer=1013,
                frage_text='Betriebszentrale',
                test_information='Zuständige Betriebszentrale korrekt zugeordnet',
                reihenfolge=13,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
        ])

        # =============================================================================
        # HGLS TESTFRAGEN (1021-1040)
        # =============================================================================
        print("   > HGLS Fragen...")
        fragen.extend([
            TestQuestion(
                komponente_typ='HGLS',
                testszenario='GWH Abnahmetest',
                frage_nummer=1021,
                frage_text='HGLS Typ (Propan/Erdgas)',
                test_information='Gastyp gemäss Konfiguration',
                reihenfolge=1,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='HGLS',
                testszenario='GWH Abnahmetest',
                frage_nummer=1022,
                frage_text='Füllventil vorhanden',
                test_information='Füllventil-Komponente konfiguriert',
                reihenfolge=2,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='HGLS',
                testszenario='GWH Abnahmetest',
                frage_nummer=1023,
                frage_text='Bypassventil vorhanden',
                test_information='Bypassventil-Komponente konfiguriert',
                reihenfolge=3,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='HGLS',
                testszenario='GWH Abnahmetest',
                frage_nummer=1024,
                frage_text='Gaswarnanlage vorhanden',
                test_information='Gaswarnanlage konfiguriert und funktionsfähig',
                reihenfolge=4,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='HGLS',
                testszenario='GWH Abnahmetest',
                frage_nummer=1025,
                frage_text='Lüftungsanlage vorhanden',
                test_information='Lüftungsanlage konfiguriert',
                reihenfolge=5,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='HGLS',
                testszenario='GWH Abnahmetest',
                frage_nummer=1026,
                frage_text='Mengenmesser vorhanden',
                test_information='Mengenmesser/Blockade konfiguriert',
                reihenfolge=6,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='HGLS',
                testszenario='GWH Abnahmetest',
                frage_nummer=1027,
                frage_text='Elektroverdampfer vorhanden',
                test_information='Elektroverdampfer konfiguriert',
                reihenfolge=7,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='HGLS',
                testszenario='GWH Abnahmetest',
                frage_nummer=1028,
                frage_text='Gasverdampfer Anzahl',
                test_information='Anzahl Gasverdampfer (0-2) gemäss Konfiguration',
                reihenfolge=8,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='HGLS',
                testszenario='GWH Abnahmetest',
                frage_nummer=1029,
                frage_text='Tankdrucküberwachung',
                test_information='Tankdrucküberwachung konfiguriert und funktionsfähig',
                reihenfolge=9,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='HGLS',
                testszenario='GWH Abnahmetest',
                frage_nummer=1030,
                frage_text='Kathodenschutz vorhanden',
                test_information='Kathodenschutz konfiguriert',
                reihenfolge=10,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
        ])

        # =============================================================================
        # ZSK TESTFRAGEN (1041-1080)
        # =============================================================================
        print("   > ZSK Fragen...")
        fragen.extend([
            # Bereich 1 - Basiskriterien
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1041,
                frage_text='ZSK Spannung 230VAC anlegen',
                test_information='230VAC Versorgungsspannung korrekt angeschlossen',
                reihenfolge=1,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1042,
                frage_text='Spannung 48VAC prüfen',
                test_information='48VAC Hilfsspannung vorhanden und stabil',
                reihenfolge=2,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1043,
                frage_text='Kommunikation zum Leitstand',
                test_information='Datenaustausch zum Leitstand funktioniert',
                reihenfolge=3,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1044,
                frage_text='ZSK sperren/entsperren',
                test_information='Sperrfunktion über Leitstand funktioniert',
                reihenfolge=4,
                preset_antworten=None
            ),

            # Bereich 2 - Betriebswahlschalter
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1045,
                frage_text='Magnetventil AUTO/AUS/EIN',
                test_information='Betriebsarten Magnetventil funktionieren',
                reihenfolge=5,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1046,
                frage_text='Zündtrafo AUTO/AUS/EIN',
                test_information='Betriebsarten Zündtrafo funktionieren',
                reihenfolge=6,
                preset_antworten=None
            ),

            # Bereich 3 - Sensoren
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1047,
                frage_text='Druckgeber Störung',
                test_information='Druckgeber-Störungsmeldung wird erkannt',
                reihenfolge=7,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1048,
                frage_text='Temperatursonde Störung',
                test_information='Temperatursonden-Störung wird erkannt (falls vorhanden)',
                reihenfolge=8,
                preset_antworten=None
            ),

            # Bereich 5/6 - Heizbefehl
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1049,
                frage_text='Einbefehl reguliert heizen',
                test_information='Heizen mit Temperaturregelung funktioniert',
                reihenfolge=9,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1050,
                frage_text='Einbefehl unreguliert heizen',
                test_information='Heizen ohne Temperaturregelung funktioniert',
                reihenfolge=10,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1051,
                frage_text='Drucküberwachung',
                test_information='Gasdrucküberwachung funktioniert korrekt',
                reihenfolge=11,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1052,
                frage_text='Zündung funktioniert',
                test_information='Zündtrafo erzeugt Zündfunken',
                reihenfolge=12,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1053,
                frage_text='Flammenüberwachung',
                test_information='Ionisationskontrolle erkennt Flamme',
                reihenfolge=13,
                preset_antworten=None
            ),

            # Bereich 10 - Prüfbetrieb
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1054,
                frage_text='Prüfbetrieb ein/aus',
                test_information='Prüfbetrieb kann aktiviert/deaktiviert werden',
                reihenfolge=14,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1055,
                frage_text='Prüfbetrieb Heizen',
                test_information='Im Prüfbetrieb wird geheizt',
                reihenfolge=15,
                preset_antworten=None
            ),

            # Bereich 13 - Notbetrieb
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1056,
                frage_text='Notbetrieb aktivieren',
                test_information='Notbetrieb kann aktiviert werden',
                reihenfolge=16,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1057,
                frage_text='Notbetrieb Heizfunktion',
                test_information='Im Notbetrieb funktioniert die Heizung',
                reihenfolge=17,
                preset_antworten=None
            ),

            # Bereich 14 - Kommunikation
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1058,
                frage_text='Datenpunkte Hardware prüfen',
                test_information='Alle Hardware-Datenpunkte korrekt',
                reihenfolge=18,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1059,
                frage_text='Datenpunkte Software prüfen',
                test_information='Alle Software-Datenpunkte korrekt',
                reihenfolge=19,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1060,
                frage_text='Meldungen an LSS-CH',
                test_information='Störungs- und Statusmeldungen werden übertragen',
                reihenfolge=20,
                preset_antworten=None
            ),

            # Zusätzliche wichtige Tests
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1061,
                frage_text='Gasversorgung (zentral/dezentral)',
                test_information='Gasversorgungstyp gemäss Konfiguration',
                reihenfolge=21,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1062,
                frage_text='Kathodenschutz (falls vorhanden)',
                test_information='Kathodenschutz gemäss Konfiguration',
                reihenfolge=22,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='ZSK',
                testszenario='GWH Abnahmetest',
                frage_nummer=1063,
                frage_text='Anzahl Teile/Brennerrohre',
                test_information='Anzahl Teile gemäss Konfiguration (1-12)',
                reihenfolge=23,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
        ])

        # =============================================================================
        # GWH_TEILE TESTFRAGEN (1081-1100)
        # =============================================================================
        print("   > GWH_Teile Fragen...")
        fragen.extend([
            TestQuestion(
                komponente_typ='GWH_Teile',
                testszenario='GWH Abnahmetest',
                frage_nummer=1081,
                frage_text='Teil/Brennerrohr Funktion prüfen',
                test_information='Brennerrohr funktioniert grundsätzlich',
                reihenfolge=1,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Teile',
                testszenario='GWH Abnahmetest',
                frage_nummer=1082,
                frage_text='Teil wird warm nach Heizbefehl',
                test_information='Brennerrohr heizt nach Einbefehl',
                reihenfolge=2,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Teile',
                testszenario='GWH Abnahmetest',
                frage_nummer=1083,
                frage_text='Teil Rückmeldung korrekt',
                test_information='Statusrückmeldung des Teils ist korrekt',
                reihenfolge=3,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Teile',
                testszenario='GWH Abnahmetest',
                frage_nummer=1084,
                frage_text='Brennerrohrstörung simulieren',
                test_information='Störung wird erkannt und gemeldet',
                reihenfolge=4,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Teile',
                testszenario='GWH Abnahmetest',
                frage_nummer=1085,
                frage_text='Flammenüberwachung Teil',
                test_information='Ionisationskontrolle des Teils funktioniert',
                reihenfolge=5,
                preset_antworten=None
            ),
        ])

        # =============================================================================
        # GWH_TEMPERATURSONDE TESTFRAGEN (1101-1120)
        # =============================================================================
        print("   > GWH_Temperatursonde Fragen...")
        fragen.extend([
            TestQuestion(
                komponente_typ='GWH_Temperatursonde',
                testszenario='GWH Abnahmetest',
                frage_nummer=1101,
                frage_text='Temperatursonde erkannt',
                test_information='Temperatursonde wird vom System erkannt',
                reihenfolge=1,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Temperatursonde',
                testszenario='GWH Abnahmetest',
                frage_nummer=1102,
                frage_text='Temperaturwert plausibel',
                test_information='Gemessener Temperaturwert ist plausibel',
                reihenfolge=2,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Temperatursonde',
                testszenario='GWH Abnahmetest',
                frage_nummer=1103,
                frage_text='Temperaturänderung wird erkannt',
                test_information='Änderungen der Temperatur werden erfasst',
                reihenfolge=3,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Temperatursonde',
                testszenario='GWH Abnahmetest',
                frage_nummer=1104,
                frage_text='Störung Kurzschluss',
                test_information='Kurzschluss wird als Störung erkannt',
                reihenfolge=4,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Temperatursonde',
                testszenario='GWH Abnahmetest',
                frage_nummer=1105,
                frage_text='Störung Leitungsbruch',
                test_information='Leitungsbruch wird als Störung erkannt',
                reihenfolge=5,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Temperatursonde',
                testszenario='GWH Abnahmetest',
                frage_nummer=1106,
                frage_text='Temperaturwert in LSS-CH',
                test_information='Temperaturwert wird an LSS-CH übertragen',
                reihenfolge=6,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Temperatursonde',
                testszenario='GWH Abnahmetest',
                frage_nummer=1107,
                frage_text='Regelung funktioniert',
                test_information='Temperaturregelung basierend auf Sondenwert funktioniert',
                reihenfolge=7,
                preset_antworten=None
            ),
        ])

        # =============================================================================
        # GWH_METEOSTATION TESTFRAGEN (1121-1140)
        # =============================================================================
        print("   > GWH_Meteostation Fragen...")
        fragen.extend([
            TestQuestion(
                komponente_typ='GWH_Meteostation',
                testszenario='GWH Abnahmetest',
                frage_nummer=1121,
                frage_text='Meteostation erkannt',
                test_information='Meteostation wird vom System erkannt',
                reihenfolge=1,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Meteostation',
                testszenario='GWH Abnahmetest',
                frage_nummer=1122,
                frage_text='Modbus-Adresse korrekt',
                test_information='Modbus-Adresse gemäss Konfiguration (Standard: 50)',
                reihenfolge=2,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
            TestQuestion(
                komponente_typ='GWH_Meteostation',
                testszenario='GWH Abnahmetest',
                frage_nummer=1123,
                frage_text='Kommunikation funktioniert',
                test_information='Datenaustausch mit Meteostation funktioniert',
                reihenfolge=3,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Meteostation',
                testszenario='GWH Abnahmetest',
                frage_nummer=1124,
                frage_text='Temperaturwert plausibel',
                test_information='Gemessene Aussentemperatur ist plausibel',
                reihenfolge=4,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Meteostation',
                testszenario='GWH Abnahmetest',
                frage_nummer=1125,
                frage_text='Windgeschwindigkeit plausibel',
                test_information='Gemessene Windgeschwindigkeit ist plausibel',
                reihenfolge=5,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Meteostation',
                testszenario='GWH Abnahmetest',
                frage_nummer=1126,
                frage_text='Niederschlag erkannt',
                test_information='Niederschlagssensor funktioniert',
                reihenfolge=6,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Meteostation',
                testszenario='GWH Abnahmetest',
                frage_nummer=1127,
                frage_text='Meteodaten an LSS-CH',
                test_information='Meteodaten werden an LSS-CH übertragen',
                reihenfolge=7,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Meteostation',
                testszenario='GWH Abnahmetest',
                frage_nummer=1128,
                frage_text='Störung wird gemeldet',
                test_information='Kommunikationsstörung wird erkannt und gemeldet',
                reihenfolge=8,
                preset_antworten=None
            ),
            TestQuestion(
                komponente_typ='GWH_Meteostation',
                testszenario='GWH Abnahmetest',
                frage_nummer=1129,
                frage_text='Zuordnung zu ZSK',
                test_information='Meteostation ist richtigem ZSK zugeordnet',
                reihenfolge=9,
                preset_antworten={"lss_ch": "richtig", "wh_lts": "richtig"}
            ),
        ])

        # Fragen in Datenbank einfügen
        db.session.add_all(fragen)
        db.session.commit()

        # Zusammenfassung
        counts = {
            'GWH_Anlage': sum(1 for f in fragen if f.komponente_typ == 'GWH_Anlage'),
            'HGLS': sum(1 for f in fragen if f.komponente_typ == 'HGLS'),
            'ZSK': sum(1 for f in fragen if f.komponente_typ == 'ZSK'),
            'GWH_Teile': sum(1 for f in fragen if f.komponente_typ == 'GWH_Teile'),
            'GWH_Temperatursonde': sum(1 for f in fragen if f.komponente_typ == 'GWH_Temperatursonde'),
            'GWH_Meteostation': sum(1 for f in fragen if f.komponente_typ == 'GWH_Meteostation'),
        }

        print("\n[OK] GWH-Testfragen erfolgreich erstellt!")
        print("\nUebersicht:")
        print(f"   - GWH_Anlage:          {counts['GWH_Anlage']} Fragen")
        print(f"   - HGLS:                {counts['HGLS']} Fragen")
        print(f"   - ZSK:                 {counts['ZSK']} Fragen")
        print(f"   - GWH_Teile:           {counts['GWH_Teile']} Fragen")
        print(f"   - GWH_Temperatursonde: {counts['GWH_Temperatursonde']} Fragen")
        print(f"   - GWH_Meteostation:    {counts['GWH_Meteostation']} Fragen")
        print(f"\n   Gesamt: {len(fragen)} Testfragen")
        print("\n[i] Tipp: Diese Fragen koennen ueber die Testfragen-Verwaltung angepasst werden.")


if __name__ == '__main__':
    seed_gwh_testfragen()
