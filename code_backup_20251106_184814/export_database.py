"""
Datenbank-Export Script für SQLite
Erstellt sowohl eine Kopie der .db-Datei als auch einen SQL-Dump
"""
import sqlite3
import shutil
from datetime import datetime
import os

# Zeitstempel für Dateinamen
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Pfade
source_db = 'database/whs.db'
backup_dir = 'database_backups'

# Erstelle Backup-Verzeichnis falls nicht vorhanden
os.makedirs(backup_dir, exist_ok=True)

# 1. Kopiere die .db-Datei direkt (vollständiges Backup)
db_backup_path = os.path.join(backup_dir, f'whs_backup_{timestamp}.db')
shutil.copy2(source_db, db_backup_path)
print(f'[OK] Datenbank-Datei kopiert: {db_backup_path}')

# 2. Erstelle SQL-Dump (textbasiertes Backup)
sql_backup_path = os.path.join(backup_dir, f'whs_backup_{timestamp}.sql')
conn = sqlite3.connect(source_db)

with open(sql_backup_path, 'w', encoding='utf-8') as f:
    for line in conn.iterdump():
        f.write(f'{line}\n')

conn.close()
print(f'[OK] SQL-Dump erstellt: {sql_backup_path}')

# 3. Statistiken anzeigen
conn = sqlite3.connect(source_db)
cursor = conn.cursor()

print('\n=== Datenbank-Statistiken ===')

# Tabellen und Anzahl der Einträge
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()

for table in tables:
    table_name = table[0]
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f'  {table_name}: {count} Einträge')

conn.close()

# 4. Dateigröße
db_size = os.path.getsize(source_db)
db_size_mb = db_size / (1024 * 1024)
print(f'\nDatenbank-Größe: {db_size_mb:.2f} MB')

print('\n[OK] Export erfolgreich abgeschlossen!')
print(f'\nBackup-Dateien:')
print(f'  1. {db_backup_path}')
print(f'  2. {sql_backup_path}')
