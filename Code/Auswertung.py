"""
Programmiert von Joris Bürger , Robin Matzke
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

    grouped = gesamt.groupby('Jahr')
    
    end_df['Energie aus Speichern [TWh]'] = (grouped['Energie aus Speicher [MWh]'].sum() / 1e6).round(2).values
    end_df['Erzeugung Erneuerbare im Jahr [TWh]'] = (grouped['Erneuerbare [MWh]'].sum() / 1e6).round(2).values
    end_df['Verbrauch [TWh]'] = (grouped['Netzlast [MWh]'].sum() / 1e6).round(2).values

    for jahr in konventionelle.keys():
        end_df.loc[end_df["Jahr"] == jahr, "Max Konventionelle Leistung [GW]"] = konventionelle[jahr]["Leistung"] /1e3
        end_df.loc[end_df["Jahr"] == jahr, "Konventionelle Energie [TWh]"] = konventionelle[jahr]["Energie"]/1e6

    nur_100_ohne = gesamt[gesamt["Anteil Erneuerbare [%]"] >= 100]
    nur_100_mit = gesamt[gesamt["Anteil Erneuerbare Speicher [%]"] >= 100]

    anzahl_100_ohne = nur_100_ohne.groupby('Jahr').size()
    anzahl_100_mit = nur_100_mit.groupby('Jahr').size()
    anzahl_gesamt = gesamt.groupby('Jahr').size()

    gesamt["Konventionelle Energie mit Speicher [MWh]"] = (
        gesamt["Netzlast [MWh]"] - gesamt["Realisierte Erzeugung [MWh]"]
    ).clip(lower=0)
    
    gesamt["Konventionelle Energie ohne Speicher [MWh]"] = (
        gesamt["Netzlast [MWh]"] - gesamt["Erneuerbare [MWh]"]
    ).clip(lower=0)

    end_df["EE Anteil am Stromverbrauch ohne Speicher [%]"] = (
        (grouped["Netzlast [MWh]"].sum() - grouped["Konventionelle Energie ohne Speicher [MWh]"].sum()) / 
        grouped["Netzlast [MWh]"].sum() * 100
    ).round(2).values
    end_df["EE Anteil am Stromverbrauch mit Speicher [%]"] = (
        (grouped["Netzlast [MWh]"].sum() - grouped["Konventionelle Energie mit Speicher [MWh]"].sum()) / 
        grouped["Netzlast [MWh]"].sum() * 100
    ).round(2).values

    end_df['Nicht genutzte Erneuerbare Energie im Jahr [TWh]'] = (grouped['Überschüssige Energie nach Laden [MWh]'].sum() / 1e6).round(2).values

    end_df['Anteil virtel Stunden ohne Speicher mit 100% [%]'] = ((anzahl_100_ohne / anzahl_gesamt * 100).round(2)).values
    end_df['Anteil virtel Stunden mit Speicher mit 100% [%]'] = ((anzahl_100_mit / anzahl_gesamt * 100).round(2)).values

    end_df["Gesamtkosten_EE [Mrd. €]"] = (grouped["Gesamtkosten_EE [€]"].sum() / 1e9).round(2).values
    
    end_df["Gesamtkosten_Speicher [Mrd. €]"] = (grouped["Gesamtkosten_Speicher [€]"].sum() / 1e9).round(2).values
    
    end_df["Gesamtkosten_EE_und_Speicher [Mrd. €]"] = (grouped["Gesamtkosten_EE_und_Speicher [€]"].sum() / 1e9).round(2).values
    
    mask1 = end_df["Jahr"] <= 2030
    mask2 = end_df["Jahr"] > 2030
    
    konventionelle_typen = ["braun", "erdgas", "stein", "sonstige_konventionelle", "importe"]
    for konv_typ in konventionelle_typen:
        if f"{konv_typ} [GW]" in gesamt.columns:
            end_df[f"Installierte Leistung {konv_typ} [GW]"] = grouped[f"{konv_typ} [GW]"].first().values
            
            kosten_capex = grouped[f"{konv_typ}_capex [€]"].sum() if f"{konv_typ}_capex [€]" in gesamt.columns else 0
            kosten_opex = grouped[f"{konv_typ}_opex [€]"].sum() if f"{konv_typ}_opex [€]" in gesamt.columns else 0
            end_df[f"Gesamtkosten {konv_typ} [Mrd. €]"] = ((kosten_capex + kosten_opex) / 1e9).round(2).values
        elif konv_typ == "importe":
            kosten_opex = grouped[f"{konv_typ}_opex [€]"].sum() if f"{konv_typ}_opex [€]" in gesamt.columns else 0
            end_df[f"Gesamtkosten {konv_typ} [Mrd. €]"] = (kosten_opex / 1e9).round(2).values

    gesamtkosten_konventionelle_spalten = ["Gesamtkosten braun [Mrd. €]", "Gesamtkosten erdgas [Mrd. €]",
                                            "Gesamtkosten stein [Mrd. €]", "Gesamtkosten sonstige_konventionelle [Mrd. €]", "Gesamtkosten importe [Mrd. €]"]

    if gesamtkosten_konventionelle_spalten:
        end_df["Gesamtkosten Konventionelle [Mrd. €]"] = end_df[gesamtkosten_konventionelle_spalten].sum(axis=1).round(2)
    else:
        end_df["Gesamtkosten Konventionelle [Mrd. €]"] = 0.0

    end_df["Gesamtkosten Gesamt [Mrd. €]"] = (
        end_df["Gesamtkosten_EE [Mrd. €]"] + 
        end_df["Gesamtkosten_Speicher [Mrd. €]"] + 
        end_df["Gesamtkosten Konventionelle [Mrd. €]"]
    ).round(2)

    for key in Keys_Erzeugung:
        if f"Gesamtkosten {key} [Mrd. €]" not in end_df.columns:
            end_df[f"Gesamtkosten {key} [Mrd. €]"] = (grouped[f"Gesamtkosten {key} [€]"].sum() / 1e9).round(2).values

    for key in Keys_Speicher:
        end_df[f"Gesamtkosten {key} [Mrd. €]"] = (grouped[f"Gesamtkosten {key} [€]"].sum() / 1e9).round(2).values

    for key in ausbauraten["zuwachsrate_2030"].keys():
        end_df.loc[mask1, f"Ausbaurate {key} [GW/Jahr]"] = ausbauraten["zuwachsrate_2030"][key]
        end_df.loc[mask2, f"Ausbaurate {key} [GW/Jahr]"] = ausbauraten["zuwachsrate_2045"][key]

    for key in Keys_Speicher:
        end_df.loc[mask1, f"Ausbaurate {key} [GWh/Jahr]"] = ausbauraten_speicher["zuwachsrate_2030"][key]
        end_df.loc[mask2, f"Ausbaurate {key} [GWh/Jahr]"] = ausbauraten_speicher["zuwachsrate_2045"][key]

    for key in Keys_Speicher:
        kapazitaet_spalte = f"Speicherkapazität {key} [MWh]"
        if kapazitaet_spalte in gesamt.columns:
            end_df[f"Speicherkapazität {key} [GWh]"] = (grouped[kapazitaet_spalte].last() / 1e3).round(2).values


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
        
        df_jahr["Konventionelle Energie [MWh]"] = (df_jahr["Netzlast [MWh]"] - df_jahr["Realisierte Erzeugung [MWh]"]).clip(lower=0)
        
        max_energie_viertelstunde = df_jahr["Konventionelle Energie [MWh]"].max()
        
        max_leistung_konventionell = round(max_energie_viertelstunde / 0.25, 2)
        
        energie_konventionell = df_jahr["Konventionelle Energie [MWh]"].sum()


        reserven_dict[jahr] = {
            "Leistung": max_leistung_konventionell,
            "Energie": energie_konventionell
        }


    return reserven_dict

def top10_fehlenergie_berechnen(gesamt_df: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet die Top 10 Zeitpunkte mit der größten Fehlenergie aus dem Speicher-DataFrame.
    Args:
        gesamt_df (pd.DataFrame): DataFrame mit Speicherinformationen
    Returns:
        pd.DataFrame: DataFrame mit den Top 10 Zeitpunkten und relevanten Daten
    """

    spalten = [
        "Datum von", 
        "Fehlende Energie [MWh]", 
        "Anteil Erneuerbare Speicher [%]", 
        "Ladestand batteriespeicher [MWh]",
        "Ladestand wasserstoff [MWh]",
        "Ladestand pumpspeicher [MWh]",
        "Viertelstundenleistung batteriespeicher [MW]", 
        "Viertelstundenleistung wasserstoff [MW]",
        "Viertelstundenleistung pumpspeicher [MW]",
        "Speicherkapazität batteriespeicher [MWh]",
        "Speicherkapazität wasserstoff [MWh]",
        "Speicherkapazität pumpspeicher [MWh]"
    ]
    
    top10_Fehlenergie_df = gesamt_df.nlargest(10, "Fehlende Energie [MWh]", 'all')[spalten]

    return top10_Fehlenergie_df

