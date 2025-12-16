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
from fractions import Fraction
from config import DATA_DIR

#TODO: Klasse in Klassen.py?
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

def Einlesen_Speicherdaten_fix(speicherart) -> Speicher:
    """
    Liest alle festen Parameter einer Speicherart aus einer JSON-Datei ein
    """
    
    with open(DATA_DIR / "Feste_Parameter" / "speicherarten.json", "r") as f:
        data = json.load(f)

    speicher_data = data.get(speicherart)
    if speicher_data is None:
        raise ValueError(f"Speicherart '{speicherart}' nicht in der JSON-Datei gefunden.")

    speicher = Speicher(**speicher_data)

    return speicher

def Einlesen_Dunkelflaute(jahr: int) -> pd.DataFrame:
    """
    Liest die Dunkelflauten-Daten aus einer CSV-Datei ein
    """

    pfad = DATA_DIR / "Variable_Parameter" /"dunkelflaute.csv"  
    df_dunkelflaute = pd.read_csv(pfad, sep=';', decimal=',', low_memory=False, names=["month","day","realisierte EE [Anteil]"], header=0)
    df_dunkelflaute.insert(0, "year", jahr)
    df_dunkelflaute.insert(0, "Datum von", pd.to_datetime(df_dunkelflaute[["year", "month", "day"]], format='%Y-%m-%d', utc=True))
    df_dunkelflaute = df_dunkelflaute.drop(columns=["year","month","day"])

    return df_dunkelflaute

# Fixparameter für Speicher einlesen
FIXPARAMETER_BATTERIE = Einlesen_Speicherdaten_fix("batteriespeicher")
FIXPARAMETER_WASSERSTOFF = Einlesen_Speicherdaten_fix("wasserstoff")
FIXPARAMETER_PUMPSPEICHER = Einlesen_Speicherdaten_fix("pumpspeicher")

