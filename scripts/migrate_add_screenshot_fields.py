"""
Migrations-Skript: Fügt erwartetes_ergebnis und screenshot_pfad Felder zur test_questions Tabelle hinzu.

Führe dieses Skript aus mit:
    python scripts/migrate_add_screenshot_fields.py
"""

import sys
import os

# Füge parent directory zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db

def migrate():
    with app.app_context():
        try:
            # Prüfe ob die Spalten bereits existieren
            with db.engine.connect() as conn:
                # Versuche eine Abfrage auf die neue Spalte
                try:
                    result = conn.execute(db.text("SELECT erwartetes_ergebnis FROM test_questions LIMIT 1"))
                    result.close()
                    print("[INFO] Spalte 'erwartetes_ergebnis' existiert bereits")
                except Exception:
                    print("[MIGRATION] Füge Spalte 'erwartetes_ergebnis' hinzu...")
                    conn.execute(db.text("ALTER TABLE test_questions ADD COLUMN erwartetes_ergebnis TEXT"))
                    conn.commit()
                    print("[OK] Spalte 'erwartetes_ergebnis' hinzugefügt")

                try:
                    result = conn.execute(db.text("SELECT screenshot_pfad FROM test_questions LIMIT 1"))
                    result.close()
                    print("[INFO] Spalte 'screenshot_pfad' existiert bereits")
                except Exception:
                    print("[MIGRATION] Füge Spalte 'screenshot_pfad' hinzu...")
                    conn.execute(db.text("ALTER TABLE test_questions ADD COLUMN screenshot_pfad VARCHAR(255)"))
                    conn.commit()
                    print("[OK] Spalte 'screenshot_pfad' hinzugefügt")

            print("\n[SUCCESS] Migration erfolgreich abgeschlossen!")
            print("Neue Felder:")
            print("  - erwartetes_ergebnis (TEXT)")
            print("  - screenshot_pfad (VARCHAR(255))")

        except Exception as e:
            print(f"\n[ERROR] Migration fehlgeschlagen: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    migrate()
