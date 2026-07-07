"""Migration PROD-Ist -> kanonisches main (Repo-Vereinheitlichung, Phase 2b/3).

Bringt eine bestehende PROD-DB (Schema-Stand ohne Steuerung/Norm-Features) auf den
kanonischen DEV-Schema-Stand. IDEMPOTENT: bereits erfolgte Schritte werden erkannt
und uebersprungen.

Schritte:
  M1  CREATE TABLE steuerung_configs (via db.create_all)
  M2  ALTER app_settings ADD COLUMN norm_name DEFAULT 'EN 61439-1/2'
  M3  Rebuild stuecknachweis: whk_config_id -> nullable, + steuerung_config_id,
      herstellungsdatum_text, norm_name, pdf_stuecknachweis_exportiert,
      pdf_konformitaet_exportiert (rename -> create_all -> copy -> drop; FK zu
      fi_messungen bleibt ueber unveraenderte id-Werte erhalten)
  M4  herstellungsdatum (Date) -> herstellungsdatum_text (TT.MM.JJJJ) fuer alle SN

VERWENDUNG (immer explizite Ziel-DB angeben — kein Default, um Unfaelle zu vermeiden):
    python scripts/migrate_prod_vereinheitlichung.py <pfad-zur-ziel-db.db>

WICHTIG (Phase 3): vorher Backup der Ziel-DB anlegen und den Dienst stoppen.
"""
import os
import sys
from datetime import datetime


def main(target_db):
    target_db = os.path.abspath(target_db)
    if not os.path.exists(target_db):
        print(f'FEHLER: Ziel-DB nicht gefunden: {target_db}')
        return 2

    # Minimale App auf Basis von models.py (NICHT app.py importieren — dessen
    # Startup-Code wuerde app_settings.norm_name abfragen, bevor die Spalte existiert).
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from flask import Flask  # noqa: E402
    import models  # noqa: E402
    from sqlalchemy import text  # noqa: E402

    db = models.db
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + target_db.replace('\\', '/')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        print(f'Ziel-DB: {target_db}')

        def columns(table):
            return {r[1]: (r[2], r[3]) for r in db.session.execute(
                text(f'PRAGMA table_info({table})')).fetchall()}

        def table_exists(name):
            return db.session.execute(text(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=:n"
            ), {'n': name}).fetchone() is not None

        # ---- M1: steuerung_configs ----
        if table_exists('steuerung_configs'):
            print('M1 steuerung_configs: existiert bereits -> uebersprungen')
        else:
            db.create_all()  # legt fehlende Modell-Tabellen an (u.a. steuerung_configs)
            print('M1 steuerung_configs: angelegt')

        # ---- M2: app_settings.norm_name ----
        if 'norm_name' in columns('app_settings'):
            print('M2 app_settings.norm_name: existiert bereits -> uebersprungen')
        else:
            db.session.execute(text(
                "ALTER TABLE app_settings ADD COLUMN norm_name VARCHAR(100) DEFAULT 'EN 61439-1/2'"))
            db.session.commit()
            print('M2 app_settings.norm_name: hinzugefuegt (Default EN 61439-1/2)')

        # ---- M3: stuecknachweis Rebuild ----
        sn_cols = columns('stuecknachweis')
        neue_spalten = ['steuerung_config_id', 'herstellungsdatum_text', 'norm_name',
                        'pdf_stuecknachweis_exportiert', 'pdf_konformitaet_exportiert']
        whk_notnull = sn_cols.get('whk_config_id', ('', 1))[1]
        bereits_migriert = all(c in sn_cols for c in neue_spalten) and whk_notnull == 0
        if bereits_migriert:
            print('M3 stuecknachweis: bereits migriert -> uebersprungen')
        else:
            db.session.execute(text('PRAGMA foreign_keys=OFF'))
            old_cols = list(sn_cols.keys())
            db.session.execute(text('DROP TABLE IF EXISTS stuecknachweis_old'))
            db.session.execute(text('ALTER TABLE stuecknachweis RENAME TO stuecknachweis_old'))
            db.session.commit()
            db.create_all()  # legt stuecknachweis mit neuem Modell-Schema an
            new_cols = list(columns('stuecknachweis').keys())
            common = [c for c in old_cols if c in new_cols]
            collist = ', '.join(common)
            db.session.execute(text(
                f'INSERT INTO stuecknachweis ({collist}) SELECT {collist} FROM stuecknachweis_old'))
            db.session.execute(text('DROP TABLE stuecknachweis_old'))
            db.session.commit()
            print(f'M3 stuecknachweis: rebuilt (whk_config_id nullable, +{len(neue_spalten)} Spalten). '
                  f'Kopierte Spalten: {len(common)}')

        # ---- M4: herstellungsdatum -> herstellungsdatum_text ----
        rows = db.session.execute(text(
            'SELECT id, herstellungsdatum FROM stuecknachweis '
            'WHERE herstellungsdatum_text IS NULL AND herstellungsdatum IS NOT NULL')).fetchall()
        m4 = 0
        for sn_id, datum in rows:
            try:
                d = datetime.strptime(str(datum)[:10], '%Y-%m-%d')
                txt = d.strftime('%d.%m.%Y')
            except (ValueError, TypeError):
                txt = str(datum)
            db.session.execute(text(
                'UPDATE stuecknachweis SET herstellungsdatum_text=:t WHERE id=:i'),
                {'t': txt, 'i': sn_id})
            m4 += 1
        db.session.commit()
        print(f'M4 herstellungsdatum_text: {m4} Datensaetze befuellt '
              f'({"nichts offen" if m4 == 0 else "ok"})')

        # ---- M5: stuecknachweis.art_produkt_text (Steuerungs-Art-des-Produkts) ----
        # Bei frischer Migration legt M3 (Rebuild aus Modell) die Spalte bereits an;
        # bei zuvor migrierten DBs (M3 uebersprungen) wird sie hier ergaenzt.
        if 'art_produkt_text' in columns('stuecknachweis'):
            print('M5 stuecknachweis.art_produkt_text: existiert bereits -> uebersprungen')
        else:
            db.session.execute(text(
                'ALTER TABLE stuecknachweis ADD COLUMN art_produkt_text VARCHAR(100)'))
            db.session.commit()
            print('M5 stuecknachweis.art_produkt_text: hinzugefuegt (nullable, NULL = Fallback)')

        print('Migration abgeschlossen.')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Aufruf: python scripts/migrate_prod_vereinheitlichung.py <ziel-db.db>')
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
