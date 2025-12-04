import pandas as pd
import json
from config import DATA_DIR
from Prognose_Erzeugung import Jährlicher_Zuwachs_EE
from Feste_Variablen import Keys_Erzeugung

def ausgabe(kosten_df: pd.DataFrame, ee_df: pd.DataFrame,szenario: json, pfad: str ):
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

    end_df['Energie aus Speichern [TWh]'] = (gesamt.groupby('Jahr')['Energie aus Speicher [MWh]'].sum() / 1e6).round(2).values
    end_df['Erzeugung Erneuerbare [TWh]'] = (gesamt.groupby('Jahr')['Erneuerbare [MWh]'].sum() / 1e6).round(2).values
    end_df['Verbrauch [TWh]'] = (gesamt.groupby('Jahr')['Netzlast [MWh]'].sum() / 1e6).round(2).values

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