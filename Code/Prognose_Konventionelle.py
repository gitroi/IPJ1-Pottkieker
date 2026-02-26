"""
Diese Datei enthält die Funktion zur Prognose konventioneller Methoden basierend auf 
Eingabedaten und festen Parametern.
Programmiert von Joris Bürger 
"""

import json
import pandas as pd
import numpy as np
from config import PROJECT_ROOT 

def konventionelle_prognose(gesamt:pd.DataFrame,konventionelle:dict,anteile:dict) -> pd.DataFrame:
    """
    Diese Funktion nimmt Eingabedaten in Form eines DataFrames entgegen,
    verarbeitet sie und gibt eine Prognose für konventionelle Methoden zurück.
    
    :param gesamt: pd.DataFrame mit den Eingabedaten
    :param konventionelle: dict mit den maximalen Jahresleistungen an konventionellen
    :param anteile: dict mit den Anteilen für konventionelle Methoden
                    Format: {"2038": {key: anteil, ...}, "2045": {key: anteil, ...}}
    :return: pd.DataFrame mit den Prognoseergebnissen
    """
    """
    Dict mit Konventionellen anteilen:
    Format: {"2038": {"braun": 0.6, "stein": 0.3, ...}, "2045": {"braun": 0.4, ...}}
    """
    prognose_konventionelle = gesamt.copy()
    if 'Jahr' not in prognose_konventionelle.columns:
        prognose_konventionelle['Jahr'] = prognose_konventionelle['Datum von'].dt.year

    konventionelle = konventionelle.copy()

    with open(f"{PROJECT_ROOT}/Daten/Feste_Parameter/konventionelle.json", "r") as file:    
        feste_parameter_konventionelle = json.load(file)

    prognose_konventionelle['konventionelle [MWh]'] = (prognose_konventionelle["Netzlast [MWh]"] - prognose_konventionelle["Realisierte Erzeugung [MWh]"]).clip(lower=0)
    
    mask_2038 = prognose_konventionelle['Jahr'] <= 2038
    mask_2045 = prognose_konventionelle['Jahr'] > 2038
    
    for key in feste_parameter_konventionelle.keys():
        if key != "importe":
            prognose_konventionelle.loc[mask_2038, f'{key} [MWh]'] = (prognose_konventionelle.loc[mask_2038, 'konventionelle [MWh]'] * anteile["2038"][key]).clip(lower=0)
            prognose_konventionelle.loc[mask_2045, f'{key} [MWh]'] = (prognose_konventionelle.loc[mask_2045, 'konventionelle [MWh]'] * anteile["2045"][key]).clip(lower=0)
            
            for jahr in prognose_konventionelle['Jahr'].unique():
                jahr_mask = prognose_konventionelle['Jahr'] == jahr
                anteil = anteile["2038"][key] if jahr <= 2038 else anteile["2045"][key]
                leistung_gw = konventionelle[jahr]['Leistung'] * anteil / 1e3  # in GW
                prognose_konventionelle.loc[jahr_mask, f'{key} [MW]'] = leistung_gw * 1e3  # in MW speichern
                anzahl_viertelstunden_jahr = jahr_mask.sum()
                
                opex_leistung_jahr = leistung_gw * 1e6 * feste_parameter_konventionelle[key]['opex_kw']  # GW → kW
                opex_leistung_pro_viertelstunde = opex_leistung_jahr / anzahl_viertelstunden_jahr
                
                opex_energie = prognose_konventionelle.loc[jahr_mask, f'{key} [MWh]'] * feste_parameter_konventionelle[key]['opex_MWh']
                
                prognose_konventionelle.loc[jahr_mask, f'{key}_opex [€]'] = (opex_leistung_pro_viertelstunde + opex_energie).clip(lower=0)
        else:
            prognose_konventionelle.loc[mask_2038, f'{key} [MWh]'] = (prognose_konventionelle.loc[mask_2038, 'konventionelle [MWh]'] * anteile["2038"][key]).clip(lower=0)
            prognose_konventionelle.loc[mask_2045, f'{key} [MWh]'] = (prognose_konventionelle.loc[mask_2045, 'konventionelle [MWh]'] * anteile["2045"][key]).clip(lower=0)
            prognose_konventionelle[f'{key}_opex [€]'] =  (prognose_konventionelle[f'{key} [MWh]'] * feste_parameter_konventionelle[key]['opex_MWh']).clip(lower=0)
            prognose_konventionelle[f'{key}_capex [€]'] = 0.0
            continue 

        prognose_konventionelle[f'{key}_capex [€]'] = 0.0
        
        installiert_vorjahr = feste_parameter_konventionelle[key]['bestand']  # Bestand 2025 als Startwert
        
        for jahr in sorted(prognose_konventionelle['Jahr'].unique()):
            jahr_mask = prognose_konventionelle['Jahr'] == jahr
            anteil = anteile["2038"][key] if jahr <= 2038 else anteile["2045"][key]
            
            installiert_aktuell = konventionelle[jahr]['Leistung'] * anteil / 1e3  # in GW
            
            prognose_konventionelle.loc[jahr_mask, f'{key} [GW]'] = installiert_aktuell
            
            zubau_gw = max(0, installiert_aktuell - installiert_vorjahr)
            
            if zubau_gw > 0:
                # CAPEX: €/kW × kW = € (einmalig im Baujahr)
                capex_gesamt = zubau_gw * 1e6 * feste_parameter_konventionelle[key]['capex']
                
                anzahl_viertelstunden = jahr_mask.sum()
                capex_pro_viertelstunde = capex_gesamt / anzahl_viertelstunden
                prognose_konventionelle.loc[jahr_mask, f'{key}_capex [€]'] = capex_pro_viertelstunde
            else:
                prognose_konventionelle.loc[jahr_mask, f'{key}_capex [€]'] = 0.0
            
            installiert_vorjahr = installiert_aktuell

    if prognose_konventionelle.isna().any().any():
        raise ValueError("Fehlende Werte in der konventionellen Prognose entdeckt.")
    
    return prognose_konventionelle.drop(columns=['Jahr'])