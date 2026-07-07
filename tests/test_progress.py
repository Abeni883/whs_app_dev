"""Regressionstests fuer die kanonische Projekt-Progressberechnung (AP1 / O-3).

Sichert die vier Ursachen der frueheren DEV-Ueberzaehlung dauerhaft ab:
  1. UND-Logik (beide Systeme muessen gueltig sein), nicht ODER
  2. Stale-Result-Filter (komponente_index muss zur Konfig passen)
  3. Deckelung pro Komponente (min(done, total))
  4. Unzugeordnete Meteostationen zaehlen in den Nenner (Entscheidung O-3)
"""
import os
import unittest

from tests._util import make_temp_app
from models import db, Project, WHKConfig, EWHMeteostation, TestQuestion, AbnahmeTestResult
from blueprints.projekte import calculate_all_projects_test_progress


class ProgressTestBase(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_temp_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        # Je 1 Testfrage pro relevantem Typ (macht die Mathematik trivial)
        self.q = {}
        for i, typ in enumerate(['Anlage', 'WHK', 'Meteostation'], start=1):
            frage = TestQuestion(komponente_typ=typ, testszenario='T', frage_nummer=i,
                                 frage_text='?', reihenfolge=i)
            db.session.add(frage)
            db.session.flush()
            self.q[typ] = frage.id
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    # Helfer
    def mk_ewh(self, whk_nummer='WHK 01', ms_assigned=True, add_ms=True):
        p = Project(energie='EWH', projektname='P')
        db.session.add(p)
        db.session.flush()
        whk = WHKConfig(projekt_id=p.id, whk_nummer=whk_nummer, anzahl_abgaenge=0,
                        anzahl_temperatursonden=0, hat_antriebsheizung=False,
                        preset_typ='kabine_16hz')
        db.session.add(whk)
        db.session.flush()
        if add_ms:
            ms = EWHMeteostation(projekt_id=p.id, ms_nummer='MS 01',
                                 zugeordnete_whk_id=whk.id if ms_assigned else None)
            db.session.add(ms)
        db.session.commit()
        return p, whk

    def result(self, pid, typ, index, lss, wh):
        db.session.add(AbnahmeTestResult(
            projekt_id=pid, test_question_id=self.q[typ], komponente_index=index,
            spalte=index, lss_ch_result=lss, wh_lts_result=wh))
        db.session.commit()

    def progress(self, pid):
        return calculate_all_projects_test_progress()[pid]


class TestAndLogic(ProgressTestBase):
    def test_ein_system_zaehlt_nicht(self):
        """UND-Logik: nur ein System beantwortet -> NICHT als erledigt gezaehlt."""
        p, whk = self.mk_ewh()
        # Anlage nur auf lss_ch beantwortet, wh_lts leer
        self.result(p.id, 'Anlage', 'Anlage', 'richtig', None)
        # expected = Anlage1 + WHK1 + MS1 = 3, completed = 0
        self.assertEqual(self.progress(p.id), 0)

    def test_beide_systeme_zaehlt(self):
        p, whk = self.mk_ewh()
        self.result(p.id, 'Anlage', 'Anlage', 'richtig', 'richtig')  # 1 von 3
        self.assertEqual(self.progress(p.id), 33)


class TestStaleFilter(ProgressTestBase):
    def test_stale_index_wird_ignoriert(self):
        """WHK-Ergebnis mit Index, der nicht zur Konfig passt, zaehlt nicht."""
        p, whk = self.mk_ewh(whk_nummer='WHK 01')
        self.result(p.id, 'WHK', 'WHK 99', 'richtig', 'richtig')  # stale
        # WHK-Komponente bleibt 0 -> Gesamt completed 0
        self.assertEqual(self.progress(p.id), 0)

    def test_passender_index_zaehlt(self):
        p, whk = self.mk_ewh(whk_nummer='WHK 01')
        self.result(p.id, 'WHK', 'WHK 01', 'richtig', 'richtig')  # 1 von 3
        self.assertEqual(self.progress(p.id), 33)


class TestDeckelung(ProgressTestBase):
    def test_deckelung_pro_komponente(self):
        """Mehr gueltige Ergebnisse als Total -> auf Total gedeckelt (kein >100%)."""
        p, whk = self.mk_ewh(whk_nummer='WHK 01')
        # 3 gueltige WHK-Ergebnisse fuer dieselbe (einzige) WHK-Frage/Spalte
        for _ in range(3):
            self.result(p.id, 'WHK', 'WHK 01', 'richtig', 'richtig')
        # WHK-Total = 1 -> done gedeckelt auf 1; Gesamt: 1 von 3
        self.assertEqual(self.progress(p.id), 33)


class TestUnzugeordneteMS(ProgressTestBase):
    def test_unzugeordnete_ms_zaehlt_in_nenner(self):
        """Entscheidung O-3: unzugeordnete MS zaehlt in den Nenner -> < 100%."""
        p, whk = self.mk_ewh(ms_assigned=False)  # MS existiert, aber nicht zugeordnet
        # Anlage + WHK beide vollstaendig beantwortet, MS ungetestet
        self.result(p.id, 'Anlage', 'Anlage', 'richtig', 'richtig')
        self.result(p.id, 'WHK', 'WHK 01', 'richtig', 'richtig')
        # expected = 3 (Anlage+WHK+MS), completed = 2 -> 66%, NICHT 100%
        self.assertEqual(self.progress(p.id), 66)

    def test_ohne_ms_voll_beantwortet_100(self):
        p, whk = self.mk_ewh(add_ms=False)  # keine MS
        self.result(p.id, 'Anlage', 'Anlage', 'richtig', 'richtig')
        self.result(p.id, 'WHK', 'WHK 01', 'richtig', 'richtig')
        # expected = 2 (Anlage+WHK), completed = 2 -> 100%
        self.assertEqual(self.progress(p.id), 100)

    def test_ewh_ohne_whk_ist_0(self):
        p = Project(energie='EWH', projektname='leer')
        db.session.add(p)
        db.session.commit()
        self.assertEqual(self.progress(p.id), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
