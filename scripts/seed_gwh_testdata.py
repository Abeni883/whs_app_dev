#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Seed-Script für GWH-Testdaten

Füllt alle GWH-Tests für ein Projekt mit verschiedenen Testresultaten.
Verwendet eine Mischung aus richtig, falsch und nicht_testbar.

Verwendung:
    python scripts/seed_gwh_testdata.py [projekt_id]

    Falls keine projekt_id angegeben wird, wird nach "Rotkreuz" gesucht.
"""

import sys
import os
import random

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (
    Project, TestQuestion, AbnahmeTestResult,
    ZSKConfig, HGLSConfig, GWHMeteostation,
    ZSKParameterPruefung, HGLSParameterPruefung
)
from parameter_definitionen import ZSK_PARAMETER, HGLS_PARAMETER
from datetime import datetime


def seed_gwh_tests(projekt_id):
    """Füllt alle GWH-Tests für ein Projekt mit Testdaten."""

    with app.app_context():
        # Projekt laden
        projekt = Project.query.get(projekt_id)
        if not projekt:
            print(f"Fehler: Projekt mit ID {projekt_id} nicht gefunden!")
            return False

        if projekt.energie != 'GWH':
            print(f"Fehler: Projekt '{projekt.projektname}' ist kein GWH-Projekt (energie={projekt.energie})!")
            return False

        print(f"\n{'='*60}")
        print(f"Fülle Testdaten für Projekt: {projekt.projektname} (ID: {projekt_id})")
        print(f"{'='*60}\n")

        # Konfigurationen laden
        hgls_config = HGLSConfig.query.filter_by(projekt_id=projekt_id).first()
        zsk_configs = ZSKConfig.query.filter_by(projekt_id=projekt_id).order_by(ZSKConfig.reihenfolge).all()
        meteostationen = GWHMeteostation.query.filter_by(projekt_id=projekt_id).all()

        print(f"Konfiguration:")
        print(f"  - HGLS: {'Ja' if hgls_config else 'Nein'}")
        print(f"  - ZSKs: {len(zsk_configs)}")
        for zsk in zsk_configs:
            print(f"    - ZSK {zsk.zsk_nummer}: {zsk.anzahl_teile} Teile, TS: {zsk.hat_temperatursonde}")
        print(f"  - Meteostationen: {len(meteostationen)}")
        for ms in meteostationen:
            print(f"    - MS {ms.ms_nummer}: {ms.name}")
        print()

        # Alte Testergebnisse löschen
        deleted = AbnahmeTestResult.query.filter_by(projekt_id=projekt_id).delete()
        print(f"Gelöschte alte Testergebnisse: {deleted}")

        # Alte Parameter-Prüfungen löschen
        deleted_zsk_param = ZSKParameterPruefung.query.filter_by(projekt_id=projekt_id).delete()
        deleted_hgls_param = HGLSParameterPruefung.query.filter_by(projekt_id=projekt_id).delete()
        print(f"Gelöschte ZSK-Parameter-Prüfungen: {deleted_zsk_param}")
        print(f"Gelöschte HGLS-Parameter-Prüfungen: {deleted_hgls_param}")

        db.session.commit()

        # Testresultate-Verteilung (gewichtet: mehr "richtig")
        # 70% richtig, 15% falsch, 15% nicht_testbar
        def get_random_result():
            r = random.random()
            if r < 0.70:
                return 'richtig'
            elif r < 0.85:
                return 'falsch'
            else:
                return 'nicht_testbar'

        # Zähler für Statistik
        stats = {'richtig': 0, 'falsch': 0, 'nicht_testbar': 0, 'total': 0}

        def create_test_result(question_id, komponente_index, spalte, lss_result=None, wh_result=None):
            """Erstellt einen Testeintrag mit zufälligen oder vorgegebenen Ergebnissen."""
            if lss_result is None:
                lss_result = get_random_result()
            if wh_result is None:
                wh_result = get_random_result()

            # Bemerkung nur bei "falsch"
            lss_bemerkung = f"Test-Bemerkung LSS-CH für {spalte}" if lss_result == 'falsch' else None
            wh_bemerkung = f"Test-Bemerkung WH-LTS für {spalte}" if wh_result == 'falsch' else None

            result = AbnahmeTestResult(
                projekt_id=projekt_id,
                test_question_id=question_id,
                komponente_index=komponente_index,
                spalte=spalte,
                lss_ch_result=lss_result,
                lss_ch_bemerkung=lss_bemerkung,
                wh_lts_result=wh_result,
                wh_lts_bemerkung=wh_bemerkung,
                getestet_am=datetime.utcnow()
            )
            db.session.add(result)

            stats[lss_result] += 1
            stats[wh_result] += 1
            stats['total'] += 2

            return result

        # ==================== GWH-ANLAGE TESTS ====================
        print("\n[1/6] GWH-Anlage Tests...")
        anlage_fragen = TestQuestion.query.filter_by(komponente_typ='GWH_Anlage').all()
        for frage in anlage_fragen:
            create_test_result(frage.id, 'GWH-Anlage', 'GWH-Anlage')
        print(f"  -> {len(anlage_fragen)} Fragen erstellt")

        # ==================== HGLS TESTS ====================
        if hgls_config:
            print("\n[2/6] HGLS Tests...")
            hgls_fragen = TestQuestion.query.filter_by(komponente_typ='HGLS').all()
            for frage in hgls_fragen:
                create_test_result(frage.id, 'HGLS', 'HGLS')
            print(f"  -> {len(hgls_fragen)} Fragen erstellt")

            # HGLS-Parameter
            print("\n[2b/6] HGLS Parameter...")
            for param in HGLS_PARAMETER:
                # 80% geprüft, 15% nicht testbar, 5% offen
                r = random.random()
                if r < 0.80:
                    geprueft = True
                    nicht_testbar = False
                    ist_wert = f"{random.uniform(0.5, 10.0):.2f}"
                elif r < 0.95:
                    geprueft = False
                    nicht_testbar = True
                    ist_wert = ""
                else:
                    geprueft = False
                    nicht_testbar = False
                    ist_wert = ""

                pruefung = HGLSParameterPruefung(
                    projekt_id=projekt_id,
                    parameter_name=param['name'],
                    ist_wert=ist_wert,
                    geprueft=geprueft,
                    nicht_testbar=nicht_testbar,
                    geprueft_von='Test-Script' if geprueft else None,
                    geprueft_am=datetime.utcnow() if geprueft else None
                )
                db.session.add(pruefung)
            print(f"  -> {len(HGLS_PARAMETER)} Parameter erstellt")
        else:
            print("\n[2/6] HGLS Tests... (übersprungen - kein HGLS konfiguriert)")

        # ==================== ZSK TESTS ====================
        print("\n[3/6] ZSK Tests...")
        zsk_fragen = TestQuestion.query.filter_by(komponente_typ='ZSK').all()
        zsk_test_count = 0
        for zsk in zsk_configs:
            for frage in zsk_fragen:
                create_test_result(frage.id, '', f'ZSK {zsk.zsk_nummer}')
                zsk_test_count += 1
        print(f"  -> {zsk_test_count} Fragen erstellt ({len(zsk_fragen)} Fragen x {len(zsk_configs)} ZSKs)")

        # ==================== ZSK PARAMETER ====================
        print("\n[3b/6] ZSK Parameter...")
        zsk_param_count = 0
        for zsk in zsk_configs:
            for param in ZSK_PARAMETER:
                r = random.random()
                if r < 0.80:
                    geprueft = True
                    nicht_testbar = False
                    ist_wert = f"{random.uniform(0.5, 10.0):.2f}"
                elif r < 0.95:
                    geprueft = False
                    nicht_testbar = True
                    ist_wert = ""
                else:
                    geprueft = False
                    nicht_testbar = False
                    ist_wert = ""

                pruefung = ZSKParameterPruefung(
                    projekt_id=projekt_id,
                    zsk_nummer=zsk.zsk_nummer,
                    parameter_name=param['name'],
                    ist_wert=ist_wert,
                    geprueft=geprueft,
                    nicht_testbar=nicht_testbar,
                    geprueft_von='Test-Script' if geprueft else None,
                    geprueft_am=datetime.utcnow() if geprueft else None
                )
                db.session.add(pruefung)
                zsk_param_count += 1
        print(f"  -> {zsk_param_count} Parameter erstellt ({len(ZSK_PARAMETER)} Parameter x {len(zsk_configs)} ZSKs)")

        # ==================== TEILE TESTS ====================
        print("\n[4/6] Teile Tests...")
        teile_fragen = TestQuestion.query.filter_by(komponente_typ='GWH_Teile').all()
        teile_test_count = 0
        for zsk in zsk_configs:
            for teil_num in range(1, (zsk.anzahl_teile or 0) + 1):
                teil_name = f"Teil {teil_num:02d}"
                for frage in teile_fragen:
                    create_test_result(frage.id, f'ZSK {zsk.zsk_nummer}', teil_name)
                    teile_test_count += 1
        print(f"  -> {teile_test_count} Fragen erstellt")

        # ==================== TEMPERATURSONDE TESTS ====================
        print("\n[5/6] Temperatursonde Tests...")
        ts_fragen = TestQuestion.query.filter_by(komponente_typ='GWH_Temperatursonde').all()
        ts_test_count = 0
        for zsk in zsk_configs:
            if zsk.hat_temperatursonde:
                for frage in ts_fragen:
                    create_test_result(frage.id, f'ZSK {zsk.zsk_nummer}', 'TS')
                    ts_test_count += 1
        print(f"  -> {ts_test_count} Fragen erstellt")

        # ==================== METEOSTATION TESTS ====================
        print("\n[6/6] Meteostation Tests...")
        ms_fragen = TestQuestion.query.filter_by(komponente_typ='GWH_Meteostation').all()
        ms_test_count = 0
        for ms in meteostationen:
            for frage in ms_fragen:
                create_test_result(frage.id, f'MS {ms.ms_nummer}', ms.name)
                ms_test_count += 1
        print(f"  -> {ms_test_count} Fragen erstellt")

        # Speichern
        db.session.commit()

        # Statistik ausgeben
        print(f"\n{'='*60}")
        print("ZUSAMMENFASSUNG")
        print(f"{'='*60}")
        print(f"Gesamte Testergebnisse: {stats['total']}")
        print(f"  - Richtig:        {stats['richtig']} ({stats['richtig']/stats['total']*100:.1f}%)")
        print(f"  - Falsch:         {stats['falsch']} ({stats['falsch']/stats['total']*100:.1f}%)")
        print(f"  - Nicht testbar:  {stats['nicht_testbar']} ({stats['nicht_testbar']/stats['total']*100:.1f}%)")
        print(f"\nTestdaten erfolgreich erstellt!")

        return True


def find_rotkreuz_project():
    """Sucht das Projekt 'Rotkreuz' in der Datenbank."""
    with app.app_context():
        # Suche nach Projekten mit "Rotkreuz" im Namen
        projekt = Project.query.filter(Project.projektname.ilike('%Rotkreuz%')).first()
        if projekt:
            return projekt.id

        # Fallback: Erstes GWH-Projekt
        projekt = Project.query.filter_by(energie='GWH').first()
        if projekt:
            print(f"Kein 'Rotkreuz' Projekt gefunden. Verwende stattdessen: {projekt.projektname}")
            return projekt.id

        return None


if __name__ == '__main__':
    # Projekt-ID aus Argumenten oder automatisch finden
    if len(sys.argv) > 1:
        try:
            projekt_id = int(sys.argv[1])
        except ValueError:
            print(f"Fehler: '{sys.argv[1]}' ist keine gültige Projekt-ID!")
            sys.exit(1)
    else:
        projekt_id = find_rotkreuz_project()
        if projekt_id is None:
            print("Fehler: Kein GWH-Projekt gefunden!")
            sys.exit(1)

    # Testdaten erstellen
    success = seed_gwh_tests(projekt_id)
    sys.exit(0 if success else 1)
