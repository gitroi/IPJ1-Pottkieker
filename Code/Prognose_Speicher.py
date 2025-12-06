"""
Zentrales Programm der Prognose vom Stromspeicher.
Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
Programmiert von Robin Matzke
"""
import pandas as pd
import numpy as np
import json
from functools import reduce
from dataclasses import dataclass
from config import PROJECT_ROOT


#TODO : Andere Grenzen für 2026-2030 und 2031-2045 einbauen?
def Verlauf_Speicher(df_anteilEE: pd.DataFrame, entladegrenze: float, ladegrenze: float, ziele_2030: dict, ziele_2045: dict ) -> pd.DataFrame:
    """
    Simuliert den Verlauf mit Erzeugung, Verbrauch und Speichern.
    """

    fixparameterBatterie = Einlesen_Speicherdaten_fix("batterie")
    fixparameterWasserstoff = Einlesen_Speicherdaten_fix("wasserstoff")
    fixparameterPumpspeicher = Einlesen_Speicherdaten_fix("pumpspeicher")

    bestandBatterie = fixparameterBatterie.bestand
    bestandWasserstoff = fixparameterWasserstoff.bestand
    bestandPumpspeicher = fixparameterPumpspeicher.bestand
    
    # Ist in nicht mehr nötig, da die Bestände aus den Fixparametern gelesen werden in der Methode
    # szenarioBatterie = 0 #TODO: Speicherdaten aus Szenario einfügen
    # szenarioWasserstoff = 0 #TODO: Speicherdaten aus Szenario einfügen
    # szenarioPumpspeicher = 0 #TODO: Speicherdaten aus Szenario einfügen

    df_gesamtAusbau = Prognose_Gesamt_Ausbau_(bestandBatterie, bestandWasserstoff, bestandPumpspeicher, ziele_2030["Ausbau Speicher"]["batteriespeicher"], ziele_2045["Ausbau Speicher"]["batteriespeicher"], ziele_2030["Ausbau Speicher"]["wasserstoff"], ziele_2045["Ausbau Speicher"]["wasserstoff"], ziele_2030["Ausbau Speicher"]["pumpspeicher"], ziele_2045["Ausbau Speicher"]["pumpspeicher"])

    dfs = [df_anteilEE, df_gesamtAusbau] 

    # Merge alle DataFrames auf gemeinsamen Spalten
    df_gesamtVerlauf = reduce(
        lambda left, right: left.merge(
            right, 
            on=['Datum von'], 
            how='outer'
        ), 
        dfs
    )
    
    # df_gesamtVerlauf.to_csv(PROJECT_ROOT / 'Daten' / 'debug_gesamtverlauf.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    # Listen für Ergebnisse initialisieren
    speicherstand_batterie = []
    speicherstand_wasserstoff = []
    speicherstand_pumpspeicher = []
    zusatz_energie = [] # Energie, die von den Speichern geliefert wird, und somit die EE-Abdeckung erhöht

    # Anfangswerte Ladestand(Annahme: 25% geladen im Januar 2026)
    aktuell_batterie = bestandBatterie*0.25*1e3 
    aktuell_wasserstoff = bestandWasserstoff*0.25*1e3
    aktuell_pumpspeicher = bestandPumpspeicher*0.25*1e3
    aktuell_zusatz_energie = 0 # Energie, die von den Speichern geliefert wird, und somit die EE-Abdeckung erhöht

    # Export/Import über den gesamten Zeitraum
    exportEnergie = 0
    importEnergie = 0


    # Simulation über alle Zeitpunkte, Leistung durch 4 um auf 15min zu kommen, Wirkungsgrad nur bei Entladung berücksichtigt
    for idx, row in df_gesamtVerlauf.iterrows():
        
        aktuelle_leistung_batterie = fixparameterBatterie.leistung * row["Speicherkapazität Batterie [MWh]"]
        aktuelle_leistung_wasserstoff = fixparameterWasserstoff.leistung * row["Speicherkapazität Wasserstoff [MWh]"]
        aktuelle_leistung_pumpspeicher = fixparameterPumpspeicher.leistung * row["Speicherkapazität Pumpspeicher [MWh]"]
        aktuell_verfugbare_batterie = aktuell_batterie - (row["Speicherkapazität Batterie [MWh]"]*fixparameterBatterie.untergrenze)
        aktuell_verfugbare_wasserstoff = aktuell_wasserstoff - (row["Speicherkapazität Wasserstoff [MWh]"]*fixparameterWasserstoff.untergrenze)
        aktuell_verfugbare_pumpspeicher = aktuell_pumpspeicher - (row["Speicherkapazität Pumpspeicher [MWh]"]*fixparameterPumpspeicher.untergrenze)
        
        #Summe aller Erzeuger berechnen...
        erzeugung = (
            row["Biomasse [MWh] Originalauflösungen"] +
            row["Wasserkraft [MWh] Originalauflösungen"] + 
            row["Wind Offshore [MWh] Originalauflösungen"] +
            row["Wind Onshore [MWh] Originalauflösungen"] +
            row["Photovoltaik [MWh] Originalauflösungen"] +
            row["Sonstige Erneuerbare [MWh] Originalauflösungen"]
        )     

        if row["Anteil Erneuerbare [%]"] > ladegrenze: #überschüssige Energie vorhanden

            lademenge = erzeugung - row["Netzlast [MWh]"]*(ladegrenze/100) #überschüssige Energie zum Laden

            # Batterie laden
            if aktuell_batterie <= ((row["Speicherkapazität Batterie [MWh]"]*fixparameterBatterie.obergrenze) - aktuelle_leistung_batterie/4):
                if lademenge > 0 and (aktuelle_leistung_batterie/4) > lademenge:
                    aktuell_batterie += lademenge
                    lademenge = 0
                elif lademenge > 0 and (aktuelle_leistung_batterie/4) <= lademenge:
                    aktuell_batterie += (aktuelle_leistung_batterie/4)
                    lademenge -= (aktuelle_leistung_batterie/4)

            # Pumpspeicher laden
            if aktuell_pumpspeicher <= ((row["Speicherkapazität Pumpspeicher [MWh]"]*fixparameterPumpspeicher.obergrenze) - aktuelle_leistung_pumpspeicher/4):
                if lademenge > 0 and (aktuelle_leistung_pumpspeicher/4) > lademenge:
                    aktuell_pumpspeicher += lademenge
                    lademenge = 0
                elif lademenge > 0 and (aktuelle_leistung_pumpspeicher/4) <= lademenge:
                    aktuell_pumpspeicher += (aktuelle_leistung_pumpspeicher/4)
                    lademenge -= (aktuelle_leistung_pumpspeicher/4)

            # Wasserstoff laden
            if aktuell_wasserstoff <= ((row["Speicherkapazität Wasserstoff [MWh]"]*fixparameterWasserstoff.obergrenze) - aktuelle_leistung_wasserstoff/4):
                if lademenge > 0 and (aktuelle_leistung_wasserstoff/4) > lademenge:
                    aktuell_wasserstoff += lademenge
                    lademenge = 0
                elif lademenge > 0 and (aktuelle_leistung_wasserstoff/4) <= lademenge:
                    aktuell_wasserstoff += (aktuelle_leistung_wasserstoff/4)
                    lademenge -= (aktuelle_leistung_wasserstoff/4)
            

            exportEnergie += lademenge

        elif row["Anteil Erneuerbare [%]"] <= entladegrenze: #fehlende Energie vorhanden

            fehlmenge = row["Netzlast [MWh]"]*(entladegrenze/100) - erzeugung #fehlende Energie
            aktuell_zusatz_energie = 0

            # Batterie entladen
            if aktuell_batterie > (row["Speicherkapazität Batterie [MWh]"]*fixparameterBatterie.untergrenze):
                if fehlmenge > 0 and ((aktuelle_leistung_batterie/4)*fixparameterBatterie.wirkungsgrad) > fehlmenge and aktuell_verfugbare_batterie >= (fehlmenge/fixparameterBatterie.wirkungsgrad):
                    aktuell_batterie -= (fehlmenge/fixparameterBatterie.wirkungsgrad)
                    aktuell_zusatz_energie += fehlmenge
                    fehlmenge = 0  
                elif fehlmenge > 0 and ((aktuelle_leistung_batterie/4)*fixparameterBatterie.wirkungsgrad) <= fehlmenge and aktuell_verfugbare_batterie >= (aktuelle_leistung_batterie/4):
                    aktuell_batterie -= (aktuelle_leistung_batterie/4)
                    aktuell_zusatz_energie += (aktuelle_leistung_batterie/4)*fixparameterBatterie.wirkungsgrad
                    fehlmenge -= ((aktuelle_leistung_batterie/4)*fixparameterBatterie.wirkungsgrad)
                elif fehlmenge > 0 and aktuell_verfugbare_batterie < aktuelle_leistung_batterie/4:
                    if fehlmenge < (aktuell_verfugbare_batterie*fixparameterBatterie.wirkungsgrad):
                        aktuell_batterie -= (fehlmenge/fixparameterBatterie.wirkungsgrad)
                        aktuell_zusatz_energie += fehlmenge
                        fehlmenge = 0
                    elif fehlmenge >= (aktuell_verfugbare_batterie*fixparameterBatterie.wirkungsgrad):
                        fehlmenge -= aktuell_verfugbare_batterie*fixparameterBatterie.wirkungsgrad
                        aktuell_zusatz_energie += aktuell_verfugbare_batterie*fixparameterBatterie.wirkungsgrad
                        aktuell_batterie = (row["Speicherkapazität Batterie [MWh]"]*fixparameterBatterie.untergrenze)
                        
            # Pumpspeicher entladen
            if aktuell_pumpspeicher > (row["Speicherkapazität Pumpspeicher [MWh]"]*fixparameterPumpspeicher.untergrenze):
                if fehlmenge > 0 and ((aktuelle_leistung_pumpspeicher/4)*fixparameterPumpspeicher.wirkungsgrad) > fehlmenge and aktuell_verfugbare_pumpspeicher >= (fehlmenge/fixparameterPumpspeicher.wirkungsgrad):
                    aktuell_pumpspeicher -= (fehlmenge/fixparameterPumpspeicher.wirkungsgrad)
                    aktuell_zusatz_energie += fehlmenge
                    fehlmenge = 0
                elif fehlmenge > 0 and ((aktuelle_leistung_pumpspeicher/4)*fixparameterPumpspeicher.wirkungsgrad) <= fehlmenge and aktuell_verfugbare_pumpspeicher >= (aktuelle_leistung_pumpspeicher/4):
                    aktuell_pumpspeicher -= (aktuelle_leistung_pumpspeicher/4)
                    aktuell_zusatz_energie += (aktuelle_leistung_pumpspeicher/4)*fixparameterPumpspeicher.wirkungsgrad
                    fehlmenge -= ((aktuelle_leistung_pumpspeicher/4)*fixparameterPumpspeicher.wirkungsgrad)
                elif fehlmenge > 0 and aktuell_verfugbare_pumpspeicher < aktuelle_leistung_pumpspeicher/4:
                    if fehlmenge < (aktuell_verfugbare_pumpspeicher*fixparameterPumpspeicher.wirkungsgrad):
                        aktuell_pumpspeicher -= (fehlmenge/fixparameterPumpspeicher.wirkungsgrad)
                        aktuell_zusatz_energie += fehlmenge
                        fehlmenge = 0
                    elif fehlmenge >= (aktuell_verfugbare_pumpspeicher*fixparameterPumpspeicher.wirkungsgrad):
                        fehlmenge -= aktuell_verfugbare_pumpspeicher*fixparameterPumpspeicher.wirkungsgrad
                        aktuell_zusatz_energie += aktuell_verfugbare_pumpspeicher*fixparameterPumpspeicher.wirkungsgrad
                        aktuell_pumpspeicher = (row["Speicherkapazität Pumpspeicher [MWh]"]*fixparameterPumpspeicher.untergrenze)

            # Wasserstoff entladen
            if aktuell_wasserstoff > (row["Speicherkapazität Wasserstoff [MWh]"]*fixparameterWasserstoff.untergrenze):
                if fehlmenge > 0 and ((aktuelle_leistung_wasserstoff/4)*fixparameterWasserstoff.wirkungsgrad) > fehlmenge and aktuell_verfugbare_wasserstoff >= (fehlmenge/fixparameterWasserstoff.wirkungsgrad):
                    aktuell_wasserstoff -= (fehlmenge/fixparameterWasserstoff.wirkungsgrad)
                    aktuell_zusatz_energie += fehlmenge
                    fehlmenge = 0
                elif fehlmenge > 0 and ((aktuelle_leistung_wasserstoff/4)*fixparameterWasserstoff.wirkungsgrad) <= fehlmenge and aktuell_verfugbare_wasserstoff >= (aktuelle_leistung_wasserstoff/4):
                    aktuell_wasserstoff -= (aktuelle_leistung_wasserstoff/4)
                    aktuell_zusatz_energie += (aktuelle_leistung_wasserstoff/4)*fixparameterWasserstoff.wirkungsgrad
                    fehlmenge -= ((aktuelle_leistung_wasserstoff/4)*fixparameterWasserstoff.wirkungsgrad)
                elif fehlmenge > 0 and aktuell_verfugbare_wasserstoff < aktuelle_leistung_wasserstoff/4:
                    if fehlmenge < (aktuell_verfugbare_wasserstoff*fixparameterWasserstoff.wirkungsgrad):
                        aktuell_wasserstoff -= (fehlmenge/fixparameterWasserstoff.wirkungsgrad)
                        aktuell_zusatz_energie += fehlmenge
                        fehlmenge = 0
                    elif fehlmenge >= (aktuell_verfugbare_wasserstoff*fixparameterWasserstoff.wirkungsgrad):
                        fehlmenge -= aktuell_verfugbare_wasserstoff*fixparameterWasserstoff.wirkungsgrad
                        aktuell_zusatz_energie += aktuell_verfugbare_wasserstoff*fixparameterWasserstoff.wirkungsgrad
                        aktuell_wasserstoff = (row["Speicherkapazität Wasserstoff [MWh]"]*fixparameterWasserstoff.untergrenze)
            
            

            importEnergie += fehlmenge 
               
        
        speicherstand_batterie.append(aktuell_batterie)
        speicherstand_wasserstoff.append(aktuell_wasserstoff)   
        speicherstand_pumpspeicher.append(aktuell_pumpspeicher)  
        zusatz_energie.append(aktuell_zusatz_energie)   

    df_gesamtVerlauf["Ladestand Batterie [MWh]"] = speicherstand_batterie
    df_gesamtVerlauf["Ladestand Wasserstoff [MWh]"] = speicherstand_wasserstoff
    df_gesamtVerlauf["Ladestand Pumpspeicher [MWh]"] = speicherstand_pumpspeicher 
    df_gesamtVerlauf["Energie aus Speicher [MWh]"] = zusatz_energie

    return df_gesamtVerlauf

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
    date_range = pd.date_range(start='2026-01-01', end='2030-12-31 23:45', freq='15min',tz="UTC")
    df_2030 = pd.DataFrame({'Datum von': date_range})

    # df_2030["Jahr"] = df_2030["Datum von"].dt.year
    # df_2030["Monat"]= df_2030["Datum von"].dt.month
    # df_2030["Wochentag"] = df_2030["Datum von"].dt.dayofweek
    # df_2030["Uhrzeit"] = df_2030["Datum von"].dt.hour
    # df_2030["Minute"] = df_2030["Datum von"].dt.minute

    anzahl_tage_2030 = len(df_2030["Datum von"].dt.date.unique()) # type: ignore
    
    wachstumsrate_2030 = (bestand2030 - bestand2025) / anzahl_tage_2030

    speichername = f"Speicherkapazität {speicherart} [MWh]"
    
    df_2030[speichername] = bestand2025 + wachstumsrate_2030 * ((df_2030['Datum von'] - df_2030['Datum von'].min()).dt.days + 1)

    # df_2030.to_csv(PROJECT_ROOT / 'Daten' / 'speicherprognosetest2030.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    #=== Dataframe für die Jahre 2030 bis 2045 erstellen ===
    date_range = pd.date_range(start='2031-01-01', end='2045-12-31 23:45', freq='15min',tz="UTC")
    df_2045 = pd.DataFrame({'Datum von': date_range})

    # df_2045["Jahr"] = df_2045["Datum von"].dt.year
    # df_2045["Monat"]= df_2045["Datum von"].dt.month
    # df_2045["Wochentag"] = df_2045["Datum von"].dt.dayofweek
    # df_2045["Uhrzeit"] = df_2045["Datum von"].dt.hour
    # df_2045["Minute"] = df_2045["Datum von"].dt.minute

    anzahl_tage_2045 = len(df_2045["Datum von"].dt.date.unique()) # type: ignore
    
    wachstumsrate_2045 = (bestand2045 - bestand2030) / anzahl_tage_2045

    df_2045[speichername] = bestand2030 + wachstumsrate_2045 * ((df_2045['Datum von'] - df_2045['Datum von'].min()).dt.days + 1)

    df_gesamt = pd.concat([df_2030, df_2045], ignore_index=True) # Bereich von 2026 bis 2030 und 2031 bis 2045 zusammenfügen
    df_gesamt[speichername] = df_gesamt[speichername].round(2)

    # df_gesamt.to_csv(PROJECT_ROOT / 'Daten' / 'speicherprognosetestgesamt.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    return df_gesamt

