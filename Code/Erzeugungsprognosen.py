"""
Zentrales Programm der Erzeugungsprognose von der Gruppe Pottkieker.
Nutzt Daten aus 2024 um eine Prognose bis 2045 zu erstellen.
Unterstützt durch KI (Claude Sonnet 4.5)
"""

import pandas as pd
import numpy as np
from config import PROJECT_ROOT #Ordnerverzeichnis in Config-Datei festgelegt, damit auf allen Geräten gleich

def Prognose_erzeugung(installierte_Leistung_pv_GW, installierte_Leistung_wind_onshore_GW, installierte_Leistung_wind_offshore_GW, installierte_Leistung_Biomasse_GW, installierte_Leistung_Wasser_GW, installierte_Leistung_Sonstige_GW):
    """
    Funktion zur Prognose der Erneuerbaren Energieerzeugung von 2026 bis 2045 basierend auf dem Ausbaustand für verschiedene Energiequellen.
    Parameters:
    installierte_Leistung_pv_GW (float): Installierte Leistung für Photovoltaik in GW im Jahr 2045.
    installierte_Leistung_wind_onshore_GW (float): Installierte Leistung für Wind Onshore in GW im Jahr 2045.
    installierte_Leistung_wind_offshore_GW (float): Installierte Leistung für Wind Offshore in GW im Jahr 2045.
    installierte_Leistung_Biomasse_GW (float): Installierte Leistung für Biomasse in GW im Jahr 2045.
    installierte_Leistung_Wasser_GW (float): Installierte Leistung für Wasserkraft in GW im Jahr 2045.
    installierte_Leistung_Sonstige_GW (float): Installierte Leistung für Sonstige Erneuerbare in GW im Jahr 2045.

    """
    #=== Variablen ===#
    installierte_leistung_PV_2021_GW = 60  
    installierte_leistung_Wind_onshore_2021_GW = 56
    installierte_leistung_Wind_offshore_2021_GW = 8
    installierte_leistung_Biomasse_2021_GW = 9  
    installierte_leistung_Wasser_2021_GW = 5    
    installierte_leistung_Sonstige_2021_GW = 3

    #=== wachstumsraten berechnen ===#
    wachstumsrate_pv = (installierte_Leistung_pv_GW  / installierte_leistung_PV_2021_GW) ** (1/24) - 1
    wachstumsrate_wind_onshore = (installierte_Leistung_wind_onshore_GW  / installierte_leistung_Wind_onshore_2021_GW) ** (1/24) - 1
    wachstumsrate_wind_offshore = (installierte_Leistung_wind_offshore_GW  / installierte_leistung_Wind_offshore_2021_GW) ** (1/24) - 1
    wachstumsrate_Biomasse = (installierte_Leistung_Biomasse_GW  / installierte_leistung_Biomasse_2021_GW) ** (1/24) - 1
    wachstumsrate_Wasser = (installierte_Leistung_Wasser_GW  / installierte_leistung_Wasser_2021_GW) ** (1/24) - 1
    wachstumsrate_Sonstige = (installierte_Leistung_Sonstige_GW  / installierte_leistung_Sonstige_2021_GW) ** (1/24) - 1

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

    erzeugung_df = erzeugung_df[~((erzeugung_df["Datum von"].dt.month == 2) & (erzeugung_df["Datum von"].dt.day == 29))]
    erzeugung_df = erzeugung_df.drop_duplicates("Datum von").reset_index(drop=True)

    # WICHTIG: Kein inplace=True mit Zuweisung verwenden, da dies None zurückgibt
    erzeugung_df = erzeugung_df.rename(columns={
        "Photovoltaik [MWh] Originalauflösungen": "PV [MWh]",
        "Wind Onshore [MWh] Originalauflösungen": "Wind Onshore [MWh]",
        "Wind Offshore [MWh] Originalauflösungen": "Wind Offshore [MWh]",
        "Biomasse [MWh] Originalauflösungen": "Biomasse [MWh]",
        "Wasserkraft [MWh] Originalauflösungen": "Wasser [MWh]",
        "Sonstige Erneuerbare [MWh] Originalauflösungen": "Sonstige [MWh]"
    })
    erzeugung_df["Kapazitätsfaktor_PV"] = erzeugung_df["PV [MWh]"] / (installierte_leistung_PV_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Kapazitätsfaktor_Wind_Onshore"] = erzeugung_df["Wind Onshore [MWh]"] / (installierte_leistung_Wind_onshore_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Kapazitätsfaktor_Wind_Offshore"] = erzeugung_df["Wind Offshore [MWh]"] / (installierte_leistung_Wind_offshore_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Kapazitätsfaktor_Biomasse"] = erzeugung_df["Biomasse [MWh]"] / (installierte_leistung_Biomasse_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Kapazitätsfaktor_Wasser"] = erzeugung_df["Wasser [MWh]"] / (installierte_leistung_Wasser_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Kapazitätsfaktor_Sonstige"] = erzeugung_df["Sonstige [MWh]"] / (installierte_leistung_Sonstige_2021_GW * 1000 * 0.25)  # 0.25 da 15min Intervalle


    # Extrahiere die Zeitkomponenten für das Mapping
    erzeugung_df["Monat"] = erzeugung_df["Datum von"].dt.month
    erzeugung_df["Tag"] = erzeugung_df["Datum von"].dt.day
    erzeugung_df["Stunde"] = erzeugung_df["Datum von"].dt.hour
    erzeugung_df["Minute"] = erzeugung_df["Datum von"].dt.minute

    # Erstelle Kapazitätsfaktoren-Profil
    kapazitätsfaktoren = erzeugung_df[["Monat","Tag","Stunde","Minute","Kapazitätsfaktor_PV","Kapazitätsfaktor_Wind_Onshore","Kapazitätsfaktor_Wind_Offshore","Kapazitätsfaktor_Biomasse","Kapazitätsfaktor_Wasser","Kapazitätsfaktor_Sonstige"]]
    
    # Erstelle Datumsbereich für 2026-2045
    date_range = pd.date_range(start='01-01-2026 00:00', end='31-12-2045 23:45', freq='15min')
    prognose = pd.DataFrame({'Datum von': date_range})
    
    # Extrahiere Zeitkomponenten für die Prognose
    prognose['Monat'] = prognose['Datum von'].dt.month
    prognose['Tag'] = prognose['Datum von'].dt.day
    prognose['Stunde'] = prognose['Datum von'].dt.hour
    prognose['Minute'] = prognose['Datum von'].dt.minute
    prognose['Jahr'] = prognose['Datum von'].dt.year
    
    prognose = prognose[~((prognose['Monat'] == 2) & (prognose['Tag'] == 29))]  

    # Merge mit Crestfaktoren
    prognose = prognose.merge(kapazitätsfaktoren, on=['Monat', 'Tag', 'Stunde', 'Minute'], how='left')

    # Berechne Erzeugung für jeden Zeitpunkt
    for jahr in range(2025, 2046):
        jahre_seit_start = jahr - 2021  # Startjahr ist 2021
        wachstumsfaktor_pv = (1 + wachstumsrate_pv) ** jahre_seit_start
        wachstumsfaktor_wind_onshore = (1 + wachstumsrate_wind_onshore) ** jahre_seit_start
        wachstumsfaktor_wind_offshore = (1 + wachstumsrate_wind_offshore) ** jahre_seit_start
        wachstumsfaktor_Biomasse = (1 + wachstumsrate_Biomasse) ** jahre_seit_start
        wachstumsfaktor_Wasser = (1 + wachstumsrate_Wasser) ** jahre_seit_start
        wachstumsfaktor_Sonstige = (1 + wachstumsrate_Sonstige) ** jahre_seit_start
        installierte_leistung_pv = installierte_leistung_PV_2021_GW * 1000 * wachstumsfaktor_pv
        installierte_leistung_wind_onshore = installierte_leistung_Wind_onshore_2021_GW * 1000 * wachstumsfaktor_wind_onshore
        installierte_leistung_wind_offshore = installierte_leistung_Wind_offshore_2021_GW * 1000 * wachstumsfaktor_wind_offshore
        installierte_leistung_Biomasse = installierte_leistung_Biomasse_2021_GW * 1000 * wachstumsfaktor_Biomasse
        installierte_leistung_Wasser = installierte_leistung_Wasser_2021_GW * 1000 * wachstumsfaktor_Wasser
        installierte_leistung_Sonstige = installierte_leistung_Sonstige_2021_GW * 1000 * wachstumsfaktor_Sonstige

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

   # Werte auf 2 Nachkommastellen runden
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

    # Interpolation auf den numerischen Spalten 
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