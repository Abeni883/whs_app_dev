"""Tests: IT-Inventar — SPS-Daten pro WHK (blueprints/sps_info.py, models.SpsInfo).

Abgedeckt (hermetische Temp-DB, echtes Template-Rendering via make_render_app):
  8. Sys-ID (hostname) + Webvisu/Config-Links: Modell-Helper, Formular (Label, Muster via
     data-Attribut), Auswahlseite (Links nur bei Sys-ID)
  9. Einstiegsseite /it-inventar: nur EWH, Zaehler "erfasst/WHK", DIDOK, Suche, Menuepunkt
  1. Auswahlseite laedt und listet WHKs aus der Konfiguration (Status 'Nicht erfasst')
  2. Formular oeffnen -> Auto-Init (leeres SpsInfo); Status wechselt erst nach
     Dateneingabe (Hostname ODER MAC) auf 'Erfasst'
  3. Autosave persistiert alle Felder, Reload zeigt sie; leer -> NULL
  4. Projekt loeschen -> SpsInfo kaskadiert (ORM-Pfad wie projekte.projekt_loeschen)
  5. WHK loeschen -> SpsInfo kaskadiert (ORM-Pfad reconcile_whk_configs UND rohes SQL)
  6. Projektuebersicht: IT-Inventar-Button nur bei EWH
  7. Autosave-Fehlerpfade: fremde WHK -> 404, leerer Body -> 400
"""
import os
import unittest

from tests._util import make_render_app
from models import db, Project, WHKConfig, SpsInfo, EWHMeteostation
from blueprints.konfiguration import reconcile_whk_configs


class SpsInfoTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_render_app()
        self.ctx = self.app.app_context(); self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

        self.p = Project(energie='EWH', projektname='P-IT')
        db.session.add(self.p); db.session.flush()
        self.whk1 = WHKConfig(projekt_id=self.p.id, whk_nummer='WHK 01',
                              whk_typ='WHK_20_SEL_01_16')
        self.whk2 = WHKConfig(projekt_id=self.p.id, whk_nummer='WHK 02')
        db.session.add_all([self.whk1, self.whk2])
        db.session.commit()

    def tearDown(self):
        db.session.remove(); self.ctx.pop()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    # ---- Helpers ----
    def _auswahl(self):
        return self.client.get(f'/projekt/{self.p.id}/it-inventar')

    def _formular(self, whk=None):
        whk = whk or self.whk1
        return self.client.get(f'/projekt/{self.p.id}/whk/{whk.id}/sps')

    def _autosave(self, daten, whk=None, project_id=None):
        whk = whk or self.whk1
        pid = project_id or self.p.id
        return self.client.post(f'/projekt/{pid}/whk/{whk.id}/sps/autosave', json=daten)

    # ---- 1. Auswahlseite ----
    def test_auswahl_listet_whks(self):
        r = self._auswahl()
        self.assertEqual(r.status_code, 200)
        self.assertIn('WHK 01', r.text)
        self.assertIn('WHK 02', r.text)
        self.assertNotIn('<th>Typ</th>', r.text)            # Typ-Spalte entfernt
        self.assertNotIn('WHK_20_SEL_01_16', r.text)
        self.assertEqual(r.text.count('Nicht erfasst'), 2)
        # Spaltenstruktur: Bezeichnung | MAC-Adresse | Webvisu | Config | Status | Aktion
        import re
        kopf = r.text[r.text.index('<thead>'):r.text.index('</thead>')]
        self.assertEqual(re.findall(r'<th>(.*?)</th>', kopf),
                         ['Bezeichnung', 'MAC-Adresse', 'Webvisu', 'Config', 'Status', 'Aktion'])
        self.assertNotIn('>Erfasst<', r.text)
        self.assertEqual(SpsInfo.query.count(), 0)          # Auswahl legt nichts an

    def test_auswahl_ohne_whk_zeigt_hinweis(self):
        leer = Project(energie='EWH', projektname='Leer')
        db.session.add(leer); db.session.commit()
        r = self.client.get(f'/projekt/{leer.id}/it-inventar')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Keine WHK-Konfigurationen vorhanden', r.text)

    # ---- 2. Auto-Init + Status ----
    def test_formular_auto_init_und_status(self):
        r = self._formular()
        self.assertEqual(r.status_code, 200)
        self.assertIn('data-save-url', r.text)
        self.assertIn('SPS — WHK 01', r.text)
        sps = SpsInfo.query.filter_by(whk_config_id=self.whk1.id).one()
        self.assertEqual(sps.project_id, self.p.id)
        self.assertIsNone(sps.hostname)
        self.assertFalse(sps.ist_erfasst)

        # Zweites Oeffnen legt KEIN zweites Objekt an
        self._formular()
        self.assertEqual(SpsInfo.query.filter_by(whk_config_id=self.whk1.id).count(), 1)

        # Nur geoeffnet -> weiterhin 'Nicht erfasst'
        self.assertEqual(self._auswahl().text.count('Nicht erfasst'), 2)

        # Nur Nebenfeld (SPS-Typ) -> bleibt 'Nicht erfasst'
        r = self._autosave({'sps_typ': 'CX8190'})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json['erfasst'])
        self.assertEqual(self._auswahl().text.count('Nicht erfasst'), 2)

        # MAC allein reicht fuer 'Erfasst'
        r = self._autosave({'mac_adresse': '00:01:05:1A:2B:3C'})
        self.assertTrue(r.json['erfasst'])
        html = self._auswahl().text
        self.assertEqual(html.count('Nicht erfasst'), 1)   # nur noch WHK 02
        self.assertIn('>Erfasst<', html)

        # Whitespace-only zaehlt nicht als erfasst
        self._autosave({'mac_adresse': '   '})
        self.assertEqual(self._auswahl().text.count('Nicht erfasst'), 2)

    # ---- 3. Autosave persistiert alles, Reload ----
    def test_autosave_persistiert_alle_felder(self):
        daten = {
            'hostname': 'CX-1A2B3C',
            'mac_adresse': '00:01:05:1A:2B:3C',
            'sps_typ': 'CX8190',
            'twincat_version': '3.1.4024.56',
            'image_version': 'IMG-2026-01',
            'bemerkung': 'Mehrzeilige\nBemerkung <mit> Sonderzeichen & ∆',
        }
        r = self._autosave(daten)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json['success'])

        sps = SpsInfo.query.filter_by(whk_config_id=self.whk1.id).one()
        for feld, wert in daten.items():
            self.assertEqual(getattr(sps, feld), wert, feld)

        # Reload: alle Werte (HTML-escaped) im Formular
        html = self._formular().text
        for wert in ('CX-1A2B3C', '00:01:05:1A:2B:3C', 'CX8190',
                     '3.1.4024.56', 'IMG-2026-01'):
            self.assertIn(f'value="{wert}"', html)
        self.assertIn('&lt;mit&gt; Sonderzeichen &amp; ∆', html)
        # Hostname erscheint auch in der Auswahlliste
        self.assertIn('CX-1A2B3C', self._auswahl().text)

    def test_autosave_feldweise_und_leer_wird_null(self):
        self._autosave({'hostname': 'H1', 'sps_typ': 'CX8190'})
        # Nur ein Feld senden -> andere bleiben unveraendert
        self._autosave({'sps_typ': 'CX9020'})
        sps = SpsInfo.query.filter_by(whk_config_id=self.whk1.id).one()
        self.assertEqual(sps.hostname, 'H1')
        self.assertEqual(sps.sps_typ, 'CX9020')
        # Leer / Whitespace -> NULL, Trim
        self._autosave({'hostname': '', 'sps_typ': '  CX8190  '})
        db.session.expire_all()
        sps = SpsInfo.query.filter_by(whk_config_id=self.whk1.id).one()
        self.assertIsNone(sps.hostname)
        self.assertEqual(sps.sps_typ, 'CX8190')

    def test_ip_und_seriennummer_entfernt_altlast_ignoriert(self):
        # Felder nicht mehr im Formular; Autosave ignoriert die Keys (Spalten bleiben als Altlast)
        html = self._formular().text
        for alt in ('name="ip_adresse"', 'IP-Adresse', 'name="seriennummer"', 'Seriennummer'):
            self.assertNotIn(alt, html)
        r = self._autosave({'hostname': 'H', 'ip_adresse': '10.0.0.1', 'seriennummer': 'SN-1'})
        self.assertEqual(r.status_code, 200)
        sps = SpsInfo.query.filter_by(whk_config_id=self.whk1.id).one()
        self.assertEqual(sps.hostname, 'H')
        self.assertIsNone(sps.ip_adresse)
        self.assertIsNone(sps.seriennummer)
        self.assertNotIn('ip_adresse', SpsInfo.DATEN_FELDER)
        self.assertNotIn('seriennummer', SpsInfo.DATEN_FELDER)

    def test_formular_verbleibende_felder_und_platzhalter(self):
        html = self._formular().text
        for name in ('hostname', 'mac_adresse', 'sps_typ', 'twincat_version', 'image_version', 'bemerkung'):
            self.assertIn(f'name="{name}"', html)
        self.assertIn('placeholder="z.B. v610a"', html)
        self.assertEqual(SpsInfo.DATEN_FELDER,
                         ('hostname', 'mac_adresse', 'sps_typ', 'twincat_version', 'image_version', 'bemerkung',
                          'meteo_baudrate', 'meteo_modbus_adresse', 'meteo_seriennummer', 'meteo_herstellungsjahr'))

    def test_autosave_ohne_vorheriges_formular_legt_an(self):
        # Autosave direkt (ohne GET) darf nicht crashen -> Auto-Init auch hier
        r = self._autosave({'hostname': 'X'}, whk=self.whk2)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(SpsInfo.query.filter_by(whk_config_id=self.whk2.id).one().hostname, 'X')

    # ---- 4. Projekt loeschen -> Cascade ----
    def test_projekt_loeschen_kaskadiert_sps(self):
        self._autosave({'hostname': 'H1'})
        self._autosave({'hostname': 'H2'}, whk=self.whk2)
        self.assertEqual(SpsInfo.query.count(), 2)

        db.session.delete(db.session.get(Project, self.p.id))   # wie projekte.projekt_loeschen
        db.session.commit()

        self.assertEqual(Project.query.count(), 0)
        self.assertEqual(WHKConfig.query.count(), 0)
        self.assertEqual(SpsInfo.query.count(), 0)
        self.assertEqual(db.session.execute(db.text('PRAGMA foreign_key_check')).fetchall(), [])

    # ---- 5. WHK loeschen -> Cascade ----
    def test_whk_loeschen_via_konfiguration_kaskadiert_sps(self):
        self._autosave({'hostname': 'H1'})
        self._autosave({'hostname': 'H2'}, whk=self.whk2)

        # Konfigurations-Save ohne WHK 02 -> WHK 02 wird geloescht (kein Lösch-Schutz
        # wie beim Stuecknachweis), SpsInfo von WHK 02 verschwindet mit.
        reconcile_whk_configs(self.p.id, [{
            'id': self.whk1.id, 'whk_nummer': 'WHK 01', 'whk_typ': 'WHK_20_SEL_01_16',
            'preset_typ': 'kabine_16hz', 'anzahl_abgaenge': 1,
            'anzahl_temperatursonden': 1, 'hat_antriebsheizung': False,
        }])
        db.session.commit()

        self.assertEqual(WHKConfig.query.count(), 1)
        rest = SpsInfo.query.all()
        self.assertEqual(len(rest), 1)
        self.assertEqual(rest[0].whk_config_id, self.whk1.id)
        self.assertEqual(rest[0].hostname, 'H1')
        self.assertEqual(db.session.execute(db.text('PRAGMA foreign_key_check')).fetchall(), [])

    def test_whk_loeschen_roh_sql_kaskadiert_sps(self):
        # Zweite Verteidigungslinie: DB-CASCADE ohne ORM.
        self._autosave({'hostname': 'H1'})
        db.session.execute(db.text('DELETE FROM whk_configs WHERE id=:i'), {'i': self.whk1.id})
        db.session.commit()
        self.assertEqual(SpsInfo.query.count(), 0)

    def test_unique_eine_sps_pro_whk(self):
        from sqlalchemy.exc import IntegrityError
        db.session.add(SpsInfo(project_id=self.p.id, whk_config_id=self.whk1.id))
        db.session.commit()
        db.session.add(SpsInfo(project_id=self.p.id, whk_config_id=self.whk1.id))
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    # ---- 6. Projektuebersicht-Button nur bei EWH ----
    def test_projekte_button_nur_ewh(self):
        from flask import render_template
        gwh = Project(energie='GWH', projektname='P-GAS')
        db.session.add(gwh); db.session.commit()
        with self.app.test_request_context():
            html = render_template('projekte.html', projekte=[self.p, gwh], progress_dict={})
        self.assertIn('<th>IT-Inventar</th>', html)
        self.assertEqual(html.count('class="itinventar-link"'), 1)
        self.assertIn(f'/projekt/{self.p.id}/it-inventar', html)
        self.assertNotIn(f'/projekt/{gwh.id}/it-inventar', html)

    # ---- 7. Fehlerpfade ----
    def test_autosave_fremde_whk_404(self):
        anderes = Project(energie='EWH', projektname='Anderes')
        db.session.add(anderes); db.session.commit()
        r = self._autosave({'hostname': 'X'}, project_id=anderes.id)   # whk1 gehoert zu self.p
        self.assertEqual(r.status_code, 404)
        self.assertEqual(SpsInfo.query.count(), 0)

    def test_autosave_leerer_body_400(self):
        r = self.client.post(f'/projekt/{self.p.id}/whk/{self.whk1.id}/sps/autosave',
                             data='', content_type='application/json')
        self.assertEqual(r.status_code, 400)

    # ---- 8. Sys-ID + Webvisu/Config-Links ----
    def test_links_aus_sysid_modell(self):
        self.assertIsNone(SpsInfo.link_aus_sysid('webvisu', None))
        self.assertIsNone(SpsInfo.link_aus_sysid('config', '   '))
        self.assertEqual(SpsInfo.link_aus_sysid('webvisu', ' lu-wh-01 '), 'https://lu-wh-01/webvisu.htm')
        self.assertEqual(SpsInfo.link_aus_sysid('config', 'lu-wh-01'), 'https://lu-wh-01/config')
        sps = SpsInfo(project_id=self.p.id, whk_config_id=self.whk1.id, hostname='lu-wh-01')
        self.assertEqual(sps.webvisu_url, 'https://lu-wh-01/webvisu.htm')
        self.assertEqual(sps.config_url, 'https://lu-wh-01/config')
        self.assertEqual(sps.sysid, 'lu-wh-01')
        # Muster: genau eine Definitionsstelle, Platzhalter vorhanden
        for muster in SpsInfo.URL_MUSTER.values():
            self.assertIn('{sysid}', muster)

    def test_formular_sysid_label_und_link_muster(self):
        html = self._formular().text
        self.assertIn('<label for="hostname">Sys-ID</label>', html)
        self.assertIn('placeholder="z.B. lu-wh-01"', html)
        self.assertNotIn('>Hostname<', html)
        self.assertIn('id="link-webvisu"', html)
        self.assertIn('id="link-config"', html)
        # Muster kommen aus dem Modell (kein Hardcoding im Template)
        self.assertIn(f'data-webvisu-muster="{SpsInfo.URL_MUSTER["webvisu"]}"', html)
        self.assertIn(f'data-config-muster="{SpsInfo.URL_MUSTER["config"]}"', html)
        self.assertNotIn('webvisu.htm', html.replace(SpsInfo.URL_MUSTER['webvisu'], ''))

    def test_auswahl_links_nur_bei_sysid(self):
        self._autosave({'hostname': 'lu-wh-01'})                      # WHK 01: Sys-ID
        self._autosave({'mac_adresse': '00:01:05:1A:2B:3C'}, whk=self.whk2)  # WHK 02: nur MAC
        html = self._auswahl().text
        self.assertIn('<th>Webvisu</th>', html)
        self.assertIn('<th>Config</th>', html)
        # URL als Text-Link (href == sichtbarer Text), kein Button
        self.assertIn('<a href="https://lu-wh-01/webvisu.htm" target="_blank" rel="noopener">https://lu-wh-01/webvisu.htm</a>', html)
        self.assertIn('<a href="https://lu-wh-01/config" target="_blank" rel="noopener">https://lu-wh-01/config</a>', html)
        self.assertNotIn('btn-secondary', html)
        # WHK 02 ist 'Erfasst' (MAC), hat aber keine Sys-ID -> keine Links, MAC sichtbar
        self.assertEqual(html.count('href="https://'), 2)      # nur WHK 01 (Webvisu + Config)
        self.assertIn('00:01:05:1A:2B:3C', html)
        self.assertEqual(html.count('>Erfasst<'), 2)

    # ---- 9. Einstiegsseite /it-inventar ----
    def test_uebersicht_listet_ewh_mit_zaehler(self):
        gwh = Project(energie='GWH', projektname='P-GAS')
        leer = Project(energie='EWH', projektname='P-Leer', didok_betriebspunkt='LZ')
        db.session.add_all([gwh, leer]); db.session.flush()
        db.session.add(WHKConfig(projekt_id=self.p.id, whk_nummer='WHK 03'))
        db.session.commit()
        self._autosave({'hostname': 'lu-wh-01'})
        self._autosave({'mac_adresse': 'AA'}, whk=self.whk2)
        self._formular(WHKConfig.query.filter_by(whk_nummer='WHK 03').one())  # nur Auto-Init

        r = self.client.get('/it-inventar')
        self.assertEqual(r.status_code, 200)
        html = r.text
        self.assertIn('P-IT', html)
        self.assertIn('P-Leer', html)
        self.assertNotIn('P-GAS', html)                       # GWH nicht gelistet
        self.assertIn('>2/3<', html)                          # Sys-ID + MAC erfasst, Auto-Init nicht
        self.assertIn('<td>LZ</td>', html)                    # DIDOK
        self.assertIn('id="searchInput"', html)               # Live-Suche
        self.assertIn(f'/projekt/{self.p.id}/it-inventar', html)   # Klick -> WHK-Auswahl
        self.assertIn(f'/projekt/{leer.id}/it-inventar', html)

    def test_menuepunkt_in_base_html(self):
        # Navigation wird nur fuer eingeloggte User gerendert (Test-Client ist anonym):
        # daher Quelltext-Pruefung, dass der Menuepunkt neben Export haengt.
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'templates', 'base.html')
        src = open(base, encoding='utf-8').read()
        self.assertIn("url_for('sps_info.uebersicht')", src)
        self.assertLess(src.index("url_for('export.export')"), src.index("url_for('sps_info.uebersicht')"))
        self.assertLess(src.index("url_for('sps_info.uebersicht')"), src.index('nav-dropdown'))

    def test_uebersicht_ohne_projekte(self):
        Project.query.delete(); db.session.commit()
        r = self.client.get('/it-inventar')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Noch keine EWH-Projekte vorhanden', r.text)

    # ---- 10. Meteostation-Sektion ----
    METEO = {'meteo_baudrate': '19200', 'meteo_modbus_adresse': '1',
             'meteo_seriennummer': 'MS-SN-77', 'meteo_herstellungsjahr': '2026'}

    def test_meteo_sektion_bei_zugeordneter_ms(self):
        # Aktueller Konfigurations-Pfad: Zuordnung ueber ewh_meteostations, KEIN Legacy-String
        db.session.add(EWHMeteostation(projekt_id=self.p.id, ms_nummer='MS 01',
                                       zugeordnete_whk_id=self.whk1.id, reihenfolge=1))
        db.session.commit()
        self.assertTrue(self.whk1.hat_meteostation)
        self.assertEqual(self.whk1.meteostation_name, 'MS 01')

        html = self._formular().text
        self.assertIn('Meteostation (MS 01)', html)
        for name in self.METEO:
            self.assertIn(f'name="{name}"', html)
        self.assertIn('placeholder="z.B. 19200"', html)
        self.assertIn('placeholder="z.B. 1"', html)
        self.assertIn('placeholder="z.B. 2026"', html)

        # Speichern + Reload
        r = self._autosave(dict(self.METEO, hostname='lu-wh-01'))
        self.assertEqual(r.status_code, 200)
        sps = SpsInfo.query.filter_by(whk_config_id=self.whk1.id).one()
        for feld, wert in self.METEO.items():
            self.assertEqual(getattr(sps, feld), wert, feld)
        html = self._formular().text
        for wert in self.METEO.values():
            self.assertIn(f'value="{wert}"', html)
        for feld in self.METEO:
            self.assertIn(feld, SpsInfo.DATEN_FELDER)

    def test_meteo_sektion_bei_legacy_string(self):
        self.whk2.meteostation = 'MS 02'   # Altbestand ohne Zuordnungszeile
        db.session.commit()
        self.assertEqual(self.whk2.meteostation_name, 'MS 02')
        html = self._formular(self.whk2).text
        self.assertIn('Meteostation (MS 02)', html)

    def test_meteo_name_zuordnung_vor_legacy(self):
        self.whk1.meteostation = 'ALT'
        db.session.add(EWHMeteostation(projekt_id=self.p.id, ms_nummer='MS 03',
                                       zugeordnete_whk_id=self.whk1.id, reihenfolge=2))
        db.session.add(EWHMeteostation(projekt_id=self.p.id, ms_nummer='MS 01',
                                       zugeordnete_whk_id=self.whk1.id, reihenfolge=1))
        db.session.commit()
        self.assertEqual(self.whk1.meteostation_name, 'MS 01 / MS 03')

    def test_meteo_sektion_fehlt_ohne_ms(self):
        self.assertFalse(self.whk1.hat_meteostation)
        self.assertIsNone(self.whk1.meteostation_name)
        html = self._formular().text
        self.assertNotIn('Meteostation', html)
        for name in self.METEO:
            self.assertNotIn(f'name="{name}"', html)
        # Autosave unveraendert: Keys werden serverseitig trotzdem akzeptiert (harmlos)
        r = self._autosave({'hostname': 'H', 'meteo_baudrate': '9600'})
        self.assertEqual(r.status_code, 200)
        sps = SpsInfo.query.filter_by(whk_config_id=self.whk1.id).one()
        self.assertEqual(sps.hostname, 'H')
        self.assertEqual(sps.meteo_baudrate, '9600')
        # Status-Logik unveraendert: Meteo-Felder allein machen nicht 'Erfasst'
        self._autosave({'hostname': '', 'meteo_baudrate': '9600'}, whk=self.whk2)
        self.assertEqual(self._auswahl().text.count('Nicht erfasst'), 1)   # nur whk2

    def test_formular_fremde_whk_redirect(self):
        anderes = Project(energie='EWH', projektname='Anderes')
        db.session.add(anderes); db.session.commit()
        r = self.client.get(f'/projekt/{anderes.id}/whk/{self.whk1.id}/sps')
        self.assertEqual(r.status_code, 302)
        self.assertIn(f'/projekt/{anderes.id}/it-inventar', r.headers['Location'])
        self.assertEqual(SpsInfo.query.count(), 0)


