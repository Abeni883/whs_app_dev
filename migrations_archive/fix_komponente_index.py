"""
Script zum Korrigieren des komponente_index in bestehenden Test-Ergebnissen
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

    # Hole alle Test-Ergebnisse
    cursor.execute("""
        SELECT id, test_question_id, komponente_index
        FROM abnahme_test_results
    """)
    results = cursor.fetchall()

    print(f"Gefundene Ergebnisse: {len(results)}")

    # Hole Testfragen um komponente_typ zu ermitteln
    cursor.execute("SELECT id, komponente_typ FROM test_questions")
    questions = {row[0]: row[1] for row in cursor.fetchall()}

    updates = 0
    for result_id, test_question_id, komponente_index in results:
        komponente_typ = questions.get(test_question_id)

        if not komponente_typ:
            print(f"[SKIP] Frage {test_question_id} nicht gefunden")
            continue

        # Für Anlage und WHK ist komponente_index korrekt (die Spalte)
        if komponente_typ in ["Anlage", "WHK"]:
            print(f"[OK] Test {result_id}: {komponente_typ} - komponente_index '{komponente_index}' ist korrekt")
            continue

        # Für andere Komponententypen ist komponente_index falsch
        # Es sollte die WHK-Nummer sein, nicht die Spalte
        # Problem: Wir wissen nicht welche WHK-Nummer es war!
        # Wir können es nur löschen und neu eingeben lassen
        print(f"[FEHLER] Test {result_id}: {komponente_typ} - komponente_index '{komponente_index}' ist falsch!")
        print(f"         Sollte eine WHK-Nummer sein (z.B. 'WHK 01'), nicht '{komponente_index}'")

        # Optional: Lösche diesen Eintrag
        # cursor.execute("DELETE FROM abnahme_test_results WHERE id = %s", (result_id,))
        # updates += 1

    print(f"\nZusammenfassung:")
    print(f"- Insgesamt: {len(results)} Einträge")
    print(f"- Fehlerhafte Einträge gefunden")
    print(f"\nLösung: Lösche ALLE Test-Ergebnisse und gebe sie neu ein:")
    print(f"  DELETE FROM abnahme_test_results;")

    # Uncomment to actually delete:
    # cursor.execute("DELETE FROM abnahme_test_results")
    # connection.commit()
    # print(f"[GELÖSCHT] Alle Test-Ergebnisse wurden gelöscht!")

except Exception as e:
    print(f"[FEHLER] {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()
