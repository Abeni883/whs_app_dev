"""
Vollständige Analyse des JSON-Files mit allen Details
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

print("=" * 80)
print("VOLLSTÄNDIGE JSON-ANALYSE")
print("=" * 80)

# Hauptschlüssel
print("\nHauptschlüssel im JSON:")
for key in data.keys():
    print(f"  - {key}")

# Abgaenge-Daten
abgaenge_data = data.get('abgaenge', {})

print("\n" + "=" * 80)
print("KOMPONENTEN IM 'abgaenge'-BEREICH:")
print("=" * 80)

for komponente_key in abgaenge_data.keys():
    print(f"\n### {komponente_key} ###")

# Detaillierte Analyse pro Komponente
print("\n" + "=" * 80)
print("DETAILLIERTE STRUKTUR PRO KOMPONENTE:")
print("=" * 80)

for komponente_key, komponente_data in abgaenge_data.items():
    print(f"\n### {komponente_key} ###")

    if not komponente_data:
        print("  LEER")
        continue

    # Erste Ebene
    erste_ebene_keys = list(komponente_data.keys())
    print(f"  Erste Ebene Keys: {erste_ebene_keys[:5]}... (total: {len(erste_ebene_keys)})")

    # Prüfe ob es WHK-Ebene oder direkt Fragen-Ebene ist
    erster_key = erste_ebene_keys[0]
    erste_ebene_data = komponente_data[erster_key]

    if isinstance(erste_ebene_data, dict):
        if 'auswahl' in erste_ebene_data:
            print(f"  Struktur: DIREKT FRAGEN (keine WHK-Ebene)")
            print(f"  Anzahl Fragen: {len(erste_ebene_keys)}")

            # Beispiel-Frage
            auswahl = erste_ebene_data.get('auswahl', {})
            spalten = list(auswahl.keys())
            print(f"  Spalten in Frage {erster_key}: {spalten}")

            # Zeige Werte für jede Spalte
            for spalte in spalten:
                if isinstance(auswahl[spalte], dict):
                    werte = list(auswahl[spalte].values())
                    print(f"    Spalte {spalte}: {werte[:3]}{'...' if len(werte) > 3 else ''}")
                else:
                    print(f"    Spalte {spalte}: {auswahl[spalte]}")
        else:
            print(f"  Struktur: MIT WHK-EBENE")
            print(f"  Anzahl WHKs: {len(erste_ebene_keys)}")

            # Schaue in erste WHK
            if erste_ebene_data:
                zweite_ebene_keys = list(erste_ebene_data.keys())
                print(f"  Anzahl Fragen in WHK {erster_key}: {len(zweite_ebene_keys)}")

                # Beispiel-Frage
                erste_frage_key = zweite_ebene_keys[0]
                erste_frage = erste_ebene_data[erste_frage_key]

                if isinstance(erste_frage, dict) and 'auswahl' in erste_frage:
                    auswahl = erste_frage.get('auswahl', {})
                    spalten = list(auswahl.keys())
                    print(f"  Spalten in Frage {erste_frage_key}: {spalten}")

                    # Zeige Werte für jede Spalte
                    for spalte in spalten:
                        if isinstance(auswahl[spalte], dict):
                            werte = list(auswahl[spalte].values())
                            print(f"    Spalte {spalte}: {werte[:3]}{'...' if len(werte) > 3 else ''}")
                        else:
                            print(f"    Spalte {spalte}: {auswahl[spalte]}")

# Zähle Fragen pro Komponente
print("\n" + "=" * 80)
print("ANZAHL FRAGEN PRO KOMPONENTE:")
print("=" * 80)

for komponente_key, komponente_data in abgaenge_data.items():
    if not komponente_data:
        print(f"{komponente_key:20s}: 0 Fragen")
        continue

    erste_ebene_keys = list(komponente_data.keys())
    erster_key = erste_ebene_keys[0]
    erste_ebene_data = komponente_data[erster_key]

    if isinstance(erste_ebene_data, dict) and 'auswahl' in erste_ebene_data:
        # Direkt Fragen
        print(f"{komponente_key:20s}: {len(erste_ebene_keys)} Fragen (direkt)")
    else:
        # Mit WHK-Ebene
        total_fragen = 0
        for whk_key, whk_data in komponente_data.items():
            if isinstance(whk_data, dict):
                total_fragen += len(whk_data)
        print(f"{komponente_key:20s}: {total_fragen} Fragen (über {len(erste_ebene_keys)} WHK(s))")

print("\n" + "=" * 80)
