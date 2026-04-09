"""
Datenbank-Update: Füge 'energie' Spalte zur projects-Tabelle hinzu
"""
import pymysql
from urllib.parse import quote_plus

# Datenbankverbindung
password = quote_plus('a&Dvi8q4W4!&HiP*')
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='a&Dvi8q4W4!&HiP*',
    database='abnahmetest'
)

try:
    cursor = connection.cursor()

    print("=== Datenbank-Update: Projects-Tabelle ===\n")

    # Prüfe ob Spalte bereits existiert
    cursor.execute("SHOW COLUMNS FROM projects LIKE 'energie'")
    result = cursor.fetchone()

    if result:
        print("Spalte 'energie' existiert bereits!")
    else:
        print("Füge Spalte 'energie' hinzu...")
        cursor.execute("""
            ALTER TABLE projects
            ADD COLUMN energie VARCHAR(10) NOT NULL DEFAULT 'EWH'
            AFTER id
        """)
        connection.commit()
        print("[OK] Spalte 'energie' erfolgreich hinzugefügt!\n")

    print("=== Update erfolgreich abgeschlossen! ===")

except Exception as e:
    print(f"\n[FEHLER] Fehler beim Update: {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()
