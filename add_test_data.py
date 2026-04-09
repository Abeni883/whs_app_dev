#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script zum Hinzufügen von Testdaten für Abnahmetests
"""

from app import app, db
from models import Project, TestQuestion, AbnahmeTestResult
import random

def add_test_results():
    with app.app_context():
        # Hole alle Projekte
        projects = Project.query.all()
        print(f"Gefundene Projekte: {len(projects)}")

        if not projects:
            print("Keine Projekte gefunden!")
            return

        # Nehme das erste Projekt
        projekt = projects[0]
        print(f"\nVerwende Projekt: {projekt.projektname} (ID: {projekt.id})")

        # Prüfe ob bereits Testergebnisse existieren
        existing = AbnahmeTestResult.query.filter_by(projekt_id=projekt.id).count()
        print(f"Existierende Testergebnisse: {existing}")

        if existing > 50:
            print("Projekt hat bereits viele Testergebnisse.")
            return

        # Hole alle Testfragen
        questions = TestQuestion.query.all()
        print(f"Verfügbare Testfragen: {len(questions)}")

        # Füge Testergebnisse für die ersten 20 Fragen hinzu
        added = 0
        for question in questions[:20]:
            # Prüfe ob bereits ein Ergebnis existiert
            existing_result = AbnahmeTestResult.query.filter_by(
                projekt_id=projekt.id,
                test_question_id=question.id,
                komponente_index=1,
                spalte='system'
            ).first()

            if existing_result:
                continue

            # Erstelle zufällige Testergebnisse
            lss_ch_result = random.choice(['correct', 'incorrect', 'not_testable'])
            wh_lts_result = random.choice(['correct', 'incorrect', 'not_testable'])

            result = AbnahmeTestResult(
                projekt_id=projekt.id,
                test_question_id=question.id,
                komponente_index=1,
                spalte='system',
                lss_ch_result=lss_ch_result,
                wh_lts_result=wh_lts_result,
                lss_ch_bemerkung='Test Bemerkung LSS-CH' if random.random() > 0.7 else None,
                wh_lts_bemerkung='Test Bemerkung WH-LTS' if random.random() > 0.7 else None
            )

            db.session.add(result)
            added += 1

        db.session.commit()
        print(f"\n✓ {added} neue Testergebnisse hinzugefügt!")
        print(f"Projekt '{projekt.projektname}' hat jetzt Testdaten zum Testen.")

if __name__ == '__main__':
    add_test_results()
