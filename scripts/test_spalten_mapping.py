"""
Testet verschiedene Spalten-Mappings für ANLAGE
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
print("SPALTEN-MAPPING TEST")
print("=" * 80)

# ANLAGE
print("\n### ANLAGE ###")
print("Erste 5 Fragen mit allen Spalten-Werten:\n")

anlage_data = abgaenge_data.get('ANLAGE', {})

for i in range(min(5, len(anlage_data))):
    frage_data = anlage_data[str(i)]
    auswahl = frage_data.get('auswahl', {})

    print(f"Frage {i}:")
    if 'C' in auswahl and '0' in auswahl['C']:
        print(f"  Spalte C: {auswahl['C']['0']}")
    if 'B' in auswahl and '0' in auswahl['B']:
        print(f"  Spalte B: {auswahl['B']['0']}")
    if 'A' in auswahl and '0' in auswahl['A']:
        print(f"  Spalte A: {auswahl['A']['0']}")
    else:
        print(f"  Spalte A: FEHLT")
    print()

print("\n" + "=" * 80)
print("MÖGLICHE INTERPRETATIONEN FÜR ANLAGE:")
print("=" * 80)
print("\nOption 1 (aktuell):")
print("  Spalte A -> LSS-CH (FEHLT)")
print("  Spalte B -> WH-LTS")
print("  Spalte C -> Ignoriert")

print("\nOption 2 (NEU):")
print("  Spalte C -> LSS-CH")
print("  Spalte B -> WH-LTS")
print("  Spalte A -> nicht vorhanden")

print("\n" + "=" * 80)
print("### MS (METEOSTATION) ###")
print("Erste 5 Fragen mit allen Spalten-Werten:\n")

ms_data = abgaenge_data.get('MS', {})

# MS hat WHK-Ebene
whk_0_data = ms_data.get('0', {})

for i in range(min(5, len(whk_0_data))):
    frage_data = whk_0_data[str(i)]
    auswahl = frage_data.get('auswahl', {})

    print(f"Frage {i}:")
    if 'C' in auswahl and '0' in auswahl['C']:
        print(f"  Spalte C: {auswahl['C']['0']}")
    if 'B' in auswahl and '0' in auswahl['B']:
        print(f"  Spalte B: {auswahl['B']['0']}")
    if 'A' in auswahl and '0' in auswahl['A']:
        print(f"  Spalte A: {auswahl['A']['0']}")
    print()

print("\n" + "=" * 80)
print("INTERPRETATION FÜR MS:")
print("=" * 80)
print("\nAktuell:")
print("  Spalte A -> LSS-CH")
print("  Spalte B -> WH-LTS")
print("  Spalte C -> Ignoriert")
print("\nStatus: MS wurde bereits korrekt importiert!")
