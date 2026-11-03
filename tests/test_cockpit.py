"""Tests: Projekt-Cockpit (/projekt/<id>/cockpit).

Abgedeckt (hermetische Temp-DB, echtes Template-Rendering via make_render_app):
  1. EWH-Projekt: 5 Kacheln, Prozente identisch mit den Dicts der Projektuebersicht
  2. GWH-Projekt: nur 3 Kacheln (ohne EN/IT), kein Fehler, GWH-Ziele
  3. Kachel-Links fuehren auf die richtigen Seiten
  4. 100 % -> complete-Klasse auf den Kacheln
  5. Loeschen-Link mit bestehendem Flow (GET projekt_loeschen + confirm), Projekt weg
  6. Projektname in der Uebersicht verlinkt aufs Cockpit (einzige Aenderung dort)
  7. Progress-Funktionen mit projekt_ids liefern dieselben Werte wie die Bulk-Variante
  8. Unbekanntes Projekt -> Redirect zur Uebersicht
"""
import os
import re
import unittest
from datetime import datetime

from flask import render_template

from tests._util import make_render_app
from models import db, Project, WHKConfig, SteuerungConfig, ZSKConfig, Stuecknachweis, SpsInfo
from blueprints.projekte import (calculate_all_projects_test_progress,
                                 calculate_all_projects_en61439_progress,
                                 calculate_all_projects_it_progress)


class CockpitTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_render_app()
        self.ctx = self.app.app_context(); self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove(); self.ctx.pop()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    # ---- Helpers ----
    def _ewh(self, whks=2, steuerungen=1, **felder):
        p = Project(energie='EWH', projektname='Luzern Nord', didok_betriebspunkt='LZN', **felder)
        db.session.add(p); db.session.flush()
        ws = [WHKConfig(projekt_id=p.id, whk_nummer=f'WHK {i:02d}') for i in range(1, whks + 1)]
        ss = [SteuerungConfig(projekt_id=p.id, name=f'ST {i}', typ='T', reihenfolge=i) for i in range(1, steuerungen + 1)]
        db.session.add_all(ws + ss); db.session.commit()
        return p, ws, ss

    def _sn_fertig(self, p, whk=None, st=None):
        now = datetime.utcnow()
        db.session.add(Stuecknachweis(project_id=p.id, whk_config_id=whk.id if whk else None,
                                      steuerung_config_id=st.id if st else None,
                                      pdf_stuecknachweis_exportiert=now, pdf_konformitaet_exportiert=now))
        db.session.commit()

    def _cockpit(self, p):
        return self.client.get(f'/projekt/{p.id}/cockpit')

    @staticmethod
    def _kacheln(html):
        return re.findall(r'<div class="cockpit-card[^"]*" id="(kachel-[a-z0-9]+)"', html)

    @staticmethod
    def _kachel_html(html, kachel_id):
        start = html.index(f'id="{kachel_id}"')
        return html[start:html.index('</a>', start)]

    # ---- 1. EWH: 5 Kacheln, Prozente = Uebersicht ----
    def test_ewh_fuenf_kacheln_prozente_wie_uebersicht(self):
        p, (w1, w2), (s1,) = self._ewh(pruefer_achermann='N. Muster', pruefdatum_text='16.05.2026')
        self._sn_fertig(p, whk=w1)                                        # EN: 1 von 3 -> 33
        db.session.add(SpsInfo(project_id=p.id, whk_config_id=w1.id, hostname='lu-wh-01'))
        db.session.commit()                                               # IT: 1 von 2 -> 50
        r = self._cockpit(p)
        self.assertEqual(r.status_code, 200)
        html = r.text
        self.assertEqual(self._kacheln(html),
                         ['kachel-info', 'kachel-konfiguration', 'kachel-abnahmetest', 'kachel-en61439', 'kachel-itinventar'])
        # Kopf
        self.assertIn('Luzern Nord · LZN', html)
        self.assertIn('energie-badge energie-ewh">EWH<', html)
        self.assertIn('Prüfer: N. Muster', html)
        self.assertIn('Prüfdatum: 16.05.2026', html)
        self.assertIn('Zurück zur Übersicht', html)
        # Bestand
        self.assertIn('2 <small>WHK</small> · 1 <small>Steuerung</small>', html)
        # Prozente identisch mit den Dicts der Uebersicht
        test_pct = calculate_all_projects_test_progress()[p.id]
        en_pct = calculate_all_projects_en61439_progress()[p.id]
        it_pct = calculate_all_projects_it_progress()[p.id]
        self.assertEqual((en_pct, it_pct), (33, 50))
        self.assertIn(f'<span class="cockpit-percent" style="color: #dc3545;">{test_pct}%</span>',
                      self._kachel_html(html, 'kachel-abnahmetest'))
        self.assertIn('style="width: 33%;"', self._kachel_html(html, 'kachel-en61439'))
        self.assertIn('>33%</span>', self._kachel_html(html, 'kachel-en61439'))
        self.assertIn('style="width: 50%;"', self._kachel_html(html, 'kachel-itinventar'))
        self.assertIn('style="color: #f5a623;">50%</span>', self._kachel_html(html, 'kachel-itinventar'))
        self.assertNotIn('cockpit-card complete', html)

    # ---- 2. GWH: ohne EN/IT ----
    def test_gwh_drei_kacheln(self):
        p = Project(energie='GWH', projektname='Gas Süd')
        db.session.add(p); db.session.flush()
        db.session.add_all([ZSKConfig(projekt_id=p.id, zsk_nummer='ZSK 01', reihenfolge=1),
                            ZSKConfig(projekt_id=p.id, zsk_nummer='ZSK 02', reihenfolge=2)])
        db.session.commit()
        r = self._cockpit(p)
        self.assertEqual(r.status_code, 200)
        html = r.text
        self.assertEqual(self._kacheln(html), ['kachel-info', 'kachel-konfiguration', 'kachel-abnahmetest'])
        self.assertIn('energie-badge energie-gwh">GWH<', html)
        self.assertIn('2 <small>ZSK</small>', html)
        self.assertIn(f'/projekt/{p.id}/gwh-konfiguration', html)
        self.assertIn(f'/projekt/{p.id}/gwh-abnahmetest', html)
        self.assertNotIn('stuecknachweis', html)
        self.assertNotIn('it-inventar', html)

    # ---- 3. Kachel-Links ----
    def test_kachel_links(self):
        p, _, _ = self._ewh()
        html = self._cockpit(p).text
        erwartet = {
            'kachel-info': f'/projekt/bearbeiten/{p.id}',
            'kachel-konfiguration': f'/projekt/konfiguration/{p.id}',
            'kachel-abnahmetest': f'/projekt/abnahmetest/{p.id}',
            'kachel-en61439': f'/projekt/{p.id}/stuecknachweis/whk-auswahl',
            'kachel-itinventar': f'/projekt/{p.id}/it-inventar',
        }
        for kachel, ziel in erwartet.items():
            k = self._kachel_html(html, kachel)
            self.assertIn(f'href="{ziel}" class="cockpit-card-link"', k, kachel)
        # Ziele muessen existierende Endpunkte sein (gleich wie die Buttons der Uebersicht)
        with self.app.test_request_context():
            uebersicht = render_template('projekte.html', projekte=[p], progress_dict={},
                                         en_progress_dict={}, it_progress_dict={})
        for ziel in erwartet.values():
            self.assertIn(f'href="{ziel}"', uebersicht, ziel)

    # ---- 4. 100 % gruen ----
    def test_hundert_prozent_complete(self):
        p, (w1, w2), (s1,) = self._ewh()
        self._sn_fertig(p, whk=w1); self._sn_fertig(p, whk=w2); self._sn_fertig(p, st=s1)
        db.session.add_all([SpsInfo(project_id=p.id, whk_config_id=w1.id, hostname='a'),
                            SpsInfo(project_id=p.id, whk_config_id=w2.id, mac_adresse='b')])
        db.session.commit()
        html = self._cockpit(p).text
        self.assertIn('<div class="cockpit-card complete" id="kachel-en61439">', html)
        self.assertIn('<div class="cockpit-card complete" id="kachel-itinventar">', html)
        self.assertIn('<div class="cockpit-card" id="kachel-abnahmetest">', html)   # 0 % -> nicht complete
        self.assertIn('style="color: inherit;">100%</span>', self._kachel_html(html, 'kachel-en61439'))

    # ---- 5. Loeschen-Flow ----
    def test_loeschen_flow(self):
        p, _, _ = self._ewh()
        html = self._cockpit(p).text
        self.assertIn(f'href="/projekt/loeschen/{p.id}" class="cockpit-delete-link"', html)
        self.assertIn("onclick=\"return confirm('Möchten Sie dieses Projekt wirklich löschen?", html)
        self.assertNotIn('kachel-loeschen', html)
        r = self.client.get(f'/projekt/loeschen/{p.id}')
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers['Location'].endswith('/projekte'))
        self.assertIsNone(db.session.get(Project, p.id))
        self.assertEqual(WHKConfig.query.count(), 0)

    # ---- 6. Uebersicht: Projektname verlinkt ----
    def test_uebersicht_projektname_link(self):
        p, _, _ = self._ewh()
        with self.app.test_request_context():
            html = render_template('projekte.html', projekte=[p], progress_dict={},
                                   en_progress_dict={}, it_progress_dict={})
        self.assertIn(f'<a href="/projekt/{p.id}/cockpit" class="cockpit-name-link">Luzern Nord</a>', html)
        # Buttons unveraendert vorhanden
        for cls in ('action-link', 'config-link', 'test-link', 'en61439-link', 'itinventar-link', 'delete-link'):
            self.assertIn(f'class="{cls}', html, cls)

    # ---- 7. projekt_ids-Variante == Bulk ----
    def test_progress_einzelprojekt_gleich_bulk(self):
        p1, (w1, _), (s1,) = self._ewh()
        p2 = Project(energie='EWH', projektname='Zwei'); db.session.add(p2); db.session.flush()
        w3 = WHKConfig(projekt_id=p2.id, whk_nummer='WHK 01'); db.session.add(w3); db.session.commit()
        self._sn_fertig(p1, whk=w1); self._sn_fertig(p2, whk=w3)
        db.session.add(SpsInfo(project_id=p2.id, whk_config_id=w3.id, hostname='x')); db.session.commit()
        for fn in (calculate_all_projects_test_progress, calculate_all_projects_en61439_progress,
                   calculate_all_projects_it_progress):
            bulk = fn()
            self.assertEqual(set(bulk), {p1.id, p2.id})
            self.assertEqual(fn([p1.id]), {p1.id: bulk[p1.id]}, fn.__name__)
            self.assertEqual(fn([p2.id]), {p2.id: bulk[p2.id]}, fn.__name__)
            self.assertEqual(fn([]), {}, fn.__name__)
        self.assertEqual(calculate_all_projects_en61439_progress([p2.id]), {p2.id: 100})
        self.assertEqual(calculate_all_projects_it_progress([p2.id]), {p2.id: 100})

    # ---- 8. Unbekannt ----
    def test_unbekanntes_projekt_redirect(self):
        r = self.client.get('/projekt/9999/cockpit')
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers['Location'].endswith('/projekte'))


if __name__ == '__main__':
    unittest.main()
