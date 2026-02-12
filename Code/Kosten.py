"""
Dieses Modul berechnet die Kosten für den Ausbau der Erneuerbaren Energien und Speicher 
basierend auf den Zielwerten und Veränderungsfaktoren in einem gegebenen Szenario.

Programmiert von Joris Bürger
Unterstützt durch Inline-Sugsestions von Claude Sonnet
"""

from Prognose_Erzeugung import Jährlicher_Zuwachs_EE
from config import DATA_DIR
import pandas as pd
import numpy as np
import json

def Kosten_EE(zieldaten: json, erzeugung_df: pd.DataFrame)-> pd.DataFrame:
    """
    Berechnet die Kosten für den Ausbau der Erneuerbaren Energien basierend auf den Zielwerten für 2030 und 2045.
    
    Args:
        zieldaten (dict): Szenario mit Zielwerten für 2030 und 2045.
        erzeugung_df (pd.DataFrame): DataFrame mit bereits berechneten installierten Leistungen.
    Returns:
        pd.DataFrame: DataFrame mit den jährlichen Ausbaukosten.
    """
    
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
    date_range = pd.date_range(start='01-01-2026 00:00', end='31-12-2045 23:45', freq='15min',tz='UTC') 
    kosten_df = pd.DataFrame({"Datum von": date_range})
    kosten_df["Jahr"] = kosten_df["Datum von"].dt.year
    kosten_df["Monat"]= kosten_df["Datum von"].dt.month
    
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
        spalten_mapping = {
            'wind_onshore': 'Installierte Wind_Onshore_GW',
            'wind_offshore': 'Installierte Wind_Offshore_GW',
            'biomasse': 'Installierte Biomasse_GW',
            'wasser': 'Installierte Wasser_GW',
            'sonstige': 'Installierte Sonstige_GW'
        }
        
        # Für PV separate Berechnung (pv_dach und pv_frei haben unterschiedliche OPEX)
        if key in ['pv_dach', 'pv_frei']:
            zuwachsraten = {"zuwachs_2030": {}, "zuwachs_2045": {}}
            zuwachsraten["zuwachs_2030"][key] = jährliche_raten["zuwachsrate_2030"][key] / 12
            zuwachsraten["zuwachs_2045"][key] = jährliche_raten["zuwachsrate_2045"][key] / 12
            
            prognose = pd.DataFrame({'Datum von': kosten_df['Datum von']})
            prognose['Monat'] = prognose['Datum von'].dt.month
            prognose['Jahr'] = prognose['Datum von'].dt.year

            maske_2030 = prognose["Jahr"] <= 2030
            maske_2045 = prognose["Jahr"] > 2030
            
            prognose.loc[maske_2030, f"Installierte {key}"] = kostendaten[key]["bestand"] + (zuwachsraten["zuwachs_2030"][key] * ((prognose.loc[maske_2030, "Jahr"] - 2026) * 12 + prognose.loc[maske_2030, "Monat"]))
            prognose.loc[maske_2045, f"Installierte {key}"] = zieldaten["Ziele 2030"]["Ausbau EE"][key] + (zuwachsraten["zuwachs_2045"][key] * ((prognose.loc[maske_2045, "Jahr"] - 2031) * 12 + prognose.loc[maske_2045, "Monat"]))

            prognose[f"Opex {key} [€]"] = 1e6 * kostendaten[key]["opex"] * prognose[f"Installierte {key}"] / virtelstunden_pro_jahr
        else:
            # Für andere Erzeugerarten: Nutze bereits berechnete installierte Leistungen aus erzeugung_df
            if key in spalten_mapping:
                spaltenname = spalten_mapping[key]
                prognose = erzeugung_df[['Datum von', spaltenname]].copy()
                prognose['Jahr'] = prognose['Datum von'].dt.year
                prognose[f"Opex {key} [€]"] = 1e6 * kostendaten[key]["opex"] * prognose[spaltenname] / virtelstunden_pro_jahr
            else:
                continue
        
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

