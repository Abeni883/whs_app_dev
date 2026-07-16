"""Tests für Upsert-Konfig-Speicherung (AP1) + Lösch-Schutz + Regression.

Deckt ab:
- Umbenennen einer Config → Id stabil, Stücknachweis-Bindung bleibt.
- Config ohne SN entfernen → gelöscht; mit SN → Fehlermeldung, nichts gelöscht/verwaist.
- Original-Symptom (Regression): zwei Steuerungen, Konfig erneut speichern → beide
  SN zeigen ihre eigene Config, keine Waisen, Ids stabil.
"""
import os
import unittest

from tests._util import make_temp_app
from models import db, Project, WHKConfig, SteuerungConfig, Stuecknachweis
from blueprints.konfiguration import (reconcile_whk_configs, reconcile_steuerung_configs,
                                      konfiguration_bp, KonfigLoeschSchutz)


class ConfigUpsertTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_temp_app()
        self.app.register_blueprint(konfiguration_bp)
        self.ctx = self.app.app_context(); self.ctx.push()
        db.create_all()
        self.p = Project(energie='EWH', projektname='P')
        db.session.add(self.p); db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove(); self.ctx.pop()
        try: os.remove(self.db_path)
        except OSError: pass

    # ---------- Steuerung ----------
    def test_umbenennen_id_stabil_bindung_bleibt(self):
        reconcile_steuerung_configs(self.p.id, [{'name': 'A', 'typ': 'TA'}]); db.session.commit()
        st = SteuerungConfig.query.filter_by(projekt_id=self.p.id).one()
        sid = st.id
        db.session.add(Stuecknachweis(project_id=self.p.id, steuerung_config_id=sid, typbezeichnung='X'))
        db.session.commit()
        # Umbenennen mit Id
        reconcile_steuerung_configs(self.p.id, [{'id': sid, 'name': 'A-neu', 'typ': 'TA2'}]); db.session.commit()
        st2 = SteuerungConfig.query.get(sid)
        self.assertIsNotNone(st2)                 # Id stabil
        self.assertEqual(st2.name, 'A-neu')
        sn = Stuecknachweis.query.filter_by(steuerung_config_id=sid).one()
        self.assertEqual(sn.typbezeichnung, 'X')  # Bindung + Daten bleiben

    def test_entfernen_ohne_sn_ok(self):
        reconcile_steuerung_configs(self.p.id, [{'name': 'A', 'typ': 'TA'}, {'name': 'B', 'typ': 'TB'}])
        db.session.commit()
        ids = [c.id for c in SteuerungConfig.query.order_by(SteuerungConfig.id)]
        # nur A behalten
        reconcile_steuerung_configs(self.p.id, [{'id': ids[0], 'name': 'A', 'typ': 'TA'}]); db.session.commit()
        self.assertEqual(SteuerungConfig.query.count(), 1)
        self.assertIsNone(SteuerungConfig.query.get(ids[1]))

    def test_entfernen_mit_sn_wird_geschuetzt(self):
        reconcile_steuerung_configs(self.p.id, [{'name': 'A', 'typ': 'TA'}]); db.session.commit()
        sid = SteuerungConfig.query.one().id
        db.session.add(Stuecknachweis(project_id=self.p.id, steuerung_config_id=sid)); db.session.commit()
        with self.assertRaises(KonfigLoeschSchutz):
            reconcile_steuerung_configs(self.p.id, [])  # A fehlt -> müsste gelöscht werden
        db.session.rollback()
        self.assertIsNotNone(SteuerungConfig.query.get(sid))  # nicht gelöscht/verwaist

    # ---------- WHK ----------
    def test_whk_entfernen_mit_sn_geschuetzt(self):
        reconcile_whk_configs(self.p.id, [{'whk_nummer': 'WHK 01'}]); db.session.commit()
        wid = WHKConfig.query.one().id
        db.session.add(Stuecknachweis(project_id=self.p.id, whk_config_id=wid)); db.session.commit()
        with self.assertRaises(KonfigLoeschSchutz):
            reconcile_whk_configs(self.p.id, [{'whk_nummer': 'WHK 99'}])  # id 01 fehlt -> Schutz
        db.session.rollback()
        self.assertIsNotNone(WHKConfig.query.get(wid))

    # ---------- Regression: Original-Symptom ----------
    def test_regression_zwei_steuerungen_resave_keine_waisen(self):
        # 2 Steuerungen anlegen, je 1 SN
        reconcile_steuerung_configs(self.p.id, [{'name': 'Steuerung 1', 'typ': 'T1'},
                                                {'name': 'Steuerung 2', 'typ': 'T2'}])
        db.session.commit()
        c1, c2 = SteuerungConfig.query.order_by(SteuerungConfig.reihenfolge).all()
        db.session.add(Stuecknachweis(project_id=self.p.id, steuerung_config_id=c1.id, typbezeichnung='SN1'))
        db.session.add(Stuecknachweis(project_id=self.p.id, steuerung_config_id=c2.id, typbezeichnung='SN2'))
        db.session.commit()
        # Konfig erneut speichern (Frontend sendet Ids)
        reconcile_steuerung_configs(self.p.id, [{'id': c1.id, 'name': 'Steuerung 1', 'typ': 'T1'},
                                                {'id': c2.id, 'name': 'Steuerung 2', 'typ': 'T2'}])
        db.session.commit()
        # Ids stabil, SN zeigen weiter auf IHRE Config
        self.assertEqual(SteuerungConfig.query.count(), 2)
        sn1 = Stuecknachweis.query.filter_by(steuerung_config_id=c1.id).one()
        sn2 = Stuecknachweis.query.filter_by(steuerung_config_id=c2.id).one()
        self.assertEqual(sn1.typbezeichnung, 'SN1')
        self.assertEqual(sn2.typbezeichnung, 'SN2')
        # Keine Waisen
        waisen = Stuecknachweis.query.filter(
            Stuecknachweis.steuerung_config_id.isnot(None),
            ~Stuecknachweis.steuerung_config_id.in_(
                db.session.query(SteuerungConfig.id))).count()
        self.assertEqual(waisen, 0)

    # ---------- Id-Rückschreibung / Save ohne Id (UNIQUE-Symptom) ----------
    def test_zweiter_save_ohne_id_kein_unique_fehler_id_stabil(self):
        """Symptom: 'UNIQUE constraint failed: whk_configs.projekt_id, whk_configs.whk_nummer'.

        Trat auf, weil die Antwort keine Ids lieferte -> die neue Zeile sendete
        weiter id=null -> INSERT eines Duplikats (vor dem DELETE, via Autoflush).
        """
        reconcile_whk_configs(self.p.id, [{'whk_nummer': 'WHK 01'}]); db.session.commit()
        wid = WHKConfig.query.one().id
        # Zweiter Save derselben Zeile, immer noch ohne Id
        ids = reconcile_whk_configs(self.p.id, [{'whk_nummer': 'WHK 01', 'anzahl_abgaenge': 3}])
        db.session.commit()
        self.assertEqual(ids, [wid])                  # gematcht statt neu angelegt
        self.assertEqual(WHKConfig.query.count(), 1)  # kein Duplikat, kein Churn
        self.assertEqual(WHKConfig.query.one().anzahl_abgaenge, 3)

    def test_save_ohne_id_loest_keinen_loeschschutz_aus_und_haelt_sn(self):
        """Ohne Fix hätte der id=null-Save die Config gelöscht -> Schutz-400 mitten
        im normalen Bearbeiten, bzw. eine verwaiste SN."""
        reconcile_whk_configs(self.p.id, [{'whk_nummer': 'WHK 01'}]); db.session.commit()
        wid = WHKConfig.query.one().id
        db.session.add(Stuecknachweis(project_id=self.p.id, whk_config_id=wid, typbezeichnung='SN'))
        db.session.commit()
        reconcile_whk_configs(self.p.id, [{'whk_nummer': 'WHK 01'}]); db.session.commit()
        self.assertIsNotNone(WHKConfig.query.get(wid))
        self.assertEqual(Stuecknachweis.query.filter_by(whk_config_id=wid).count(), 1)

    def test_umbenennen_gibt_nummer_frei_fuer_neue_zeile(self):
        """Update muss vor Insert flushen, sonst kollidiert die freigewordene Nummer."""
        reconcile_whk_configs(self.p.id, [{'whk_nummer': 'WHK 01'}]); db.session.commit()
        wid = WHKConfig.query.one().id
        ids = reconcile_whk_configs(self.p.id, [{'id': wid, 'whk_nummer': 'WHK 02'},
                                                {'whk_nummer': 'WHK 01'}])
        db.session.commit()
        self.assertEqual(ids[0], wid)
        self.assertNotEqual(ids[1], wid)
        self.assertEqual(WHKConfig.query.count(), 2)

    def test_steuerung_zweiter_save_ohne_id_kein_churn(self):
        ids1 = reconcile_steuerung_configs(self.p.id, [{'name': 'A', 'typ': 'TA'}])
        db.session.commit()
        ids2 = reconcile_steuerung_configs(self.p.id, [{'name': 'A', 'typ': 'TA'}])
        db.session.commit()
        self.assertEqual(ids1, ids2)                      # Id stabil
        self.assertEqual(SteuerungConfig.query.count(), 1)

    def test_ids_sind_positionsgleich_zu_den_zeilen(self):
        """Leere Zeile -> None an ihrer Position. Das Frontend mappt über den Index;
        eine Verschiebung würde die Id in die falsche Zeile schreiben."""
        ids = reconcile_whk_configs(self.p.id, [{'whk_nummer': ''},
                                                {'whk_nummer': 'WHK 01'},
                                                {'whk_nummer': '   '}])
        db.session.commit()
        self.assertEqual(len(ids), 3)
        self.assertIsNone(ids[0])
        self.assertIsNone(ids[2])
        self.assertEqual(ids[1], WHKConfig.query.one().id)

    # ---------- Auto-Save-Endpunkt (End-to-End) ----------
    def test_autosave_endpoint_liefert_ids_und_bleibt_stabil(self):
        r = self.client.post(f'/projekt/konfiguration/auto-save/{self.p.id}',
                             json={'whk_rows': [{'whk_nummer': 'WHK 01'}],
                                   'meteostationen': [],
                                   'steuerung_rows': [{'name': 'A', 'typ': 'TA'}]})
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertEqual(d['whk_ids'], [WHKConfig.query.one().id])
        self.assertEqual(d['steuerung_ids'], [SteuerungConfig.query.one().id])

        # Zweiter Save — Frontend sendet die zurückgeschriebenen Ids
        r2 = self.client.post(f'/projekt/konfiguration/auto-save/{self.p.id}',
                              json={'whk_rows': [{'id': d['whk_ids'][0], 'whk_nummer': 'WHK 01'}],
                                    'meteostationen': [],
                                    'steuerung_rows': [{'id': d['steuerung_ids'][0],
                                                        'name': 'A', 'typ': 'TA'}]})
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()['whk_ids'], d['whk_ids'])
        self.assertEqual(WHKConfig.query.count(), 1)
        self.assertEqual(SteuerungConfig.query.count(), 1)

    def test_autosave_endpoint_doppelter_post_ohne_id_kein_500(self):
        """Doppel-POST (verlorene Antwort / überlappender Save) muss idempotent sein."""
        body = {'whk_rows': [{'whk_nummer': 'WHK 01'}], 'meteostationen': [],
                'steuerung_rows': [{'name': 'A', 'typ': 'TA'}]}
        r1 = self.client.post(f'/projekt/konfiguration/auto-save/{self.p.id}', json=body)
        r2 = self.client.post(f'/projekt/konfiguration/auto-save/{self.p.id}', json=body)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r1.get_json()['whk_ids'], r2.get_json()['whk_ids'])
        self.assertEqual(WHKConfig.query.count(), 1)
        self.assertEqual(SteuerungConfig.query.count(), 1)

    def test_autosave_endpoint_loeschschutz_400(self):
        reconcile_steuerung_configs(self.p.id, [{'name': 'A', 'typ': 'TA'}]); db.session.commit()
        sid = SteuerungConfig.query.one().id
        db.session.add(Stuecknachweis(project_id=self.p.id, steuerung_config_id=sid)); db.session.commit()
        # Auto-Save ohne die Steuerung (Löschversuch) -> 400, nichts gelöscht
        r = self.client.post(f'/projekt/konfiguration/auto-save/{self.p.id}',
                             json={'whk_rows': [{'whk_nummer': 'WHK 01'}],
                                   'meteostationen': [], 'steuerung_rows': []})
        self.assertEqual(r.status_code, 400)
        self.assertIn('Stücknachweis', r.get_json()['error'])
        self.assertIsNotNone(SteuerungConfig.query.get(sid))


if __name__ == '__main__':
    unittest.main(verbosity=2)
