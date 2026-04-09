"""
Datenbank-Migration: project_id Spalte hinzufuegen
"""
import pymysql
from urllib.parse import quote_plus
import sys

# UTF-8 Encoding fuer Windows Console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

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

    print("=== Datenbank-Migration startet ===\n")

    # 1. Prüfen ob projects Tabelle existiert
    print("1. Prüfe ob 'projects' Tabelle existiert...")
    cursor.execute("SHOW TABLES LIKE 'projects'")
    if not cursor.fetchone():
        print("   'projects' Tabelle existiert nicht. Erstelle sie...")
        cursor.execute("""
            CREATE TABLE projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                projektname VARCHAR(200) NOT NULL,
                projektnummer VARCHAR(50),
                kundenname VARCHAR(150),
                beschreibung TEXT,
                status VARCHAR(30),
                erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
                geaendert_am DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("   [OK] 'projects' Tabelle erstellt!\n")
    else:
        print("   [OK] 'projects' Tabelle existiert bereits.\n")

    # 2. Prüfen ob project_id Spalte bereits existiert
    print("2. Prüfe ob 'project_id' Spalte in 'test_results' existiert...")
    cursor.execute("SHOW COLUMNS FROM test_results LIKE 'project_id'")
    if not cursor.fetchone():
        print("   'project_id' Spalte existiert nicht. Füge sie hinzu...")
        cursor.execute("ALTER TABLE test_results ADD COLUMN project_id INT NULL")
        print("   [OK] 'project_id' Spalte hinzugefuegt!\n")
    else:
        print("   [OK] 'project_id' Spalte existiert bereits.\n")

    # 3. Prüfen ob Foreign Key bereits existiert
    print("3. Prüfe Foreign Key Constraint...")
    cursor.execute("""
        SELECT CONSTRAINT_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = 'abnahmetest'
        AND TABLE_NAME = 'test_results'
        AND CONSTRAINT_NAME = 'fk_test_results_project'
    """)
    if not cursor.fetchone():
        print("   Foreign Key existiert nicht. Füge ihn hinzu...")
        try:
            cursor.execute("""
                ALTER TABLE test_results
                ADD CONSTRAINT fk_test_results_project
                FOREIGN KEY (project_id) REFERENCES projects(id)
                ON DELETE SET NULL
            """)
            print("   [OK] Foreign Key hinzugefuegt!\n")
        except pymysql.err.OperationalError as e:
            if "Duplicate key" in str(e) or "already exists" in str(e):
                print("   [OK] Foreign Key existiert bereits.\n")
            else:
                raise
    else:
        print("   [OK] Foreign Key existiert bereits.\n")

    # 4. Änderungen committen
    connection.commit()

    # 5. Tabellenstruktur anzeigen
    print("4. Aktuelle Tabellenstruktur von 'test_results':")
    cursor.execute("DESCRIBE test_results")
    columns = cursor.fetchall()
    print("\n   Spalte              | Typ                | Null | Key | Default")
    print("   " + "-" * 75)
    for col in columns:
        print(f"   {col[0]:18} | {col[1]:18} | {col[2]:4} | {col[3]:3} | {str(col[4]):10}")

    print("\n=== Migration erfolgreich abgeschlossen! ===")
    print("\nDie Anwendung kann jetzt gestartet werden.")

except Exception as e:
    print(f"\n[FEHLER] Fehler bei der Migration: {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()
