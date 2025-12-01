from Prognose_Erzeugung import Jährlicher_Zuwachs_EE
from config import DATA_DIR
# from Szenarien_auswahl import json_objekt_bearbeiten
import pandas as pd
import numpy as np
import json

def Kosten_EE(zieldaten: json)-> pd.DataFrame:
    """
    Berechnet die Kosten für den Ausbau der Erneuerbaren Energien basierend auf den Zielwerten für 2030 und 2045.
    
    Args:
        zielwerte_2030 (dict): Zielwerte für 2030 in GW.
        zielwerte_2045 (dict): Zielwerte für 2045 in GW.
        
    Returns:
        pd.DataFrame: DataFrame mit den jährlichen Ausbaukosten.
    """
    
    virtelstunden_pro_jahr = 365.25 * 24 * 4 

    #=== Einlesen der Kostendaten mit werten in €/KW ===
    kostendaten_pfad = DATA_DIR / "Feste_Parameter" / "erzeugerarten.json"
    with open(kostendaten_pfad, "r") as file:
        kostendaten = json.load(file)
    
    #=== DataFrame für die Kosten erstellen ===
    date_range = pd.date_range(start='01-01-2026', end='31-12-2045', freq='15min',tz='UTC') 
    kosten_df = pd.DataFrame({"Datum von": date_range})
    kosten_df["Jahr"] = kosten_df["Datum von"].dt.year
    kosten_df["Monat"]= kosten_df["Datum von"].dt.month
    kosten_df = kosten_df.drop_duplicates().reset_index(drop=True)
    
    #=== Capex Berechnung ===

    jährliche_raten = Jährlicher_Zuwachs_EE(zieldaten["Ziele 2030"]["Ausbau EE"], zieldaten["Ziele 2045"]["Ausbau EE"])
    baukosten_EE_virstellstündlich = {"2030": 0, "2045": 0}

    for key in kostendaten.keys():
        #=== Baukosten pro Viertelstunde berechnen ===
        baukosten_EE_virstellstündlich["2030"] = 1e6 * jährliche_raten["zuwachsrate_2030"][key] * kostendaten[key]["capex"] / virtelstunden_pro_jahr
        baukosten_EE_virstellstündlich["2045"] = 1e6 * jährliche_raten["zuwachsrate_2045"][key] * kostendaten[key]["capex"] / virtelstunden_pro_jahr

        baukosten_EE_virstellstündlich["2030"] = round(baukosten_EE_virstellstündlich["2030"], 2)
        baukosten_EE_virstellstündlich["2045"] = round(baukosten_EE_virstellstündlich["2045"], 2)

        for jahr in range(2026, 2046):
            mask = kosten_df["Jahr"] == jahr
            if jahr <= 2030:
                kosten_df.loc[mask, f"Capex {key} [€]"] = baukosten_EE_virstellstündlich["2030"]
            else:
                kosten_df.loc[mask, f"Capex {key} [€]"] = baukosten_EE_virstellstündlich["2045"]
                
        #=== OpEx Berechnung ===
        
        #=== Opex bestand 2025 pro Monat berechnen ===
        opex_bestand_2025_monatlich = kostendaten[key]["bestand"] * 1e6 * kostendaten[key]["opex"] / 12
        opex_bestand_2030_monatlich = zieldaten["Ziele 2030"]["Ausbau EE"][key] * 1e6 * kostendaten[key]["opex"] / 12

        #=== Opex zuname pro Monat berechnen === 
        monatliche_opex_zunahme_2026_2030 = jährliche_raten["zuwachsrate_2030"][key] * 1e6 * kostendaten[key]["opex"] / 12
        monatliche_opex_zunahme_2031_2045 = jährliche_raten["zuwachsrate_2045"][key] * 1e6 * kostendaten[key]["opex"] / 12

        #=== Opex pro Viertelstunde berechnen ===
        for jahr in range(2026, 2046):
            for monat in range(1, 13):
                mask = (kosten_df["Jahr"] == jahr) & (kosten_df["Monat"] == monat)
                if jahr <= 2030:
                    monate_seit_start = (jahr - 2026) * 12 + monat
                    kosten_df.loc[mask, f"Opex {key} [€]"] = (
                        opex_bestand_2025_monatlich + monatliche_opex_zunahme_2026_2030 * monate_seit_start
                ) / mask.sum()
                else:
                    monate_seit_start = (jahr - 2031) * 12 + monat
                    kosten_df.loc[mask, f"Opex {key} [€]"] = (
                        opex_bestand_2030_monatlich + monatliche_opex_zunahme_2031_2045 * monate_seit_start
                    ) / mask.sum()

        kosten_df[f"Gesamtkosten {key} [€]"] = kosten_df[f"Capex {key} [€]"] + kosten_df[f"Opex {key} [€]"]
        spalten_kosten = [f"Capex {key} [€]", f"Opex {key} [€]", f"Gesamtkosten {key} [€]"]
        kosten_df[spalten_kosten] = kosten_df[spalten_kosten].round(2)

    kosten_df = kosten_df.drop(columns=["Monat", "Jahr"])

    kosten_df["Opex_EE [€]"] = kosten_df.filter(like="Opex").sum(axis=1).round(2)
    kosten_df["Capex_EE [€]"] = kosten_df.filter(like="Capex").sum(axis=1).round(2)
    kosten_df["Gesamtkosten_EE [€]"] = kosten_df.filter(like="Gesamtkosten").sum(axis=1).round(2)
   
    return kosten_df