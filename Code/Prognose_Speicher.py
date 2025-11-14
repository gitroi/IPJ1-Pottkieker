"""
Zentrales Programm der Prognose vom Stromspeicher.
Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
"""
import pandas as pd
import numpy as np
from config import PROJECT_ROOT

def Prognose_Speicher_Ausbau(bestand2025, bestand2030, bestand2045):
    """
    Berechnet den Verlauf des Speicherausbaus einer Speicherart
    Ünterstützt durch KI (Claude Sonnet 4.5)
    """

    #=== Kapazitäten in MWh umrechnen ===
    bestand2025 = bestand2025 * 1e3
    bestand2030 = bestand2030 * 1e3
    bestand2045 = bestand2045 * 1e3

    #=== Dataframe für die Jahre 2026 bis 2030 erstellen ===
    date_range = pd.date_range(start='2026-01-01', end='2030-12-31 23:45', freq='15min')
    df_2030 = pd.DataFrame({'Datum': date_range})

    df_2030["Jahr"] = df_2030["Datum"].dt.year
    df_2030["Monat"]= df_2030["Datum"].dt.month
    df_2030["Wochentag"] = df_2030["Datum"].dt.dayofweek
    df_2030["Uhrzeit"] = df_2030["Datum"].dt.hour
    df_2030["Minute"] = df_2030["Datum"].dt.minute

    anzahl_viertelstunden_2030 = len(df_2030["Datum"].unique())
    
    wachstumsrate_2030 = (bestand2030 - bestand2025) / anzahl_viertelstunden_2030

    speicher = []
    for i in range(anzahl_viertelstunden_2030):
        speicher.append(bestand2025 + wachstumsrate_2030 * (i+1))
    
    df_2030["Speicherkapazität [MWh]"] = speicher

    #df_2030.to_csv(PROJECT_ROOT / 'Daten' / 'speicherprognosetest2030.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    #=== Dataframe für die Jahre 2030 bis 2045 erstellen ===
    date_range = pd.date_range(start='2031-01-01', end='2045-12-31 23:45', freq='15min')
    df_2045 = pd.DataFrame({'Datum': date_range})

    df_2045["Jahr"] = df_2045["Datum"].dt.year
    df_2045["Monat"]= df_2045["Datum"].dt.month
    df_2045["Wochentag"] = df_2045["Datum"].dt.dayofweek
    df_2045["Uhrzeit"] = df_2045["Datum"].dt.hour
    df_2045["Minute"] = df_2045["Datum"].dt.minute

    anzahl_viertelstunden_2045 = len(df_2045["Datum"].unique())
    
    wachstumsrate_2045 = (bestand2045 - bestand2030) / anzahl_viertelstunden_2045
    
    speicher = []
    for i in range(anzahl_viertelstunden_2045):
        speicher.append(bestand2030 + wachstumsrate_2045 * (i+1))
    
    df_2045["Speicherkapazität [MWh]"] = speicher

    df_gesamt = pd.concat([df_2030, df_2045], ignore_index=True)
    df_gesamt["Speicherkapazität [MWh]"] = df_gesamt["Speicherkapazität [MWh]"].round(2)

    #df_gesamt.to_csv(PROJECT_ROOT / 'Daten' / 'speicherprognosetestgesamt.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

Prognose_Speicher_Ausbau(51, 160, 400)