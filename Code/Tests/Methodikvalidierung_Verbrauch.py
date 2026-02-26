"""
Backtesting des Verbrauchsprognosemoduls.
Verlgeicht den Simulierten Verbrauch mit dem realen Verbrauch aus 2025
Programmiert von Joris Bürger 
"""

import sys
from pathlib import Path
import json

# Pfad zum Code-Ordner hinzufügen
code_path = Path(__file__).parent.parent
sys.path.insert(0, str(code_path))

import pandas as pd
import numpy as np
from config import PROJECT_ROOT

#=== Prognose Funktion für 2025 (Leicht abgewandelte Prognose Verbrauch Funktion) ====
def Prognose_Verbrauch_2025(verbrauch_2025: float ) -> pd.DataFrame:

    #=== Parameter in MWh umrechnen ===
    verbrauch_2025_MWh = verbrauch_2025 * 1e6

    #==== Einlesen der Daten und anpassung ====
    verbrauchpfad = PROJECT_ROOT / "Daten" /"SMARD-Daten"/ "verbrauch_2024.csv"

    verbrauch_df = pd.read_csv(verbrauchpfad,
    sep=';',low_memory=False)

    verbrauch_df["Datum von"] = pd.to_datetime(verbrauch_df["Datum von"], format="%d.%m.%Y %H:%M")
    verbrauch_df["Datum von"] = verbrauch_df["Datum von"].dt.tz_localize("Europe/Berlin", ambiguous='infer').dt.tz_convert('UTC')

    verbrauch_df = verbrauch_df[["Datum von", "Netzlast [MWh] Originalauflösungen"]]\
    .rename(columns={"Netzlast [MWh] Originalauflösungen": "Netzlast [MWh] origin"})

    verbrauch_df["Netzlast [MWh] origin"] = pd.to_numeric(
    verbrauch_df["Netzlast [MWh] origin"].astype(str)
    .str.replace('.', '',regex=False)
    .str.replace(',', '.',regex=False)
    .str.replace('-', '0', regex=False),
    errors='coerce'
    )

    verbrauch_df["Monat"]= verbrauch_df["Datum von"].dt.month
    verbrauch_df["Wochentag"] = verbrauch_df["Datum von"].dt.dayofweek
    verbrauch_df["Uhrzeit"] = verbrauch_df["Datum von"].dt.hour
    verbrauch_df["Minute"] = verbrauch_df["Datum von"].dt.minute

    #=== profil für 2024 erstellen ===

    basisprofil_2024 = verbrauch_df.groupby(["Monat", "Wochentag", "Uhrzeit", "Minute"])[["Netzlast [MWh] origin"]].mean().reset_index()

    # Erstelle DataFrame für 2024 um Gesamtverbrauch aus Basisprofil zu berechnen
    date_range_2024 = pd.date_range(start='01-01-2024 00:00', end='31-12-2024 23:45', freq='15min',tz='UTC')
    df_2024 = pd.DataFrame({"Datum von": date_range_2024})
    
    df_2024["Monat"]= df_2024["Datum von"].dt.month
    df_2024["Wochentag"] = df_2024["Datum von"].dt.dayofweek
    df_2024["Uhrzeit"] = df_2024["Datum von"].dt.hour
    df_2024["Minute"] = df_2024["Datum von"].dt.minute
    
    df_2024 = df_2024.merge(basisprofil_2024, on=["Monat", "Wochentag", "Uhrzeit", "Minute"], how='left')
    
    # Berechne Gesamtverbrauch aus Basisprofil (wie in Prognose_Verbrauch)
    gesamtverbrauch_2024 = df_2024["Netzlast [MWh] origin"].sum().round(2)

    #=== Wachstumsrate bis 2025 berechnen ===

    #ziel = wachstumsrate * jahr + startwert -> wachstumsrate = (ziel - startwert) / jahr
    wachstumsrate_2025 = (verbrauch_2025_MWh - gesamtverbrauch_2024) 

    #=== DataFrame für 2025 erstellen ===

    date_range = pd.date_range(start='01-01-2025 00:00', end='31-12-2025 23:45', freq='15min',tz='UTC')
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
    
    # Berechne Anzahl Viertelstunden pro Jahr (Schaltjahre berücksichtigen)
    df_gesamt["Viertelstunden_im_Jahr"] = np.where(
        (df_gesamt["Jahr"] % 4 == 0) & ((df_gesamt["Jahr"] % 100 != 0) | (df_gesamt["Jahr"] % 400 == 0)),
        366 * 96,
        365 * 96
    )

    df_gesamt["Netzlast_Prognose [MWh]"] = (
        df_gesamt["Netzlast [MWh] origin"] + 
        (wachstumsrate_2025 * (df_gesamt["Jahr"] - 2024)) / df_gesamt["Viertelstunden_im_Jahr"]
    )

    df_gesamt["Netzlast_Prognose [MWh]"] = df_gesamt["Netzlast_Prognose [MWh]"].round(2)
    
    df_gesamt = df_gesamt.rename(columns={"Netzlast_Prognose [MWh]": "Netzlast [MWh]"})

    df_gesamt = df_gesamt[["Datum von", "Netzlast [MWh]"]]
    df_gesamt = df_gesamt.sort_values(by="Datum von").reset_index(drop=True)

    #=== Rückgabe des DataFrames nur mit den relevanten Spalten ===
    if(df_gesamt.isna().any().any()):
        raise ValueError("Fehlende Werte in der Verbrauchsprognose entdeckt.")

    return df_gesamt

