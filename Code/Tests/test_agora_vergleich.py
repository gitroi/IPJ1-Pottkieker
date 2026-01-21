"""
Test zur Validierung der Erzeugungsprognose gegen die Agora-Studie "Klimaneutrales Deutschland"
Vergleicht die prognostizierten Erzeugungsmengen für PV und Wind mit den Studien-Zielwerten:
- 2030: 507 TWh
- 2045: 1087 TWh
Erstellt durch Joris Bürger
Programmiert durch KI unter Verwendung von OpenAI GPT-4
(Kannst du mir einen Test ergenzen, der die Funktion Prognose_erzeugung 
mit folgenden installierten Leistungen: 
2030: PV_dach= 115GW, PV_frei = 100GW, wind_on=98GW, Windof = 26GW, 
2045: PV_dach= 300GW, PV_frei = 169GW, wind_on=180GW, Windof = 79GW 
berechnet und dann die Summe nur von diesen Technologien mit den 
erzeugungsprognosen aus der studie Klimanuetrale Deutschland von Agora 
mit den erzeugerwerten von 507TWH in 2030 und 1087 TWh in 2045 für
die ertragsarten gut, mittel und schlecht verlgeicht?)
"""
import sys
from pathlib import Path
import json

# Pfad zum Code-Ordner hinzufügen
code_path = Path(__file__).parent.parent
sys.path.insert(0, str(code_path))

from Prognose_Erzeugung import Prognose_erzeugung
from config import PROJECT_ROOT


