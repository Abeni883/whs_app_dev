"""
Datenbank-Migration: Abnahmetest-Tabellen und Testfragen anlegen
Erstellt die neuen Tabellen: whk_configs, test_questions, abnahme_test_results
"""
import pymysql
from urllib.parse import quote_plus
from datetime import datetime

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

    print("=== Datenbank-Migration: Abnahmetest-Funktionalität ===\n")

    # 1. WHK-Konfiguration Tabelle erstellen
    print("1. Erstelle 'whk_configs' Tabelle...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS whk_configs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            projekt_id INT NOT NULL,
            whk_nummer VARCHAR(20) NOT NULL,
            anzahl_abgaenge INT NOT NULL,
            anzahl_temperatursonden INT NOT NULL,
            hat_antriebsheizung BOOLEAN DEFAULT FALSE,
            meteostation VARCHAR(50),
            erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (projekt_id) REFERENCES projects(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("   [OK] 'whk_configs' Tabelle erstellt!\n")

    # 2. Testfragen-Vorlagen Tabelle erstellen
    print("2. Erstelle 'test_questions' Tabelle...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            komponente_typ VARCHAR(50) NOT NULL,
            testszenario VARCHAR(200) NOT NULL,
            frage_nummer INT NOT NULL,
            frage_text TEXT NOT NULL,
            test_information TEXT,
            reihenfolge INT NOT NULL,
            erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("   [OK] 'test_questions' Tabelle erstellt!\n")

    # 3. Abnahmetest-Ergebnisse Tabelle erstellen
    print("3. Erstelle 'abnahme_test_results' Tabelle...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS abnahme_test_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            projekt_id INT NOT NULL,
            test_question_id INT NOT NULL,
            komponente_index VARCHAR(50) NOT NULL,
            lss_ch_result VARCHAR(20),
            wh_lts_result VARCHAR(20),
            bemerkung TEXT,
            getestet_am DATETIME DEFAULT CURRENT_TIMESTAMP,
            tester VARCHAR(100),
            FOREIGN KEY (projekt_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (test_question_id) REFERENCES test_questions(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("   [OK] 'abnahme_test_results' Tabelle erstellt!\n")

    # 4. Basis-Testfragen einfügen
    print("4. Füge Basis-Testfragen ein...")

    testfragen = [
        # Anlage-Tests
        ('Anlage', 'Kommunikation und Netzwerk', 1, 'Kommunikation zum LSS-CH ist aktiv', 'Prüfen Sie die Verbindung im LSS-CH System', 1),
        ('Anlage', 'Kommunikation und Netzwerk', 2, 'Lastmanagement funktioniert', 'Überprüfen Sie die Lastverteilung', 2),
        ('Anlage', 'Meteo-Daten', 3, 'Meteostationen liefern Daten', 'Kontrollieren Sie die Meteo-Datenwerte', 3),

        # WHK-Tests
        ('WHK', 'Sichtbarkeit und Status', 1, 'WHK ist im LSS-CH sichtbar', 'Überprüfen Sie die WHK-Liste im LSS-CH', 10),
        ('WHK', 'Störungsmeldungen', 2, 'Störungsmeldungen werden übertragen', 'Simulieren Sie eine Störung', 11),
        ('WHK', 'Status-Anzeige', 3, 'WHK-Status wird korrekt angezeigt', 'Prüfen Sie die Status-Anzeige', 12),

        # Abgang-Tests
        ('Abgang', 'Konfiguration', 1, 'Abgang ist konfiguriert und sichtbar', 'Überprüfen Sie die Abgang-Konfiguration im System', 20),
        ('Abgang', 'Heizleistung', 2, 'Heizleistung wird gemessen', 'Prüfen Sie die Leistungsmessung', 21),
        ('Abgang', 'Betriebswahlschalter', 3, 'Betriebswahlschalter funktioniert', 'Testen Sie die verschiedenen Betriebsmodi', 22),

        # Temperatursonde-Tests
        ('Temperatursonde', 'Messwerte', 1, 'Temperatursonde liefert Werte', 'Überprüfen Sie die aktuellen Temperaturwerte', 30),
        ('Temperatursonde', 'Störungsmeldung', 2, 'Störungsmeldung bei Ausfall funktioniert', 'Simulieren Sie einen Sensor-Ausfall', 31),
        ('Temperatursonde', 'LSS-CH Integration', 3, 'Temperaturwerte im LSS-CH sichtbar', 'Kontrollieren Sie die Werte im LSS-CH', 32),

        # Antriebsheizung-Tests
        ('Antriebsheizung', 'Schaltung', 1, 'Antriebsheizung ist geschaltet', 'Prüfen Sie den Schaltzustand', 40),
        ('Antriebsheizung', 'Leistungsmessung', 2, 'Leistungsmessung funktioniert', 'Überprüfen Sie die Leistungsaufnahme', 41),

        # Meteostation-Tests
        ('Meteostation', 'Wetterdaten', 1, 'Meteostation liefert Wetterdaten', 'Kontrollieren Sie die Meteo-Werte', 50),
        ('Meteostation', 'Schneefallsensor', 2, 'Schneefallsensor ist aktiv', 'Prüfen Sie den Schneefallsensor-Status', 51),
        ('Meteostation', 'Windmessung', 3, 'Windmessung funktioniert', 'Überprüfen Sie die Windgeschwindigkeit', 52),
    ]

    for frage in testfragen:
        cursor.execute("""
            INSERT INTO test_questions
            (komponente_typ, testszenario, frage_nummer, frage_text, test_information, reihenfolge)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, frage)

    connection.commit()
    print(f"   [OK] {len(testfragen)} Basis-Testfragen eingefügt.\n")

    print("=== Migration erfolgreich abgeschlossen! ===")
    print("\nDie folgenden Tabellen wurden erstellt:")
    print("- whk_configs (WHK-Konfigurationen)")
    print("- test_questions (Testfragen-Vorlagen)")
    print("- abnahme_test_results (Test-Ergebnisse)")
    print(f"\n{len(testfragen)} Basis-Testfragen wurden angelegt.")

except Exception as e:
    print(f"\n[FEHLER] Fehler bei der Migration: {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()
