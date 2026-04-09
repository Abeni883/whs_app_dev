-- Migration: Fügt erwartetes_ergebnis und screenshot_pfad Felder zur test_questions Tabelle hinzu
--
-- Führe diese SQL-Befehle aus oder verwende das Python-Skript in der virtuellen Umgebung

ALTER TABLE test_questions ADD COLUMN erwartetes_ergebnis TEXT;
ALTER TABLE test_questions ADD COLUMN screenshot_pfad VARCHAR(255);
