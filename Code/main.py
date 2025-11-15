"""
Zentrales Programm der Gruppe Pottkieker.
Nutz die anderen Module zur Analyse und Visualisierung.
Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from Analyse import analyse_erneuerbare_anteil
from Erzeugungsprognosen import Prognose_erzeugung
from Prognose_Verbrauch import Prognose_Verbrauch
from Histogramme import plot_ee_anteil_histogram_overflow
from EE_Anteil_DataFrame import anteil_erneuerbare_df,anteil_erneuerbare_Jahrx_df
from config import PROJECT_ROOT

map_installed_capacity = {
    "pv": 285,  
    "wind_onshore": 90,
    "wind_offshore": 40,
    "biomasse": 6,
    "wasser": 9,
    "sonstige": 3
}

map_installed_capacity_2045 = {
    "pv": 485,
    "wind_onshore": 145,
    "wind_offshore": 75,
    "biomasse": 4,
    "wasser": 9,
    "sonstige": 3
}

verbrauch = Prognose_Verbrauch(650, 1000)
erzeugung = Prognose_erzeugung(map_installed_capacity, map_installed_capacity_2045)

gesamt2 = anteil_erneuerbare_Jahrx_df(erzeugung, verbrauch, "Netzlast [MWh] Originalauflösungen",2026)
    
gesamt2["Jahr"] = gesamt2["Datum von"].dt.year
print(gesamt2[gesamt2["Jahr"]==2026]["Erneuerbare [MWh]"].sum()/1e6)
print(gesamt2[gesamt2["Jahr"]==2026]["Netzlast [MWh] Originalauflösungen"].sum()/1e6)


# gesamt =analyse_erneuerbare_anteil(
#      PROJECT_ROOT / "Daten" / "Ist_Analyse" / "erzeugung.csv",
#      PROJECT_ROOT / "Daten" / "Ist_Analyse" / "verbrauch.csv",
#      "Netzlast inkl. Pumpspeicher [MWh] Originalauflösungen"
# )

plot_ee_anteil_histogram_overflow(gesamt2)
# plot_ee_anteil_histogram_overflow(gesamt)