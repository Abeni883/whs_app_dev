"""
Erstellt Testprojekte für PDF-Export-Tests.

Erstellt zwei vollständig ausgefüllte Testprojekte:
1. EWH-Projekt "PDF-Test EWH Zürich"
2. GWH-Projekt "PDF-Test GWH Basel"

Alle Tests werden zu 100% ausgefüllt.
"""

import random
import sys
import os
from datetime import date

# Füge das Hauptverzeichnis zum Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import (
    db, Project, WHKConfig, ZSKConfig, EWHMeteostation, GWHMeteostation,
    HGLSConfig, TestQuestion, AbnahmeTestResult,
    HGLSParameterPruefung, ZSKParameterPruefung
)
from parameter_definitionen import HGLS_PARAMETER, ZSK_PARAMETER


# EWH Komponente-Typen
EWH_KOMPONENTEN = ['Anlage', 'WHK', 'Abgang', 'Temperatursonde', 'Antriebsheizung', 'Meteostation']

# GWH Komponente-Typen
GWH_KOMPONENTEN = ['GWH_Anlage', 'HGLS', 'ZSK', 'GWH_Teile', 'GWH_Temperatursonde', 'GWH_Meteostation']


def get_random_result():
    """80% richtig, 10% falsch, 10% nicht_testbar"""
    r = random.random()
    if r < 0.8:
        return 'richtig'
    elif r < 0.9:
        return 'falsch'
    else:
        return 'nicht_testbar'


def get_random_bemerkung():
    """20% Chance auf Bemerkung"""
    if random.random() < 0.2:
        return random.choice([
            "Alles in Ordnung",
            "Wurde nachgeprüft",
            "Siehe Protokoll",
            "OK nach Korrektur",
            "Gemäss Spezifikation",
            "Nachkontrolle erfolgt"
        ])
    return None


def fill_ewh_test_results(projekt_id, whk_configs, ms_nummer):
    """Füllt alle EWH-Testergebnisse aus"""

    # Alle EWH-Testfragen laden
    testfragen = TestQuestion.query.filter(
        TestQuestion.komponente_typ.in_(EWH_KOMPONENTEN)
    ).all()

    print(f"  Fülle {len(testfragen)} EWH-Testfragen...", flush=True)

    for frage in testfragen:
        komponente_typ = frage.komponente_typ

        # Bestimme Spalten basierend auf Komponente
        if komponente_typ == 'Anlage':
            # Eine Zeile für die gesamte Anlage
            # Format: komponente_index='', spalte='Anlage' (konsistent mit ewh.py POST-Handler)
            spalten_data = [('', 'Anlage')]

        elif komponente_typ == 'WHK':
            # Eine Zeile pro WHK
            spalten_data = [(whk.whk_nummer, whk.whk_nummer) for whk in whk_configs]

        elif komponente_typ == 'Abgang':
            # Mehrere Spalten pro WHK (je nach Anzahl Abgänge)
            spalten_data = []
            for whk in whk_configs:
                for a in range(1, whk.anzahl_abgaenge + 1):
                    spalten_data.append((whk.whk_nummer, f"Abgang {str(a).zfill(2)}"))

        elif komponente_typ == 'Temperatursonde':
            # Mehrere Spalten pro WHK (je nach Anzahl TS)
            spalten_data = []
            for whk in whk_configs:
                for ts in range(1, whk.anzahl_temperatursonden + 1):
                    spalten_data.append((whk.whk_nummer, f"TS {str(ts).zfill(2)}"))

        elif komponente_typ == 'Antriebsheizung':
            # Nur WHKs mit Antriebsheizung
            spalten_data = [(whk.whk_nummer, 'Antriebsheizung') for whk in whk_configs if whk.hat_antriebsheizung]

        elif komponente_typ == 'Meteostation':
            # Eine Zeile für die Meteostation
            spalten_data = [(ms_nummer, ms_nummer)]

        else:
            spalten_data = [('', komponente_typ)]

        # Ergebnisse erstellen
        for komponente_index, spalte in spalten_data:
            result = AbnahmeTestResult(
                projekt_id=projekt_id,
                test_question_id=frage.id,
                komponente_index=komponente_index,
                spalte=spalte,
                lss_ch_result=get_random_result(),
                wh_lts_result=get_random_result(),
                lss_ch_bemerkung=get_random_bemerkung(),
                wh_lts_bemerkung=get_random_bemerkung()
            )
            db.session.add(result)


