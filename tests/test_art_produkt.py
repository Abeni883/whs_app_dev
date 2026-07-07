"""Tests fuer "Art des Produkts (Produktenorm)" bei Steuerungs-SN.

Muster wie norm_name: Fallback (Config-Name) + Override + Autosave.
- Steuerung ohne Override: Formular + beide PDFs zeigen den Config-Namen.
- Override: persistiert, PDFs zeigen Override; Feld geleert -> Fallback.
- WHK-SN: kein Feld, PDFs unveraendert ('Weichenheizkabine').

render_template wird gepatcht, um den an die Templates uebergebenen Kontext
(sn_art_produkt / art_produkt_fallback) zu pruefen — ohne echtes PDF-Rendering.
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
        # render_template patchen -> Kontext einfangen
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

    def _steuerung_sn(self, name='Steuerung ABC', art=None):
        p = Project(energie='EWH', projektname='P'); db.session.add(p); db.session.flush()
        st = SteuerungConfig(projekt_id=p.id, name=name, reihenfolge=0); db.session.add(st); db.session.flush()
        sn = Stuecknachweis(project_id=p.id, steuerung_config_id=st.id, art_produkt_text=art)
        db.session.add(sn); db.session.commit()
        return p, st, sn

    def _whk_sn(self):
        p = Project(energie='EWH', projektname='P'); db.session.add(p); db.session.flush()
        whk = WHKConfig(projekt_id=p.id, whk_nummer='WHK 01', anzahl_abgaenge=1,
                        anzahl_temperatursonden=1, preset_typ='kabine_16hz'); db.session.add(whk); db.session.flush()
        sn = Stuecknachweis(project_id=p.id, whk_config_id=whk.id); db.session.add(sn); db.session.commit()
        return p, whk, sn

    # ---- Steuerung: Fallback ----
    def test_steuerung_formular_fallback(self):
        p, st, sn = self._steuerung_sn()
        self.client.get(f'/projekt/{p.id}/steuerung/{st.id}/stuecknachweis')
        ctx = self.cap['ctx']
        self.assertTrue(ctx['ist_steuerung'])
        self.assertEqual(ctx['art_produkt_fallback'], 'Steuerung ABC')  # Config-Name

    def test_steuerung_pdfs_fallback(self):
        p, st, sn = self._steuerung_sn()
        self.client.get(f'/stuecknachweis/{sn.id}/pdf')
        self.assertEqual(self.cap['ctx']['sn_art_produkt'], 'Steuerung ABC')
        self.client.get(f'/stuecknachweis/{sn.id}/konformitaet/pdf')
        self.assertEqual(self.cap['ctx']['sn_art_produkt'], 'Steuerung ABC')

    # ---- Steuerung: Override + Leeren ----
    def test_override_persist_und_leeren(self):
        p, st, sn = self._steuerung_sn()
        sn_id = sn.id
        # Override via Autosave
        r = self.client.post(f'/stuecknachweis/{sn_id}/autosave', json={'art_produkt_text': 'Sonderprodukt Y'})
        self.assertTrue(r.get_json()['success'])
        self.assertEqual(Stuecknachweis.query.get(sn_id).art_produkt_text, 'Sonderprodukt Y')
        self.client.get(f'/stuecknachweis/{sn_id}/pdf')
        self.assertEqual(self.cap['ctx']['sn_art_produkt'], 'Sonderprodukt Y')
        # Feld leeren -> Fallback
        r = self.client.post(f'/stuecknachweis/{sn_id}/autosave', json={'art_produkt_text': ''})
        self.assertIsNone(Stuecknachweis.query.get(sn_id).art_produkt_text)
        self.client.get(f'/stuecknachweis/{sn_id}/konformitaet/pdf')
        self.assertEqual(self.cap['ctx']['sn_art_produkt'], 'Steuerung ABC')

    # ---- WHK: unveraendert ----
    def test_whk_kein_feld_und_pdf_unveraendert(self):
        p, whk, sn = self._whk_sn()
        self.client.get(f'/projekt/{p.id}/whk/{whk.id}/stuecknachweis')
        self.assertFalse(self.cap['ctx']['ist_steuerung'])
        self.assertIsNone(self.cap['ctx']['art_produkt_fallback'])
        self.client.get(f'/stuecknachweis/{sn.id}/pdf')
        self.assertEqual(self.cap['ctx']['sn_art_produkt'], 'Weichenheizkabine')


if __name__ == '__main__':
    unittest.main(verbosity=2)
