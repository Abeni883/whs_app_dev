"""
Migration: Sicherstellen dass alle Projekte mindestens 1 Meteostation haben
Erstellt Standard-Meteostationen für bestehende Projekte ohne MS
"""
import sys
import os

# Füge das Parent-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Project, EWHMeteostation, GWHMeteostation


def ensure_meteostations():
    """Stellt sicher, dass alle Projekte mindestens 1 Meteostation haben."""
    with app.app_context():
        # EWH-Projekte ohne Meteostation
        ewh_projects = Project.query.filter_by(energie='EWH').all()
        ewh_count = 0

        for projekt in ewh_projects:
            existing_ms = EWHMeteostation.query.filter_by(projekt_id=projekt.id).first()
            if not existing_ms:
                ms = EWHMeteostation(
                    projekt_id=projekt.id,
                    ms_nummer='MS 01',
                    reihenfolge=0
                )
                db.session.add(ms)
                ewh_count += 1
                print(f"  EWH-Projekt '{projekt.projektname}' (ID: {projekt.id}): MS 01 erstellt")

        # GWH-Projekte ohne Meteostation
        gwh_projects = Project.query.filter_by(energie='GWH').all()
        gwh_count = 0

        for projekt in gwh_projects:
            existing_ms = GWHMeteostation.query.filter_by(projekt_id=projekt.id).first()
            if not existing_ms:
                ms = GWHMeteostation(
                    projekt_id=projekt.id,
                    ms_nummer='01',
                    name='MS 01',
                    reihenfolge=0
                )
                db.session.add(ms)
                gwh_count += 1
                print(f"  GWH-Projekt '{projekt.projektname}' (ID: {projekt.id}): MS 01 erstellt")

        if ewh_count > 0 or gwh_count > 0:
            db.session.commit()
            print(f"\nMigration abgeschlossen:")
            print(f"  - {ewh_count} EWH-Projekte mit Meteostation ergänzt")
            print(f"  - {gwh_count} GWH-Projekte mit Meteostation ergänzt")
        else:
            print("Alle Projekte haben bereits mindestens 1 Meteostation.")


if __name__ == '__main__':
    print("Starte Migration: Sicherstellen dass alle Projekte mindestens 1 Meteostation haben...")
    ensure_meteostations()
