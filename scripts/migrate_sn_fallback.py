"""Datenbereinigung: Stuecknachweis folgt der Konfiguration (Fallback-Muster, 10/2026).

Hintergrund: Bis zu diesem Stand wurden typbezeichnung und art_produkt_text beim
Anlegen eines Stuecknachweises (SN) physisch aus der Konfiguration kopiert. Spaetere
Aenderungen an der Konfiguration (Steuerung: "Art des Produkts (Produktenorm)" = name,
"Typ" = typ; WHK: whk_typ) kamen im bestehenden SN nicht mehr an. Neu gilt das
Fallback-Muster wie bei norm_name:

    sn.typbezeichnung   NULL -> steuerung_configs.typ  bzw. whk_configs.whk_typ (sonst whk_nummer)
    sn.art_produkt_text NULL -> steuerung_configs.name bzw. 'Weichenheizkabine'

Dieses Skript setzt in bestehenden SN die beiden Spalten auf NULL, WENN der gespeicherte
Wert nie eine bewusste Abweichung war, d. h. exakt einem dieser Werte entspricht:

  Typbezeichnung:
    T1  aktueller Config-Fallback (steuerung.typ / 'Steuerung' bzw. whk_typ / whk_nummer)
    T2  Steuerung: steuerung.name  (Alt-Init vor 07.07.2026 kopierte name statt typ ->
        "ueber Kreuz"; siehe Commit d267e59)
    T3  leerer String
  Art des Produkts:
    A1  aktueller Config-Fallback (steuerung.name / 'Steuerung (SHDSL)' bzw. 'Weichenheizkabine')
    A2  Steuerung: steuerung.typ   (vertauschter Altwert -> "ueber Kreuz")
    A3  leerer String

Alle anderen Werte werden NICHT angefasst (koennten gewollt sein) und am Ende als Liste
zur manuellen Sichtung ausgegeben. SN ohne zugeordnete Konfiguration werden uebersprungen.

IDEMPOTENT: ein zweiter Lauf findet nichts mehr zu tun.

VERWENDUNG (immer explizite Ziel-DB angeben — kein Default, um Unfaelle zu vermeiden):
    python scripts/migrate_sn_fallback.py <pfad-zur-ziel-db.db> --dry-run
    python scripts/migrate_sn_fallback.py <pfad-zur-ziel-db.db>

--dry-run oeffnet die DB READ-ONLY (sqlite ?mode=ro) und meldet nur, was geaendert wuerde.

WICHTIG: vorher Backup der Ziel-DB anlegen (bei PROD: Dienst stoppen, Backup, Skript,
Dienst starten — oder konsistenter Snapshot ueber die SQLite-Backup-API).
"""
import os
import sqlite3
import sys

# Muss mit models.py (config_typbezeichnung / config_art_produkt) uebereinstimmen.
ART_PRODUKT_WHK = 'Weichenheizkabine'
TYP_FALLBACK_STEUERUNG = 'Steuerung'
ART_PRODUKT_FALLBACK_STEUERUNG = 'Steuerung (SHDSL)'


def _lade_sn(con):
    """Alle SN mit zugeordneter Config als Plain-Tupel (keine ORM-Objekte)."""
    rows = con.execute("""
        SELECT sn.id, sn.project_id, sn.whk_config_id, sn.steuerung_config_id,
               sn.typbezeichnung, sn.art_produkt_text,
               w.whk_nummer, w.whk_typ,
               st.name, st.typ,
               w.id, st.id
          FROM stuecknachweis sn
          LEFT JOIN whk_configs w        ON w.id  = sn.whk_config_id
          LEFT JOIN steuerung_configs st ON st.id = sn.steuerung_config_id
         ORDER BY sn.id
    """).fetchall()
    return rows


def analysiere(rows):
    """Gibt (aenderungen, offen, uebersprungen) zurueck.

    aenderungen:  [(sn_id, spalte, altwert, grund)]
    offen:        [(sn_id, kontext, spalte, altwert, fallback)]  -> manuelle Sichtung
    uebersprungen:[(sn_id, grund)]
    """
    aenderungen, offen, uebersprungen = [], [], []
    for (sn_id, project_id, whk_id, st_id, typ_sn, art_sn,
         whk_nummer, whk_typ, st_name, st_typ, w_ok, st_ok) in rows:
        ist_steuerung = st_id is not None

        if ist_steuerung:
            if st_ok is None:
                # LEFT JOIN ohne Treffer -> Config fehlt (Waise)
                uebersprungen.append((sn_id, f'steuerung_config_id={st_id} nicht gefunden'))
                continue
            kontext = f'Steuerung "{st_name or ""}" / "{st_typ or ""}"'
            typ_fb = st_typ or TYP_FALLBACK_STEUERUNG
            art_fb = st_name or ART_PRODUKT_FALLBACK_STEUERUNG
            typ_vertauscht = st_name
            art_vertauscht = st_typ
        else:
            if w_ok is None:
                uebersprungen.append((sn_id, f'whk_config_id={whk_id} nicht gefunden'))
                continue
            kontext = f'WHK {whk_nummer} / "{whk_typ or ""}"'
            typ_fb = whk_typ or whk_nummer
            art_fb = ART_PRODUKT_WHK
            typ_vertauscht = None
            art_vertauscht = None

        # Typbezeichnung
        if typ_sn is not None:
            v = typ_sn.strip()
            if v == '':
                aenderungen.append((sn_id, 'typbezeichnung', typ_sn, 'T3 leer'))
            elif v == typ_fb:
                aenderungen.append((sn_id, 'typbezeichnung', typ_sn, 'T1 = Config-Fallback'))
            elif typ_vertauscht and v == typ_vertauscht:
                aenderungen.append((sn_id, 'typbezeichnung', typ_sn,
                                    'T2 = steuerung.name (Alt-Init/ueber Kreuz)'))
            else:
                offen.append((sn_id, kontext, 'typbezeichnung', typ_sn, typ_fb))

        # Art des Produkts
        if art_sn is not None:
            v = art_sn.strip()
            if v == '':
                aenderungen.append((sn_id, 'art_produkt_text', art_sn, 'A3 leer'))
            elif v == art_fb:
                aenderungen.append((sn_id, 'art_produkt_text', art_sn, 'A1 = Config-Fallback'))
            elif art_vertauscht and v == art_vertauscht:
                aenderungen.append((sn_id, 'art_produkt_text', art_sn,
                                    'A2 = steuerung.typ (ueber Kreuz)'))
            else:
                offen.append((sn_id, kontext, 'art_produkt_text', art_sn, art_fb))

    return aenderungen, offen, uebersprungen


