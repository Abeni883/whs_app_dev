"""AP6-Tests: EWH-Detailseite bezieht unzugeordnete Meteostationen ein.

- Projekt MIT unzugeordneter MS: Detailseite listet sie (unassigned_meteostationen)
  und zaehlt sie im Fortschritt -> gleicher Nenner wie die Uebersicht.
- Projekt OHNE unzugeordnete MS: keine Sektion, Verhalten unveraendert.

Statt das vollstaendige Template zu rendern (viele Abhaengigkeiten), wird
render_template gepatcht, um den an das Template uebergebenen Kontext zu pruefen.
"""
import os
import unittest

from tests._util import make_temp_app
from models import db, Project, WHKConfig, EWHMeteostation, TestQuestion, AbnahmeTestResult
import blueprints.ewh as ewhmod
from blueprints.projekte import calculate_all_projects_test_progress


class DetailUnassignedMsTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_temp_app()
        self.app.config['LOGIN_DISABLED'] = True
        self.app.register_blueprint(ewhmod.ewh_bp)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        # 1 Frage je Typ
        self.q = {}
        for i, typ in enumerate(['Anlage', 'WHK', 'Meteostation'], start=1):
            f = TestQuestion(komponente_typ=typ, testszenario='T', frage_nummer=i, frage_text='?', reihenfolge=i)
            db.session.add(f); db.session.flush(); self.q[typ] = f.id
        db.session.commit()
        # render_template patchen: Kontext einfangen, nichts rendern
        self._orig_render = ewhmod.render_template
        self.captured = {}
        def fake_render(template, **ctx):
            self.captured['template'] = template
            self.captured['ctx'] = ctx
            return ''
        ewhmod.render_template = fake_render
        self.client = self.app.test_client()

    def tearDown(self):
        ewhmod.render_template = self._orig_render
        db.session.remove()
        self.ctx.pop()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def _mk_project(self, ms_assigned):
        p = Project(energie='EWH', projektname='P'); db.session.add(p); db.session.flush()
        whk = WHKConfig(projekt_id=p.id, whk_nummer='WHK 01', anzahl_abgaenge=0,
                        anzahl_temperatursonden=0, hat_antriebsheizung=False, preset_typ='kabine_16hz')
        db.session.add(whk); db.session.flush()
        ms = EWHMeteostation(projekt_id=p.id, ms_nummer='MS 01',
                             zugeordnete_whk_id=whk.id if ms_assigned else None)
        db.session.add(ms)
        # Anlage + WHK vollstaendig beantwortet, MS ungetestet
        for typ, idx in [('Anlage', 'Anlage'), ('WHK', 'WHK 01')]:
            db.session.add(AbnahmeTestResult(projekt_id=p.id, test_question_id=self.q[typ],
                                             komponente_index=idx, spalte=idx,
                                             lss_ch_result='richtig', wh_lts_result='richtig'))
        db.session.commit()
        return p

    def test_unzugeordnete_ms_wird_gelistet_und_gezaehlt(self):
        p = self._mk_project(ms_assigned=False)
        r = self.client.get(f'/projekt/abnahmetest/{p.id}')
        self.assertEqual(r.status_code, 200)
        ctx = self.captured['ctx']
        # Sektion vorhanden
        self.assertEqual(len(ctx['unassigned_meteostationen']), 1)
        self.assertEqual(ctx['unassigned_meteostationen'][0]['ms_nummer'], 'MS 01')
        # MS zaehlt im Fortschritt (im meteostationen-Dict enthalten)
        self.assertIn('MS 01', ctx['fortschritt']['meteostationen'])
        # Konsistenz: Uebersicht zaehlt MS ebenfalls -> < 100%
        self.assertEqual(calculate_all_projects_test_progress()[p.id], 66)

    def test_zugeordnete_ms_keine_sektion(self):
        p = self._mk_project(ms_assigned=True)
        r = self.client.get(f'/projekt/abnahmetest/{p.id}')
        self.assertEqual(r.status_code, 200)
        ctx = self.captured['ctx']
        self.assertEqual(ctx['unassigned_meteostationen'], [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
