"""
Zentrales Programm der Gruppe Pottkieker.
Nutz die anderen Module zur Analyse und Visualisierung.
Ünterstützt durch KI (Claude Sonnet 4.5)
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import Analyse
import Erzeugungsprognosen
import Prognose_Verbrauch
import Histogramme as Hist
import EE_Anteil_DataFrame as EEdf
from config import PROJECT_ROOT

map_installed_capacity = {
    "pv": 485,  
    "wind_onshore": 145,
    "wind_offshore": 75,
    "biomasse": 4,
    "wasser": 9,
    "sonstige": 3
}

verbrauch = Prognose_Verbrauch.Prognose_Verbrauch(650, 1000)
erzeugung = Erzeugungsprognosen.Prognose_erzeugung(map_installed_capacity, installierte_2045=None)

gesamt2 = EEdf.anteil_erneuerbare_Jahrx_df(erzeugung, verbrauch, "Netzlast [MWh] Originalauflösungen",2045)
    
gesamt2["Jahr"] = gesamt2["Datum von"].dt.year
print(gesamt2[gesamt2["Jahr"]==2045]["Erneuerbare [MWh]"].sum()/1e6)
print(gesamt2[gesamt2["Jahr"]==2045]["Netzlast [MWh] Originalauflösungen"].sum()/1e6)

# gesamt =Analyse.analyse_erneuerbare_anteil(
#      PROJECT_ROOT / "Daten" / "Ist_Analyse" / "erzeugung.csv",
#      PROJECT_ROOT / "Daten" / "Ist_Analyse" / "verbrauch.csv",
#      "Netzlast inkl. Pumpspeicher [MWh] Originalauflösungen"
# )

Hist.plot_ee_anteil_histogram_overflow(gesamt2)
# Hist.plot_ee_anteil_histogram_overflow(gesamt)