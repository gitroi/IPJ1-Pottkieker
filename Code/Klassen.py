"""
Programmiert von Joris Bürger
"""

import json
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional
from config import DATA_DIR, PROJECT_ROOT
from Analyse import analyse_erneuerbare_anteil
from Prognose_Erzeugung import Prognose_erzeugung, Jährlicher_Zuwachs_EE
from Prognose_Verbrauch import Prognose_Verbrauch
from Histogramme import plot_ee_anteil_histogram_overflow,plot_histogram_ausbauraten_EE
from EE_Anteil_DataFrame import anteil_erneuerbare_df, anteil_erneuerbare_speicher
from Kosten import Kosten_EE
from Prognose_Speicher import Verlauf_Speicher
from Auswertung import ausgabe, konventionelle_Leistung_Energie

@dataclass
class Szenario:
    """Speichert alle Daten und Ergebnisse für ein Szenario"""
    name: str
    beschreibung: str
    szenario: json
    ziele_2030: dict
    ziele_2045: dict
    ertragsart: str
    veränderungsfaktoren: dict
    
    erzeugung_df: Optional[pd.DataFrame] = None
    verbrauch_df: Optional[pd.DataFrame] = None
    ee_anteil_ohne_speicher_df: Optional[pd.DataFrame] = None
    kosten_df: Optional[pd.DataFrame] = None
    speicher_df: Optional[pd.DataFrame] = None
    gesamt_df: Optional[pd.DataFrame] = None
    konventionelle: Optional[dict] = None
    
    def berechne_alle_prognosen(self):
        """Führt alle Berechnungen durch"""
        print(f"Berechne Prognosen für Szenario '{self.name}'...")
        
        self.erzeugung_df = Prognose_erzeugung(
            self.ziele_2030["Ausbau EE"], 
            self.ziele_2045["Ausbau EE"],
            self.veränderungsfaktoren,
            self.ertragsart
        )
        
        self.verbrauch_df = Prognose_Verbrauch(
            self.ziele_2030["Strombedarf"], 
            self.ziele_2045["Strombedarf"]
        )
        
        self.ee_anteil_ohne_speicher_df = anteil_erneuerbare_df(
            self.erzeugung_df, 
            self.verbrauch_df
        )
        
        self.kosten_df = Kosten_EE(self.szenario)
        
        self.speicher_df = Verlauf_Speicher(self.ee_anteil_ohne_speicher_df, 100, 100, self.ziele_2030, self.ziele_2045)
        
        self.gesamt_df = anteil_erneuerbare_speicher(self.speicher_df)
        
        self.konventionelle = konventionelle_Leistung_Energie(self.gesamt_df)
        
        print(f"✓ Berechnungen für '{self.name}' abgeschlossen.")
    
    def exportiere_ergebnisse(self):
        """Exportiert alle Ergebnisse nach Excel"""
        pfad = PROJECT_ROOT/ "Ergebnisse" / f"szenario_{self.name}_auswertung_ertrag_{self.ertragsart}.xlsx"
        ausgabe(self.kosten_df, self.gesamt_df, self.szenario,pfad,self.konventionelle)
    
    def zeige_plots(self, jahr1=None, jahr2=None):
        """Zeigt Histogramme und Analysen"""
        
        self.gesamt_df
        fig, axs = plt.subplots(2, 2, figsize=(14, 12)) 
        plot_ee_anteil_histogram_overflow(self.gesamt_df, jahr1, axs[0, 0])
        plot_ee_anteil_histogram_overflow(self.gesamt_df, jahr2, axs[1, 0])
        plot_histogram_ausbauraten_EE(self.ziele_2030["Ausbau EE"], self.ziele_2045["Ausbau EE"], axs[0, 1])
        plt.tight_layout()
        plt.pause(5)
        plt.close()
    
    def getErgebnisse(self) -> pd.DataFrame:
        """Gibt die Ergebnisse als DataFrame zurück"""
        ergebnisse = pd.DataFrame()
        ergebnisse["Name"] = [self.name]
        ausbauraten = Jährlicher_Zuwachs_EE(self.ziele_2030["Ausbau EE"], self.ziele_2045["Ausbau EE"])
        for key in ausbauraten["zuwachsrate_2030"].keys():
            ergebnisse[f"Ausbaurate {key} 2030"] = [ausbauraten["zuwachsrate_2030"][key]]
            ergebnisse[f"Ausbaurate {key} 2045"] = [ausbauraten["zuwachsrate_2045"][key]]
            ergebnisse[f"Gesamtkosten {key} [Mil. €]"] = [self.kosten_df[f"Gesamtkosten {key} [€]"].sum() / 1e6]

        ergebnisse["Gesamtkosten_EE [Miliarden €]"] = [self.kosten_df["Gesamtkosten_EE [€]"].sum() / 1e9]
        
       
        ergebnisse[f"Anteil virtel Stunden mit >=100% EE ohne Speicher [%]"] = [
            (self.ee_anteil_ohne_speicher_df["Anteil Erneuerbare [%]"] >= 100).sum() / len(self.ee_anteil_ohne_speicher_df) * 100
        ]
        ergebnisse[f"Anteil virtel Stunden mit >=100% EE mit Speicher [%]"] = [
            (self.gesamt_df["Anteil Erneuerbare Speicher [%]"] >= 100).sum() / len(self.gesamt_df) * 100
        ]
        mask = self.gesamt_df["Anteil Erneuerbare Speicher [%]"] < 100
        nicht_ee_strom = (
            self.gesamt_df.loc[mask, "Netzlast [MWh]"] - 
            self.gesamt_df.loc[mask, "Realisierte Erzeugung [MWh]"]
        ).sum() / 1e6
        ergebnisse["Nicht durch EE gedeckter Strombedarf [TWh]"] = [nicht_ee_strom]
        ergebnisse["Benötigte Leistung Konventioennelle 2045 [GW]"] = [
            self.konventionelle["2045"]["Leistung"] / 1e3
        ]
        ergebnisse["Benötigte Leistung Konventioennelle 2030 [GW]"] = [
            self.konventionelle["2030"]["Energie"] / 1e3
        ]

        return ergebnisse