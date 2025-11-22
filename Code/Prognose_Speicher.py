"""
Zentrales Programm der Prognose vom Stromspeicher.
Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
"""
import pandas as pd
import numpy as np
import json
from functools import reduce
from dataclasses import dataclass
from config import PROJECT_ROOT


def Verlauf_Speicher(verbrauchsprognose, erzeugungsprognose, entladegrenze, ladegrenze):
    """
    Simuliert den Verlauf mit Erzeugung, Verbrauch und Speichern.
    """

    fixparameterBatterie = Einlesen_Speicherdaten_fix("batterie")
    fixparameterEAuto = Einlesen_Speicherdaten_fix("e-auto")
    fixparameterSchwungrad = Einlesen_Speicherdaten_fix("schwungrad")
    fixparameterWasserstoff = Einlesen_Speicherdaten_fix("wasserstoff")
    fixparameterPumpspeicher = Einlesen_Speicherdaten_fix("pumpspeicher")

    bestandBatterie = fixparameterBatterie.bestand
    bestandEAuto = fixparameterEAuto.bestand
    bestandSchwungrad = fixparameterSchwungrad.bestand
    bestandWasserstoff = fixparameterWasserstoff.bestand
    bestandPumpspeicher = fixparameterPumpspeicher.bestand

    szenarioBatterie = 0 #TODO: Speicherdaten aus Szenario einfügen
    szenarioEAuto = 0 #TODO: Speicherdaten aus Szenario einfügen
    szenarioSchwungrad = 0 #TODO: Speicherdaten aus Szenario einfügen
    szenarioWasserstoff = 0 #TODO: Speicherdaten aus Szenario einfügen
    szenarioPumpspeicher = 0 #TODO: Speicherdaten aus Szenario einfügen

    gesamtAusbau = Prognose_Gesamt_Ausbau_(bestandBatterie, bestandEAuto, bestandSchwungrad, bestandWasserstoff, bestandPumpspeicher, 100, 200, 100, 200, 100, 200, 100, 200, 100, 200)


def Einlesen_Speicherdaten_fix(speicherart):
    """
    Liest alle festen Parameter einer Speicherart aus einer JSON-Datei ein
    """

    @dataclass
    class Speicher:
        bestand: float
        wirkungsgrad: float
        capex: float
        opex: float
        verluste: float
        leistung: float
        obergrenze: float
        untergrenze: float
    
    with open(PROJECT_ROOT / "Daten" / "Feste_Parameter" / "speicherarten.json", "r") as f:
        data = json.load(f)

    speicher_data = data.get(speicherart)
    if speicher_data is None:
        raise ValueError(f"Speicherart '{speicherart}' nicht in der JSON-Datei gefunden.")

    speicher = Speicher(**speicher_data)

    return speicher

