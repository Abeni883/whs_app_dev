#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script zum Hinzufügen von Test-Informationen zu allen Testfragen
"""

from app import app, db
from models import TestQuestion

# Mapping von Fragenummer zu Test-Information
TEST_INFOS = {
    1: "Prüfen Sie den Anlagennamen auf dem Display und in der Dokumentation",
    2: "Vergleichen Sie die DIDOK-Bezeichnung mit den Planungsunterlagen",
    3: "Kontrollieren Sie die DDC Station-Nummer im System",
    4: "Zählen Sie die tatsächlich vorhandenen Kabinen und vergleichen Sie mit der Konfiguration",
    5: "Überprüfen Sie die Anzahl der installierten Meteostationen",
    6: "Testen Sie die Kommunikation zwischen den Systemen",
    7: "Prüfen Sie die Netzwerkverbindung und IP-Adressen",
    8: "Kontrollieren Sie die Spannungsversorgung und Absicherung",
    9: "Testen Sie die Alarmweiterleitung an die Leitstelle",
    10: "Überprüfen Sie die Heizleistung bei verschiedenen Temperaturen",
}

# Generische Test-Informationen nach Komponententyp
GENERIC_INFOS = {
    'Anlage': 'Überprüfen Sie die System-Konfiguration und Kommunikation',
    'WHK': 'Testen Sie die WHK-Funktion und Kommunikation mit der Zentrale',
    'Abgang': 'Prüfen Sie die Heizkreis-Funktion und Temperaturregelung',
    'Temperatursonde': 'Kontrollieren Sie die Temperaturmessung und Genauigkeit',
    'Antriebsheizung': 'Testen Sie die Antriebsheizung bei verschiedenen Temperaturen',
    'Meteostation': 'Überprüfen Sie die Wetterdaten und deren Übertragung'
}

def add_test_information():
    with app.app_context():
        questions = TestQuestion.query.all()
        print(f"Gefundene Testfragen: {len(questions)}")

        updated = 0
        for question in questions:
            if question.test_information:
                continue  # Bereits vorhanden

            # Verwende spezifische Info falls vorhanden, sonst generische
            if question.frage_nummer in TEST_INFOS:
                info = TEST_INFOS[question.frage_nummer]
            else:
                # Verwende generische Info basierend auf Komponententyp
                info = GENERIC_INFOS.get(
                    question.komponente_typ,
                    'Fuehren Sie die Pruefung gemaess Testplan durch'
                )

            question.test_information = info
            updated += 1

        db.session.commit()
        print(f"\nErfolgreich: {updated} Testfragen mit Test-Information aktualisiert!")

if __name__ == '__main__':
    add_test_information()
