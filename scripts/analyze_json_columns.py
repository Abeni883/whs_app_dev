"""
Analysiert welche Spalten (A, B, C) für jede Komponente im JSON vorhanden sind
"""
import sys
import os
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         'Alte Projekte', 'Bowil BOW.json')

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

abgaenge_data = data.get('abgaenge', {})

print("=" * 80)
print("SPALTEN-ANALYSE PRO KOMPONENTE")
print("=" * 80)

for komponente, komponente_data in abgaenge_data.items():
    print(f"\n### {komponente} ###")

    # Beispiel-Frage nehmen
    if komponente == 'ANLAGE' or komponente == 'WHK':
        # Direkte Fragenstruktur
        erste_frage_key = list(komponente_data.keys())[0]
        erste_frage = komponente_data[erste_frage_key]
    else:
        # WHK-Ebene vorhanden
        if komponente_data:
            erste_whk_key = list(komponente_data.keys())[0]
            erste_whk = komponente_data[erste_whk_key]
            if erste_whk:
                erste_frage_key = list(erste_whk.keys())[0]
                erste_frage = erste_whk[erste_frage_key]
            else:
                print("  Keine Daten")
                continue
        else:
            print("  Keine Daten")
            continue

    auswahl = erste_frage.get('auswahl', {})
    spalten = list(auswahl.keys())

    print(f"  Vorhandene Spalten: {', '.join(spalten)}")

    # Beispielwerte zeigen
    for spalte in spalten:
        if '0' in auswahl[spalte]:
            wert = auswahl[spalte]['0']
        elif isinstance(auswahl[spalte], dict) and auswahl[spalte]:
            erster_key = list(auswahl[spalte].keys())[0]
            wert = auswahl[spalte][erster_key]
        else:
            wert = "?"
        print(f"    Spalte {spalte}: {wert}")

print("\n" + "=" * 80)
print("INTERPRETATION:")
print("=" * 80)
print("Spalte A -> LSS-CH")
print("Spalte B -> WH-LTS")
print("Spalte C -> Ignoriert")
