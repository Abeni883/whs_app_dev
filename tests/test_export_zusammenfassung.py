"""Tests: PDF-Export — Leerfall der «Zusammenfassung fehlgeschlagener Tests».

Verhalten der Zusammenfassung bleibt unveraendert: sie zeigt nur fehlgeschlagene Tests der
AUSGEWAEHLTEN Komponenten. Abgefangen wird nur der Leerfall (frueher: leere Seite nach dem
Deckblatt):
  1. Zusammenfassung ohne Komponente      -> «Keine Komponenten ausgewaehlt», keine Leerseite
  2. Komponente gewaehlt, dort kein Fehler -> «Keine fehlgeschlagenen Tests»
  3. Komponente mit Fehler                 -> Tabelle wie bisher, kein Hinweistext
  4. Zusammenfassung nicht gewaehlt        -> kein Abschnitt (wie bisher)
  5. GWH: dieselben Leerfaelle
  6. Export-Dialog: Hinweis beim Haekchen vorhanden (per JS ein-/ausgeblendet)

End-to-end ueber /export/generate (hermetische Temp-DB, echtes Rendering, echtes xhtml2pdf);
der PDF-Text wird mit pypdf gelesen.
"""
import os
import unittest
from io import BytesIO

from pypdf import PdfReader

from tests._util import make_render_app
from models import (db, Project, WHKConfig, ZSKConfig, TestQuestion, AbnahmeTestResult)

KEINE_KOMPONENTEN = 'Keine Komponenten ausgewählt'
KEINE_FEHLER = 'Keine fehlgeschlagenen Tests'
TITEL = 'Zusammenfassung fehlgeschlagener Tests'
TABELLEN_INTRO = 'wurden als "falsch" markiert'


