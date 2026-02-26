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

E_FAHRZEUG_JAHR_MWH = 2.25  
WAERMEPUMPE_JAHR_MWH = 4

E_AUTOS_2025 = 1700000
WAERMEPUMPEN_2025 = 1950000

def Prognose_Verbrauch(verbrauchsprofil: json , lastprofil: bool ) -> pd.DataFrame:
    


    #=== Parameter in MWh umrechnen ===
    verbrauch_2030_MWh = verbrauchsprofil["Verbrauch_2030"] * 1e6
    verbrauch_2045_MWh = verbrauchsprofil["Verbrauch_2045"] * 1e6

    if  lastprofil:
        verbrauch_2030_MWh -= ((verbrauchsprofil["E_Autos_2030"] * E_FAHRZEUG_JAHR_MWH) + (verbrauchsprofil["WP_2030"] * WAERMEPUMPE_JAHR_MWH))
        verbrauch_2045_MWh -= ((verbrauchsprofil["E_Autos_2045"] * E_FAHRZEUG_JAHR_MWH) + (verbrauchsprofil["WP_2045"] * WAERMEPUMPE_JAHR_MWH))



    #==== Einlesen der Daten und anpassung ====
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
    verbrauch_df = verbrauch_df[verbrauch_df["Datum von"].dt.year == 2024]

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

    #=== Wachstumsrate bis 2030 berechnen ===
    
    # Berechne die Summe des Basisprofils über ein Normaljahr (365 Tage) als Startwert
    gesamtverbrauch_basisprofil = df_gesamt[df_gesamt["Jahr"] == 2026]["Netzlast [MWh] origin"].sum()
    
    # Interpoliere von der Basisprofil-Summe zum Zielwert 2030
    wachstumsrate_2030 = (verbrauch_2030_MWh - gesamtverbrauch_basisprofil) / (2030 - 2024)

    #=== Verbrauchsprognose berechnen ===
    
    # Berechne Anzahl Viertelstunden pro Jahr (Schaltjahre berücksichtigen)
    df_gesamt["Viertelstunden_im_Jahr"] = np.where(
        (df_gesamt["Jahr"] % 4 == 0) & ((df_gesamt["Jahr"] % 100 != 0) | (df_gesamt["Jahr"] % 400 == 0)),
        366 * 96,
        365 * 96
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

    gesamtverbrauch_2030_basisprofil = df_gesamt[df_gesamt["Jahr"] == 2030]["Netzlast_Prognose [MWh]"].sum()

    wachstumsrate_2045 = (verbrauch_2045_MWh - gesamtverbrauch_2030_basisprofil) / 15

    basisprofil_2030 = df_gesamt[df_gesamt["Jahr"] == 2030][["Jahr","Monat","Wochentag","Uhrzeit","Minute" ,"Netzlast_Prognose [MWh]"]].copy()

    profil_2030 = (basisprofil_2030.groupby(["Monat","Wochentag","Uhrzeit","Minute"]).mean().reset_index().rename(columns={"Netzlast_Prognose [MWh]": "Profil [MWh]"})
    )

    profil_2030 = profil_2030.drop(columns=["Jahr","Datum von"], errors='ignore')

    prognose_2045 = df_2045.merge(profil_2030, on=["Monat", "Wochentag", "Uhrzeit", "Minute"
        ], how='left'
    )

    prognose_2045["Viertelstunden_im_Jahr"] = np.where(
        (prognose_2045["Jahr"] % 4 == 0) & ((prognose_2045["Jahr"] % 100 != 0) | (prognose_2045["Jahr"] % 400 == 0)),
        366 * 96,
        365 * 96
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

        df_gesamt_2045 = lastprofil_wärmepumpe(
            anzahl_wärmepumpen={
                2030: verbrauchsprofil["WP_2030"],
                2045: verbrauchsprofil["WP_2045"]
            },
            gesamt_df=df_gesamt_2045
        )

    df_gesamt_2045 = df_gesamt_2045[["Datum von", "Netzlast [MWh]"]]
    df_gesamt_2045 = df_gesamt_2045.sort_values(by="Datum von").reset_index(drop=True)

    if(df_gesamt_2045.isna().any().any()):
        raise ValueError("Fehlende Werte in der Verbrauchsprognose entdeckt.")

    return df_gesamt_2045

def e_auto_Lastprofil(anzahl_e_autos:dict, gesamt_df:pd.DataFrame  ) -> pd.DataFrame:
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

    werktag_profil = werktage_e_autos.rename(columns={"Stunde": "Uhrzeit", "Szenario_B": "Profil_Werktag"})
    wochenende_profil = wochenende_e_autos.rename(columns={"Stunde": "Uhrzeit", "Szenario_B": "Profil_Wochenende"})
    
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
    
    # Profil enthält 24 Stundenwerte, die sich zu 1.0 pro Tag summieren
    # Für eine Viertelstunde: Profilwert × Jahresverbrauch / (365 Tage × 4 Viertelstunden pro Stunde)
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

def lastprofil_wärmepumpe(anzahl_wärmepumpen: dict, gesamt_df: pd.DataFrame) -> pd.DataFrame:
    """
    Erstellt auf Basis eines Lastprofils die Lastprognose für Wärmepumpen.
    :param anzahl_wärmepumpen: dict mit Anzahl der Wärmepumpen pro Jahr z.B. {2030: 5000000, 2045: 10000000}
    :param gesamt_df: DataFrame mit der Gesamtverbrauchsprognose
    :return: DataFrame mit der Wärmepumpen Lastprognose eingerechnet in die Gesamtverbrauchsprognose
    """

    df_aktuell = pd.read_csv(DATA_DIR / "Feste_Parameter" / "Wetter_aktuell.csv",sep=',',decimal='.')
    df_prognose = pd.read_csv(DATA_DIR / "Feste_Parameter" / "Wetter_prognose.csv",sep=',',decimal='.')

    df_aktuell['Datum'] = (
        '2025-' + df_aktuell['MM'].astype(int).astype(str) + '-' + 
        df_aktuell['DD'].astype(int).astype(str) + ' ' + 
        (df_aktuell['HH']-1).astype(int).astype(str) + ':00'
    )

    df_prognose['Datum'] = (
        '2031-' + df_prognose['MM'].astype(int).astype(str) + '-' + 
        df_prognose['DD'].astype(int).astype(str) + ' ' + 
        (df_prognose['HH']-1).astype(int).astype(str) + ':00'
    )

    lastprofil = pd.read_csv(DATA_DIR / "Feste_Parameter" / "Lastprofil_waermepumpe.csv", sep=';', decimal=',')
    lastprofil[['Uhrzeit', 'Minute']] = lastprofil['Zeit'].str.split('-', expand=True)[0].str.split(':', expand=True).astype(int)


    df_aktuell['Datum'] = pd.to_datetime(df_aktuell['Datum'])
    df_aktuell = df_aktuell.drop(columns=['RW','HW','MM','DD','HH','N','x','RF','B','D','A','E','IL','p','WR','WG'])
    df_prognose['Datum'] = pd.to_datetime(df_prognose['Datum'])
    df_prognose = df_prognose.drop(columns=['RW','HW','MM','DD','HH','N','x','RF','B','D','A','E','IL','p','WR','WG'])

    tages_temp_aktuell = df_aktuell.groupby(df_aktuell['Datum'].dt.date)['t'].mean().reset_index()
    tages_temp_aktuell.columns = ['Datum', 'Tages_Mittel_Temp']
    tages_temp_aktuell['Datum'] = pd.to_datetime(tages_temp_aktuell['Datum'])
    tages_temp_aktuell['Monat'] = tages_temp_aktuell['Datum'].dt.month
    tages_temp_aktuell['Tag'] = tages_temp_aktuell['Datum'].dt.day
    tages_temp_aktuell['Temp_Spalte'] = tages_temp_aktuell['Tages_Mittel_Temp'].clip(-14, 18).round().astype(int)
    
    # 29. Februar ergänzen (falls nicht vorhanden): Nutze Werte vom 28. Februar
    if not ((tages_temp_aktuell['Monat'] == 2) & (tages_temp_aktuell['Tag'] == 29)).any():
        feb28 = tages_temp_aktuell[(tages_temp_aktuell['Monat'] == 2) & (tages_temp_aktuell['Tag'] == 28)].copy()
        feb28['Tag'] = 29
        tages_temp_aktuell = pd.concat([tages_temp_aktuell, feb28], ignore_index=True)
    
    tages_temp_prognose = df_prognose.groupby(df_prognose['Datum'].dt.date)['t'].mean().reset_index()
    tages_temp_prognose.columns = ['Datum', 'Tages_Mittel_Temp']
    tages_temp_prognose['Datum'] = pd.to_datetime(tages_temp_prognose['Datum'])
    tages_temp_prognose['Monat'] = tages_temp_prognose['Datum'].dt.month
    tages_temp_prognose['Tag'] = tages_temp_prognose['Datum'].dt.day
    tages_temp_prognose['Temp_Spalte'] = tages_temp_prognose['Tages_Mittel_Temp'].clip(-14, 18).round().astype(int)
    
    # 29. Februar ergänzen (falls nicht vorhanden)
    if not ((tages_temp_prognose['Monat'] == 2) & (tages_temp_prognose['Tag'] == 29)).any():
        feb28 = tages_temp_prognose[(tages_temp_prognose['Monat'] == 2) & (tages_temp_prognose['Tag'] == 28)].copy()
        feb28['Tag'] = 29
        tages_temp_prognose = pd.concat([tages_temp_prognose, feb28], ignore_index=True)

    tmz_summe_jahr = np.maximum(19 - tages_temp_aktuell['Tages_Mittel_Temp'], 1).sum()
    a_wp = WAERMEPUMPE_JAHR_MWH / tmz_summe_jahr

    gesamt_df['Jahr'] = gesamt_df['Datum von'].dt.year
    gesamt_df['Monat'] = gesamt_df['Datum von'].dt.month
    gesamt_df['Tag'] = gesamt_df['Datum von'].dt.day
    gesamt_df['Uhrzeit'] = gesamt_df['Datum von'].dt.hour
    gesamt_df['Minute'] = gesamt_df['Datum von'].dt.minute
    
    gesamt_df["anzahl_wp"] = np.where(
        gesamt_df["Jahr"] <= 2030,
        WAERMEPUMPEN_2025 + (anzahl_wärmepumpen[2030] - WAERMEPUMPEN_2025) * (gesamt_df["Jahr"] - 2025) / (2030 - 2025),
        anzahl_wärmepumpen[2030] + (anzahl_wärmepumpen[2045] - anzahl_wärmepumpen[2030]) * (gesamt_df["Jahr"] - 2030) / (2045 - 2030)
    )

    gesamt_df_bis_2030 = gesamt_df[gesamt_df['Jahr'] <= 2030].copy()
    gesamt_df_ab_2031 = gesamt_df[gesamt_df['Jahr'] >= 2031].copy()
    
    gesamt_df_bis_2030 = gesamt_df_bis_2030.merge(
        tages_temp_aktuell[['Monat', 'Tag', 'Temp_Spalte']],
        on=['Monat', 'Tag'],
        how='left'
    )
    
    gesamt_df_ab_2031 = gesamt_df_ab_2031.merge(
        tages_temp_prognose[['Monat', 'Tag', 'Temp_Spalte']],
        on=['Monat', 'Tag'],
        how='left'
    )
    
    gesamt_df = pd.concat([gesamt_df_bis_2030, gesamt_df_ab_2031], ignore_index=True).sort_values('Datum von').reset_index(drop=True)

    lastprofil = lastprofil.drop(columns=['Zeit'])
    
    lastprofil_long = lastprofil.melt(
        id_vars=['Uhrzeit', 'Minute'], 
        var_name='Temp_Spalte', 
        value_name='profil_wert'
    )
    lastprofil_long['Temp_Spalte'] = lastprofil_long['Temp_Spalte'].astype(int)
    
    gesamt_df = gesamt_df.merge(
        lastprofil_long,
        on=['Uhrzeit', 'Minute', 'Temp_Spalte'],
        how='left'
    )
    
    gesamt_df['Wärmepumpe Last [MWh]'] = ( 
        gesamt_df['profil_wert'] * a_wp * gesamt_df["anzahl_wp"] / 4  
    )
    
    gesamt_df["Netzlast [MWh]"] += gesamt_df["Wärmepumpe Last [MWh]"]
    
    return gesamt_df.drop(columns=["Jahr", "Monat", "Tag", "Uhrzeit", "Minute", "Temp_Spalte","profil_wert", "anzahl_wp", "Wärmepumpe Last [MWh]"])




