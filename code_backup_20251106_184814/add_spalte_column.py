"""
Migration: Füge 'spalte' Spalte zur abnahme_test_results Tabelle hinzu
"""
import pymysql

connection = pymysql.connect(
    host='localhost',
    user='root',
    password='a&Dvi8q4W4!&HiP*',
    database='abnahmetest'
)

try:
    cursor = connection.cursor()

    # Prüfe ob Spalte bereits existiert
    cursor.execute("SHOW COLUMNS FROM abnahme_test_results LIKE 'spalte'")
    result = cursor.fetchone()

    if not result:
        print("Füge 'spalte' Spalte hinzu...")
        cursor.execute("""
            ALTER TABLE abnahme_test_results
            ADD COLUMN spalte VARCHAR(100) NULL
            AFTER komponente_index
        """)
        connection.commit()
        print("[OK] Spalte 'spalte' erfolgreich hinzugefügt!")

        # Lösche alle bestehenden Daten (sie sind jetzt veraltet)
        cursor.execute("DELETE FROM abnahme_test_results")
        connection.commit()
        print("[INFO] Alle Test-Ergebnisse wurden gelöscht (müssen neu eingegeben werden)")
    else:
        print("Spalte 'spalte' existiert bereits!")

except Exception as e:
    print(f"[FEHLER] Fehler bei der Migration: {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()

print("\nBitte gebe alle Tests neu ein!")
