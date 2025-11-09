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

verbrauch = Prognose_Verbrauch.Prognose_Verbrauch(650e6, 1200e6)
erzeugung = Erzeugungsprognosen.Prognose_erzeugung(0.06, 0.065, 0.09, 0, 0, 0)

gesamt2 = EEdf.anteil_erneuerbare_df(erzeugung, verbrauch, "Netzlast [MWh] Originalauflösungen")

# gesamt =Analyse.analyse_erneuerbare_anteil(
#      PROJECT_ROOT / "Daten" / "Ist_Analyse" / "erzeugung.csv",
#      PROJECT_ROOT / "Daten" / "Ist_Analyse" / "verbrauch.csv",
#      "Netzlast inkl. Pumpspeicher [MWh] Originalauflösungen"
# )

Hist.plot_ee_anteil_histogram_overflow(gesamt2)
# Hist.plot_ee_anteil_histogram_overflow(gesamt)