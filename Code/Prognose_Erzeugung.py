"""
Zentrales Programm der Erzeugungsprognose von der Gruppe Pottkieker.
Nutzt Daten aus 2024 um eine Prognose bis 2045 zu erstellen.
Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
Programmiert von Joris Bürger   
"""
import json
import pandas as pd
import numpy as np
from config import PROJECT_ROOT #Ordnerverzeichnis in Config-Datei festgelegt, damit auf allen Geräten gleich

def Jährlicher_Zuwachs_EE( zielwert_2030:dict, zielwert_2045:dict ) -> dict:
    """
    Berechnet den jährlichen Zuwachs der Erneuerbaren Energien zwischen 2024 und 2030 sowie zwischen 2030 und 2045.
    Parameters:
        zielwert_2030 (dict): Zielwerte für 2030 in GW. Schlüssel: 'pv', 'wind_onshore', 'wind_offshore', 'biomasse', 'wasser', 'sonstige'.
        zielwert_2045 (dict): Zielwerte für 2045 in GW. Schlüssel: 'pv', 'wind_onshore', 'wind_offshore', 'biomasse', 'wasser', 'sonstige'.
    """

    #=== Installierte Leistung in GW einlesen ===
    pfad = PROJECT_ROOT / "Daten" / "Feste_Parameter" / "erzeugerarten.json"
    with open(pfad, "r") as file:
        erzeugerarten = json.load(file)

    #=== Zuwachs pro Jahr berechnen ===#
    zuwachs_dict = {"zuwachsrate_2030": {}, "zuwachsrate_2045": {}}
    for key in zielwert_2030.keys():
        aktueller_wert_2024 = erzeugerarten[key]["bestand"]
        zuwachsrate_2030 = (zielwert_2030[key] - aktueller_wert_2024) / 6  
        zuwachsrate_2045 = (zielwert_2045[key] - zielwert_2030[key]) / 15  
        zuwachs_dict["zuwachsrate_2030"][key] = round(zuwachsrate_2030, 3)
        zuwachs_dict["zuwachsrate_2045"][key] = round(zuwachsrate_2045, 3)

    return zuwachs_dict 

""" Jahreswerte für PV und Wind leistung der letzen 5 Jahre: 
    2020: PV: 10,387% Wind: 25,202%
    2021: PV: 9,608% Wind: 20,860%
    2022: PV: 10,319% Wind: 21,435%
    2023: PV: 8,789% Wind: 23,325%
    2024: PV: 8,459% Wind:22,022%
    Bestes Jahr PV: 10,387% (2020)
    Bestes Jahr Wind: 25,202% (2020)
    Schlechtestes Jahr PV: 8,459% (2024)
    Schlechtestes Jahr Wind: 20,860% (2021)
"""

