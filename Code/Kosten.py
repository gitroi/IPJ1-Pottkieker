from Erzeugungsprognosen import Jährlicher_Zuwachs_EE
from config import DATA_DIR
from Feste_Variablen import map_ausbaustand_EE_GW, map_wirkungsgrade
import pandas as pd
import numpy as np
import json

def Kosten_Ausbau(zielwerte_2030:dict, zielwerte_2045:dict)-> pd.DataFrame:
    """
    Berechnet die Kosten für den Ausbau der Erneuerbaren Energien basierend auf den Zielwerten für 2030 und 2045.
    
    Args:
        zielwerte_2030 (dict): Zielwerte für 2030 in GW.
        zielwerte_2045 (dict): Zielwerte für 2045 in GW.
        
    Returns:
        pd.DataFrame: DataFrame mit den jährlichen Ausbaukosten.
    """
    
    # Einlesen der Kostendaten
    kostendaten_pfad = DATA_DIR / "Feste_Parameter" / "Kosten_EE.json"
    with open(kostendaten_pfad, "r") as file:
        kostendaten = json.load(file)
    
    date_range = pd.date_range(start='01-01-2026', end='31-12-2045', freq='15min') 
    kosten_df = pd.DataFrame({"Datum": date_range})
    kosten_df["Jahr"] = kosten_df["Datum"].dt.year
    kosten_df = kosten_df.drop(columns=["Datum"]).drop_duplicates().reset_index(drop=True)

    
    jährliche_raten = Jährlicher_Zuwachs_EE(zielwerte_2030, zielwerte_2045)
    baukosten_EE_virstellstündlich = {"2030": 0, "2045": 0}
    for key in kostendaten["baukosten"].keys():
        baukosten_EE_virstellstündlich["2030"] += 1e6 * jährliche_raten["zuwachsrate_2030"][key] * kostendaten["baukosten"][key] / (365.25 * 24 * 4)
        baukosten_EE_virstellstündlich["2045"] += 1e6 * jährliche_raten["zuwachsrate_2045"][key] * kostendaten["baukosten"][key] / (365.25 * 24 * 4)

    baukosten_EE_virstellstündlich["2030"] = round(baukosten_EE_virstellstündlich["2030"], 2)
    baukosten_EE_virstellstündlich["2045"] = round(baukosten_EE_virstellstündlich["2045"], 2)

    for jahr in range(2026, 2046):
        mask = kosten_df["Jahr"] == jahr
        if jahr <= 2030:
            kosten_df.loc[mask, "Baukosten_EE [€]"] = baukosten_EE_virstellstündlich["2030"]
        else:
            kosten_df.loc[mask, "Baukosten_EE [€]"] = baukosten_EE_virstellstündlich["2045"]
            
