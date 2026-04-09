# Testprotokoll - Session 14.12.2024

## Übersicht der Änderungen

1. **EWH-Konfiguration: Meteostation-Sektion umstrukturiert**
2. **Mindestens 1 Meteostation pro Projekt**
3. **WHK-Block Styling an ZSK-Block angepasst**
4. **Abnahmetest: Auto-Jump zur ersten unbeantworteten Frage**

---

## 1. EWH-Konfiguration: Meteostation-Sektion

### Beschreibung
- Meteostation-Spalte aus WHK-Tabelle entfernt
- Separate Meteostationen-Sektion hinzugefügt (max. 5 Stück, wie bei GWH)
- Dynamisches Hinzufügen/Löschen von Meteostationen

### Testschritte

| Nr. | Testfall | Erwartetes Ergebnis | ✓/✗ |
|-----|----------|---------------------|-----|
| 1.1 | EWH-Projekt öffnen → Konfiguration | Separate "Meteostationen"-Sektion unterhalb der WHK-Tabelle sichtbar |  |
| 1.2 | WHK-Tabelle prüfen | Keine "Meteostation"-Spalte mehr in der WHK-Tabelle |  |
| 1.3 | Meteostation hinzufügen (+ Button) | Neue Zeile wird hinzugefügt mit automatischer Nummerierung (MS 02, MS 03...) |  |
| 1.4 | Maximal 5 Meteostationen hinzufügen | Nach 5 Meteostationen ist der "+ Hinzufügen" Button deaktiviert |  |
| 1.5 | Meteostation-Name bearbeiten | Name wird per Auto-Save gespeichert |  |
| 1.6 | WHK-Dropdown in Meteostation | Dropdown zeigt alle konfigurierten WHKs zur Auswahl |  |
| 1.7 | Seite neu laden | Alle Meteostationen sind korrekt gespeichert |  |

---

## 2. Mindestens 1 Meteostation pro Projekt

### Beschreibung
- Jedes Projekt (EWH und GWH) muss mindestens 1 Meteostation haben
- Automatische Erstellung bei neuen Projekten
- Löschen der letzten Meteostation wird verhindert

### Testschritte

| Nr. | Testfall | Erwartetes Ergebnis | ✓/✗ |
|-----|----------|---------------------|-----|
| 2.1 | Neues EWH-Projekt erstellen | Automatisch "MS 01" in der Meteostationen-Sektion vorhanden |  |
| 2.2 | Neues GWH-Projekt erstellen | Automatisch "MS 01" in der Meteostationen-Sektion vorhanden |  |
| 2.3 | EWH: Letzte Meteostation löschen versuchen | Löschen-Button ist deaktiviert (ausgegraut) |  |
| 2.4 | GWH: Letzte Meteostation löschen versuchen | Löschen-Button ist deaktiviert (ausgegraut) |  |
| 2.5 | EWH: Bei 2+ Meteostationen eine löschen | Löschen funktioniert, solange mindestens 1 übrig bleibt |  |
| 2.6 | GWH: Bei 2+ Meteostationen eine löschen | Löschen funktioniert, solange mindestens 1 übrig bleibt |  |
| 2.7 | Klick auf deaktivierten Löschen-Button | Alert: "Mindestens eine Meteostation muss vorhanden sein" |  |

---

## 3. WHK-Block Styling an ZSK-Block angepasst

### Beschreibung
- EWH WHK-Sektion hat jetzt gleiches Styling wie GWH ZSK-Sektion
- Container-Struktur vereinheitlicht
- Titel geändert zu "Weichenheizungskästen (WHK)"

### Testschritte

| Nr. | Testfall | Erwartetes Ergebnis | ✓/✗ |
|-----|----------|---------------------|-----|
| 3.1 | EWH-Konfiguration öffnen | WHK-Sektion hat Titel "Weichenheizungskästen (WHK)" |  |
| 3.2 | Visueller Vergleich EWH vs GWH | WHK-Block (EWH) sieht aus wie ZSK-Block (GWH) |  |
| 3.3 | Checkbox-Zellen prüfen | Checkboxen sind vertikal zentriert |  |
| 3.4 | Dark Mode testen | Styling funktioniert korrekt im Dark Mode |  |

---

## 4. Abnahmetest: Auto-Jump zur ersten unbeantworteten Frage

