"Ünterstützt durch KI (GPT-4.1 Inline Suggestions)"
import json
import matplotlib.pyplot as plt
import pandas as pd
from config import DATA_DIR
from Analyse import analyse_erneuerbare_anteil
from Erzeugungsprognosen import Prognose_erzeugung
from Prognose_Verbrauch import Prognose_Verbrauch
from Histogramme import plot_ee_anteil_histogram_overflow,plot_histogram_ausbauraten_EE
from EE_Anteil_DataFrame import anteil_erneuerbare_df
from Kosten import Kosten_EE
from Prognose_Speicher import Verlauf_Speicher

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

def prognose_eines_Szenarios():
    szenarien = load_scenarios()
    
    print("Verfügbare Szenarien:")
    for szenario in szenarien:
        print(f"- {szenario['Name']}")
    
    auswahl = input("Bitte geben Sie den Namen des gewünschten Szenarios ein: ")
    jahr = input("Bitte geben Sie das Jahr für die Analyse ein (z.B. 2026 oder nichts für alle Jahre): ")
    gewaehltes_szenario = get_scenario_by_name(szenarien, auswahl)
    
    if gewaehltes_szenario:
        print(f"Szenario '{auswahl}' wurde ausgewählt und wird ausgegeben.")
        prognose_erzeugung = Prognose_erzeugung(gewaehltes_szenario["Ziele 2030"]["Ausbau EE"], gewaehltes_szenario["Ziele 2045"]["Ausbau EE"])
        prognose_verbrauch = Prognose_Verbrauch(gewaehltes_szenario["Ziele 2030"]["Strombedarf"], gewaehltes_szenario["Ziele 2045"]["Strombedarf"])
        prognose_speicher = Verlauf_Speicher(anteil_erneuerbare_df(prognose_erzeugung,prognose_verbrauch), 100, 100)
        if jahr.strip().isdigit():
            jahr_int = int(jahr)
            gesamt = anteil_erneuerbare_df(prognose_erzeugung, prognose_verbrauch)
        else:
            jahr_int = 0
            gesamt = anteil_erneuerbare_df(prognose_erzeugung, prognose_verbrauch)
            #prognose_speicher.to_csv(DATA_DIR / 'Output' / 'speicherprognosetestALLES.csv', index=False, sep=';', decimal=',',date_format='%d.%m.%Y %H:%M')
       
        prognose_kosten = Kosten_EE(gewaehltes_szenario)
        print(f"Die Gesamtkosten für das Szenario belaufen sich auf {round(prognose_kosten['Gesamtkosten_EE [€]'].sum()/1e12 ,2)} Billionen Euro.")
        plot_ee_anteil_histogram_overflow(gesamt,jahr_int)
        plot_histogram_ausbauraten_EE(gewaehltes_szenario["Ziele 2030"]["Ausbau EE"], gewaehltes_szenario["Ziele 2045"]["Ausbau EE"])
        plt.show()
        #TODO Speicherdaten einlesen


        return
    else:
        print(f"Szenario '{auswahl}' nicht gefunden.")
        return None