def formatiere_spaltennamen(df):
    """Formatiert DataFrame-Spaltennamen für bessere Lesbarkeit"""
    df_formatiert = df.copy()
    
    # Mapping für spezifische Ersetzungen
    ersetzungen = {
        'virtel': 'Viertel',
        'Miliarden': 'Mrd.',
        'Konventioenelle': 'Konventionelle',
        'Mil.': 'Mio.',
        'pv': 'PV',
        'PV_dach': 'PV-Dach',
        'PV_freifläche': 'PV-Freifläche',
        'wind_onshore': 'Wind-Onshore',
        'wind_offshore': 'Wind-Offshore',
        '_': ' ',  # Unterstriche durch Leerzeichen ersetzen
    }
    
    neue_spalten = []
    for col in df_formatiert.columns:
        neuer_name = col
        
        for alt, neu in ersetzungen.items():
            if alt != '_':  
                neuer_name = neuer_name.replace(alt, neu)
        
        
        if '[' in neuer_name:
            teile = neuer_name.split('[')
            teile[0] = teile[0].replace('_', ' ')
            neuer_name = '['.join(teile)
        else:
            neuer_name = neuer_name.replace('_', ' ')
        
        neuer_name = ' '.join(neuer_name.split())
        
        neue_spalten.append(neuer_name)
    
    df_formatiert.columns = neue_spalten
    return df_formatiert