"""
Script zum Löschen ALLER Test-Ergebnisse
Nach dem Bug-Fix müssen die Daten neu eingegeben werden!
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

    # Zähle aktuelle Einträge
    cursor.execute("SELECT COUNT(*) FROM abnahme_test_results")
    count = cursor.fetchone()[0]
    print(f"Aktuell in Datenbank: {count} Test-Ergebnisse")

    if count > 0:
        confirm = input(f"\nMöchtest du ALLE {count} Test-Ergebnisse löschen? (ja/nein): ")
        if confirm.lower() == 'ja':
            cursor.execute("DELETE FROM abnahme_test_results")
            connection.commit()
            print(f"✓ GELÖSCHT! Alle {count} Test-Ergebnisse wurden entfernt.")
            print(f"\nJetzt kannst du die Tests neu eingeben!")
        else:
            print("Abgebrochen.")
    else:
        print("Keine Test-Ergebnisse vorhanden.")

except Exception as e:
    print(f"[FEHLER] {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()
