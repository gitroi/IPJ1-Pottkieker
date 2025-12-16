"""
Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
Programmiert von Joris Bürger und Robin Matzke
"""
import json
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional
from config import DATA_DIR, PROJECT_ROOT
from Klassen import Szenario
from Histogramme import plot_histogram_gesamtauswertung

def load_scenarios():
    """Lädt Szenarien aus einer JSON-Datei."""
    pfad = DATA_DIR / "Szenarien.json"

    with open(pfad, 'r', encoding='utf-8') as datei:
        scenarios = json.load(datei)

    return scenarios

def load_verbrauchsprofile():
    """Lädt Verbrauchsprofile aus einer JSON-Datei."""
    pfad = DATA_DIR / "Verbrauchsprofile.json"

    with open(pfad, 'r', encoding='utf-8') as datei:
        verbrauchsprofile = json.load(datei)

    return verbrauchsprofile

def get_scenario_by_name(szenarien, name):
    """Gibt ein Szenario basierend auf dem Namen zurück."""
    for szenario in szenarien:
        if szenario["Name"].lower() == name.lower():
            return szenario
    return None

def get_verbrauchsprofil_by_name(verbrauchsprofile, name):
    """Gibt ein Verbrauchsprofil basierend auf dem Namen zurück."""
    for profil in verbrauchsprofile:
        if profil["Name"].lower() == name.lower():
            return profil
    return None

def prognose_eines_Szenarios():
    szenarien = load_scenarios()
    verbrauchsprofile = load_verbrauchsprofile()
    
    print("Verfügbare Szenarien:")
    for szenario in szenarien:
        print(f"- {szenario['Name']}")

    while(True):
        auswahl = input("Bitte geben Sie den Namen des gewünschten Szenarios ein: ")
        if get_scenario_by_name(szenarien, auswahl):
            break
        else:
            print(f"Szenario '{auswahl}' nicht gefunden. Bitte versuchen Sie es erneut.")

    print("Verfügbare Verbrauchsprofile:")
    for profil in verbrauchsprofile:
        print(f"- {profil['Name']}")

    while(True):
        verbrauch = input("Bitte geben Sie den Namen des gewünschten Verbrauchsprofils ein: ")
        if get_verbrauchsprofil_by_name(verbrauchsprofile, verbrauch):
            break
        else:
            print(f"Verbrauchsprofil '{verbrauch}' nicht gefunden. Bitte versuchen Sie es erneut.")
    
    jahr = input("Erstes Jahr für Analyse (z.B. 2026, leer für alle): ")
    ertragsart = input("Ertragsart (schlecht, mittel, gut): ")
    bilder = input("Möchten Sie die Plots speichern? (ja/nein): ").lower() == "ja"

    gewaehltes_szenario = get_scenario_by_name(szenarien, auswahl)
    gewaehltes_profil = get_verbrauchsprofil_by_name(verbrauchsprofile, verbrauch)
    
    if gewaehltes_szenario:
        szenario_ergebnis = Szenario(
            name=auswahl,
            beschreibung=gewaehltes_szenario["Beschreibung"],
            szenario=gewaehltes_szenario,
            ziele_2030=gewaehltes_szenario["Ziele 2030"],
            ziele_2045=gewaehltes_szenario["Ziele 2045"],
            ertragsart=ertragsart,
            verbrauchsprofile=gewaehltes_profil,
            veränderungsfaktoren=gewaehltes_szenario["Veränderungsfaktoren"]["Erzeugung"]
        )
        
        szenario_ergebnis.berechne_alle_prognosen()
        
        if jahr.strip().isdigit():
            jahr1 = int(jahr)
        else:
            jahr1 = None
        
        szenario_ergebnis.zeige_plots(jahr1,bilder)
        
        if (input("Möchten Sie die Ergebnisse in einer Excel-Datei speichern? (ja/nein): ").lower() == "ja"):
            szenario_ergebnis.exportiere_ergebnisse()
        
        print(f"✓ Szenario '{auswahl}' erfolgreich verarbeitet!")
    else:
        print(f"Szenario '{auswahl}' wurde nicht gefunden.")

def prognose_alle_Szenarien():
    szenarien = load_scenarios()
    alle_ergebnisse = pd.DataFrame()
    verbrauchsprofile = load_verbrauchsprofile()

    print("Verfügbare Verbrauchsprofile:")
    for profil in verbrauchsprofile:
        print(f"- {profil['Name']}")

    while(True):
        verbrauch = input("Bitte geben Sie den Namen des gewünschten Verbrauchsprofils ein: ")
        if get_verbrauchsprofil_by_name(verbrauchsprofile, verbrauch):
            break
        else:
            print(f"Verbrauchsprofil '{verbrauch}' nicht gefunden. Bitte versuchen Sie es erneut.")

    gewaehltes_profil = get_verbrauchsprofil_by_name(verbrauchsprofile, verbrauch)

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
            ertragsart=ertragsart,
            verbrauchsprofile=gewaehltes_profil,
            veränderungsfaktoren=szenario["Veränderungsfaktoren"]["Erzeugung"]
        )
        
        szenario_ergebnis.berechne_alle_prognosen()
        ergebnisse_df = szenario_ergebnis.getErgebnisse()
        alle_ergebnisse = pd.concat([alle_ergebnisse, ergebnisse_df], ignore_index=True)
    
    fig1, ax1 = plt.subplots(1, 2, figsize=(12, 6))
    fig2, ax2 = plt.subplots(1, 2, figsize=(12, 6))

    plot_histogram_gesamtauswertung(alle_ergebnisse,  ax1[0],ax1[1], ax2[0],ax2[1])
    plt.tight_layout()
    if(input("Möchten Sie die Plots speichern? (ja/nein): ").lower() == "ja"):
        pfad = DATA_DIR/ "Output" / f"auswertung_aller_szenarien_erzeugung_{ertragsart}.png"
        fig1.savefig(pfad)
        fig2.savefig(pfad.with_name(pfad.stem + "_2.png"))
        print(f"✓ Plots wurden in '{pfad}' und '{pfad.with_name(pfad.stem + '_2.png')}' gespeichert.")
    plt.show()

    pfad = DATA_DIR/ "Output" / f"auswertung_aller_szenarien_erzeugung_{ertragsart}.xlsx"
    alle_ergebnisse.to_excel(pfad, index=False)
    print(f"✓ Alle Szenarien wurden verarbeitet und in '{pfad}' gespeichert.")