def fill_gwh_test_results(projekt_id, zsk_configs, ms_nummer, has_hgls):
    """Füllt alle GWH-Testergebnisse aus"""

    # Alle GWH-Testfragen laden
    testfragen = TestQuestion.query.filter(
        TestQuestion.komponente_typ.in_(GWH_KOMPONENTEN)
    ).all()

    print(f"  Fülle {len(testfragen)} GWH-Testfragen...", flush=True)

    for frage in testfragen:
        komponente_typ = frage.komponente_typ

        # Bestimme Spalten basierend auf Komponente
        if komponente_typ == 'GWH_Anlage':
            # Eine Zeile für die gesamte Anlage
            spalten_data = [('Anlage', 'Anlage')]

        elif komponente_typ == 'HGLS':
            # Nur wenn HGLS vorhanden
            if has_hgls:
                spalten_data = [('HGLS', 'HGLS')]
            else:
                spalten_data = []

        elif komponente_typ == 'ZSK':
            # Eine Zeile pro ZSK
            spalten_data = [(zsk.zsk_nummer, zsk.zsk_nummer) for zsk in zsk_configs]

        elif komponente_typ == 'GWH_Teile':
            # Mehrere Spalten pro ZSK (je nach Anzahl Teile)
            spalten_data = []
            for zsk in zsk_configs:
                for t in range(1, zsk.anzahl_teile + 1):
                    spalten_data.append((zsk.zsk_nummer, f"Teil {str(t).zfill(2)}"))

        elif komponente_typ == 'GWH_Temperatursonde':
            # Eine TS pro ZSK (jeder ZSK hat eine TS)
            spalten_data = [(zsk.zsk_nummer, 'TS') for zsk in zsk_configs]

        elif komponente_typ == 'GWH_Meteostation':
            # Eine Zeile für die Meteostation
            spalten_data = [(ms_nummer, ms_nummer)]

        else:
            spalten_data = [('', komponente_typ)]

        # Ergebnisse erstellen
        for komponente_index, spalte in spalten_data:
            result = AbnahmeTestResult(
                projekt_id=projekt_id,
                test_question_id=frage.id,
                komponente_index=komponente_index,
                spalte=spalte,
                lss_ch_result=get_random_result(),
                wh_lts_result=get_random_result(),
                lss_ch_bemerkung=get_random_bemerkung(),
                wh_lts_bemerkung=get_random_bemerkung()
            )
            db.session.add(result)


def fill_gwh_parameter_pruefungen(projekt_id, zsk_configs):
    """Füllt HGLS und ZSK Parameter-Prüfungen"""

    print("  Fülle HGLS-Parameter...", flush=True)
    for param in HGLS_PARAMETER:
        pruefung = HGLSParameterPruefung(
            projekt_id=projekt_id,
            parameter_name=param['name'],
            ist_wert=str(random.randint(1, 100)),
            geprueft=True,
            nicht_testbar=False
        )
        db.session.add(pruefung)

    print("  Fülle ZSK-Parameter...", flush=True)
    for zsk in zsk_configs:
        for param in ZSK_PARAMETER:
            pruefung = ZSKParameterPruefung(
                projekt_id=projekt_id,
                zsk_nummer=zsk.zsk_nummer,
                parameter_name=param['name'],
                ist_wert=str(random.randint(1, 100)),
                geprueft=True,
                nicht_testbar=False
            )
            db.session.add(pruefung)


def create_ewh_project():
    """Erstellt EWH-Projekt mit 100% Testabschluss"""
    print("\n" + "=" * 50)
    print("Erstelle EWH-Projekt...")
    print("=" * 50, flush=True)

    # Prüfe ob schon existiert
    existing = Project.query.filter_by(projektname="PDF-Test EWH Zürich").first()
    if existing:
        print(f"  WARNUNG: Projekt existiert bereits (ID={existing.id}). Überspringe...", flush=True)
        return existing

    # Projekt anlegen
    projekt = Project(
        projektname="PDF-Test EWH Zürich",
        energie="EWH",
        didok_betriebspunkt=f"DIDOK-{random.randint(10000, 99999)}",
        projektleiter_sbb="Max Mustermann",
        pruefer_achermann="Hans Meier",
        pruefdatum=date.today(),
        baumappenversion=date.today()  # ist ein Date-Feld
    )
    db.session.add(projekt)
    db.session.flush()  # ID generieren
    print(f"  Projekt erstellt: ID={projekt.id}", flush=True)

    # WHKs konfigurieren (2-3 zufällig)
    num_whks = random.randint(2, 3)
    whk_configs = []
    print(f"  Erstelle {num_whks} WHKs...", flush=True)

    for i in range(num_whks):
        hat_ah = random.choice([True, False])
        whk = WHKConfig(
            projekt_id=projekt.id,
            whk_nummer=f"WHK {str(i+1).zfill(2)}",
            anzahl_abgaenge=random.randint(2, 5),
            anzahl_temperatursonden=random.randint(1, 2),
            hat_antriebsheizung=hat_ah
        )
        db.session.add(whk)
        whk_configs.append(whk)
        print(f"    - {whk.whk_nummer}: {whk.anzahl_abgaenge} Abgänge, {whk.anzahl_temperatursonden} TS, AH={'Ja' if hat_ah else 'Nein'}", flush=True)

    db.session.flush()

    # Meteostation
    ms_nummer = "MS 01"
    ms = EWHMeteostation(
        projekt_id=projekt.id,
        ms_nummer="01",
        zugeordnete_whk_id=whk_configs[0].id,
        reihenfolge=1
    )
    db.session.add(ms)
    print(f"  Meteostation erstellt: {ms_nummer} -> {whk_configs[0].whk_nummer}", flush=True)

    # Alle EWH-Tests ausfüllen
    fill_ewh_test_results(projekt.id, whk_configs, ms_nummer)

    db.session.commit()
    print(f"\n  EWH-Projekt erfolgreich erstellt: ID={projekt.id}", flush=True)
    return projekt


