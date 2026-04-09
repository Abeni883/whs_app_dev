r"""
Migration: GWH ZSK und MS Nummerierung aktualisieren

Dieses Skript:
1. Aktualisiert alle ZSK-Nummern von "01" zu "ZSK 01"
2. Aktualisiert alle MS-Nummern von "01" zu "MS 01"
3. Fuegt fehlende ZSK 01 zu GWH-Projekten hinzu
4. Fuegt fehlende MS 01 zu GWH-Projekten hinzu

Ausfuehrung:
    cd C:\inetpub\whs_app
    venv\Scripts\activate
    python scripts/migrate_gwh_numbering.py
"""

import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Project, ZSKConfig, GWHMeteostation


def migrate_gwh_numbering():
    """Migriert GWH ZSK und MS Nummern zum neuen Format."""

    with app.app_context():
        print("=" * 60)
        print("GWH Nummerierung Migration")
        print("=" * 60)

        # Statistiken
        zsk_updated = 0
        ms_updated = 0
        zsk_created = 0
        ms_created = 0

        # ==================== ZSK Nummern aktualisieren ====================
        print("\n1. ZSK-Nummern aktualisieren...")
        zsks = ZSKConfig.query.all()

        for zsk in zsks:
            old_nummer = zsk.zsk_nummer

            # Prüfe ob bereits im neuen Format
            if old_nummer.startswith('ZSK '):
                continue

            # Konvertiere zum neuen Format
            # Entferne führende Nullen und formatiere neu
            try:
                # Extrahiere die Nummer
                nummer = int(old_nummer.lstrip('0') or '0')
                new_nummer = f'ZSK {str(nummer).zfill(2)}'

                zsk.zsk_nummer = new_nummer
                zsk_updated += 1
                print(f"   ZSK aktualisiert: '{old_nummer}' -> '{new_nummer}' (Projekt ID: {zsk.projekt_id})")
            except ValueError:
                print(f"   WARNUNG: Konnte ZSK-Nummer '{old_nummer}' nicht konvertieren (Projekt ID: {zsk.projekt_id})")

        # ==================== MS Nummern aktualisieren ====================
        print("\n2. GWH Meteostation-Nummern aktualisieren...")
        meteostationen = GWHMeteostation.query.all()

        for ms in meteostationen:
            old_nummer = ms.ms_nummer

            # Prüfe ob bereits im neuen Format
            if old_nummer.startswith('MS '):
                continue

            # Konvertiere zum neuen Format
            try:
                # Extrahiere die Nummer
                nummer = int(old_nummer.lstrip('0') or '0')
                new_nummer = f'MS {str(nummer).zfill(2)}'

                ms.ms_nummer = new_nummer
                ms_updated += 1
                print(f"   MS aktualisiert: '{old_nummer}' -> '{new_nummer}' (Projekt ID: {ms.projekt_id})")
            except ValueError:
                print(f"   WARNUNG: Konnte MS-Nummer '{old_nummer}' nicht konvertieren (Projekt ID: {ms.projekt_id})")

        # ==================== Fehlende ZSKs erstellen ====================
        print("\n3. Fehlende ZSKs für GWH-Projekte erstellen...")
        gwh_projects = Project.query.filter_by(energie='GWH').all()

        for project in gwh_projects:
            existing_zsks = ZSKConfig.query.filter_by(projekt_id=project.id).count()

            if existing_zsks == 0:
                new_zsk = ZSKConfig(
                    projekt_id=project.id,
                    zsk_nummer='ZSK 01',
                    anzahl_teile=1,
                    hat_temperatursonde=False,
                    gasversorgung='zentral',
                    kathodenschutz=False,
                    reihenfolge=0
                )
                db.session.add(new_zsk)
                zsk_created += 1
                print(f"   ZSK 01 erstellt für Projekt: {project.projektname} (ID: {project.id})")

        # ==================== Fehlende MS erstellen ====================
        print("\n4. Fehlende Meteostationen für GWH-Projekte erstellen...")

        for project in gwh_projects:
            existing_ms = GWHMeteostation.query.filter_by(projekt_id=project.id).count()

            if existing_ms == 0:
                new_ms = GWHMeteostation(
                    projekt_id=project.id,
                    ms_nummer='MS 01',
                    name='MS 01',
                    reihenfolge=0
                )
                db.session.add(new_ms)
                ms_created += 1
                print(f"   MS 01 erstellt für Projekt: {project.projektname} (ID: {project.id})")

        # ==================== Änderungen speichern ====================
        db.session.commit()

        # ==================== Zusammenfassung ====================
        print("\n" + "=" * 60)
        print("MIGRATION ABGESCHLOSSEN")
        print("=" * 60)
        print(f"ZSK-Nummern aktualisiert: {zsk_updated}")
        print(f"MS-Nummern aktualisiert:  {ms_updated}")
        print(f"ZSKs erstellt:            {zsk_created}")
        print(f"Meteostationen erstellt:  {ms_created}")
        print("=" * 60)


if __name__ == '__main__':
    migrate_gwh_numbering()
