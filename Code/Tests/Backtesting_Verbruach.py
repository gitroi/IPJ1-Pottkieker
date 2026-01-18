"""
Backtesting des Verbrauchsprognosemoduls.
Verlgeicht den Simulierten Verbrauch mit dem realen Verbrauch aus 2025
"""

import sys
from pathlib import Path
import json

# Pfad zum Code-Ordner hinzufügen
code_path = Path(__file__).parent.parent
sys.path.insert(0, str(code_path))

import pandas as pd
from Prognose_Verbrauch import Prognose_Verbrauch
from config import PROJECT_ROOT

def backtesting_verbrauch():

    #==== Einlesen der Daten und anpassung ====
    verbrauchpfad = PROJECT_ROOT / "Daten" /"SMARD-Daten"/ "verbrauch_2025.csv"

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

    gesamtverbrauch_2024 = verbrauch_df["Netzlast [MWh] origin"].sum().round(2)  