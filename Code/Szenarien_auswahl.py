"Ünterstützt durch KI (GPT-4.1 Inline Suggestions)"
import json
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional
from config import DATA_DIR
from Analyse import analyse_erneuerbare_anteil
from Prognose_Erzeugung import Prognose_erzeugung
from Prognose_Verbrauch import Prognose_Verbrauch
from Histogramme import plot_ee_anteil_histogram_overflow,plot_histogram_ausbauraten_EE
from EE_Anteil_DataFrame import anteil_erneuerbare_df, anteil_erneuerbare_speicher
from Kosten import Kosten_EE
from Prognose_Speicher import Verlauf_Speicher
from Auswertung import ausgabe

def load_scenarios():
    """Lädt Szenarien aus einer JSON-Datei."""
    pfad = DATA_DIR / "szenarien.json"

    with open(pfad, 'r', encoding='utf-8') as datei:
        scenarios = json.load(datei)

    return scenarios

def get_scenario_by_name(szenarien, name):
    """Gibt ein Szenario basierend auf dem Namen zurück."""
    for szenario in szenarien:
        if szenario["Name"] == name:
            return szenario
    return None

# def prognose_eines_Szenarios():
#     szenarien = load_scenarios()
    
#     print("Verfügbare Szenarien:")
#     for szenario in szenarien:
#         print(f"- {szenario['Name']}")
    
#     auswahl = input("Bitte geben Sie den Namen des gewünschten Szenarios ein: ")
#     jahr = input("Bitte geben Sie das erste Jahr für die Analyse ein (z.B. 2026 oder nichts für alle Jahre): ")
#     jahr_2 = input("Bitte geben Sie das zweite Jahr für die Analyse ein (z.B. 2030 oder nichts für alle Jahre): ")
#     ertragsart = input("Bitte geben Sie die Ertragsart ein (schlecht, mittel, gut): ")
#     gewaehltes_szenario = get_scenario_by_name(szenarien, auswahl)
    
#     if gewaehltes_szenario:
#         print(f"Szenario '{auswahl}' wurde ausgewählt und wird ausgegeben.")
#         prognose_erzeugung = Prognose_erzeugung(gewaehltes_szenario["Ziele 2030"]["Ausbau EE"], gewaehltes_szenario["Ziele 2045"]["Ausbau EE"], ertragsart)
#         prognose_verbrauch = Prognose_Verbrauch(gewaehltes_szenario["Ziele 2030"]["Strombedarf"], gewaehltes_szenario["Ziele 2045"]["Strombedarf"])
#         prognose_speicher = Verlauf_Speicher(anteil_erneuerbare_df(prognose_erzeugung,prognose_verbrauch), 100, 100)
#         gesamt = anteil_erneuerbare_speicher(prognose_speicher)
#         # prognose_speicher.to_excel(DATA_DIR / f"szenario_{auswahl}_speicherverlauf.xlsx")
        
#         if (jahr.strip().isdigit()) and (jahr_2.strip().isdigit()) :
#             jahr_int = int(jahr)
#             jahr_int_2 = int(jahr_2)
#         elif (jahr.strip().isdigit()) and (not jahr_2.strip().isdigit()):
#             jahr_int = int(jahr)
#             jahr_int_2 = 0
#         elif (not jahr.strip().isdigit()) and (jahr_2.strip().isdigit()):
#             jahr_int = 0
#             jahr_int_2 = int(jahr_2)  
#         else:
#             jahr_int = 0
#             jahr_int_2 = 0
        
#         prognose_kosten = Kosten_EE(gewaehltes_szenario)
#         print(f"Die Gesamtkosten für das Szenario belaufen sich auf {round(prognose_kosten['Gesamtkosten_EE [€]'].sum()/1e12 ,2)} Billionen Euro.")
        
