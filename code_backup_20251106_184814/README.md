# Code Backup vom 06.11.2025

**⚠️ HINWEIS: Dies ist ein historisches Code-Backup und sollte nicht mehr verwendet werden.**

## Zweck

Dieses Verzeichnis enthält ein vollständiges Backup des Codes vom **6. November 2025**, vor einer größeren Refactoring-Phase.

## Wichtige Informationen

### MySQL-Bezüge

Viele Dateien in diesem Backup enthalten noch **MySQL-spezifischen Code**:
- Python-Scripts mit `import pymysql`
- MySQL-Connection-Strings
- MySQL-spezifische SQL-Befehle

### Was ist veraltet?

- ❌ **Migrations-Scripts** mit pymysql-Imports
- ❌ **Config-Dateien** mit MySQL-Connection-Strings
- ❌ Verschiedene Utility-Scripts für MySQL-Datenbank

### Was wurde geändert?

Nach diesem Backup wurde das Projekt auf **SQLite 3** umgestellt:
- Alle MySQL-Dependencies entfernt
- Connection-Strings auf SQLite angepasst
- Migrations-Scripts archiviert

## Verwendung

**NICHT VERWENDEN!** Diese Dateien sind nur als Backup/Referenz gedacht.

Für den aktuellen Code siehe die Hauptverzeichnis-Dateien:
- `/app.py` - Aktuelle Hauptanwendung
- `/models.py` - Aktuelle Datenbankmodelle
- `/config.py` - Aktuelle Konfiguration (SQLite)

## Warum wurde dieses Backup erstellt?

1. **Sicherheit** vor größeren Code-Änderungen
2. **Referenz** für alte Implementierungen
3. **Rollback-Möglichkeit** falls benötigt

## Datum

- **Backup erstellt:** 06. November 2025, 18:48 Uhr
- **Backup-Grund:** Vor Code-Cleanup und Refactoring

---

**Status:** ARCHIVIERT
**Verwendung:** NUR ALS REFERENZ
