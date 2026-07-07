"""PROD-Waisen-Bereinigung (verwaiste Stuecknachweise nach dem Delete-all-recreate-Bug).

Der Konfig-Speicher-Bug (vor AP1) loeschte beim Speichern ALLE Configs und legte sie
mit NEUEN ids neu an. Stuecknachweise (SN), die an die alte id gebunden waren, wurden
dadurch verwaist. Dieses Skript bereinigt die in PROD gefundenen Waisen GEZIELT:

  UMHAENGEN (an die neue, gueltige Config):
    SN 9  -> whk_config_id 143   (Projekt 36, Typ WHK_20_ST_01_16)
    SN 10 -> whk_config_id 144   (Projekt 36, Typ WHK_20_ST_04_16)

  LOESCHEN (verwaiste Duplikate / gegenstandslose Waisen, inkl. FI-Messungen):
    SN 13  -> Waisen-Duplikat von SN 14 (beide Projekt 29, dieselbe WHK 01 /
              Config 148; SN 13 zeigt auf tote Config 105, aelter, nicht exportiert)
    SN 5, 47, 51, 50, 48, 49  -> verwaiste SN ohne gueltige Ziel-Config

  BEHALTEN (bewusst NICHT anfassen):
    SN 8  (Projekt 35) und SN 21 (Projekt 42) -> jeweils die EINZIGE SN ihres
    Projekts; kein gueltiges Umhaengeziel und kein Duplikat -> bleiben (gemeldet).

SICHERHEIT / ABLAUF:
- DRY-RUN ist Default. Ohne --execute wird NICHTS geaendert (nur Plan ausgegeben).
- IDEMPOTENT: bereits umgehaengte/geloeschte SN werden als "erledigt" erkannt und
  uebersprungen. Mehrfachlauf ist unschaedlich.
- VALIDIERUNG VOR AENDERUNG: erst werden ALLE Vorbedingungen geprueft. Schlaegt eine
  fehl (Ziel-Config fehlt/passt nicht/hat eigene SN; eine "Waise" ist doch gebunden;
  ein Duplikat ist doch keins), wird der GESAMTE Lauf ohne Aenderung abgebrochen.
- Nur sqlite3, keine Flask-/Model-Importe -> laeuft gegen jede DB-Kopie.

VERWENDUNG (immer explizite Ziel-DB angeben — kein Default-Pfad, um Unfaelle mit der
echten PROD-DB zu vermeiden):
    python scripts/bereinige_prod_waisen.py <pfad-zur-db.db>            # Dry-Run
    python scripts/bereinige_prod_waisen.py <pfad-zur-db.db> --execute  # anwenden

REIHENFOLGE ZU M6 (FK-ondelete, migrate_prod_vereinheitlichung.py):
    ZUERST diese Waisen-Bereinigung, DANN M6. Grund: M6 baut stuecknachweis/fi_messungen
    neu auf und aktiviert (mit FK-ON zur Laufzeit) RESTRICT/CASCADE. Laufen die Waisen
    noch mit, meldet PRAGMA foreign_key_check nach M6 Verletzungen. Erst waisenfrei,
    dann FK-Enforcement.

WICHTIG: Dieses Skript aendert PROD-Daten. Ausfuehrung gegen die echte PROD-DB nur nach
ausdruecklicher Freigabe, mit vorherigem Backup und gestopptem Dienst.
"""
import os
import sys
import sqlite3

# (sn_id, ziel_whk_config_id)
REASSIGN = [(9, 143), (10, 144)]
# schlichte Waisen-Loeschungen
DELETE_PLAIN = [5, 47, 51, 50, 48, 49]
# (sn_id, referenz_sn_id): sn_id ist Waisen-Duplikat von referenz_sn_id
DELETE_DUP = [(13, 14)]
# nur Doku: einzige SN ihres Projekts -> bleiben
KEEP = [8, 21]


