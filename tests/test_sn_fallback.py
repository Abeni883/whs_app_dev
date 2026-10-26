"""Tests: Stuecknachweis folgt der Konfiguration (Fallback-Muster wie norm_name).

Abgedeckt:
  1. Steuerung: Config-Name/Typ aendern -> bestehender SN zeigt neue Werte
     (Formular + beide PDFs + PDF-Dateiname)
  2. SN-Feld manuell ueberschreiben -> bleibt bei Config-Aenderung erhalten
  3. Ueberschriebenes Feld leeren -> folgt wieder der Config
  4. WHK: whk_typ aendern -> Typbezeichnung + PDF-Dateiname folgen
  5. Speichern normalisiert: Wert == Config-Fallback -> NULL (Formular-POST + Autosave)
  6. Auswahlseite zeigt effektive Werte
  7. Migrationsskript scripts/migrate_sn_fallback.py (inkl. ueber Kreuz, Idempotenz, dry-run)

render_template wird gepatcht, um den Template-Kontext zu pruefen (kein echtes
PDF-Rendering); die Auswahlseite wird einmal echt gerendert.
"""
import os
import sqlite3
import sys
import unittest

from tests._util import make_temp_app
from models import db, Project, WHKConfig, SteuerungConfig, Stuecknachweis
import blueprints.stuecknachweis as snmod

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))
import migrate_sn_fallback as mig  # noqa: E402


class SnFallbackTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_temp_app(register_blueprints=True)
        self.ctx = self.app.app_context(); self.ctx.push()
        db.create_all()
        self._orig = snmod.render_template
        self.cap = {}

        def fake(template, **ctx):
            self.cap['t'] = template; self.cap['ctx'] = ctx; return ''
        snmod.render_template = fake
        self.client = self.app.test_client()

    def tearDown(self):
        snmod.render_template = self._orig
        db.session.remove(); self.ctx.pop()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    # ---- Helpers ----
    def _steuerung(self, name='SHDSL Schnittstelle', typ='SHDSL_Schnittstelle_BUB'):
        p = Project(energie='EWH', projektname='P'); db.session.add(p); db.session.flush()
        st = SteuerungConfig(projekt_id=p.id, name=name, typ=typ, reihenfolge=0)
        db.session.add(st); db.session.commit()
        return p, st

    def _whk(self, whk_typ='WHK_20_SEL_01_16'):
        p = Project(energie='EWH', projektname='P'); db.session.add(p); db.session.flush()
        whk = WHKConfig(projekt_id=p.id, whk_nummer='WHK 01', whk_typ=whk_typ, anzahl_abgaenge=1,
                        anzahl_temperatursonden=1, preset_typ='kabine_16hz')
        db.session.add(whk); db.session.commit()
        return p, whk

    def _sn_steuerung(self, p, st):
        self.client.get(f'/projekt/{p.id}/steuerung/{st.id}/stuecknachweis')
        return Stuecknachweis.query.filter_by(steuerung_config_id=st.id).first()

    def _sn_whk(self, p, whk):
        self.client.get(f'/projekt/{p.id}/whk/{whk.id}/stuecknachweis')
        return Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()

    def _pdf_ctx(self, sn_id, konf=False):
        url = f'/stuecknachweis/{sn_id}/konformitaet/pdf' if konf else f'/stuecknachweis/{sn_id}/pdf'
        resp = self.client.get(url)
        return self.cap['ctx'], resp.headers.get('Content-Disposition', '')

    # ---- 1. Steuerung: Config aendern -> bestehender SN folgt ----
    def test_steuerung_config_aenderung_schlaegt_durch(self):
        p, st = self._steuerung(name='SHDSL Schnittstelle', typ='SHDSL_Schnittstelle_BUB')
        sn = self._sn_steuerung(p, st)
        self.assertIsNone(sn.typbezeichnung); self.assertIsNone(sn.art_produkt_text)
        ctx = self.cap['ctx']
        self.assertEqual(ctx['art_produkt'], 'SHDSL Schnittstelle')          # <- config.name
        self.assertEqual(ctx['typbezeichnung'], 'SHDSL_Schnittstelle_BUB')   # <- config.typ
        self.assertEqual(ctx['art_produkt_fallback'], 'SHDSL Schnittstelle')
        self.assertEqual(ctx['typbezeichnung_fallback'], 'SHDSL_Schnittstelle_BUB')

        # Konfiguration aendern (wie auf der Konfigurationsseite)
        st.name = 'SHDSL Schnittstelle NEU'; st.typ = 'SHDSL_BUB_V2'; db.session.commit()

        self.client.get(f'/projekt/{p.id}/steuerung/{st.id}/stuecknachweis')
        self.assertEqual(self.cap['ctx']['art_produkt'], 'SHDSL Schnittstelle NEU')
        self.assertEqual(self.cap['ctx']['typbezeichnung'], 'SHDSL_BUB_V2')
        for konf in (False, True):
            ctx, cd = self._pdf_ctx(sn.id, konf)
            self.assertEqual(ctx['sn_art_produkt'], 'SHDSL Schnittstelle NEU')
            self.assertEqual(ctx['typbezeichnung'], 'SHDSL_BUB_V2')
            self.assertIn('SHDSL_BUB_V2.pdf', cd)

    # ---- 2./3. Override bleibt bei Config-Aenderung; leeren -> folgt wieder ----
    def test_override_bleibt_und_leeren_folgt_wieder(self):
        p, st = self._steuerung()
        sn = self._sn_steuerung(p, st); sn_id = sn.id
        self.client.post(f'/stuecknachweis/{sn_id}/autosave',
                         json={'typbezeichnung': 'MEIN-TYP', 'art_produkt_text': 'Mein Produkt'})
        sn = Stuecknachweis.query.get(sn_id)
        self.assertEqual(sn.typbezeichnung, 'MEIN-TYP')
        self.assertEqual(sn.art_produkt_text, 'Mein Produkt')

        st = SteuerungConfig.query.get(st.id)
        st.name = 'Anders'; st.typ = 'ANDERS_TYP'; db.session.commit()
        ctx, cd = self._pdf_ctx(sn_id)
        self.assertEqual(ctx['typbezeichnung'], 'MEIN-TYP')
        self.assertEqual(ctx['sn_art_produkt'], 'Mein Produkt')
        self.assertIn('MEIN-TYP.pdf', cd)
        self.client.get(f'/projekt/{p.id}/steuerung/{st.id}/stuecknachweis')
        self.assertEqual(self.cap['ctx']['typbezeichnung'], 'MEIN-TYP')
        self.assertEqual(self.cap['ctx']['typbezeichnung_fallback'], 'ANDERS_TYP')  # placeholder

        # Leeren -> NULL -> folgt wieder der (neuen) Config
        self.client.post(f'/stuecknachweis/{sn_id}/autosave',
                         json={'typbezeichnung': '', 'art_produkt_text': '   '})
        sn = Stuecknachweis.query.get(sn_id)
        self.assertIsNone(sn.typbezeichnung); self.assertIsNone(sn.art_produkt_text)
        ctx, cd = self._pdf_ctx(sn_id, konf=True)
        self.assertEqual(ctx['typbezeichnung'], 'ANDERS_TYP')
        self.assertEqual(ctx['sn_art_produkt'], 'Anders')
        self.assertIn('ANDERS_TYP.pdf', cd)

    # ---- 4. WHK: whk_typ aendern -> Typbezeichnung + Dateiname folgen ----
    def test_whk_typ_aenderung_folgt(self):
        p, whk = self._whk(whk_typ=None)
        sn = self._sn_whk(p, whk)
        self.assertIsNone(sn.typbezeichnung); self.assertIsNone(sn.art_produkt_text)
        self.assertEqual(self.cap['ctx']['typbezeichnung'], 'WHK 01')   # Fallback whk_nummer
        self.assertEqual(self.cap['ctx']['art_produkt'], 'Weichenheizkabine')

        whk = WHKConfig.query.get(whk.id); whk.whk_typ = 'WHK_20_SEL_01_16'; db.session.commit()
        self.client.get(f'/projekt/{p.id}/whk/{whk.id}/stuecknachweis')
        self.assertEqual(self.cap['ctx']['typbezeichnung'], 'WHK_20_SEL_01_16')
        for konf in (False, True):
            ctx, cd = self._pdf_ctx(sn.id, konf)
            self.assertEqual(ctx['typbezeichnung'], 'WHK_20_SEL_01_16')
            self.assertEqual(ctx['sn_art_produkt'], 'Weichenheizkabine')
            self.assertIn('WHK_20_SEL_01_16.pdf', cd)

    # ---- 5. Speichern normalisiert Config-gleiche Werte auf NULL ----
    def test_speichern_normalisiert_auf_null(self):
        p, st = self._steuerung(name='SHDSL Schnittstelle', typ='SHDSL_Schnittstelle_BUB')
        sn = self._sn_steuerung(p, st); sn_id = sn.id
        # Autosave schickt die vorbefuellten Werte (== Config) zurueck -> bleibt NULL
        r = self.client.post(f'/stuecknachweis/{sn_id}/autosave',
                             json={'typbezeichnung': 'SHDSL_Schnittstelle_BUB',
                                   'art_produkt_text': ' SHDSL Schnittstelle '})
        self.assertEqual(r.status_code, 200)
        sn = Stuecknachweis.query.get(sn_id)
        self.assertIsNone(sn.typbezeichnung); self.assertIsNone(sn.art_produkt_text)

        # Formular-POST mit Config-Werten -> bleibt NULL; mit Abweichung -> gespeichert
        self.client.post(f'/projekt/{p.id}/steuerung/{st.id}/stuecknachweis',
                         data={'typbezeichnung': 'SHDSL_Schnittstelle_BUB',
                               'art_produkt_text': 'SHDSL Schnittstelle'})
        sn = Stuecknachweis.query.get(sn_id)
        self.assertIsNone(sn.typbezeichnung); self.assertIsNone(sn.art_produkt_text)
        self.client.post(f'/projekt/{p.id}/steuerung/{st.id}/stuecknachweis',
                         data={'typbezeichnung': 'ABWEICHUNG', 'art_produkt_text': 'SHDSL Schnittstelle'})
        sn = Stuecknachweis.query.get(sn_id)
        self.assertEqual(sn.typbezeichnung, 'ABWEICHUNG'); self.assertIsNone(sn.art_produkt_text)

        # Formular-POST OHNE die Felder (Steuerung ohne typ -> Fallback 'Steuerung')
        st2 = SteuerungConfig(projekt_id=p.id, name=None, typ=None, reihenfolge=1)
        db.session.add(st2); db.session.commit()
        sn2 = self._sn_steuerung(p, st2)
        self.assertEqual(self.cap['ctx']['typbezeichnung'], 'Steuerung')
        self.assertEqual(self.cap['ctx']['art_produkt'], 'Steuerung (SHDSL)')
        self.client.post(f'/stuecknachweis/{sn2.id}/autosave',
                         json={'typbezeichnung': 'Steuerung', 'art_produkt_text': 'Steuerung (SHDSL)'})
        sn2 = Stuecknachweis.query.get(sn2.id)
        self.assertIsNone(sn2.typbezeichnung); self.assertIsNone(sn2.art_produkt_text)

        # WHK: 'Weichenheizkabine' zurueckgeschickt -> NULL
        p2, whk = self._whk()
        snw = self._sn_whk(p2, whk)
        self.client.post(f'/projekt/{p2.id}/whk/{whk.id}/stuecknachweis',
                         data={'typbezeichnung': 'WHK_20_SEL_01_16', 'art_produkt_text': 'Weichenheizkabine'})
        snw = Stuecknachweis.query.get(snw.id)
        self.assertIsNone(snw.typbezeichnung); self.assertIsNone(snw.art_produkt_text)

    # ---- 6. Auswahlseite liefert effektive Werte (Template-Kontext) ----
    def test_auswahl_zeigt_effektive_werte(self):
        p, st = self._steuerung(name='SHDSL Schnittstelle', typ='SHDSL_Schnittstelle_BUB')
        whk = WHKConfig(projekt_id=p.id, whk_nummer='WHK 01', whk_typ='WHK_X', anzahl_abgaenge=1,
                        anzahl_temperatursonden=1, preset_typ='kabine_16hz')
        db.session.add(whk); db.session.commit()
        sn = Stuecknachweis(project_id=p.id, steuerung_config_id=st.id, typbezeichnung='OVERRIDE_TYP')
        db.session.add(sn); db.session.commit()
        self.client.get(f'/projekt/{p.id}/stuecknachweis/whk-auswahl')
        self.assertEqual(self.cap['t'], 'stuecknachweis/whk_auswahl.html')
        st_row = self.cap['ctx']['steuerung_data'][0]
        self.assertEqual(st_row['art_anzeige'], 'SHDSL Schnittstelle')   # Art <- config.name
        self.assertEqual(st_row['typ_anzeige'], 'OVERRIDE_TYP')          # Typ <- SN-Override
        whk_row = self.cap['ctx']['whk_data'][0]
        self.assertEqual(whk_row['typ_anzeige'], 'WHK_X')                # WHK ohne SN: whk_typ

    # ---- 7. Migrationsskript ----
    def test_migration_bereinigt_und_ist_idempotent(self):
        p, st = self._steuerung(name='SHDSL Schnittstelle', typ='SHDSL_Schnittstelle_BUB')
        st2 = SteuerungConfig(projekt_id=p.id, name='Elektrische Steuerung', typ='ES223', reihenfolge=1)
        whk = WHKConfig(projekt_id=p.id, whk_nummer='WHK 01', whk_typ='WHK_20_SEL_01_16', anzahl_abgaenge=1,
                        anzahl_temperatursonden=1, preset_typ='kabine_16hz')
        whk2 = WHKConfig(projekt_id=p.id, whk_nummer='WHK 02', whk_typ=None, anzahl_abgaenge=1,
                         anzahl_temperatursonden=1, preset_typ='kabine_16hz')
        whk3 = WHKConfig(projekt_id=p.id, whk_nummer='WHK 03', whk_typ='WHK_00UP_WE_03_16', anzahl_abgaenge=1,
                         anzahl_temperatursonden=1, preset_typ='kabine_16hz')
        db.session.add_all([st2, whk, whk2, whk3]); db.session.commit()
        rows = [
            # realer Fall: ueber Kreuz (Art = config.typ, Typ = config.name) -> beide NULL
            Stuecknachweis(project_id=p.id, steuerung_config_id=st.id,
                           typbezeichnung='SHDSL Schnittstelle', art_produkt_text='SHDSL_Schnittstelle_BUB'),
            # Alt-Init: Typ = config.typ (T1), Art NULL -> Typ NULL
            Stuecknachweis(project_id=p.id, steuerung_config_id=st2.id, typbezeichnung='ES223'),
            # WHK Alt-Init: beides == Config -> beide NULL
            Stuecknachweis(project_id=p.id, whk_config_id=whk.id,
                           typbezeichnung='WHK_20_SEL_01_16', art_produkt_text='Weichenheizkabine'),
            # WHK ohne whk_typ, bewusste Abweichung bei Art -> Typ NULL, Art bleibt
            Stuecknachweis(project_id=p.id, whk_config_id=whk2.id,
                           typbezeichnung='WHK 02', art_produkt_text='Weichenheizkabine Spezial'),
            # WHK mit spaeter ergaenztem whk_typ: Alt-Init hat whk_nummer kopiert (T4) -> NULL
            Stuecknachweis(project_id=p.id, whk_config_id=whk3.id, typbezeichnung='WHK 03'),
        ]
        db.session.add_all(rows); db.session.commit()
        ids = [r.id for r in rows]
        db.session.remove()

        # dry-run aendert nichts
        self.assertEqual(mig.dry_run(self.db_path), 0)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute(
            'SELECT COUNT(*) FROM stuecknachweis WHERE typbezeichnung IS NOT NULL').fetchone()[0], 5)
        con.close()

        self.assertEqual(mig.migrate(self.db_path), 0)
        con = sqlite3.connect(self.db_path)
        got = {r[0]: (r[1], r[2]) for r in con.execute(
            'SELECT id, typbezeichnung, art_produkt_text FROM stuecknachweis')}
        con.close()
        self.assertEqual(got[ids[0]], (None, None))
        self.assertEqual(got[ids[1]], (None, None))
        self.assertEqual(got[ids[2]], (None, None))
        self.assertEqual(got[ids[3]], (None, 'Weichenheizkabine Spezial'))
        self.assertEqual(got[ids[4]], (None, None))   # T4: whk_nummer-Altwert

        # Idempotent: zweiter Lauf findet nichts, Abweichung bleibt
        self.assertEqual(mig.migrate(self.db_path), 0)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute(
            'SELECT art_produkt_text FROM stuecknachweis WHERE id=?', (ids[3],)).fetchone()[0],
            'Weichenheizkabine Spezial')
        con.close()

        # Nach Bereinigung: realer Fall korrekt zugeordnet (Art = Name, Typ = Typ)
        sn = Stuecknachweis.query.get(ids[0])
        self.assertEqual(sn.effektive_art_produkt, 'SHDSL Schnittstelle')
        self.assertEqual(sn.effektive_typbezeichnung, 'SHDSL_Schnittstelle_BUB')


if __name__ == '__main__':
    unittest.main(verbosity=2)
