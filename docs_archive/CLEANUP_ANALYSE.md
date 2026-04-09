# Code-Aufräum-Analyse
**Datum:** 2025-11-06
**Ziel:** Identifikation nicht mehr benötigter Dateien und Code

---

## 📁 DATEIEN-KATEGORISIERUNG

### ✅ PRODUKTIV - BEHALTEN (8 Dateien)
**Diese Dateien sind essentiell für die Anwendung:**

| Datei | Größe | Zweck | Status |
|-------|-------|-------|--------|
| `app.py` | 49K | Haupt-Anwendung | ✅ KRITISCH |
| `models.py` | 4.9K | Datenbank-Modelle | ✅ KRITISCH |
| `config.py` | 666B | Production-Config | ✅ KRITISCH |
| `config_dev.py` | 716B | Development-Config | ✅ KRITISCH |
| `run_dev.py` | 1.4K | Dev-Server Starter | ✅ BEHALTEN |
| `run_dev_alt.py` | 636B | Dev-Server Port 8080 | ✅ BEHALTEN |
| `run_production.py` | 416B | Production-Server | ✅ BEHALTEN |

---

### 🔧 MIGRATIONS-SCRIPTS - ARCHIVIEREN (11 Dateien)
**Einmalig verwendete Scripts - bereits ausgeführt:**

| Datei | Größe | Zweck | Empfehlung |
|-------|-------|-------|------------|
| `migrate_database.py` | 3.7K | Initiale DB-Migration | 🗂️ ARCHIVIEREN |
| `migrate_weichenheizung.py` | 4.0K | WH-Migration | 🗂️ ARCHIVIEREN |
| `migrate_abnahmetest.py` | 6.0K | Abnahmetest-Migration | 🗂️ ARCHIVIEREN |
| `add_preset_antworten.py` | 1.2K | Preset-Spalte hinzufügen | 🗂️ ARCHIVIEREN |
| `add_spalte_column.py` | 1.3K | Spalten-Migration | 🗂️ ARCHIVIEREN |
| `fix_foreign_keys.py` | 2.0K | Foreign Key Fix | 🗂️ ARCHIVIEREN |
| `fix_komponente_index.py` | 2.4K | Index-Fix | 🗂️ ARCHIVIEREN |
| `update_projects_table.py` | 1.2K | Projekt-Tabelle Update | 🗂️ ARCHIVIEREN |
| `clear_test_results.py` | 1.1K | Test-Ergebnisse löschen | 🗂️ ARCHIVIEREN |
| `reset_db.py.py` | 447B | DB-Reset (falscher Name!) | ❌ LÖSCHEN |

**Empfehlung:** In `migrations_archive/` Ordner verschieben

---

### 🧪 TEST & HELPER-SCRIPTS - OPTIONAL (7 Dateien)
**Nützliche Helfer-Scripts:**

| Datei | Größe | Zweck | Empfehlung |
|-------|-------|-------|------------|
| `generate_test_data.py` | 11K | Test-Daten generieren | ⚠️ OPTIONAL |
| `create_test_project.py` | 9.5K | Test-Projekt erstellen | ✅ BEHALTEN |
| `update_all_presets.py` | 2.5K | Presets bulk update | ✅ BEHALTEN |
| `test_weasyprint.py` | 1.7K | WeasyPrint testen | ✅ BEHALTEN |
| `test_waitress.py` | 944B | Waitress testen | ⚠️ OPTIONAL |
| `verify_import.py` | 2.4K | Import verifizieren | ⚠️ OPTIONAL |
| `export_database.py` | 1.8K | DB-Export | ✅ BEHALTEN |

**Empfehlung:** In `scripts/` Ordner verschieben

---

### 📥 IMPORT-SCRIPTS - SPEZIALFALL (2 Dateien)

| Datei | Größe | Zweck | Empfehlung |
|-------|-------|-------|------------|
| `import_json_project.py` | 17K | JSON-Import | ⚠️ BEHALTEN (evtl. nutzen) |
| `import_obermatt_testfragen.py` | 9.7K | Obermatt-Testfragen Import | ⚠️ PRÜFEN |

**Frage:** Werden diese noch verwendet?

---

## 🗂️ VORGESCHLAGENE ORDNER-STRUKTUR

```
whs_app/
├── app.py                          # Haupt-App
├── models.py                       # Modelle
├── config.py                       # Production
├── config_dev.py                   # Development
├── run_dev.py                      # Dev-Server
├── run_dev_alt.py                  # Dev-Server Alt
├── run_production.py               # Production-Server
│
├── scripts/                        # ⭐ NEU: Helper-Scripts
│   ├── create_test_project.py
│   ├── update_all_presets.py
│   ├── test_weasyprint.py
│   ├── export_database.py
│   ├── import_json_project.py
│   ├── import_obermatt_testfragen.py
│   ├── generate_test_data.py       # optional
│   ├── test_waitress.py            # optional
│   └── verify_import.py            # optional
│
├── migrations_archive/             # ⭐ NEU: Alte Migrations
│   ├── migrate_database.py
│   ├── migrate_weichenheizung.py
│   ├── migrate_abnahmetest.py
│   ├── add_preset_antworten.py
│   ├── add_spalte_column.py
│   ├── fix_foreign_keys.py
│   ├── fix_komponente_index.py
│   ├── update_projects_table.py
│   └── clear_test_results.py
│
├── templates/                      # HTML-Templates
├── static/                         # CSS, JS
├── database/                       # SQLite-DB
├── uploads/                        # Uploads
├── logs/                           # Logs
└── venv/                           # Virtual Env
```

---

## 📄 TEMPLATES-ANALYSE

**Zu prüfen:**
- Gibt es ungenutzte Templates?
- Werden alle Templates in app.py verwendet?

---

## 🧹 APP.PY CODE-ANALYSE

**Zu prüfen:**
1. Gibt es ungenutzten Import?
2. Gibt es tote Routen?
3. Gibt es auskommentierten Code?
4. Gibt es doppelten Code?

---

## ⚠️ WICHTIGE DATEIEN ZUM LÖSCHEN

| Datei | Grund |
|-------|-------|
| `reset_db.py.py` | Falscher Dateiname (doppelt .py) |
| `config.py.backup` | Alte Backup-Datei |

---

## 📊 SPEICHER-EINSPARUNG

**Migrations-Scripts:** ~23 KB
**Optionale Test-Scripts:** ~15 KB
**Gesamt potentiell:** ~38 KB

(Nicht viel, aber bessere Organisation!)

---

## ✅ EMPFOHLENE AKTIONEN

### PHASE 1: Sicher löschen
1. ❌ `reset_db.py.py` löschen (falscher Name)
2. ❌ `config.py.backup` löschen (falls vorhanden)

### PHASE 2: Migrations archivieren
1. 📁 Ordner `migrations_archive/` erstellen
2. ➡️ Alle Migrations-Scripts verschieben

### PHASE 3: Scripts organisieren
1. 📁 Ordner `scripts/` erstellen
2. ➡️ Helper-Scripts verschieben

### PHASE 4: Code aufräumen
1. 🔍 app.py analysieren
2. 🔍 templates/ analysieren
3. 🧹 Toten Code entfernen

---

## 🚨 BACKUP ERSTELLEN

**VOR dem Aufräumen:**
```bash
# Datenbank-Backup
copy database\whs.db database_backups\whs_before_cleanup.db

# Code-Backup (ganzes Projekt)
# Einfach den kompletten Ordner kopieren
```

---

**NÄCHSTE SCHRITTE:** Warte auf Benutzer-Bestätigung!
