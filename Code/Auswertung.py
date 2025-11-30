import pandas as pd
import json
from config import DATA_DIR
from Prognose_Erzeugung import Jährlicher_Zuwachs_EE
from Feste_Variablen import Keys_Erzeugung

def ausgabe(kosten_df: pd.DataFrame, ee_df: pd.DataFrame,szenario: json):
    """
    Gibt die Daten als Excel-Datei aus.
    Args:
        kosten_df (pd.DataFrame): DataFrame mit den Kosteninformationen
        ee_df (pd.DataFrame): DataFrame mit den Erneuerbaren-Anteil-Informationen
        szenario (json): Das Szenario, das analysiert wurde
    """

    ausbauraten = Jährlicher_Zuwachs_EE(szenario["Ziele 2030"]["Ausbau EE"], szenario["Ziele 2045"]["Ausbau EE"])

    gesamt = pd.merge(ee_df, kosten_df, on="Datum von", how="inner")

    pfad = DATA_DIR / f"szenario_{szenario['Name']}_auswertung.xlsx"

    gesamt["Jahr"] = gesamt["Datum von"].dt.year

    end_df = pd.DataFrame()
    jahre = range(2026, 2046)
    end_df = pd.DataFrame({"Jahr": jahre})

    for jahr in range(2026, 2046):
        end_df.loc[end_df["Jahr"] == jahr, "Realisierte Erzeugung [TWh]"] = gesamt[gesamt["Jahr"] == jahr]["Realisierte Erzeugung [MWh]"].sum().round(2) / 1e6
        end_df.loc[end_df["Jahr"] == jahr, "Erzeugung Erneuerbare [TWh]"] = gesamt[gesamt["Jahr"] == jahr]["Erneuerbare [MWh]"].sum().round(2) / 1e6
        end_df.loc[end_df["Jahr"] == jahr, "Verbrauch [TWh]"] = gesamt[gesamt["Jahr"] == jahr]["Netzlast [MWh]"].sum().round(2) / 1e6
        end_df.loc[end_df["Jahr"] == jahr, "Anteil ohne Speicher mit 100% [%]"] = round(gesamt[(gesamt["Jahr"] == jahr) & (gesamt["Anteil Erneuerbare [%]"] >= 100)].shape[0] / len(gesamt[gesamt["Jahr"] == jahr]) * 100, 2)
        end_df.loc[end_df["Jahr"] == jahr, "Anteil mit Speicher mit 100% [%]"] = round(gesamt[(gesamt["Jahr"] == jahr) & (gesamt["Anteil Erneuerbare Speicher [%]"] >= 100)].shape[0] / len(gesamt[gesamt["Jahr"] == jahr]) * 100, 2)
        for key in Keys_Erzeugung:
            end_df.loc[end_df["Jahr"] == jahr, f"Gesamtkosten {key} [Tsd. €]"] = gesamt[gesamt["Jahr"] == jahr][f"Gesamtkosten {key} [€]"].sum() / 1e3
    
    for key in Keys_Erzeugung:
        end_df.loc[end_df["Jahr"]<=2030, f"Ausbaurate {key} [GW/Jahr]"] = round(ausbauraten["zuwachsrate_2030"][key], 2)
        end_df.loc[end_df["Jahr"]>2030, f"Ausbaurate {key} [GW/Jahr]"] = round(ausbauraten["zuwachsrate_2045"][key], 2)

    with pd.ExcelWriter(pfad, engine='openpyxl') as writer:
        end_df.to_excel(writer, sheet_name="Jahresübersicht", index=False)