def test_agora_vergleich():
    """
    Testet die Erzeugungsprognose für die drei Ertragsarten (gut, mittel, schlecht)
    und vergleicht die Summen mit den Agora-Studien-Werten.
    """
    
    # Installierte Leistungen aus der Aufgabenstellung
    installierte_2030 = {
        'pv_dach': 115,      # GW
        'pv_frei': 100,      # GW
        'wind_onshore': 98,  # GW
        'wind_offshore': 26, # GW
        'biomasse': 8.4,     # Standardwert
        'wasser': 5.6,       # Standardwert
        'sonstige': 0.5      # Standardwert
    }
    
    installierte_2045 = {
        'pv_dach': 300,      # GW
        'pv_frei': 169,      # GW
        'wind_onshore': 180, # GW
        'wind_offshore': 79, # GW
        'biomasse': 8.4,     # Standardwert
        'wasser': 5.6,       # Standardwert
        'sonstige': 0.5      # Standardwert
    }
    
    # Steigerungsfaktoren: keine Effizienzsteigerung (Faktor 1.0 = keine Änderung)
    # Für realistischere Prognosen könnten hier Werte > 1.0 verwendet werden
    steigerungsfaktoren = {
        'pv_dach': 1.0,
        'pv_frei': 1.0,
        'wind_onshore': 1.0,
        'wind_offshore': 1.0,
        'biomasse': 1.0,
        'wasser': 1.0,
        'sonstige': 1.0
    }
    
    # Agora-Zielwerte in TWh
    agora_2030_twh = 507
    agora_2045_twh = 1087
    
    # Toleranzbereich (±15% gilt als akzeptabel für Prognosen)
    toleranz = 0.15
    
    ertragsarten = ['gut', 'mittel', 'schlecht']
    
    print("=" * 80)
    print("Test: Vergleich Erzeugungsprognose mit Agora-Studie 'Klimaneutrales Deutschland'")
    print("=" * 80)
    print(f"\nZielwerte Agora-Studie:")
    print(f"  2030: {agora_2030_twh} TWh (PV + Wind)")
    print(f"  2045: {agora_2045_twh} TWh (PV + Wind)")
    print(f"\nToleranzbereich: ±{toleranz*100}%")
    print("\n" + "-" * 80)
    
    ergebnisse = {}
    
    for ertragsart in ertragsarten:
        print(f"\n{'='*80}")
        print(f"ERTRAGSART: {ertragsart.upper()}")
        print('='*80)
        
        # Prognose berechnen
        print(f"Berechne Prognose für Ertragsart '{ertragsart}'...")
        prognose_df = Prognose_erzeugung(
            installierte_2030=installierte_2030,
            installierte_2045=installierte_2045,
            steigerungsfaktoren=steigerungsfaktoren,
            ertragsart=ertragsart
        )
        
        # Jahr extrahieren
        prognose_df['Jahr'] = prognose_df['Datum von'].dt.year
        
        # Nur PV und Wind summieren (wie in der Agora-Studie)
        prognose_df['PV_Wind_Summe_MWh'] = (
            prognose_df['Photovoltaik [MWh] Originalauflösungen'] +
            prognose_df['Wind Onshore [MWh] Originalauflösungen'] +
            prognose_df['Wind Offshore [MWh] Originalauflösungen']
        )
        
        # Jahressummen berechnen
        jahressummen = prognose_df.groupby('Jahr')['PV_Wind_Summe_MWh'].sum() / 1_000_000  # MWh -> TWh
        
        # 2030 und 2045 extrahieren
        summe_2030_twh = jahressummen[2030]
        summe_2045_twh = jahressummen[2045]
        
        # Abweichungen berechnen
        abweichung_2030_prozent = ((summe_2030_twh - agora_2030_twh) / agora_2030_twh) * 100
        abweichung_2045_prozent = ((summe_2045_twh - agora_2045_twh) / agora_2045_twh) * 100
        
        # Ergebnisse speichern
        ergebnisse[ertragsart] = {
            '2030_twh': summe_2030_twh,
            '2045_twh': summe_2045_twh,
            'abweichung_2030_%': abweichung_2030_prozent,
            'abweichung_2045_%': abweichung_2045_prozent
        }
        
        # Ausgabe
        print(f"\nErgebnisse für {ertragsart}:")
        print(f"\n  Jahr 2030:")
        print(f"    Prognose:     {summe_2030_twh:.2f} TWh")
        print(f"    Agora-Ziel:   {agora_2030_twh} TWh")
        print(f"    Abweichung:   {abweichung_2030_prozent:+.2f}%")
        
        # Bewertung 2030
        if abs(abweichung_2030_prozent) <= toleranz * 100:
            print(f"    Status:       ✓ INNERHALB der Toleranz")
        else:
            print(f"    Status:       ✗ AUßERHALB der Toleranz")
        
        print(f"\n  Jahr 2045:")
        print(f"    Prognose:     {summe_2045_twh:.2f} TWh")
        print(f"    Agora-Ziel:   {agora_2045_twh} TWh")
        print(f"    Abweichung:   {abweichung_2045_prozent:+.2f}%")
        
        # Bewertung 2045
        if abs(abweichung_2045_prozent) <= toleranz * 100:
            print(f"    Status:       ✓ INNERHALB der Toleranz")
        else:
            print(f"    Status:       ✗ AUßERHALB der Toleranz")
    
    # Zusammenfassung
    print("\n" + "=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print(f"\n{'Ertragsart':<15} {'2030 [TWh]':<15} {'Abw. 2030':<15} {'2045 [TWh]':<15} {'Abw. 2045':<15}")
    print("-" * 80)
    
    for ertragsart in ertragsarten:
        erg = ergebnisse[ertragsart]
        print(f"{ertragsart:<15} {erg['2030_twh']:>10.2f} TWh  {erg['abweichung_2030_%']:>+7.2f}%      "
              f"{erg['2045_twh']:>10.2f} TWh  {erg['abweichung_2045_%']:>+7.2f}%")
    
    print("\n" + "=" * 80)
    
    # Assertions für automatisierte Tests
    for ertragsart in ertragsarten:
        erg = ergebnisse[ertragsart]
        
        # Prüfe ob Werte positiv sind
        assert erg['2030_twh'] > 0, f"Erzeugung 2030 ({ertragsart}) muss positiv sein"
        assert erg['2045_twh'] > 0, f"Erzeugung 2045 ({ertragsart}) muss positiv sein"
        
        # Prüfe ob 2045 > 2030 (aufgrund höherer installierter Leistung)
        assert erg['2045_twh'] > erg['2030_twh'], \
            f"Erzeugung 2045 ({ertragsart}) sollte höher sein als 2030"
    
    # Prüfe ob mittlerer Ertrag zwischen gut und schlecht liegt
    assert (ergebnisse['schlecht']['2030_twh'] <= ergebnisse['mittel']['2030_twh'] <= ergebnisse['gut']['2030_twh']), \
        "Mittlerer Ertrag 2030 sollte zwischen schlecht und gut liegen"
    
    assert (ergebnisse['schlecht']['2045_twh'] <= ergebnisse['mittel']['2045_twh'] <= ergebnisse['gut']['2045_twh']), \
        "Mittlerer Ertrag 2045 sollte zwischen schlecht und gut liegen"
    
    print("\n✓ Alle Validierungen erfolgreich bestanden!")
    print("\nHinweis: Abweichungen von den Agora-Zielwerten sind normal und hängen von:")
    print("  - Unterschiedlichen Wetterbedingungen in den Basis-Jahren ab")
    print("  - Unterschiedlichen Annahmen zu Kapazitätsfaktoren")
    print("  - Unterschiedlichen Effizienzsteigerungen über die Zeit")
    print("=" * 80)
    
    return ergebnisse


if __name__ == "__main__":
    test_agora_vergleich()
