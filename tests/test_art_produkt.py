"""Tests fuer getrennte Rollen bei Steuerungs-SN:
  - Typbezeichnung / Kennnummer  <- steuerung_configs.typ  (Vorbefuellung)
  - Art des Produkts (Produktenorm) <- steuerung_configs.name (Fallback) + Override

Muster wie norm_name (Fallback + Override + Autosave). render_template wird
gepatcht, um den Template-Kontext zu pruefen (kein echtes PDF-Rendering).
"""
import os
import unittest

from tests._util import make_temp_app
from models import db, Project, WHKConfig, SteuerungConfig, Stuecknachweis
import blueprints.stuecknachweis as snmod


class ArtProduktTest(unittest.TestCase):
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
        try: os.remove(self.db_path)
        except OSError: pass

    def _steuerung(self, name='Elektrische Steuerung', typ='ES223'):
        p = Project(energie='EWH', projektname='P'); db.session.add(p); db.session.flush()
        st = SteuerungConfig(projekt_id=p.id, name=name, typ=typ, reihenfolge=0)
        db.session.add(st); db.session.commit()
        return p, st

    def _whk(self):
        p = Project(energie='EWH', projektname='P'); db.session.add(p); db.session.flush()
        whk = WHKConfig(projekt_id=p.id, whk_nummer='WHK 01', anzahl_abgaenge=1,
                        anzahl_temperatursonden=1, preset_typ='kabine_16hz')
        db.session.add(whk); db.session.commit()
        return p, whk

    # ---- getrennte Rollen: typ -> Typbezeichnung, name -> Art des Produkts ----
    def test_neuer_sn_getrennte_rollen(self):
        p, st = self._steuerung(name='Elektrische Steuerung', typ='ES223')
        self.client.get(f'/projekt/{p.id}/steuerung/{st.id}/stuecknachweis')
        ctx = self.cap['ctx']
        self.assertTrue(ctx['ist_steuerung'])
        self.assertEqual(ctx['typbezeichnung'], 'ES223')                 # aus config.typ
        self.assertEqual(ctx['art_produkt_fallback'], 'Elektrische Steuerung')  # aus config.name
        # Auto-Init hat Typbezeichnung aus typ gesetzt
        sn = Stuecknachweis.query.filter_by(steuerung_config_id=st.id).first()
        self.assertEqual(sn.typbezeichnung, 'ES223')

    def test_typ_leer_fallback_steuerung(self):
        p, st = self._steuerung(name='Nur Name', typ=None)
        self.client.get(f'/projekt/{p.id}/steuerung/{st.id}/stuecknachweis')
        self.assertEqual(self.cap['ctx']['typbezeichnung'], 'Steuerung')  # Fallback
        self.assertEqual(self.cap['ctx']['art_produkt_fallback'], 'Nur Name')

    def test_bestehende_typbezeichnung_bleibt(self):
        p, st = self._steuerung(typ='ES223')
        # SN mit bereits gespeicherter Typbezeichnung anlegen
        sn = Stuecknachweis(project_id=p.id, steuerung_config_id=st.id, typbezeichnung='ALT-TYP-001')
        db.session.add(sn); db.session.commit(); sn_id = sn.id
        self.client.get(f'/projekt/{p.id}/steuerung/{st.id}/stuecknachweis')
        # Formular gibt den Fallback (config.typ) als Kontext, aber der gespeicherte
        # Wert wird NICHT ueberschrieben.
        self.assertEqual(Stuecknachweis.query.get(sn_id).typbezeichnung, 'ALT-TYP-001')

    # ---- Art des Produkts: PDFs Fallback + Override ----
    def test_pdfs_art_produkt_fallback_und_override(self):
        p, st = self._steuerung(name='Elektrische Steuerung', typ='ES223')
        self.client.get(f'/projekt/{p.id}/steuerung/{st.id}/stuecknachweis')
        sn_id = Stuecknachweis.query.filter_by(steuerung_config_id=st.id).first().id
        # Fallback in beiden PDFs = config.name
        self.client.get(f'/stuecknachweis/{sn_id}/pdf')
        self.assertEqual(self.cap['ctx']['sn_art_produkt'], 'Elektrische Steuerung')
        self.client.get(f'/stuecknachweis/{sn_id}/konformitaet/pdf')
        self.assertEqual(self.cap['ctx']['sn_art_produkt'], 'Elektrische Steuerung')
        # Override
        self.client.post(f'/stuecknachweis/{sn_id}/autosave', json={'art_produkt_text': 'Sonderprodukt Y'})
        self.assertEqual(Stuecknachweis.query.get(sn_id).art_produkt_text, 'Sonderprodukt Y')
        self.client.get(f'/stuecknachweis/{sn_id}/pdf')
        self.assertEqual(self.cap['ctx']['sn_art_produkt'], 'Sonderprodukt Y')
        # Leeren -> Fallback
        self.client.post(f'/stuecknachweis/{sn_id}/autosave', json={'art_produkt_text': ''})
        self.assertIsNone(Stuecknachweis.query.get(sn_id).art_produkt_text)
        self.client.get(f'/stuecknachweis/{sn_id}/pdf')
        self.assertEqual(self.cap['ctx']['sn_art_produkt'], 'Elektrische Steuerung')

    # ---- WHK unveraendert ----
    def test_whk_unveraendert(self):
        p, whk = self._whk()
        self.client.get(f'/projekt/{p.id}/whk/{whk.id}/stuecknachweis')
        self.assertFalse(self.cap['ctx']['ist_steuerung'])
        self.assertIsNone(self.cap['ctx']['art_produkt_fallback'])
        self.assertEqual(self.cap['ctx']['typbezeichnung'], 'WHK 01')  # aus whk_nummer
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        self.client.get(f'/stuecknachweis/{sn.id}/pdf')
        self.assertEqual(self.cap['ctx']['sn_art_produkt'], 'Weichenheizkabine')


if __name__ == '__main__':
    unittest.main(verbosity=2)
