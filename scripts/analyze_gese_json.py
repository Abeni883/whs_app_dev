"""
Analysiert die JSON-Struktur von GESE
"""
import sys
import os
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         'Alte Projekte', 'Gèneve-Sécheron GESE.json')

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("GESE JSON-ANALYSE")
print("=" * 80)

# WHK-Konfiguration (felder)
felder = data.get('felder', [])
print(f"\nWHK-Konfigurationen (felder): {len(felder)}")
for idx, feld in enumerate(felder):
    print(f"  Index {idx}: {feld.get('name')} - {feld.get('abgang')} ABG, {feld.get('temp')} TS, MS: {feld.get('meteo')}")

# Abgänge-Daten
abgaenge_data = data.get('abgaenge', {})

print("\n" + "=" * 80)
print("WHK-DATEN IM JSON")
print("=" * 80)

if 'WHK' in abgaenge_data:
    whk_data = abgaenge_data['WHK']
    print(f"\nWHK-Keys (direkte Fragen-Ebene): {list(whk_data.keys())[:10]}")
    print(f"Total Fragen: {len(whk_data)}")

    # Erste Frage anschauen
    first_key = list(whk_data.keys())[0]
    first_frage = whk_data[first_key]
    print(f"\nBeispiel Frage {first_key}:")
    print(f"  auswahl Keys: {list(first_frage.get('auswahl', {}).keys())}")

    # Prüfe ob es Spalten gibt
    if 'auswahl' in first_frage:
        auswahl = first_frage['auswahl']
        for spalte_key in list(auswahl.keys())[:3]:
            spalte_data = auswahl[spalte_key]
            print(f"  Spalte {spalte_key}: {spalte_data}")

print("\n" + "=" * 80)
print("ABG-DATEN IM JSON (WHK-Ebene)")
print("=" * 80)

if 'ABG' in abgaenge_data:
    abg_data = abgaenge_data['ABG']
    print(f"\nWHK-Indizes: {list(abg_data.keys())}")

    for whk_idx_str in list(abg_data.keys()):
        whk_idx = int(whk_idx_str)
        whk_fragen = abg_data[whk_idx_str]

        # Erste Frage dieser WHK
        first_frage_key = list(whk_fragen.keys())[0]
        first_frage = whk_fragen[first_frage_key]

        # Anzahl Abgänge ermitteln
        anzahl_abg = 0
        if 'auswahl' in first_frage and 'A' in first_frage['auswahl']:
            anzahl_abg = len(first_frage['auswahl']['A'])

        print(f"  WHK-Index {whk_idx}: {len(whk_fragen)} Fragen, {anzahl_abg} Abgänge")

print("\n" + "=" * 80)
print("MAPPING-PROBLEM:")
print("=" * 80)
print("\nAktuelles Script:")
print("  WHK-Index 0 -> WHK 01")
print("  WHK-Index 1 -> WHK 02")
print("  usw.")
print("\nAber GESE hat:")
for idx, feld in enumerate(felder):
    print(f"  WHK-Index {idx} -> {feld.get('name')}")
