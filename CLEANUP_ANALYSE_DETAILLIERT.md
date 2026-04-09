# DETAILLIERTE CLEANUP-ANALYSE
**Datum:** 2025-11-06 (nach Phase 1-3)
**Ziel:** Identifikation ALLER nicht benötigten Dateien

---

## DATEIEN ZUM LÖSCHEN

### 1. DOKUMENTATIONS-DATEIEN (Optional archivieren)

| Datei | Größe | Beschreibung | Empfehlung |
|-------|-------|--------------|------------|
| `CHANGELOG.md` | 11K | Alte Änderungshistorie | ⚠️ ARCHIVIEREN |
| `CHANGELOG_SESSION_2025-11-03.md` | 14K | Session-Changelog | ⚠️ ARCHIVIEREN |
| `SESSION_BUTTON_FORTSCHRITT.md` | 20K | Session-Dokumentation | ⚠️ ARCHIVIEREN |
| `SESSION_DOKUMENTATION.md` | 18K | Session-Dokumentation | ⚠️ ARCHIVIEREN |
| `CLEANUP_ANALYSE.md` | 6.1K | Erste Cleanup-Analyse | ⚠️ ARCHIVIEREN |

**Empfehlung:** In `docs_archive/` verschieben

---

### 2. SQL-DATEIEN (MySQL - nicht mehr benötigt)

| Datei | Größe | Beschreibung | Empfehlung |
|-------|-------|--------------|------------|
| `setup_database.sql` | 1.4K | MySQL Datenbank-Setup | ❌ LÖSCHEN |
| `migrate_add_project_id.sql` | 523B | MySQL Migration | ❌ LÖSCHEN |

**Grund:** Anwendung nutzt SQLite, nicht MySQL!

---

### 3. ALTE PROJEKT-DATEIEN

| Datei | Größe | Beschreibung | Empfehlung |
|-------|-------|--------------|------------|
| `Projekte/Sargans SA.json` | 230K | Alte JSON-Projektdatei | ⚠️ ARCHIVIEREN |
| `WH_331 Obermatt OM_signed.pdf` | 558K | Test-PDF-Dokument | ⚠️ ARCHIVIEREN |

**Empfehlung:** In `archive/` oder `test_data/` verschieben

---

### 4. SYSTEM-ARTEFAKTE

| Datei | Größe | Beschreibung | Empfehlung |
|-------|-------|--------------|------------|
| `nul` | 83B | Windows-Artefakt | ❌ LÖSCHEN |
| `__pycache__/` | 196K | Python Cache | ✅ KANN GELÖSCHT WERDEN |

**Hinweis:** __pycache__ wird automatisch neu erstellt

---

### 5. ALTE DATABASE-BACKUPS

| Datei | Größe | Beschreibung | Empfehlung |
|-------|-------|--------------|------------|
| `database_backups/abnahmetest_backup_%date...sql` | 52B | Fehlerhafter Backup-Name | ❌ LÖSCHEN |
| `database_backups/whs_backup_%date...sql` | 0B | Fehlerhafter Backup-Name | ❌ LÖSCHEN |
| `database_backups/whs_backup_20251106_154328.db` | 124K | Altes Backup | ⚠️ OPTIONAL |
| `database_backups/whs_backup_20251106_154341.db` | 124K | Altes Backup | ⚠️ OPTIONAL |
| `database_backups/whs_backup_20251106_154341.sql` | 156K | Altes Backup | ⚠️ OPTIONAL |
| `database_backups/whs_before_cleanup_20251106_184814.db` | 124K | **NEUESTES BACKUP** | ✅ BEHALTEN |

**Empfehlung:** Alte Backups löschen, nur neuestes behalten

---

### 6. LOGS (Optional bereinigen)

| Datei | Größe | Beschreibung | Empfehlung |
|-------|-------|--------------|------------|
| `logs/production.log` | 3.2K | Production-Log | ⚠️ BEHALTEN |
| `logs/service_error.log` | 118K | Service-Fehlerlog | ⚠️ KANN GELEERT WERDEN |
| `logs/service_output.log` | 5.2K | Service-Output | ⚠️ BEHALTEN |

---

## DATEIEN BEHALTEN

### PRODUKTIV (7 Python-Dateien)
- ✅ app.py
- ✅ models.py
- ✅ config.py
- ✅ config_dev.py
- ✅ run_dev.py
- ✅ run_dev_alt.py
- ✅ run_production.py

