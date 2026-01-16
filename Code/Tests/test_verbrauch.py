"""
Test für Prognose_Verbrauch.py
Prüft ob die Gesamtjahresverbräuche mit und ohne Lastprofil korrekt erreicht werden.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import json
from Prognose_Verbrauch import Prognose_Verbrauch
from config import DATA_DIR


def test_gesamtjahresverbrauch():
    """
    Testet, ob der Gesamtjahresverbrauch in 2030 und 2045 mit und ohne Lastprofil
    annähernd den Zielwerten aus den Verbrauchsprofilen entspricht.
    """
    print("\n" + "="*70)
    print("  TEST: Gesamtjahresverbrauch mit/ohne Lastprofil")
    print("="*70)
    
    # Lade Verbrauchsprofile
    verbrauchsprofile_pfad = DATA_DIR / "Verbrauchsprofile.json"
    with open(verbrauchsprofile_pfad, "r") as file:
        verbrauchsprofile = json.load(file)
    
    # Toleranz: 2% Abweichung erlaubt
    toleranz_prozent = 2.0
    
    for profil in verbrauchsprofile:
        profil_name = profil["Name"]
        ziel_2030_TWh = profil["Verbrauch_2030"]
        ziel_2045_TWh = profil["Verbrauch_2045"]
        
        print(f"\n--- Verbrauchsprofil: {profil_name} ---")
        print(f"Zielwerte: 2030={ziel_2030_TWh} TWh, 2045={ziel_2045_TWh} TWh")
        
        # Test MIT Lastprofil
        print("\n1. MIT Lastprofil:")
        df_mit_lastprofil = Prognose_Verbrauch(profil, lastprofil=True)
        
        verbrauch_2030_mit = df_mit_lastprofil[
            df_mit_lastprofil["Datum von"].dt.year == 2030
        ]["Netzlast [MWh]"].sum()
        
        verbrauch_2045_mit = df_mit_lastprofil[
            df_mit_lastprofil["Datum von"].dt.year == 2045
        ]["Netzlast [MWh]"].sum()
        
        # Umrechnung MWh -> TWh
        verbrauch_2030_mit_TWh = verbrauch_2030_mit / 1e6
        verbrauch_2045_mit_TWh = verbrauch_2045_mit / 1e6
        
        abweichung_2030_mit = abs(verbrauch_2030_mit_TWh - ziel_2030_TWh) / ziel_2030_TWh * 100
        abweichung_2045_mit = abs(verbrauch_2045_mit_TWh - ziel_2045_TWh) / ziel_2045_TWh * 100
        
        print(f"   2030: {verbrauch_2030_mit_TWh:.2f} TWh (Abweichung: {abweichung_2030_mit:.2f}%)")
        print(f"   2045: {verbrauch_2045_mit_TWh:.2f} TWh (Abweichung: {abweichung_2045_mit:.2f}%)")
        
        # Test OHNE Lastprofil
        print("\n2. OHNE Lastprofil:")
        df_ohne_lastprofil = Prognose_Verbrauch(profil, lastprofil=False)
        
        verbrauch_2030_ohne = df_ohne_lastprofil[
            df_ohne_lastprofil["Datum von"].dt.year == 2030
        ]["Netzlast [MWh]"].sum()
        
        verbrauch_2045_ohne = df_ohne_lastprofil[
            df_ohne_lastprofil["Datum von"].dt.year == 2045
        ]["Netzlast [MWh]"].sum()
        
        verbrauch_2030_ohne_TWh = verbrauch_2030_ohne / 1e6
        verbrauch_2045_ohne_TWh = verbrauch_2045_ohne / 1e6
        
        abweichung_2030_ohne = abs(verbrauch_2030_ohne_TWh - ziel_2030_TWh) / ziel_2030_TWh * 100
        abweichung_2045_ohne = abs(verbrauch_2045_ohne_TWh - ziel_2045_TWh) / ziel_2045_TWh * 100
        
        print(f"   2030: {verbrauch_2030_ohne_TWh:.2f} TWh (Abweichung: {abweichung_2030_ohne:.2f}%)")
        print(f"   2045: {verbrauch_2045_ohne_TWh:.2f} TWh (Abweichung: {abweichung_2045_ohne:.2f}%)")
        
        # Validierung
        print("\n3. Validierung:")
        
        if abweichung_2030_mit <= toleranz_prozent:
            print(f"   ✅ 2030 MIT Lastprofil innerhalb der Toleranz ({toleranz_prozent}%)")
        else:
            print(f"   ❌ 2030 MIT Lastprofil außerhalb der Toleranz (Abw: {abweichung_2030_mit:.2f}%)")
        
        if abweichung_2045_mit <= toleranz_prozent:
            print(f"   ✅ 2045 MIT Lastprofil innerhalb der Toleranz ({toleranz_prozent}%)")
        else:
            print(f"   ❌ 2045 MIT Lastprofil außerhalb der Toleranz (Abw: {abweichung_2045_mit:.2f}%)")
        
        if abweichung_2030_ohne <= toleranz_prozent:
            print(f"   ✅ 2030 OHNE Lastprofil innerhalb der Toleranz ({toleranz_prozent}%)")
        else:
            print(f"   ❌ 2030 OHNE Lastprofil außerhalb der Toleranz (Abw: {abweichung_2030_ohne:.2f}%)")
        
        if abweichung_2045_ohne <= toleranz_prozent:
            print(f"   ✅ 2045 OHNE Lastprofil innerhalb der Toleranz ({toleranz_prozent}%)")
        else:
            print(f"   ❌ 2045 OHNE Lastprofil außerhalb der Toleranz (Abw: {abweichung_2045_ohne:.2f}%)")
        
        # Unterschied zwischen mit und ohne Lastprofil
        diff_2030 = abs(verbrauch_2030_mit - verbrauch_2030_ohne)
        diff_2045 = abs(verbrauch_2045_mit - verbrauch_2045_ohne)
        
        print(f"\n4. Unterschied mit/ohne Lastprofil:")
        print(f"   2030: {diff_2030/1e6:.2f} TWh Unterschied")
        print(f"   2045: {diff_2045/1e6:.2f} TWh Unterschied")
        
        # Assertions für automatisiertes Testing
        assert abweichung_2030_mit <= toleranz_prozent, \
            f"2030 mit Lastprofil: Abweichung {abweichung_2030_mit:.2f}% > {toleranz_prozent}%"
        assert abweichung_2045_mit <= toleranz_prozent, \
            f"2045 mit Lastprofil: Abweichung {abweichung_2045_mit:.2f}% > {toleranz_prozent}%"
        assert abweichung_2030_ohne <= toleranz_prozent, \
            f"2030 ohne Lastprofil: Abweichung {abweichung_2030_ohne:.2f}% > {toleranz_prozent}%"
        assert abweichung_2045_ohne <= toleranz_prozent, \
            f"2045 ohne Lastprofil: Abweichung {abweichung_2045_ohne:.2f}% > {toleranz_prozent}%"
    
    print("\n" + "="*70)
    print("  ✅ ALLE TESTS ERFOLGREICH")
    print("="*70)


if __name__ == "__main__":
    test_gesamtjahresverbrauch()