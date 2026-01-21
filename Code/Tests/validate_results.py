"""
Validierungsskript für das IPJ1-Pottkieker Projekt.
Prüft die Plausibilität und Konsistenz der Simulationsergebnisse.
Erstellt durch Joris Bürger
Programmiert von GitHub Copilot
"""
    

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import json
import warnings

# Projektpfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, PROJECT_ROOT
from Klassen import Szenario
from Szenarien_auswahl import load_scenarios, load_verbrauchsprofile, get_scenario_by_name, get_verbrauchsprofil_by_name

warnings.filterwarnings('ignore')

def print_header(text: str):
    """Druckt eine formatierte Überschrift"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_subheader(text: str):
    """Druckt eine formatierte Unterüberschrift"""
    print(f"\n--- {text} ---")

def check_pass(message: str):
    """Druckt eine Erfolgs-Nachricht"""
    print(f"✅ {message}")

def check_warn(message: str):
    """Druckt eine Warn-Nachricht"""
    print(f"⚠️  {message}")

def check_fail(message: str):
    """Druckt eine Fehler-Nachricht"""
    print(f"❌ {message}")

def validate_dataframe_structure(df: pd.DataFrame, name: str, required_cols: list = None) -> bool:
    """Validiert die Grundstruktur eines DataFrames
    
    Args:
        df: Der zu validierende DataFrame
        name: Name für die Ausgabe
        required_cols: Optional - Liste von Spaltennamen, die vorhanden sein müssen
    """
    print_subheader(f"Validiere DataFrame: {name}")
    
    if df is None:
        check_fail(f"{name} ist None!")
        return False
    
    if df.empty:
        check_fail(f"{name} ist leer!")
        return False
    
    check_pass(f"{name} hat {len(df)} Zeilen und {len(df.columns)} Spalten")
    
    # Prüfe auf erforderliche Spalten (wird meist nicht verwendet)
    if required_cols:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            check_fail(f"Fehlende Spalten: {missing}")
            return False
        check_pass(f"Alle erforderlichen Spalten vorhanden")
    
    # Prüfe auf NaN-Werte
    nan_counts = df.isna().sum()
    total_nans = nan_counts.sum()
    if total_nans > 0:
        check_warn(f"Gefunden: {total_nans} NaN-Werte")
        for col, count in nan_counts[nan_counts > 0].items():
            print(f"   - {col}: {count} NaN-Werte")
    else:
        check_pass("Keine NaN-Werte gefunden")
    
    return True

def validate_erzeugung(df: pd.DataFrame, ziele_2030: dict, ziele_2045: dict):
    """Validiert die Erzeugungsprognose"""
    print_header("VALIDIERUNG: ERZEUGUNGSPROGNOSE")
    
    if not validate_dataframe_structure(df, "Erzeugung"):
        return
    
    # Konvertiere "Datum von" zu datetime falls nötig
    zeitpunkt_col = "Datum von"
    if zeitpunkt_col not in df.columns:
        check_warn(f"Spalte '{zeitpunkt_col}' nicht gefunden! Verfügbare Spalten: {list(df.columns[:5])}...")
        zeitpunkt_col = None
    elif not pd.api.types.is_datetime64_any_dtype(df[zeitpunkt_col]):
        print(f"  Konvertiere '{zeitpunkt_col}' zu datetime...")
        df[zeitpunkt_col] = pd.to_datetime(df[zeitpunkt_col], errors='coerce')
    
    # 1. Prüfe Zeitspanne
    print_subheader("Zeitspanne")
    if zeitpunkt_col and zeitpunkt_col in df.columns:
        min_year = df[zeitpunkt_col].min().year if pd.notna(df[zeitpunkt_col].min()) else None
        max_year = df[zeitpunkt_col].max().year if pd.notna(df[zeitpunkt_col].max()) else None
        print(f"  Zeitraum: {min_year} bis {max_year}")
    else:
        min_year = max_year = None
        print(f"  Zeitraum: Unbekannt (Spalte 'Datum von' nicht gefunden)")
    
    if min_year and max_year:
        if min_year < 2025 or max_year > 2045:
            check_warn(f"Unerwarteter Zeitraum: {min_year}-{max_year}")
        else:
            check_pass("Zeitraum plausibel (2025-2045)")
    
    # 2. Prüfe auf negative Werte
    print_subheader("Wertebereiche")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    negative_found = False
    for col in numeric_cols:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            negative_found = True
            min_val = df[col].min()
            check_fail(f"{col}: {neg_count} negative Werte (Min: {min_val:.6f})")
            # Zeige wo sie auftreten
            if zeitpunkt_col and zeitpunkt_col in df.columns:
                first_neg_idx = df[df[col] < 0].index[0]
                print(f"          Erstes Auftreten: Index {first_neg_idx}, Zeitpunkt: {df.loc[first_neg_idx, zeitpunkt_col]}")
    
    if not negative_found:
        check_pass("Keine negativen Erzeugungswerte")
    
    # 3. Prüfe PV nachts
    print_subheader("PV Nachtproduktion")
    if zeitpunkt_col and zeitpunkt_col in df.columns:
        pv_cols = [col for col in df.columns if ("pv" in col.lower() or "photovoltaik" in col.lower()) and "[MWh]" in col]
        if pv_cols:
            night_hours = df[(df[zeitpunkt_col].dt.hour <= 4) | (df[zeitpunkt_col].dt.hour >= 22)]
            for col in pv_cols:
                if col in night_hours.columns:
                    night_pv = night_hours[col].sum()
                    if night_pv > 1.0:  # Toleranz für Rundungsfehler
                        check_warn(f"{col}: {night_pv:.2f} MWh Nachtproduktion")
                    else:
                        check_pass(f"{col}: Keine signifikante Nachtproduktion")
        else:
            check_warn("Keine PV-Spalten mit '[MWh]' gefunden")
    else:
        check_warn("Übersprungen (Spalte 'Datum von' nicht verfügbar)")
    
    # 4. Prüfe Ausbauziele für 2030
    print_subheader("Ausbauziele 2030")
    if zeitpunkt_col and zeitpunkt_col in df.columns and min_year and max_year:
        df_2030 = df[df[zeitpunkt_col].dt.year == 2030]
        if not df_2030.empty:
            for key in ziele_2030.keys():
                # Suche passende Spalte (verschiedene Benennungen möglich)
                matching_cols = [col for col in df.columns if key.replace("_", "").lower() in col.replace("_", "").replace(" ", "").lower() and "[MWh]" in col]
                if matching_cols:
                    col = matching_cols[0]
                    produktion_twh = df_2030[col].sum() / 1_000_000
                    print(f"  {key}: {produktion_twh:.2f} TWh produziert")
        else:
            check_warn("Keine Daten für 2030 gefunden")
    else:
        check_warn("Übersprungen (keine Zeitinformation)")
    
    # 5. Prüfe Saisonalität
    print_subheader("Saisonalität")
    if zeitpunkt_col and zeitpunkt_col in df.columns:
        pv_cols = [col for col in df.columns if ("pv" in col.lower() or "photovoltaik" in col.lower()) and "[MWh]" in col]
        if pv_cols:
            col = pv_cols[0]
            df_with_month = df.copy()
            df_with_month["Monat"] = df[zeitpunkt_col].dt.month
            
            winter_prod = df_with_month[df_with_month["Monat"].isin([12, 1, 2])][col].mean()
            summer_prod = df_with_month[df_with_month["Monat"].isin([6, 7, 8])][col].mean()
            
            print(f"  PV Winter-Mittel: {winter_prod:.2f} MWh")
            print(f"  PV Sommer-Mittel: {summer_prod:.2f} MWh")
            
            if summer_prod > winter_prod * 1.5:
                check_pass("PV-Saisonalität plausibel (Sommer > Winter)")
            else:
                check_warn("PV-Saisonalität erscheint ungewöhnlich")
    else:
        check_warn("Übersprungen (keine Zeitinformation)")

def validate_verbrauch(df: pd.DataFrame, verbrauchsprofil: dict):
    """Validiert die Verbrauchsprognose"""
    print_header("VALIDIERUNG: VERBRAUCHSPROGNOSE")
    
    if not validate_dataframe_structure(df, "Verbrauch"):
        return
    
    # Konvertiere "Datum von" zu datetime falls nötig
    zeitpunkt_col = "Datum von"
    if zeitpunkt_col not in df.columns:
        check_warn(f"Spalte '{zeitpunkt_col}' nicht gefunden!")
        zeitpunkt_col = None
    elif not pd.api.types.is_datetime64_any_dtype(df[zeitpunkt_col]):
        df[zeitpunkt_col] = pd.to_datetime(df[zeitpunkt_col], errors='coerce')
    
    # 1. Prüfe auf negative Werte
    print_subheader("Wertebereiche")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if (df[numeric_cols] < 0).any().any():
        check_fail("Negative Verbrauchswerte gefunden!")
    else:
        check_pass("Keine negativen Verbrauchswerte")
    
    # 2. Prüfe Gesamtverbrauch für 2030
    print_subheader("Jahresverbrauch 2030")
    # Suche nach Gesamt-Spalte
    gesamt_cols = [col for col in df.columns if "gesamt" in col.lower() or "netzlast [mwh]" in col.lower()]
    gesamt_col = gesamt_cols[0] if gesamt_cols else None
    
    if zeitpunkt_col and zeitpunkt_col in df.columns and gesamt_col:
        df_2030 = df[df[zeitpunkt_col].dt.year == 2030]
        if not df_2030.empty:
            verbrauch_twh = df_2030[gesamt_col].sum() / 1_000_000
            print(f"  Gesamtverbrauch 2030: {verbrauch_twh:.2f} TWh")
            
            # Plausibilitätsprüfung: Deutschland ~500-700 TWh
            if 400 < verbrauch_twh < 800:
                check_pass("Verbrauch liegt im plausiblen Bereich")
            else:
                check_warn(f"Verbrauch außerhalb des erwarteten Bereichs (400-800 TWh)")
    else:
        check_warn("Übersprungen (keine Zeitinformation oder Gesamt-Spalte nicht gefunden)")
    
    # 3. Prüfe Tagesverlauf (Peaks tagsüber)
    print_subheader("Tagesverlauf")
    if zeitpunkt_col and zeitpunkt_col in df.columns and gesamt_col:
        df_with_hour = df.copy()
        df_with_hour["Stunde"] = df[zeitpunkt_col].dt.hour
        hourly_mean = df_with_hour.groupby("Stunde")[gesamt_col].mean()
        
        day_mean = hourly_mean[8:20].mean()
        night_mean = hourly_mean[0:6].mean()
        
        print(f"  Tagesmittel (8-20h): {day_mean:.2f} MWh")
        print(f"  Nachtmittel (0-6h): {night_mean:.2f} MWh")
        
        if day_mean > night_mean:
            check_pass("Tagesverlauf plausibel (Tag > Nacht)")
        else:
            check_warn("Tagesverlauf ungewöhnlich (Nacht >= Tag)")
    else:
        check_warn("Übersprungen (keine Zeitinformation)")
    
    # 4. Prüfe auf extreme Sprünge
    print_subheader("Kontinuität")
    if zeitpunkt_col and zeitpunkt_col in df.columns and gesamt_col:
        df_sorted = df.sort_values(zeitpunkt_col)
        diff = df_sorted[gesamt_col].diff().abs()
        max_diff = diff.max()
        mean_value = df_sorted[gesamt_col].mean()
        
        print(f"  Maximaler Sprung: {max_diff:.2f} MWh ({(max_diff/mean_value*100):.1f}% vom Mittelwert)")
        
        if max_diff / mean_value > 2.0:  # Sprung > 200% des Mittelwerts
            check_warn("Sehr große Sprünge im Verbrauch gefunden!")
        else:
            check_pass("Keine ungewöhnlich großen Sprünge")
    else:
        check_warn("Übersprungen (keine Zeitinformation)")

def validate_ee_anteil(df: pd.DataFrame):
    """Validiert die EE-Anteil-Berechnung"""
    print_header("VALIDIERUNG: EE-ANTEIL (ohne Speicher)")
    
    if not validate_dataframe_structure(df, "EE-Anteil"):
        return
    
    # 1. Prüfe Anteilswerte
    print_subheader("Anteilswerte")
    ee_cols = [col for col in df.columns if "anteil" in col.lower() or "prozent" in col.lower()]
    
    for col in ee_cols:
        min_val = df[col].min()
        max_val = df[col].max()
        mean_val = df[col].mean()
        over_100_count = (df[col] > 100).sum()
        
        print(f"  {col}:")
        print(f"    Min: {min_val:.2f}, Max: {max_val:.2f}, Mittel: {mean_val:.2f}")
        
        # Prüfe Format und Plausibilität
        if min_val < 0:
            check_fail(f"Negative Anteile gefunden!")
        elif max_val > 1.5:  # Prozent-Format (0-100+)
            print(f"    Format: Prozent (0-100+)")
            if over_100_count > 0:
                percent_over = (over_100_count / len(df)) * 100
                check_pass(f"Überproduktion: {over_100_count} Zeitpunkte (={percent_over:.1f}%) mit EE-Anteil > 100%")
                print(f"              → Das ist gut! Überschüssige EE kann gespeichert/exportiert werden.")
        elif max_val <= 1.5:  # Dezimal-Format (0-1+)
            print(f"    Format: Dezimal (0-1+)")
            if max_val > 1.0:
                over_1_count = (df[col] > 1.0).sum()
                percent_over = (over_1_count / len(df)) * 100
                check_pass(f"Überproduktion: {over_1_count} Zeitpunkte (={percent_over:.1f}%) mit EE-Anteil > 100%")
                print(f"              → Das ist gut! Überschüssige EE kann gespeichert/exportiert werden.")
    
    # 2. Prüfe Konsistenz: EE-Anteil = Erzeugung / Verbrauch
    print_subheader("Berechnungskonsistenz")
    if all(col in df.columns for col in ["Erzeugung [MWh]", "Verbrauch [MWh]", "EE-Anteil [%]"]):
        calculated_anteil = (df["Erzeugung [MWh]"] / df["Verbrauch [MWh]"] * 100)
        diff = (df["EE-Anteil [%]"] - calculated_anteil).abs()
        max_diff = diff.max()
        
        print(f"  Maximale Abweichung: {max_diff:.6f}%")
        
        if max_diff < 0.01:
            check_pass("EE-Anteil korrekt berechnet")
        else:
            check_warn(f"Abweichungen in der Berechnung gefunden")

def validate_speicher(df: pd.DataFrame, speicher_ziele_2030: dict, speicher_ziele_2045: dict):
    """Validiert die Speichersimulation"""
    print_header("VALIDIERUNG: SPEICHERSIMULATION")
    
    if df is None or df.empty:
        check_fail("Keine Speicherdaten vorhanden")
        return
    
    # 1. Grundstruktur
    if not validate_dataframe_structure(df, "Speicher"):
        return
    
    # Konvertiere "Datum von" zu datetime falls nötig
    zeitpunkt_col = "Datum von"
    if zeitpunkt_col not in df.columns:
        zeitpunkt_col = None
    elif not pd.api.types.is_datetime64_any_dtype(df[zeitpunkt_col]):
        df[zeitpunkt_col] = pd.to_datetime(df[zeitpunkt_col], errors='coerce')
    
    # 2. Prüfe jeden Speichertyp
    speichertypen = ["Batteriespeicher", "Pumpspeicher", "Wasserstoff"]
    
    for stype in speichertypen:
        print_subheader(f"Speichertyp: {stype}")
        
        # Finde relevante Spalten
        ladestand_col = f"{stype} Ladestand [MWh]"
        geladen_col = f"{stype} Geladene [MWh]"
        entladen_col = f"{stype} Entladene [MWh]"
        
        if ladestand_col not in df.columns:
            check_warn(f"Spalte '{ladestand_col}' nicht gefunden")
            continue
        
        # Prüfe Ladezustand
        soc = df[ladestand_col]
        min_soc = soc.min()
        max_soc = soc.max()
        mean_soc = soc.mean()
        
        print(f"  Ladestand [MWh]:")
        print(f"    Min: {min_soc:.2f}, Max: {max_soc:.2f}, Mittel: {mean_soc:.2f}")
        
        # Prüfe auf negative Werte
        if min_soc < -0.01:  # kleine Toleranz für Rundungsfehler
            check_fail(f"Negativer Ladestand gefunden!")
        else:
            check_pass(f"Kein negativer Ladestand")
        
        # Prüfe Kapazitätsgrenzen für 2030
        stype_key = stype.lower().replace(" ", "")
        if zeitpunkt_col and zeitpunkt_col in df.columns:
            df_2030 = df[df[zeitpunkt_col].dt.year == 2030]
            if not df_2030.empty and stype_key in speicher_ziele_2030:
                max_soc_2030 = df_2030[ladestand_col].max()
                kapazitaet_2030 = speicher_ziele_2030[stype_key]
                
                print(f"  Kapazitätsprüfung 2030:")
                print(f"    Max SOC: {max_soc_2030:.2f} MWh")
                print(f"    Zielkapazität: {kapazitaet_2030:.2f} MWh")
                
                if max_soc_2030 > kapazitaet_2030 * 1.01:  # 1% Toleranz
                    check_fail(f"Ladestand überschreitet Kapazität!")
                else:
                    check_pass(f"Ladestand innerhalb der Kapazität")
        
        # Prüfe Aktivität
        if geladen_col in df.columns and entladen_col in df.columns:
            total_geladen = df[geladen_col].sum()
            total_entladen = df[entladen_col].sum()
            
            print(f"  Aktivität:")
            print(f"    Gesamt geladen: {total_geladen:.2f} MWh")
            print(f"    Gesamt entladen: {total_entladen:.2f} MWh")
            
            if total_geladen == 0 and total_entladen == 0:
                check_warn(f"Speicher wurde nicht genutzt!")
            else:
                check_pass(f"Speicher aktiv")
                
                # Prüfe Wirkungsgrad (entladen sollte < geladen sein)
                if total_entladen > total_geladen * 1.01:
                    check_fail(f"Entladene Energie > geladene Energie (Energieerhaltung verletzt!)")
                else:
                    effizienz = (total_entladen / total_geladen * 100) if total_geladen > 0 else 0
                    print(f"    Effektiver Wirkungsgrad: {effizienz:.2f}%")

def validate_kosten(df: pd.DataFrame):
    """Validiert die Kostenberechnung"""
    print_header("VALIDIERUNG: KOSTENBERECHNUNG")
    
    if not validate_dataframe_structure(df, "Kosten"):
        return
    
    # 1. Prüfe auf negative Kosten
    print_subheader("Wertebereiche")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    negative_found = False
    for col in numeric_cols:
        if (df[col] < 0).any():
            check_warn(f"Negative Werte in {col} gefunden")
            negative_found = True
    
    if not negative_found:
        check_pass("Keine negativen Kostenwerte")
    

def validate_dunkelflaute(df: pd.DataFrame, jahr: int):
    """Validiert die Dunkelflaute-Analyse"""
    print_header(f"VALIDIERUNG: DUNKELFLAUTE {jahr}")
    
    if not validate_dataframe_structure(df, f"Dunkelflaute {jahr}"):
        return
    
    # 1. Prüfe Zeiträume
    print_subheader("Dunkelflaute-Perioden")
    if "Datum von" in df.columns and "Datum bis" in df.columns:
        df["Dauer"] = (pd.to_datetime(df["Datum bis"]) - pd.to_datetime(df["Datum von"])).dt.total_seconds() / 3600
        
        print(f"  Anzahl Perioden: {len(df)}")
        print(f"  Gesamtdauer: {df['Dauer'].sum():.0f} Stunden")
        print(f"  Durchschnittliche Dauer: {df['Dauer'].mean():.1f} Stunden")
        print(f"  Längste Periode: {df['Dauer'].max():.0f} Stunden")
        
        if df['Dauer'].max() > 336:  # > 2 Wochen
            check_warn("Sehr lange Dunkelflaute-Periode gefunden (>14 Tage)")
    
    # 2. Prüfe EE-Realisierung
    print_subheader("EE-Realisierung während Dunkelflaute")
    ee_cols = [col for col in df.columns if "realisierte" in col.lower() and "ee" in col.lower()]
    
    for col in ee_cols:
        mean_real = df[col].mean()
        min_real = df[col].min()
        max_real = df[col].max()
        
        print(f"  {col}:")
        print(f"    Mittelwert: {mean_real:.2%}")
        print(f"    Min: {min_real:.2%}, Max: {max_real:.2%}")
        
        if mean_real > 0.5:
            check_warn("Hohe EE-Realisierung während Dunkelflaute (>50%)")

def validate_scenario(scenario_name: str, verbrauchsprofil_name: str, lastprofil: bool = True, ertragsart: str = "mittel"):
    """
    Führt eine vollständige Validierung eines Szenarios durch
    """
    print_header(f"VALIDIERUNG: SZENARIO '{scenario_name}'")
    print(f"Verbrauchsprofil: {verbrauchsprofil_name}")
    print(f"Lastprofile aktiv: {lastprofil}")
    print(f"Ertragsart: {ertragsart}")
    
    # 1. Lade Szenario-Daten
    szenarien = load_scenarios()
    verbrauchsprofile = load_verbrauchsprofile()
    
    szenario_data = get_scenario_by_name(szenarien, scenario_name)
    if szenario_data is None:
        check_fail(f"Szenario '{scenario_name}' nicht gefunden!")
        return
    
    verbrauchsprofil_data = get_verbrauchsprofil_by_name(verbrauchsprofile, verbrauchsprofil_name)
    if verbrauchsprofil_data is None:
        check_fail(f"Verbrauchsprofil '{verbrauchsprofil_name}' nicht gefunden!")
        return
    
    check_pass("Szenario-Daten erfolgreich geladen")
    
    # 2. Erstelle Szenario-Objekt (führt Berechnungen durch)
    print("\nStarte Szenario-Berechnungen...")
    
    # Konventionelle Anteile aus Szenario laden oder Standardwerte verwenden
    konven_anteile = szenario_data.get("Konventionelle Anteile", {
        "2038": {"braun": 0.25, "erdgas": 0.4, "stein": 0.15, "sonstige": 0.1, "importe": 0.1},
        "2045": {"braun": 0.0, "erdgas": 0.6, "stein": 0.0, "sonstige": 0.2, "importe": 0.2}
    })
    
    try:
        szenario = Szenario(
            name=szenario_data["Name"],
            beschreibung=szenario_data["Beschreibung"],
            szenario=szenario_data,
            ziele_2030=szenario_data["Ziele 2030"],
            ziele_2045=szenario_data["Ziele 2045"],
            ertragsart=ertragsart,
            verbrauchsprofile=verbrauchsprofil_data,
            veränderungsfaktoren=szenario_data["Veränderungsfaktoren"]["Erzeugung"],
            konven_anteile=konven_anteile,
            lastprofile=lastprofil
        )
        check_pass("Szenario erfolgreich erstellt")
    except Exception as e:
        check_fail(f"Fehler beim Erstellen des Szenarios: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Validiere einzelne Komponenten
    try:
        validate_erzeugung(
            szenario.erzeugung_df,
            szenario_data["Ziele 2030"]["Ausbau EE"],
            szenario_data["Ziele 2045"]["Ausbau EE"]
        )
    except Exception as e:
        check_fail(f"Fehler bei Erzeugungsvalidierung: {e}")
    
    try:
        validate_verbrauch(
            szenario.verbrauch_df,
            verbrauchsprofil_data
        )
    except Exception as e:
        check_fail(f"Fehler bei Verbrauchsvalidierung: {e}")
    
    try:
        validate_ee_anteil(szenario.ee_anteil_ohne_speicher_df)
    except Exception as e:
        check_fail(f"Fehler bei EE-Anteil-Validierung: {e}")
    
    try:
        if szenario.speicher_df is not None:
            validate_speicher(
                szenario.speicher_df,
                szenario_data["Ziele 2030"]["Ausbau Speicher"],
                szenario_data["Ziele 2045"]["Ausbau Speicher"]
            )
    except Exception as e:
        check_fail(f"Fehler bei Speichervalidierung: {e}")
    
    try:
        if szenario.kosten_df is not None:
            validate_kosten(szenario.kosten_df)
    except Exception as e:
        check_fail(f"Fehler bei Kostenvalidierung: {e}")
    
    try:
        if szenario.dunkelflaute_2030_df is not None:
            validate_dunkelflaute(szenario.dunkelflaute_2030_df, 2030)
    except Exception as e:
        check_fail(f"Fehler bei Dunkelflaute-2030-Validierung: {e}")
    
    try:
        if szenario.dunkelflaute_2045_df is not None:
            validate_dunkelflaute(szenario.dunkelflaute_2045_df, 2045)
    except Exception as e:
        check_fail(f"Fehler bei Dunkelflaute-2045-Validierung: {e}")
    
    print_header("VALIDIERUNG ABGESCHLOSSEN")

def main():
    """Hauptfunktion für die Validierung"""
    print_header("IPJ1-POTTKIEKER VALIDIERUNGSSKRIPT")
    print("Dieses Skript validiert die Plausibilität und Konsistenz")
    print("der Simulationsergebnisse des Pottkieker-Projekts.")
    
    scenario_name = "Test Szenario"
    verbrauchsprofil_name = "1"
    lastprofil = True
    ertragsart = "mittel"
    
    if len(sys.argv) > 1:
        scenario_name = sys.argv[1]
    if len(sys.argv) > 2:
        verbrauchsprofil_name = sys.argv[2]
    if len(sys.argv) > 3:
        lastprofil = sys.argv[3].lower() in ["true", "ja", "1"]
    if len(sys.argv) > 4:
        ertragsart = sys.argv[4]
    
    print(f"\nParameter:")
    print(f"  Szenario: {scenario_name}")
    print(f"  Verbrauchsprofil: {verbrauchsprofil_name}")
    print(f"  Lastprofile: {lastprofil}")
    print(f"  Ertragsart: {ertragsart}")
    
    input("\nDrücken Sie Enter, um die Validierung zu starten...")
    
    validate_scenario(scenario_name, verbrauchsprofil_name, lastprofil, ertragsart)

if __name__ == "__main__":
    main()
