"""Direkte Migration: Fügt ibn_inbetriebnahme_jahre Spalte hinzu."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'whs.db')
print(f"Datenbank: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Prüfen ob Spalte existiert
cursor.execute('PRAGMA table_info(projects)')
columns = [col[1] for col in cursor.fetchall()]
print(f"Vorhandene Spalten: {columns}")

if 'ibn_inbetriebnahme_jahre' not in columns:
    cursor.execute('ALTER TABLE projects ADD COLUMN ibn_inbetriebnahme_jahre VARCHAR(200)')
    conn.commit()
    print("Spalte ibn_inbetriebnahme_jahre erfolgreich hinzugefuegt!")
else:
    print("Spalte existiert bereits.")

conn.close()
print("Fertig!")