def backtesting_verbrauch():

    #==== Einlesen der Daten und anpassung ====
    verbrauchpfad = PROJECT_ROOT / "Daten" /"SMARD-Daten"/ "verbrauch_2025.csv"

    verbrauch_df = pd.read_csv(verbrauchpfad,
    sep=';',low_memory=False)

    verbrauch_df["Datum von"] = pd.to_datetime(verbrauch_df["Datum von"], format="%d.%m.%Y %H:%M")
    verbrauch_df["Datum von"] = verbrauch_df["Datum von"].dt.tz_localize("Europe/Berlin", ambiguous='infer').dt.tz_convert('UTC')

    verbrauch_df = verbrauch_df[["Datum von", "Netzlast [MWh] Originalauflösungen"]]\
    .rename(columns={"Netzlast [MWh] Originalauflösungen": "Netzlast [MWh] 2025"})

    verbrauch_df["Netzlast [MWh] 2025"] = pd.to_numeric(
    verbrauch_df["Netzlast [MWh] 2025"].astype(str)
    .str.replace('.', '',regex=False)
    .str.replace(',', '.',regex=False)
    .str.replace('-', '0', regex=False),
    errors='coerce'
    )

    verbrauch_df["Monat"]= verbrauch_df["Datum von"].dt.month
    verbrauch_df["Wochentag"] = verbrauch_df["Datum von"].dt.day
    verbrauch_df["Uhrzeit"] = verbrauch_df["Datum von"].dt.hour
    verbrauch_df["Minute"] = verbrauch_df["Datum von"].dt.minute
    verbrauch_df["Jahr"] = verbrauch_df["Datum von"].dt.year

    verbrauch_df = verbrauch_df[verbrauch_df["Jahr"]== 2025]
    gesamtverbrauch_2025 = verbrauch_df["Netzlast [MWh] 2025"].sum().round(2)  

    print(f"Gesamtverbrauch 2025 (real): {gesamtverbrauch_2025/1e6} TWH")

    #==== Verbrauchsprognose ====
    prognose_df = Prognose_Verbrauch_2025( round(gesamtverbrauch_2025/1e6,2))
    
    prognose_df["Monat"] = prognose_df["Datum von"].dt.month
    prognose_df["Wochentag"] = prognose_df["Datum von"].dt.day
    prognose_df["Uhrzeit"] = prognose_df["Datum von"].dt.hour
    prognose_df["Minute"] = prognose_df["Datum von"].dt.minute
    prognose_df["Jahr"] = prognose_df["Datum von"].dt.year

    prognose_df = prognose_df[prognose_df["Jahr"]==2025]
    prognose_df = prognose_df.rename(columns={"Netzlast [MWh]": "Netzlast [MWh] prognose"})
    prognose_df = prognose_df.drop(columns=["Datum von"])

    gesamtverbrauch_prognose_2025 = prognose_df["Netzlast [MWh] prognose"].sum().round(2)
    print(f"Gesamtverbrauch 2025 (Prognose): {gesamtverbrauch_prognose_2025/1e6} TWh")


    abweichung = gesamtverbrauch_prognose_2025 - gesamtverbrauch_2025
    prozent_abweichung = (abweichung / gesamtverbrauch_2025) * 100

    print(f"Abweichung: {abweichung/1e6} TWh")
    print(f"Prozentuale Abweichung: {prozent_abweichung:.2f}%")

    #==== Vergleich der Daten ====
    verleich_df = pd.merge(verbrauch_df, prognose_df,
    on=["Wochentag","Monat","Uhrzeit","Minute"],
    how="inner")

    vergleich_df = verleich_df[["Datum von","Netzlast [MWh] 2025","Netzlast [MWh] prognose"]].copy()
    vergleich_df["Relative Abweichung [MWh]"] = (vergleich_df["Netzlast [MWh] prognose"] - vergleich_df["Netzlast [MWh] 2025"]) / vergleich_df["Netzlast [MWh] 2025"] * 100

    print("Vergleich der Simulatiion mit realen Verbrauchsdaten:")
    print("Durchschnittliche relative Abweichung (%): ",
    vergleich_df["Relative Abweichung [MWh]"].mean().round(2))
    print("Maximale relative Abweichung (%): ",
    vergleich_df["Relative Abweichung [MWh]"].max().round(2))
    print("Minimale relative Abweichung (%): ",
    vergleich_df["Relative Abweichung [MWh]"].min().round(2))

    vergleich_df["RMSE"] = (vergleich_df["Netzlast [MWh] prognose"] - vergleich_df["Netzlast [MWh] 2025"])**2
    rmse = (vergleich_df["RMSE"].mean())**0.5
    mittlere_reale_energie = vergleich_df["Netzlast [MWh] 2025"].mean()
    normalized_rmse = rmse / mittlere_reale_energie * 100
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f} MWh")
    print(f"Normalized RMSE: {normalized_rmse:.2f}%")
    print(f"Es treten die folgenden Peak Energien auf: real: {vergleich_df['Netzlast [MWh] 2025'].max():.2f} MWh, prognose: {vergleich_df['Netzlast [MWh] prognose'].max():.2f} MWh")

    perzintile_95_real = vergleich_df['Netzlast [MWh] 2025'].quantile(0.95)
    perzintile_95_prognose = vergleich_df['Netzlast [MWh] prognose'].quantile(0.95)
    print(f"95. Perzentil der realen Verbrauchsdaten: {perzintile_95_real:.2f} MWh")
    print(f"95. Perzentil der prognostizierten Verbrauchsdaten: {perzintile_95_prognose:.2f} MWh")
    print(f"Abweichung im 95. Perzentil: {perzintile_95_prognose - perzintile_95_real:.2f} MWh")
    print(vergleich_df["Netzlast [MWh] 2025"].mean())

if __name__ == "__main__":
    backtesting_verbrauch()
