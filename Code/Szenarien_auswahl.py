"Ünterstützt durch KI (GPT-4.1 Inline Suggestions)"
import json
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional
from config import DATA_DIR
from Klassen import Szenario

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


def prognose_eines_Szenarios():
    szenarien = load_scenarios()
    
    print("Verfügbare Szenarien:")
    for szenario in szenarien:
        print(f"- {szenario['Name']}")
    
    auswahl = input("Bitte geben Sie den Namen des gewünschten Szenarios ein: ")
    jahr = input("Erstes Jahr für Analyse (z.B. 2026, leer für alle): ")
    jahr_2 = input("Zweites Jahr für Analyse (z.B. 2030, leer für alle): ")
    ertragsart = input("Ertragsart (schlecht, mittel, gut): ")
    
    gewaehltes_szenario = get_scenario_by_name(szenarien, auswahl)
    
    if gewaehltes_szenario:
        szenario_ergebnis = Szenario(
            name=auswahl,
            beschreibung=gewaehltes_szenario["Beschreibung"],
            szenario=gewaehltes_szenario,
            ziele_2030=gewaehltes_szenario["Ziele 2030"],
            ziele_2045=gewaehltes_szenario["Ziele 2045"],
            ertragsart=ertragsart,
            veränderungsfaktoren=gewaehltes_szenario["Veränderungsfaktoren"]["Erzeugung"]
        )
        
        szenario_ergebnis.berechne_alle_prognosen()
        
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
        
        szenario_ergebnis.zeige_plots(jahr1, jahr2)
        
        if (input("Möchten Sie die Ergebnisse in einer Excel-Datei speichern? (ja/nein): ").lower() == "ja"):
            szenario_ergebnis.exportiere_ergebnisse()
        
        print(f"✓ Szenario '{auswahl}' erfolgreich verarbeitet!")
    else:
        print(f"Szenario '{auswahl}' wurde nicht gefunden.")

def prognose_alle_Szenarien():
    szenarien = load_scenarios()
    alle_ergebnisse = pd.DataFrame()
    
    ertragsart = input("Wie soll die Ertragsart für alle Szenarien sein? (schlecht, mittel, gut): ")

    if ertragsart not in ["schlecht", "mittel", "gut"]:
        raise ValueError("Ungültige Ertragsart. Bitte wählen Sie 'schlecht', 'mittel' oder 'gut'.")
    
    for szenario in szenarien:
        szenario_ergebnis = Szenario(
            name=szenario["Name"],
            beschreibung=szenario["Beschreibung"],
            szenario=szenario,
            ziele_2030=szenario["Ziele 2030"],
            ziele_2045=szenario["Ziele 2045"],
            ertragsart=ertragsart
        )
        
        szenario_ergebnis.berechne_alle_prognosen()
        ergebnisse_df = szenario_ergebnis.getErgebnisse()
        alle_ergebnisse = pd.concat([alle_ergebnisse, ergebnisse_df], ignore_index=True)
    
    pfad = DATA_DIR / "auswertung_aller_szenarien.xlsx"
    alle_ergebnisse.to_excel(pfad, index=False)
    print(f"✓ Alle Szenarien wurden verarbeitet und in '{pfad}' gespeichert.")