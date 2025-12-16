"""
Programmiert von Joris Bürger
"""

from Prognose_Speicher import Prognose_Gesamt_Ausbau_
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

    capex_wachstum = zieldaten["Veränderungsfaktoren"]["Capex_EE"]
    opex_wachstum = zieldaten["Veränderungsfaktoren"]["Opex_EE"]

    virtelstunden_capex = {}
    virtelstunden_opex = {}
    for key in capex_wachstum.keys():
        virtelstunden_capex[key] = capex_wachstum[key] ** (1 / virtelstunden_pro_jahr)
        virtelstunden_opex[key] = opex_wachstum[key] ** (1 / virtelstunden_pro_jahr)

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
            baukosten_EE_2030 = 1e6 * jährliche_raten["zuwachsrate_2030"][key] * kostendaten[key]["capex"] / (virtelstunden_pro_jahr )
        else:
            baukosten_EE_2030 = 0
        if jährliche_raten["zuwachsrate_2045"][key] >= 0:
            baukosten_EE_2045 = 1e6 * jährliche_raten["zuwachsrate_2045"][key] * kostendaten[key]["capex"] / (virtelstunden_pro_jahr )
        else:
            baukosten_EE_2045 = 0

        baukosten_EE_2030 = round(baukosten_EE_2030, 2)
        baukosten_EE_2045 = round(baukosten_EE_2045, 2)

        
        mask1 = kosten_df["Jahr"] <= 2030 
        mask2 = kosten_df["Jahr"] > 2030
        
        kosten_df.loc[mask1, f"Capex {key} [€]"] = baukosten_EE_2030
        kosten_df.loc[mask2, f"Capex {key} [€]"] = baukosten_EE_2045
                
        #=== OpEx Berechnung ===
        
        #=== Opex Bestand in df berechnen ===
        zuwachsraten = {"zuwachs_2030": {}, "zuwachs_2045": {}}
        
        zuwachsraten["zuwachs_2030"][key] = jährliche_raten["zuwachsrate_2030"][key] / 12
        zuwachsraten["zuwachs_2045"][key] = jährliche_raten["zuwachsrate_2045"][key] / 12
        
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
        prognose.loc[maske_2045, f"Installierte {key}"] = zieldaten["Ziele 2030"]["Ausbau EE"][key]+ (zuwachsraten["zuwachs_2045"][key] * ((prognose.loc[maske_2045, "Jahr"] - 2031) * 12 + prognose.loc[maske_2045, "Monat"]))

        prognose[f"Opex {key} [€]"] = 1e6 * kostendaten[key]["opex"] * prognose[f"Installierte {key}"] / virtelstunden_pro_jahr
        
        prognose[f"Opex {key} [€]"] = prognose[f"Opex {key} [€]"] * (virtelstunden_opex[key] ** (prognose['Jahr'] - 2026))
        prognose[f"Capex {key} [€]"] = kosten_df[f"Capex {key} [€]"] * (virtelstunden_capex[key] ** (prognose['Jahr'] - 2026))
        prognose[f"Opex {key} [€]"] = prognose[f"Opex {key} [€]"].round(2)
        prognose[f"Capex {key} [€]"] = prognose[f"Capex {key} [€]"].round(2)
    
        kosten_df = pd.merge(kosten_df, prognose[["Datum von", f"Opex {key} [€]"]], on="Datum von", how="left")

        #=== Opex in kosten_df übernehmen ===
        kosten_df[f"Gesamtkosten {key} [€]"] = kosten_df[f"Capex {key} [€]"] + kosten_df[f"Opex {key} [€]"]
        spalten_kosten = [f"Capex {key} [€]", f"Opex {key} [€]", f"Gesamtkosten {key} [€]"]
        kosten_df[spalten_kosten] = kosten_df[spalten_kosten].round(2)

    kosten_df = kosten_df.drop(columns=["Monat", "Jahr"])

    kosten_df["Opex_EE [€]"] = kosten_df.filter(like="Opex").sum(axis=1).round(2)
    kosten_df["Capex_EE [€]"] = kosten_df.filter(like="Capex").sum(axis=1).round(2)
    kosten_df["Gesamtkosten_EE [€]"] = kosten_df.filter(like="Gesamtkosten").sum(axis=1).round(2)

   
    return kosten_df

