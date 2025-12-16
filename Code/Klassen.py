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
from Histogramme import plot_ee_anteil_histogram_overflow,plot_histogram_ausbauraten_EE,plot_histogram_energie_nichtEE,plot_histogram_ausbauraten_Speicher,kosten, plot_Anteil_EE_mit_ohne_Speicher
from EE_Anteil_DataFrame import anteil_erneuerbare_df, anteil_erneuerbare_speicher
from Kosten import kostenrechnung
# from Prognose_Speicher import Verlauf_Speicher, ausbaurate_GWh_Jahr
import Prognose_Speicher as speicher
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
    verbrauchsprofile: json
    veränderungsfaktoren: dict
    
    erzeugung_df: Optional[pd.DataFrame] = None
    verbrauch_df: Optional[pd.DataFrame] = None
    ee_anteil_ohne_speicher_df: Optional[pd.DataFrame] = None
    kosten_df: Optional[pd.DataFrame] = None
    speicher_df: Optional[pd.DataFrame] = None
    dunkelflaute_2030_df: Optional[pd.DataFrame] = None
    dunkelflaute_2045_df: Optional[pd.DataFrame] = None
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
            self.verbrauchsprofile["Verbrauch_2030"],
            self.verbrauchsprofile["Verbrauch_2045"]
        )
        
        self.ee_anteil_ohne_speicher_df = anteil_erneuerbare_df(
            self.erzeugung_df, 
            self.verbrauch_df
        )
        
        self.kosten_df = kostenrechnung(self.szenario)
        
        self.speicher_df = speicher.Verlauf_Speicher(self.ee_anteil_ohne_speicher_df, 100, 100, self.ziele_2030, self.ziele_2045)

        self.dunkelflaute_2030_df = speicher.Simulation_Dunkelflaute(self.speicher_df, 2030)
        self.dunkelflaute_2045_df = speicher.Simulation_Dunkelflaute(self.speicher_df, 2045)

        # --FIXME: in Auswertung einpflegen?--
        self.dunkelflaute_2030_df.to_csv(DATA_DIR / 'Output' / 'dunkelflaute_2030.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')
        self.dunkelflaute_2045_df.to_csv(DATA_DIR / 'Output' / 'dunkelflaute_2045.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')
        # ------------------------------------

        self.gesamt_df = anteil_erneuerbare_speicher(self.speicher_df)
        
        self.konventionelle = konventionelle_Leistung_Energie(self.gesamt_df)
        
        print(f"✓ Berechnungen für '{self.name}' abgeschlossen.")
    
    def auswertungsdaten_generieren(self):
        """Generiert die Auswertungsdaten"""
        return ausgabe(self.kosten_df, self.gesamt_df, self.szenario,self.konventionelle)

    def exportiere_ergebnisse(self):
        """Exportiert alle Ergebnisse nach Excel"""
        pfad = DATA_DIR/ "Output" / f"szenario_{self.name}_auswertung_ertrag_{self.ertragsart}.xlsx"
        df = ausgabe(self.kosten_df, self.gesamt_df, self.szenario,self.konventionelle)
        with pd.ExcelWriter(pfad, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Jahresübersicht", index=False)
        
    def zeige_plots(self, jahr1=None,speichern: bool=False):
        """Zeigt Histogramme und Analysen"""
        pfad = DATA_DIR/ "Output" / f"szenario_{self.name}_auswertung_ertrag_{self.ertragsart}_plots.png" #FIXME wozu steht der hier?

        fig, axs = plt.subplots(2,  figsize=(14, 12)) 
        fig2, axs2 = plt.subplots(1, 2, figsize=(14, 12)) 
        fig3, axs3 = plt.subplots(1, 2, figsize=(14, 12)) 
        fig4, axs4 = plt.subplots(2, figsize=(14, 12))
        fig5, axs5 = plt.subplots(1, figsize=(14, 12))

        plot_Anteil_EE_mit_ohne_Speicher(self.gesamt_df, axs5)
        plot_ee_anteil_histogram_overflow(self.gesamt_df, jahr1, axs[1])
        plot_histogram_energie_nichtEE(self.konventionelle,axs[0])
        kosten(self.kosten_df, axs2[0], axs2[1])
        plot_histogram_ausbauraten_EE(self.ziele_2030["Ausbau EE"], self.ziele_2045["Ausbau EE"], axs3[0],axs4[0])
        plot_histogram_ausbauraten_Speicher(self.szenario, axs3[1],axs4[1]) 
        plt.tight_layout()
        
        if(speichern):
            fig.savefig(DATA_DIR/ "Output" / f"szenario_{self.name}_auswertung_ertrag_{self.ertragsart}_plots1.png", dpi=300, bbox_inches='tight', format='png')
            fig2.savefig(DATA_DIR/ "Output" / f"szenario_{self.name}_auswertung_ertrag_{self.ertragsart}_plots2.png", dpi=300, bbox_inches='tight', format='png')
            fig3.savefig(DATA_DIR/ "Output" / f"szenario_{self.name}_auswertung_ertrag_{self.ertragsart}_plots3.png", dpi=300, bbox_inches='tight', format='png')
            fig4.savefig(DATA_DIR/ "Output" / f"szenario_{self.name}_auswertung_ertrag_{self.ertragsart}_plots4.png", dpi=300, bbox_inches='tight', format='png')
        plt.show()

    def gebe_plots(self, jahr1=None):
        """
        Erstellt alle Plots und gibt sie als Dictionary von Figure-Objekten zurück.
        Perfekt für Streamlit: st.pyplot(figures['fig1'])
        
        Returns:
            dict: Dictionary mit Figure-Objekten
                - 'fig1': EE-Anteil und Energie nicht-EE
                - 'fig2': Kosten-Analyse
                - 'fig3': Ausbauraten EE und Speicher
                - 'fig4': Detaillierte Ausbauraten
                - 'fig5': EE-Anteil mit/ohne Speicher
        """
        fig1, axs1 = plt.subplots(2, figsize=(14, 12)) 
        fig2, axs2 = plt.subplots(1, 2, figsize=(14, 12)) 
        fig3, axs3 = plt.subplots(1, 2, figsize=(14, 12)) 
        fig4, axs4 = plt.subplots(2, figsize=(14, 12))
        fig5, axs5 = plt.subplots(1, figsize=(14, 12))

        plot_Anteil_EE_mit_ohne_Speicher(self.gesamt_df, axs5)
        plot_ee_anteil_histogram_overflow(self.gesamt_df, jahr1, axs1[1])
        plot_histogram_energie_nichtEE(self.konventionelle, axs1[0])
        kosten(self.kosten_df, axs2[0], axs2[1])
        plot_histogram_ausbauraten_EE(self.ziele_2030["Ausbau EE"], self.ziele_2045["Ausbau EE"], axs3[0], axs4[0])
        plot_histogram_ausbauraten_Speicher(self.szenario, axs3[1], axs4[1])
        
        fig1.tight_layout()
        fig2.tight_layout()
        fig3.tight_layout()
        fig4.tight_layout()
        fig5.tight_layout()
        
        return {
            'fig1': fig1,  # EE-Anteil Histogram + Energie nicht-EE
            'fig2': fig2,  # Kosten-Analyse
            'fig3': fig3,  # Ausbauraten EE und Speicher (Übersicht)
            'fig4': fig4,  # Detaillierte Ausbauraten
            'fig5': fig5   # EE-Anteil mit/ohne Speicher
        }
    
    def getErgebnisse(self) -> pd.DataFrame:
        """Gibt die Ergebnisse als DataFrame zurück"""
        ergebnisse = pd.DataFrame()
        ergebnisse["Name"] = [self.name]
        ausbauraten = Jährlicher_Zuwachs_EE(self.ziele_2030["Ausbau EE"], self.ziele_2045["Ausbau EE"])
        ausbauraten_speicher = speicher.ausbaurate_GWh_Jahr(self.szenario)
        
        ergebnisse["Gesamtkosten_EE [Miliarden €]"] = [self.kosten_df["Gesamtkosten_EE [€]"].sum() / 1e9]
        ergebnisse["Gesamtkosten_Speicher [Miliarden €]"] = [self.kosten_df["Gesamtkosten_Speicher [€]"].sum() / 1e9]
        ergebnisse["Gesamtkosten_EE_und_Speicher [Miliarden €]"] = [self.kosten_df["Gesamtkosten_EE_und_Speicher [€]"].sum() / 1e9]
        
        if "Jahr" not in self.ee_anteil_ohne_speicher_df.columns:
            self.ee_anteil_ohne_speicher_df["Jahr"] = self.ee_anteil_ohne_speicher_df["Datum von"].dt.year
        if "Jahr" not in self.gesamt_df.columns:
            self.gesamt_df["Jahr"] = self.gesamt_df["Datum von"].dt.year
        
        ergebnisse[f"Anteil virtel Stunden mit >=100% EE ohne Speicher 2030 [%]"] = [
            (len(self.ee_anteil_ohne_speicher_df[self.ee_anteil_ohne_speicher_df["Jahr"]==2030]["Anteil Erneuerbare [%]"] >= 100)) / len(self.ee_anteil_ohne_speicher_df[self.ee_anteil_ohne_speicher_df["Jahr"]==2030]) * 100
        ]
        ergebnisse[f"Anteil virtel Stunden mit >=100% EE mit Speicher 2030 [%]"] = [
            (len(self.gesamt_df[self.gesamt_df["Jahr"]==2030]["Anteil Erneuerbare Speicher [%]"] >= 100)) / len(self.gesamt_df[self.gesamt_df["Jahr"]==2030]) * 100
        ]

        ergebnisse[f"Anteil virtel Stunden mit >=100% EE ohne Speicher 2045 [%]"] = [
            (len(self.ee_anteil_ohne_speicher_df[self.ee_anteil_ohne_speicher_df["Jahr"]==2045]["Anteil Erneuerbare [%]"] >= 100)) / len(self.ee_anteil_ohne_speicher_df[self.ee_anteil_ohne_speicher_df["Jahr"]==2045]) * 100
        ]
        ergebnisse[f"Anteil virtel Stunden mit >=100% EE mit Speicher 2045 [%]"] = [
            (len(self.gesamt_df[self.gesamt_df["Jahr"]==2045]["Anteil Erneuerbare Speicher [%]"] >= 100)) / len(self.gesamt_df[self.gesamt_df["Jahr"]==2045]) * 100
        ]

        mask = self.gesamt_df["Anteil Erneuerbare Speicher [%]"] < 100
        nicht_ee_strom = (
            self.gesamt_df.loc[mask, "Netzlast [MWh]"] - 
            self.gesamt_df.loc[mask, "Realisierte Erzeugung [MWh]"]
        ).sum() / 1e6
        ergebnisse["Nicht durch EE gedeckter Strombedarf [TWh]"] = [nicht_ee_strom]
        ergebnisse["Benötigte Leistung Konventioenelle 2045 [GW]"] = [
            self.konventionelle[2045]["Leistung"] / 1e3
        ]
        ergebnisse["Benötigte Leistung Konventioenelle 2030 [GW]"] = [
            self.konventionelle[2030]["Leistung"] / 1e3
        ]

        for key in ausbauraten["zuwachsrate_2030"].keys():
            ergebnisse[f"Ausbaurate {key} 2030"] = [ausbauraten["zuwachsrate_2030"][key]]
            ergebnisse[f"Ausbaurate {key} 2045"] = [ausbauraten["zuwachsrate_2045"][key]]
            ergebnisse[f"Gesamtkosten {key} [Mil. €]"] = [self.kosten_df[f"Gesamtkosten {key} [€]"].sum() / 1e6]

        for key in ausbauraten_speicher["zuwachsrate_2030"].keys():
            ergebnisse[f"Ausbaurate {key} 2030"] = [ausbauraten_speicher["zuwachsrate_2030"][key]]
            ergebnisse[f"Ausbaurate {key} 2045"] = [ausbauraten_speicher["zuwachsrate_2045"][key]]
            ergebnisse[f"Gesamtkosten {key} [Mil. €]"] = [self.kosten_df[f"Gesamtkosten {key} [€]"].sum() / 1e6]

        return ergebnisse