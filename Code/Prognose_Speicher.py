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
    #=== Dataframe für die Jahre bis 2030 erstellen ===
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
    
    df_2030["Speicherkapazität [GWh]"] = speicher

    #df_2030.to_csv(PROJECT_ROOT / 'Daten' / 'speicherprognosetest.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

Prognose_Speicher_Ausbau(51, 160, 200)