### KONFIGURATION
- ✅ requirements.txt
- ✅ .gitignore

### DOKUMENTATION
- ✅ README.md
- ✅ README_DEV.md
- ✅ SOFTWAREBESCHREIBUNG.md

### ASSETS (Produktive Dateien)
- ✅ assets/ (Logo, Icons)

### BACKUPS
- ✅ code_backup_20251106_184814/
- ✅ database_backups/whs_before_cleanup_20251106_184814.db

### ORDNER-STRUKTUR
- ✅ templates/
- ✅ static/
- ✅ database/
- ✅ migrations_archive/
- ✅ scripts/
- ✅ .claude/

---

## EMPFOHLENE AKTIONEN

### PHASE 4: Aufräumen nach Reorganisation

#### 4.1 - Dokumentation archivieren
```bash
mkdir docs_archive
mv CHANGELOG*.md docs_archive/
mv SESSION*.md docs_archive/
mv CLEANUP_ANALYSE.md docs_archive/
```

#### 4.2 - SQL-Dateien löschen
```bash
rm setup_database.sql
rm migrate_add_project_id.sql
```

#### 4.3 - System-Artefakte löschen
```bash
rm nul
rm -rf __pycache__
```

#### 4.4 - Alte Projekt-Dateien archivieren
```bash
mkdir archive
mv "WH_331 Obermatt OM_signed.pdf" archive/
mv Projekte/ archive/
```

#### 4.5 - Alte Backups bereinigen
```bash
cd database_backups
rm "abnahmetest_backup_%date"*
rm "whs_backup_%date"*
rm whs_backup_20251106_154328.db
rm whs_backup_20251106_154341.db
rm whs_backup_20251106_154341.sql
# BEHALTEN: whs_before_cleanup_20251106_184814.db
```

#### 4.6 - Logs bereinigen (optional)
```bash
# Service-Error-Log leeren (wird neu erstellt)
echo "" > logs/service_error.log
```

---

## SPEICHER-EINSPARUNG

| Kategorie | Größe |
|-----------|-------|
| Dokumentation | ~69 KB |
| SQL-Dateien | ~2 KB |
| Projekt-Dateien | ~788 KB |
| System-Artefakte | ~279 KB |
| Alte Backups | ~404 KB |
| **GESAMT** | **~1.5 MB** |

---

## FINALE STRUKTUR NACH PHASE 4

```
whs_app/
├── app.py                          # Haupt-Anwendung
├── models.py                       # Datenbank-Modelle
├── config.py                       # Production-Config
├── config_dev.py                   # Development-Config
├── run_dev.py                      # Dev-Server
├── run_dev_alt.py                  # Dev-Server Alt
├── run_production.py               # Production-Server
├── requirements.txt                # Dependencies
├── .gitignore                      # Git-Ignore
│
├── README.md                       # ✅ Haupt-Readme
├── README_DEV.md                   # ✅ Dev-Readme
├── SOFTWAREBESCHREIBUNG.md         # ✅ Software-Doku
│
├── migrations_archive/             # Alte Migrations
├── scripts/                        # Helper-Scripts
├── docs_archive/                   # ⭐ NEU: Alte Dokumentation
├── archive/                        # ⭐ NEU: Alte Projekt-Dateien
│
├── templates/                      # HTML-Templates
├── static/                         # CSS, JS
├── assets/                         # Logos, Icons
├── database/                       # SQLite-DB
├── database_backups/               # Nur neuestes Backup
├── logs/                           # Logs (bereinigt)
├── uploads/                        # Uploads
├── venv/                           # Virtual Environment
├── code_backup_20251106_184814/    # Code-Backup
└── .claude/                        # Claude-Einstellungen
```

---

## ZUSAMMENFASSUNG

### ZU LÖSCHEN
- 2 SQL-Dateien (MySQL, nicht mehr benötigt)
- 2 System-Artefakte (nul, __pycache__)
- 5 alte DB-Backups

### ZU ARCHIVIEREN
- 5 Dokumentations-Dateien
- 1 PDF-Datei
- 1 Projekte-Ordner

### SPEICHER-EINSPARUNG
- ~1.5 MB gespart
- Deutlich übersichtlichere Struktur

---

**WICHTIG:** Backup ist bereits vorhanden: `code_backup_20251106_184814/`