def Prognose_Speicher_Ausbau(speicherart, bestand2025, bestand2030, bestand2045):
    """
    Berechnet den Verlauf des Speicherausbaus einer Speicherart
    """

    #=== Kapazitäten in MWh umrechnen ===
    bestand2025 = bestand2025 * 1e3
    bestand2030 = bestand2030 * 1e3
    bestand2045 = bestand2045 * 1e3

    #=== Dataframe für die Jahre 2026 bis 2030 erstellen ===
    date_range = pd.date_range(start='2026-01-01', end='2030-12-31 23:45', freq='15min')
    df_2030 = pd.DataFrame({'Datum': date_range})

    df_2030["Jahr"] = df_2030["Datum"].dt.year
    df_2030["Monat"]= df_2030["Datum"].dt.month
    df_2030["Wochentag"] = df_2030["Datum"].dt.dayofweek
    df_2030["Uhrzeit"] = df_2030["Datum"].dt.hour
    df_2030["Minute"] = df_2030["Datum"].dt.minute

    anzahl_tage_2030 = len(df_2030["Datum"].dt.date.unique())
    
    wachstumsrate_2030 = (bestand2030 - bestand2025) / anzahl_tage_2030

    speichername = f"Speicherkapazität {speicherart} [MWh]"
    
    df_2030[speichername] = bestand2025 + wachstumsrate_2030 * ((df_2030['Datum'] - df_2030['Datum'].min()).dt.days + 1)

    # df_2030.to_csv(PROJECT_ROOT / 'Daten' / 'speicherprognosetest2030.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    #=== Dataframe für die Jahre 2030 bis 2045 erstellen ===
    date_range = pd.date_range(start='2031-01-01', end='2045-12-31 23:45', freq='15min')
    df_2045 = pd.DataFrame({'Datum': date_range})

    df_2045["Jahr"] = df_2045["Datum"].dt.year
    df_2045["Monat"]= df_2045["Datum"].dt.month
    df_2045["Wochentag"] = df_2045["Datum"].dt.dayofweek
    df_2045["Uhrzeit"] = df_2045["Datum"].dt.hour
    df_2045["Minute"] = df_2045["Datum"].dt.minute

    anzahl_tage_2045 = len(df_2045["Datum"].dt.date.unique())
    
    wachstumsrate_2045 = (bestand2045 - bestand2030) / anzahl_tage_2045

    df_2045[speichername] = bestand2030 + wachstumsrate_2045 * ((df_2045['Datum'] - df_2045['Datum'].min()).dt.days + 1)

    df_gesamt = pd.concat([df_2030, df_2045], ignore_index=True) # Bereich von 2026 bis 2030 und 2031 bis 2045 zusammenfügen
    df_gesamt[speichername] = df_gesamt[speichername].round(2)

    # df_gesamt.to_csv(PROJECT_ROOT / 'Daten' / 'speicherprognosetestgesamt.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    return df_gesamt

def Prognose_Gesamt_Ausbau_(bestandBatterie, bestandEAuto, bestandSchwungrad, bestandWasserstoff, bestandPumpspeicher, Batterie30, Batterie45, EAuto30, EAuto45, Schwungrad30, Schwungrad45, Wasserstoff30, Wasserstoff45, Pumpspeicher30, Pumpspeicher45):
    """
    Erstellt die Gesamtprognose für alle Speicherarten
    """

    #bestandBatterie30 = szenarioBatterie.bestand_2030
    #bestandBatterie45 = szenarioBatterie.bestand_2045
    #bestandEAuto30 = szenarioEAuto.bestand_2030
    #bestandEAuto45 = szenarioEAuto.bestand_2045
    #bestandSchwungrad30 = szenarioSchwungrad.bestand_2030
    #bestandSchwungrad45 = szenarioSchwungrad.bestand_
    #bestandWasserstoff30 = szenarioWasserstoff.bestand_2030
    #bestandWasserstoff45 = szenarioWasserstoff.bestand_2045
    #bestandPumpspeicher30 = szenarioPumpspeicher.bestand_2030
    #bestandPumpspeicher45 = szenarioPumpspeicher.bestand_2045

    df_batterie = Prognose_Speicher_Ausbau("Batterie", bestandBatterie, Batterie30, Batterie45)
    # df_auto = Prognose_Speicher_Ausbau("E-Auto", bestandEAuto, EAuto30, EAuto45) erstmal rausgenommen, da unklar ist, wie hier gerechnet werden soll
    df_schwungrad = Prognose_Speicher_Ausbau("Schwungrad", bestandSchwungrad, Schwungrad30, Schwungrad45)
    df_wasserstoff = Prognose_Speicher_Ausbau("Wasserstoff", bestandWasserstoff, Wasserstoff30, Wasserstoff45)
    df_pump = Prognose_Speicher_Ausbau("Pumpspeicher", bestandPumpspeicher, Pumpspeicher30, Pumpspeicher45)

    dfs = [df_batterie, df_schwungrad, df_wasserstoff, df_pump] # Auto rausgenommen

    # Merge alle DataFrames auf gemeinsamen Spalten
    df_ausbau = reduce(
        lambda left, right: left.merge(
            right, 
            on=['Datum', 'Jahr', 'Monat', 'Wochentag', 'Uhrzeit', 'Minute'], 
            how='outer'
        ), 
        dfs
    )

    # df_ausbau.to_csv(PROJECT_ROOT / 'Daten' / 'speicherprognosetestgesamt.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    return df_ausbau
