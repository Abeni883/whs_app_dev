#!/usr/bin/env python3
"""
Script zur Bereinigung der Datenbank von doppelten Präfixen.

Behebt:
1. AbnahmeTestResult.komponente_index: "ZSK ZSK 01" -> "ZSK 01"
2. AbnahmeTestResult.komponente_index: "MS MS 01" -> "MS 01"
3. AbnahmeTestResult.spalte: "ZSK ZSK 01" -> "ZSK 01"
4. AbnahmeTestResult.spalte: "MS MS 01" -> "MS 01"
5. GWHMeteostation.name: "MS MS 01" -> "MS 01"

Verwendung:
    python scripts/fix_double_prefix.py
"""

import sys
import os

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import AbnahmeTestResult, GWHMeteostation


def fix_database():
    """Bereinigt die Datenbank von doppelten Präfixen."""

    with app.app_context():
        print("=" * 60)
        print("Datenbank-Bereinigung: Doppelte Präfixe entfernen")
        print("=" * 60)

        total_fixed = 0

        # 1. Fix AbnahmeTestResult.komponente_index mit "ZSK ZSK"
        print("\n1. AbnahmeTestResult.komponente_index mit 'ZSK ZSK'...")
        wrong_ki_zsk = AbnahmeTestResult.query.filter(
            AbnahmeTestResult.komponente_index.like('ZSK ZSK%')
        ).all()
        print(f"   Gefunden: {len(wrong_ki_zsk)} Einträge")

        for result in wrong_ki_zsk:
            old_value = result.komponente_index
            new_value = old_value.replace('ZSK ZSK', 'ZSK')
            result.komponente_index = new_value
            print(f"   Fix: '{old_value}' -> '{new_value}'")
            total_fixed += 1

        # 2. Fix AbnahmeTestResult.komponente_index mit "MS MS"
        print("\n2. AbnahmeTestResult.komponente_index mit 'MS MS'...")
        wrong_ki_ms = AbnahmeTestResult.query.filter(
            AbnahmeTestResult.komponente_index.like('MS MS%')
        ).all()
        print(f"   Gefunden: {len(wrong_ki_ms)} Einträge")

        for result in wrong_ki_ms:
            old_value = result.komponente_index
            new_value = old_value.replace('MS MS', 'MS')
            result.komponente_index = new_value
            print(f"   Fix: '{old_value}' -> '{new_value}'")
            total_fixed += 1

        # 3. Fix AbnahmeTestResult.spalte mit "ZSK ZSK"
        print("\n3. AbnahmeTestResult.spalte mit 'ZSK ZSK'...")
        wrong_sp_zsk = AbnahmeTestResult.query.filter(
            AbnahmeTestResult.spalte.like('ZSK ZSK%')
        ).all()
        print(f"   Gefunden: {len(wrong_sp_zsk)} Einträge")

        for result in wrong_sp_zsk:
            old_value = result.spalte
            new_value = old_value.replace('ZSK ZSK', 'ZSK')
            result.spalte = new_value
            print(f"   Fix: '{old_value}' -> '{new_value}'")
            total_fixed += 1

        # 4. Fix AbnahmeTestResult.spalte mit "MS MS"
        print("\n4. AbnahmeTestResult.spalte mit 'MS MS'...")
        wrong_sp_ms = AbnahmeTestResult.query.filter(
            AbnahmeTestResult.spalte.like('MS MS%')
        ).all()
        print(f"   Gefunden: {len(wrong_sp_ms)} Einträge")

        for result in wrong_sp_ms:
            old_value = result.spalte
            new_value = old_value.replace('MS MS', 'MS')
            result.spalte = new_value
            print(f"   Fix: '{old_value}' -> '{new_value}'")
            total_fixed += 1

        # 5. Fix GWHMeteostation.name mit "MS MS"
        print("\n5. GWHMeteostation.name mit 'MS MS'...")
        wrong_ms_name = GWHMeteostation.query.filter(
            GWHMeteostation.name.like('MS MS%')
        ).all()
        print(f"   Gefunden: {len(wrong_ms_name)} Einträge")

        for ms in wrong_ms_name:
            old_value = ms.name
            new_value = old_value.replace('MS MS', 'MS')
            ms.name = new_value
            print(f"   Fix: '{old_value}' -> '{new_value}' (Projekt {ms.projekt_id})")
            total_fixed += 1

        # Änderungen speichern
        if total_fixed > 0:
            db.session.commit()
            print(f"\n{'=' * 60}")
            print(f"FERTIG: {total_fixed} Einträge korrigiert!")
            print("=" * 60)
        else:
            print(f"\n{'=' * 60}")
            print("Keine fehlerhaften Einträge gefunden - alles OK!")
            print("=" * 60)

        # Zeige aktuelle Werte zur Überprüfung
        print("\n\nAktuelle eindeutige Werte in AbnahmeTestResult:")
        print("-" * 60)

        ki_values = db.session.query(
            AbnahmeTestResult.komponente_index
        ).distinct().all()
        print(f"komponente_index: {[v[0] for v in ki_values]}")

        sp_values = db.session.query(
            AbnahmeTestResult.spalte
        ).distinct().all()
        print(f"spalte: {[v[0] for v in sp_values]}")

        print("\nAktuelle GWHMeteostation Namen:")
        print("-" * 60)
        ms_all = GWHMeteostation.query.all()
        for ms in ms_all:
            print(f"  Projekt {ms.projekt_id}: ms_nummer='{ms.ms_nummer}', name='{ms.name}'")


if __name__ == '__main__':
    fix_database()
