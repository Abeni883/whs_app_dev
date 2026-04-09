"""
Import der Testfragen aus dem PDF Obermatt in die Datenbank
Basiert auf dem Abnahmetest Elektroweichenheizung WH_331 Funktionalitätstest
"""

import sqlite3
import json
import os

# SQLite-Datenbank-Verbindung
database_path = os.path.join(os.path.dirname(__file__), 'database', 'whs.db')
connection = sqlite3.connect(database_path)

try:
    cursor = connection.cursor()
    
    # Lösche bestehende Testfragen
    print("[INFO] Lösche bestehende Testfragen...")
    cursor.execute("DELETE FROM test_questions")
    connection.commit()
    print("[OK] Bestehende Testfragen gelöscht!")
    
    # Testfragen-Daten basierend auf PDF Obermatt
    testfragen = []
    
    # ===== ANLAGE =====
    anlage_fragen = [
        ("Kommunikation zum LSS-CH", 1, "Name der Anlage", ""),
        ("Kommunikation zum LSS-CH", 2, "DIDOK Bezeichnung", ""),
        ("Kommunikation zum LSS-CH", 3, "DDC Station", ""),
        ("Kommunikation zum LSS-CH", 4, "Anzahl Kabinen", ""),
        ("Kommunikation zum LSS-CH", 5, "Anzahl Meteostationen", ""),
        ("Systemkonfiguration", 6, "Anlage aktiviert", ""),
        ("Systemkonfiguration", 7, "Freigabe Ein/Aus", ""),
        ("Systemkonfiguration", 8, "Meldung an LSS-CH", ""),
        ("Betriebsmodus", 9, "Heizbetrieb", ""),
        ("Betriebsmodus", 10, "Manuell unreguliert", ""),
        ("Betriebsmodus", 11, "Manuell reguliert", ""),
        ("Betriebsmodus", 12, "Lastmanagement", ""),
        ("Temperaturkonfiguration", 13, "Aussentemperatur minimal [°C]", ""),
        ("Temperaturkonfiguration", 14, "Aussentemperatur maximal [°C]", ""),
        ("Systemzugriff", 15, "Link auf Website", ""),
        ("Systemzugriff", 16, "Betriebszentrale", "")
    ]
    
    for testszenario, frage_nr, frage_text, test_info in anlage_fragen:
        testfragen.append({
            'komponente_typ': 'Anlage',
            'testszenario': testszenario,
            'frage_nummer': frage_nr,
            'frage_text': frage_text,
            'test_information': test_info,
            'reihenfolge': frage_nr,
            'preset_antworten': {'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        })
    
    # ===== WHK =====
    whk_fragen = [
        ("Identifikation", 1, "Name der WHK", ""),
        ("Systemkonfiguration", 2, "Frequenz", ""),
        ("Meteostation-Zuordnung", 3, "Meteostation Priorität 1", ""),
        ("Meteostation-Zuordnung", 4, "Meteostation Priorität 2", ""),
        ("Meteostation-Zuordnung", 5, "Meteostation Priorität 3", ""),
        ("Meteostation-Zuordnung", 6, "Meteostation Priorität 4", ""),
        ("Meteostation-Zuordnung", 7, "Meteostation Priorität 5", ""),
        ("Konfiguration", 8, "Anzahl Abgänge", ""),
        ("Betriebsfreigabe", 9, "WHK aktiviert", ""),
        ("Betriebsfreigabe", 10, "WHK Freigabe Ein/Aus", ""),
        ("Kommunikation", 11, "Meldung an LSS-CH Ein/Aus", ""),
        ("Heizbetrieb", 12, "Heizen (rechte Ampel)", ""),
        ("Heizbetrieb", 13, "Prüfbetrieb", ""),
        ("Störmeldungen Stromversorgung", 14, "Sicherungsautomat Batterie", ""),
        ("Störmeldungen Stromversorgung", 15, "Störung Überspannungsschutz", ""),
        ("Störmeldungen Stromversorgung", 16, "230VAC am Netzgerät fehlt", ""),
        ("Störmeldungen Stromversorgung", 17, "Netzgerät Störung", ""),
        ("Temperaturüberwachung", 18, "Schienentemperatur min.", ""),
        ("Temperaturüberwachung", 19, "Schienentemperatur max.", ""),
        ("Störmeldungen Betrieb", 20, "Hauptschalter ausgeschaltet", ""),
        ("Störmeldungen Betrieb", 21, "Gesperrt", ""),
        ("Störmeldungen Betrieb", 22, "Sicherungsautomat Steuerung", ""),
        ("Störmeldungen Betrieb", 23, "Spannungsausfall 16,7Hz/50Hz", "")
    ]
    
    for testszenario, frage_nr, frage_text, test_info in whk_fragen:
        testfragen.append({
            'komponente_typ': 'WHK',
            'testszenario': testszenario,
            'frage_nummer': frage_nr,
            'frage_text': frage_text,
            'test_information': test_info,
            'reihenfolge': 100 + frage_nr,
            'preset_antworten': {'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        })
    
    # ===== ABGANG =====
    abgang_fragen = [
        ("Identifikation", 1, "Name des Abgangs", ""),
        ("Identifikation", 2, "Name der Weiche", ""),
        ("Identifikation", 3, "Name des QC", ""),
        ("Temperatursonden-Zuordnung", 4, "TS Priorität 1", ""),
        ("Temperatursonden-Zuordnung", 5, "TS Priorität 2", ""),
        ("Temperatursonden-Zuordnung", 6, "TS Priorität 3", ""),
        ("Temperatursonden-Zuordnung", 7, "TS Priorität 4", ""),
        ("Temperatursonden-Zuordnung", 8, "TS Priorität 5", ""),
        ("Temperatursonden-Zuordnung", 9, "TS Priorität 6", ""),
        ("Temperatursonden-Zuordnung", 10, "TS Priorität 7", ""),
        ("Temperatursonden-Zuordnung", 11, "TS Priorität 8", ""),
        ("Temperatursonden-Zuordnung", 12, "TS Priorität 9", ""),
        ("Temperatursonden-Zuordnung", 13, "TS Priorität 10", ""),
        ("Temperatursonden-Zuordnung", 14, "TS Priorität 11", ""),
        ("Temperatursonden-Zuordnung", 15, "TS Priorität 12", ""),
        ("Betriebsfreigabe", 16, "Freigegeben Ein/Aus", ""),
        ("Kommunikation", 17, "Störung an LSS-CH Ein/Aus", ""),
        ("Heizbetrieb", 18, "Heizen (rechte Ampel)", ""),
        ("Betriebsschalter", 19, "Betriebswahlschalter Aus", ""),
        ("Betriebsschalter", 20, "Betriebswahlschalter Ein", ""),
        ("Betriebsschalter", 21, "Betriebswahlschalter Auto", ""),
        ("Störmeldungen Schutz", 22, "FI manuell Aus", ""),
        ("Störmeldungen Schutz", 23, "FI ausgelöst", ""),
        ("Störmeldungen Schutz", 24, "Sicherungsautomat manuell Aus", ""),
        ("Störmeldungen Schutz", 25, "Sicherungsautomat ausgelöst", ""),
        ("Störmeldungen Ansteuerung", 26, "Störung Ansteuerung", ""),
        ("Störmeldungen Betrieb", 27, "Gesperrt", ""),
        ("Heizstab-Überwachung", 28, "Leistungsmessung Heizstab", ""),
        ("Heizstab-Überwachung", 29, "Störung Heizstab", "")
    ]
    
    for testszenario, frage_nr, frage_text, test_info in abgang_fragen:
        testfragen.append({
            'komponente_typ': 'Abgang',
            'testszenario': testszenario,
            'frage_nummer': frage_nr,
            'frage_text': frage_text,
            'test_information': test_info,
            'reihenfolge': 200 + frage_nr,
            'preset_antworten': {'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        })
    
    # ===== TEMPERATURSONDE =====
    ts_fragen = [
        ("Identifikation", 1, "Name der Temperatursonde", ""),
        ("Messwerte", 2, "Schienentemperatur [°C]", ""),
        ("Störmeldungen", 3, "Störung Temperatursonde", ""),
        ("Betriebsfreigabe", 4, "Temperatursonde aktiviert", "")
    ]
    
    for testszenario, frage_nr, frage_text, test_info in ts_fragen:
        testfragen.append({
            'komponente_typ': 'Temperatursonde',
            'testszenario': testszenario,
            'frage_nummer': frage_nr,
            'frage_text': frage_text,
            'test_information': test_info,
            'reihenfolge': 300 + frage_nr,
            'preset_antworten': {'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        })
    
    # ===== METEOSTATION =====
    meteo_fragen = [
        ("Identifikation", 1, "Name der Meteostation", ""),
        ("Morgenheizen", 2, "Morgenheizen Uhrzeit von", ""),
        ("Morgenheizen", 3, "Morgenheizen Uhrzeit bis", ""),
        ("Morgenheizen", 4, "Morgenheizen Einschaltdauer", ""),
        ("Störmeldungen Sensoren", 5, "Störung Aussentemperaturfühler", ""),
        ("Störmeldungen Sensoren", 6, "Störung Innentemperaturfühler", ""),
        ("Störmeldungen Sensoren", 7, "Störung Niederschlagsensor", ""),
        ("Störmeldungen System", 8, "Sicherungsautomat MS", ""),
        ("Störmeldungen System", 9, "Kommunikationsstörung", ""),
        ("Messwerte", 10, "Niederschlag", ""),
        ("Messwerte", 11, "Aussentemperatur [°C]", ""),
        ("Messwerte", 12, "Innentemperatur [°C]", ""),
        ("Betriebsfreigabe", 13, "Meteostation aktiviert", "")
    ]
    
    for testszenario, frage_nr, frage_text, test_info in meteo_fragen:
        testfragen.append({
            'komponente_typ': 'Meteostation',
            'testszenario': testszenario,
            'frage_nummer': frage_nr,
            'frage_text': frage_text,
            'test_information': test_info,
            'reihenfolge': 400 + frage_nr,
            'preset_antworten': {'lss_ch': 'richtig', 'wh_lts': 'richtig'}
        })
    
    # Testfragen in Datenbank einfügen
    print(f"[INFO] Füge {len(testfragen)} Testfragen ein...")
    
    for frage in testfragen:
        sql = """
        INSERT INTO test_questions 
        (komponente_typ, testszenario, frage_nummer, frage_text, test_information, reihenfolge, preset_antworten)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(sql, (
            frage['komponente_typ'],
            frage['testszenario'],
            frage['frage_nummer'],
            frage['frage_text'],
            frage['test_information'],
            frage['reihenfolge'],
            json.dumps(frage['preset_antworten'], ensure_ascii=False)
        ))
    
    connection.commit()
    print(f"[OK] {len(testfragen)} Testfragen erfolgreich eingefügt!")
    
    # Zusammenfassung
    cursor.execute("SELECT komponente_typ, COUNT(*) FROM test_questions GROUP BY komponente_typ ORDER BY komponente_typ")
    zusammenfassung = cursor.fetchall()
    
    print("\n[ZUSAMMENFASSUNG]")
    for komponente_typ, anzahl in zusammenfassung:
        print(f"  {komponente_typ}: {anzahl} Testfragen")
    
except Exception as e:
    print(f"[FEHLER] Fehler beim Import: {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()