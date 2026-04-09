"""
Zeigt eine Übersicht aller importierten Projekte
"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import Project, WHKConfig, AbnahmeTestResult, TestQuestion
from sqlalchemy import func

with app.app_context():
    projekte = Project.query.order_by(Project.id).all()

    print("=" * 80)
    print("ALLE IMPORTIERTEN PROJEKTE")
    print("=" * 80)
    print(f"\nTotal Projekte: {len(projekte)}\n")

    total_whks = 0
    total_results = 0

    for p in projekte:
        whks = WHKConfig.query.filter_by(projekt_id=p.id).all()
        results = AbnahmeTestResult.query.filter_by(projekt_id=p.id).count()

        total_whks += len(whks)
        total_results += results

        print(f"{p.id:2d}. {p.projektname:30s} ({p.didok_betriebspunkt:6s}) - {len(whks):2d} WHKs, {results:4d} Ergebnisse")

        # Zeige Komponententyp-Verteilung
        komponenten = db.session.query(
            TestQuestion.komponente_typ,
            func.count(AbnahmeTestResult.id).label('anzahl')
        ).join(
            AbnahmeTestResult
        ).filter(
            AbnahmeTestResult.projekt_id == p.id
        ).group_by(TestQuestion.komponente_typ).all()

        if komponenten:
            komponenten_str = ", ".join([f"{k}: {a}" for k, a in komponenten])
            print(f"    {komponenten_str}")

    print("\n" + "=" * 80)
    print("GESAMT")
    print("=" * 80)
    print(f"Projekte: {len(projekte)}")
    print(f"WHK-Konfigurationen: {total_whks}")
    print(f"Testergebnisse: {total_results}")
