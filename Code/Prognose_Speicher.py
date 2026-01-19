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

# JSON-Datei einmal am Anfang laden um Rechenleistung zu verringern
with open(DATA_DIR / "Feste_Parameter" / "speicherarten.json", "r") as f:
    SPEICHERARTEN_DATA = json.load(f)

def Einlesen_Speicherdaten_fix(speicherart) -> Speicher:
    """
    Liest alle festen Parameter einer Speicherart aus vorgeladenen Daten ein
    """
    
    speicher_data = SPEICHERARTEN_DATA.get(speicherart) # Über den Funktionen eingelesen, um Datei nicht mehrfach zu öffnen

    if speicher_data is None:
        raise ValueError(f"Speicherart '{speicherart}' nicht in der JSON-Datei gefunden.")

    speicher = Speicher(**speicher_data)

    return speicher

def Einlesen_Dunkelflaute(jahr: int) -> pd.DataFrame:
    """
    Liest die Dunkelflauten-Daten aus einer CSV-Datei ein
    """

    #TODO: Was tun, wenn Dauer der Dunkelflaute über Jahreswechsel geht?
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

# Hilfsfunktion zum Laden eines Speichers
def speicher_laden(
    aktueller_bestand: float,
    lademenge: float,
    leistung: float,
    kapazitaet: float,
    obergrenze: float,
    wirkungsgrad: Fraction
) -> tuple[float, float]:
    """
    Lädt einen Speicher mit verfügbarer Energie.
    Code refactored aus vorheriger Verlaufs-Funktion mithilfe von KI Claude Opus 4.5.
    
    Args:
        aktueller_bestand: Aktueller Ladestand in MWh
        lademenge: Verfügbare Energie zum Laden in MWh
        leistung: Maximale Viertelstundenleistung in MW
        kapazitaet: Gesamtkapazität des Speichers in MWh
        obergrenze: Maximaler Füllstand als Anteil (0-1)
        wirkungsgrad: Wirkungsgrad beim Laden
    
    Returns:
        (neuer_bestand, verbleibende_lademenge)
    """
    max_bestand = kapazitaet * obergrenze
    
    # Prüfen ob Speicher noch Platz hat
    if aktueller_bestand > (max_bestand - leistung): 
        lademenge = lademenge - ((max_bestand - aktueller_bestand) / wirkungsgrad)
        aktueller_bestand = max_bestand
        return aktueller_bestand, lademenge  
    
    if lademenge <= 0:
        return aktueller_bestand, lademenge
    
    # Berechne wie viel geladen werden kann
    energie_mit_wirkungsgrad = lademenge * wirkungsgrad
    
    if leistung > energie_mit_wirkungsgrad:
        # Gesamte Lademenge passt in einen Zeitschritt
        neuer_bestand = aktueller_bestand + energie_mit_wirkungsgrad
        return neuer_bestand, 0.0
    else:
        # Leistung begrenzt die Lademenge
        neuer_bestand = aktueller_bestand + leistung
        verbraucht = leistung / wirkungsgrad
        return neuer_bestand, lademenge - verbraucht

# Hilfsfunktion zum Entladen eines Speichers
def speicher_entladen(
    aktueller_bestand: float,
    fehlmenge: float,
    leistung: float,
    kapazitaet: float,
    untergrenze: float,
    wirkungsgrad: Fraction
) -> tuple[float, float, float]:
    """
    Entlädt einen Speicher um Fehlmenge zu decken. 
    Code refactored aus vorheriger Verlaufs-Funktion mithilfe von KI Claude Opus 4.5.
    
    Args:
        aktueller_bestand: Aktueller Ladestand in MWh
        fehlmenge: Benötigte Energie in MWh
        leistung: Maximale Viertelstundenleistung in MW
        kapazitaet: Gesamtkapazität des Speichers in MWh
        untergrenze: Minimaler Füllstand als Anteil (0-1)
        wirkungsgrad: Wirkungsgrad beim Entladen
    
    Returns:
        (neuer_bestand, gelieferte_energie, verbleibende_fehlmenge)
    """
    min_bestand = kapazitaet * untergrenze
    verfuegbar = aktueller_bestand - min_bestand
    
    # Prüfen ob Speicher über Minimum und Fehlmenge vorhanden
    if aktueller_bestand <= min_bestand or fehlmenge <= 0:
        return aktueller_bestand, 0.0, fehlmenge
    
    # Berechne benötigte Entnahme (mit Wirkungsgrad-Verlust)
    benoetigt_fuer_fehlmenge = fehlmenge / wirkungsgrad
    max_entnahme_leistung = leistung / wirkungsgrad
    
    # Fall 1: Leistung reicht, Kapazität reicht → vollständig decken
    if leistung > fehlmenge and verfuegbar >= benoetigt_fuer_fehlmenge:
        neuer_bestand = aktueller_bestand - benoetigt_fuer_fehlmenge
        return neuer_bestand, fehlmenge, 0.0
    
    # Fall 2: Leistung begrenzt, aber genug Kapazität
    if leistung <= fehlmenge and verfuegbar >= max_entnahme_leistung:
        neuer_bestand = aktueller_bestand - max_entnahme_leistung
        geliefert = leistung
        return neuer_bestand, geliefert, fehlmenge - geliefert
    
    # Fall 3: Kapazität begrenzt (nicht genug im Speicher)
    lieferbar = verfuegbar * wirkungsgrad
    if fehlmenge < lieferbar:
        # Fehlmenge ist kleiner als verfügbar
        neuer_bestand = aktueller_bestand - benoetigt_fuer_fehlmenge
        return neuer_bestand, fehlmenge, 0.0
    else:
        # Alles Verfügbare liefern
        neuer_bestand = min_bestand
        return neuer_bestand, lieferbar, fehlmenge - lieferbar

