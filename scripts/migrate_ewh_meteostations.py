"""
Migration: EWH Meteostations Tabelle erstellen
Erstellt die neue ewh_meteostations Tabelle für EWH-Projekte
"""
import sqlite3
import os

# Datenbankpfad
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'whs.db')

def migrate():
    """Erstellt die ewh_meteostations Tabelle"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Prüfe ob Tabelle bereits existiert
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='ewh_meteostations'
    """)

    if cursor.fetchone():
        print("Tabelle 'ewh_meteostations' existiert bereits.")
        conn.close()
        return

    # Erstelle die Tabelle
    cursor.execute("""
        CREATE TABLE ewh_meteostations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projekt_id INTEGER NOT NULL,
            zugeordnete_whk_id INTEGER,
            ms_nummer VARCHAR(20) NOT NULL,
            reihenfolge INTEGER NOT NULL DEFAULT 0,
            erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (projekt_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (zugeordnete_whk_id) REFERENCES whk_configs(id) ON DELETE SET NULL,
            UNIQUE (projekt_id, ms_nummer)
        )
    """)

    # Erstelle Indizes
    cursor.execute("""
        CREATE INDEX ix_ewh_meteostations_projekt_id ON ewh_meteostations(projekt_id)
    """)
    cursor.execute("""
        CREATE INDEX ix_ewh_meteostations_zugeordnete_whk_id ON ewh_meteostations(zugeordnete_whk_id)
    """)
    cursor.execute("""
        CREATE INDEX ix_ewh_meteostations_reihenfolge ON ewh_meteostations(reihenfolge)
    """)

    conn.commit()
    conn.close()

    print("Tabelle 'ewh_meteostations' erfolgreich erstellt!")

if __name__ == '__main__':
    migrate()
