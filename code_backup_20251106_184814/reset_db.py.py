from app import app, db

with app.app_context():
    print("⚠️  ACHTUNG: Alle Daten werden gelöscht!")
    antwort = input("Fortfahren? (ja/nein): ")
    
    if antwort.lower() == 'ja':
        print("Lösche alte Tabellen...")
        db.drop_all()
        
        print("Erstelle neue Tabellen...")
        db.create_all()
        
        print("✅ Datenbank wurde erfolgreich neu erstellt!")
    else:
        print("❌ Abgebrochen.")