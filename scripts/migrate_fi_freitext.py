"""Migration: FI-Freitextwerte + manuell verwaltete FI-Liste (08/2026).

Bringt eine bestehende DB (DEV oder PROD) auf den Modellstand nach:
  - "Alle FI loeschbar (auch die letzte)"  -> stuecknachweis.fi_manuell_verwaltet
  - "Sonderzeichen in Delta-I/Delta-t"     -> fi_messungen.delta_i_ma/_t_ms als Text

Schritte (IDEMPOTENT — bereits erfolgte Schritte werden erkannt und uebersprungen):
  F1  ALTER stuecknachweis ADD COLUMN fi_manuell_verwaltet BOOLEAN DEFAULT 0
  F2  Rebuild fi_messungen: delta_i_ma/delta_t_ms FLOAT -> VARCHAR(20)
      (rename -> create_all -> copy -> drop). Bestehende Zahlen werden als Text
      uebernommen und dabei normalisiert: 240.0 -> "240", 52.9 -> "52.9".
      Der SQLite-Rebuild folgt dem Muster aus migrate_prod_vereinheitlichung.py (M6).

VERWENDUNG (immer explizite Ziel-DB angeben — kein Default, um Unfaelle zu vermeiden):
    python scripts/migrate_fi_freitext.py <pfad-zur-ziel-db.db>

WICHTIG: vorher Backup der Ziel-DB anlegen und (bei PROD) den Dienst stoppen.
"""
import os
import sys


def _als_text(wert):
    """Float-Messwert -> Anzeigetext ohne ueberfluessige Dezimalstellen."""
    if wert is None:
        return None
    try:
        f = float(wert)
    except (ValueError, TypeError):
        s = str(wert).strip()
        return s or None
    return str(int(f)) if f == int(f) else ('%g' % f)


def main(target_db):
    target_db = os.path.abspath(target_db)
    if not os.path.exists(target_db):
        print(f'FEHLER: Ziel-DB nicht gefunden: {target_db}')
        return 2

    # Minimale App auf Basis von models.py (NICHT app.py importieren — dessen
    # Startup-Code wuerde beim Import bereits Queries absetzen).
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from flask import Flask  # noqa: E402
    import models  # noqa: E402
    from sqlalchemy import text  # noqa: E402

    db = models.db
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + target_db.replace(chr(92), '/')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        print(f'Ziel-DB: {target_db}')

        def columns(table):
            return {r[1]: r[2] for r in db.session.execute(
                text(f'PRAGMA table_info({table})')).fetchall()}

        # ---- F1: stuecknachweis.fi_manuell_verwaltet ----
        if 'fi_manuell_verwaltet' in columns('stuecknachweis'):
            print('F1 stuecknachweis.fi_manuell_verwaltet: existiert bereits -> uebersprungen')
        else:
            db.session.execute(text(
                'ALTER TABLE stuecknachweis ADD COLUMN fi_manuell_verwaltet BOOLEAN DEFAULT 0'))
            db.session.execute(text(
                'UPDATE stuecknachweis SET fi_manuell_verwaltet = 0 '
                'WHERE fi_manuell_verwaltet IS NULL'))
            db.session.commit()
            print('F1 stuecknachweis.fi_manuell_verwaltet: hinzugefuegt (default 0 = Sync aktiv)')

        # ---- F2: fi_messungen Rebuild (FLOAT -> VARCHAR(20)) ----
        fi_cols = columns('fi_messungen')
        typ_i = (fi_cols.get('delta_i_ma') or '').upper()
        typ_t = (fi_cols.get('delta_t_ms') or '').upper()
        if typ_i.startswith('VARCHAR') and typ_t.startswith('VARCHAR'):
            print('F2 fi_messungen: delta_i_ma/delta_t_ms bereits VARCHAR -> uebersprungen')
        else:
            rows = db.session.execute(text(
                'SELECT id, delta_i_ma, delta_t_ms FROM fi_messungen')).fetchall()
            werte = {r[0]: (_als_text(r[1]), _als_text(r[2])) for r in rows}
            alt_cols = list(fi_cols.keys())

            # FK-Enforcement aus (Rebuild), stuecknachweis-Referenzen bleiben ueber
            # unveraenderte id-Werte erhalten.
            db.session.execute(text('PRAGMA foreign_keys=OFF'))
            db.session.commit()

            db.session.execute(text('DROP TABLE IF EXISTS fi_messungen_f2_old'))
            db.session.execute(text('ALTER TABLE fi_messungen RENAME TO fi_messungen_f2_old'))
            db.session.commit()

            db.create_all()  # legt fi_messungen frisch mit Modell-Schema (VARCHAR) an
            neu_cols = list(columns('fi_messungen').keys())
            common = [c for c in alt_cols if c in neu_cols]
            collist = ', '.join(common)
            db.session.execute(text(
                f'INSERT INTO fi_messungen ({collist}) SELECT {collist} FROM fi_messungen_f2_old'))

            # Zahlen als sauberen Text nachziehen (240.0 -> "240")
            for fid, (wi, wt) in werte.items():
                db.session.execute(text(
                    'UPDATE fi_messungen SET delta_i_ma = :wi, delta_t_ms = :wt WHERE id = :id'),
                    {'wi': wi, 'wt': wt, 'id': fid})

            db.session.execute(text('DROP TABLE fi_messungen_f2_old'))
            db.session.commit()
            db.session.execute(text('PRAGMA foreign_keys=ON'))
            db.session.commit()
            print(f'F2 fi_messungen: rebuilt -> delta_i_ma/delta_t_ms VARCHAR(20), '
                  f'{len(rows)} Zeilen uebernommen ({len(common)} Spalten)')

        # ---- Verifikation ----
        integrity = db.session.execute(text('PRAGMA integrity_check')).fetchone()[0]
        fk = db.session.execute(text('PRAGMA foreign_key_check')).fetchall()
        anzahl = db.session.execute(text('SELECT COUNT(*) FROM fi_messungen')).fetchone()[0]
        print(f'Verifikation: integrity_check={integrity}, '
              f'foreign_key_check={len(fk)} Verletzungen, fi_messungen={anzahl} Zeilen')
        if integrity != 'ok' or fk:
            print('FEHLER: Verifikation fehlgeschlagen — Backup zurueckspielen!')
            return 1

        print('Migration abgeschlossen.')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Aufruf: python scripts/migrate_fi_freitext.py <ziel-db.db>')
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