def main(db_path, execute):
    db_path = os.path.abspath(db_path)
    if not os.path.exists(db_path):
        print(f'FEHLER: DB nicht gefunden: {db_path}')
        return 2

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    def sn(sid):
        return cur.execute('SELECT * FROM stuecknachweis WHERE id=?', (sid,)).fetchone()

    def config(cid):
        return cur.execute('SELECT * FROM whk_configs WHERE id=?', (cid,)).fetchone()

    def config_exists(cid):
        return config(cid) is not None

    def is_whk_orphan(row):
        wid = row['whk_config_id']
        return wid is not None and not config_exists(wid)

    def other_sn_on_config(cid, ausser_sn):
        r = cur.execute(
            'SELECT id FROM stuecknachweis WHERE whk_config_id=? AND id<>?',
            (cid, ausser_sn)).fetchall()
        return [x['id'] for x in r]

    def project_sn_ids(pid):
        return [x['id'] for x in cur.execute(
            'SELECT id FROM stuecknachweis WHERE project_id=?', (pid,)).fetchall()]

    problems = []          # abbruchrelevante Befunde
    plan_reassign = []     # (sid, target)
    plan_delete = []       # sid
    done = []              # bereits erledigt (idempotent)
    keep_report = []

    print(f'Ziel-DB: {db_path}')
    print(f'Modus:   {"EXECUTE (schreibt!)" if execute else "DRY-RUN (keine Aenderung)"}')
    print('-' * 70)

    # ---- Umhaengen validieren ----
    for sid, target in REASSIGN:
        row = sn(sid)
        if row is None:
            done.append(f'SN {sid} nicht vorhanden -> uebersprungen (bereits weg?)')
            continue
        if row['whk_config_id'] == target:
            done.append(f'SN {sid} zeigt bereits auf Config {target} -> erledigt')
            continue
        tgt = config(target)
        if tgt is None:
            problems.append(f'SN {sid}: Ziel-Config {target} existiert NICHT')
            continue
        if tgt['projekt_id'] != row['project_id']:
            problems.append(f'SN {sid} (Projekt {row["project_id"]}): Ziel-Config {target} '
                            f'gehoert zu Projekt {tgt["projekt_id"]} -> Projekt-Mismatch')
            continue
        fremde = other_sn_on_config(target, sid)
        if fremde:
            problems.append(f'SN {sid}: Ziel-Config {target} hat bereits eigene SN {fremde}')
            continue
        if not is_whk_orphan(row):
            problems.append(f'SN {sid}: aktuelle Config {row["whk_config_id"]} ist NICHT '
                            f'verwaist -> unerwartet, kein Umhaengen')
            continue
        if row['typbezeichnung'] != tgt['whk_typ']:
            problems.append(f'SN {sid}: Typ "{row["typbezeichnung"]}" != Ziel-Config-Typ '
                            f'"{tgt["whk_typ"]}" -> passt nicht')
            continue
        plan_reassign.append((sid, target))

    # ---- Schlichte Waisen-Loeschungen validieren ----
    for sid in DELETE_PLAIN:
        row = sn(sid)
        if row is None:
            done.append(f'SN {sid} nicht vorhanden -> uebersprungen (bereits geloescht?)')
            continue
        if not is_whk_orphan(row):
            problems.append(f'SN {sid}: Config {row["whk_config_id"]} existiert -> SN ist '
                            f'NICHT verwaist, wird NICHT geloescht')
            continue
        plan_delete.append(sid)

    # ---- Duplikat-Loeschungen validieren ----
    for sid, ref in DELETE_DUP:
        row = sn(sid)
        if row is None:
            done.append(f'SN {sid} nicht vorhanden -> uebersprungen (bereits geloescht?)')
            continue
        refrow = sn(ref)
        if refrow is None:
            problems.append(f'SN {sid}: Referenz-SN {ref} fehlt -> Duplikat nicht belegbar')
            continue
        if refrow['project_id'] != row['project_id']:
            problems.append(f'SN {sid}: Referenz-SN {ref} in anderem Projekt '
                            f'({refrow["project_id"]} != {row["project_id"]})')
            continue
        if is_whk_orphan(refrow):
            problems.append(f'SN {sid}: Referenz-SN {ref} ist selbst verwaist -> keine '
                            f'gueltige Referenz')
            continue
        if not is_whk_orphan(row):
            problems.append(f'SN {sid}: eigene Config {row["whk_config_id"]} existiert -> '
                            f'nicht verwaist, Loeschung nicht gerechtfertigt')
            continue
        # Semantische Duplikat-Bestaetigung: die gueltige Config von SN {ref}
        # traegt denselben WHK-Namen/-Typ wie SN {sid} -> selbe physische WHK.
        refcfg = config(refrow['whk_config_id'])
        same_whk = refcfg is not None and (
            row['typbezeichnung'] in (refcfg['whk_nummer'], refcfg['whk_typ']))
        if not same_whk:
            problems.append(f'SN {sid}: Typ "{row["typbezeichnung"]}" passt nicht zu '
                            f'Referenz-Config (whk_nummer/typ) von SN {ref} -> '
                            f'Duplikat nicht bestaetigt')
            continue
        plan_delete.append(sid)

    # ---- Behalten (nur melden) ----
    for sid in KEEP:
        row = sn(sid)
        if row is None:
            keep_report.append(f'SN {sid}: nicht (mehr) vorhanden')
            continue
        geschw = project_sn_ids(row['project_id'])
        keep_report.append(
            f'SN {sid} (Projekt {row["project_id"]}): bleibt. Waise={is_whk_orphan(row)}, '
            f'SN im Projekt={geschw}')

    # ---- Ausgabe ----
    if done:
        print('Bereits erledigt / uebersprungen:')
        for m in done:
            print('  -', m)
    print('Geplant: umhaengen:')
    for sid, target in plan_reassign:
        print(f'  - SN {sid} -> Config {target}')
    if not plan_reassign:
        print('  (nichts)')
    print('Geplant: loeschen (inkl. FI-Messungen):')
    for sid in plan_delete:
        fi = cur.execute('SELECT COUNT(*) FROM fi_messungen WHERE stuecknachweis_id=?',
                         (sid,)).fetchone()[0]
        print(f'  - SN {sid} (+ {fi} FI-Messungen)')
    if not plan_delete:
        print('  (nichts)')
    print('Behalten:')
    for m in keep_report:
        print('  -', m)

    if problems:
        print('-' * 70)
        print('ABBRUCH — Vorbedingungen verletzt, KEINE Aenderung:')
        for p in problems:
            print('  !', p)
        con.close()
        return 2

    if not execute:
        print('-' * 70)
        print('DRY-RUN abgeschlossen. Mit --execute anwenden (vorher Backup + Dienst stoppen).')
        con.close()
        return 0

    # ---- Anwenden ----
    for sid, target in plan_reassign:
        cur.execute('UPDATE stuecknachweis SET whk_config_id=? WHERE id=?', (target, sid))
    for sid in plan_delete:
        cur.execute('DELETE FROM fi_messungen WHERE stuecknachweis_id=?', (sid,))
        cur.execute('DELETE FROM stuecknachweis WHERE id=?', (sid,))
    con.commit()

    # ---- Nachverifikation: sind die beruehrten SN nun sauber / weg? ----
    print('-' * 70)
    print('Angewendet. Nachverifikation:')
    rest_waisen = cur.execute(
        'SELECT COUNT(*) FROM stuecknachweis WHERE whk_config_id IS NOT NULL '
        'AND whk_config_id NOT IN (SELECT id FROM whk_configs)').fetchone()[0]
    fi_waisen = cur.execute(
        'SELECT COUNT(*) FROM fi_messungen WHERE stuecknachweis_id NOT IN '
        '(SELECT id FROM stuecknachweis)').fetchone()[0]
    print(f'  Verbleibende SN->whk Waisen gesamt: {rest_waisen} '
          f'(erwartet: {len(KEEP)} bewusst behaltene = SN {KEEP})')
    print(f'  Verwaiste FI-Messungen: {fi_waisen} (erwartet 0)')
    con.close()
    return 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    execute = '--execute' in sys.argv[1:]
    if len(args) != 1:
        print('Aufruf: python scripts/bereinige_prod_waisen.py <db.db> [--execute]')
        sys.exit(2)
    sys.exit(main(args[0], execute))
