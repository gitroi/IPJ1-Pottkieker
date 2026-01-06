"""
Zentrales Programm der Prognose von dem Verbrauch der Gruppe Pottkieker.
Nutzt Daten aus 2024 um eine Prognose bis 2045 zu erstellen.
Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
Programmiert von Joris Bürger
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from config import PROJECT_ROOT, DATA_DIR
import json

E_FAHRZEUG_JAHR_MWH = 2.25  # MWh pro E-Fahrzeug und Jahr

# CSV-Dateien einmal am Anfang laden um Rechenleistung zu verringern

#TODO: Richtigen Wert recherchieren
#BEISPIELWERTE
E_AUTOS_2025 = 2000000

def Prognose_Verbrauch(verbrauchsprofil: json , lastprofil: bool = True) -> pd.DataFrame:
    


    #=== Parameter in MWh umrechnen ===
    verbrauch_2030_MWh = verbrauchsprofil["Verbrauch_2030"] * 1e6
    verbrauch_2045_MWh = verbrauchsprofil["Verbrauch_2045"] * 1e6

    if not lastprofil:
        verbrauch_2030_MWh += verbrauchsprofil["E_Autos_2030"] * E_FAHRZEUG_JAHR_MWH
        verbrauch_2045_MWh += verbrauchsprofil["E_Autos_2045"] * E_FAHRZEUG_JAHR_MWH



    #==== Einlesen der Daten und anpassung ====
    # Pfad relativ zum Skript bestimmen
    verbrauchpfad = PROJECT_ROOT / "Daten" /"SMARD-Daten"/ "verbrauch_2024.csv"

    verbrauch_df = pd.read_csv(verbrauchpfad,
    sep=';',low_memory=False)

    verbrauch_df["Datum von"] = pd.to_datetime(verbrauch_df["Datum von"], format="%d.%m.%Y %H:%M")
    verbrauch_df["Datum von"] = verbrauch_df["Datum von"].dt.tz_localize("Europe/Berlin", ambiguous='infer').dt.tz_convert('UTC')

    verbrauch_df = verbrauch_df[["Datum von", "Netzlast [MWh] Originalauflösungen"]]\
    .rename(columns={"Netzlast [MWh] Originalauflösungen": "Netzlast [MWh] origin"})

    verbrauch_df["Netzlast [MWh] origin"] = pd.to_numeric(
    verbrauch_df["Netzlast [MWh] origin"].astype(str)
    .str.replace('.', '',regex=False)
    .str.replace(',', '.',regex=False)
    .str.replace('-', '0', regex=False),
    errors='coerce'
    )

    verbrauch_df["Monat"]= verbrauch_df["Datum von"].dt.month
    verbrauch_df["Wochentag"] = verbrauch_df["Datum von"].dt.dayofweek
    verbrauch_df["Uhrzeit"] = verbrauch_df["Datum von"].dt.hour
    verbrauch_df["Minute"] = verbrauch_df["Datum von"].dt.minute

    gesamtverbrauch_2024 = verbrauch_df["Netzlast [MWh] origin"].sum().round(2)    

    #=== Wachstumsrate bis 2030 berechnen ===

    #ziel = wachstumsrate * jahr + startwert -> wachstumsrate = (ziel - startwert) / jahr
    wachstumsrate_2030 = (verbrauch_2030_MWh - gesamtverbrauch_2024) / 6

    #=== profil für 2024 erstellen ===

    basisprofil_2024 = verbrauch_df.groupby(["Monat", "Wochentag", "Uhrzeit", "Minute"])[["Netzlast [MWh] origin"]].mean().reset_index()

    date_range = pd.date_range(start='01-01-2026 00:00', end='31-12-2030 23:45', freq='15min',tz='UTC')
    df_gesamt = pd.DataFrame({"Datum von": date_range})

    df_gesamt["Jahr"]= df_gesamt["Datum von"].dt.year
    df_gesamt["Monat"]= df_gesamt["Datum von"].dt.month
    df_gesamt["Wochentag"] = df_gesamt["Datum von"].dt.dayofweek
    df_gesamt["Uhrzeit"] = df_gesamt["Datum von"].dt.hour
    df_gesamt["Minute"] = df_gesamt["Datum von"].dt.minute

    df_gesamt = df_gesamt.merge(basisprofil_2024, on=["Monat", "Wochentag", "Uhrzeit", "Minute"
        ], how='left'
    )

    #=== Verbrauchsprognose berechnen ===
    
    # Berechne Anzahl Viertelstunden pro Jahr (Schaltjahre berücksichtigen)
    df_gesamt["Viertelstunden_im_Jahr"] = df_gesamt["Jahr"].apply(
        lambda jahr: 366 * 96 if (jahr % 4 == 0 and (jahr % 100 != 0 or jahr % 400 == 0)) else 365 * 96
    )

    df_gesamt["Netzlast_Prognose [MWh]"] = (
        df_gesamt["Netzlast [MWh] origin"] + 
        (wachstumsrate_2030 * (df_gesamt["Jahr"] - 2024)) / df_gesamt["Viertelstunden_im_Jahr"]
    )

    df_gesamt["Netzlast_Prognose [MWh]"] = df_gesamt["Netzlast_Prognose [MWh]"].round(2)

    #=== Erweitern bis 2045 ===

    date_range_2045 = pd.date_range(start='01-01-2031 00:00', end='31-12-2045 23:45', freq='15min',tz='UTC')
    df_2045 = pd.DataFrame({"Datum von": date_range_2045})

    df_2045["Jahr"]= df_2045["Datum von"].dt.year
    df_2045["Monat"]= df_2045["Datum von"].dt.month
    df_2045["Wochentag"] = df_2045["Datum von"].dt.dayofweek    
    df_2045["Uhrzeit"] = df_2045["Datum von"].dt.hour
    df_2045["Minute"] = df_2045["Datum von"].dt.minute

    #===  wachstumsfaktor für 2031 bis 2045 berechnen ===

    gesamtverbrauch_2030_berechnet = df_gesamt[df_gesamt["Jahr"] == 2030]["Netzlast_Prognose [MWh]"].sum()

    wachstumsrate_2045 = (verbrauch_2045_MWh - gesamtverbrauch_2030_berechnet ) / 15

    basisprofil_2030 = df_gesamt[df_gesamt["Jahr"] == 2030][["Jahr","Monat","Wochentag","Uhrzeit","Minute" ,"Netzlast_Prognose [MWh]"]].copy()

    profil_2030 = (basisprofil_2030.groupby(["Monat","Wochentag","Uhrzeit","Minute"]).mean().reset_index().rename(columns={"Netzlast_Prognose [MWh]": "Profil [MWh]"})
    )

    profil_2030 = profil_2030.drop(columns=["Jahr","Datum von"], errors='ignore')

    prognose_2045 = df_2045.merge(profil_2030, on=["Monat", "Wochentag", "Uhrzeit", "Minute"
        ], how='left'
    )

    prognose_2045["Viertelstunden_im_Jahr"] = prognose_2045["Jahr"].apply(
        lambda jahr: 366 * 96 if (jahr % 4 == 0 and (jahr % 100 != 0 or jahr % 400 == 0)) else 365 * 96
    )

    prognose_2045["Netzlast_Prognose [MWh]"] = (
        prognose_2045["Profil [MWh]"] + 
        (wachstumsrate_2045 * (prognose_2045["Jahr"] - 2030)) / prognose_2045["Viertelstunden_im_Jahr"]
    )

    prognose_2045 = prognose_2045.drop(columns=["Profil [MWh]", "Viertelstunden_im_Jahr"])

    prognose_2045["Netzlast_Prognose [MWh]"] = prognose_2045["Netzlast_Prognose [MWh]"].round(2)

    df_gesamt_2045 = pd.concat([df_gesamt, prognose_2045], ignore_index=True)
    df_gesamt_2045 = df_gesamt_2045.rename(columns={"Netzlast_Prognose [MWh]": "Netzlast [MWh]"})
    
    if lastprofil:
        df_gesamt_2045 = e_auto_Lastprofil(
            anzahl_e_autos={
                2030: verbrauchsprofil["E_Autos_2030"],
                2045: verbrauchsprofil["E_Autos_2045"]
            },
            gesamt_df=df_gesamt_2045
        )

    # lastprofil_wärmepumpe(4555, df_gesamt_2045)

    #=== Rückgabe des DataFrames nur mit den relevanten Spalten ===
    df_gesamt_2045 = df_gesamt_2045[["Datum von", "Netzlast [MWh]"]]
    if(df_gesamt_2045.isna().any().any()):
        print("Warnung: Es gibt fehlende Werte in der Verbrauchsprognose!"  )
        print(df_gesamt_2045.isna().sum())
        mask = df_gesamt_2045.isna() | df_gesamt_2045.isin([np.inf, -np.inf])
        print(df_gesamt_2045[mask.any(axis=1)])

    return df_gesamt_2045

def e_auto_Lastprofil(anzahl_e_autos:dict, gesamt_df:pd.DataFrame) -> pd.DataFrame:
    """
    Erstelltt auf basis eines Lastprofils die Lastprognose für E-Autos.
    :param anzahl_e_autos: dict mit Anzahl der E-Autos pro Jahr in 2030 und 2045 z.B. {2030: 1000000, 2045: 5000000}
    :param gesamt_df: DataFrame mit der Gesamtverbrauchsprognose
    :return: DataFrame mit der E-Auto Lastprognose eingerechnet in die Gesamtverbrauchsprognose
    """
    gesamt_df["Jahr"] = gesamt_df["Datum von"].dt.year
    gesamt_df["Monat"] = gesamt_df["Datum von"].dt.month
    gesamt_df["Wochentag"] = gesamt_df["Datum von"].dt.dayofweek
    gesamt_df["Uhrzeit"] = gesamt_df["Datum von"].dt.hour
    gesamt_df["Minute"] = gesamt_df["Datum von"].dt.minute

    with open(DATA_DIR / "Feste_Parameter" / "Wochenende_E_Autos.csv", "r") as f:
        wochenende_e_autos = pd.read_csv(f, sep=',',decimal='.')

    with open(DATA_DIR / "Feste_Parameter" / "Werktag_E_Autos.csv", "r") as f:
        werktage_e_autos = pd.read_csv(f, sep=',',decimal='.')

    if wochenende_e_autos["Zeitstempel"].str.contains("-").any():
        wochenende_e_autos["Zeitstempel"] = wochenende_e_autos["Zeitstempel"].str.split("-").str[0]
    wochenende_e_autos["Zeitstempel"] = pd.to_datetime(
        wochenende_e_autos["Zeitstempel"], format="%H:%M"
    )
    wochenende_e_autos["Stunde"] = wochenende_e_autos["Zeitstempel"].dt.hour

    if werktage_e_autos["Zeitstempel"].str.contains("-").any():
        werktage_e_autos["Zeitstempel"] = werktage_e_autos["Zeitstempel"].str.split("-").str[0]
    werktage_e_autos["Zeitstempel"] = pd.to_datetime(
        werktage_e_autos["Zeitstempel"], format="%H:%M"
    )
    werktage_e_autos["Stunde"] = werktage_e_autos["Zeitstempel"].dt.hour

    werktag_profil = werktage_e_autos.rename(columns={"Stunde": "Uhrzeit", "Szenario_C": "Profil_Werktag"})
    wochenende_profil = wochenende_e_autos.rename(columns={"Stunde": "Uhrzeit", "Szenario_C": "Profil_Wochenende"})
    
    gesamt_df = gesamt_df.merge(
        werktag_profil[["Uhrzeit", "Profil_Werktag"]], 
        on="Uhrzeit", 
        how="left"
    )
    gesamt_df = gesamt_df.merge(
        wochenende_profil[["Uhrzeit", "Profil_Wochenende"]], 
        on="Uhrzeit", 
        how="left"
    )
    
    # # Fehlerhaftes "s" oder andere Zeichen entfernen, falls vorhanden
    # if gesamt_df["Profil_Werktag"].dtype == 'object':
    #     gesamt_df["Profil_Werktag"] = gesamt_df["Profil_Werktag"].astype(str).str.replace(r'[^\d\.]', '', regex=True)
    # if gesamt_df["Profil_Wochenende"].dtype == 'object':
    #     gesamt_df["Profil_Wochenende"] = gesamt_df["Profil_Wochenende"].astype(str).str.replace(r'[^\d\.]', '', regex=True)
    
    # gesamt_df["Profil_Werktag"] = pd.to_numeric(gesamt_df["Profil_Werktag"], errors='coerce')
    # gesamt_df["Profil_Wochenende"] = pd.to_numeric(gesamt_df["Profil_Wochenende"], errors='coerce')
    
    gesamt_df["basis_last"] = np.where(
        gesamt_df["Wochentag"] >= 5, 
        gesamt_df["Profil_Wochenende"], 
        gesamt_df["Profil_Werktag"]
    ) * E_FAHRZEUG_JAHR_MWH / (365 * 4)
    
    gesamt_df["anzahl_autos"] = np.where(
        gesamt_df["Jahr"] <= 2030,
        E_AUTOS_2025 + (anzahl_e_autos[2030] - E_AUTOS_2025) * (gesamt_df["Jahr"] - 2025) / (2030 - 2025),
        anzahl_e_autos[2030] + (anzahl_e_autos[2045] - anzahl_e_autos[2030]) * (gesamt_df["Jahr"] - 2030) / (2045 - 2030)
    )
    
    gesamt_df["E-Auto Last [MWh]"] = gesamt_df["basis_last"] * gesamt_df["anzahl_autos"]
    
    gesamt_df = gesamt_df.drop(columns=["Profil_Werktag", "Profil_Wochenende", "basis_last", "anzahl_autos"])

    gesamt_df["Netzlast [MWh]"] += gesamt_df["E-Auto Last [MWh]"]

    return gesamt_df.drop(columns=["Jahr", "Monat", "Wochentag", "Uhrzeit", "Minute", "E-Auto Last [MWh]"])

def lastprofil_wärmepumpe(anzahl_wärmepumpen: int, gesamt_df: pd.DataFrame) -> pd.DataFrame:
    """
    Erstellt auf Basis eines Lastprofils die Lastprognose für Wärmepumpen.
    :param anzahl_wärmepumpen: Anzahl der Wärmepumpen
    :param gesamt_df: DataFrame mit der Gesamtverbrauchsprognose
    :return: DataFrame mit der Wärmepumpen Lastprognose eingerechnet in die Gesamtverbrauchsprognose
    """

    df_2015 = pd.read_csv(DATA_DIR / "Feste_Parameter" / "Wetter_2015.csv",sep=',',decimal='.')

    df_2015['Datum'] = pd.to_datetime(
        '2015-' + df_2015['MM'].astype(str) + '-' + 
        df_2015['DD'].astype(str) + ' ' + 
        df_2015['HH'].astype(str) + ':00:00'
    )
    df_2015.set_index('Datum', inplace=True)

    print(df_2015['t'].describe())