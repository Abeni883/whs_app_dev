"""
Datenbank-Migration: Umstellung auf Weichenheizungsprojekte
Löscht die alte projects-Tabelle und erstellt sie mit der neuen Struktur neu.
ACHTUNG: Alle bestehenden Projekt-Daten gehen verloren!
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

    print("=== Datenbank-Migration: Weichenheizungsprojekte ===\n")

    # 1. Foreign Key Constraint von test_results löschen
    print("1. Lösche Foreign Key Constraint...")
    try:
        cursor.execute("ALTER TABLE test_results DROP FOREIGN KEY fk_test_results_project")
        print("   [OK] Foreign Key gelöscht.\n")
    except Exception as e:
        print(f"   [INFO] Kein Foreign Key vorhanden oder bereits gelöscht.\n")

    # 2. Bestehende projects-Tabelle löschen
    print("2. Lösche alte 'projects'-Tabelle...")
    cursor.execute("DROP TABLE IF EXISTS projects")
    print("   [OK] Tabelle gelöscht.\n")

    # 3. Neue projects-Tabelle mit Weichenheizungs-Feldern erstellen
    print("3. Erstelle neue 'projects'-Tabelle...")
    cursor.execute("""
        CREATE TABLE projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            energie VARCHAR(10) NOT NULL,
            projektname VARCHAR(200) NOT NULL,
            didok_betriebspunkt VARCHAR(100),
            baumappenversion DATE,
            projektleiter_sbb VARCHAR(150),
            pruefer_achermann VARCHAR(150),
            pruefdatum DATE,
            bemerkung TEXT,
            erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
            geaendert_am DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("   [OK] Neue Tabelle erstellt!\n")

    # 4. Foreign Key Constraint wieder hinzufügen
    print("4. Füge Foreign Key Constraint wieder hinzu...")
    cursor.execute("""
        ALTER TABLE test_results
        ADD CONSTRAINT fk_test_results_project
        FOREIGN KEY (project_id) REFERENCES projects(id)
        ON DELETE SET NULL
    """)
    print("   [OK] Foreign Key hinzugefügt.\n")

    # 5. Änderungen committen
    connection.commit()

    # 4. Tabellenstruktur anzeigen
    print("3. Neue Tabellenstruktur von 'projects':\n")
    cursor.execute("DESCRIBE projects")
    columns = cursor.fetchall()
    print("   Spalte                | Typ               | Null | Key | Default")
    print("   " + "-" * 78)
    for col in columns:
        print(f"   {col[0]:20} | {col[1]:17} | {col[2]:4} | {col[3]:3} | {str(col[4] or ''):10}")

    # 5. Beispiel-Projekte einfügen (optional)
    print("\n4. Füge Beispiel-Projekte ein...")
    beispiel_projekte = [
        ('EWH', 'Weichenheizung Bahnhof Zürich HB', '8503000', '2025-01-15', 'Max Mustermann', 'Peter Achermann', '2025-02-20', 'Hauptbahnhof Zürich, Weiche 101-105'),
        ('GWH', 'Weichenheizung Bern', '8507000', '2025-01-20', 'Anna Schmidt', 'Hans Achermann', '2025-02-25', 'Bahnhof Bern, Weiche 201-204'),
        ('EWH', 'Weichenheizung Luzern', '8505000', None, 'Thomas Weber', None, None, 'In Planung'),
    ]

    for projekt in beispiel_projekte:
        cursor.execute("""
            INSERT INTO projects
            (energie, projektname, didok_betriebspunkt, baumappenversion, projektleiter_sbb,
             pruefer_achermann, pruefdatum, bemerkung)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, projekt)

    connection.commit()
    print("   [OK] 3 Beispiel-Projekte eingefügt.\n")

    print("=== Migration erfolgreich abgeschlossen! ===")
    print("\nDie Anwendung kann jetzt neu gestartet werden.")
    print("WICHTIG: Alle alten Projekt-Daten wurden gelöscht!")

except Exception as e:
    print(f"\n[FEHLER] Fehler bei der Migration: {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()
