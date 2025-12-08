"""
Programmiert von Joris Bürger
"""
import pandas as pd
import json
from config import DATA_DIR
from Prognose_Erzeugung import Jährlicher_Zuwachs_EE
from Feste_Variablen import Keys_Erzeugung
import matplotlib.pyplot as plt

def ausgabe(kosten_df: pd.DataFrame, ee_df: pd.DataFrame,szenario: json, pfad: str, konventionelle: dict):
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

    gesamt["Jahr"] = gesamt["Datum von"].dt.year

    end_df = pd.DataFrame()
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

    anzahl_100_ohne = nur_100_ohne.groupby('Jahr').size()
    anzahl_100_mit = nur_100_mit.groupby('Jahr').size()
    anzahl_gesamt = gesamt.groupby('Jahr').size()

    end_df['Anteil ohne Speicher mit 100% [%]'] = (anzahl_100_ohne / anzahl_gesamt * 100).round(2).values
    end_df['Anteil mit Speicher mit 100% [%]'] = (anzahl_100_mit / anzahl_gesamt * 100).round(2).values

    for key in Keys_Erzeugung:
        kosten_summe = gesamt.groupby('Jahr')[f"Gesamtkosten {key} [€]"].sum() / 1e3
        end_df[f"Gesamtkosten {key} [Tsd. €]"] = kosten_summe.values

    end_df["Gesamtkosten_EE [Tsd. €]"] = (gesamt.groupby('Jahr')["Gesamtkosten_EE [€]"].sum() / 1e3).round(2).values

    with pd.ExcelWriter(pfad, engine='openpyxl') as writer:
        end_df.to_excel(writer, sheet_name="Jahresübersicht", index=False)

def ausgabe_alle(szenarien: json, pfad: str,jahr: int = 2045):
    """
    Gibt die Daten eines SzenarioErgebnis als Excel-Datei aus.
    Args:
        SzenarioErgebnis (SzenarioErgebnis): Das SzenarioErgebnis-Objekt
        pfad (str): Pfad zur Ausgabedatei
    """
    Ergebnisse_df = pd.DataFrame()
    
    for szenario in szenarien:
        if szenario.erzeugung_df is not None:
            temp_df = szenario.erzeugung_df.copy()
            temp_df["Szenario"] = szenario.name
            Ergebnisse_df = pd.concat([Ergebnisse_df, temp_df], ignore_index=True)

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