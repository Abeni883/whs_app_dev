#!/usr/bin/env python
"""
Migration Script: Erstellt die Tabelle 'testabschluss_items' und fügt initiale Daten hinzu.

Ausführen mit:
    python scripts/migrate_add_testabschluss_items.py

Dieses Script ist idempotent - kann mehrfach ausgeführt werden ohne Fehler.
"""

import sqlite3
import os
import sys

# Pfad zur Datenbank
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'whs.db')


def migrate():
    """Erstellt die Tabelle und fügt initiale Daten hinzu, falls nicht vorhanden."""
    print(f"Verbinde mit Datenbank: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("FEHLER: Datenbank nicht gefunden!")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Prüfen ob Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='testabschluss_items'")
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            print("\nErstelle Tabelle 'testabschluss_items'...")
            cursor.execute('''
                CREATE TABLE testabschluss_items (
                    id INTEGER PRIMARY KEY,
                    energie_typ VARCHAR(10) NOT NULL,
                    titel VARCHAR(200) NOT NULL,
                    beschreibung TEXT NOT NULL,
                    highlight_text VARCHAR(100),
                    reihenfolge INTEGER NOT NULL DEFAULT 0,
                    aktiv BOOLEAN DEFAULT 1,
                    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
                    geaendert_am DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX ix_testabschluss_items_energie_typ ON testabschluss_items(energie_typ)')
            cursor.execute('CREATE INDEX ix_testabschluss_items_reihenfolge ON testabschluss_items(reihenfolge)')
            cursor.execute('CREATE INDEX ix_testabschluss_items_aktiv ON testabschluss_items(aktiv)')
            conn.commit()
            print("OK: Tabelle erfolgreich erstellt!")
        else:
            print("\nOK: Tabelle 'testabschluss_items' existiert bereits.")

        # Prüfe ob initiale Daten vorhanden sind
        cursor.execute('SELECT COUNT(*) FROM testabschluss_items')
        count = cursor.fetchone()[0]

        if count == 0:
            print("\nFuege initiale EWH-Daten hinzu...")
            initial_data = [
                ('EWH', 'Freigabe deaktivieren',
                 'Die WH-Anlage muss nach dem Abnahmetest auf {highlight} geschaltet werden.',
                 'Freigabe Aus', 1, 1),
                ('EWH', 'LSS-CH Meldung deaktivieren',
                 'Die WH-Anlage muss nach dem Abnahmetest auf {highlight} geschaltet werden.',
                 'Meldung an LSS-CH Aus', 2, 1),
                ('EWH', 'Betriebszentrale Einschaltdauer',
                 'Falls die Einschaltdauer der Betriebszentrale veraendert wurde, muss sie wieder auf den {highlight} gesetzt werden.',
                 'Standardwert', 3, 1)
            ]

            cursor.executemany('''
                INSERT INTO testabschluss_items (energie_typ, titel, beschreibung, highlight_text, reihenfolge, aktiv)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', initial_data)
            conn.commit()
            print(f"OK: {len(initial_data)} EWH-Eintraege eingefuegt!")
        else:
            print(f"\nOK: {count} Eintraege bereits vorhanden - keine Daten eingefuegt.")

        # Verifizieren
        cursor.execute('SELECT id, energie_typ, titel FROM testabschluss_items ORDER BY energie_typ, reihenfolge')
        rows = cursor.fetchall()
        print(f"\nAktuelle Eintraege ({len(rows)}):")
        for row in rows:
            print(f"  - [{row[0]}] {row[1]}: {row[2]}")

    except Exception as e:
        print(f"FEHLER: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

    print("\nMigration erfolgreich abgeschlossen!")


if __name__ == '__main__':
    migrate()