def kosten_speicher(szenario: json, speicher_df: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet die Kosten für Speicher basierend auf dem Szenario.
    
    Args:
        szenario (json): Das Szenario mit den Speicherzielen und Veränderungsfaktoren.
        speicher_df (pd.DataFrame): DataFrame mit bereits berechneten Speicherkapazitäten und Viertelstundenleistungen.
        
    Returns:
        pd.DataFrame: DataFrame mit den jährlichen Speicherkosten.
    """
    
    virtelstunden_pro_jahr = 365.25 * 24 * 4
    ausbau_2030_GWh = szenario["Ziele 2030"]["Ausbau Speicher"]
    ausbau_2045_GWh = szenario["Ziele 2045"]["Ausbau Speicher"]

    #=== Einlesen der Kostendaten mit werten in Mio. €/GWh bzw. Mio. €/(GW *a) ===
    kostendaten_pfad = DATA_DIR / "Feste_Parameter" / "speicherarten.json"
    with open(kostendaten_pfad, "r") as file:
        kostendaten = json.load(file)

    date_range = pd.date_range(start='01-01-2026 00:00', end='31-12-2045 23:45', freq='15min',tz='UTC') 
    kosten_df = pd.DataFrame({"Datum von": date_range})

    kosten_df["Jahr"] = kosten_df["Datum von"].dt.year
    kosten_df["Monat"]= kosten_df["Datum von"].dt.month

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
        kosten_df.loc[mask1,f"Ausbaurate {key}"] = (ausbau_2030_GWh[key]-kostendaten[key]["bestand"])  / len(kosten_df[mask1])
        kosten_df.loc[mask2,f"Ausbaurate {key}"] = (ausbau_2045_GWh[key]-ausbau_2030_GWh[key])  / len(kosten_df[mask2])
        mask3 = kosten_df[f"Ausbaurate {key}"] > 0
        kosten_df.loc[mask3,f"Capex {key} [€]"] = 1e6 * kosten_df[f"Ausbaurate {key}"] * kostendaten[key]["capex"] 
        kosten_df.loc[~mask3,f"Capex {key} [€]"] = 0
        kosten_df[f"Capex {key} [€]"] = kosten_df[f"Capex {key} [€]"] * (virtelstunden_capex[key] ** (kosten_df['Jahr'] - 2025))
        kosten_df[f"Capex {key} [€]"] = kosten_df[f"Capex {key} [€]"].round(2)

    #=== OpEx Berechnung ===
    relevante_spalten = ['Datum von', 'Speicherkapazität batteriespeicher [MWh]', 'Speicherkapazität wasserstoff [MWh]', 
                        'Speicherkapazität pumpspeicher [MWh]', 'Viertelstundenleistung batteriespeicher [MW]',
                        'Viertelstundenleistung wasserstoff [MW]', 'Viertelstundenleistung pumpspeicher [MW]']
    kosten_df = pd.merge(kosten_df, speicher_df[relevante_spalten], on="Datum von", how="left")

    for key in kostendaten.keys():      # (MWh/1e3) * (GW/GWh) * (Mio. €/(GW*a)) *1e6 / virtelstunden_pro_jahr  = € / virtelstunde
        #kosten_df[f"Opex {key} [€]"] = (1e3 * kostendaten[key]["opex"] * kosten_df[f"Speicherkapazität {key} [MWh]"] * kostendaten[key]["leistung"]) / virtelstunden_pro_jahr
        kosten_df[f"Opex {key} [€]"] = 4 * kosten_df[f"Viertelstundenleistung {key} [MW]"]  * 1e3 * kostendaten[key]["opex"] / virtelstunden_pro_jahr
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
    
def kostenrechnung(szenario: json, erzeugung_df: pd.DataFrame, speicher_df: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet die Gesamtkosten für Erneuerbare Energien und Speicher basierend auf dem Szenario.
    
    Args:
        szenario (json): Das Szenario mit den Zielwerten und Veränderungsfaktoren.
        erzeugung_df (pd.DataFrame): DataFrame mit bereits berechneten installierten Leistungen.
        speicher_df (pd.DataFrame): DataFrame mit bereits berechneten Speicherkapazitäten.
        
    Returns:
        pd.DataFrame: DataFrame mit den jährlichen Gesamtkosten.
    """
    kosten_ee_df = Kosten_EE(szenario, erzeugung_df)
    kosten_speicher_df = kosten_speicher(szenario, speicher_df)

    gesamt_kosten_df = pd.merge(kosten_ee_df, kosten_speicher_df, on="Datum von", how="inner")

    gesamt_kosten_df["Gesamtkosten_EE_und_Speicher [€]"] = gesamt_kosten_df["Gesamtkosten_EE [€]"] + gesamt_kosten_df["Gesamtkosten_Speicher [€]"]
    if(gesamt_kosten_df.isna().any().any()):
        print("Warnung: Es gibt fehlende Werte in der Verbrauchsprognose!"  )
        print(gesamt_kosten_df.isna().sum())
        mask = gesamt_kosten_df.isna() | gesamt_kosten_df.isin([np.inf, -np.inf])
        print(gesamt_kosten_df[mask.any(axis=1)])
        
    return gesamt_kosten_df