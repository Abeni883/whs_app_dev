"""Tests: Prozentanzeige der Buttons EN 61439 und IT-Inventar auf der Projektuebersicht.

Abgedeckt (hermetische Temp-DB, echtes Template-Rendering):
  1. EN: 2 WHK, 1 SN komplett exportiert -> 50 %; nur ein PDF exportiert zaehlt nicht
  2. EN: Steuerungen zaehlen im Nenner mit (WHK + Steuerung)
  3. IT: 1 von 3 SPS erfasst -> 33 %
  4. Projekt ohne WHK/Steuerung -> 0 %, keine Division durch 0
  5. 100 % -> beide Buttons tragen die gruene test-complete-Klasse
  6. GWH-Projekte: weiterhin "—" statt Button; Template rendert mit den neuen Dicts
  7. Query-Anzahl der Bulk-Funktionen unabhaengig von der Projektanzahl (keine N+1)
"""
import os
import re
import unittest
from datetime import datetime

from flask import render_template
from sqlalchemy import event

from tests._util import make_render_app
from models import db, Project, WHKConfig, SteuerungConfig, Stuecknachweis, SpsInfo
from blueprints.projekte import (calculate_all_projects_en61439_progress,
                                 calculate_all_projects_it_progress)


class ButtonProgressTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_render_app()
        self.ctx = self.app.app_context(); self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove(); self.ctx.pop()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    # ---- Helpers ----
    def _projekt(self, name='P', energie='EWH', whks=0, steuerungen=0):
        p = Project(energie=energie, projektname=name)
        db.session.add(p); db.session.flush()
        ws = [WHKConfig(projekt_id=p.id, whk_nummer=f'WHK {i:02d}') for i in range(1, whks + 1)]
        ss = [SteuerungConfig(projekt_id=p.id, name=f'ST {i}', typ='T', reihenfolge=i)
              for i in range(1, steuerungen + 1)]
        db.session.add_all(ws + ss); db.session.commit()
        return p, ws, ss

    def _sn(self, p, whk=None, st=None, sn_pdf=True, konf_pdf=True):
        now = datetime.utcnow()
        sn = Stuecknachweis(project_id=p.id,
                            whk_config_id=whk.id if whk else None,
                            steuerung_config_id=st.id if st else None,
                            pdf_stuecknachweis_exportiert=now if sn_pdf else None,
                            pdf_konformitaet_exportiert=now if konf_pdf else None)
        db.session.add(sn); db.session.commit()
        return sn

    def _sps(self, p, whk, hostname=None, mac=None):
        db.session.add(SpsInfo(project_id=p.id, whk_config_id=whk.id, hostname=hostname, mac_adresse=mac))
        db.session.commit()

    def _render(self, projekte):
        with self.app.test_request_context():
            return render_template('projekte.html', projekte=projekte, progress_dict={},
                                   en_progress_dict=calculate_all_projects_en61439_progress(),
                                   it_progress_dict=calculate_all_projects_it_progress())

    # ---- 1. EN: 1 von 2 WHK komplett ----
    def test_en_halb_fertig(self):
        p, (w1, w2), _ = self._projekt(whks=2)
        self._sn(p, whk=w1)                              # beide PDFs -> 'vorhanden'
        self.assertEqual(calculate_all_projects_en61439_progress()[p.id], 50)
        # Zweites SN nur halb exportiert ('in_arbeit') zaehlt nicht
        self._sn(p, whk=w2, konf_pdf=False)
        self.assertEqual(calculate_all_projects_en61439_progress()[p.id], 50)
        html = self._render([p])
        self.assertIn('title="EN 61439">EN <span class="chip-pct" style="color: #f5a623;">50%</span>', html)
        self.assertNotIn('chip-complete', html)

    # ---- 2. EN: Steuerungen im Nenner ----
    def test_en_steuerungen_zaehlen_mit(self):
        p, (w1, w2), (s1, s2) = self._projekt(whks=2, steuerungen=2)
        self._sn(p, whk=w1); self._sn(p, whk=w2)        # 2 von 4 Einheiten
        self.assertEqual(calculate_all_projects_en61439_progress()[p.id], 50)
        self._sn(p, st=s1)                               # 3 von 4
        self.assertEqual(calculate_all_projects_en61439_progress()[p.id], 75)
        # Waisen-SN (ohne Config) zaehlt nicht
        self._sn(p)
        self.assertEqual(calculate_all_projects_en61439_progress()[p.id], 75)

    # ---- 3. IT: 1 von 3 ----
    def test_it_ein_drittel(self):
        p, (w1, w2, w3), _ = self._projekt(whks=3)
        self._sps(p, w1, hostname='lu-wh-01')
        self._sps(p, w2)                                 # Auto-Init leer -> nicht erfasst
        self.assertEqual(calculate_all_projects_it_progress()[p.id], 33)
        html = self._render([p])
        self.assertIn('title="IT-Inventar">IT <span class="chip-pct" style="color: #e9621f;">33%</span>', html)
        # MAC allein reicht (bestehende Status-Logik)
        self._sps(p, w3, mac='00:01:05:1A:2B:3C')
        self.assertEqual(calculate_all_projects_it_progress()[p.id], 67)

    # ---- 4. Ohne Einheiten -> 0 ----
    def test_ohne_einheiten_null(self):
        p, _, _ = self._projekt(whks=0)
        self.assertEqual(calculate_all_projects_en61439_progress()[p.id], 0)
        self.assertEqual(calculate_all_projects_it_progress()[p.id], 0)
        html = self._render([p])
        self.assertIn('title="EN 61439">EN <span class="chip-pct" style="color: #dc3545;">0%</span>', html)
        self.assertIn('title="IT-Inventar">IT <span class="chip-pct" style="color: #dc3545;">0%</span>', html)
        self.assertEqual(calculate_all_projects_en61439_progress(), {p.id: 0})  # keine Projekte ohne Eintrag

    # ---- 5. 100 % -> gruen ----
    def test_hundert_prozent_gruen(self):
        p, (w1, w2), (s1,) = self._projekt(whks=2, steuerungen=1)
        self._sn(p, whk=w1); self._sn(p, whk=w2); self._sn(p, st=s1)
        self._sps(p, w1, hostname='a'); self._sps(p, w2, mac='b')
        self.assertEqual(calculate_all_projects_en61439_progress()[p.id], 100)
        self.assertEqual(calculate_all_projects_it_progress()[p.id], 100)
        html = self._render([p])
        self.assertIn('class="progress-chip chip-complete" title="EN 61439">', html)
        self.assertIn('class="progress-chip chip-complete" title="IT-Inventar">', html)
        # Farbe bei 100 % = inherit (Makro-Logik), Chip gruen gefuellt
        self.assertIn('EN <span class="chip-pct" style="color: inherit;">100%</span>', html)
        self.assertIn('IT <span class="chip-pct" style="color: inherit;">100%</span>', html)

    # ---- 6. GWH ohne Button, mehrere Projekte ----
    def test_gwh_kein_button_und_mehrere_projekte(self):
        p1, (w1,), _ = self._projekt('A', whks=1)
        p2, _, _ = self._projekt('B', energie='GWH')
        self._sn(p1, whk=w1); self._sps(p1, w1, hostname='x')
        html = self._render([p1, p2])
        self.assertEqual(html.count('class="progress-chip chip-complete" title="EN 61439">'), 1)
        self.assertEqual(html.count('class="progress-chip chip-complete" title="IT-Inventar">'), 1)
        self.assertEqual(html.count('title="IT-Inventar"'), 1)      # GWH: kein IT-Chip
        self.assertEqual(html.count('title="Abnahmetest"'), 2)      # beide Projekte haben AT
        en = calculate_all_projects_en61439_progress()
        self.assertEqual((en[p1.id], en[p2.id]), (100, 0))

    # ---- 7. Keine N+1 ----
    def test_konstante_queryanzahl(self):
        def anzahl_queries(fn):
            zaehler = []
            def hook(conn, cursor, statement, params, context, executemany):
                zaehler.append(statement)
            event.listen(db.engine, 'before_cursor_execute', hook)
            try:
                fn()
            finally:
                event.remove(db.engine, 'before_cursor_execute', hook)
            return len(zaehler)

        for i in range(3):
            p, ws, ss = self._projekt(f'P{i}', whks=2, steuerungen=1)
            self._sn(p, whk=ws[0]); self._sps(p, ws[0], hostname='h')
        db.session.expire_all()
        q_en_3 = anzahl_queries(calculate_all_projects_en61439_progress)
        q_it_3 = anzahl_queries(calculate_all_projects_it_progress)
        for i in range(3, 15):
            p, ws, ss = self._projekt(f'P{i}', whks=2, steuerungen=1)
            self._sn(p, whk=ws[0]); self._sps(p, ws[0], hostname='h')
        db.session.expire_all()
        self.assertEqual(anzahl_queries(calculate_all_projects_en61439_progress), q_en_3)
        self.assertEqual(anzahl_queries(calculate_all_projects_it_progress), q_it_3)
        self.assertLessEqual(q_en_3, 5)
        self.assertLessEqual(q_it_3, 4)


if __name__ == '__main__':
    unittest.main()