# Hilfsfunktion zur Aufteilung der Lademenge
def berechne_speicher_aufteilung(
    lademenge: float,
    platz_batterie: float,
    platz_pumpspeicher: float,
    platz_wasserstoff: float,
    leistung_batterie: float,
    leistung_pumpspeicher: float,
    leistung_wasserstoff: float,
    gewicht_kapazitaet: float = 0.5,
    gewicht_leistung: float = 0.5
) -> tuple[float, float, float]:
    """
    Berechnet die Aufteilung der Lademenge auf drei Speichertypen basierend auf
    verfügbarer Kapazität und Leistung mit gewichteter Kombination.
    Erstellt von KI Claude Sonnet 4.5.
    
    Args:
        lademenge: Verfügbare Energie zum Laden in MWh
        platz_batterie: Verfügbarer Platz im Batteriespeicher in MWh
        platz_pumpspeicher: Verfügbarer Platz im Pumpspeicher in MWh
        platz_wasserstoff: Verfügbarer Platz im Wasserstoffspeicher in MWh
        leistung_batterie: Viertelstundenleistung Batterie in MW
        leistung_pumpspeicher: Viertelstundenleistung Pumpspeicher in MW
        leistung_wasserstoff: Viertelstundenleistung Wasserstoff in MW
        gewicht_kapazitaet: Gewichtungsfaktor für verfügbare Kapazität (0-1)
        gewicht_leistung: Gewichtungsfaktor für Leistung (0-1)
    
    Returns:
        (anteil_batterie, anteil_pumpspeicher, anteil_wasserstoff)
    """
    # Gesamtwerte berechnen
    gesamt_platz = platz_batterie + platz_pumpspeicher + platz_wasserstoff
    gesamt_leistung = leistung_batterie + leistung_pumpspeicher + leistung_wasserstoff
    
    # Normalisierte Faktoren berechnen
    norm_platz_batterie = platz_batterie / gesamt_platz if gesamt_platz > 0 else 0
    norm_platz_pump = platz_pumpspeicher / gesamt_platz if gesamt_platz > 0 else 0
    norm_platz_h2 = platz_wasserstoff / gesamt_platz if gesamt_platz > 0 else 0
    
    norm_leistung_batterie = leistung_batterie / gesamt_leistung if gesamt_leistung > 0 else 0
    norm_leistung_pump = leistung_pumpspeicher / gesamt_leistung if gesamt_leistung > 0 else 0
    norm_leistung_h2 = leistung_wasserstoff / gesamt_leistung if gesamt_leistung > 0 else 0
    
    # Gewichtete Kombination TODO: GEWICHTUNG WIRKT SO ÜBERHAUPT NICHT, NACH MS5 ANPASSEN
    gewicht_batterie = (norm_platz_batterie * gewicht_kapazitaet) * (norm_leistung_batterie * gewicht_leistung)
    gewicht_pump = (norm_platz_pump * gewicht_kapazitaet) * (norm_leistung_pump * gewicht_leistung)
    gewicht_h2 = (norm_platz_h2 * gewicht_kapazitaet) * (norm_leistung_h2 * gewicht_leistung)
    
    # Normalisieren und Lademenge aufteilen
    gesamt_gewicht = gewicht_batterie + gewicht_pump + gewicht_h2
    
    if gesamt_gewicht > 0:
        anteil_batterie = lademenge * (gewicht_batterie / gesamt_gewicht)
        anteil_pumpspeicher = lademenge * (gewicht_pump / gesamt_gewicht)
        anteil_wasserstoff = lademenge * (gewicht_h2 / gesamt_gewicht)
    else:
        # Fallback: Gleichverteilung wenn keine Gewichte berechnet werden können
        anteil_batterie = lademenge / 3
        anteil_pumpspeicher = lademenge / 3
        anteil_wasserstoff = lademenge / 3
    
    return anteil_batterie, anteil_pumpspeicher, anteil_wasserstoff


