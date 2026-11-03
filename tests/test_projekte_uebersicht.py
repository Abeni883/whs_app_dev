"""Tests: verschlankte Projektuebersicht (templates/projekte.html).

Abgedeckt (hermetische Temp-DB, echtes Rendering ueber die Route /projekte):
  1. Spalten: Energie | Projektname | Fortschritt | Aktionen; alte Button-Spalten weg
  2. Zeile traegt data-href aufs Cockpit, Name "Projektname · DIDOK" ohne eigenen Link
  3. Chips: EWH = AT/EN/IT mit Direktlinks + Tooltips; GWH = nur AT (GWH-Ziel)
  4. 100 % -> chip-complete; Farbe aus dem Makro
  5. ⋮-Menue: Bearbeiten, Konfiguration (EWH/GWH-Ziel), Loeschen (rot, confirm) — Loesch-Flow
  6. Suche/JS: Suchfeld vorhanden, Zeilen-Klick-Script mit stopPropagation, Name in Spalte 1
"""
import os
import re
import unittest
from datetime import datetime

from tests._util import make_render_app
from models import db, Project, WHKConfig, SteuerungConfig, Stuecknachweis, SpsInfo


class ProjekteUebersichtTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_render_app()
        self.ctx = self.app.app_context(); self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        self.ewh = Project(energie='EWH', projektname='Luzern Nord', didok_betriebspunkt='LZN')
        self.gwh = Project(energie='GWH', projektname='Gas Süd')
        db.session.add_all([self.ewh, self.gwh]); db.session.flush()
        self.whk = WHKConfig(projekt_id=self.ewh.id, whk_nummer='WHK 01')
        db.session.add(self.whk); db.session.commit()

    def tearDown(self):
        db.session.remove(); self.ctx.pop()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def _html(self):
        r = self.client.get('/projekte')
        self.assertEqual(r.status_code, 200)
        return r.text

    @staticmethod
    def _zeile(html, name):
        start = html.index(f'<strong>{name}</strong>')
        start = html.rindex('<tr class="project-row"', 0, start)
        return html[start:html.index('</tr>', start)]

    # ---- 1. Spalten ----
    def test_spalten(self):
        html = self._html()
        kopf = re.findall(r'<th>(.*?)</th>', html[html.index('<thead>'):html.index('</thead>')])
        self.assertEqual(kopf, ['Energie', 'Projektname', 'Fortschritt', 'Aktionen'])
        for alt in ('<th>Projektinformationen</th>', '<th>WH-Anlage</th>', '<th>Abnahmetest</th>',
                    '<th>Löschen</th>', 'class="en61439-link', 'class="itinventar-link', 'class="test-link',
                    'class="config-link"', 'class="action-link"', 'class="delete-link"'):
            self.assertNotIn(alt, html, alt)
        self.assertIn('Neues Projekt anlegen', html)
        self.assertIn('id="searchInput"', html)

    # ---- 2. Zeile -> Cockpit ----
    def test_zeile_cockpit_link(self):
        z = self._zeile(self._html(), 'Luzern Nord')
        self.assertTrue(z.startswith(f'<tr class="project-row" data-href="/projekt/{self.ewh.id}/cockpit"'))
        self.assertIn('tabindex="0"', z)
        self.assertIn('<strong>Luzern Nord</strong><span class="projekt-didok"> · LZN</span>', z)
        self.assertNotIn('/cockpit"', z.replace(f'data-href="/projekt/{self.ewh.id}/cockpit"', ''))  # kein zweiter Link
        # Name steht in Spalte 1 (Index 1) -> Live-Suche unveraendert
        zellen = re.findall(r'<td[^>]*>', z)
        self.assertEqual(len(zellen), 4)
        self.assertIn('class="projekt-name-zelle"', zellen[1])

    # ---- 3. Chips EWH/GWH ----
    def test_chips_ewh_und_gwh(self):
        html = self._html()
        ze = self._zeile(html, 'Luzern Nord')
        self.assertIn(f'<a href="/projekt/abnahmetest/{self.ewh.id}" class="progress-chip" title="Abnahmetest">AT <span class="chip-pct"', ze)
        self.assertIn(f'<a href="/projekt/{self.ewh.id}/stuecknachweis/whk-auswahl" class="progress-chip" title="EN 61439">EN <span class="chip-pct"', ze)
        self.assertIn(f'<a href="/projekt/{self.ewh.id}/it-inventar" class="progress-chip" title="IT-Inventar">IT <span class="chip-pct"', ze)
        self.assertEqual(ze.count('class="progress-chip'), 3)
        zg = self._zeile(html, 'Gas Süd')
        self.assertIn(f'<a href="/projekt/{self.gwh.id}/gwh-abnahmetest" class="progress-chip" title="Abnahmetest">AT <span class="chip-pct"', zg)
        self.assertEqual(zg.count('class="progress-chip'), 1)
        self.assertNotIn('title="EN 61439"', zg); self.assertNotIn('title="IT-Inventar"', zg)

    # ---- 4. 100 % ----
    def test_chip_complete(self):
        now = datetime.utcnow()
        db.session.add(Stuecknachweis(project_id=self.ewh.id, whk_config_id=self.whk.id,
                                      pdf_stuecknachweis_exportiert=now, pdf_konformitaet_exportiert=now))
        db.session.add(SpsInfo(project_id=self.ewh.id, whk_config_id=self.whk.id, hostname='lu-wh-01'))
        db.session.commit()
        ze = self._zeile(self._html(), 'Luzern Nord')
        self.assertIn('class="progress-chip chip-complete" title="EN 61439">EN <span class="chip-pct" style="color: inherit;">100%</span>', ze)
        self.assertIn('class="progress-chip chip-complete" title="IT-Inventar">IT <span class="chip-pct" style="color: inherit;">100%</span>', ze)
        self.assertIn('class="progress-chip" title="Abnahmetest">AT <span class="chip-pct" style="color: #dc3545;">0%</span>', ze)

    # ---- 5. Aktionsmenue + Loesch-Flow ----
    def test_aktionsmenue(self):
        html = self._html()
        ze = self._zeile(html, 'Luzern Nord')
        self.assertIn('<button type="button" class="row-menu-toggle" aria-haspopup="true" aria-expanded="false" title="Aktionen">⋮</button>', ze)
        self.assertIn(f'<a href="/projekt/bearbeiten/{self.ewh.id}">Bearbeiten</a>', ze)
        self.assertIn(f'<a href="/projekt/konfiguration/{self.ewh.id}">Konfiguration</a>', ze)
        self.assertIn(f'<a href="/projekt/loeschen/{self.ewh.id}" class="row-menu-delete" onclick="return confirm(', ze)
        zg = self._zeile(html, 'Gas Süd')
        self.assertIn(f'<a href="/projekt/{self.gwh.id}/gwh-konfiguration">Konfiguration</a>', zg)
        self.assertIn(f'<a href="/projekt/loeschen/{self.gwh.id}" class="row-menu-delete"', zg)
        # Loesch-Flow unveraendert (GET-Route, Redirect zur Uebersicht)
        r = self.client.get(f'/projekt/loeschen/{self.gwh.id}')
        self.assertEqual(r.status_code, 302)
        self.assertIsNone(db.session.get(Project, self.gwh.id))

    # ---- 6. JS-Verhalten (statisch) ----
    def test_js_zeilenklick_und_menue(self):
        html = self._html()
        js = html[html.index("// Klickbare Zeilen"):html.index('</script>', html.index("// Klickbare Zeilen"))]
        self.assertIn("e.stopPropagation()", js)
        self.assertIn("'.progress-chip, .row-menu-dropdown a'", js)
        self.assertIn("closest('a, button, .row-menu')", js)
        self.assertIn("row.dataset.href", js)
        self.assertIn("schliesseAlleMenues", js)
        self.assertIn("document.addEventListener('click'", js)
        # Live-Suche: Projektname weiterhin aus Spalte Index 1
        self.assertIn("cells[1]?.textContent", html)


if __name__ == '__main__':
    unittest.main()
