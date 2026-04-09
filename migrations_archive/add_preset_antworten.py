"""
Datenbank-Migration: Füge 'preset_antworten' Spalte zur test_questions-Tabelle hinzu
"""
import pymysql

# Datenbankverbindung
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='a&Dvi8q4W4!&HiP*',
    database='abnahmetest'
)

try:
    cursor = connection.cursor()

    print("=== Datenbank-Migration: test_questions-Tabelle ===\n")

    # Prüfe ob Spalte bereits existiert
    cursor.execute("SHOW COLUMNS FROM test_questions LIKE 'preset_antworten'")
    result = cursor.fetchone()

    if result:
        print("Spalte 'preset_antworten' existiert bereits!")
    else:
        print("Füge Spalte 'preset_antworten' hinzu...")
        cursor.execute("""
            ALTER TABLE test_questions
            ADD COLUMN preset_antworten JSON NULL
            AFTER reihenfolge
        """)
        connection.commit()
        print("[OK] Spalte 'preset_antworten' erfolgreich hinzugefügt!\n")

    print("=== Migration erfolgreich abgeschlossen! ===")

except Exception as e:
    print(f"\n[FEHLER] Fehler bei der Migration: {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()
