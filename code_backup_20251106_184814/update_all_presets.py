"""
Aktualisiert alle Testfragen-Presets:
- WH-LTS: richtig
- LSS-CH: Kein Preset (leer)
"""

from app import app, db
from models import TestQuestion

def update_presets():
    with app.app_context():
        print("=" * 60)
        print("AKTUALISIERE ALLE TESTFRAGEN-PRESETS")
        print("=" * 60)

        # Lade alle Testfragen
        all_questions = TestQuestion.query.all()

        print(f"\n[INFO] Gefundene Testfragen: {len(all_questions)}")
        print("\n" + "-" * 60)
        print("SETZE PRESETS...")
        print("-" * 60)

        updated_count = 0

        for frage in all_questions:
            # Altes Preset anzeigen
            old_preset = frage.preset_antworten or {}
            old_lss_ch = old_preset.get('lss_ch', 'nicht gesetzt')
            old_wh_lts = old_preset.get('wh_lts', 'nicht gesetzt')

            # Neues Preset setzen
            # WH-LTS = richtig, LSS-CH = leer (kein Preset)
            new_preset = {
                'wh_lts': 'richtig'
                # lss_ch wird nicht gesetzt = kein Preset
            }

            frage.preset_antworten = new_preset
            updated_count += 1

            # Zeige Änderung
            print(f"[{updated_count:3d}] {frage.komponente_typ:20s} | ID {frage.id:3d}")
            print(f"      Alt: LSS-CH={old_lss_ch:15s}, WH-LTS={old_wh_lts:15s}")
            print(f"      Neu: LSS-CH=kein Preset    , WH-LTS=richtig")
            print()

        # Speichern
        db.session.commit()

        print("-" * 60)
        print(f"\n[ERFOLG] {updated_count} Testfragen aktualisiert!")
        print("\n" + "=" * 60)
        print("ZUSAMMENFASSUNG")
        print("=" * 60)
        print(f"Aktualisierte Fragen:  {updated_count}")
        print(f"WH-LTS Preset:         richtig")
        print(f"LSS-CH Preset:         Kein Preset")
        print("=" * 60)

        # Zeige Komponententyp-Statistik
        print("\nAktualisiert nach Komponententyp:")
        komponenten = {}
        for frage in all_questions:
            typ = frage.komponente_typ
            komponenten[typ] = komponenten.get(typ, 0) + 1

        for typ, anzahl in sorted(komponenten.items()):
            print(f"  - {typ:20s}: {anzahl:3d} Fragen")

        print("\n" + "=" * 60)
        print("[OK] Fertig! Alle Presets wurden aktualisiert.")
        print("=" * 60)

if __name__ == '__main__':
    update_presets()
