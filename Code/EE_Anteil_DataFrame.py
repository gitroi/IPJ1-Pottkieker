import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def anteil_erneuerbare_df(erzeugung: pd.DataFrame, verbrauch: pd.DataFrame, spaltenname_verbrauch: str) -> pd.DataFrame:
    """
    Analysiert den Anteil der Erneuerbaren Energien am Stromverbrauch
    basierend auf den Dataframes 'erzeugung' und 'verbrauch'.
    """
    # ==============================
    # 1. Datumsangaben konvertieren
    # ==============================

    erzeugung["Datum von"] = pd.to_datetime(erzeugung["Datum von"], format="%d.%m.%Y %H:%M")
    verbrauch["Datum von"] = pd.to_datetime(verbrauch["Datum von"], format="%d.%m.%Y %H:%M")

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