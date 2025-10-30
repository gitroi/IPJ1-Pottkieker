import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def Prognose_PV(wachstumsrate_PV):
    #=== Variablen ===#
    installierte_leistung_PV_2024_MW = 101000  # Installierte Leistung PV in MW im Jahr 2024

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
                .str.replace(',', '.',regex=False),
                errors='coerce'
            )
            erzeugung_df[col] = erzeugung_df[col].fillna(0)

    erzeugung_df["Datum von"] = pd.to_datetime(erzeugung_df["Datum von"], format="%d.%m.%Y %H:%M")

    erzeugung_df = erzeugung_df[["Datum von", "Photovoltaik [MWh] Originalauflösungen"]]

    erzeugung_df = erzeugung_df.rename(columns={"Photovoltaik [MWh] Originalauflösungen": "PV [MWh]"})
    erzeugung_df["Crestfaktor_PV"] = erzeugung_df["PV [MWh]"] / (installierte_leistung_PV_2024_MW * 0.25)  # 0.25 da 15min Intervalle 

    # Extrahiere die Zeitkomponenten für das Mapping
    erzeugung_df["Monat"] = erzeugung_df["Datum von"].dt.month
    erzeugung_df["Tag"] = erzeugung_df["Datum von"].dt.day
    erzeugung_df["Stunde"] = erzeugung_df["Datum von"].dt.hour
    erzeugung_df["Minute"] = erzeugung_df["Datum von"].dt.minute

    # Erstelle Crestfaktoren-Profil
    crestfaktoren = erzeugung_df.groupby(["Monat", "Tag", "Stunde", "Minute"])["Crestfaktor_PV"].mean().reset_index()

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
    
    # Berechne PV-Erzeugung für jeden Zeitpunkt
    for jahr in range(2025, 2046):
        jahre_seit_start = jahr - 2024  # Startjahr ist 2024
        wachstumsfaktor = (1 + wachstumsrate_PV) ** jahre_seit_start
        installierte_leistung = installierte_leistung_PV_2024_MW * wachstumsfaktor
        
        mask = prognose['Jahr'] == jahr
        prognose.loc[mask, 'PV_Prognose_MWh'] = (
            installierte_leistung 
            * prognose.loc[mask, 'Crestfaktor_PV'] 
            * 0.25  # 15-Minuten-Intervall
        )
    
    # Speichere Prognose
    prognose_export = prognose[['Datum von', 'PV_Prognose_MWh']]
    prognose_export.to_csv('PV_Prognose_2026_2045.csv', index=False, sep=';', decimal=',')

    return prognose_export

# Beispielaufruf mit einer Wachstumsrate von 6,8%
pv_prognose = Prognose_PV(0.068)