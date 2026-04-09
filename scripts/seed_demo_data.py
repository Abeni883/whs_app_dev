"""
Demo-Daten Seed-Script fuer WHS Testprotokoll
Erstellt neue Testfragen und 4 kleine Testprojekte mit 100% Ergebnissen
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from app import app
from models import (db, Project, TestQuestion, AbnahmeTestResult, WHKConfig,
                   ZSKConfig, HGLSConfig, GWHMeteostation, EWHMeteostation, TestResult)


# ==================== EWH TESTFRAGEN (4 Fragen + 4 Infos pro Komponente) ====================

EWH_TESTFRAGEN = [
    # ==================== ANLAGE ====================
    {'komponente_typ': 'Anlage', 'testszenario': 'Grundkonfiguration', 'frage_nummer': 101,
     'frage_text': 'Anlagenname korrekt konfiguriert?',
     'test_information': 'Pruefen Sie den Anlagennamen im WH-LTS und LSS-CH.',
     'erwartetes_ergebnis': 'Name stimmt mit Projektdokumentation ueberein', 'reihenfolge': 1},
    {'komponente_typ': 'Anlage', 'testszenario': 'Grundkonfiguration', 'frage_nummer': 102,
     'frage_text': 'DIDOK-Betriebspunkt korrekt?',
     'test_information': 'DIDOK-Nummer im System mit SBB-Vorgaben vergleichen.',
     'erwartetes_ergebnis': 'DIDOK stimmt ueberein', 'reihenfolge': 2},
    {'komponente_typ': 'Anlage', 'testszenario': 'Kommunikation', 'frage_nummer': 103,
     'frage_text': 'Verbindung zu LSS-CH aktiv?',
     'test_information': 'Kommunikationsstatus im WH-LTS pruefen.',
     'erwartetes_ergebnis': 'Verbindung steht, gruenes Symbol', 'reihenfolge': 3},
    {'komponente_typ': 'Anlage', 'testszenario': 'Betrieb', 'frage_nummer': 104,
     'frage_text': 'Freigabe Ein/Aus funktioniert?',
     'test_information': 'Freigabe aktivieren und deaktivieren, Reaktion beobachten.',
     'erwartetes_ergebnis': 'Anlage reagiert auf Freigabebefehle', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'Anlage', 'testszenario': 'Info', 'frage_nummer': 105,
     'frage_text': 'Anzahl WHK im System?',
     'test_information': 'Anzahl konfigurierter WHK zaehlen.',
     'erwartetes_ergebnis': 'INFO: Anzahl notieren', 'reihenfolge': 5},
    {'komponente_typ': 'Anlage', 'testszenario': 'Info', 'frage_nummer': 106,
     'frage_text': 'Betriebszentrale zugeordnet?',
     'test_information': 'Zugewiesene Betriebszentrale pruefen.',
     'erwartetes_ergebnis': 'INFO: BZ notieren', 'reihenfolge': 6},
    {'komponente_typ': 'Anlage', 'testszenario': 'Info', 'frage_nummer': 107,
     'frage_text': 'Software-Version WH-LTS?',
     'test_information': 'Aktuelle Software-Version im System ablesen.',
     'erwartetes_ergebnis': 'INFO: Version notieren', 'reihenfolge': 7},
    {'komponente_typ': 'Anlage', 'testszenario': 'Info', 'frage_nummer': 108,
     'frage_text': 'Inbetriebnahmejahr erfasst?',
     'test_information': 'IBN-Jahr in Projektdaten pruefen.',
     'erwartetes_ergebnis': 'INFO: Jahr notieren', 'reihenfolge': 8},

    # ==================== WHK ====================
    {'komponente_typ': 'WHK', 'testszenario': 'Identifikation', 'frage_nummer': 201,
     'frage_text': 'WHK-Bezeichnung korrekt?',
     'test_information': 'Bezeichnung am Schrank mit System vergleichen.',
     'erwartetes_ergebnis': 'Bezeichnungen stimmen ueberein', 'reihenfolge': 1},
    {'komponente_typ': 'WHK', 'testszenario': 'Alarme', 'frage_nummer': 202,
     'frage_text': 'Tuerkontaktmeldung funktioniert?',
     'test_information': 'Schranktuer oeffnen und Meldung pruefen.',
     'erwartetes_ergebnis': 'Tueroffen-Meldung erscheint', 'reihenfolge': 2},
    {'komponente_typ': 'WHK', 'testszenario': 'Temperatur', 'frage_nummer': 203,
     'frage_text': 'Schranktemperatur plausibel?',
     'test_information': 'Temperaturanzeige mit Referenzthermometer vergleichen.',
     'erwartetes_ergebnis': 'Abweichung < 3°C', 'reihenfolge': 3},
    {'komponente_typ': 'WHK', 'testszenario': 'Heizung', 'frage_nummer': 204,
     'frage_text': 'Schaltschrankheizung regelt?',
     'test_information': 'Bei niedriger Temperatur Heizungsaktivierung pruefen.',
     'erwartetes_ergebnis': 'Heizung schaltet bei Bedarf ein', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'WHK', 'testszenario': 'Info', 'frage_nummer': 205,
     'frage_text': 'Anzahl Abgaenge konfiguriert?',
     'test_information': 'Anzahl der konfigurierten Abgaenge pruefen.',
     'erwartetes_ergebnis': 'INFO: Anzahl notieren', 'reihenfolge': 5},
    {'komponente_typ': 'WHK', 'testszenario': 'Info', 'frage_nummer': 206,
     'frage_text': 'Anzahl Temperatursonden?',
     'test_information': 'Anzahl TS im System zaehlen.',
     'erwartetes_ergebnis': 'INFO: Anzahl notieren', 'reihenfolge': 6},
    {'komponente_typ': 'WHK', 'testszenario': 'Info', 'frage_nummer': 207,
     'frage_text': 'Meteostation zugeordnet?',
     'test_information': 'Zugewiesene Meteostation pruefen.',
     'erwartetes_ergebnis': 'INFO: MS-Name notieren', 'reihenfolge': 7},
    {'komponente_typ': 'WHK', 'testszenario': 'Info', 'frage_nummer': 208,
     'frage_text': 'Standort/Gleisbereich?',
     'test_information': 'Physischen Standort des WHK dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Standort notieren', 'reihenfolge': 8},

    # ==================== ABGANG ====================
    {'komponente_typ': 'Abgang', 'testszenario': 'Identifikation', 'frage_nummer': 301,
     'frage_text': 'Abgangsbezeichnung korrekt?',
     'test_information': 'Abgangsnummer am Klemmenblock und im System pruefen.',
     'erwartetes_ergebnis': 'Bezeichnungen stimmen', 'reihenfolge': 1},
    {'komponente_typ': 'Abgang', 'testszenario': 'Schaltfunktion', 'frage_nummer': 302,
     'frage_text': 'Manuelles Schalten funktioniert?',
     'test_information': 'Abgang manuell ein- und ausschalten.',
     'erwartetes_ergebnis': 'Schaltet zuverlaessig', 'reihenfolge': 2},
    {'komponente_typ': 'Abgang', 'testszenario': 'Stromaufnahme', 'frage_nummer': 303,
     'frage_text': 'Stromaufnahme im Normbereich?',
     'test_information': 'Stromwert bei aktivem Heizelement messen.',
     'erwartetes_ergebnis': 'Strom gemaess Datenblatt', 'reihenfolge': 3},
    {'komponente_typ': 'Abgang', 'testszenario': 'Rueckmeldung', 'frage_nummer': 304,
     'frage_text': 'Statusrueckmeldung korrekt?',
     'test_information': 'Status im WH-LTS mit physischem Zustand vergleichen.',
     'erwartetes_ergebnis': 'Status stimmt ueberein', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'Abgang', 'testszenario': 'Info', 'frage_nummer': 305,
     'frage_text': 'Heizleistung in kW?',
     'test_information': 'Nennleistung des Heizelements ablesen.',
     'erwartetes_ergebnis': 'INFO: Leistung notieren', 'reihenfolge': 5},
    {'komponente_typ': 'Abgang', 'testszenario': 'Info', 'frage_nummer': 306,
     'frage_text': 'Weichennummer zugeordnet?',
     'test_information': 'Zugehoerige Weiche identifizieren.',
     'erwartetes_ergebnis': 'INFO: Weichen-Nr notieren', 'reihenfolge': 6},
    {'komponente_typ': 'Abgang', 'testszenario': 'Info', 'frage_nummer': 307,
     'frage_text': 'Heizstabtyp dokumentiert?',
     'test_information': 'Typ des Heizstabes aus Dokumentation entnehmen.',
     'erwartetes_ergebnis': 'INFO: Typ notieren', 'reihenfolge': 7},
    {'komponente_typ': 'Abgang', 'testszenario': 'Info', 'frage_nummer': 308,
     'frage_text': 'Sicherungsgroesse?',
     'test_information': 'Vorsicherung des Abgangs pruefen.',
     'erwartetes_ergebnis': 'INFO: Sicherung notieren', 'reihenfolge': 8},

    # ==================== TEMPERATURSONDE ====================
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Identifikation', 'frage_nummer': 401,
     'frage_text': 'Sondenbezeichnung korrekt?',
     'test_information': 'Sondennummer am Sensor und im System pruefen.',
     'erwartetes_ergebnis': 'Bezeichnungen stimmen', 'reihenfolge': 1},
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Messwert', 'frage_nummer': 402,
     'frage_text': 'Temperaturwert plausibel?',
     'test_information': 'Mit Referenzthermometer an Schienenoberkante vergleichen.',
     'erwartetes_ergebnis': 'Abweichung < 2°C', 'reihenfolge': 2},
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Stoerung', 'frage_nummer': 403,
     'frage_text': 'Sensorausfall wird gemeldet?',
     'test_information': 'Sensor abklemmen und Stoermeldung pruefen.',
     'erwartetes_ergebnis': 'Stoermeldung erscheint', 'reihenfolge': 3},
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Regelung', 'frage_nummer': 404,
     'frage_text': 'Temperaturregelung funktioniert?',
     'test_information': 'Sollwert aendern und Heizreaktion beobachten.',
     'erwartetes_ergebnis': 'Heizung reagiert auf Sollwert', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Info', 'frage_nummer': 405,
     'frage_text': 'Sensortyp (PT100/PT1000)?',
     'test_information': 'Sensortyp aus Dokumentation entnehmen.',
     'erwartetes_ergebnis': 'INFO: Typ notieren', 'reihenfolge': 5},
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Info', 'frage_nummer': 406,
     'frage_text': 'Montageort dokumentiert?',
     'test_information': 'Position der Sonde beschreiben.',
     'erwartetes_ergebnis': 'INFO: Ort notieren', 'reihenfolge': 6},
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Info', 'frage_nummer': 407,
     'frage_text': 'Kabellaenge bekannt?',
     'test_information': 'Kabellaenge aus Planung entnehmen.',
     'erwartetes_ergebnis': 'INFO: Laenge notieren', 'reihenfolge': 7},
    {'komponente_typ': 'Temperatursonde', 'testszenario': 'Info', 'frage_nummer': 408,
     'frage_text': 'Solltemperatur konfiguriert?',
     'test_information': 'Sollwert im System ablesen.',
     'erwartetes_ergebnis': 'INFO: Sollwert notieren', 'reihenfolge': 8},

    # ==================== ANTRIEBSHEIZUNG ====================
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Identifikation', 'frage_nummer': 501,
     'frage_text': 'Antriebsheizung bezeichnet?',
     'test_information': 'Bezeichnung im System mit physischer Komponente vergleichen.',
     'erwartetes_ergebnis': 'Bezeichnung korrekt', 'reihenfolge': 1},
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Heizfunktion', 'frage_nummer': 502,
     'frage_text': 'Heizung erwaermt Antrieb?',
     'test_information': 'Heizung aktivieren und Erwaermung fuehlen.',
     'erwartetes_ergebnis': 'Erwaermung spuerbar', 'reihenfolge': 2},
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Thermostat', 'frage_nummer': 503,
     'frage_text': 'Thermostat regelt korrekt?',
     'test_information': 'Abschaltung bei Erreichen der Solltemperatur pruefen.',
     'erwartetes_ergebnis': 'Schaltet bei Sollwert ab', 'reihenfolge': 3},
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Stromaufnahme', 'frage_nummer': 504,
     'frage_text': 'Stromaufnahme OK?',
     'test_information': 'Stromwert bei aktivem Betrieb messen.',
     'erwartetes_ergebnis': 'Im Sollbereich', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Info', 'frage_nummer': 505,
     'frage_text': 'Heizleistung in Watt?',
     'test_information': 'Nennleistung der Antriebsheizung ablesen.',
     'erwartetes_ergebnis': 'INFO: Leistung notieren', 'reihenfolge': 5},
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Info', 'frage_nummer': 506,
     'frage_text': 'Weichenantriebstyp?',
     'test_information': 'Typ des Weichenantriebs dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Typ notieren', 'reihenfolge': 6},
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Info', 'frage_nummer': 507,
     'frage_text': 'Thermostat-Einstellung?',
     'test_information': 'Eingestellte Schalttemperatur ablesen.',
     'erwartetes_ergebnis': 'INFO: Temperatur notieren', 'reihenfolge': 7},
    {'komponente_typ': 'Antriebsheizung', 'testszenario': 'Info', 'frage_nummer': 508,
     'frage_text': 'Hersteller/Modell?',
     'test_information': 'Herstellerangaben vom Typenschild.',
     'erwartetes_ergebnis': 'INFO: Hersteller notieren', 'reihenfolge': 8},

    # ==================== METEOSTATION ====================
    {'komponente_typ': 'Meteostation', 'testszenario': 'Identifikation', 'frage_nummer': 601,
     'frage_text': 'Meteostationsname korrekt?',
     'test_information': 'Bezeichnung im System pruefen.',
     'erwartetes_ergebnis': 'Name stimmt', 'reihenfolge': 1},
    {'komponente_typ': 'Meteostation', 'testszenario': 'Niederschlag', 'frage_nummer': 602,
     'frage_text': 'Niederschlagssensor funktioniert?',
     'test_information': 'Sensor mit Wasser benetzen und Signal pruefen.',
     'erwartetes_ergebnis': 'Erkennt Niederschlag', 'reihenfolge': 2},
    {'komponente_typ': 'Meteostation', 'testszenario': 'Temperatur', 'frage_nummer': 603,
     'frage_text': 'Aussentemperatur plausibel?',
     'test_information': 'Mit Referenzthermometer vergleichen.',
     'erwartetes_ergebnis': 'Abweichung < 2°C', 'reihenfolge': 3},
    {'komponente_typ': 'Meteostation', 'testszenario': 'Kommunikation', 'frage_nummer': 604,
     'frage_text': 'Datenuebertragung funktioniert?',
     'test_information': 'Aktualitaet der Meteodaten im System pruefen.',
     'erwartetes_ergebnis': 'Daten werden uebertragen', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'Meteostation', 'testszenario': 'Info', 'frage_nummer': 605,
     'frage_text': 'Modbus-Adresse?',
     'test_information': 'Konfigurierte Modbus-Adresse ablesen.',
     'erwartetes_ergebnis': 'INFO: Adresse notieren', 'reihenfolge': 5},
    {'komponente_typ': 'Meteostation', 'testszenario': 'Info', 'frage_nummer': 606,
     'frage_text': 'Montagehoehe?',
     'test_information': 'Hoehe der Meteostation ueber Boden.',
     'erwartetes_ergebnis': 'INFO: Hoehe notieren', 'reihenfolge': 6},
    {'komponente_typ': 'Meteostation', 'testszenario': 'Info', 'frage_nummer': 607,
     'frage_text': 'Hersteller/Modell?',
     'test_information': 'Herstellerangaben dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Hersteller notieren', 'reihenfolge': 7},
    {'komponente_typ': 'Meteostation', 'testszenario': 'Info', 'frage_nummer': 608,
     'frage_text': 'Anzahl zugeordneter WHK?',
     'test_information': 'Welche WHK diese MS nutzen.',
     'erwartetes_ergebnis': 'INFO: WHK-Liste notieren', 'reihenfolge': 8},
]


# ==================== GWH TESTFRAGEN (4 Fragen + 4 Infos pro Komponente) ====================

GWH_TESTFRAGEN = [
    # ==================== GWH_ANLAGE ====================
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Grundkonfiguration', 'frage_nummer': 1101,
     'frage_text': 'GWH-Anlagenname korrekt?',
     'test_information': 'Bezeichnung im Leitsystem mit Projektdokumentation vergleichen.',
     'erwartetes_ergebnis': 'Name stimmt ueberein', 'reihenfolge': 1},
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Grundkonfiguration', 'frage_nummer': 1102,
     'frage_text': 'DIDOK-Betriebspunkt korrekt?',
     'test_information': 'DIDOK-Nummer pruefen.',
     'erwartetes_ergebnis': 'DIDOK stimmt', 'reihenfolge': 2},
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Kommunikation', 'frage_nummer': 1103,
     'frage_text': 'Verbindung zu LSS-CH aktiv?',
     'test_information': 'Kommunikationsstatus pruefen.',
     'erwartetes_ergebnis': 'Verbindung steht', 'reihenfolge': 3},
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Betrieb', 'frage_nummer': 1104,
     'frage_text': 'Freigabe Ein/Aus funktioniert?',
     'test_information': 'Freigabebefehle testen.',
     'erwartetes_ergebnis': 'Anlage reagiert korrekt', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Info', 'frage_nummer': 1105,
     'frage_text': 'Anzahl ZSK im System?',
     'test_information': 'Anzahl Zuendschaltkaesten zaehlen.',
     'erwartetes_ergebnis': 'INFO: Anzahl notieren', 'reihenfolge': 5},
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Info', 'frage_nummer': 1106,
     'frage_text': 'Gasversorgungstyp?',
     'test_information': 'Propan oder Erdgas dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Gastyp notieren', 'reihenfolge': 6},
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Info', 'frage_nummer': 1107,
     'frage_text': 'Betriebszentrale zugeordnet?',
     'test_information': 'Zustaendige BZ pruefen.',
     'erwartetes_ergebnis': 'INFO: BZ notieren', 'reihenfolge': 7},
    {'komponente_typ': 'GWH_Anlage', 'testszenario': 'Info', 'frage_nummer': 1108,
     'frage_text': 'Inbetriebnahmejahr?',
     'test_information': 'IBN-Jahr dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Jahr notieren', 'reihenfolge': 8},

    # ==================== HGLS ====================
    {'komponente_typ': 'HGLS', 'testszenario': 'Identifikation', 'frage_nummer': 1201,
     'frage_text': 'HGLS-Typ korrekt (Propan/Erdgas)?',
     'test_information': 'Gasversorgungstyp im System pruefen.',
     'erwartetes_ergebnis': 'Typ stimmt mit Konfiguration', 'reihenfolge': 1},
    {'komponente_typ': 'HGLS', 'testszenario': 'Sicherheit', 'frage_nummer': 1202,
     'frage_text': 'Hauptabsperrventil funktioniert?',
     'test_information': 'Ventil betaetigen und Gasfluss pruefen.',
     'erwartetes_ergebnis': 'Ventil schliesst/oeffnet', 'reihenfolge': 2},
    {'komponente_typ': 'HGLS', 'testszenario': 'Druckregelung', 'frage_nummer': 1203,
     'frage_text': 'Gasdruck im Normbereich?',
     'test_information': 'Manometer am Druckregler ablesen.',
     'erwartetes_ergebnis': 'Druck im Sollbereich', 'reihenfolge': 3},
    {'komponente_typ': 'HGLS', 'testszenario': 'Alarme', 'frage_nummer': 1204,
     'frage_text': 'Gaswarnanlage funktioniert?',
     'test_information': 'Testgas an Sensor und Alarm pruefen.',
     'erwartetes_ergebnis': 'Alarm wird ausgeloest', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'HGLS', 'testszenario': 'Info', 'frage_nummer': 1205,
     'frage_text': 'Anzahl Gasverdampfer?',
     'test_information': 'Vorhandene Verdampfer zaehlen.',
     'erwartetes_ergebnis': 'INFO: Anzahl notieren', 'reihenfolge': 5},
    {'komponente_typ': 'HGLS', 'testszenario': 'Info', 'frage_nummer': 1206,
     'frage_text': 'Tankgroesse (bei Propan)?',
     'test_information': 'Tankvolumen dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Volumen notieren', 'reihenfolge': 6},
    {'komponente_typ': 'HGLS', 'testszenario': 'Info', 'frage_nummer': 1207,
     'frage_text': 'Fuellstand aktuell?',
     'test_information': 'Fuellstandsanzeige ablesen.',
     'erwartetes_ergebnis': 'INFO: Fuellstand notieren', 'reihenfolge': 7},
    {'komponente_typ': 'HGLS', 'testszenario': 'Info', 'frage_nummer': 1208,
     'frage_text': 'Letzte Wartung?',
     'test_information': 'Wartungsdatum aus Dokumentation.',
     'erwartetes_ergebnis': 'INFO: Datum notieren', 'reihenfolge': 8},

    # ==================== ZSK ====================
    {'komponente_typ': 'ZSK', 'testszenario': 'Identifikation', 'frage_nummer': 1301,
     'frage_text': 'ZSK-Bezeichnung korrekt?',
     'test_information': 'Nummer am Schrank mit System vergleichen.',
     'erwartetes_ergebnis': 'Bezeichnung stimmt', 'reihenfolge': 1},
    {'komponente_typ': 'ZSK', 'testszenario': 'Zuendung', 'frage_nummer': 1302,
     'frage_text': 'Zuendung funktioniert?',
     'test_information': 'Zuendvorgang starten und Flammenbildung beobachten.',
     'erwartetes_ergebnis': 'Brenner zuendet zuverlaessig', 'reihenfolge': 2},
    {'komponente_typ': 'ZSK', 'testszenario': 'Flammenueberwachung', 'frage_nummer': 1303,
     'frage_text': 'Flammenwaechter funktioniert?',
     'test_information': 'Flammensignal im System pruefen.',
     'erwartetes_ergebnis': 'Signal vorhanden bei Flamme', 'reihenfolge': 3},
    {'komponente_typ': 'ZSK', 'testszenario': 'Druckueberwachung', 'frage_nummer': 1304,
     'frage_text': 'Druckueberwachung aktiv?',
     'test_information': 'Gasdruck am ZSK messen und mit Anzeige vergleichen.',
     'erwartetes_ergebnis': 'Druckwert korrekt', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'ZSK', 'testszenario': 'Info', 'frage_nummer': 1305,
     'frage_text': 'Anzahl Teile/Brennerrohre?',
     'test_information': 'Angeschlossene Brennerrohre zaehlen.',
     'erwartetes_ergebnis': 'INFO: Anzahl notieren', 'reihenfolge': 5},
    {'komponente_typ': 'ZSK', 'testszenario': 'Info', 'frage_nummer': 1306,
     'frage_text': 'Gasversorgung zentral/dezentral?',
     'test_information': 'Versorgungsart dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Art notieren', 'reihenfolge': 6},
    {'komponente_typ': 'ZSK', 'testszenario': 'Info', 'frage_nummer': 1307,
     'frage_text': 'Temperatursonde vorhanden?',
     'test_information': 'Vorhandensein einer TS pruefen.',
     'erwartetes_ergebnis': 'INFO: Ja/Nein notieren', 'reihenfolge': 7},
    {'komponente_typ': 'ZSK', 'testszenario': 'Info', 'frage_nummer': 1308,
     'frage_text': 'Kathodenschutz vorhanden?',
     'test_information': 'Vorhandensein pruefen.',
     'erwartetes_ergebnis': 'INFO: Ja/Nein notieren', 'reihenfolge': 8},

    # ==================== GWH_TEILE ====================
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Identifikation', 'frage_nummer': 1401,
     'frage_text': 'Teil/Brennerrohr bezeichnet?',
     'test_information': 'Bezeichnung des Brennerrohrs im System pruefen.',
     'erwartetes_ergebnis': 'Bezeichnung korrekt', 'reihenfolge': 1},
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Funktion', 'frage_nummer': 1402,
     'frage_text': 'Brennerrohr zuendet?',
     'test_information': 'Zuendvorgang am einzelnen Teil beobachten.',
     'erwartetes_ergebnis': 'Teil zuendet zuverlaessig', 'reihenfolge': 2},
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Heizung', 'frage_nummer': 1403,
     'frage_text': 'Teil wird warm nach Heizbefehl?',
     'test_information': 'Waermeentwicklung am Brennerrohr pruefen.',
     'erwartetes_ergebnis': 'Erwaermung spuerbar', 'reihenfolge': 3},
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Rueckmeldung', 'frage_nummer': 1404,
     'frage_text': 'Statusrueckmeldung korrekt?',
     'test_information': 'Status im System mit physischem Zustand vergleichen.',
     'erwartetes_ergebnis': 'Status stimmt', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Info', 'frage_nummer': 1405,
     'frage_text': 'Brennerrohrtyp?',
     'test_information': 'Typ des Brennerrohrs dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Typ notieren', 'reihenfolge': 5},
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Info', 'frage_nummer': 1406,
     'frage_text': 'Weichennummer zugeordnet?',
     'test_information': 'Zugehoerige Weiche identifizieren.',
     'erwartetes_ergebnis': 'INFO: Weichen-Nr notieren', 'reihenfolge': 6},
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Info', 'frage_nummer': 1407,
     'frage_text': 'Laenge Brennerrohr?',
     'test_information': 'Laenge des Brennerrohrs dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Laenge notieren', 'reihenfolge': 7},
    {'komponente_typ': 'GWH_Teile', 'testszenario': 'Info', 'frage_nummer': 1408,
     'frage_text': 'Leistung in kW?',
     'test_information': 'Nennleistung des Brennerrohrs.',
     'erwartetes_ergebnis': 'INFO: Leistung notieren', 'reihenfolge': 8},

    # ==================== GWH_TEMPERATURSONDE ====================
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Identifikation', 'frage_nummer': 1501,
     'frage_text': 'GWH-Temperatursonde bezeichnet?',
     'test_information': 'Bezeichnung im System pruefen.',
     'erwartetes_ergebnis': 'Bezeichnung korrekt', 'reihenfolge': 1},
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Messwert', 'frage_nummer': 1502,
     'frage_text': 'Schienentemperatur plausibel?',
     'test_information': 'Mit Referenzthermometer vergleichen.',
     'erwartetes_ergebnis': 'Abweichung < 2°C', 'reihenfolge': 2},
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Stoerung', 'frage_nummer': 1503,
     'frage_text': 'Sensorausfall wird gemeldet?',
     'test_information': 'Sensor abklemmen und Stoermeldung pruefen.',
     'erwartetes_ergebnis': 'Stoermeldung erscheint', 'reihenfolge': 3},
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Regelung', 'frage_nummer': 1504,
     'frage_text': 'Temperaturregelung funktioniert?',
     'test_information': 'Sollwert aendern und Heizreaktion beobachten.',
     'erwartetes_ergebnis': 'Heizung reagiert auf Sollwert', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Info', 'frage_nummer': 1505,
     'frage_text': 'Sensortyp (PT100/PT1000)?',
     'test_information': 'Sensortyp dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Typ notieren', 'reihenfolge': 5},
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Info', 'frage_nummer': 1506,
     'frage_text': 'Montageort dokumentiert?',
     'test_information': 'Position der Sonde beschreiben.',
     'erwartetes_ergebnis': 'INFO: Ort notieren', 'reihenfolge': 6},
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Info', 'frage_nummer': 1507,
     'frage_text': 'Zugeordneter ZSK?',
     'test_information': 'Welchem ZSK die Sonde zugeordnet ist.',
     'erwartetes_ergebnis': 'INFO: ZSK notieren', 'reihenfolge': 7},
    {'komponente_typ': 'GWH_Temperatursonde', 'testszenario': 'Info', 'frage_nummer': 1508,
     'frage_text': 'Solltemperatur konfiguriert?',
     'test_information': 'Sollwert im System ablesen.',
     'erwartetes_ergebnis': 'INFO: Sollwert notieren', 'reihenfolge': 8},

    # ==================== GWH_METEOSTATION ====================
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Identifikation', 'frage_nummer': 1601,
     'frage_text': 'GWH-Meteostation bezeichnet?',
     'test_information': 'Bezeichnung im System pruefen.',
     'erwartetes_ergebnis': 'Name korrekt', 'reihenfolge': 1},
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Niederschlag', 'frage_nummer': 1602,
     'frage_text': 'Niederschlagserkennung funktioniert?',
     'test_information': 'Sensor mit Wasser benetzen.',
     'erwartetes_ergebnis': 'Erkennt Naesse', 'reihenfolge': 2},
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Temperatur', 'frage_nummer': 1603,
     'frage_text': 'Aussentemperatur plausibel?',
     'test_information': 'Mit Referenzthermometer vergleichen.',
     'erwartetes_ergebnis': 'Abweichung < 2°C', 'reihenfolge': 3},
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Kommunikation', 'frage_nummer': 1604,
     'frage_text': 'Datenuebertragung OK?',
     'test_information': 'Aktualitaet der Daten pruefen.',
     'erwartetes_ergebnis': 'Daten werden uebertragen', 'reihenfolge': 4},
    # Infos
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Info', 'frage_nummer': 1605,
     'frage_text': 'Modbus-Adresse?',
     'test_information': 'Konfigurierte Adresse ablesen.',
     'erwartetes_ergebnis': 'INFO: Adresse notieren', 'reihenfolge': 5},
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Info', 'frage_nummer': 1606,
     'frage_text': 'Zugeordneter ZSK?',
     'test_information': 'Zuordnung zu ZSK dokumentieren.',
     'erwartetes_ergebnis': 'INFO: ZSK notieren', 'reihenfolge': 6},
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Info', 'frage_nummer': 1607,
     'frage_text': 'Montageort?',
     'test_information': 'Physischen Standort dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Ort notieren', 'reihenfolge': 7},
    {'komponente_typ': 'GWH_Meteostation', 'testszenario': 'Info', 'frage_nummer': 1608,
     'frage_text': 'Hersteller/Modell?',
     'test_information': 'Herstellerangaben dokumentieren.',
     'erwartetes_ergebnis': 'INFO: Hersteller notieren', 'reihenfolge': 8},
]


# ==================== KLEINE TESTPROJEKTE (2 EWH, 2 GWH mit 100%) ====================

DEMO_PROJEKTE = [
    # EWH Projekte (klein: 1 WHK mit 2 Abgaengen, 1 TS)
    {'energie': 'EWH', 'projektname': 'EWH Demo Aarau', 'didok': '8502113',
     'projektleiter': 'Hans Muster', 'pruefer': 'Achermann AG',
     'whk_count': 1, 'abgaenge': 2, 'ts': 1, 'antriebsheizung': True},
    {'energie': 'EWH', 'projektname': 'EWH Demo Baden', 'didok': '8502201',
     'projektleiter': 'Peter Beispiel', 'pruefer': 'Achermann AG',
     'whk_count': 1, 'abgaenge': 2, 'ts': 1, 'antriebsheizung': False},

    # GWH Projekte (klein: 1 ZSK mit 2 Teilen)
    {'energie': 'GWH', 'projektname': 'GWH Demo Brugg', 'didok': '8502206',
     'projektleiter': 'Anna Test', 'pruefer': 'Achermann AG',
     'zsk_count': 1, 'teile': 2, 'gastyp': 'Propan'},
    {'energie': 'GWH', 'projektname': 'GWH Demo Turgi', 'didok': '8502218',
     'projektleiter': 'Lisa Demo', 'pruefer': 'Achermann AG',
     'zsk_count': 1, 'teile': 2, 'gastyp': 'Erdgas'},
]


def clear_all_data():
    """Loescht alle relevanten Daten aus der Datenbank."""
    print("Loesche bestehende Daten...")

    # Loesche in korrekter Reihenfolge (Foreign Keys beachten)
    AbnahmeTestResult.query.delete()
    EWHMeteostation.query.delete()
    GWHMeteostation.query.delete()
    WHKConfig.query.delete()
    ZSKConfig.query.delete()
    HGLSConfig.query.delete()
    TestQuestion.query.delete()
    TestResult.query.delete()
    Project.query.delete()

    db.session.commit()
    print("[OK] Alle Daten geloescht")


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

    # Zaehle Fragen pro Komponente
    ewh_komponenten = ['Anlage', 'WHK', 'Abgang', 'Temperatursonde', 'Antriebsheizung', 'Meteostation']
    gwh_komponenten = ['GWH_Anlage', 'HGLS', 'ZSK', 'GWH_Teile', 'GWH_Temperatursonde', 'GWH_Meteostation']

    print(f"[OK] {len(all_questions)} Testfragen erstellt")
    print("\n   EWH Komponenten:")
    for komp in ewh_komponenten:
        count = len([q for q in EWH_TESTFRAGEN if q['komponente_typ'] == komp])
        print(f"      - {komp}: {count} Fragen")
    print("\n   GWH Komponenten:")
    for komp in gwh_komponenten:
        count = len([q for q in GWH_TESTFRAGEN if q['komponente_typ'] == komp])
        print(f"      - {komp}: {count} Fragen")


def create_demo_projects():
    """Erstellt Demo-Projekte mit Konfigurationen und 100% Testergebnissen."""
    print("\nErstelle Demo-Projekte...")

    for p in DEMO_PROJEKTE:
        # Projekt erstellen
        projekt = Project(
            energie=p['energie'],
            projektname=p['projektname'],
            didok_betriebspunkt=p['didok'],
            projektleiter_sbb=p['projektleiter'],
            pruefer_achermann=p['pruefer'],
            pruefdatum=date.today(),
            ibn_inbetriebnahme_jahre='2024',
            bemerkung=f"Demo-Projekt mit 100% Testfortschritt"
        )
        db.session.add(projekt)
        db.session.flush()  # Um die ID zu bekommen

        if p['energie'] == 'EWH':
            create_ewh_config_and_results(projekt, p)
        else:
            create_gwh_config_and_results(projekt, p)

        print(f"   [OK] {p['projektname']} erstellt")

    db.session.commit()
    print(f"\n[OK] {len(DEMO_PROJEKTE)} Demo-Projekte erstellt")


def create_ewh_config_and_results(projekt, config):
    """Erstellt EWH-Konfiguration und 100% Testergebnisse."""

    # WHK Configs erstellen
    for i in range(config['whk_count']):
        whk = WHKConfig(
            projekt_id=projekt.id,
            whk_nummer=f"WHK {i+1:02d}",
            anzahl_abgaenge=config['abgaenge'],
            anzahl_temperatursonden=config['ts'],
            hat_antriebsheizung=config.get('antriebsheizung', False) and i == 0,
            meteostation=f"MS {i+1:02d}A"
        )
        db.session.add(whk)
        db.session.flush()

        # EWH Meteostation erstellen
        ms = EWHMeteostation(
            projekt_id=projekt.id,
            zugeordnete_whk_id=whk.id,
            ms_nummer=f"{i+1:02d}",
            reihenfolge=i+1
        )
        db.session.add(ms)

    db.session.flush()

    # Hole alle WHK-Configs fuer dieses Projekt
    whk_configs = WHKConfig.query.filter_by(projekt_id=projekt.id).all()

    # Alle EWH-Fragen durchgehen und Ergebnisse erstellen
    for frage_def in EWH_TESTFRAGEN:
        frage = TestQuestion.query.filter_by(frage_nummer=frage_def['frage_nummer']).first()
        if not frage:
            continue

        komp = frage_def['komponente_typ']

        if komp == 'Anlage':
            # Eine Antwort fuer die gesamte Anlage
            result = AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=frage.id,
                komponente_index='Anlage',
                spalte=None,
                lss_ch_result='richtig',
                wh_lts_result='richtig',
                tester='Demo-Tester'
            )
            db.session.add(result)

        elif komp == 'WHK':
            # Fuer jede WHK eine Antwort
            for whk in whk_configs:
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=frage.id,
                    komponente_index=whk.whk_nummer,
                    spalte=None,
                    lss_ch_result='richtig',
                    wh_lts_result='richtig',
                    tester='Demo-Tester'
                )
                db.session.add(result)

        elif komp == 'Abgang':
            # Fuer jeden Abgang jeder WHK eine Antwort
            for whk in whk_configs:
                for j in range(whk.anzahl_abgaenge):
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=whk.whk_nummer,
                        spalte=f"Abgang {j+1:02d}",
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        tester='Demo-Tester'
                    )
                    db.session.add(result)

        elif komp == 'Temperatursonde':
            # Fuer jede TS jeder WHK eine Antwort
            for whk in whk_configs:
                for j in range(whk.anzahl_temperatursonden):
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=whk.whk_nummer,
                        spalte=f"TS {j+1:02d}",
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        tester='Demo-Tester'
                    )
                    db.session.add(result)

        elif komp == 'Antriebsheizung':
            # Nur fuer WHKs mit Antriebsheizung
            for whk in whk_configs:
                if whk.hat_antriebsheizung:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=whk.whk_nummer,
                        spalte='Antriebsheizung',
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        tester='Demo-Tester'
                    )
                    db.session.add(result)

        elif komp == 'Meteostation':
            # Fuer jede Meteostation
            meteostations = EWHMeteostation.query.filter_by(projekt_id=projekt.id).all()
            for ms in meteostations:
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=frage.id,
                    komponente_index=f"MS {ms.ms_nummer}A",
                    spalte=None,
                    lss_ch_result='richtig',
                    wh_lts_result='richtig',
                    tester='Demo-Tester'
                )
                db.session.add(result)


def create_gwh_config_and_results(projekt, config):
    """Erstellt GWH-Konfiguration und 100% Testergebnisse."""

    # HGLS Config erstellen
    hgls = HGLSConfig(
        projekt_id=projekt.id,
        hgls_typ=config.get('gastyp', 'Propan'),
        hat_fuellventil=True,
        hat_bypassventil=True,
        hat_gaswarnanlage=True
    )
    db.session.add(hgls)

    # ZSK Configs erstellen
    for i in range(config['zsk_count']):
        zsk = ZSKConfig(
            projekt_id=projekt.id,
            zsk_nummer=f"{i+1:02d}",
            anzahl_teile=config['teile'],
            hat_temperatursonde=True,
            gasversorgung='zentral',
            kathodenschutz=False,
            reihenfolge=i+1
        )
        db.session.add(zsk)

    # GWH Meteostation erstellen
    meteo = GWHMeteostation(
        projekt_id=projekt.id,
        ms_nummer="01",
        name="MS 01",
        modbus_adresse=50,
        reihenfolge=1
    )
    db.session.add(meteo)

    db.session.flush()

    # Hole alle ZSK-Configs fuer dieses Projekt
    zsk_configs = ZSKConfig.query.filter_by(projekt_id=projekt.id).all()

    # Alle GWH-Fragen durchgehen und Ergebnisse erstellen
    for frage_def in GWH_TESTFRAGEN:
        frage = TestQuestion.query.filter_by(frage_nummer=frage_def['frage_nummer']).first()
        if not frage:
            continue

        komp = frage_def['komponente_typ']

        if komp == 'GWH_Anlage':
            # GWH-Anlage: komponente_index='GWH-Anlage', spalte='GWH-Anlage'
            result = AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=frage.id,
                komponente_index='GWH-Anlage',
                spalte='GWH-Anlage',
                lss_ch_result='richtig',
                wh_lts_result='richtig',
                tester='Demo-Tester'
            )
            db.session.add(result)

        elif komp == 'HGLS':
            # HGLS: komponente_index='HGLS', spalte='HGLS'
            result = AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=frage.id,
                komponente_index='HGLS',
                spalte='HGLS',
                lss_ch_result='richtig',
                wh_lts_result='richtig',
                tester='Demo-Tester'
            )
            db.session.add(result)

        elif komp == 'ZSK':
            # ZSK: komponente_index='' (leer), spalte='ZSK_01'
            for zsk in zsk_configs:
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=frage.id,
                    komponente_index='',
                    spalte=f"ZSK_{zsk.zsk_nummer}",
                    lss_ch_result='richtig',
                    wh_lts_result='richtig',
                    tester='Demo-Tester'
                )
                db.session.add(result)

        elif komp == 'GWH_Teile':
            # Teile: komponente_index='ZSK_01', spalte='Teil_01'
            for zsk in zsk_configs:
                for j in range(zsk.anzahl_teile):
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=f"ZSK_{zsk.zsk_nummer}",
                        spalte=f"Teil_{j+1:02d}",
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        tester='Demo-Tester'
                    )
                    db.session.add(result)

        elif komp == 'GWH_Temperatursonde':
            # Temperatursonde: komponente_index='ZSK_01', spalte='TS'
            for zsk in zsk_configs:
                if zsk.hat_temperatursonde:
                    result = AbnahmeTestResult(
                        projekt_id=projekt.id,
                        test_question_id=frage.id,
                        komponente_index=f"ZSK_{zsk.zsk_nummer}",
                        spalte='TS',
                        lss_ch_result='richtig',
                        wh_lts_result='richtig',
                        tester='Demo-Tester'
                    )
                    db.session.add(result)

        elif komp == 'GWH_Meteostation':
            # Meteostation: komponente_index='MS_01', spalte='MS_01'
            gwh_meteostations = GWHMeteostation.query.filter_by(projekt_id=projekt.id).all()
            for ms in gwh_meteostations:
                ms_key = f"MS_{ms.ms_nummer}"
                result = AbnahmeTestResult(
                    projekt_id=projekt.id,
                    test_question_id=frage.id,
                    komponente_index=ms_key,
                    spalte=ms_key,
                    lss_ch_result='richtig',
                    wh_lts_result='richtig',
                    tester='Demo-Tester'
                )
                db.session.add(result)


def main():
    """Hauptfunktion."""
    print("=" * 60)
    print("WHS Demo-Daten Generator")
    print("=" * 60)
    print("ACHTUNG: Loescht alle bestehenden Testfragen und Projekte!")
    print("=" * 60)

    with app.app_context():
        # 1. Bestehende Daten loeschen
        clear_all_data()

        # 2. Testfragen erstellen
        create_test_questions()

        # 3. Demo-Projekte mit 100% Ergebnissen erstellen
        create_demo_projects()

        # Zusammenfassung
        print("\n" + "=" * 60)
        print("ZUSAMMENFASSUNG")
        print("=" * 60)

        ewh_fragen = TestQuestion.query.filter(
            TestQuestion.komponente_typ.in_(['Anlage', 'WHK', 'Abgang', 'Temperatursonde', 'Antriebsheizung', 'Meteostation'])
        ).count()
        gwh_fragen = TestQuestion.query.filter(
            TestQuestion.komponente_typ.in_(['GWH_Anlage', 'HGLS', 'ZSK', 'GWH_Teile', 'GWH_Temperatursonde', 'GWH_Meteostation'])
        ).count()

        print(f"Testfragen EWH:     {ewh_fragen} (6 Komponenten x 8 Fragen)")
        print(f"Testfragen GWH:     {gwh_fragen} (6 Komponenten x 8 Fragen)")
        print(f"Testfragen Gesamt:  {ewh_fragen + gwh_fragen}")
        print()
        print(f"Projekte EWH:       {Project.query.filter_by(energie='EWH').count()}")
        print(f"Projekte GWH:       {Project.query.filter_by(energie='GWH').count()}")
        print(f"Testergebnisse:     {AbnahmeTestResult.query.count()}")
        print("=" * 60)
        print("[OK] Demo-Daten erfolgreich erstellt!")
        print("\nAlle 4 Projekte haben 100% Testfortschritt.")


if __name__ == '__main__':
    main()