class SpsMeteoMigrationTest(unittest.TestCase):
    """scripts/migrate_sps_meteo.py: idempotent, dry-run read-only, Kontrolle sauber."""

    def setUp(self):
        import sys, tempfile, sqlite3
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, os.path.join(root, 'scripts'))
        import migrate_sps_meteo
        self.mig = migrate_sps_meteo
        fd, self.db_path = tempfile.mkstemp(suffix='.db', prefix='whs_mig_')
        os.close(fd)
        # Alt-Schema ohne Meteo-Spalten simulieren
        con = sqlite3.connect(self.db_path)
        con.execute('CREATE TABLE projects (id INTEGER PRIMARY KEY)')
        con.execute('CREATE TABLE whk_configs (id INTEGER PRIMARY KEY)')
        con.execute('''CREATE TABLE sps_infos (id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            whk_config_id INTEGER NOT NULL UNIQUE REFERENCES whk_configs(id),
            hostname VARCHAR(100))''')
        con.execute('INSERT INTO projects VALUES (1)'); con.execute('INSERT INTO whk_configs VALUES (1)')
        con.execute("INSERT INTO sps_infos (project_id, whk_config_id, hostname) VALUES (1, 1, 'h')")
        con.commit(); con.close()

    def tearDown(self):
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def _spalten(self):
        import sqlite3
        con = sqlite3.connect(self.db_path)
        try:
            return [r[1] for r in con.execute('PRAGMA table_info(sps_infos)')]
        finally:
            con.close()

    def _tabelle_loeschen(self):
        import sqlite3
        con = sqlite3.connect(self.db_path)
        con.execute('DROP TABLE sps_infos'); con.commit(); con.close()

    def test_tabelle_fehlt_dry_run_legt_nichts_an(self):
        # Erst-Deployment (PROD): sps_infos existiert noch nicht
        self._tabelle_loeschen()
        self.assertEqual(self.mig.main([self.db_path, '--dry-run']), 0)
        self.assertEqual(self._spalten(), [])

    def test_tabelle_fehlt_wird_aus_modell_angelegt(self):
        self._tabelle_loeschen()
        self.assertEqual(self.mig.main([self.db_path]), 0)
        spalten = self._spalten()
        # Exakt die Modell-Spalten (wie db.create_all), inkl. meteo_*
        self.assertEqual(spalten, [c.name for c in SpsInfo.__table__.columns])
        for name, _ in self.mig.NEUE_SPALTEN:
            self.assertIn(name, spalten)
        # zweiter Lauf: nichts zu tun
        self.assertEqual(self.mig.main([self.db_path]), 0)
        self.assertEqual(self._spalten(), spalten)
        # FK/UNIQUE wie im Modell: zweite SPS fuer dieselbe WHK scheitert, FK-Check leer
        import sqlite3
        con = sqlite3.connect(self.db_path)
        con.execute('PRAGMA foreign_keys=ON')
        con.execute("INSERT INTO sps_infos (project_id, whk_config_id, hostname) VALUES (1, 1, 'a')")
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute("INSERT INTO sps_infos (project_id, whk_config_id) VALUES (1, 1)")
        self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(), [])
        con.close()

    def test_dry_run_aendert_nichts(self):
        self.assertEqual(self.mig.main([self.db_path, '--dry-run']), 0)
        self.assertNotIn('meteo_baudrate', self._spalten())

    def test_migration_und_idempotenz(self):
        self.assertEqual(self.mig.main([self.db_path]), 0)
        spalten = self._spalten()
        for name, _ in self.mig.NEUE_SPALTEN:
            self.assertIn(name, spalten)
        # Modell und Skript muessen dieselben Spalten kennen
        self.assertEqual([n for n, _ in self.mig.NEUE_SPALTEN],
                         [f for f in SpsInfo.DATEN_FELDER if f.startswith('meteo_')])
        # zweiter Lauf: nichts zu tun, keine Fehler
        self.assertEqual(self.mig.main([self.db_path]), 0)
        self.assertEqual(self._spalten(), spalten)
        # Altdaten unveraendert
        import sqlite3
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute('SELECT hostname, meteo_baudrate FROM sps_infos').fetchone(), ('h', None))
        con.close()


if __name__ == '__main__':
    unittest.main()
