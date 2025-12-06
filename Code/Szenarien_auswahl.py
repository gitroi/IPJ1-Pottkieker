"""
Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
Programmiert von Joris Bürger
"""
import json
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional
from config import DATA_DIR, PROJECT_ROOT
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
        if szenario["Name"].lower() == name.lower():
            return szenario
    return None

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
    
    pfad = PROJECT_ROOT/ "Ergebnisse" / "auswertung_aller_szenarien.xlsx"
    alle_ergebnisse.to_excel(pfad, index=False)
    print(f"✓ Alle Szenarien wurden verarbeitet und in '{pfad}' gespeichert.")