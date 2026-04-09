"""
Parameter-Definitionen für GWH-Komponenten.

Definiert die zu prüfenden Parameter für ZSK und HGLS.
Diese Parameter werden bei der Parameter-Prüfung (Inbetriebnahme) verwendet.
"""

# ZSK-Parameter (17 Parameter)
ZSK_PARAMETER = [
    {"name": "anstiegsdruck_maximal", "label": "Anstiegsdruck maximal", "einheit": "bar"},
    {"name": "druckanstiegsdifferenz", "label": "Druckanstiegsdifferenz", "einheit": "bar"},
    {"name": "druckanstiegszeit", "label": "Druckanstiegszeit", "einheit": "sec"},
    {"name": "druck_io_ein", "label": "Druck i.O. ein", "einheit": "bar"},
    {"name": "druck_io_aus", "label": "Druck i.O. aus", "einheit": "bar"},
    {"name": "druckaufbauzeit", "label": "Druckaufbauzeit", "einheit": "sec"},
    {"name": "druck_nach_io_zeit", "label": "Druck nach i.O. Zeit", "einheit": "sec"},
    {"name": "druck_nach_stop", "label": "Druck nach stop", "einheit": "bar"},
    {"name": "druck_nach_stop_zeit", "label": "Druck nach stop Zeit", "einheit": "sec"},
    {"name": "brennerrohr_aufbauzeit", "label": "Brennerrohr Aufbauzeit", "einheit": "min"},
    {"name": "brennerrohr_nach_io_zeit", "label": "Brennerrohr nach i.O. Zeit", "einheit": "min"},
    {"name": "schienentemp_einschaltpunkt", "label": "Schienentemperatur-Einschaltpunkt", "einheit": "°C"},
    {"name": "schienentemp_ausschaltpunkt", "label": "Schienentemperatur-Ausschaltpunkt", "einheit": "°C"},
    {"name": "test_druckhysterese", "label": "Test-Druckhysterese", "einheit": "bar"},
    {"name": "test_dauer", "label": "Test-Dauer", "einheit": "sec"},
    {"name": "test_abbruchzeit", "label": "Test-Abbruchzeit", "einheit": "min"},
    {"name": "notbetrieb_wartezeit", "label": "Notbetrieb Wartezeit", "einheit": "min"},
    {"name": "notbetrieb_einschaltpunkt", "label": "Notbetrieb Einschaltpunkt", "einheit": "°C"},
]

# HGLS-Parameter (22 Parameter)
HGLS_PARAMETER = [
    {"name": "druckanstiegszeit", "label": "Druckanstiegszeit", "einheit": "sec"},
    {"name": "fuellventilumschaltung", "label": "Füllventilumschaltung", "einheit": "bar"},
    {"name": "fuellventil_nachlaufzeit", "label": "Füllventil Nachlaufzeit", "einheit": "sec"},
    {"name": "gasfreigabezeit", "label": "Gasfreigabezeit", "einheit": "sec"},
    {"name": "druck_io_ein", "label": "Druck i.O. ein", "einheit": "bar"},
    {"name": "druck_io_aus", "label": "Druck i.O. aus", "einheit": "bar"},
    {"name": "druckaufbauzeit", "label": "Druckaufbauzeit", "einheit": "sec"},
    {"name": "druck_nach_io_zeit", "label": "Druck nach i.O. Zeit", "einheit": "sec"},
    {"name": "hauptventil_nachlaufzeit", "label": "Hauptventil Nachlaufzeit", "einheit": "sec"},
    {"name": "druck_im_stillstand", "label": "Druck im Stillstand", "einheit": "bar"},
    {"name": "stillstandzeit", "label": "Stillstandzeit", "einheit": "sec"},
    {"name": "toleranzwert_verbrauch", "label": "Toleranzwert Verbrauch", "einheit": "m³/h"},
    {"name": "leckzeit", "label": "Leckzeit", "einheit": "sec"},
    {"name": "bypassventil_ein", "label": "Bypassventil ein", "einheit": "bar"},
    {"name": "bypassventil_aus", "label": "Bypassventil aus", "einheit": "bar"},
    {"name": "notbetrieb_druckdifferenz", "label": "Notbetrieb Druckdifferenz", "einheit": "bar"},
    {"name": "notbetrieb_lecktestzeit", "label": "Notbetrieb Lecktestzeit", "einheit": "min"},
    {"name": "tankberieselung_ein", "label": "Tankberieselung ein", "einheit": "bar"},
    {"name": "tankberieselung_aus", "label": "Tankberieselung aus", "einheit": "bar"},
    {"name": "tankdruck_zu_hoch", "label": "Tankdruck zu hoch", "einheit": "bar"},
    {"name": "eingangsdruck_ein", "label": "Eingangsdruck ein", "einheit": "bar"},
    {"name": "eingangsdruck_aus", "label": "Eingangsdruck aus", "einheit": "bar"},
]