def Prognose_erzeugung(installierte_2030: dict, installierte_2045: dict,steigerungsfaktoren: dict, ertragsart: str) -> pd.DataFrame:
    """
    Funktion zur Prognose der Erneuerbaren Energieerzeugung von 2026 bis 2045 basierend auf dem Ausbaustand für verschiedene Energiequellen.
    Parameters:
        installierte_2030 (dict): Installierte Leistung für 2030 in GW. Schlüssel: 'pv', 'wind_onshore', 'wind_offshore', 'biomasse', 'wasser', 'sonstige'.
        installierte_2045 (dict): Installierte Leistung für 2045 in GW. Schlüssel: 'pv', 'wind_onshore', 'wind_offshore', 'biomasse', 'wasser', 'sonstige'.

    """

    #=== Steigerungsfaktoren auf virtel Stunden werte umrechnen ===
    virtelstunden_steigerungsfaktoren = {}
    for key in steigerungsfaktoren.keys():
        virtelstunden_steigerungsfaktoren[key] = steigerungsfaktoren[key] ** (1/(365.25*24*4))  

    #=== Installierte Leistung in GW einlesen ===
    pfad = PROJECT_ROOT / "Daten" / "Feste_Parameter" / "Netto_Installiert_GW.csv"  
    installierte_leistung_df = pd.read_csv(pfad, sep=';', decimal=',', low_memory=False)
    
    pfad2 = PROJECT_ROOT / "Daten" / "Feste_Parameter" / "erzeugerarten.json"
    with open(pfad2, "r") as file:
        erzeugerarten = json.load(file)

    installierte_leistung_df["Jahr"] = pd.to_numeric(installierte_leistung_df["Jahr"], errors='coerce').astype(int)
    installierte_leistung_df["Monat"] = pd.to_numeric(installierte_leistung_df["Monat"], errors='coerce').astype(int)

    #=== Zuwachs pro Monat berechnen ===#
    jahres_raten = Jährlicher_Zuwachs_EE(installierte_2030, installierte_2045)
    zuwachsraten = {"zuwachs_2030": {}, "zuwachs_2045": {}}
    zuwachsraten["zuwachs_2030"]["pv"] = 0
    zuwachsraten["zuwachs_2045"]["pv"] = 0
    # bis 2030
    for key in jahres_raten["zuwachsrate_2030"].keys():
        if(key == "pv_dach") or (key == "pv_frei"):
            zuwachsraten["zuwachs_2030"]["pv"] += jahres_raten["zuwachsrate_2030"][key] / 12
            zuwachsraten["zuwachs_2045"]["pv"] += jahres_raten["zuwachsrate_2045"][key] / 12
            continue

        zuwachsraten["zuwachs_2030"][key] = jahres_raten["zuwachsrate_2030"][key] / 12
        zuwachsraten["zuwachs_2045"][key] = jahres_raten["zuwachsrate_2045"][key] / 12
    
    #==== Einlesen der Daten und anpassung ====
    erzeugungpfad = PROJECT_ROOT / "Daten" / "SMARD-Daten"/ "erzeugung_20_24.csv"
    erzeugung_df = pd.read_csv(erzeugungpfad,
    sep=';', low_memory=False
    )

    for col in erzeugung_df.columns:
        if "MWh" in col:
            erzeugung_df[col] = pd.to_numeric(
                erzeugung_df[col].astype(str)
                .str.replace('.', '',regex=False)
                .str.replace(',', '.',regex=False)
                .str.replace('-', '0', regex=False)
                .astype(float),
                errors='coerce'
            )

    erzeugung_df["Datum von"] = pd.to_datetime(erzeugung_df["Datum von"], format="%d.%m.%Y %H:%M")
    erzeugung_df["Datum von"] = erzeugung_df["Datum von"].dt.tz_localize("Europe/Berlin", ambiguous='infer').dt.tz_convert('UTC')

    erzeugung_df = erzeugung_df[["Datum von", "Photovoltaik [MWh] Originalauflösungen","Wind Onshore [MWh] Originalauflösungen","Wind Offshore [MWh] Originalauflösungen","Biomasse [MWh] Originalauflösungen","Wasserkraft [MWh] Originalauflösungen","Sonstige Erneuerbare [MWh] Originalauflösungen"]]

    # WICHTIG: Kein inplace=True mit Zuweisung verwenden, da dies None zurückgibt
    erzeugung_df = erzeugung_df.rename(columns={
        "Photovoltaik [MWh] Originalauflösungen": "PV [MWh]",
        "Wind Onshore [MWh] Originalauflösungen": "Wind Onshore [MWh]",
        "Wind Offshore [MWh] Originalauflösungen": "Wind Offshore [MWh]",
        "Biomasse [MWh] Originalauflösungen": "Biomasse [MWh]",
        "Wasserkraft [MWh] Originalauflösungen": "Wasser [MWh]",
        "Sonstige Erneuerbare [MWh] Originalauflösungen": "Sonstige [MWh]"
    })
    
    spalten_EE = ["PV [MWh]", "Wind Onshore [MWh]", "Wind Offshore [MWh]", "Biomasse [MWh]", "Wasser [MWh]", "Sonstige [MWh]"]

    erzeugung_df["Jahr"] = erzeugung_df["Datum von"].dt.year
    erzeugung_df["Monat"] = erzeugung_df["Datum von"].dt.month
    erzeugung_df["Tag"] = erzeugung_df["Datum von"].dt.day
    erzeugung_df["Stunde"] = erzeugung_df["Datum von"].dt.hour
    erzeugung_df["Minute"] = erzeugung_df["Datum von"].dt.minute

    #=== Kapazitätsfaktoren berechnen ===

    #=== Installierte Leistungen in DataFrame der Erzeugung einfügen ===
    erzeugung_df = pd.merge(
        erzeugung_df[["Jahr", "Monat", "Tag", "Stunde", "Minute",]+ spalten_EE],
        installierte_leistung_df,on=["Jahr", "Monat"], how="left"
    )

    #=== Kapazitätsfaktoren berechnen ===
    erzeugung_df["Kapazitätsfaktor_PV"] = erzeugung_df["PV [MWh]"] / (erzeugung_df["pv"] * 1000 * 0.25)
    erzeugung_df["Kapazitätsfaktor_Wind_Onshore"] = erzeugung_df["Wind Onshore [MWh]"] / (erzeugung_df["wind_onshore"] * 1000 * 0.25)
    erzeugung_df["Kapazitätsfaktor_Wind_Offshore"] = erzeugung_df["Wind Offshore [MWh]"] / (erzeugung_df["wind_offshore"] * 1000 * 0.25)
    erzeugung_df["Kapazitätsfaktor_Biomasse"] = erzeugung_df["Biomasse [MWh]"] / (erzeugung_df["biomasse"] * 1000 * 0.25)
    erzeugung_df["Kapazitätsfaktor_Wasser"] = erzeugung_df["Wasser [MWh]"] / (erzeugung_df["wasser"] * 1000 * 0.25)
    erzeugung_df["Kapazitätsfaktor_Sonstige"] = erzeugung_df["Sonstige [MWh]"] / (erzeugung_df["sonstige"] * 1000 * 0.25)
   
    spalten_kapazitätsfaktoren = ["Kapazitätsfaktor_PV","Kapazitätsfaktor_Wind_Onshore","Kapazitätsfaktor_Wind_Offshore","Kapazitätsfaktor_Biomasse","Kapazitätsfaktor_Wasser","Kapazitätsfaktor_Sonstige"]

    #=== kapazitäsfaktoren für gutes, schlechtes und mittleres Jahr speichern ===
    if (ertragsart != "gut") and (ertragsart != "mittel") and (ertragsart != "schlecht"):
            raise ValueError("Ungültige Ertragsart. Bitte 'gut', 'mittel' oder 'schlecht' angeben.")
    
    if ertragsart == "gut":
        erzeugung_df = erzeugung_df[erzeugung_df["Jahr"] == 2020]
    elif ertragsart == "mittel":
        erzeugung_df_2020_2024 = erzeugung_df[erzeugung_df["Jahr"].between(2020, 2024)].copy()
        
        # Gruppiere nach Monat, Tag, Stunde, Minute und berechne Median
        erzeugung_df = erzeugung_df_2020_2024.groupby(['Monat', 'Tag', 'Stunde', 'Minute'])[
            ['Monat', 'Tag', 'Stunde', 'Minute'] + spalten_kapazitätsfaktoren
        ].median().reset_index(drop=True)
    elif ertragsart == "schlecht":
        basis_2024 = erzeugung_df[erzeugung_df["Jahr"] == 2024].copy()
        basis_2021 = erzeugung_df[erzeugung_df["Jahr"] == 2021].copy()
        
        # 29. Februar für 2021 interpolieren: Durchschnitt von 28. Feb und 1. März
        feb_28 = basis_2021[(basis_2021["Monat"] == 2) & (basis_2021["Tag"] == 28)].copy()
        mar_01 = basis_2021[(basis_2021["Monat"] == 3) & (basis_2021["Tag"] == 1)].copy()
       
        feb_29 = pd.merge(
            feb_28[["Monat","Tag","Stunde","Minute","Kapazitätsfaktor_Wind_Onshore","Kapazitätsfaktor_Wind_Offshore"]],
            mar_01[["Stunde","Minute","Kapazitätsfaktor_Wind_Onshore","Kapazitätsfaktor_Wind_Offshore"]],
            on=["Stunde","Minute"], how="inner", suffixes=('_feb28', '_mar01')
        )

        feb_29["Kapazitätsfaktor_Wind_Onshore"] = (feb_29["Kapazitätsfaktor_Wind_Onshore_feb28"] + feb_29["Kapazitätsfaktor_Wind_Onshore_mar01"]) / 2
        feb_29["Kapazitätsfaktor_Wind_Offshore"] = (feb_29["Kapazitätsfaktor_Wind_Offshore_feb28"] + feb_29["Kapazitätsfaktor_Wind_Offshore_mar01"]) / 2
        feb_29["Tag"] = feb_28["Tag"].values + 1
        feb_29["Monat"] = feb_28["Monat"].values
        feb_29 = feb_29[["Monat","Tag","Stunde","Minute","Kapazitätsfaktor_Wind_Onshore","Kapazitätsfaktor_Wind_Offshore"]]
        
        basis_2021_erweitert = pd.concat([
            basis_2021[["Monat","Tag","Stunde","Minute","Kapazitätsfaktor_Wind_Onshore","Kapazitätsfaktor_Wind_Offshore"]],
            feb_29
        ], ignore_index=True)

        erzeugung_df = pd.merge(
            basis_2024[["Monat","Tag","Stunde","Minute","Kapazitätsfaktor_PV","Kapazitätsfaktor_Biomasse","Kapazitätsfaktor_Wasser","Kapazitätsfaktor_Sonstige"]],
            basis_2021_erweitert,
            on=["Monat","Tag","Stunde","Minute"],
            how="left"  
        )

    kapazitätsfaktoren = erzeugung_df[["Monat","Tag","Stunde","Minute","Kapazitätsfaktor_PV","Kapazitätsfaktor_Wind_Onshore","Kapazitätsfaktor_Wind_Offshore","Kapazitätsfaktor_Biomasse","Kapazitätsfaktor_Wasser","Kapazitätsfaktor_Sonstige"]]
    
    date_range = pd.date_range(start='01-01-2026 00:00', end='31-12-2045 23:45', freq='15min',tz='UTC')
    prognose = pd.DataFrame({'Datum von': date_range})
    
    prognose['Monat'] = prognose['Datum von'].dt.month
    prognose['Tag'] = prognose['Datum von'].dt.day
    prognose['Stunde'] = prognose['Datum von'].dt.hour
    prognose['Minute'] = prognose['Datum von'].dt.minute
    prognose['Jahr'] = prognose['Datum von'].dt.year
    
    prognose = prognose.merge(kapazitätsfaktoren, on=['Monat', 'Tag', 'Stunde', 'Minute'], how='left')

    maske_2030 = prognose["Jahr"] <= 2030
    maske_2045 = prognose["Jahr"] > 2030
    
    prognose.loc[maske_2030, "Installierte PV_GW"] = erzeugerarten["pv_dach"]["bestand"] + erzeugerarten["pv_frei"]["bestand"] + (zuwachsraten["zuwachs_2030"]["pv"] * ((prognose.loc[maske_2030, "Jahr"] - 2026) * 12 + prognose.loc[maske_2030, "Monat"]))
    prognose.loc[maske_2030, "Installierte Wind_Onshore_GW"] = erzeugerarten["wind_onshore"]["bestand"] + (zuwachsraten["zuwachs_2030"]["wind_onshore"] * ((prognose.loc[maske_2030, "Jahr"] - 2026) * 12 + prognose.loc[maske_2030, "Monat"]))
    prognose.loc[maske_2030, "Installierte Wind_Offshore_GW"] = erzeugerarten["wind_offshore"]["bestand"] + (zuwachsraten["zuwachs_2030"]["wind_offshore"] * ((prognose.loc[maske_2030, "Jahr"] - 2026) * 12 + prognose.loc[maske_2030, "Monat"]))
    prognose.loc[maske_2030, "Installierte Biomasse_GW"] = erzeugerarten["biomasse"]["bestand"] + (zuwachsraten["zuwachs_2030"]["biomasse"] * ((prognose.loc[maske_2030, "Jahr"] - 2026) * 12 + prognose.loc[maske_2030, "Monat"]))
    prognose.loc[maske_2030, "Installierte Wasser_GW"] = erzeugerarten["wasser"]["bestand"] + (zuwachsraten["zuwachs_2030"]["wasser"] * ((prognose.loc[maske_2030, "Jahr"] - 2026) * 12 + prognose.loc[maske_2030, "Monat"]))
    prognose.loc[maske_2030, "Installierte Sonstige_GW"] = erzeugerarten["sonstige"]["bestand"] + (zuwachsraten["zuwachs_2030"]["sonstige"] * ((prognose.loc[maske_2030, "Jahr"] - 2026) * 12 + prognose.loc[maske_2030, "Monat"]))
    
    prognose.loc[maske_2045, "Installierte PV_GW"] = installierte_2030["pv_dach"] + installierte_2030["pv_frei"] + (zuwachsraten["zuwachs_2045"]["pv"] * ((prognose.loc[maske_2045, "Jahr"] - 2031) * 12 + prognose.loc[maske_2045, "Monat"]))
    prognose.loc[maske_2045, "Installierte Wind_Onshore_GW"] = installierte_2030["wind_onshore"] + (zuwachsraten["zuwachs_2045"]["wind_onshore"] * ((prognose.loc[maske_2045, "Jahr"] - 2031) * 12 + prognose.loc[maske_2045, "Monat"]))
    prognose.loc[maske_2045, "Installierte Wind_Offshore_GW"] = installierte_2030["wind_offshore"] + (zuwachsraten["zuwachs_2045"]["wind_offshore"] * ((prognose.loc[maske_2045, "Jahr"] - 2031) * 12 + prognose.loc[maske_2045, "Monat"]))
    prognose.loc[maske_2045, "Installierte Biomasse_GW"] = installierte_2030["biomasse"] + (zuwachsraten["zuwachs_2045"]["biomasse"] * ((prognose.loc[maske_2045, "Jahr"] - 2031) * 12 + prognose.loc[maske_2045, "Monat"]))
    prognose.loc[maske_2045, "Installierte Wasser_GW"] = installierte_2030["wasser"] + (zuwachsraten["zuwachs_2045"]["wasser"] * ((prognose.loc[maske_2045, "Jahr"] - 2031) * 12 + prognose.loc[maske_2045, "Monat"]))
    prognose.loc[maske_2045, "Installierte Sonstige_GW"] = installierte_2030["sonstige"] + (zuwachsraten["zuwachs_2045"]["sonstige"] * ((prognose.loc[maske_2045, "Jahr"] - 2031) * 12 + prognose.loc[maske_2045, "Monat"]))

    prognose['PV_Prognose_MWh'] = prognose['Installierte PV_GW'] * 1000 * prognose['Kapazitätsfaktor_PV'] * 0.25 * (virtelstunden_steigerungsfaktoren['pv_dach']**(prognose['Jahr'] - 2025))
    prognose['Wind_Onshore_Prognose_MWh'] = prognose['Installierte Wind_Onshore_GW'] * 1000 * prognose['Kapazitätsfaktor_Wind_Onshore'] * 0.25 * (virtelstunden_steigerungsfaktoren['wind_onshore']**(prognose['Jahr'] - 2025))
    prognose['Wind_Offshore_Prognose_MWh'] = prognose['Installierte Wind_Offshore_GW'] * 1000 * prognose['Kapazitätsfaktor_Wind_Offshore'] * 0.25 * (virtelstunden_steigerungsfaktoren['wind_offshore']**(prognose['Jahr'] - 2025))
    prognose['Biomasse_Prognose_MWh'] = prognose['Installierte Biomasse_GW'] * 1000 * prognose['Kapazitätsfaktor_Biomasse'] * 0.25 * (virtelstunden_steigerungsfaktoren['biomasse']**(prognose['Jahr'] - 2025))
    prognose['Wasser_Prognose_MWh'] = prognose['Installierte Wasser_GW'] * 1000 * prognose['Kapazitätsfaktor_Wasser'] * 0.25 * (virtelstunden_steigerungsfaktoren['wasser']**(prognose['Jahr'] - 2025))
    prognose['Sonstige_Prognose_MWh'] = prognose['Installierte Sonstige_GW'] * 1000 * prognose['Kapazitätsfaktor_Sonstige'] * 0.25 * (virtelstunden_steigerungsfaktoren['sonstige']**(prognose['Jahr'] - 2025)) 
   
    prognose['PV_Prognose_MWh'] = prognose['PV_Prognose_MWh'].round(2)
    prognose['Wind_Onshore_Prognose_MWh'] = prognose['Wind_Onshore_Prognose_MWh'].round(2)
    prognose['Wind_Offshore_Prognose_MWh'] = prognose['Wind_Offshore_Prognose_MWh'].round(2)
    prognose['Biomasse_Prognose_MWh'] = prognose['Biomasse_Prognose_MWh'].round(2)
    prognose['Wasser_Prognose_MWh'] = prognose['Wasser_Prognose_MWh'].round(2)
    prognose['Sonstige_Prognose_MWh'] = prognose['Sonstige_Prognose_MWh'].round(2)
   
    # Speichere Prognose
    prognose_export = prognose[['Datum von', 'PV_Prognose_MWh', 'Wind_Onshore_Prognose_MWh', 'Wind_Offshore_Prognose_MWh','Biomasse_Prognose_MWh', 'Wasser_Prognose_MWh', 'Sonstige_Prognose_MWh']]
    prognose_export = prognose_export.rename(columns={
        'PV_Prognose_MWh': 'Photovoltaik [MWh] Originalauflösungen',
        'Wind_Onshore_Prognose_MWh': 'Wind Onshore [MWh] Originalauflösungen',
        'Wind_Offshore_Prognose_MWh': 'Wind Offshore [MWh] Originalauflösungen',
        'Biomasse_Prognose_MWh': 'Biomasse [MWh] Originalauflösungen',
        'Wasser_Prognose_MWh': 'Wasserkraft [MWh] Originalauflösungen',
        'Sonstige_Prognose_MWh': 'Sonstige Erneuerbare [MWh] Originalauflösungen'
    })

    spalten = ["Photovoltaik [MWh] Originalauflösungen","Wind Onshore [MWh] Originalauflösungen",
               "Wind Offshore [MWh] Originalauflösungen","Biomasse [MWh] Originalauflösungen",
               "Wasserkraft [MWh] Originalauflösungen","Sonstige Erneuerbare [MWh] Originalauflösungen"]
    
    prognose_export = prognose_export[["Datum von"] + spalten]

    if(prognose_export.isna().any().any()):
        print("Warnung: Es gibt fehlende Werte in der Erzeugungsprognose!"  )
        print(prognose_export.isna().sum())
        mask = prognose_export.isna() | prognose_export.isin([np.inf, -np.inf])
        print(prognose_export[mask.any(axis=1)])

    return prognose_export