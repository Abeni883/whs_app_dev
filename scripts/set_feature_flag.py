"""Feature-Schalter in einer DB setzen (Tabelle app_setting_flags).

    python scripts/set_feature_flag.py <db-pfad> <key> on|off [--dry-run]

Beispiel (einmalig in DEV, IT-Inventar freischalten):
    venv/Scripts/python.exe scripts/set_feature_flag.py database/whs_dev.db feature_it_inventar on

Idempotent. Die Tabelle legt die App beim Start selbst an (db.create_all) - fehlt sie,
bricht das Skript ab, statt ein eigenes Schema zu erfinden. In PROD ist KEIN Lauf noetig:
fehlender Key = AUS; freigeschaltet wird dort ueber "Allgemeine Einstellungen".
"""
import sqlite3
import sys
from datetime import datetime


def main(argv):
    args = [a for a in argv if a != '--dry-run']
    dry = '--dry-run' in argv
    if len(args) != 3 or args[2] not in ('on', 'off'):
        print(__doc__)
        return 2
    pfad, key, wert = args[0].replace('\\', '/'), args[1], 1 if args[2] == 'on' else 0

    con = sqlite3.connect(f'file:{pfad}?mode=rw', uri=True)   # rw: legt keine Schatten-DB an
    try:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                           "AND name='app_setting_flags'").fetchone():
            print('FEHLER: Tabelle app_setting_flags fehlt - App/Dienst einmal starten (create_all).')
            return 1
        alt = con.execute('SELECT value FROM app_setting_flags WHERE key = ?', (key,)).fetchone()
        alt_txt = 'fehlt' if alt is None else ('on' if alt[0] else 'off')
        if dry:
            print(f'DRY-RUN: {key}: {alt_txt} -> {args[2]} (DB unveraendert)')
            return 0
        jetzt = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
        con.execute('INSERT INTO app_setting_flags (key, value, geaendert_am) VALUES (?, ?, ?) '
                    'ON CONFLICT(key) DO UPDATE SET value = excluded.value, '
                    'geaendert_am = excluded.geaendert_am', (key, wert, jetzt))
        con.commit()
        print(f'OK: {key}: {alt_txt} -> {args[2]}')
        return 0
    finally:
        con.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
