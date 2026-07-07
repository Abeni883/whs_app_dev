"""Tests für FK-Enforcement (AP3): PRAGMA foreign_keys=ON + ondelete-Verhalten.

Zweite Verteidigungslinie zum App-Lösch-Schutz (AP1):
- Direktes DB-Löschen einer Config MIT Stücknachweis -> RESTRICT (IntegrityError).
- Projekt-Löschung -> DB-CASCADE räumt SN + FI ab (kein NOT-NULL-Fehler, keine Waisen).
"""
import os
import unittest

from sqlalchemy.exc import IntegrityError

from tests._util import make_temp_app
from models import (db, Project, WHKConfig, SteuerungConfig,
                    Stuecknachweis, FiMessung)


class FkEnforcementTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_temp_app()
        self.ctx = self.app.app_context(); self.ctx.push()
        db.create_all()
        self.p = Project(energie='EWH', projektname='P')
        db.session.add(self.p); db.session.flush()
        self.whk = WHKConfig(projekt_id=self.p.id, whk_nummer='WHK 01')
        db.session.add(self.whk); db.session.flush()
        self.sn = Stuecknachweis(project_id=self.p.id, whk_config_id=self.whk.id)
        db.session.add(self.sn); db.session.flush()
        db.session.add(FiMessung(stuecknachweis_id=self.sn.id, sicherung='F1'))
        db.session.commit()

    def tearDown(self):
        db.session.remove(); self.ctx.pop()
        try: os.remove(self.db_path)
        except OSError: pass

    def test_pragma_foreign_keys_ist_an(self):
        val = db.session.execute(db.text('PRAGMA foreign_keys')).scalar()
        self.assertEqual(val, 1)

    def test_config_direkt_loeschen_mit_sn_restrict(self):
        # Umgeht den App-Schutz -> DB muss selbst per RESTRICT blocken.
        with self.assertRaises(IntegrityError):
            db.session.execute(db.text(
                'DELETE FROM whk_configs WHERE id=:i'), {'i': self.whk.id})
            db.session.commit()
        db.session.rollback()
        self.assertIsNotNone(db.session.get(WHKConfig, self.whk.id))  # nicht gelöscht
        self.assertIsNotNone(db.session.get(Stuecknachweis, self.sn.id))  # SN erhalten

    def test_projekt_loeschen_cascade_raeumt_sn_und_fi(self):
        # ORM-Projekt-Löschung (App-Pfad) -> DB-CASCADE, keine Waisen, kein NOT-NULL-Fehler.
        db.session.delete(db.session.get(Project, self.p.id))
        db.session.commit()
        self.assertEqual(Project.query.count(), 0)
        self.assertEqual(WHKConfig.query.count(), 0)
        self.assertEqual(Stuecknachweis.query.count(), 0)
        self.assertEqual(FiMessung.query.count(), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