def Verlauf_Speicher(df_anteilEE: pd.DataFrame, entladegrenze: float, ladegrenze: float, ziele_2030: dict, ziele_2045: dict, untergrenze_h2_prozent: float, langzeit_kurzzeit: bool) -> pd.DataFrame:
    """
    Simuliert den Verlauf mit Erzeugung, Verbrauch und Speichern.
    (Optimierte Version mit Hilfsfunktionen und NumPy-Arrays)
    
    Args:
        untergrenze_h2_prozent: Winterladestand für Wasserstoffspeicher in Prozent (0-100)
    """

    bestandBatterie = FIXPARAMETER_BATTERIE.bestand
    bestandWasserstoff = FIXPARAMETER_WASSERSTOFF.bestand
    bestandPumpspeicher = FIXPARAMETER_PUMPSPEICHER.bestand

    # Errechnung der Wirkungsgrade für Lade- und Entladevorgang aus Gesamtwirkungsgrad
    inputWirkungsgradBatterie = Fraction(FIXPARAMETER_BATTERIE.wirkungsgrad + ((1-FIXPARAMETER_BATTERIE.wirkungsgrad)/2))
    inputWirkungsgradWasserstoff = Fraction(FIXPARAMETER_WASSERSTOFF.wirkungsgrad + ((1-FIXPARAMETER_WASSERSTOFF.wirkungsgrad)/2))
    inputWirkungsgradPumpspeicher = Fraction(FIXPARAMETER_PUMPSPEICHER.wirkungsgrad + ((1-FIXPARAMETER_PUMPSPEICHER.wirkungsgrad)/2)) 

    outputWirkungsgradBatterie = Fraction(inputWirkungsgradBatterie.numerator - 1, inputWirkungsgradBatterie.denominator - 1)
    outputWirkungsgradWasserstoff = Fraction(inputWirkungsgradWasserstoff.numerator - 1, inputWirkungsgradWasserstoff.denominator - 1)
    outputWirkungsgradPumpspeicher = Fraction(inputWirkungsgradPumpspeicher.numerator - 1, inputWirkungsgradPumpspeicher.denominator - 1)

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

    # DataFrame-Spalten als NumPy-Arrays extrahieren
    erneuerbare = df_gesamtVerlauf["Erneuerbare [MWh]"].values
    netzlast = df_gesamtVerlauf["Netzlast [MWh]"].values
    anteil_ee = df_gesamtVerlauf["Anteil Erneuerbare [%]"].values
    
    leistung_batterie = df_gesamtVerlauf["Viertelstundenleistung batteriespeicher [MW]"].values
    leistung_wasserstoff = df_gesamtVerlauf["Viertelstundenleistung wasserstoff [MW]"].values
    leistung_pumpspeicher = df_gesamtVerlauf["Viertelstundenleistung pumpspeicher [MW]"].values
    
    kap_batterie = df_gesamtVerlauf["Speicherkapazität batteriespeicher [MWh]"].values
    kap_wasserstoff = df_gesamtVerlauf["Speicherkapazität wasserstoff [MWh]"].values
    kap_pumpspeicher = df_gesamtVerlauf["Speicherkapazität pumpspeicher [MWh]"].values

    datum_series = pd.to_datetime(df_gesamtVerlauf["Datum von"])
    monate = datum_series.dt.month.values

    # Untergrenze-Array erstellen
    untergrenzen_h2 = np.where(
        (monate >= 11) | (monate <= 2),  # Winter
        0.00,
        np.where(
            (monate >= 3) & (monate <= 10),  # nicht Winter
            untergrenze_h2_prozent / 100,
            FIXPARAMETER_WASSERSTOFF.untergrenze  # Standard
        )
    )

    # Listen für Ergebnisse initialisieren
    speicherstand_batterie = []
    speicherstand_wasserstoff = []
    speicherstand_pumpspeicher = []
    zusatz_energie = []
    fehl_energie = []
    ueber_energie = []
    ueber_energie_post = []

    # Anfangswerte Ladestand (Annahme: 25% geladen im Januar 2026)
    aktuell_batterie = bestandBatterie * 0.25 * 1e3 
    aktuell_wasserstoff = bestandWasserstoff * 0.25 * 1e3
    aktuell_pumpspeicher = bestandPumpspeicher * 0.25 * 1e3

    # Export/Import über den gesamten Zeitraum
    exportEnergie = 0
    importEnergie = 0

    # Debug-Zählvariable für das Laden der Kurzzeitspeicher aus Langzeitspeicher
    # debug_kurzzeitladen = 0

    # Simulation über alle Zeitpunkte
    if langzeit_kurzzeit:
        # Version MIT Batterie-aus-H2-Laden
        for idx in range(len(erneuerbare)):
            
            erzeugung = erneuerbare[idx]
            aktuell_zusatz_energie = 0
            fehlmenge = 0
            lademenge = 0
            rest = 0 #übergebliebene Energie nach Laden
            geliefert = 0 #gelieferte Energie beim Entladen
            verbrauchte_leistung_batterie = 0 #Tracking für gegenseitiges Speicherladen
            verbrauchte_leistung_wasserstoff = 0 #Tracking für gegenseitiges Speicherladen

            
            # Speicher laden
            if anteil_ee[idx] > ladegrenze:  # Überschüssige Energie vorhanden
            
                lademenge = erzeugung - netzlast[idx] * (ladegrenze / 100)

                ueber_energie.append(lademenge)

                # Verfügbaren Platz berechnen
                platz_batterie = (kap_batterie[idx] * FIXPARAMETER_BATTERIE.obergrenze) - aktuell_batterie
                platz_pump = (kap_pumpspeicher[idx] * FIXPARAMETER_PUMPSPEICHER.obergrenze) - aktuell_pumpspeicher
                platz_h2 = (kap_wasserstoff[idx] * FIXPARAMETER_WASSERSTOFF.obergrenze) - aktuell_wasserstoff

                # Aufteilung berechnen
                anteil_batterie, anteil_pump, anteil_h2 = berechne_speicher_aufteilung(
                lademenge,
                platz_batterie,
                platz_pump,
                platz_h2,
                leistung_batterie[idx],
                leistung_pumpspeicher[idx],
                leistung_wasserstoff[idx],
                0.5,  # Optional: Standard ist 0.5
                0.5   # Optional: Standard ist 0.5
                )

                # Batterie laden
                aktuell_batterie, rest = speicher_laden(
                    aktuell_batterie, anteil_batterie, leistung_batterie[idx],
                    kap_batterie[idx], FIXPARAMETER_BATTERIE.obergrenze, inputWirkungsgradBatterie
                )
                
                verbrauchte_leistung_batterie = (anteil_batterie - rest) / inputWirkungsgradBatterie
                lademenge -= (anteil_batterie - rest)

                # Pumpspeicher laden
                aktuell_pumpspeicher, rest = speicher_laden(
                    aktuell_pumpspeicher, anteil_pump, leistung_pumpspeicher[idx],
                    kap_pumpspeicher[idx], FIXPARAMETER_PUMPSPEICHER.obergrenze, inputWirkungsgradPumpspeicher
                )

                lademenge -= (anteil_pump - rest)
                
                # Wasserstoff laden
                aktuell_wasserstoff, rest = speicher_laden(
                    aktuell_wasserstoff, anteil_h2, leistung_wasserstoff[idx],
                    kap_wasserstoff[idx], FIXPARAMETER_WASSERSTOFF.obergrenze, inputWirkungsgradWasserstoff
                )

                lademenge -= (anteil_h2 - rest)

            # Speicher entladen
            elif anteil_ee[idx] <= entladegrenze:  # Fehlende Energie vorhanden

                fehlmenge = netzlast[idx] * (entladegrenze / 100) - erzeugung

                ueber_energie.append(lademenge)

                # Batterie entladen
                aktuell_batterie, geliefert, fehlmenge = speicher_entladen(
                    aktuell_batterie, fehlmenge, leistung_batterie[idx],
                    kap_batterie[idx], FIXPARAMETER_BATTERIE.untergrenze, outputWirkungsgradBatterie
                )
                aktuell_zusatz_energie += geliefert
                
                # Pumpspeicher entladen
                aktuell_pumpspeicher, geliefert, fehlmenge = speicher_entladen(
                    aktuell_pumpspeicher, fehlmenge, leistung_pumpspeicher[idx],
                    kap_pumpspeicher[idx], FIXPARAMETER_PUMPSPEICHER.untergrenze, outputWirkungsgradPumpspeicher
                )
                aktuell_zusatz_energie += geliefert
                
                # Wasserstoff entladen
                aktuell_wasserstoff, geliefert, fehlmenge = speicher_entladen(
                    aktuell_wasserstoff, fehlmenge, leistung_wasserstoff[idx],
                    kap_wasserstoff[idx], untergrenzen_h2[idx], outputWirkungsgradWasserstoff
                )

                verbrauchte_leistung_wasserstoff = geliefert 
                aktuell_zusatz_energie += geliefert

        
            # Kurzzeitspeicher aus Langzeitspeicher auffüllen
            if (
                aktuell_batterie < (1.1 * leistung_batterie[idx] / FIXPARAMETER_BATTERIE.wirkungsgrad) and 
                aktuell_wasserstoff > (FIXPARAMETER_WASSERSTOFF.untergrenze * kap_wasserstoff[idx]) and
                (leistung_wasserstoff[idx] - verbrauchte_leistung_wasserstoff) > 0 and
                (leistung_batterie[idx] - verbrauchte_leistung_batterie) > 0
                ):

                fehlmenge_batterie = (1.1 * leistung_batterie[idx] / FIXPARAMETER_BATTERIE.wirkungsgrad) - aktuell_batterie
                geliefert = 0 #sicherheitshalber zurücksetzen

                # Wasserstoff entladen um Batterie zu füllen
                aktuell_wasserstoff, geliefert, fehlmenge_batterie = speicher_entladen(
                    aktuell_wasserstoff, fehlmenge_batterie, (leistung_wasserstoff[idx] - verbrauchte_leistung_wasserstoff),
                    kap_wasserstoff[idx], untergrenzen_h2[idx], outputWirkungsgradWasserstoff
                )
                
                # Batterie laden mit gelieferter Energie
                aktuell_batterie, rest = speicher_laden(
                    aktuell_batterie, geliefert, (leistung_batterie[idx]-verbrauchte_leistung_batterie),
                    kap_batterie[idx], FIXPARAMETER_BATTERIE.obergrenze, inputWirkungsgradBatterie
                )

            # debug_kurzzeitladen += 1
            # print(f"Anzahl Kurzzeitladen aus Langzeitspeicher: {debug_kurzzeitladen}", end='\n')

            exportEnergie += lademenge #TODO: Außerhalb berechnen
            importEnergie += fehlmenge #TODO: Außerhalb berechnen

            speicherstand_batterie.append(aktuell_batterie)
            speicherstand_wasserstoff.append(aktuell_wasserstoff)   
            speicherstand_pumpspeicher.append(aktuell_pumpspeicher)  
            zusatz_energie.append(aktuell_zusatz_energie)   
            fehl_energie.append(fehlmenge)
            ueber_energie_post.append(lademenge)

            # Langzeitverluste der Speicher jede Stunde
            if idx % 4 == 0:
                aktuell_batterie -= ((FIXPARAMETER_BATTERIE.verluste/100) * aktuell_batterie)
                aktuell_wasserstoff -= ((FIXPARAMETER_WASSERSTOFF.verluste/100) * aktuell_wasserstoff)
                aktuell_pumpspeicher -= ((FIXPARAMETER_PUMPSPEICHER.verluste/100) * aktuell_pumpspeicher)
    else:
        # Version OHNE Batterie-aus-H2-Laden (effizienter)
        for idx in range(len(erneuerbare)):
            
            erzeugung = erneuerbare[idx]
            aktuell_zusatz_energie = 0
            fehlmenge = 0
            lademenge = 0
            rest = 0
            geliefert = 0

            # Speicher laden
            if anteil_ee[idx] > ladegrenze:
                
                lademenge = erzeugung - netzlast[idx] * (ladegrenze / 100)
                ueber_energie.append(lademenge)

                platz_batterie = (kap_batterie[idx] * FIXPARAMETER_BATTERIE.obergrenze) - aktuell_batterie
                platz_pump = (kap_pumpspeicher[idx] * FIXPARAMETER_PUMPSPEICHER.obergrenze) - aktuell_pumpspeicher
                platz_h2 = (kap_wasserstoff[idx] * FIXPARAMETER_WASSERSTOFF.obergrenze) - aktuell_wasserstoff

                anteil_batterie, anteil_pump, anteil_h2 = berechne_speicher_aufteilung(
                    lademenge, platz_batterie, platz_pump, platz_h2,
                    leistung_batterie[idx], leistung_pumpspeicher[idx], leistung_wasserstoff[idx], 0.5, 0.5
                )

                aktuell_batterie, rest = speicher_laden(
                    aktuell_batterie, anteil_batterie, leistung_batterie[idx],
                    kap_batterie[idx], FIXPARAMETER_BATTERIE.obergrenze, inputWirkungsgradBatterie
                )
                lademenge -= (anteil_batterie - rest)

                aktuell_pumpspeicher, rest = speicher_laden(
                    aktuell_pumpspeicher, anteil_pump, leistung_pumpspeicher[idx],
                    kap_pumpspeicher[idx], FIXPARAMETER_PUMPSPEICHER.obergrenze, inputWirkungsgradPumpspeicher
                )
                lademenge -= (anteil_pump - rest)
                
                aktuell_wasserstoff, rest = speicher_laden(
                    aktuell_wasserstoff, anteil_h2, leistung_wasserstoff[idx],
                    kap_wasserstoff[idx], FIXPARAMETER_WASSERSTOFF.obergrenze, inputWirkungsgradWasserstoff
                )
                lademenge -= (anteil_h2 - rest)

            elif anteil_ee[idx] <= entladegrenze:
                
                fehlmenge = netzlast[idx] * (entladegrenze / 100) - erzeugung
                ueber_energie.append(lademenge)

                aktuell_batterie, geliefert, fehlmenge = speicher_entladen(
                    aktuell_batterie, fehlmenge, leistung_batterie[idx],
                    kap_batterie[idx], FIXPARAMETER_BATTERIE.untergrenze, outputWirkungsgradBatterie
                )
                aktuell_zusatz_energie += geliefert
                
                aktuell_pumpspeicher, geliefert, fehlmenge = speicher_entladen(
                    aktuell_pumpspeicher, fehlmenge, leistung_pumpspeicher[idx],
                    kap_pumpspeicher[idx], FIXPARAMETER_PUMPSPEICHER.untergrenze, outputWirkungsgradPumpspeicher
                )
                aktuell_zusatz_energie += geliefert
                
                aktuell_wasserstoff, geliefert, fehlmenge = speicher_entladen(
                    aktuell_wasserstoff, fehlmenge, leistung_wasserstoff[idx],
                    kap_wasserstoff[idx], untergrenzen_h2[idx], outputWirkungsgradWasserstoff
                )
                aktuell_zusatz_energie += geliefert

            exportEnergie += lademenge
            importEnergie += fehlmenge

            speicherstand_batterie.append(aktuell_batterie)
            speicherstand_wasserstoff.append(aktuell_wasserstoff)   
            speicherstand_pumpspeicher.append(aktuell_pumpspeicher)  
            zusatz_energie.append(aktuell_zusatz_energie)   
            fehl_energie.append(fehlmenge)
            ueber_energie_post.append(lademenge)

            if idx % 4 == 0:
                aktuell_batterie -= ((FIXPARAMETER_BATTERIE.verluste/100) * aktuell_batterie)
                aktuell_wasserstoff -= ((FIXPARAMETER_WASSERSTOFF.verluste/100) * aktuell_wasserstoff)
                aktuell_pumpspeicher -= ((FIXPARAMETER_PUMPSPEICHER.verluste/100) * aktuell_pumpspeicher)

    df_gesamtVerlauf["Ladestand batteriespeicher [MWh]"] = speicherstand_batterie
    df_gesamtVerlauf["Ladestand wasserstoff [MWh]"] = speicherstand_wasserstoff
    df_gesamtVerlauf["Ladestand pumpspeicher [MWh]"] = speicherstand_pumpspeicher 
    df_gesamtVerlauf["Energie aus Speicher [MWh]"] = zusatz_energie
    df_gesamtVerlauf["Fehlende Energie [MWh]"] = fehl_energie
    df_gesamtVerlauf["Überschüssige Energie vor Laden [MWh]"] = ueber_energie
    df_gesamtVerlauf["Überschüssige Energie nach Laden [MWh]"] = ueber_energie_post


    if(df_gesamtVerlauf.isna().any().any()):
        raise ValueError("Fehlende Werte nach Speicherprognose entdeckt.")

    # Debug-Code
    # df_gesamtVerlauf.to_csv(DATA_DIR / 'Output' / 'debug_gesamtverlauf_neu.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    return df_gesamtVerlauf


