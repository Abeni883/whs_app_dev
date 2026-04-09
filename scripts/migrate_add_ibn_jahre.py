#!/usr/bin/env python
"""
Migration Script: Fügt die Spalte 'ibn_inbetriebnahme_jahre' zur projects-Tabelle hinzu.

Ausführen mit:
    python scripts/migrate_add_ibn_jahre.py

Dieses Script ist idempotent - kann mehrfach ausgeführt werden ohne Fehler.
"""

import sqlite3
import os
import sys

# Pfad zur Datenbank
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'whs.db')


def migrate():
    """Fügt die neue Spalte zur Datenbank hinzu, falls sie nicht existiert."""
    print(f"Verbinde mit Datenbank: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("FEHLER: Datenbank nicht gefunden!")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Prüfen ob Spalte existiert
        cursor.execute('PRAGMA table_info(projects)')
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Vorhandene Spalten: {columns}")

        if 'ibn_inbetriebnahme_jahre' not in columns:
            print("\nFüge Spalte 'ibn_inbetriebnahme_jahre' hinzu...")
            cursor.execute('ALTER TABLE projects ADD COLUMN ibn_inbetriebnahme_jahre VARCHAR(200)')
            conn.commit()
            print("✓ Spalte erfolgreich hinzugefügt!")
        else:
            print("\n✓ Spalte 'ibn_inbetriebnahme_jahre' existiert bereits.")

        # Verifizieren
        cursor.execute('PRAGMA table_info(projects)')
        columns_after = [col[1] for col in cursor.fetchall()]
        print(f"\nAktuelle Spalten: {columns_after}")

    except Exception as e:
        print(f"FEHLER: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

    print("\nMigration erfolgreich abgeschlossen!")


if __name__ == '__main__':
    migrate()
