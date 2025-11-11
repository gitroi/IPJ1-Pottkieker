"""
Zentrales Programm der Prognose von dem Verbrauch der Gruppe Pottkieker.
Nutzt Daten aus 2024 um eine Prognose bis 2045 zu erstellen.
Ünterstützt durch KI (Claude Sonnet 4.5)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from config import PROJECT_ROOT 

def Prognose_Verbrauch(verbrauch_2030_TWh , verbrauch_2045_TWh):
    
    #=== Parameter in MWh umrechnen ===
    verbrauch_2030_MWh = verbrauch_2030_TWh * 1e6
    verbrauch_2045_MWh = verbrauch_2045_TWh * 1e6

    #==== Einlesen der Daten und anpassung ====
    # Pfad relativ zum Skript bestimmen
    verbrauchpfad = PROJECT_ROOT / "Daten" /"SMARD-Daten"/ "verbrauch_2024.csv"

    verbrauch_df = pd.read_csv(verbrauchpfad,
    sep=';', low_memory=False)

    verbrauch_df["Datum von"] = pd.to_datetime(verbrauch_df["Datum von"], format="%d.%m.%Y %H:%M")

    verbrauch_df = verbrauch_df[["Datum von", "Netzlast [MWh] Originalauflösungen"]]\
    .rename(columns={"Netzlast [MWh] Originalauflösungen": "Netzlast [MWh]"})

    verbrauch_df["Netzlast [MWh]"] = pd.to_numeric(
    verbrauch_df["Netzlast [MWh]"].astype(str)
    .str.replace('.', '',regex=False)
    .str.replace(',', '.',regex=False)
    .str.replace('-', '0', regex=False),
    errors='coerce'
    )

    verbrauch_df["Monat"]= verbrauch_df["Datum von"].dt.month
    verbrauch_df["Wochentag"] = verbrauch_df["Datum von"].dt.dayofweek
    verbrauch_df["Uhrzeit"] = verbrauch_df["Datum von"].dt.hour
    verbrauch_df["Minute"] = verbrauch_df["Datum von"].dt.minute

    #=== Gesamtverbrauch 2024 aus bestehenden Messungen berechnen ===

    gesamtverbrauch_2024 = verbrauch_df["Netzlast [MWh]"].sum().round(2)    

    #=== Wachstumsrate bis 2030 berechnen ===

    #ziel = start * (1+ r) ** n  => r = (ziel/start)^(1/n) -1
    wachstumsrate_2030 = ((verbrauch_2030_MWh/gesamtverbrauch_2024)**(1/6)) - 1

    #=== profil für 2024 erstellen ===

    basisprofil_2024 = verbrauch_df.groupby(["Monat", "Wochentag", "Uhrzeit", "Minute"])[["Netzlast [MWh]"]].mean().reset_index()

    #=== Dataframe für die Jahre bis 2030 erstellen ===

    date_range = pd.date_range(start='01-01-2026 00:00', end='31-12-2030 23:45', freq='15min')
    df_gesamt = pd.DataFrame({"Datum von": date_range})

    df_gesamt["Jahr"]= df_gesamt["Datum von"].dt.year
    df_gesamt["Monat"]= df_gesamt["Datum von"].dt.month
    df_gesamt["Wochentag"] = df_gesamt["Datum von"].dt.dayofweek
    df_gesamt["Uhrzeit"] = df_gesamt["Datum von"].dt.hour
    df_gesamt["Minute"] = df_gesamt["Datum von"].dt.minute

    df_gesamt = df_gesamt.merge(basisprofil_2024, on=["Monat", "Wochentag", "Uhrzeit", "Minute"
        ], how='left'
    )

    #=== Verbrauchsprognose berechnen ===

    df_gesamt["Netzlast_Prognose [MWh]"] = (
        df_gesamt["Netzlast [MWh]"]
        * (1 + wachstumsrate_2030) ** (df_gesamt["Jahr"] - 2024) 
    )

    df_gesamt["Netzlast_Prognose [MWh]"] = df_gesamt["Netzlast_Prognose [MWh]"].round(2)

    #=== Erweitern bis 2045 ===

    date_range_2045 = pd.date_range(start='01-01-2031 00:00', end='31-12-2045 23:45', freq='15min')
    df_2045 = pd.DataFrame({"Datum von": date_range_2045})

    df_2045["Jahr"]= df_2045["Datum von"].dt.year
    df_2045["Monat"]= df_2045["Datum von"].dt.month
    df_2045["Wochentag"] = df_2045["Datum von"].dt.dayofweek    
    df_2045["Uhrzeit"] = df_2045["Datum von"].dt.hour
    df_2045["Minute"] = df_2045["Datum von"].dt.minute

    #===  wachstumsfaktor für 2031 bis 2045 berechnen ===

   
    gesamtverbrauch_2030_berechnet = df_gesamt[df_gesamt["Jahr"] == 2030]["Netzlast_Prognose [MWh]"].sum()

    wachstumsrate_2045 = (verbrauch_2045_MWh/gesamtverbrauch_2030_berechnet) **(1/15) - 1

    basisprofil_2030 = df_gesamt[df_gesamt["Jahr"] == 2030][["Jahr","Monat","Wochentag","Uhrzeit","Minute" ,"Netzlast_Prognose [MWh]"]].copy()

    profil_2030 = (basisprofil_2030.groupby(["Monat","Wochentag","Uhrzeit","Minute"]).mean().reset_index().rename(columns={"Netzlast_Prognose [MWh]": "Profil [MWh]"})
    )

    profil_2030 = profil_2030.drop(columns=["Jahr","Datum von"], errors='ignore')

    prognose_2045 = df_2045.merge(profil_2030, on=["Monat", "Wochentag", "Uhrzeit", "Minute"
        ], how='left'
    )

    prognose_2045["Netzlast_Prognose [MWh]"] = (
        prognose_2045["Profil [MWh]"]
        * (1 + wachstumsrate_2045) ** (prognose_2045["Jahr"] - 2030)
    )

    prognose_2045["Netzlast_Prognose [MWh]"] = prognose_2045["Netzlast_Prognose [MWh]"].round(2)

    df_gesamt_2045 = pd.concat([df_gesamt, prognose_2045], ignore_index=True)
    df_gesamt_2045 = df_gesamt_2045.rename(columns={"Netzlast_Prognose [MWh]": "Netzlast [MWh] Originalauflösungen"})

    # #speichern
    # df_prognose_export = df_gesamt_2045[["Datum von", "Netzlast [MWh] Originalauflösungen"]]
    # df_prognose_export.to_csv(PROJECT_ROOT / 'Daten' / 'verbrauch_prognose_2045.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    #=== Rückgabe des DataFrames nur mit den relevanten Spalten ===
    df_gesamt_2045 = df_gesamt_2045[["Datum von", "Netzlast [MWh] Originalauflösungen"]]
    df_gesamt_2045 = df_gesamt_2045[~((df_gesamt_2045["Datum von"].dt.month == 2) & (df_gesamt_2045["Datum von"].dt.day == 29))]

    return df_gesamt_2045