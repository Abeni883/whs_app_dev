"""Tests fuer die typabhaengige FI-Loeschregel (AP2 / O-4a).

- WHK-Stuecknachweis: letzte FI darf NICHT geloescht werden (HTTP 400).
- WHK-Stuecknachweis mit mehreren FI: eine loeschen ist OK.
- Steuerungs-Stuecknachweis: alle FI loeschen (auch die letzte) ist OK.
"""
import os
import unittest

from tests._util import make_temp_app
from models import db, Project, WHKConfig, SteuerungConfig, Stuecknachweis, FiMessung


class FiRuleTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_temp_app(register_blueprints=True)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def _projekt(self):
        p = Project(energie='EWH', projektname='P')
        db.session.add(p)
        db.session.flush()
        return p

    def _sn_whk(self, n_fi):
        p = self._projekt()
        whk = WHKConfig(projekt_id=p.id, whk_nummer='WHK 01', anzahl_abgaenge=1,
                        anzahl_temperatursonden=1, preset_typ='kabine_16hz')
        db.session.add(whk)
        db.session.flush()
        sn = Stuecknachweis(project_id=p.id, whk_config_id=whk.id)
        db.session.add(sn)
        db.session.flush()
        fis = []
        for i in range(n_fi):
            fi = FiMessung(stuecknachweis_id=sn.id, sicherung=f'F{i}', reihenfolge=i)
            db.session.add(fi)
            fis.append(fi)
        db.session.commit()
        return sn, fis

    def _sn_steuerung(self, n_fi):
        p = self._projekt()
        st = SteuerungConfig(projekt_id=p.id, name='ST', reihenfolge=0)
        db.session.add(st)
        db.session.flush()
        sn = Stuecknachweis(project_id=p.id, steuerung_config_id=st.id)
        db.session.add(sn)
        db.session.flush()
        fis = []
        for i in range(n_fi):
            fi = FiMessung(stuecknachweis_id=sn.id, sicherung=f'F{i}', reihenfolge=i)
            db.session.add(fi)
            fis.append(fi)
        db.session.commit()
        return sn, fis

    def _delete(self, sn_id, fi_id):
        return self.client.post(f'/stuecknachweis/{sn_id}/fi/{fi_id}/delete')

    def test_whk_letzte_fi_loeschen_400(self):
        sn, fis = self._sn_whk(1)
        r = self._delete(sn.id, fis[0].id)
        self.assertEqual(r.status_code, 400)
        self.assertFalse(r.get_json()['success'])
        self.assertEqual(FiMessung.query.filter_by(stuecknachweis_id=sn.id).count(), 1)

    def test_whk_eine_von_mehreren_loeschen_ok(self):
        sn, fis = self._sn_whk(3)
        r = self._delete(sn.id, fis[0].id)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()['success'])
        self.assertEqual(FiMessung.query.filter_by(stuecknachweis_id=sn.id).count(), 2)

    def test_steuerung_alle_fi_loeschen_ok(self):
        sn, fis = self._sn_steuerung(1)
        r = self._delete(sn.id, fis[0].id)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()['success'])
        self.assertEqual(FiMessung.query.filter_by(stuecknachweis_id=sn.id).count(), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
