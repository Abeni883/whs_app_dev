"""
Einfaches Migrations-Skript für SQLite (ohne Flask-Abhängigkeiten).
"""
import sqlite3
import os

# Pfad zur Datenbank
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'whs.db')

if not os.path.exists(db_path):
    print(f"[ERROR] Datenbank nicht gefunden: {db_path}")
    exit(1)

print(f"[INFO] Verbinde mit Datenbank: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Prüfe ob erwartetes_ergebnis bereits existiert
    cursor.execute("PRAGMA table_info(test_questions)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'erwartetes_ergebnis' in columns:
        print("[INFO] Spalte 'erwartetes_ergebnis' existiert bereits")
    else:
        print("[MIGRATION] Füge Spalte 'erwartetes_ergebnis' hinzu...")
        cursor.execute("ALTER TABLE test_questions ADD COLUMN erwartetes_ergebnis TEXT")
        print("[OK] Spalte 'erwartetes_ergebnis' hinzugefügt")

    if 'screenshot_pfad' in columns:
        print("[INFO] Spalte 'screenshot_pfad' existiert bereits")
    else:
        print("[MIGRATION] Füge Spalte 'screenshot_pfad' hinzu...")
        cursor.execute("ALTER TABLE test_questions ADD COLUMN screenshot_pfad VARCHAR(255)")
        print("[OK] Spalte 'screenshot_pfad' hinzugefügt")

    conn.commit()
    print("\n[SUCCESS] Migration erfolgreich abgeschlossen!")

except Exception as e:
    print(f"\n[ERROR] Migration fehlgeschlagen: {e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()
