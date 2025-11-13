"""
Zentrales Programm der Erzeugungsprognose von der Gruppe Pottkieker.
Nutzt Daten aus 2024 um eine Prognose bis 2045 zu erstellen.
Unterstützt durch KI (Claude Sonnet 4.5)
"""

import pandas as pd
import numpy as np
from config import PROJECT_ROOT #Ordnerverzeichnis in Config-Datei festgelegt, damit auf allen Geräten gleich

def Prognose_erzeugung(installierte_2030: dict, installierte_2045: dict) -> pd.DataFrame:
    """
    Funktion zur Prognose der Erneuerbaren Energieerzeugung von 2026 bis 2045 basierend auf dem Ausbaustand für verschiedene Energiequellen.
    Parameters:
        installierte_2030 (dict): Installierte Leistung für 2030 in GW. Schlüssel: 'pv', 'wind_onshore', 'wind_offshore', 'biomasse', 'wasser', 'sonstige'.
        installierte_2045 (dict): Installierte Leistung für 2045 in GW. Schlüssel: 'pv', 'wind_onshore', 'wind_offshore', 'biomasse', 'wasser', 'sonstige'.

    """
    #=== Feste Variablen ===
    map_wirkungsgrade = {
        "pv": 0.88,
        "wind_onshore": 0.95,
        "wind_offshore": 0.95,
        "biomasse": 0.95,
        "wasser": 0.92,
        "sonstige": 0.9
    }

    #=== Installierte Leistung in GW einlesen ===
    pfad = PROJECT_ROOT / "Daten" / "Feste_Parameter" / "Netto_Installiert_GW.csv"
    installierte_leistung_df = pd.read_csv(pfad, sep=';', decimal=',', low_memory=False)

    #=== Zuwachs pro Monat berechnen ===#
    # bis 2030
    zuwachsrate_pv_30 = (installierte_2030['pv']  - (installierte_leistung_df[(installierte_leistung_df["Jahr"]==2024) & (installierte_leistung_df["Monat"]==12)]["PV"] / map_wirkungsgrade["pv"])) / 72
    zuwachsrate_wind_onshore_30 = (installierte_2030['wind_onshore']  - (installierte_leistung_df[(installierte_leistung_df["Jahr"]==2024) & (installierte_leistung_df["Monat"]==12)]["Wind_onshore"] / map_wirkungsgrade["wind_onshore"])) / 72
    zuwachsrate_wind_offshore_30 = (installierte_2030['wind_offshore']  - (installierte_leistung_df[(installierte_leistung_df["Jahr"]==2024) & (installierte_leistung_df["Monat"]==12)]["Wind_offshore"] / map_wirkungsgrade["wind_offshore"])) / 72
    zuwachsrate_biomasse_30 = (installierte_2030['biomasse']  - (installierte_leistung_df[(installierte_leistung_df["Jahr"]==2024) & (installierte_leistung_df["Monat"]==12)]["Biomasse"] / map_wirkungsgrade["biomasse"])) / 72
    zuwachsrate_wasser_30 = (installierte_2030['wasser']  - (installierte_leistung_df[(installierte_leistung_df["Jahr"]==2024) & (installierte_leistung_df["Monat"]==12)]["Wasser"] / map_wirkungsgrade["wasser"])) / 72
    zuwachsrate_sonstige_30 = (installierte_2030['sonstige']  - (installierte_leistung_df[(installierte_leistung_df["Jahr"]==2024) & (installierte_leistung_df["Monat"]==12)]["Sonstige"] / map_wirkungsgrade["sonstige"])) / 72
    # bis 2045
    zuwachsrate_pv_45 = (installierte_2045['pv']  - installierte_2030['pv']) / 180
    zuwachsrate_wind_onshore_45 = (installierte_2045['wind_onshore']  - installierte_2030['wind_onshore']) / 180
    zuwachsrate_wind_offshore_45 = (installierte_2045['wind_offshore']  - installierte_2030['wind_offshore']) / 180
    zuwachsrate_biomasse_45 = (installierte_2045['biomasse']  - installierte_2030['biomasse']) / 180
    zuwachsrate_wasser_45 = (installierte_2045['wasser']  - installierte_2030['wasser']) / 180
    zuwachsrate_sonstige_45 = (installierte_2045['sonstige']  - installierte_2030['sonstige']) / 180
    
    #==== Einlesen der Daten und anpassung ====
    erzeugungpfad = PROJECT_ROOT / "Daten" / "SMARD-Daten"/ "erzeugung_2021.csv"
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
            erzeugung_df[col]  = erzeugung_df[col].fillna(0)

    erzeugung_df["Datum von"] = pd.to_datetime(erzeugung_df["Datum von"], format="%d.%m.%Y %H:%M")

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
    
    #=== Kapazitätsfaktoren berechnen ===
    erzeugung_df["Kapazitätsfaktor_PV"] = erzeugung_df["PV [MWh]"] / (installierte_leistung_PV_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Kapazitätsfaktor_Wind_Onshore"] = erzeugung_df["Wind Onshore [MWh]"] / (installierte_leistung_Wind_onshore_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Kapazitätsfaktor_Wind_Offshore"] = erzeugung_df["Wind Offshore [MWh]"] / (installierte_leistung_Wind_offshore_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Kapazitätsfaktor_Biomasse"] = erzeugung_df["Biomasse [MWh]"] / (installierte_leistung_Biomasse_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Kapazitätsfaktor_Wasser"] = erzeugung_df["Wasser [MWh]"] / (installierte_leistung_Wasser_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Kapazitätsfaktor_Sonstige"] = erzeugung_df["Sonstige [MWh]"] / (installierte_leistung_Sonstige_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle

    erzeugung_df["Monat"] = erzeugung_df["Datum von"].dt.month
    erzeugung_df["Tag"] = erzeugung_df["Datum von"].dt.day
    erzeugung_df["Stunde"] = erzeugung_df["Datum von"].dt.hour
    erzeugung_df["Minute"] = erzeugung_df["Datum von"].dt.minute

    kapazitätsfaktoren = erzeugung_df[["Monat","Tag","Stunde","Minute","Kapazitätsfaktor_PV","Kapazitätsfaktor_Wind_Onshore","Kapazitätsfaktor_Wind_Offshore","Kapazitätsfaktor_Biomasse","Kapazitätsfaktor_Wasser","Kapazitätsfaktor_Sonstige"]]
    
    # Erstelle Datumsbereich für 2026-2045
    date_range = pd.date_range(start='01-01-2026 00:00', end='31-12-2045 23:45', freq='15min')
    prognose = pd.DataFrame({'Datum von': date_range})
    
    prognose['Monat'] = prognose['Datum von'].dt.month
    prognose['Tag'] = prognose['Datum von'].dt.day
    prognose['Stunde'] = prognose['Datum von'].dt.hour
    prognose['Minute'] = prognose['Datum von'].dt.minute
    prognose['Jahr'] = prognose['Datum von'].dt.year

    # prognose = prognose[~((prognose['Monat'] == 2) & (prognose['Tag'] == 29))]

    
    prognose = prognose.merge(kapazitätsfaktoren, on=['Monat', 'Tag', 'Stunde', 'Minute'], how='left')

    # Berechne Erzeugung für jeden Zeitpunkt
    for jahr in range(2025, 2046):
        if(jahr <= 2030):
            zuwachsrate_pv = zuwachsrate_pv_30
            zuwachsrate_wind_onshore = zuwachsrate_wind_onshore_30
            zuwachsrate_wind_offshore = zuwachsrate_wind_offshore_30
            zuwachsrate_Biomasse = zuwachsrate_biomasse_30
            zuwachsrate_Wasser = zuwachsrate_wasser_30
            zuwachsrate_Sonstige = zuwachsrate_sonstige_30
            jahre_seit_start = jahr - 2021  
            zuwachs_pv = zuwachsrate_pv * jahre_seit_start
            zuwachs_wind_onshore = zuwachsrate_wind_onshore * jahre_seit_start
            zuwachs_wind_offshore = zuwachsrate_wind_offshore * jahre_seit_start
            zuwachs_Biomasse = zuwachsrate_Biomasse * jahre_seit_start
            zuwachs_Wasser = zuwachsrate_Wasser * jahre_seit_start
            zuwachs_Sonstige = zuwachsrate_Sonstige * jahre_seit_start
            installierte_leistung_pv = (installierte_leistung_PV_2021_GW  + zuwachs_pv) * 1000
            installierte_leistung_wind_onshore = (installierte_leistung_Wind_onshore_2021_GW  + zuwachs_wind_onshore) * 1000
            installierte_leistung_wind_offshore = (installierte_leistung_Wind_offshore_2021_GW  + zuwachs_wind_offshore) * 1000
            installierte_leistung_Biomasse = (installierte_leistung_Biomasse_2021_GW  + zuwachs_Biomasse) * 1000
            installierte_leistung_Wasser = (installierte_leistung_Wasser_2021_GW  + zuwachs_Wasser) * 1000
            installierte_leistung_Sonstige = (installierte_leistung_Sonstige_2021_GW  + zuwachs_Sonstige) * 1000
        elif(jahr <= 2045):
            zuwachsrate_pv = zuwachsrate_pv_45
            zuwachsrate_wind_onshore = zuwachsrate_wind_onshore_45
            zuwachsrate_wind_offshore = zuwachsrate_wind_offshore_45
            zuwachsrate_Biomasse = zuwachsrate_biomasse_45
            zuwachsrate_Wasser = zuwachsrate_wasser_45
            zuwachsrate_Sonstige = zuwachsrate_sonstige_45
            jahre_seit_start = jahr - 2030  
            zuwachs_pv = zuwachsrate_pv * jahre_seit_start
            zuwachs_wind_onshore = zuwachsrate_wind_onshore * jahre_seit_start
            zuwachs_wind_offshore = zuwachsrate_wind_offshore * jahre_seit_start
            zuwachs_Biomasse = zuwachsrate_Biomasse * jahre_seit_start
            zuwachs_Wasser = zuwachsrate_Wasser * jahre_seit_start
            zuwachs_Sonstige = zuwachsrate_Sonstige * jahre_seit_start
            installierte_leistung_pv = (installierte_2030['pv']  + zuwachs_pv) * 1000
            installierte_leistung_wind_onshore = (installierte_2030['wind_onshore']  + zuwachs_wind_onshore) * 1000
            installierte_leistung_wind_offshore = (installierte_2030['wind_offshore']  + zuwachs_wind_offshore) * 1000
            installierte_leistung_Biomasse = (installierte_2030['biomasse']  + zuwachs_Biomasse) * 1000
            installierte_leistung_Wasser = (installierte_2030['wasser']  + zuwachs_Wasser) * 1000
            installierte_leistung_Sonstige = (installierte_2030['sonstige']  + zuwachs_Sonstige) * 1000

        mask = prognose['Jahr'] == jahr
        prognose.loc[mask, 'PV_Prognose_MWh'] = (
            installierte_leistung_pv
            * prognose.loc[mask, 'Kapazitätsfaktor_PV'] * 0.25  
        )
        prognose.loc[mask, 'Wind_Onshore_Prognose_MWh'] = (
            installierte_leistung_wind_onshore 
            * prognose.loc[mask, 'Kapazitätsfaktor_Wind_Onshore'] * 0.25  
        )
        prognose.loc[mask, 'Wind_Offshore_Prognose_MWh'] = (
            installierte_leistung_wind_offshore
            * prognose.loc[mask, 'Kapazitätsfaktor_Wind_Offshore'] * 0.25
        )
        prognose.loc[mask, 'Biomasse_Prognose_MWh'] = (
            prognose.loc[mask, 'Kapazitätsfaktor_Biomasse'] * installierte_leistung_Biomasse * 0.25
        )
        prognose.loc[mask, 'Wasser_Prognose_MWh'] = (
            prognose.loc[mask, 'Kapazitätsfaktor_Wasser'] * installierte_leistung_Wasser * 0.25
        )
        prognose.loc[mask, 'Sonstige_Prognose_MWh'] = (
            prognose.loc[mask, 'Kapazitätsfaktor_Sonstige'] * installierte_leistung_Sonstige * 0.25
        )
   
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
    prognose_export[spalten] = prognose_export[spalten].interpolate(method='linear')
    
    prognose_export = prognose_export[["Datum von"] + spalten]

    if(prognose_export.isna().any().any()):
        print("Warnung: Es gibt fehlende Werte in der Erzeugungsprognose!"  )
        print(prognose_export.isna().sum())
        mask = prognose_export.isna() | prognose_export.isin([np.inf, -np.inf])
        print(prognose_export[mask.any(axis=1)])


    return prognose_export

# Prognose_erzeugung(0.068, 0.045, 0.09, 0, 0, 0)
# Prognose_erzeugung(0, 0, 0, 0, 0, 0)