def kosten_speicher(szenario: json) -> pd.DataFrame:
    """
    Berechnet die Kosten für Speicher basierend auf dem Szenario.
    
    Args:
        szenario (json): Das Szenario mit den Speicherzielen und Veränderungsfaktoren.
        
    Returns:
        pd.DataFrame: DataFrame mit den jährlichen Speicherkosten.
    """
    
    virtelstunden_pro_jahr = 365.25 * 24 * 4
    ausbau_2030_GW = szenario["Ziele 2030"]["Ausbau Speicher"]
    ausbau_2045_GW = szenario["Ziele 2045"]["Ausbau Speicher"]

    #=== Einlesen der Kostendaten mit werten in €/KW bzw. €/KWh ===
    kostendaten_pfad = DATA_DIR / "Feste_Parameter" / "speicherarten.json"
    with open(kostendaten_pfad, "r") as file:
        kostendaten = json.load(file)

    date_range = pd.date_range(start='01-01-2026', end='31-12-2045', freq='15min',tz='UTC') 
    kosten_df = pd.DataFrame({"Datum von": date_range})

    kosten_df["Jahr"] = kosten_df["Datum von"].dt.year
    kosten_df["Monat"]= kosten_df["Datum von"].dt.month
    kosten_df = kosten_df.drop_duplicates().reset_index(drop=True)

    capex_wachstum  = szenario["Veränderungsfaktoren"]["Capex_Speicher"]
    opex_wachstum = szenario["Veränderungsfaktoren"]["Opex_Speicher"]

    virtelstunden_capex = {}
    virtelstunden_opex = {}

    for key in capex_wachstum.keys():
        virtelstunden_capex[key] = capex_wachstum[key] ** (1 / virtelstunden_pro_jahr)
        virtelstunden_opex[key] = opex_wachstum[key] ** (1 / virtelstunden_pro_jahr)

    for key in kostendaten.keys():
        mask1 = kosten_df["Jahr"] <= 2030 
        mask2 = kosten_df["Jahr"] > 2030
        kosten_df.loc[mask1,f"Ausbaurate {key}"] = (ausbau_2030_GW[key]-kostendaten[key]["bestand"])  / len(kosten_df[mask1])
        kosten_df.loc[mask2,f"Ausbaurate {key}"] = (ausbau_2045_GW[key]-ausbau_2030_GW[key])  / len(kosten_df[mask2])
        mask3 = kosten_df[f"Ausbaurate {key}"] > 0
        kosten_df.loc[mask3,f"Capex {key} [€]"] = 1e6 * kosten_df[f"Ausbaurate {key}"] * kostendaten[key]["capex"] 
        kosten_df.loc[~mask3,f"Capex {key} [€]"] = 0
        kosten_df[f"Capex {key} [€]"] = kosten_df[f"Capex {key} [€]"] * (virtelstunden_capex[key] ** (kosten_df['Jahr'] - 2025))
        kosten_df[f"Capex {key} [€]"] = kosten_df[f"Capex {key} [€]"].round(2)

    #=== OpEx Berechnung ===
    installierte_speicher = Prognose_Gesamt_Ausbau_(kostendaten["batteriespeicher"]["bestand"], kostendaten["wasserstoff"]["bestand"],kostendaten["pumpspeicher"]["bestand"], ausbau_2030_GW["batteriespeicher"], ausbau_2045_GW["batteriespeicher"], ausbau_2030_GW["wasserstoff"], ausbau_2045_GW["wasserstoff"], ausbau_2030_GW["pumpspeicher"], ausbau_2045_GW["pumpspeicher"])
    kosten_df = pd.merge(kosten_df, installierte_speicher, on="Datum von", how="left")

    for key in kostendaten.keys():
        kosten_df[f"Opex {key} [€]"] = 1e3 * kostendaten[key]["opex"] * kosten_df[f"Speicherkapazität {key} [MWh]"] * kostendaten[key]["leistung"] / virtelstunden_pro_jahr
        kosten_df[f"Opex {key} [€]"] = kosten_df[f"Opex {key} [€]"] * (virtelstunden_opex[key] ** (kosten_df['Jahr'] - 2025))
        kosten_df[f"Opex {key} [€]"] = kosten_df[f"Opex {key} [€]"].round(2)

        kosten_df[f"Gesamtkosten {key} [€]"] = kosten_df[f"Capex {key} [€]"] + kosten_df[f"Opex {key} [€]"]
        spalten_kosten = [f"Capex {key} [€]", f"Opex {key} [€]", f"Gesamtkosten {key} [€]"]
        kosten_df[spalten_kosten] = kosten_df[spalten_kosten].round(2)

    kosten_df = kosten_df[["Datum von", "Opex batteriespeicher [€]", "Capex batteriespeicher [€]", "Gesamtkosten batteriespeicher [€]",
                          "Opex wasserstoff [€]", "Capex wasserstoff [€]", "Gesamtkosten wasserstoff [€]",
                          "Opex pumpspeicher [€]", "Capex pumpspeicher [€]", "Gesamtkosten pumpspeicher [€]"]]
    kosten_df["Opex_Speicher [€]"] = kosten_df[["Opex batteriespeicher [€]", "Opex wasserstoff [€]", "Opex pumpspeicher [€]"]].sum(axis=1).round(2)
    kosten_df["Capex_Speicher [€]"] = kosten_df[["Capex batteriespeicher [€]", "Capex wasserstoff [€]", "Capex pumpspeicher [€]"]].sum(axis=1).round(2)
    kosten_df["Gesamtkosten_Speicher [€]"] = kosten_df[["Gesamtkosten batteriespeicher [€]", "Gesamtkosten wasserstoff [€]", "Gesamtkosten pumpspeicher [€]"]].sum(axis=1).round(2)
    return kosten_df
    
def kostenrechnung(szenario: json) -> pd.DataFrame:
    """
    Berechnet die Gesamtkosten für Erneuerbare Energien und Speicher basierend auf dem Szenario.
    
    Args:
        szenario (json): Das Szenario mit den Zielwerten und Veränderungsfaktoren.
        
    Returns:
        pd.DataFrame: DataFrame mit den jährlichen Gesamtkosten.
    """
    kosten_ee_df = Kosten_EE(szenario)
    kosten_speicher_df = kosten_speicher(szenario)

    gesamt_kosten_df = pd.merge(kosten_ee_df, kosten_speicher_df, on="Datum von", how="inner")

    gesamt_kosten_df["Gesamtkosten_EE_und_Speicher [€]"] = gesamt_kosten_df["Gesamtkosten_EE [€]"] + gesamt_kosten_df["Gesamtkosten_Speicher [€]"]

    return gesamt_kosten_df