#TODO : Andere Grenzen für 2026-2030 und 2031-2045 einbauen?
def Verlauf_Speicher(df_anteilEE: pd.DataFrame, entladegrenze: float, ladegrenze: float, ziele_2030: dict, ziele_2045: dict ) -> pd.DataFrame:
    """
    Simuliert den Verlauf mit Erzeugung, Verbrauch und Speichern.
    """

    bestandBatterie = FIXPARAMETER_BATTERIE.bestand
    bestandWasserstoff = FIXPARAMETER_WASSERSTOFF.bestand
    bestandPumpspeicher = FIXPARAMETER_PUMPSPEICHER.bestand

    # Errechnung der Wirkungsgrade für Lade- und Entladevorgang aus Gesamtwirkungsgrad, 
    # sodass die Hälfte des Ursprungsbetrags bei input die andere bei output verloren wird, 
    # umrechnen in Brüche
    inputWirkungsgradBatterie = Fraction(FIXPARAMETER_BATTERIE.wirkungsgrad + ((1-FIXPARAMETER_BATTERIE.wirkungsgrad)/2))
    inputWirkungsgradWasserstoff = Fraction(FIXPARAMETER_WASSERSTOFF.wirkungsgrad + ((1-FIXPARAMETER_WASSERSTOFF.wirkungsgrad)/2))
    inputWirkungsgradPumpspeicher = Fraction(FIXPARAMETER_PUMPSPEICHER.wirkungsgrad + ((1-FIXPARAMETER_PUMPSPEICHER.wirkungsgrad)/2)) 

    outputWirkungsgradBatterie = Fraction(inputWirkungsgradBatterie.numerator - 1, inputWirkungsgradBatterie.denominator - 1)
    outputWirkungsgradWasserstoff = Fraction(inputWirkungsgradWasserstoff.numerator - 1, inputWirkungsgradWasserstoff.denominator - 1)
    outputWirkungsgradPumpspeicher = Fraction(inputWirkungsgradPumpspeicher.numerator - 1, inputWirkungsgradPumpspeicher.denominator - 1)

    
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

    # Debug-Code
    # df_gesamtVerlauf.to_csv(DATA_DIR / 'Output' / 'debug_gesamtverlauf.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    

    # Listen für Ergebnisse initialisieren TODO: Lademenge und Fehlmenge in Spalten speichern?
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
        
        #TODO: Leistung direkt auf 15min umrechnen?
        aktuelle_leistung_batterie = FIXPARAMETER_BATTERIE.leistung * row["Speicherkapazität batteriespeicher [MWh]"] 
        aktuelle_leistung_wasserstoff = FIXPARAMETER_WASSERSTOFF.leistung * row["Speicherkapazität wasserstoff [MWh]"]
        aktuelle_leistung_pumpspeicher = FIXPARAMETER_PUMPSPEICHER.leistung * row["Speicherkapazität pumpspeicher [MWh]"]
        aktuell_verfugbare_batterie = aktuell_batterie - (row["Speicherkapazität batteriespeicher [MWh]"]*FIXPARAMETER_BATTERIE.untergrenze)
        aktuell_verfugbare_wasserstoff = aktuell_wasserstoff - (row["Speicherkapazität wasserstoff [MWh]"]*FIXPARAMETER_WASSERSTOFF.untergrenze)
        aktuell_verfugbare_pumpspeicher = aktuell_pumpspeicher - (row["Speicherkapazität pumpspeicher [MWh]"]*FIXPARAMETER_PUMPSPEICHER.untergrenze)
        
        #Summe aller Erzeuger 
        erzeugung = row["Erneuerbare [MWh]"]     

        if row["Anteil Erneuerbare [%]"] > ladegrenze: #überschüssige Energie vorhanden

            lademenge = erzeugung - row["Netzlast [MWh]"]*(ladegrenze/100) #überschüssige Energie zum Laden

            # Batterie laden
            if aktuell_batterie <= ((row["Speicherkapazität batteriespeicher [MWh]"]*FIXPARAMETER_BATTERIE.obergrenze) - aktuelle_leistung_batterie/4):
                if lademenge > 0 and (aktuelle_leistung_batterie/4) > (lademenge*inputWirkungsgradBatterie):
                    aktuell_batterie += (lademenge*inputWirkungsgradBatterie)
                    lademenge = 0
                elif lademenge > 0 and (aktuelle_leistung_batterie/4) <= (lademenge*inputWirkungsgradBatterie):
                    aktuell_batterie += (aktuelle_leistung_batterie/4)
                    lademenge -= ((aktuelle_leistung_batterie/4)/inputWirkungsgradBatterie)

            # Pumpspeicher laden
            if aktuell_pumpspeicher <= ((row["Speicherkapazität pumpspeicher [MWh]"]*FIXPARAMETER_PUMPSPEICHER.obergrenze) - aktuelle_leistung_pumpspeicher/4):
                if lademenge > 0 and (aktuelle_leistung_pumpspeicher/4) > (lademenge*inputWirkungsgradPumpspeicher):
                    aktuell_pumpspeicher += (lademenge*inputWirkungsgradPumpspeicher)
                    lademenge = 0
                elif lademenge > 0 and (aktuelle_leistung_pumpspeicher/4) <= (lademenge*inputWirkungsgradPumpspeicher):
                    aktuell_pumpspeicher += (aktuelle_leistung_pumpspeicher/4)
                    lademenge -= ((aktuelle_leistung_pumpspeicher/4)/inputWirkungsgradPumpspeicher)

            # Wasserstoff laden
            if aktuell_wasserstoff <= ((row["Speicherkapazität wasserstoff [MWh]"]*FIXPARAMETER_WASSERSTOFF.obergrenze) - aktuelle_leistung_wasserstoff/4):
                if lademenge > 0 and (aktuelle_leistung_wasserstoff/4) > (lademenge*inputWirkungsgradWasserstoff):
                    aktuell_wasserstoff += (lademenge*inputWirkungsgradWasserstoff)
                    lademenge = 0
                elif lademenge > 0 and (aktuelle_leistung_wasserstoff/4) <= (lademenge*inputWirkungsgradWasserstoff):
                    aktuell_wasserstoff += (aktuelle_leistung_wasserstoff/4)
                    lademenge -= ((aktuelle_leistung_wasserstoff/4)/inputWirkungsgradWasserstoff)
            

            exportEnergie += lademenge

        elif row["Anteil Erneuerbare [%]"] <= entladegrenze: #fehlende Energie vorhanden

            fehlmenge = row["Netzlast [MWh]"]*(entladegrenze/100) - erzeugung #fehlende Energie
            aktuell_zusatz_energie = 0

            # Batterie entladen
            if aktuell_batterie > (row["Speicherkapazität batteriespeicher [MWh]"]*FIXPARAMETER_BATTERIE.untergrenze):
                if fehlmenge > 0 and (aktuelle_leistung_batterie/4) > fehlmenge and aktuell_verfugbare_batterie >= (fehlmenge/outputWirkungsgradBatterie):
                    aktuell_batterie -= (fehlmenge/outputWirkungsgradBatterie)
                    aktuell_zusatz_energie += fehlmenge
                    fehlmenge = 0  
                elif fehlmenge > 0 and (aktuelle_leistung_batterie/4) <= fehlmenge and aktuell_verfugbare_batterie >= ((aktuelle_leistung_batterie/4)/outputWirkungsgradBatterie):
                    aktuell_batterie -= ((aktuelle_leistung_batterie/4)/outputWirkungsgradBatterie)
                    aktuell_zusatz_energie += (aktuelle_leistung_batterie/4)
                    fehlmenge -= (aktuelle_leistung_batterie/4)
                elif fehlmenge > 0 and aktuell_verfugbare_batterie < ((aktuelle_leistung_batterie/4)/outputWirkungsgradBatterie):
                    if fehlmenge < (aktuell_verfugbare_batterie*outputWirkungsgradBatterie):
                        aktuell_batterie -= (fehlmenge/outputWirkungsgradBatterie)
                        aktuell_zusatz_energie += fehlmenge
                        fehlmenge = 0
                    elif fehlmenge >= (aktuell_verfugbare_batterie*outputWirkungsgradBatterie):
                        fehlmenge -= (aktuell_verfugbare_batterie*outputWirkungsgradBatterie)
                        aktuell_zusatz_energie += (aktuell_verfugbare_batterie*outputWirkungsgradBatterie)
                        aktuell_batterie = (row["Speicherkapazität batteriespeicher [MWh]"]*FIXPARAMETER_BATTERIE.untergrenze)
                        
            # Pumpspeicher entladen
            if aktuell_pumpspeicher > (row["Speicherkapazität pumpspeicher [MWh]"]*FIXPARAMETER_PUMPSPEICHER.untergrenze):
                if fehlmenge > 0 and (aktuelle_leistung_pumpspeicher/4) > fehlmenge and aktuell_verfugbare_pumpspeicher >= (fehlmenge/outputWirkungsgradPumpspeicher):
                    aktuell_pumpspeicher -= (fehlmenge/outputWirkungsgradPumpspeicher)
                    aktuell_zusatz_energie += fehlmenge
                    fehlmenge = 0  
                elif fehlmenge > 0 and (aktuelle_leistung_pumpspeicher/4) <= fehlmenge and aktuell_verfugbare_pumpspeicher >= ((aktuelle_leistung_pumpspeicher/4)/outputWirkungsgradPumpspeicher):
                    aktuell_pumpspeicher -= ((aktuelle_leistung_pumpspeicher/4)/outputWirkungsgradPumpspeicher)
                    aktuell_zusatz_energie += (aktuelle_leistung_pumpspeicher/4)
                    fehlmenge -= (aktuelle_leistung_pumpspeicher/4)
                elif fehlmenge > 0 and aktuell_verfugbare_pumpspeicher < ((aktuelle_leistung_pumpspeicher/4)/outputWirkungsgradPumpspeicher):
                    if fehlmenge < (aktuell_verfugbare_pumpspeicher*outputWirkungsgradPumpspeicher):
                        aktuell_pumpspeicher -= (fehlmenge/outputWirkungsgradPumpspeicher)
                        aktuell_zusatz_energie += fehlmenge
                        fehlmenge = 0
                    elif fehlmenge >= (aktuell_verfugbare_pumpspeicher*outputWirkungsgradPumpspeicher):
                        fehlmenge -= (aktuell_verfugbare_pumpspeicher*outputWirkungsgradPumpspeicher)
                        aktuell_zusatz_energie += (aktuell_verfugbare_pumpspeicher*outputWirkungsgradPumpspeicher)
                        aktuell_pumpspeicher = (row["Speicherkapazität pumpspeicher [MWh]"]*FIXPARAMETER_PUMPSPEICHER.untergrenze)

            # Wasserstoff entladen
            if aktuell_wasserstoff > (row["Speicherkapazität wasserstoff [MWh]"]*FIXPARAMETER_WASSERSTOFF.untergrenze):
                if fehlmenge > 0 and (aktuelle_leistung_wasserstoff/4) > fehlmenge and aktuell_verfugbare_wasserstoff >= (fehlmenge/outputWirkungsgradWasserstoff):
                    aktuell_wasserstoff -= (fehlmenge/outputWirkungsgradWasserstoff)
                    aktuell_zusatz_energie += fehlmenge
                    fehlmenge = 0  
                elif fehlmenge > 0 and (aktuelle_leistung_wasserstoff/4) <= fehlmenge and aktuell_verfugbare_wasserstoff >= ((aktuelle_leistung_wasserstoff/4)/outputWirkungsgradWasserstoff):
                    aktuell_wasserstoff -= ((aktuelle_leistung_wasserstoff/4)/outputWirkungsgradWasserstoff)
                    aktuell_zusatz_energie += (aktuelle_leistung_wasserstoff/4)
                    fehlmenge -= (aktuelle_leistung_wasserstoff/4)
                elif fehlmenge > 0 and aktuell_verfugbare_wasserstoff < ((aktuelle_leistung_wasserstoff/4)/outputWirkungsgradWasserstoff):
                    if fehlmenge < (aktuell_verfugbare_wasserstoff*outputWirkungsgradWasserstoff):
                        aktuell_wasserstoff -= (fehlmenge/outputWirkungsgradWasserstoff)
                        aktuell_zusatz_energie += fehlmenge
                        fehlmenge = 0
                    elif fehlmenge >= (aktuell_verfugbare_wasserstoff*outputWirkungsgradWasserstoff):
                        fehlmenge -= (aktuell_verfugbare_wasserstoff*outputWirkungsgradWasserstoff)
                        aktuell_zusatz_energie += (aktuell_verfugbare_wasserstoff*outputWirkungsgradWasserstoff)
                        aktuell_wasserstoff = (row["Speicherkapazität wasserstoff [MWh]"]*FIXPARAMETER_WASSERSTOFF.untergrenze)
            
            

            importEnergie += fehlmenge 
               
        
        speicherstand_batterie.append(aktuell_batterie)
        speicherstand_wasserstoff.append(aktuell_wasserstoff)   
        speicherstand_pumpspeicher.append(aktuell_pumpspeicher)  
        zusatz_energie.append(aktuell_zusatz_energie)   

        # Langzeitverluste der Speicher jede Stunde, validiert (in CSV-Ausgabe mehrere Werte ausgerechnet)
        # (type ignore, da pylance nicht erkennt, dass idx ein int ist)
        if idx % 4 == 0: # type: ignore
            aktuell_batterie -= ((FIXPARAMETER_BATTERIE.verluste/100) * aktuell_batterie)
            aktuell_wasserstoff -= ((FIXPARAMETER_WASSERSTOFF.verluste/100) * aktuell_wasserstoff)
            aktuell_pumpspeicher -= ((FIXPARAMETER_PUMPSPEICHER.verluste/100) * aktuell_pumpspeicher)

    df_gesamtVerlauf["Ladestand batteriespeicher [MWh]"] = speicherstand_batterie
    df_gesamtVerlauf["Ladestand wasserstoff [MWh]"] = speicherstand_wasserstoff
    df_gesamtVerlauf["Ladestand pumpspeicher [MWh]"] = speicherstand_pumpspeicher 
    df_gesamtVerlauf["Energie aus Speicher [MWh]"] = zusatz_energie

    if(df_gesamtVerlauf.isna().any().any()):
        print("Warnung: Es gibt fehlende Werte in der Speicherprognose!"  )
        print(df_gesamtVerlauf.isna().sum())
        mask = df_gesamtVerlauf.isna() | df_gesamtVerlauf.isin([np.inf, -np.inf])
        print(df_gesamtVerlauf[mask.any(axis=1)])

    # Debug-Code
    # df_gesamtVerlauf.to_csv(DATA_DIR / 'Output' / 'debug_gesamtverlauf.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    return df_gesamtVerlauf

