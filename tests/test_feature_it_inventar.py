"""Tests: Feature-Schalter «IT-Inventar» (models.AppSettingFlag / FEATURE_IT_INVENTAR).

Abgedeckt (hermetische Temp-DB, echtes Template-Rendering via make_render_app):
  1. Key fehlt komplett (Zustand PROD-DB nach Deployment) -> verhaelt sich wie AUS
  2. Schalter AUS: keine Spalte/kein Button (Menue: nur fuer eingeloggte User gerendert,
     daher im Smoke-Test mit echter app.py geprueft); ALLE Routen des
     Blueprints -> 404 (auch POST/Autosave), ohne Seiteneffekt in der DB
  3. Schalter EIN: alles wie bisher
  4. Projektuebersicht laeuft in beiden Zustaenden
  5. Daten bleiben beim Aus-/Einschalten unveraendert
"""
import os
import unittest

from tests._util import make_render_app, it_inventar_ein
from models import (db, Project, WHKConfig, SpsInfo, AppSettingFlag,
                    get_feature_flag, FEATURE_IT_INVENTAR)


class FeatureItInventarTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_render_app()
        self.ctx = self.app.app_context(); self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        self.p = Project(energie='EWH', projektname='P-Flag')
        db.session.add(self.p); db.session.flush()
        self.whk = WHKConfig(projekt_id=self.p.id, whk_nummer='WHK 01')
        db.session.add(self.whk); db.session.flush()
        db.session.add(SpsInfo(project_id=self.p.id, whk_config_id=self.whk.id, hostname='lu-wh-01'))
        db.session.commit()

    def tearDown(self):
        db.session.remove(); self.ctx.pop()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def _modul_urls(self):
        return ['/it-inventar',
                f'/projekt/{self.p.id}/it-inventar',
                f'/projekt/{self.p.id}/whk/{self.whk.id}/sps']

    def _assert_ausgeblendet(self):
        for url in self._modul_urls():
            self.assertEqual(self.client.get(url).status_code, 404, url)
        r = self.client.post(f'/projekt/{self.p.id}/whk/{self.whk.id}/sps/autosave',
                             json={'hostname': 'geaendert'})
        self.assertEqual(r.status_code, 404)
        db.session.expire_all()
        self.assertEqual(SpsInfo.query.one().hostname, 'lu-wh-01')   # POST hat nichts geschrieben

        r = self.client.get('/projekte')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('it-inventar', r.text)      # kein Link (Menue/Spalte)
        self.assertNotIn('IT-Inventar', r.text)      # auch kein Spaltenkopf
        # uebrige Module unveraendert
        self.assertIn('class="en61439-link"', r.text)

    def test_key_fehlt_verhaelt_sich_wie_aus(self):
        self.assertEqual(AppSettingFlag.query.count(), 0)
        self.assertFalse(get_feature_flag(FEATURE_IT_INVENTAR))
        self._assert_ausgeblendet()

    def test_schalter_aus(self):
        it_inventar_ein(False)
        self.assertEqual(AppSettingFlag.query.count(), 1)
        self._assert_ausgeblendet()

    def test_schalter_ein(self):
        it_inventar_ein()
        for url in self._modul_urls():
            self.assertEqual(self.client.get(url).status_code, 200, url)
        r = self.client.post(f'/projekt/{self.p.id}/whk/{self.whk.id}/sps/autosave',
                             json={'hostname': 'lu-wh-02'})
        self.assertEqual(r.status_code, 200)
        html = self.client.get('/projekte').text
        self.assertIn(f'/projekt/{self.p.id}/it-inventar', html)             # Button
        self.assertIn('<th>IT-Inventar</th>', html)

    def test_aus_und_wieder_ein_daten_bleiben(self):
        it_inventar_ein()
        it_inventar_ein(False)
        self.assertEqual(self.client.get('/it-inventar').status_code, 404)
        it_inventar_ein()
        r = self.client.get(f'/projekt/{self.p.id}/it-inventar')
        self.assertEqual(r.status_code, 200)
        self.assertIn('lu-wh-01', r.text)


if __name__ == '__main__':
    unittest.main()
