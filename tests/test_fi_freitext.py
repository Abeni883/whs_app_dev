"""Tests fuer FI-Freitextwerte und den abschaltbaren FI-Abgangs-Sync (08/2026).

Deckt die beiden Anforderungen ab:
  1. Alle FI loeschbar — und Geloeschtes wird vom Abgangs-Sync NICHT wiederbelebt
     (Stuecknachweis.fi_manuell_verwaltet).
  2. Freitext in Delta-I/Delta-t ("-" statt Zahl), inkl. Einheiten-Logik fuers PDF.

Der Sync laeuft in stuecknachweis_formular vor der POST-Verarbeitung, deshalb wird
hier per POST (endet mit Redirect, kein Template-Rendering) "neu geladen".
"""
import os
import unittest

from tests._util import make_temp_app
from models import db, Project, WHKConfig, Stuecknachweis, FiMessung, generiere_fi_sicherungen


class FiFreitextTest(unittest.TestCase):
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

    def _whk_projekt(self, abgaenge=4):
        p = Project(energie='EWH', projektname='P')
        db.session.add(p)
        db.session.flush()
        whk = WHKConfig(projekt_id=p.id, whk_nummer='WHK 01', anzahl_abgaenge=abgaenge,
                        anzahl_temperatursonden=1, preset_typ='kabine_16hz')
        db.session.add(whk)
        db.session.commit()
        return p, whk

    def _formular_url(self, p, whk):
        return f'/projekt/{p.id}/whk/{whk.id}/stuecknachweis'

    def _reload(self, p, whk):
        """Seitenaufruf simulieren: POST durchlaeuft den Sync-Block, endet im Redirect."""
        return self.client.post(self._formular_url(p, whk), data={})

    def _fi_count(self, sn_id):
        return FiMessung.query.filter_by(stuecknachweis_id=sn_id).count()

    # ---------- Anforderung 1: Sync ----------

    def test_erstanlage_generiert_fi_pro_abgang(self):
        p, whk = self._whk_projekt(abgaenge=4)
        self._reload(p, whk)
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        self.assertIsNotNone(sn)
        self.assertEqual(self._fi_count(sn.id), len(generiere_fi_sicherungen(4)))

    def test_sync_folgt_abgangsaenderung_wenn_unberuehrt(self):
        """Unberuehrter SN: Abgaenge aendern -> FI-Liste zieht nach."""
        p, whk = self._whk_projekt(abgaenge=4)
        self._reload(p, whk)
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        self.assertEqual(self._fi_count(sn.id), 4)

        whk.anzahl_abgaenge = 6
        db.session.commit()
        self._reload(p, whk)
        self.assertEqual(self._fi_count(sn.id), 6)

    def test_alle_fi_geloescht_bleiben_nach_reload_weg(self):
        """Kernfall: alle FI loeschen -> naechster Seitenaufruf regeneriert NICHT."""
        p, whk = self._whk_projekt(abgaenge=4)
        self._reload(p, whk)
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        for fi in FiMessung.query.filter_by(stuecknachweis_id=sn.id).all():
            r = self.client.post(f'/stuecknachweis/{sn.id}/fi/{fi.id}/delete')
            self.assertEqual(r.status_code, 200)
        self.assertEqual(self._fi_count(sn.id), 0)

        self._reload(p, whk)
        self.assertEqual(self._fi_count(sn.id), 0)
        self.assertTrue(bool(Stuecknachweis.query.get(sn.id).fi_manuell_verwaltet))

    def test_hinzufuegen_nach_komplettloeschung(self):
        """Nach dem Loeschen aller FI laesst sich wieder eine hinzufuegen — und sie bleibt."""
        p, whk = self._whk_projekt(abgaenge=2)
        self._reload(p, whk)
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        for fi in FiMessung.query.filter_by(stuecknachweis_id=sn.id).all():
            self.client.post(f'/stuecknachweis/{sn.id}/fi/{fi.id}/delete')

        r = self.client.post(f'/stuecknachweis/{sn.id}/fi/add')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()['success'])
        self.assertEqual(self._fi_count(sn.id), 1)

        self._reload(p, whk)
        self.assertEqual(self._fi_count(sn.id), 1)

    def test_sync_bleibt_aus_auch_bei_abgangsaenderung(self):
        """Nach manuellem Eingriff darf auch eine Abgangsaenderung nicht regenerieren."""
        p, whk = self._whk_projekt(abgaenge=4)
        self._reload(p, whk)
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        erste = FiMessung.query.filter_by(stuecknachweis_id=sn.id).first()
        self.client.post(f'/stuecknachweis/{sn.id}/fi/{erste.id}/delete')

        whk.anzahl_abgaenge = 8
        db.session.commit()
        self._reload(p, whk)
        self.assertEqual(self._fi_count(sn.id), 3)

    # ---------- Anforderung 2: Freitext ----------

    def test_autosave_speichert_sonderzeichen(self):
        p, whk = self._whk_projekt(abgaenge=1)
        self._reload(p, whk)
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        fi = FiMessung.query.filter_by(stuecknachweis_id=sn.id).first()

        r = self.client.post(
            f'/stuecknachweis/{sn.id}/autosave',
            json={'fi_messungen': [{'id': fi.id, 'delta_i_ma': '-', 'delta_t_ms': ' n.a. '}]})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()['success'])

        db.session.expire_all()
        fi = FiMessung.query.get(fi.id)
        self.assertEqual(fi.delta_i_ma, '-')
        self.assertEqual(fi.delta_t_ms, 'n.a.')

    def test_autosave_leerer_wert_wird_none(self):
        p, whk = self._whk_projekt(abgaenge=1)
        self._reload(p, whk)
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        fi = FiMessung.query.filter_by(stuecknachweis_id=sn.id).first()

        self.client.post(f'/stuecknachweis/{sn.id}/autosave',
                         json={'fi_messungen': [{'id': fi.id, 'delta_i_ma': '   ',
                                                 'delta_t_ms': ''}]})
        db.session.expire_all()
        fi = FiMessung.query.get(fi.id)
        self.assertIsNone(fi.delta_i_ma)
        self.assertIsNone(fi.delta_t_ms)

    def test_formular_post_speichert_sonderzeichen(self):
        p, whk = self._whk_projekt(abgaenge=1)
        self._reload(p, whk)
        sn = Stuecknachweis.query.filter_by(whk_config_id=whk.id).first()
        fi = FiMessung.query.filter_by(stuecknachweis_id=sn.id).first()

        self.client.post(self._formular_url(p, whk), data={
            f'fi_{fi.id}_sicherung': 'F302.2',
            f'fi_{fi.id}_delta_i': '-',
            f'fi_{fi.id}_delta_t': '52.9',
        })
        db.session.expire_all()
        fi = FiMessung.query.get(fi.id)
        self.assertEqual(fi.delta_i_ma, '-')
        self.assertEqual(fi.delta_t_ms, '52.9')

    def test_einheit_nur_bei_zahlen(self):
        """PDF-Logik: Zahl -> Einheit, Freitext/leer -> keine Einheit."""
        fi = FiMessung(stuecknachweis_id=1, sicherung='F1')
        for wert, erwartet_i in [('240', 'mA'), ('52.9', 'mA'), ('52,9', 'mA'),
                                 ('-', ''), ('n.a.', ''), (None, '')]:
            fi.delta_i_ma = wert
            self.assertEqual(fi.delta_i_einheit, erwartet_i, f'delta_i={wert!r}')
        for wert, erwartet_t in [('52.9', 'ms'), ('-', ''), (None, '')]:
            fi.delta_t_ms = wert
            self.assertEqual(fi.delta_t_einheit, erwartet_t, f'delta_t={wert!r}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