def Simulation_Dunkelflaute(df_verlauf: pd.DataFrame, jahr: int):
    """
    Simuliert den Verlauf einer Dunkelflaute
    """

    # Dunkelflauten-Daten einlesen
    df_dunkelflaute = Einlesen_Dunkelflaute(jahr)

    # Kopie des Verlaufs erstellen um Original nicht zu verändern
    df_verlauf_dunkelflaute = df_verlauf.copy()

    # Berechnen neuer Erzeugungswerte während der Dunkelflaute
        # Liste der Dunkelflaute-Daten und Faktoren
    dunkelflaute_dict = dict(zip(
        df_dunkelflaute['Datum von'].dt.date, 
        df_dunkelflaute['realisierte EE [Anteil]']
    ))
    
    # Maske für alle Dunkelflaute-Tage
    mask = df_verlauf_dunkelflaute['Datum von'].dt.date.isin(dunkelflaute_dict.keys())
    
    # Faktor-Spalte temporär hinzufügen
    df_verlauf_dunkelflaute.loc[mask, 'faktor'] = df_verlauf_dunkelflaute.loc[mask, 'Datum von'].dt.date.map(dunkelflaute_dict)
    
    # Alle Erzeugungsspalten multiplizieren
    df_verlauf_dunkelflaute.loc[mask, 'Wind Offshore [MWh] Originalauflösungen'] = df_verlauf_dunkelflaute.loc[mask, 'Installierte Wind_Offshore_GW'] * 1000 * df_verlauf_dunkelflaute.loc[mask, 'faktor']
    df_verlauf_dunkelflaute.loc[mask, 'Wind Onshore [MWh] Originalauflösungen'] = df_verlauf_dunkelflaute.loc[mask, 'Installierte Wind_Onshore_GW'] * 1000 * df_verlauf_dunkelflaute.loc[mask, 'faktor']
    df_verlauf_dunkelflaute.loc[mask, 'Photovoltaik [MWh] Originalauflösungen'] = df_verlauf_dunkelflaute.loc[mask, 'Installierte PV_GW'] * 1000 * df_verlauf_dunkelflaute.loc[mask, 'faktor']

    # Faktor-Spalte wieder entfernen
    df_verlauf_dunkelflaute.drop('faktor', axis=1, inplace=True)

    # Gesamt Erneuerbare neu berechnen
    erneuerbare_cols = [
    "Biomasse [MWh] Originalauflösungen",
    "Wasserkraft [MWh] Originalauflösungen",
    "Wind Offshore [MWh] Originalauflösungen",
    "Wind Onshore [MWh] Originalauflösungen",
    "Photovoltaik [MWh] Originalauflösungen",
    "Sonstige Erneuerbare [MWh] Originalauflösungen",
    ]
    df_verlauf_dunkelflaute.loc[mask, "Erneuerbare [MWh]"] = df_verlauf_dunkelflaute.loc[mask, erneuerbare_cols].sum(axis=1)

    # Neuer Anteil Erneuerbare an Netzlast berechnen
    df_verlauf_dunkelflaute.loc[mask, "Anteil Erneuerbare [%]"] = (df_verlauf_dunkelflaute.loc[mask, "Erneuerbare [MWh]"] / df_verlauf_dunkelflaute.loc[mask, "Netzlast [MWh]"] * 100).round(2)
    
    # Erweitere Dunkelflaute-Daten um +/- 1 Tag für Simulation
    dunkelflaute_tage = set(df_dunkelflaute['Datum von'].dt.date)
    extra_tage = set()
    for date in dunkelflaute_tage:
        extra_tage.add(date - pd.Timedelta(days=1))  # Tag davor
        extra_tage.add(date)  # Dunkelflaute-Tag selbst
        extra_tage.add(date + pd.Timedelta(days=1))  # Tag danach
    
    # Maske für Dunkelflaute-Tage +/- 1 Tag
    mask_simulation = df_verlauf_dunkelflaute['Datum von'].dt.date.isin(extra_tage)
    
    # Hole Speicherstände vom letzten Zeitpunkt vor der Simulation
    idx_start = df_verlauf_dunkelflaute.loc[mask_simulation].index[0]
    
    aktuell_batterie = df_verlauf_dunkelflaute.loc[idx_start - 1, "Ladestand batteriespeicher [MWh]"]
    aktuell_wasserstoff = df_verlauf_dunkelflaute.loc[idx_start - 1, "Ladestand wasserstoff [MWh]"]
    aktuell_pumpspeicher = df_verlauf_dunkelflaute.loc[idx_start - 1, "Ladestand pumpspeicher [MWh]"]
    
    # Wirkungsgrade berechnen
    inputWirkungsgradBatterie = Fraction(FIXPARAMETER_BATTERIE.wirkungsgrad + ((1-FIXPARAMETER_BATTERIE.wirkungsgrad)/2))
    inputWirkungsgradWasserstoff = Fraction(FIXPARAMETER_WASSERSTOFF.wirkungsgrad + ((1-FIXPARAMETER_WASSERSTOFF.wirkungsgrad)/2))
    inputWirkungsgradPumpspeicher = Fraction(FIXPARAMETER_PUMPSPEICHER.wirkungsgrad + ((1-FIXPARAMETER_PUMPSPEICHER.wirkungsgrad)/2))
    
    outputWirkungsgradBatterie = Fraction(inputWirkungsgradBatterie.numerator - 1, inputWirkungsgradBatterie.denominator - 1)
    outputWirkungsgradWasserstoff = Fraction(inputWirkungsgradWasserstoff.numerator - 1, inputWirkungsgradWasserstoff.denominator - 1)
    outputWirkungsgradPumpspeicher = Fraction(inputWirkungsgradPumpspeicher.numerator - 1, inputWirkungsgradPumpspeicher.denominator - 1)
    
    # TODO: Diese Parameter sollten als Funktionsargumente übergeben werden
    ladegrenze = 100  # Platzhalter - sollte übergeben werden
    entladegrenze = 100  # Platzhalter - sollte übergeben werden
    exportEnergie = 0
    importEnergie = 0
    
    # Listen für Ergebnisse
    speicherstand_batterie = []
    speicherstand_wasserstoff = []
    speicherstand_pumpspeicher = []
    zusatz_energie = []
    
    # Simulation nur über Dunkelflaute-Tage +/- 1 Tag
    for idx, row in df_verlauf_dunkelflaute.loc[mask_simulation].iterrows():
        
        #TODO: Leistung direkt auf 15min umrechnen?
        aktuelle_leistung_batterie = FIXPARAMETER_BATTERIE.leistung * row["Speicherkapazität batteriespeicher [MWh]"] 
        aktuelle_leistung_wasserstoff = FIXPARAMETER_WASSERSTOFF.leistung * row["Speicherkapazität wasserstoff [MWh]"]
        aktuelle_leistung_pumpspeicher = FIXPARAMETER_PUMPSPEICHER.leistung * row["Speicherkapazität pumpspeicher [MWh]"]
        aktuell_verfugbare_batterie = aktuell_batterie - (row["Speicherkapazität batteriespeicher [MWh]"]*FIXPARAMETER_BATTERIE.untergrenze)
        aktuell_verfugbare_wasserstoff = aktuell_wasserstoff - (row["Speicherkapazität wasserstoff [MWh]"]*FIXPARAMETER_WASSERSTOFF.untergrenze)
        aktuell_verfugbare_pumpspeicher = aktuell_pumpspeicher - (row["Speicherkapazität pumpspeicher [MWh]"]*FIXPARAMETER_PUMPSPEICHER.untergrenze)
        
        #Summe aller Erzeuger 
        erzeugung = row["Erneuerbare [MWh]"]
        
        # Variable immer zu Beginn der Iteration initialisieren
        aktuell_zusatz_energie = 0

        if row["Anteil Erneuerbare [%]"] > ladegrenze: #überschüssige Energie vorhanden

            lademenge = erzeugung - row["Netzlast [MWh]"]*(ladegrenze/100) #überschüssige Energie zum Laden

            # Batterie laden
            if aktuell_batterie <= ((row["Speicherkapazität batteriespeicher [MWh]"]*FIXPARAMETER_BATTERIE.obergrenze) - aktuelle_leistung_batterie/4):
                if lademenge > 0 and (aktuelle_leistung_batterie/4) > (lademenge*inputWirkungsgradBatterie):
                    aktuell_batterie += (lademenge*inputWirkungsgradBatterie)
                    lademenge = 0
                elif lademenge > 0 and (aktuelle_leistung_batterie/4) <= (lademenge*inputWirkungsgradBatterie):
                    aktuell_batterie += (aktuelle_leistung_batterie/4)
                    lademenge -= ((aktuelle_leistung_batterie/4)/inputWirkungsgradBatterie)

            # Pumpspeicher laden
            if aktuell_pumpspeicher <= ((row["Speicherkapazität pumpspeicher [MWh]"]*FIXPARAMETER_PUMPSPEICHER.obergrenze) - aktuelle_leistung_pumpspeicher/4):
                if lademenge > 0 and (aktuelle_leistung_pumpspeicher/4) > (lademenge*inputWirkungsgradPumpspeicher):
                    aktuell_pumpspeicher += (lademenge*inputWirkungsgradPumpspeicher)
                    lademenge = 0
                elif lademenge > 0 and (aktuelle_leistung_pumpspeicher/4) <= (lademenge*inputWirkungsgradPumpspeicher):
                    aktuell_pumpspeicher += (aktuelle_leistung_pumpspeicher/4)
                    lademenge -= ((aktuelle_leistung_pumpspeicher/4)/inputWirkungsgradPumpspeicher)

            # Wasserstoff laden
            if aktuell_wasserstoff <= ((row["Speicherkapazität wasserstoff [MWh]"]*FIXPARAMETER_WASSERSTOFF.obergrenze) - aktuelle_leistung_wasserstoff/4):
                if lademenge > 0 and (aktuelle_leistung_wasserstoff/4) > (lademenge*inputWirkungsgradWasserstoff):
                    aktuell_wasserstoff += (lademenge*inputWirkungsgradWasserstoff)
                    lademenge = 0
                elif lademenge > 0 and (aktuelle_leistung_wasserstoff/4) <= (lademenge*inputWirkungsgradWasserstoff):
                    aktuell_wasserstoff += (aktuelle_leistung_wasserstoff/4)
                    lademenge -= ((aktuelle_leistung_wasserstoff/4)/inputWirkungsgradWasserstoff)
            

            exportEnergie += lademenge

        elif row["Anteil Erneuerbare [%]"] <= entladegrenze: #fehlende Energie vorhanden

            fehlmenge = row["Netzlast [MWh]"]*(entladegrenze/100) - erzeugung #fehlende Energie
            aktuell_zusatz_energie = 0

            # Batterie entladen
            if aktuell_batterie > (row["Speicherkapazität batteriespeicher [MWh]"]*FIXPARAMETER_BATTERIE.untergrenze):
                if fehlmenge > 0 and (aktuelle_leistung_batterie/4) > fehlmenge and aktuell_verfugbare_batterie >= (fehlmenge/outputWirkungsgradBatterie):
                    aktuell_batterie -= (fehlmenge/outputWirkungsgradBatterie)
                    aktuell_zusatz_energie += fehlmenge
                    fehlmenge = 0  
                elif fehlmenge > 0 and (aktuelle_leistung_batterie/4) <= fehlmenge and aktuell_verfugbare_batterie >= ((aktuelle_leistung_batterie/4)/outputWirkungsgradBatterie):
                    aktuell_batterie -= ((aktuelle_leistung_batterie/4)/outputWirkungsgradBatterie)
                    aktuell_zusatz_energie += (aktuelle_leistung_batterie/4)
                    fehlmenge -= (aktuelle_leistung_batterie/4)
                elif fehlmenge > 0 and aktuell_verfugbare_batterie < ((aktuelle_leistung_batterie/4)/outputWirkungsgradBatterie):
                    if fehlmenge < (aktuell_verfugbare_batterie*outputWirkungsgradBatterie):
                        aktuell_batterie -= (fehlmenge/outputWirkungsgradBatterie)
                        aktuell_zusatz_energie += fehlmenge
                        fehlmenge = 0
                    elif fehlmenge >= (aktuell_verfugbare_batterie*outputWirkungsgradBatterie):
                        fehlmenge -= (aktuell_verfugbare_batterie*outputWirkungsgradBatterie)
                        aktuell_zusatz_energie += (aktuell_verfugbare_batterie*outputWirkungsgradBatterie)
                        aktuell_batterie = (row["Speicherkapazität batteriespeicher [MWh]"]*FIXPARAMETER_BATTERIE.untergrenze)
                        
            # Pumpspeicher entladen
            if aktuell_pumpspeicher > (row["Speicherkapazität pumpspeicher [MWh]"]*FIXPARAMETER_PUMPSPEICHER.untergrenze):
                if fehlmenge > 0 and (aktuelle_leistung_pumpspeicher/4) > fehlmenge and aktuell_verfugbare_pumpspeicher >= (fehlmenge/outputWirkungsgradPumpspeicher):
                    aktuell_pumpspeicher -= (fehlmenge/outputWirkungsgradPumpspeicher)
                    aktuell_zusatz_energie += fehlmenge
                    fehlmenge = 0  
                elif fehlmenge > 0 and (aktuelle_leistung_pumpspeicher/4) <= fehlmenge and aktuell_verfugbare_pumpspeicher >= ((aktuelle_leistung_pumpspeicher/4)/outputWirkungsgradPumpspeicher):
                    aktuell_pumpspeicher -= ((aktuelle_leistung_pumpspeicher/4)/outputWirkungsgradPumpspeicher)
                    aktuell_zusatz_energie += (aktuelle_leistung_pumpspeicher/4)
                    fehlmenge -= (aktuelle_leistung_pumpspeicher/4)
                elif fehlmenge > 0 and aktuell_verfugbare_pumpspeicher < ((aktuelle_leistung_pumpspeicher/4)/outputWirkungsgradPumpspeicher):
                    if fehlmenge < (aktuell_verfugbare_pumpspeicher*outputWirkungsgradPumpspeicher):
                        aktuell_pumpspeicher -= (fehlmenge/outputWirkungsgradPumpspeicher)
                        aktuell_zusatz_energie += fehlmenge
                        fehlmenge = 0
                    elif fehlmenge >= (aktuell_verfugbare_pumpspeicher*outputWirkungsgradPumpspeicher):
                        fehlmenge -= (aktuell_verfugbare_pumpspeicher*outputWirkungsgradPumpspeicher)
                        aktuell_zusatz_energie += (aktuell_verfugbare_pumpspeicher*outputWirkungsgradPumpspeicher)
                        aktuell_pumpspeicher = (row["Speicherkapazität pumpspeicher [MWh]"]*FIXPARAMETER_PUMPSPEICHER.untergrenze)

            # Wasserstoff entladen
            if aktuell_wasserstoff > (row["Speicherkapazität wasserstoff [MWh]"]*FIXPARAMETER_WASSERSTOFF.untergrenze):
                if fehlmenge > 0 and (aktuelle_leistung_wasserstoff/4) > fehlmenge and aktuell_verfugbare_wasserstoff >= (fehlmenge/outputWirkungsgradWasserstoff):
                    aktuell_wasserstoff -= (fehlmenge/outputWirkungsgradWasserstoff)
                    aktuell_zusatz_energie += fehlmenge
                    fehlmenge = 0  
                elif fehlmenge > 0 and (aktuelle_leistung_wasserstoff/4) <= fehlmenge and aktuell_verfugbare_wasserstoff >= ((aktuelle_leistung_wasserstoff/4)/outputWirkungsgradWasserstoff):
                    aktuell_wasserstoff -= ((aktuelle_leistung_wasserstoff/4)/outputWirkungsgradWasserstoff)
                    aktuell_zusatz_energie += (aktuelle_leistung_wasserstoff/4)
                    fehlmenge -= (aktuelle_leistung_wasserstoff/4)
                elif fehlmenge > 0 and aktuell_verfugbare_wasserstoff < ((aktuelle_leistung_wasserstoff/4)/outputWirkungsgradWasserstoff):
                    if fehlmenge < (aktuell_verfugbare_wasserstoff*outputWirkungsgradWasserstoff):
                        aktuell_wasserstoff -= (fehlmenge/outputWirkungsgradWasserstoff)
                        aktuell_zusatz_energie += fehlmenge
                        fehlmenge = 0
                    elif fehlmenge >= (aktuell_verfugbare_wasserstoff*outputWirkungsgradWasserstoff):
                        fehlmenge -= (aktuell_verfugbare_wasserstoff*outputWirkungsgradWasserstoff)
                        aktuell_zusatz_energie += (aktuell_verfugbare_wasserstoff*outputWirkungsgradWasserstoff)
                        aktuell_wasserstoff = (row["Speicherkapazität wasserstoff [MWh]"]*FIXPARAMETER_WASSERSTOFF.untergrenze)
            
            

            importEnergie += fehlmenge 
               
        
        speicherstand_batterie.append(aktuell_batterie)
        speicherstand_wasserstoff.append(aktuell_wasserstoff)   
        speicherstand_pumpspeicher.append(aktuell_pumpspeicher)  
        zusatz_energie.append(aktuell_zusatz_energie)   

        # Langzeitverluste der Speicher jede Stunde, validiert (in CSV-Ausgabe mehrere Werte ausgerechnet)
        # (type ignore, da pylance nicht erkennt, dass idx ein int ist)
        if idx % 4 == 0: # type: ignore
            aktuell_batterie -= ((FIXPARAMETER_BATTERIE.verluste/100) * aktuell_batterie)
            aktuell_wasserstoff -= ((FIXPARAMETER_WASSERSTOFF.verluste/100) * aktuell_wasserstoff)
            aktuell_pumpspeicher -= ((FIXPARAMETER_PUMPSPEICHER.verluste/100) * aktuell_pumpspeicher)

    # Aktualisiere nur die simulierten Zeilen im DataFrame
    simulation_indices = df_verlauf_dunkelflaute.loc[mask_simulation].index
    df_verlauf_dunkelflaute.loc[simulation_indices, "Ladestand batteriespeicher [MWh]"] = speicherstand_batterie
    df_verlauf_dunkelflaute.loc[simulation_indices, "Ladestand wasserstoff [MWh]"] = speicherstand_wasserstoff
    df_verlauf_dunkelflaute.loc[simulation_indices, "Ladestand pumpspeicher [MWh]"] = speicherstand_pumpspeicher 
    df_verlauf_dunkelflaute.loc[simulation_indices, "Energie aus Speicher [MWh]"] = zusatz_energie

    # Dataframe auf relevante Zeilen reduzieren
    df_verlauf_dunkelflaute = df_verlauf_dunkelflaute.loc[mask_simulation].reset_index(drop=True)
    
    return df_verlauf_dunkelflaute

