"Ünterstützt durch KI (GPT-4.1 Inline Suggestions)"
import json
from config import DATA_DIR
from Analyse import analyse_erneuerbare_anteil
from Erzeugungsprognosen import Prognose_erzeugung
from Prognose_Verbrauch import Prognose_Verbrauch
from Histogramme import plot_ee_anteil_histogram_overflow
from EE_Anteil_DataFrame import anteil_erneuerbare_df,anteil_erneuerbare_Jahrx_df

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
        bearbeitetes_szenario = json_objekt_bearbeiten(gewaehltes_szenario)
        prognose_erzeugung = Prognose_erzeugung(bearbeitetes_szenario["Ziele 2030"]["Ausbau_EE"], bearbeitetes_szenario["Ziele 2045"]["Ausbau_EE"])
        prognose_verbrauch = Prognose_Verbrauch(gewaehltes_szenario["Ziele 2030"]["Strombedarf"], gewaehltes_szenario["Ziele 2045"]["Strombedarf"])
        if jahr.strip().isdigit():
            jahr_int = int(jahr)
            gesamt = anteil_erneuerbare_Jahrx_df(prognose_erzeugung, prognose_verbrauch, "Netzlast [MWh] Originalauflösungen", jahr_int)
        else:
            gesamt = anteil_erneuerbare_df(prognose_erzeugung, prognose_verbrauch, "Netzlast [MWh] Originalauflösungen")
        
        plot_ee_anteil_histogram_overflow(gesamt)

        return
    else:
        print(f"Szenario '{auswahl}' nicht gefunden.")
        return None

def json_objekt_bearbeiten(daten):
    objekt = {}

    for jahr in ["Ziele 2030", "Ziele 2045"]:
        ee = daten[jahr]["Ausbau EE"]

        objekt[jahr] = {
            "Ausbau_EE": {
                "pv": ee["pv_dach"] + ee["pv_frei"],
                "wind_onshore": ee["wind_onshore"],
                "wind_offshore": ee["wind_offshore"],
                "biomasse": ee["biomasse"],
                "wasser": ee["wasser"],
                "sonstige": ee["sonstige"]
            }
        }

    return objekt