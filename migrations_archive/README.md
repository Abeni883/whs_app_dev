# Migrations-Archive (MySQL - VERALTET)

**⚠️ ACHTUNG: Diese Dateien sind veraltet und dürfen NICHT mehr verwendet werden!**

## Zweck dieses Verzeichnisses

Dieses Verzeichnis enthält alte Migrations-Scripts, die **für MySQL** geschrieben wurden, als das Projekt noch MySQL als Datenbank verwendete.

## Aktueller Status

- ✅ Das Projekt verwendet jetzt **SQLite 3** als Datenbank
- ❌ Diese MySQL-Migrations-Scripts sind **nicht kompatibel** mit SQLite
- 🗂️ Die Dateien werden nur aus historischen Gründen aufbewahrt

## Inhalt

Alle Python-Dateien in diesem Verzeichnis:
- Verwenden `pymysql` für Datenbankverbindungen
- Enthalten MySQL-spezifische SQL-Befehle (z.B. `SHOW TABLES`, `DESCRIBE`, `ALTER TABLE`)
- Sind für die MySQL-Datenbank `abnahmetest` geschrieben
- Enthalten teilweise hart-codierte MySQL-Credentials (nicht mehr gültig)

## Was tun, wenn Sie diese Scripts verwenden möchten?

**NICHT VERWENDEN!** Stattdessen:

1. **Für Datenbank-Initialisierung:**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Datenbank erstellt!')"
   ```

2. **Für Datenbank-Schema-Änderungen:**
   - Ändere die Models in `models.py`
   - Erstelle eine neue SQLite-Migration mit Alembic (falls benötigt)
   - Oder verwende SQLAlchemy's `db.create_all()` für neue Tabellen

3. **Für Datenbank-Backups:**
   ```bash
   # SQLite Backup (einfache Dateikopie)
   copy database\whs.db database_backups\whs_backup.db

   # Oder mit Python-Script
   python scripts\export_database.py
   ```

## Dateien in diesem Verzeichnis

| Datei | Zweck | Status |
|-------|-------|--------|
| `add_spalte_column.py` | Fügt 'spalte' Spalte zu abnahme_test_results hinzu | ❌ Veraltet (MySQL) |
| `add_preset_antworten.py` | Fügt preset_antworten JSON-Feld hinzu | ❌ Veraltet (MySQL) |
| `clear_test_results.py` | Löscht alle Test-Ergebnisse | ❌ Veraltet (MySQL) |
| `fix_foreign_keys.py` | Korrigiert Foreign Key Constraints | ❌ Veraltet (MySQL) |
| `fix_komponente_index.py` | Korrigiert komponente_index-Feldstruktur | ❌ Veraltet (MySQL) |
| `migrate_abnahmetest.py` | Große Datenbank-Migration für Abnahmetest-System | ❌ Veraltet (MySQL) |
| `migrate_database.py` | Initiale project_id-Migration | ❌ Veraltet (MySQL) |
| `migrate_weichenheizung.py` | Umstellung auf Weichenheizungs-Struktur | ❌ Veraltet (MySQL) |
| `update_projects_table.py` | Aktualisiert projects-Tabelle | ❌ Veraltet (MySQL) |

## Für Entwickler

Falls Sie neue Datenbank-Änderungen vornehmen müssen:

1. **Modelle ändern** in `models.py`
2. **SQLAlchemy nutzen** für Schema-Updates:
   ```python
   from app import app, db
   from models import YourNewModel

   with app.app_context():
       db.create_all()  # Erstellt neue Tabellen
   ```

3. **Alembic verwenden** (optional, für komplexe Migrations):
   ```bash
   pip install alembic
   alembic init alembic
   alembic revision --autogenerate -m "Beschreibung der Änderung"
   alembic upgrade head
   ```

## Warum wurden diese Dateien nicht gelöscht?

Diese Dateien werden aus folgenden Gründen archiviert:

1. **Historische Dokumentation** des Entwicklungsprozesses
2. **Referenz** für ursprüngliche Datenbank-Struktur
3. **Nachvollziehbarkeit** von Schema-Änderungen
4. **Backup** für den Fall, dass alte Migrations-Logik benötigt wird

## Weitere Informationen

Für aktuelle Datenbank-Informationen siehe:
- `models.py` - Aktuelle SQLAlchemy Models
- `config.py` - Aktuelle Datenbank-Konfiguration (SQLite)
- `README.md` - Haupt-Dokumentation
- `SOFTWAREBESCHREIBUNG.md` - Detaillierte Software-Beschreibung

---

**Letzte Aktualisierung:** 2025-01-10
**Status:** ARCHIVIERT - NUR FÜR HISTORISCHE ZWECKE
**Warnung:** NICHT VERWENDEN! Diese Scripts sind nur für MySQL kompatibel.