def _bericht(aenderungen, offen, uebersprungen, anzahl_sn, dry):
    praefix = 'wuerde' if dry else 'wird'
    print(f'Bestand: {anzahl_sn} Stuecknachweise')
    print(f'\n{len(aenderungen)} Feld(er) {praefix} auf NULL gesetzt (folgen danach der Konfiguration):')
    for sn_id, spalte, alt, grund in aenderungen:
        print(f'  SN {sn_id:>4}  {spalte:<17} {alt!r:<40} -> NULL   [{grund}]')
    if not aenderungen:
        print('  (nichts — bereits bereinigt)')
    print(f'\n{len(offen)} abweichende(r) Wert(e) NICHT angefasst — bitte manuell sichten:')
    for sn_id, kontext, spalte, alt, fb in offen:
        print(f'  SN {sn_id:>4}  {spalte:<17} {alt!r:<40} (Config: {fb!r})  {kontext}')
    if not offen:
        print('  (keine)')
    if uebersprungen:
        print(f'\n{len(uebersprungen)} SN ohne Konfiguration uebersprungen:')
        for sn_id, grund in uebersprungen:
            print(f'  SN {sn_id:>4}  {grund}')


def dry_run(target_db):
    """READ-ONLY Vorabpruefung (sqlite ?mode=ro) — es wird garantiert nichts geschrieben."""
    uri = 'file:' + target_db.replace(os.sep, '/') + '?mode=ro'
    con = sqlite3.connect(uri, uri=True)
    try:
        print(f'DRY-RUN (read-only): {target_db}')
        cols = {r[1] for r in con.execute('PRAGMA table_info(stuecknachweis)')}
        if not {'typbezeichnung', 'art_produkt_text'} <= cols:
            print('FEHLER: stuecknachweis.typbezeichnung/art_produkt_text fehlen — '
                  'vorher migrate_prod_vereinheitlichung.py (M5) ausfuehren')
            return 2
        rows = _lade_sn(con)
        aenderungen, offen, uebersprungen = analysiere(rows)
        _bericht(aenderungen, offen, uebersprungen, len(rows), dry=True)
        return 0
    finally:
        con.close()


def migrate(target_db):
    con = sqlite3.connect(target_db)
    try:
        print(f'MIGRATION: {target_db}')
        cols = {r[1] for r in con.execute('PRAGMA table_info(stuecknachweis)')}
        if not {'typbezeichnung', 'art_produkt_text'} <= cols:
            print('FEHLER: stuecknachweis.typbezeichnung/art_produkt_text fehlen — '
                  'vorher migrate_prod_vereinheitlichung.py (M5) ausfuehren')
            return 2
        rows = _lade_sn(con)
        aenderungen, offen, uebersprungen = analysiere(rows)
        _bericht(aenderungen, offen, uebersprungen, len(rows), dry=False)

        if aenderungen:
            con.execute('BEGIN')
            for sn_id, spalte, _alt, _grund in aenderungen:
                con.execute(f'UPDATE stuecknachweis SET {spalte} = NULL WHERE id = ?', (sn_id,))
            con.commit()

        # Verifikation: zweiter Analyse-Lauf muss leer sein (Idempotenz)
        rest, _, _ = analysiere(_lade_sn(con))
        if rest:
            print(f'\nFEHLER: nach Migration noch {len(rest)} offene Aenderung(en)!')
            return 1
        print(f'\nOK: {len(aenderungen)} Feld(er) bereinigt, Kontrolllauf leer.')
        return 0
    finally:
        con.close()


def main(argv):
    args = [a for a in argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in argv
    if len(args) != 1:
        print(__doc__)
        return 2
    target_db = os.path.abspath(args[0])
    if not os.path.exists(target_db):
        print(f'FEHLER: DB nicht gefunden: {target_db}')
        return 2
    return dry_run(target_db) if dry else migrate(target_db)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main(sys.argv))