### Beschreibung
- Beim Öffnen einer Test-Seite springt die Ansicht automatisch zur ersten unbeantworteten Frage
- "Unbeantwortet" = LSS-CH ODER WH-LTS hat keine Auswahl
- Grüne Benachrichtigung "Fortgesetzt bei Frage X von Y" für 3 Sekunden
- Gilt für EWH (alle Komponenten) und GWH (alle außer Parameter)

### Testschritte EWH

| Nr. | Testfall | Erwartetes Ergebnis | ✓/✗ |
|-----|----------|---------------------|-----|
| 4.1 | EWH Anlage-Test neu starten | Startet bei Frage 1, keine Benachrichtigung |  |
| 4.2 | Frage 1-3 beantworten (LSS-CH + WH-LTS), Seite neu laden | Springt zu Frage 4, Benachrichtigung "Fortgesetzt bei Frage 4 von X" |  |
| 4.3 | Nur LSS-CH bei Frage 1 beantworten, Seite neu laden | Bleibt bei Frage 1 (WH-LTS fehlt noch) |  |
| 4.4 | Nur WH-LTS bei Frage 1 beantworten, Seite neu laden | Bleibt bei Frage 1 (LSS-CH fehlt noch) |  |
| 4.5 | Alle Fragen beantworten, Seite neu laden | Startet bei Frage 1, keine Benachrichtigung |  |
| 4.6 | EWH WHK-Test testen | Auto-Jump funktioniert wie oben |  |
| 4.7 | EWH Abgang-Test testen | Auto-Jump funktioniert wie oben |  |
| 4.8 | EWH Temperatursonde-Test testen | Auto-Jump funktioniert wie oben |  |
| 4.9 | EWH Antriebsheizung-Test testen | Auto-Jump funktioniert wie oben |  |
| 4.10 | EWH Meteostation-Test testen | Auto-Jump funktioniert wie oben |  |

### Testschritte GWH

| Nr. | Testfall | Erwartetes Ergebnis | ✓/✗ |
|-----|----------|---------------------|-----|
| 4.11 | GWH Anlage-Test neu starten | Startet bei Frage 1, keine Benachrichtigung |  |
| 4.12 | Frage 1-3 beantworten (LSS-CH + WH-LTS), Seite neu laden | Springt zu Frage 4, Benachrichtigung erscheint |  |
| 4.13 | GWH HGLS-Test testen | Auto-Jump funktioniert |  |
| 4.14 | GWH ZSK-Test testen | Auto-Jump funktioniert |  |
| 4.15 | GWH Teile-Test testen | Auto-Jump funktioniert |  |
| 4.16 | GWH Temperatursonde-Test testen | Auto-Jump funktioniert |  |
| 4.17 | GWH Meteostation-Test testen | Auto-Jump funktioniert |  |
| 4.18 | GWH ZSK-Parameter-Seite | KEIN Auto-Jump (Parameter-Seiten ausgenommen) |  |

### Benachrichtigung prüfen

| Nr. | Testfall | Erwartetes Ergebnis | ✓/✗ |
|-----|----------|---------------------|-----|
| 4.19 | Benachrichtigung erscheint | Grüne Box mittig oben, Text "Fortgesetzt bei Frage X von Y" |  |
| 4.20 | Animation | Benachrichtigung gleitet von oben rein |  |
| 4.21 | Auto-Hide | Benachrichtigung verschwindet nach 3 Sekunden mit Fade-Out |  |

---

## Allgemeine Tests

| Nr. | Testfall | Erwartetes Ergebnis | ✓/✗ |
|-----|----------|---------------------|-----|
| A.1 | Auto-Save funktioniert | Änderungen werden automatisch gespeichert (grüner Status) |  |
| A.2 | Dark Mode | Alle neuen UI-Elemente funktionieren im Dark Mode |  |
| A.3 | Responsive Design | Layout funktioniert auf verschiedenen Bildschirmgrößen |  |
| A.4 | Browser-Kompatibilität | Chrome, Firefox, Edge funktionieren |  |

---

## Notizen

| Datum | Tester | Bemerkungen |
|-------|--------|-------------|
|       |        |             |

---

## Commits dieser Session

- `d5e1a21` - EWH-Konfiguration: Meteostation-Sektion analog zu GWH umstrukturiert
- `b55361c` - Mindestens 1 Meteostation pro Projekt sicherstellen
- `1efd6cf` - EWH-Konfiguration: WHK-Block Styling an ZSK-Block angepasst
- `0e000ce` - Abnahmetest: Auto-Jump zur ersten unbeantworteten Frage
