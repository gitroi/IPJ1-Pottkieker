"""
Programm zur Analyse des Anteils der Erneuerbaren Energien am Stromverbrauch.
Nutzt SMARD-Daten aus CSV-Dateien und berechnet den Anteil der Erneuerbaren Energien.
Programmiert von Joris Bürger
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from config import DATA_DIR

def analyse_erneuerbare_anteil(pfaderzeugung, pfadverbrauch, spaltenname_verbrauch):
    """
    Analysiert den Anteil der Erneuerbaren Energien am Stromverbrauch
    basierend auf den CSV-Dateien 'erzeugung.csv' und 'verbrauch.csv'.
    Erstellt Visualisierungen und speichert die Ergebnisse in einer Excel-Datei.
    """
    # ==============================
    # 1. CSV-Dateien einlesen
    # ==============================

    erzeugung = pd.read_csv(pfaderzeugung, sep=";", low_memory=False)
    verbrauch = pd.read_csv(pfadverbrauch, sep=";", low_memory=False)

    # ==============================
    # 2. Datumsangaben konvertieren
    # ==============================

    erzeugung["Datum von"] = pd.to_datetime(erzeugung["Datum von"], format="%d.%m.%Y %H:%M")
    verbrauch["Datum von"] = pd.to_datetime(verbrauch["Datum von"], format="%d.%m.%Y %H:%M")

    # ==============================
    # 3. Anpassen der Datein (Entfernen von Leerzeichen in Spaltennamen etc.) 
    # ==============================

    for col in erzeugung.columns:
        if "MWh" in col:
            erzeugung[col] = (
                erzeugung[col]
                .astype(str)
                .str.replace("-", "0", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .astype(float)
    )

    for col in verbrauch.columns:
        if "MWh" in col:
            verbrauch[col] = (
                verbrauch[col]
                .astype(str)
                .str.replace("-", "0", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .astype(float)
        )

    # ==============================
    # 4. Erneuerbare Energien zusammenfassen
    # ==============================

    erneuerbare_cols = [
    "Biomasse [MWh] Originalauflösungen",
    "Wasserkraft [MWh] Originalauflösungen",
    "Wind Offshore [MWh] Originalauflösungen",
    "Wind Onshore [MWh] Originalauflösungen",
    "Photovoltaik [MWh] Originalauflösungen",
    "Sonstige Erneuerbare [MWh] Originalauflösungen",
    ]

    erzeugung["Erneuerbare [MWh]"] = erzeugung[erneuerbare_cols].sum(axis=1)
    # ==============================
    # 5. verbrauch und erzeugung zusammenführen und anteile berechnen
    # ==============================

    gesamt = pd.merge(
    erzeugung[["Datum von","Biomasse [MWh] Originalauflösungen",
        "Wasserkraft [MWh] Originalauflösungen",
        "Wind Offshore [MWh] Originalauflösungen",
        "Wind Onshore [MWh] Originalauflösungen",
        "Photovoltaik [MWh] Originalauflösungen",
        "Sonstige Erneuerbare [MWh] Originalauflösungen",
        "Erneuerbare [MWh]"]],
    verbrauch[["Datum von",  spaltenname_verbrauch]],
    on="Datum von",
    how="inner",
    )

    # sichere Division: ersetze 0 durch np.nan vor Division
    den = gesamt[ spaltenname_verbrauch].replace(0, np.nan)
    gesamt["Anteil Erneuerbare [MWh]"] = (gesamt["Erneuerbare [MWh]"] / den * 100).round(2)

    return gesamt

ergebniss = analyse_erneuerbare_anteil(
    pfaderzeugung=f"{DATA_DIR}\Ist_Analyse\Erzeugung.csv",
    pfadverbrauch=f"{DATA_DIR}\Ist_Analyse\Verbrauch.csv",
    spaltenname_verbrauch="Netzlast [MWh] Originalauflösungen",
)

print(ergebniss["Anteil Erneuerbare [MWh]"].mean())
