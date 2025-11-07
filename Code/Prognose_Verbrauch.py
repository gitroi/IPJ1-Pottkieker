import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def Prognose_Verbrauch(verbrauch_2030_MWh , verbrauch_2045_MWh):
    
    #==== Einlesen der Daten und anpassung ====
    # Pfad relativ zum Skript bestimmen
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    verbrauchpfad = os.path.join(repo_root, "Daten", "verbrauch_2024.csv")

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
    verbrauch_df["Wochentag"] = verbrauch_df["Datum von"].dt.weekday
    verbrauch_df["Uhrzeit"] = verbrauch_df["Datum von"].dt.hour
    verbrauch_df["Minute"] = verbrauch_df["Datum von"].dt.minute
    verbrauch_df["Woche"] = verbrauch_df["Datum von"].dt.isocalendar().week

    #=== Gesamtverbrauch 2024 aus bestehenden Messungen berechnen ===

    gesamtverbrauch_2024 = verbrauch_df["Netzlast [MWh]"].sum().round(2)    

    #=== Wachstumsrate bis 2030 berechnen ===

    #ziel = start * (1+ r) ** n  => r = (ziel/start)^(1/n) -1

    wachstumsrate_2030 = ((verbrauch_2030_MWh/gesamtverbrauch_2024)**(1/6)) - 1

    #=== Dataframe für die Jahre bis 2030 erstellen ===

    date_range = pd.date_range(start='01-01-2026 00:00', end='31-12-2030 23:45', freq='15min')
    df_gesamt = pd.DataFrame({"Datum von": date_range})

    df_gesamt["Jahr"]= df_gesamt["Datum von"].dt.year
    df_gesamt["Monat"]= df_gesamt["Datum von"].dt.month
    df_gesamt["Wochentag"] = df_gesamt["Datum von"].dt.weekday
    df_gesamt["Uhrzeit"] = df_gesamt["Datum von"].dt.hour
    df_gesamt["Minute"] = df_gesamt["Datum von"].dt.minute
    df_gesamt["Woche"] = df_gesamt["Datum von"].dt.isocalendar().week

    df_gesamt = df_gesamt.merge(verbrauch_df, on=["Monat", "Wochentag", "Uhrzeit", "Minute","Woche"
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
    df_2045["Wochentag"] = df_2045["Datum von"].dt.weekday
    df_2045["Uhrzeit"] = df_2045["Datum von"].dt.hour
    df_2045["Minute"] = df_2045["Datum von"].dt.minute
    df_2045["Woche"] = df_2045["Datum von"].dt.isocalendar().week

    #===  wachstumsfaktor für 2031 bis 2045 berechnen ===

   
    gesamtverbrauch_2030_berechnet = df_gesamt[df_gesamt["Jahr"] == 2030]["Netzlast_Prognose [MWh]"].sum()

    wachstumsrate_2045 = (verbrauch_2045_MWh/gesamtverbrauch_2030_berechnet) **(1/15) - 1

    basisprofil_2030 = df_gesamt[df_gesamt["Jahr"] == 2030][["Jahr","Monat","Wochentag","Uhrzeit","Minute","Woche" ,"Netzlast_Prognose [MWh]"]].copy()

    profil_2030 = (basisprofil_2030.rename(columns={"Netzlast_Prognose [MWh]": "Profil [MWh]"})
    )

    profil_2030 = profil_2030.drop(columns=["Jahr"])

    prognose_2045 = df_2045.merge(profil_2030, on=["Monat", "Wochentag", "Uhrzeit", "Minute","Woche"
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
    # df_prognose_export.to_csv('C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\verbrauch_prognose_2045.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    return df_gesamt_2045