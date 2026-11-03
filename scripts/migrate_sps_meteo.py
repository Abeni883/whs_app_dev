"""Schema-Migration: Meteostation-Felder in sps_infos (IT-Inventar, 11/2026).

Ergaenzt vier Freitext-Spalten fuer die Meteostation einer WHK (nur relevant, wenn der
WHK eine Meteostation zugeordnet ist; das Formular blendet die Sektion sonst aus):

    meteo_baudrate          VARCHAR(50)
    meteo_modbus_adresse    VARCHAR(50)
    meteo_seriennummer      VARCHAR(100)
    meteo_herstellungsjahr  VARCHAR(20)

Jede Spalte wird nur angelegt, wenn sie noch fehlt (PRAGMA table_info) — IDEMPOTENT,
ein zweiter Lauf meldet "nichts zu tun". Kein Rebuild, keine Datenaenderung.
Danach integrity_check + foreign_key_check.

VERWENDUNG (immer explizite Ziel-DB angeben — kein Default, um Unfaelle zu vermeiden):
    python scripts/migrate_sps_meteo.py <pfad-zur-ziel-db.db> --dry-run
    python scripts/migrate_sps_meteo.py <pfad-zur-ziel-db.db>

--dry-run oeffnet die DB READ-ONLY (sqlite ?mode=ro) und meldet nur, was angelegt wuerde.

WICHTIG: vorher Backup der Ziel-DB anlegen (PROD: Dienst stoppen, Backup, Skript,
Dienst starten — oder konsistenter Snapshot ueber die SQLite-Backup-API). Hinweis:
db.create_all() beim App-Start legt NUR neue Tabellen an, keine neuen Spalten — dieses
Skript ist daher fuer bestehende DBs (PROD) zwingend.
"""
import os
import sqlite3
import sys

# Muss mit models.SpsInfo uebereinstimmen (Name, SQL-Typ).
NEUE_SPALTEN = [
    ('meteo_baudrate', 'VARCHAR(50)'),
    ('meteo_modbus_adresse', 'VARCHAR(50)'),
    ('meteo_seriennummer', 'VARCHAR(100)'),
    ('meteo_herstellungsjahr', 'VARCHAR(20)'),
]
TABELLE = 'sps_infos'


def fehlende_spalten(con):
    vorhanden = {row[1] for row in con.execute(f'PRAGMA table_info({TABELLE})')}
    if not vorhanden:
        raise SystemExit(f'FEHLER: Tabelle {TABELLE} existiert nicht '
                         f'(App einmal starten -> db.create_all legt sie an).')
    return [(n, t) for n, t in NEUE_SPALTEN if n not in vorhanden]


def migrate(db_pfad, dry_run):
    uri = f'file:{db_pfad}?mode=ro' if dry_run else f'file:{db_pfad}'
    con = sqlite3.connect(uri, uri=True)
    try:
        fehlend = fehlende_spalten(con)
        if not fehlend:
            print(f'OK: nichts zu tun — alle {len(NEUE_SPALTEN)} Meteo-Spalten vorhanden.')
            return 0
        for name, typ in fehlend:
            if dry_run:
                print(f'  wuerde anlegen: {TABELLE}.{name} {typ}')
            else:
                con.execute(f'ALTER TABLE {TABELLE} ADD COLUMN {name} {typ}')
                print(f'  angelegt: {TABELLE}.{name} {typ}')
        if dry_run:
            print(f'DRY-RUN: {len(fehlend)} Spalte(n) wuerden angelegt, DB unveraendert.')
            return 0
        con.commit()

        # Kontrolle
        integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
        fk = con.execute('PRAGMA foreign_key_check').fetchall()
        rest = fehlende_spalten(con)
        print(f'integrity_check: {integrity} | foreign_key_check: {len(fk)} Verstoesse | '
              f'Kontrolllauf: {len(rest)} fehlend')
        if integrity != 'ok' or fk or rest:
            print('FEHLER: Kontrolle nicht sauber — Backup pruefen!')
            return 1
        print(f'OK: {len(fehlend)} Spalte(n) angelegt, Kontrolllauf leer.')
        return 0
    finally:
        con.close()


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    dry = '--dry-run' in argv
    if len(args) != 1:
        print(__doc__)
        return 2
    db_pfad = os.path.abspath(args[0]).replace('\\', '/')
    if not os.path.isfile(db_pfad):
        print(f'FEHLER: DB nicht gefunden: {db_pfad}')
        return 2
    print(f'{"DRY-RUN " if dry else ""}Ziel-DB: {db_pfad}')
    return migrate(db_pfad, dry)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