def Prognose_Gesamt_Ausbau_(bestandBatterie, bestandWasserstoff, bestandPumpspeicher, Batterie30, Batterie45, Wasserstoff30, Wasserstoff45, Pumpspeicher30, Pumpspeicher45):
    """
    Erstellt die Gesamtprognose für alle Speicherarten
    """

    #bestandBatterie30 = szenarioBatterie.bestand_2030
    #bestandBatterie45 = szenarioBatterie.bestand_2045
    #bestandWasserstoff30 = szenarioWasserstoff.bestand_2030
    #bestandWasserstoff45 = szenarioWasserstoff.bestand_2045
    #bestandPumpspeicher30 = szenarioPumpspeicher.bestand_2030
    #bestandPumpspeicher45 = szenarioPumpspeicher.bestand_2045

    df_batterie = Prognose_Speicher_Ausbau("Batterie", bestandBatterie, Batterie30, Batterie45)
    df_wasserstoff = Prognose_Speicher_Ausbau("Wasserstoff", bestandWasserstoff, Wasserstoff30, Wasserstoff45)
    df_pump = Prognose_Speicher_Ausbau("Pumpspeicher", bestandPumpspeicher, Pumpspeicher30, Pumpspeicher45)

    dfs = [df_batterie, df_wasserstoff, df_pump]

    # Merge alle DataFrames auf gemeinsamen Spalten
    df_ausbau = reduce(
        lambda left, right: left.merge(
            right, 
            on=['Datum von'], 
            how='outer'
        ), 
        dfs
    )

    # df_ausbau.to_csv(PROJECT_ROOT / 'Daten' / 'speicherprognosetestgesamt.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    return df_ausbau