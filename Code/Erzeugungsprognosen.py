import pandas as pd
import numpy as np

def Prognose_erzeugung(wachstumsrate_pv, wachstumsrate_wind_onshore, wachstumsrate_wind_offshore, wachstumsrate_Biomasse, wachstumsrate_Wasser, wachstumsrate_Sonstige):
    #=== Variablen ===#
    installierte_leistung_PV_2024_MW = 101000  # Installierte Leistung PV in MW im Jahr 2024
    installierte_leistung_Wind_onshore_2024_MW = 64000
    installierte_leistung_Wind_offshore_2024_MW = 9000
    installierte_leistung_Biomasse_2024_MW = 9000  # Installierte Leistung Biomasse in MW im Jahr 2024
    installierte_leistung_Wasser_2024_MW = 5000    # Installierte Leistung Wasser in MW im Jahr 2024
    installierte_leistung_Sonstige_2024_MW = 3000   # Installierte Leistung Sonstige in MW im Jahr 2024

    #==== Einlesen der Daten und anpassung ====
    erzeugungpfad = "C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\erzeugung_2024.csv"
    erzeugung_df = pd.read_csv(erzeugungpfad,
    sep=';', decimal=',', parse_dates=['Datum von'],
    dayfirst=True, low_memory=False
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
    erzeugung_df["Crestfaktor_PV"] = erzeugung_df["PV [MWh]"] / (installierte_leistung_PV_2024_MW * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Crestfaktor_Wind_onshore"] = erzeugung_df["Wind Onshore [MWh]"] / (installierte_leistung_Wind_onshore_2024_MW * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Crestfaktor_Wind_offshore"] = erzeugung_df["Wind Offshore [MWh]"] / (installierte_leistung_Wind_offshore_2024_MW * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Crestfaktor_Biomasse"] = erzeugung_df["Biomasse [MWh]"] / (installierte_leistung_Biomasse_2024_MW * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Crestfaktor_Wasser"] = erzeugung_df["Wasser [MWh]"] / (installierte_leistung_Wasser_2024_MW * 0.25)  # 0.25 da 15min Intervalle
    erzeugung_df["Crestfaktor_Sonstige"] = erzeugung_df["Sonstige [MWh]"] / (installierte_leistung_Sonstige_2024_MW * 0.25)  # 0.25 da 15min Intervalle


    # Extrahiere die Zeitkomponenten für das Mapping
    erzeugung_df["Monat"] = erzeugung_df["Datum von"].dt.month
    erzeugung_df["Tag"] = erzeugung_df["Datum von"].dt.day
    erzeugung_df["Stunde"] = erzeugung_df["Datum von"].dt.hour
    erzeugung_df["Minute"] = erzeugung_df["Datum von"].dt.minute

    # Erstelle Crestfaktoren-Profil
    crestfaktoren = erzeugung_df.groupby(["Monat", "Tag", "Stunde", "Minute"])[["Crestfaktor_PV","Crestfaktor_Wind_onshore","Crestfaktor_Wind_offshore","Crestfaktor_Biomasse","Crestfaktor_Wasser","Crestfaktor_Sonstige"]].mean().reset_index()

    # Erstelle Datumsbereich für 2026-2045
    date_range = pd.date_range(start='2025-01-01 00:00', end='2045-12-31 23:45', freq='15min')
    prognose = pd.DataFrame({'Datum von': date_range})
    
    # Extrahiere Zeitkomponenten für die Prognose
    prognose['Monat'] = prognose['Datum von'].dt.month
    prognose['Tag'] = prognose['Datum von'].dt.day
    prognose['Stunde'] = prognose['Datum von'].dt.hour
    prognose['Minute'] = prognose['Datum von'].dt.minute
    prognose['Jahr'] = prognose['Datum von'].dt.year
    
    # Merge mit Crestfaktoren
    prognose = prognose.merge(crestfaktoren, on=['Monat', 'Tag', 'Stunde', 'Minute'], how='left')

    # Berechne Erzeugung für jeden Zeitpunkt
    for jahr in range(2025, 2046):
        jahre_seit_start = jahr - 2024  # Startjahr ist 2024
        wachstumsfaktor_pv = (1 + wachstumsrate_pv) ** jahre_seit_start
        wachstumsfaktor_wind_onshore = (1 + wachstumsrate_wind_onshore) ** jahre_seit_start
        wachstumsfaktor_wind_offshore = (1 + wachstumsrate_wind_offshore) ** jahre_seit_start
        wachstumsfaktor_Biomasse = (1 + wachstumsrate_Biomasse) ** jahre_seit_start
        wachstumsfaktor_Wasser = (1 + wachstumsrate_Wasser) ** jahre_seit_start
        wachstumsfaktor_Sonstige = (1 + wachstumsrate_Sonstige) ** jahre_seit_start
        installierte_leistung_pv = installierte_leistung_PV_2024_MW * wachstumsfaktor_pv
        installierte_leistung_wind_onshore = installierte_leistung_Wind_onshore_2024_MW * wachstumsfaktor_wind_onshore
        installierte_leistung_wind_offshore = installierte_leistung_Wind_offshore_2024_MW * wachstumsfaktor_wind_offshore
        installierte_leistung_Biomasse = installierte_leistung_Biomasse_2024_MW * wachstumsfaktor_Biomasse
        installierte_leistung_Wasser = installierte_leistung_Wasser_2024_MW * wachstumsfaktor_Wasser
        installierte_leistung_Sonstige = installierte_leistung_Sonstige_2024_MW * wachstumsfaktor_Sonstige
        
        mask = prognose['Jahr'] == jahr
        prognose.loc[mask, 'PV_Prognose_MWh'] = (
            installierte_leistung_pv
            * prognose.loc[mask, 'Crestfaktor_PV'] * 0.25  # 15-Minuten-Intervall
        )
        prognose.loc[mask, 'Wind_Onshore_Prognose_MWh'] = (
            installierte_leistung_wind_onshore 
            * prognose.loc[mask, 'Crestfaktor_Wind_onshore'] * 0.25  # 15-Minuten-Intervall
        )
        prognose.loc[mask, 'Wind_Offshore_Prognose_MWh'] = (
            installierte_leistung_wind_offshore 
            * prognose.loc[mask, 'Crestfaktor_Wind_offshore'] * 0.25  # 15-Minuten-Intervall
        )
        prognose.loc[mask, 'Biomasse_Prognose_MWh'] = (
            prognose.loc[mask, 'Crestfaktor_Biomasse'] * installierte_leistung_Biomasse * 0.25
        )
        prognose.loc[mask, 'Wasser_Prognose_MWh'] = (
            prognose.loc[mask, 'Crestfaktor_Wasser'] * installierte_leistung_Wasser * 0.25
        )
        prognose.loc[mask, 'Sonstige_Prognose_MWh'] = (
            prognose.loc[mask, 'Crestfaktor_Sonstige'] * installierte_leistung_Sonstige * 0.25
        )

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
    prognose_export.to_csv('C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\Erzeugungs_Prognose_2026_2045.csv', index=False, sep=';', decimal=',')

    return prognose_export

Prognose_erzeugung(0.068, 0.045, 0.09, 0, 0, 0)