def create_gwh_project():
    """Erstellt GWH-Projekt mit 100% Testabschluss"""
    print("\n" + "=" * 50)
    print("Erstelle GWH-Projekt...")
    print("=" * 50, flush=True)

    # Prüfe ob schon existiert
    existing = Project.query.filter_by(projektname="PDF-Test GWH Basel").first()
    if existing:
        print(f"  WARNUNG: Projekt existiert bereits (ID={existing.id}). Überspringe...", flush=True)
        return existing

    # Projekt anlegen
    projekt = Project(
        projektname="PDF-Test GWH Basel",
        energie="GWH",
        didok_betriebspunkt=f"DIDOK-{random.randint(10000, 99999)}",
        projektleiter_sbb="Max Mustermann",
        pruefer_achermann="Hans Meier",
        pruefdatum=date.today(),
        baumappenversion=date.today()  # ist ein Date-Feld
    )
    db.session.add(projekt)
    db.session.flush()
    print(f"  Projekt erstellt: ID={projekt.id}", flush=True)

    # ZSKs konfigurieren (2-3 zufällig)
    num_zsks = random.randint(2, 3)
    zsk_configs = []
    print(f"  Erstelle {num_zsks} ZSKs...", flush=True)

    for i in range(num_zsks):
        gasv = random.choice(['zentral', 'dezentral'])
        zsk = ZSKConfig(
            projekt_id=projekt.id,
            zsk_nummer=f"ZSK {str(i+1).zfill(2)}",
            anzahl_teile=random.randint(1, 4),
            gasversorgung=gasv,
            reihenfolge=i+1
        )
        db.session.add(zsk)
        zsk_configs.append(zsk)
        print(f"    - {zsk.zsk_nummer}: {zsk.anzahl_teile} Teile, Gasversorgung={gasv}", flush=True)

    db.session.flush()

    # HGLS-Konfiguration
    hgls = HGLSConfig(
        projekt_id=projekt.id,
        hgls_typ=random.choice(['Propan', 'Erdgas']),
        hat_fuellventil=random.choice([True, False]),
        hat_bypassventil=random.choice([True, False]),
        hat_gaswarnanlage=random.choice([True, False]),
        hat_lueftungsanlage=random.choice([True, False]),
        hat_mengenmesser_blockade=random.choice([True, False]),
        hat_elektroverdampfer=random.choice([True, False]),
        gasverdampfer_anzahl=random.randint(0, 2),
        hat_tankdruckueberwachung=random.choice([True, False]),
        hat_tankberieselung=random.choice([True, False]),
        hat_kathodenschutz=random.choice([True, False])
    )
    db.session.add(hgls)
    print(f"  HGLS erstellt: Typ={hgls.hgls_typ}", flush=True)

    # Meteostation
    ms_nummer = "MS 01"
    ms = GWHMeteostation(
        projekt_id=projekt.id,
        ms_nummer="01",
        name="MS 01",
        zugeordneter_zsk_id=zsk_configs[0].id,
        modbus_adresse=50,
        reihenfolge=1
    )
    db.session.add(ms)
    print(f"  Meteostation erstellt: {ms_nummer} -> {zsk_configs[0].zsk_nummer}", flush=True)

    # Alle GWH-Tests ausfüllen
    fill_gwh_test_results(projekt.id, zsk_configs, ms_nummer, has_hgls=True)

    # Parameter-Prüfungen ausfüllen
    fill_gwh_parameter_pruefungen(projekt.id, zsk_configs)

    db.session.commit()
    print(f"\n  GWH-Projekt erfolgreich erstellt: ID={projekt.id}", flush=True)
    return projekt


def main():
    """Hauptfunktion"""
    print("\n" + "=" * 60)
    print("  PDF-Test Projekte erstellen")
    print("=" * 60, flush=True)

    with app.app_context():
        # EWH-Projekt erstellen
        ewh = create_ewh_project()

        # GWH-Projekt erstellen
        gwh = create_gwh_project()

        print("\n" + "=" * 60)
        print("  FERTIG!")
        print("=" * 60)
        print(f"\n  EWH-Projekt: {ewh.projektname} (ID={ewh.id})")
        print(f"  GWH-Projekt: {gwh.projektname} (ID={gwh.id})")
        print("\n  Die Projekte können jetzt in der Anwendung geöffnet werden.")
        print("  Navigiere zu 'Projekte' und wähle eines der Test-Projekte aus.")
        print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
