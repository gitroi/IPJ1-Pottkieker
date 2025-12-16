"""
Programmiert von Joris Bürger
"""
import pandas as pd
import json
from config import DATA_DIR
from Prognose_Erzeugung import Jährlicher_Zuwachs_EE
from Feste_Variablen import Keys_Erzeugung, Keys_Speicher
import matplotlib.pyplot as plt
from Prognose_Speicher import ausbaurate_GWh_Jahr

def ausgabe(kosten_df: pd.DataFrame, ee_df: pd.DataFrame,szenario: json, konventionelle: dict) -> pd.DataFrame:
    """
    Gibt die Daten als Excel-Datei aus.
    Args:
        kosten_df (pd.DataFrame): DataFrame mit den Kosteninformationen
        ee_df (pd.DataFrame): DataFrame mit den Erneuerbaren-Anteil-Informationen
        szenario (json): Das Szenario, das analysiert wurde
        pfad (str): Pfad zur Ausgabedatei
    """

    ausbauraten = Jährlicher_Zuwachs_EE(szenario["Ziele 2030"]["Ausbau EE"], szenario["Ziele 2045"]["Ausbau EE"])
    gesamt = pd.merge(ee_df, kosten_df, on="Datum von", how="inner")
    ausbauraten_speicher = ausbaurate_GWh_Jahr(szenario)

    gesamt["Jahr"] = gesamt["Datum von"].dt.year

    jahre = range(2026, 2046)
    end_df = pd.DataFrame({"Jahr": jahre})

    gesamt["Jahr"] = gesamt["Datum von"].dt.year

    end_df['Benötigte Energie aus Speichern [TWh]'] = (gesamt.groupby('Jahr')['Energie aus Speicher [MWh]'].sum() / 1e6).round(2).values
    end_df['Erzeugung Erneuerbare im Jahr [TWh]'] = (gesamt.groupby('Jahr')['Erneuerbare [MWh]'].sum() / 1e6).round(2).values
    end_df['Verbrauch [TWh]'] = (gesamt.groupby('Jahr')['Netzlast [MWh]'].sum() / 1e6).round(2).values

    for jahr in konventionelle.keys():
        end_df.loc[end_df["Jahr"] == jahr, "Max Konventionelle Leistung [GW]"] = konventionelle[jahr]["Leistung"] /1e3
        end_df.loc[end_df["Jahr"] == jahr, "Konventionelle Energie [TWh]"] = konventionelle[jahr]["Energie"]/1e6

    nur_100_ohne = gesamt[gesamt["Anteil Erneuerbare [%]"] >= 100]
    nur_100_mit = gesamt[gesamt["Anteil Erneuerbare Speicher [%]"] >= 100]

    anzahl_100_ohne_30 = nur_100_ohne[nur_100_ohne["Jahr"]==2030].groupby('Jahr').size()
    anzahl_100_mit_30 = nur_100_mit[nur_100_mit["Jahr"]==2030].groupby('Jahr').size()
    anzahl_gesamt_30 = gesamt[gesamt["Jahr"]==2030]["Jahr"].groupby('Jahr').size()
    
    end_df['Anteil ohne Speicher mit 100% 2030 [%]'] = (anzahl_100_ohne_30 / anzahl_gesamt_30 * 100).round(2).values
    end_df['Anteil mit Speicher mit 100% 2030 [%]'] = (anzahl_100_mit_30 / anzahl_gesamt_30 * 100).round(2).values

    anzahl_100_ohne_45 = nur_100_ohne[nur_100_ohne["Jahr"]==2045].groupby('Jahr').size()
    anzahl_100_mit_45 = nur_100_mit[nur_100_mit["Jahr"]==2045].groupby('Jahr').size()
    anzahl_gesamt_45 = gesamt[gesamt["Jahr"]==2045]["Jahr"].groupby('Jahr').size()

    end_df['Anteil ohne Speicher mit 100% 2045 [%]'] = (anzahl_100_ohne_45 / anzahl_gesamt_45 * 100).round(2).values
    end_df['Anteil mit Speicher mit 100% 2045 [%]'] = (anzahl_100_mit_45 / anzahl_gesamt_45 * 100).round(2).values

    end_df["Gesamtkosten_EE [Mrd. €]"] = (gesamt.groupby('Jahr')["Gesamtkosten_EE [€]"].sum() / 1e9).round(2).values
    
    end_df["Gesamtkosten_Speicher [Mrd. €]"] = (gesamt.groupby('Jahr')["Gesamtkosten_Speicher [€]"].sum() / 1e9).round(2).values
    
    end_df["Gesamtkosten_EE_und_Speicher [Mrd. €]"] = (gesamt.groupby('Jahr')["Gesamtkosten_EE_und_Speicher [€]"].sum() / 1e9).round(2).values
    
    mask1 = end_df["Jahr"] <= 2030
    mask2 = end_df["Jahr"] > 2030

    for key in Keys_Erzeugung:
        kosten_summe = gesamt.groupby('Jahr')[f"Gesamtkosten {key} [€]"].sum() / 1e9
        end_df[f"Gesamtkosten {key} [Mrd. €]"] = kosten_summe.values

    for key in Keys_Speicher:
        kosten_summe = gesamt.groupby('Jahr')[f"Gesamtkosten {key} [€]"].sum() / 1e9
        end_df[f"Gesamtkosten {key} [Mrd. €]"] = kosten_summe.values

    for key in ausbauraten["zuwachsrate_2030"].keys():
        end_df.loc[mask1, f"Ausbaurate {key} [GW/Jahr]"] = ausbauraten["zuwachsrate_2030"][key]
        end_df.loc[mask2, f"Ausbaurate {key} [GW/Jahr]"] = ausbauraten["zuwachsrate_2045"][key]

    for key in Keys_Speicher:
        end_df.loc[mask1, f"Ausbaurate {key} [GWh/Jahr]"] = ausbauraten_speicher["zuwachsrate_2030"][key]
        end_df.loc[mask2, f"Ausbaurate {key} [GWh/Jahr]"] = ausbauraten_speicher["zuwachsrate_2045"][key]

    return end_df

def konventionelle_Leistung_Energie(erzeugung: pd.DataFrame) -> dict:
    """
    Analysiert die konventionelle Leistung und Energie basierend auf dem Dataframe 'erzeugung'.
    Args:
        erzeugung (pd.DataFrame): DataFrame mit Erzeugungsdaten und speicherinformationen
        jahr (int): Jahr für die Analyse
    Returns:
        dict: Dictionary mit konventioneller Leistung und Energie
    Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
    """
    erzeugung = erzeugung.copy()
    
    erzeugung["Jahr"] = erzeugung["Datum von"].dt.year
    reserven_dict = {}
    for jahr in erzeugung["Jahr"].unique():
        df_jahr = erzeugung[erzeugung["Jahr"] == jahr]
        df_jahr = df_jahr[["Datum von","Netzlast [MWh]","Erneuerbare [MWh]","Realisierte Erzeugung [MWh]"]]
        
        df_jahr["Konventionelle Energie [MWh]"] = (df_jahr["Netzlast [MWh]"] - df_jahr["Erneuerbare [MWh]"]).clip(lower=0)
        
        max_energie_viertelstunde = df_jahr["Konventionelle Energie [MWh]"].max()
        
        max_leistung_konventionell = round(max_energie_viertelstunde / 0.25, 2)
        
        energie_konventionell = df_jahr["Konventionelle Energie [MWh]"].sum()


        reserven_dict[jahr] = {
            "Leistung": max_leistung_konventionell,
            "Energie": energie_konventionell
        }


    return reserven_dict