def Simulation_Dunkelflaute(df_verlauf: pd.DataFrame, jahr: int):
    """
    Simuliert den Verlauf einer Dunkelflaute
    (Optimierte Version mit Hilfsfunktionen und NumPy-Arrays)
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
    df_verlauf_dunkelflaute.loc[mask, 'Wind Offshore [MWh] Originalauflösungen'] = df_verlauf_dunkelflaute.loc[mask, 'Installierte Wind_Offshore_GW'] * 1000 * 0.25 * df_verlauf_dunkelflaute.loc[mask, 'faktor']
    df_verlauf_dunkelflaute.loc[mask, 'Wind Onshore [MWh] Originalauflösungen'] = df_verlauf_dunkelflaute.loc[mask, 'Installierte Wind_Onshore_GW'] * 1000 * 0.25 * df_verlauf_dunkelflaute.loc[mask, 'faktor']
    df_verlauf_dunkelflaute.loc[mask, 'Photovoltaik [MWh] Originalauflösungen'] = df_verlauf_dunkelflaute.loc[mask, 'Installierte PV_GW'] * 1000 * 0.25 * df_verlauf_dunkelflaute.loc[mask, 'faktor']

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
    
    # Reduziere DataFrame auf Simulationszeitraum für Array-Extraktion
    df_simulation = df_verlauf_dunkelflaute.loc[mask_simulation].reset_index(drop=True)
    
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
    
    # ===== OPTIMIERUNG: DataFrame-Spalten als NumPy-Arrays extrahieren =====
    erneuerbare = df_simulation["Erneuerbare [MWh]"].values
    netzlast = df_simulation["Netzlast [MWh]"].values
    anteil_ee = df_simulation["Anteil Erneuerbare [%]"].values
    
    leistung_batterie = df_simulation["Viertelstundenleistung batteriespeicher [MW]"].values
    leistung_wasserstoff = df_simulation["Viertelstundenleistung wasserstoff [MW]"].values
    leistung_pumpspeicher = df_simulation["Viertelstundenleistung pumpspeicher [MW]"].values
    
    kap_batterie = df_simulation["Speicherkapazität batteriespeicher [MWh]"].values
    kap_wasserstoff = df_simulation["Speicherkapazität wasserstoff [MWh]"].values
    kap_pumpspeicher = df_simulation["Speicherkapazität pumpspeicher [MWh]"].values
    
    # Listen für Ergebnisse
    speicherstand_batterie = []
    speicherstand_wasserstoff = []
    speicherstand_pumpspeicher = []
    zusatz_energie = []
    fehl_energie = []
    ueber_energie = []
    ueber_energie_post = []

    
    # Simulation über alle Zeitpunkte im Simulationszeitraum
    for idx in range(len(erneuerbare)):
        
        erzeugung = erneuerbare[idx]
        aktuell_zusatz_energie = 0
        fehlmenge = 0
        lademenge = 0

        if anteil_ee[idx] > ladegrenze:  # Überschüssige Energie vorhanden
            
            lademenge = erzeugung - netzlast[idx] * (ladegrenze / 100)

            ueber_energie.append(lademenge)

            # Batterie laden
            aktuell_batterie, lademenge = speicher_laden(
                aktuell_batterie, lademenge, leistung_batterie[idx],
                kap_batterie[idx], FIXPARAMETER_BATTERIE.obergrenze, inputWirkungsgradBatterie
            )
            
            # Pumpspeicher laden
            aktuell_pumpspeicher, lademenge = speicher_laden(
                aktuell_pumpspeicher, lademenge, leistung_pumpspeicher[idx],
                kap_pumpspeicher[idx], FIXPARAMETER_PUMPSPEICHER.obergrenze, inputWirkungsgradPumpspeicher
            )
            
            # Wasserstoff laden
            aktuell_wasserstoff, lademenge = speicher_laden(
                aktuell_wasserstoff, lademenge, leistung_wasserstoff[idx],
                kap_wasserstoff[idx], FIXPARAMETER_WASSERSTOFF.obergrenze, inputWirkungsgradWasserstoff
            )

            exportEnergie += lademenge

        elif anteil_ee[idx] <= entladegrenze:  # Fehlende Energie vorhanden

            fehlmenge = netzlast[idx] * (entladegrenze / 100) - erzeugung

            ueber_energie.append(lademenge)

            # Batterie entladen
            aktuell_batterie, geliefert, fehlmenge = speicher_entladen(
                aktuell_batterie, fehlmenge, leistung_batterie[idx],
                kap_batterie[idx], FIXPARAMETER_BATTERIE.untergrenze, outputWirkungsgradBatterie
            )
            aktuell_zusatz_energie += geliefert
            
            # Pumpspeicher entladen
            aktuell_pumpspeicher, geliefert, fehlmenge = speicher_entladen(
                aktuell_pumpspeicher, fehlmenge, leistung_pumpspeicher[idx],
                kap_pumpspeicher[idx], FIXPARAMETER_PUMPSPEICHER.untergrenze, outputWirkungsgradPumpspeicher
            )
            aktuell_zusatz_energie += geliefert
            
            # Wasserstoff entladen
            aktuell_wasserstoff, geliefert, fehlmenge = speicher_entladen(
                aktuell_wasserstoff, fehlmenge, leistung_wasserstoff[idx],
                kap_wasserstoff[idx], FIXPARAMETER_WASSERSTOFF.untergrenze, outputWirkungsgradWasserstoff
            )
            aktuell_zusatz_energie += geliefert

            importEnergie += fehlmenge 
        
        speicherstand_batterie.append(aktuell_batterie)
        speicherstand_wasserstoff.append(aktuell_wasserstoff)   
        speicherstand_pumpspeicher.append(aktuell_pumpspeicher)  
        zusatz_energie.append(aktuell_zusatz_energie)   
        fehl_energie.append(fehlmenge)
        ueber_energie_post.append(lademenge)

        # Langzeitverluste der Speicher jede Stunde
        if idx % 4 == 0:
            aktuell_batterie -= ((FIXPARAMETER_BATTERIE.verluste/100) * aktuell_batterie)
            aktuell_wasserstoff -= ((FIXPARAMETER_WASSERSTOFF.verluste/100) * aktuell_wasserstoff)
            aktuell_pumpspeicher -= ((FIXPARAMETER_PUMPSPEICHER.verluste/100) * aktuell_pumpspeicher)

    # Ergebnisse in den reduzierten DataFrame schreiben
    df_simulation["Ladestand batteriespeicher [MWh]"] = speicherstand_batterie
    df_simulation["Ladestand wasserstoff [MWh]"] = speicherstand_wasserstoff
    df_simulation["Ladestand pumpspeicher [MWh]"] = speicherstand_pumpspeicher 
    df_simulation["Energie aus Speicher [MWh]"] = zusatz_energie
    df_simulation["Fehlende Energie [MWh]"] = fehl_energie
    df_simulation["Überschüssige Energie vor Laden [MWh]"] = ueber_energie
    df_simulation["Überschüssige Energie nach Laden [MWh]"] = ueber_energie_post
    
    return df_simulation

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

    anzahl_tage_2030 = len(df_2030["Datum von"].dt.date.unique()) # type: ignore
    
    wachstumsrate_2030 = (bestand2030 - bestand2025) / anzahl_tage_2030

    speichername = f"Speicherkapazität {speicherart} [MWh]"
    
    df_2030[speichername] = bestand2025 + wachstumsrate_2030 * ((df_2030['Datum von'] - df_2030['Datum von'].min()).dt.days + 1)

    # df_2030.to_csv(DATA_DIR / 'Output' / 'speicherprognosetest2030.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')

    #=== Dataframe für die Jahre 2030 bis 2045 erstellen ===
    date_range = pd.date_range(start='2031-01-01', end='2045-12-31 23:45', freq='15min',tz="UTC")
    df_2045 = pd.DataFrame({'Datum von': date_range})

    anzahl_tage_2045 = len(df_2045["Datum von"].dt.date.unique()) # type: ignore
    
    wachstumsrate_2045 = (bestand2045 - bestand2030) / anzahl_tage_2045

    df_2045[speichername] = bestand2030 + wachstumsrate_2045 * ((df_2045['Datum von'] - df_2045['Datum von'].min()).dt.days + 1)

    df_gesamt = pd.concat([df_2030, df_2045], ignore_index=True) # Bereich von 2026 bis 2030 und 2031 bis 2045 zusammenfügen
    df_gesamt[speichername] = df_gesamt[speichername].round(2)

    vierteltunden_leistung_spalte = f"Viertelstundenleistung {speicherart} [MW]"
    match speicherart:
        case "batteriespeicher": FIXPARAMETER_SPEICHERART = FIXPARAMETER_BATTERIE
        case "wasserstoff": FIXPARAMETER_SPEICHERART = FIXPARAMETER_WASSERSTOFF
        case "pumpspeicher": FIXPARAMETER_SPEICHERART = FIXPARAMETER_PUMPSPEICHER
        case _: raise ValueError(f"Unbekannte Speicherart: {speicherart}")
    
    df_gesamt[vierteltunden_leistung_spalte] = df_gesamt[speichername] * (FIXPARAMETER_SPEICHERART.leistung / 4)

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