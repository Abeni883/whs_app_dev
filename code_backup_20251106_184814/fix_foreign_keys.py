"""
Fix Foreign Key Constraints: ON DELETE CASCADE für abnahme_test_results
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

    print("=== Foreign Key Constraints Fix ===\n")

    # 1. Finde den aktuellen Foreign Key Namen
    print("1. Suche bestehende Foreign Key Constraints...")
    cursor.execute("""
        SELECT CONSTRAINT_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = 'abnahmetest'
        AND TABLE_NAME = 'abnahme_test_results'
        AND COLUMN_NAME = 'test_question_id'
        AND CONSTRAINT_NAME != 'PRIMARY'
    """)

    fk_name = None
    result = cursor.fetchone()
    if result:
        fk_name = result[0]
        print(f"   Gefunden: {fk_name}")
    else:
        print("   Keine Foreign Key Constraint gefunden")

    # 2. Lösche alten Foreign Key
    if fk_name:
        print(f"\n2. Lösche alten Foreign Key '{fk_name}'...")
        cursor.execute(f"""
            ALTER TABLE abnahme_test_results
            DROP FOREIGN KEY {fk_name}
        """)
        print("   [OK] Foreign Key gelöscht")

    # 3. Erstelle neuen Foreign Key mit ON DELETE CASCADE
    print("\n3. Erstelle neuen Foreign Key mit ON DELETE CASCADE...")
    cursor.execute("""
        ALTER TABLE abnahme_test_results
        ADD CONSTRAINT fk_test_question
        FOREIGN KEY (test_question_id)
        REFERENCES test_questions(id)
        ON DELETE CASCADE
    """)
    print("   [OK] Foreign Key mit CASCADE erstellt")

    connection.commit()
    print("\n=== Fix erfolgreich abgeschlossen! ===")
    print("\nJetzt können Testfragen gelöscht werden, und die zugehörigen Ergebnisse werden automatisch mitgelöscht.")

except Exception as e:
    print(f"\n[FEHLER] Fehler beim Fix: {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()
