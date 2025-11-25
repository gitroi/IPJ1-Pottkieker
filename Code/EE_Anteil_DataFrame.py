import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import config

def anteil_erneuerbare_df(erzeugung: pd.DataFrame, verbrauch: pd.DataFrame) -> pd.DataFrame:
    """
    Analysiert den Anteil der Erneuerbaren Energien am Stromverbrauch
    basierend auf den Dataframes 'erzeugung' und 'verbrauch'.
    Args:
        erzeugung (pd.DataFrame): DataFrame mit Erzeugungsdaten
        verbrauch (pd.DataFrame): DataFrame mit Verbrauchsdaten
        spaltenname_verbrauch (str): Name der Spalte im Verbrauchs-DataFrame, die den Verbrauch in MWh enthält
    Returns:
        pd.DataFrame: DataFrame mit dem Anteil der Erneuerbaren Energien am Stromverbrauch
    Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
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
    verbrauch[["Datum von",  "Netzlast [MWh]"]],
    on="Datum von",
    how="inner",
    )
    
    gesamt = gesamt.drop_duplicates(subset=["Datum von","Netzlast [MWh]"]).reset_index(drop=True)

    # sichere Division: ersetze 0 durch np.nan vor Division
    den = gesamt["Netzlast [MWh]"].replace(0, np.nan)
    gesamt["Anteil Erneuerbare [%]"] = (gesamt["Erneuerbare [MWh]"] / den * 100).round(2)

    return gesamt

# def anteil_erneuerbare_Jahrx_df(erzeugung: pd.DataFrame, verbrauch: pd.DataFrame, spaltenname_verbrauch: str, jahr: int):
#     """
#     Analysiert den Anteil der Erneuerbaren Energien am Stromverbrauch
#     basierend auf den Dataframes 'erzeugung' und 'verbrauch'.
#     Args:
#         erzeugung (pd.DataFrame): DataFrame mit Erzeugungsdaten
#         verbrauch (pd.DataFrame): DataFrame mit Verbrauchsdaten
#         spaltenname_verbrauch (str): Name der Spalte im Verbrauchs-DataFrame, die den Verbrauch in MWh enthält
#         jahr (int): Jahr, für das die Analyse durchgeführt werden soll
#     Returns:
#         pd.DataFrame: DataFrame mit dem Anteil der Erneuerbaren Energien am Stromverbrauch
#     Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
#     """
#     # ==============================
#     # 1. Datumsangaben konvertieren
#     # ==============================

#     erzeugung = erzeugung.copy()
#     verbrauch = verbrauch.copy()

#     erzeugung["Datum von"] = pd.to_datetime(erzeugung["Datum von"], format="%d.%m.%Y %H:%M")
#     verbrauch["Datum von"] = pd.to_datetime(verbrauch["Datum von"], format="%d.%m.%Y %H:%M")

#     erzeugung["Jahr"] = erzeugung["Datum von"].dt.year
#     verbrauch["Jahr"] = verbrauch["Datum von"].dt.year

#     erzeugung = erzeugung[erzeugung["Jahr"] == jahr]
#     verbrauch = verbrauch[verbrauch["Jahr"] == jahr]

#     # ==============================
#     # 4. Erneuerbare Energien zusammenfassen
#     # ==============================

#     erneuerbare_cols = [
#     "Biomasse [MWh] Originalauflösungen",
#     "Wasserkraft [MWh] Originalauflösungen",
#     "Wind Offshore [MWh] Originalauflösungen",
#     "Wind Onshore [MWh] Originalauflösungen",
#     "Photovoltaik [MWh] Originalauflösungen",
#     "Sonstige Erneuerbare [MWh] Originalauflösungen",
#     ]

#     erzeugung["Erneuerbare [MWh]"] = erzeugung[erneuerbare_cols].sum(axis=1)

#     # ==============================
#     # 5. verbrauch und erzeugung zusammenführen und anteile berechnen
#     # ==============================

#     gesamt = pd.merge(
#     erzeugung[["Datum von","Biomasse [MWh] Originalauflösungen",
#         "Wasserkraft [MWh] Originalauflösungen",
#         "Wind Offshore [MWh] Originalauflösungen",
#         "Wind Onshore [MWh] Originalauflösungen",
#         "Photovoltaik [MWh] Originalauflösungen",
#         "Sonstige Erneuerbare [MWh] Originalauflösungen",
#         "Erneuerbare [MWh]"]],
#     verbrauch[["Datum von",  "Netzlast [MWh] Originalauflösungen"]],
#     on="Datum von",
#     how="inner",
#     )

#     # sichere Division: ersetze 0 durch np.nan vor Division
#     den = gesamt["Netzlast [MWh] Originalauflösungen"].replace(0, np.nan)
#     gesamt["Anteil Erneuerbare [%]"] = (gesamt["Erneuerbare [MWh]"] / den * 100).round(2)

#     return gesamt