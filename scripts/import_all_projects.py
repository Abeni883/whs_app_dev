"""
Importiert alle Projekte aus dem "Alte Projekte" Ordner
"""
import sys
import os
import io
import glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from scripts.import_json_project import import_projekt

# Alle JSON-Dateien im Alte Projekte Ordner
projekt_ordner = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Alte Projekte')
json_files = glob.glob(os.path.join(projekt_ordner, '*.json'))

print("=" * 80)
print(f"BATCH-IMPORT ALLER PROJEKTE")
print("=" * 80)
print(f"\nGefundene Projekte: {len(json_files)}")
for f in json_files:
    print(f"  - {os.path.basename(f)}")

erfolgreiche = []
fehlgeschlagene = []

print("\n" + "=" * 80)
print("STARTE IMPORT")
print("=" * 80)

for idx, json_file in enumerate(json_files, 1):
    projekt_name = os.path.basename(json_file)
    print(f"\n[{idx}/{len(json_files)}] {projekt_name}")
    print("-" * 80)

    try:
        with app.app_context():
            success = import_projekt(json_file, force=False)

            if success:
                erfolgreiche.append(projekt_name)
            else:
                fehlgeschlagene.append(projekt_name)
    except Exception as e:
        print(f"⚠ FEHLER: {e}")
        fehlgeschlagene.append(projekt_name)

print("\n" + "=" * 80)
print("ZUSAMMENFASSUNG")
print("=" * 80)
print(f"\nErfolgreich importiert: {len(erfolgreiche)}")
for p in erfolgreiche:
    print(f"  ✓ {p}")

if fehlgeschlagene:
    print(f"\nFehlgeschlagen: {len(fehlgeschlagene)}")
    for p in fehlgeschlagene:
        print(f"  ⚠ {p}")

print(f"\n✓ BATCH-IMPORT ABGESCHLOSSEN!")
print(f"Total: {len(erfolgreiche)}/{len(json_files)} erfolgreich")
