"""
Zentrales Programm der Gruppe Pottkieker.
Nutz die anderen Module zur Analyse und Visualisierung.
Programmiert von Joris Bürger
"""

import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from Szenarien_auswahl import prognose_eines_Szenarios,prognose_alle_Szenarien


def main():
    """Hauptfunktion des Programms."""
    print("Starte Szenario-Prognose...")
    while(True):
        auswahl = input("Was möchten Sie simulieren? Ein Szenario oder alle? ")

        if auswahl.lower() not in ("ein szenario", "alle"):
            print("Ungültige Eingabe. Bitte 'Ein Szenario' oder 'salle' eingeben.")
            raise ValueError("Ungültige Eingabe.")
        
        if auswahl.lower() == "ein szenario":
            start = time.time()
            prognose_eines_Szenarios()
        elif auswahl.lower() == "alle":
            start = time.time()
            prognose_alle_Szenarien()

        print("Simulation abgeschlossen.")
        end = time.time()
        print(f"Benötigte Zeit: {end - start:.2f} Sekunden.")
        if input("Möchten Sie eine weitere Simulation durchführen? (ja/nein) ").lower() != "ja":
            break

main()