#         #=== Visualisierungen ===#
#         fig, axs = plt.subplots(2, 2, figsize=(14, 12)) 
#         # ee_gesamt_2045 = gesamt[pd.to_datetime(gesamt["Datum von"]).dt.year == 2045]["Erneuerbare [MWh]"].sum()
#         # verbrauch_gesamt_2045 = gesamt[pd.to_datetime(gesamt["Datum von"]).dt.year == 2045]["Netzlast [MWh]"].sum()
#         # print(f"Im Jahr 2045 beträgt der Anteil der Erneuerbaren Energien am Stromverbrauch {round((ee_gesamt_2045 / verbrauch_gesamt_2045)*100,2)}%.")
#         # print(f"Die erzeugte Energiemenge aus Erneuerbaren Energien im Jahr 2045 beträgt {round(ee_gesamt_2045/1e6,2)} TWh.")
#         # print(f"Der Stromverbrauch im Jahr 2045 beträgt {round(verbrauch_gesamt_2045/1e6,2)} TWh.")
#         plot_ee_anteil_histogram_overflow(gesamt,jahr_int,axs[0, 0])
#         plot_ee_anteil_histogram_overflow(gesamt,jahr_int_2,axs[1, 0])
#         plot_histogram_ausbauraten_EE(gewaehltes_szenario["Ziele 2030"]["Ausbau EE"], gewaehltes_szenario["Ziele 2045"]["Ausbau EE"], axs[0, 1])
#         plt.tight_layout()
#         plt.pause(10)
#         plt.close(fig)

        
#         excel = input("Möchten Sie die Ergebnisse in einer Excel-Datei speichern? (ja/nein): ")
#         if excel.lower() == "ja":
#             ausgabe(prognose_kosten, gesamt, gewaehltes_szenario)
#             print("Ergebnisse wurden in gespeichert.")
        


#         return
#     else:
#         print(f"Szenario '{auswahl}' nicht gefunden.")
#         return None

@dataclass
class SzenarioErgebnis:
    """Speichert alle Daten und Ergebnisse für ein Szenario"""
    name: str
    beschreibung: str
    szenario: json
    ziele_2030: dict
    ziele_2045: dict
    ertragsart: str
    
    erzeugung_df: Optional[pd.DataFrame] = None
    verbrauch_df: Optional[pd.DataFrame] = None
    ee_anteil_ohne_speicher_df: Optional[pd.DataFrame] = None
    kosten_df: Optional[pd.DataFrame] = None
    speicher_df: Optional[pd.DataFrame] = None
    gesamt_df: Optional[pd.DataFrame] = None
    
    def berechne_alle_prognosen(self):
        """Führt alle Berechnungen durch"""
        print(f"Berechne Prognosen für Szenario '{self.name}'...")
        
        self.erzeugung_df = Prognose_erzeugung(
            self.ziele_2030["Ausbau EE"], 
            self.ziele_2045["Ausbau EE"], 
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
        
        print(f"✓ Berechnungen für '{self.name}' abgeschlossen.")
    
    def exportiere_ergebnisse(self):
        """Exportiert alle Ergebnisse nach Excel"""
        pfad = DATA_DIR / f"szenario_{self.name}_auswertung.xlsx"
        ausgabe(self.kosten_df, self.gesamt_df, self.szenario,pfad)
    
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


def prognose_eines_Szenarios():
    szenarien = load_scenarios()
    
    print("Verfügbare Szenarien:")
    for szenario in szenarien:
        print(f"- {szenario['Name']}")
    
    # Eingaben
    auswahl = input("Bitte geben Sie den Namen des gewünschten Szenarios ein: ")
    jahr = input("Erstes Jahr für Analyse (z.B. 2026, leer für alle): ")
    jahr_2 = input("Zweites Jahr für Analyse (z.B. 2030, leer für alle): ")
    ertragsart = input("Ertragsart (schlecht, mittel, gut): ")
    
    gewaehltes_szenario = get_scenario_by_name(szenarien, auswahl)
    
    if gewaehltes_szenario:
        # Szenario-Objekt erstellen
        szenario_ergebnis = SzenarioErgebnis(
            name=auswahl,
            beschreibung=gewaehltes_szenario["Beschreibung"],
            szenario=gewaehltes_szenario,
            ziele_2030=gewaehltes_szenario["Ziele 2030"],
            ziele_2045=gewaehltes_szenario["Ziele 2045"],
            ertragsart=ertragsart
        )
        
        # Alle Berechnungen durchführen
        szenario_ergebnis.berechne_alle_prognosen()
        
        # Jahre parsen
        if jahr.strip().isdigit() and jahr_2.strip().isdigit():
            jahr1 = int(jahr)
            jahr2 = int(jahr_2)
        elif jahr.strip().isdigit():
            jahr1 = int(jahr)
            jahr2 = None
        elif jahr_2.strip().isdigit():
            jahr1 = None
            jahr2 = int(jahr_2)
        else:
            jahr1 = None
            jahr2 = None
        
        # Plots anzeigen
        szenario_ergebnis.zeige_plots(jahr1, jahr2)
        
        # Ergebnisse exportieren
        if (input("Möchten Sie die Ergebnisse in einer Excel-Datei speichern? (ja/nein): ").lower() == "ja"):
            szenario_ergebnis.exportiere_ergebnisse()
        
        print(f"✓ Szenario '{auswahl}' erfolgreich verarbeitet!")
    else:
        print(f"Szenario '{auswahl}' wurde nicht gefunden.")