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
    
    #((df_2030['Datum von'] - df_2030['Datum von'].min()).dt.days + 1)
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
    

    for key in kostendaten.keys():
        #=== Baukosten pro Viertelstunde berechnen ===
        if jährliche_raten["zuwachsrate_2030"][key] >= 0:
<<<<<<< HEAD
            baukosten_EE_2030 = 1e6 * jährliche_raten["zuwachsrate_2030"][key] * kostendaten[key]["capex"] / (virtelstunden_pro_jahr * 10)
        else:
            baukosten_EE_2030 = 0
        if jährliche_raten["zuwachsrate_2045"][key] >= 0:
            baukosten_EE_2045 = 1e6 * jährliche_raten["zuwachsrate_2045"][key] * kostendaten[key]["capex"] / (virtelstunden_pro_jahr * 15 )
        else:
            baukosten_EE_2045 = 0
=======
            baukosten_EE_virstellstündlich["2030"] = 1e6 * jährliche_raten["zuwachsrate_2030"][key] * kostendaten[key]["capex"] / virtelstunden_pro_jahr
        else:
            baukosten_EE_virstellstündlich["2030"] = 0
        if jährliche_raten["zuwachsrate_2045"][key] >= 0:
            baukosten_EE_virstellstündlich["2045"] = 1e6 * jährliche_raten["zuwachsrate_2045"][key] * kostendaten[key]["capex"] / virtelstunden_pro_jahr
        else:
            baukosten_EE_virstellstündlich["2045"] = 0
>>>>>>> 3c6a52cfbeec8fe12d7958b382ff8da1df267791

        baukosten_EE_2030 = round(baukosten_EE_2030, 2)
        baukosten_EE_2045 = round(baukosten_EE_2045, 2)

        
        mask1 = kosten_df["Jahr"] <= 2030 
        mask2 = kosten_df["Jahr"] > 2030
        
<<<<<<< HEAD
        kosten_df.loc[mask1, f"Capex {key} [€]"] = baukosten_EE_2030
        kosten_df.loc[mask2, f"Capex {key} [€]"] = baukosten_EE_2045
=======
        kosten_df.loc[mask1, f"Capex {key} [€]"] = baukosten_EE_virstellstündlich["2030"]
        kosten_df.loc[mask2, f"Capex {key} [€]"] = baukosten_EE_virstellstündlich["2045"]
>>>>>>> 3c6a52cfbeec8fe12d7958b382ff8da1df267791
                
        #=== OpEx Berechnung ===
        
        #=== Opex Bestand in df berechnen ===
        zuwachsraten = {"zuwachs_2030": {}, "zuwachs_2045": {}}
<<<<<<< HEAD
        
        zuwachsraten["zuwachs_2030"][key] = jährliche_raten["zuwachsrate_2030"][key] / 12
        zuwachsraten["zuwachs_2045"][key] = jährliche_raten["zuwachsrate_2045"][key] / 12
=======
        for key in jährliche_raten["zuwachsrate_2030"].keys():
            zuwachsraten["zuwachs_2030"][key] = jährliche_raten["zuwachsrate_2030"][key] / 12
            zuwachsraten["zuwachs_2045"][key] = jährliche_raten["zuwachsrate_2045"][key] / 12
>>>>>>> 3c6a52cfbeec8fe12d7958b382ff8da1df267791
        
        date_range = pd.date_range(start='01-01-2026 00:00', end='31-12-2045 23:45', freq='15min',tz='UTC')
        prognose = pd.DataFrame({'Datum von': date_range})
        
        prognose['Monat'] = prognose['Datum von'].dt.month
        prognose['Tag'] = prognose['Datum von'].dt.day
        prognose['Stunde'] = prognose['Datum von'].dt.hour
        prognose['Minute'] = prognose['Datum von'].dt.minute
        prognose['Jahr'] = prognose['Datum von'].dt.year

        maske_2030 = prognose["Jahr"] <= 2030
        maske_2045 = prognose["Jahr"] > 2030
        
        prognose.loc[maske_2030, f"Installierte {key}"] = kostendaten[key]["bestand"] + (zuwachsraten["zuwachs_2030"][key] * ((prognose.loc[maske_2030, "Jahr"] - 2026) * 12 + prognose.loc[maske_2030, "Monat"]))
        prognose.loc[maske_2045, f"Installierte {key}"] = kostendaten[key]["bestand"] + (zuwachsraten["zuwachs_2045"][key] * ((prognose.loc[maske_2045, "Jahr"] - 2031) * 12 + prognose.loc[maske_2045, "Monat"]))

<<<<<<< HEAD
        prognose[f"Opex {key} [€]"] = 1e6 * kostendaten[key]["opex"] * prognose[f"Installierte {key}"] / virtelstunden_pro_jahr
        prognose[f"Opex {key} [€]"] = prognose[f"Opex {key} [€]"].round(2)
        
        kosten_df = pd.merge(kosten_df, prognose[["Datum von", f"Opex {key} [€]"]], on="Datum von", how="left")

=======
        prognose[f"Opex {key} [€]"] = 1e6 * kostendaten[key]["opex"] * prognose[f"Installierte {key}"]

        kosten_df = pd.merge(kosten_df, prognose[["Datum von", f"Opex {key} [€]"]], on="Datum von", how="left")

>>>>>>> 3c6a52cfbeec8fe12d7958b382ff8da1df267791
        #=== Opex in kosten_df übernehmen ===
        kosten_df[f"Gesamtkosten {key} [€]"] = kosten_df[f"Capex {key} [€]"] + kosten_df[f"Opex {key} [€]"]
        spalten_kosten = [f"Capex {key} [€]", f"Opex {key} [€]", f"Gesamtkosten {key} [€]"]
        kosten_df[spalten_kosten] = kosten_df[spalten_kosten].round(2)

    kosten_df = kosten_df.drop(columns=["Monat", "Jahr"])

    kosten_df["Opex_EE [€]"] = kosten_df.filter(like="Opex").sum(axis=1).round(2)
    kosten_df["Capex_EE [€]"] = kosten_df.filter(like="Capex").sum(axis=1).round(2)
    kosten_df["Gesamtkosten_EE [€]"] = kosten_df.filter(like="Gesamtkosten").sum(axis=1).round(2)

   
    return kosten_df