class ExportZusammenfassungTest(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_render_app()
        self.ctx = self.app.app_context(); self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

        fragen = [('Anlage', 'Anlage-Frage Alpha'), ('WHK', 'WHK-Frage Beta'),
                  ('Abgang', 'Abgang-Frage Gamma'), ('GWH_Anlage', 'GWH-Anlage-Frage Delta'),
                  ('ZSK', 'ZSK-Frage Epsilon')]
        self.q = {}
        for nr, (typ, text) in enumerate(fragen, start=1):
            frage = TestQuestion(komponente_typ=typ, testszenario='Szenario', frage_nummer=nr,
                                 frage_text=text, reihenfolge=nr)
            db.session.add(frage)
            self.q[typ] = frage

        # EWH: Fehler nur in WHK 01, WH-Anlage fehlerfrei
        self.ewh = Project(energie='EWH', projektname='P-EWH')
        db.session.add(self.ewh); db.session.flush()
        db.session.add(WHKConfig(projekt_id=self.ewh.id, whk_nummer='WHK 01',
                                 anzahl_abgaenge=1, anzahl_temperatursonden=0))
        db.session.flush()
        db.session.add_all([
            AbnahmeTestResult(projekt_id=self.ewh.id, test_question_id=self.q['Anlage'].id,
                              komponente_index='Anlage', spalte='Anlage',
                              wh_lts_result='richtig', lss_ch_result='richtig'),
            AbnahmeTestResult(projekt_id=self.ewh.id, test_question_id=self.q['WHK'].id,
                              komponente_index='WHK 01', spalte='WHK 01',
                              wh_lts_result='falsch', lss_ch_result='richtig'),
        ])

        # GWH: ein ZSK, keine Fehler
        self.gwh = Project(energie='GWH', projektname='P-GWH')
        db.session.add(self.gwh); db.session.flush()
        db.session.add(ZSKConfig(projekt_id=self.gwh.id, zsk_nummer='01', anzahl_teile=0,
                                 hat_temperatursonde=False, reihenfolge=1))
        db.session.flush()
        db.session.add(AbnahmeTestResult(projekt_id=self.gwh.id, test_question_id=self.q['ZSK'].id,
                                         komponente_index='01', spalte='01',
                                         wh_lts_result='richtig', lss_ch_result='richtig'))
        db.session.commit()

    def tearDown(self):
        db.session.remove(); self.ctx.pop()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def _pdf_seiten(self, projekt, sections):
        """Exportiert und liefert den Text jeder PDF-Seite (Liste)."""
        r = self.client.post('/export/generate', data={
            'projekt_id': str(projekt.id), 'export_format': 'pdf', 'selected_sections': sections})
        self.assertEqual(r.status_code, 200, r.headers.get('Location'))
        self.assertEqual(r.mimetype, 'application/pdf')
        return [' '.join((s.extract_text() or '').split()) for s in PdfReader(BytesIO(r.data)).pages]

    # ---- 1. EWH: nur Deckblatt + Zusammenfassung ----
    def test_ewh_ohne_komponente_hinweis_statt_leerseite(self):
        seiten = self._pdf_seiten(self.ewh, ['deckblatt', 'zusammenfassung_fehler'])
        self.assertEqual(len(seiten), 2)                     # Deckblatt + Zusammenfassung, keine 3. Seite
        self.assertIn(TITEL, seiten[1])
        self.assertIn(KEINE_KOMPONENTEN, seiten[1])
        self.assertNotIn(KEINE_FEHLER, seiten[1])
        # Verhalten unveraendert: Fehler nicht gewaehlter Komponenten erscheinen NICHT
        self.assertNotIn('WHK-Frage Beta', ' '.join(seiten))

    def test_ewh_nur_zusammenfassung(self):
        seiten = self._pdf_seiten(self.ewh, ['zusammenfassung_fehler'])
        self.assertEqual(len(seiten), 1)
        self.assertIn(KEINE_KOMPONENTEN, seiten[0])

    # ---- 2. Komponente gewaehlt, dort kein Fehler ----
    def test_ewh_komponente_ohne_fehler(self):
        seiten = self._pdf_seiten(self.ewh, ['deckblatt', 'zusammenfassung_fehler', 'wh_anlage'])
        # (Die Leerseite am Ende JEDES Exports mit Komponenten-Abschnitt ist Altverhalten und
        #  bewusst nicht Teil dieses Fixes - daher hier keine Gesamtseitenzahl.)
        self.assertIn(TITEL, seiten[1])
        self.assertIn(KEINE_FEHLER, seiten[1])
        self.assertNotIn(KEINE_KOMPONENTEN, seiten[1])
        self.assertIn('Anlage-Frage Alpha', seiten[2])       # Abschnitt folgt auf eigener Seite

    # ---- 3. Komponente mit Fehler: Tabelle wie bisher ----
    def test_ewh_komponente_mit_fehler_tabelle(self):
        seiten = self._pdf_seiten(self.ewh, ['deckblatt', 'zusammenfassung_fehler', 'whk_WHK_01'])
        self.assertIn(TITEL, seiten[1])
        self.assertIn(TABELLEN_INTRO, seiten[1])
        self.assertIn('Die folgenden 1 Test(s)', seiten[1])
        self.assertIn('WHK-Frage Beta', seiten[1])
        self.assertNotIn(KEINE_FEHLER, seiten[1])
        self.assertNotIn(KEINE_KOMPONENTEN, seiten[1])

    # ---- 4. Zusammenfassung nicht gewaehlt ----
    def test_ewh_ohne_zusammenfassung_kein_abschnitt(self):
        text = ' '.join(self._pdf_seiten(self.ewh, ['deckblatt', 'wh_anlage', 'whk_WHK_01']))
        self.assertNotIn(TITEL, text)
        self.assertNotIn(KEINE_FEHLER, text)
        self.assertNotIn(KEINE_KOMPONENTEN, text)

    # ---- 5. GWH ----
    def test_gwh_ohne_komponente(self):
        seiten = self._pdf_seiten(self.gwh, ['deckblatt', 'zusammenfassung_fehler'])
        self.assertEqual(len(seiten), 2)
        self.assertIn(TITEL, seiten[1])
        self.assertIn(KEINE_KOMPONENTEN, seiten[1])

    def test_gwh_komponente_ohne_fehler(self):
        seiten = self._pdf_seiten(self.gwh, ['deckblatt', 'zusammenfassung_fehler', 'zsk_01'])
        self.assertIn(TITEL, seiten[1])
        self.assertIn(KEINE_FEHLER, seiten[1])
        self.assertNotIn(KEINE_KOMPONENTEN, seiten[1])
        self.assertIn('ZSK-Frage Epsilon', ' '.join(seiten[2:]))

    def test_gwh_ohne_zusammenfassung_kein_abschnitt(self):
        text = ' '.join(self._pdf_seiten(self.gwh, ['deckblatt', 'zsk_01']))
        self.assertNotIn(TITEL, text)

    # ---- 6. Export-Dialog ----
    def test_dialog_hinweis_vorhanden(self):
        for projekt in (self.ewh, self.gwh):
            html = self.client.get(f'/export/projekt/{projekt.id}').text
            self.assertIn('id="zusammenfassung-hinweis" class="section-hint" style="display: none;"', html)
            self.assertIn('Die Zusammenfassung enthält nur Tests der folgenden ausgewählten Komponenten.', html)
            # Hinweis steht direkt nach der Zusammenfassungs-Checkbox, vor der naechsten Checkbox
            pos_cb = html.index('value="zusammenfassung_fehler"')
            pos_hinweis = html.index('id="zusammenfassung-hinweis"')
            pos_naechste = html.index('name="selected_sections"', pos_cb + 1)
            self.assertLess(pos_cb, pos_hinweis)
            self.assertLess(pos_hinweis, pos_naechste)
            # Export bleibt erlaubt: der Hinweis sperrt den Button nicht
            self.assertIn("zusammenfassungHinweis.style.display = (zusammenfassung && !komponente)", html)


if __name__ == '__main__':
    unittest.main()