# Debug Code
# df_test = Einlesen_Dunkelflaute(2030)
# df_test.to_csv(DATA_DIR / 'Output' / 'debug_dunkelflaute.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

def Prognose_Speicher_Ausbau(speicherart, bestand2025, bestand2030, bestand2045) -> pd.DataFrame:
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

    # df_2030.to_csv(DATA_DIR / 'Output' / 'speicherprognosetest2030.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

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

    # df_gesamt.to_csv(DATA_DIR / 'Output' / 'speicherprognosetestgesamt.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    return df_gesamt

def Prognose_Gesamt_Ausbau_(bestandBatterie, bestandWasserstoff, bestandPumpspeicher, Batterie30, Batterie45, Wasserstoff30, Wasserstoff45, Pumpspeicher30, Pumpspeicher45) -> pd.DataFrame:
    """
    Erstellt die Gesamtprognose für alle Speicherarten
    """

    #bestandBatterie30 = szenarioBatterie.bestand_2030
    #bestandBatterie45 = szenarioBatterie.bestand_2045
    #bestandWasserstoff30 = szenarioWasserstoff.bestand_2030
    #bestandWasserstoff45 = szenarioWasserstoff.bestand_2045
    #bestandPumpspeicher30 = szenarioPumpspeicher.bestand_2030
    #bestandPumpspeicher45 = szenarioPumpspeicher.bestand_2045

    df_batterie = Prognose_Speicher_Ausbau("batteriespeicher", bestandBatterie, Batterie30, Batterie45)
    df_wasserstoff = Prognose_Speicher_Ausbau("wasserstoff", bestandWasserstoff, Wasserstoff30, Wasserstoff45)
    df_pump = Prognose_Speicher_Ausbau("pumpspeicher", bestandPumpspeicher, Pumpspeicher30, Pumpspeicher45)

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

    # df_ausbau.to_csv(DATA_DIR / 'Output' / 'speicherausbautestgesamt.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    return df_ausbau

def ausbaurate_GWh_Jahr(szenario: json) -> dict:
    """
    Berechnet die jährlichen Ausbauraten in GWh/Jahr für jede Speicherart
    """
    
    with open(DATA_DIR / "Feste_Parameter" / "speicherarten.json", 'r', encoding='utf-8') as datei:
        speicherarten = json.load(datei)

    ausbauraten = {
        "zuwachsrate_2030": {},
        "zuwachsrate_2045": {},
    }

    for key in speicherarten.keys():
        ausbauraten["zuwachsrate_2030"][key] = (szenario["Ziele 2030"]["Ausbau Speicher"][key] - speicherarten[key]["bestand"]) / 5
        ausbauraten["zuwachsrate_2045"][key] = (szenario["Ziele 2045"]["Ausbau Speicher"][key] - szenario["Ziele 2030"]["Ausbau Speicher"][key]) / 15

    return ausbauraten