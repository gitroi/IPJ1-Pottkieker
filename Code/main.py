import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import Analyse
import Erzeugungsprognosen
import Prognose_Verbrauch
import Histogramme as Hist
import EE_Anteil_DataFrame as EEdf

verbrauch = Prognose_Verbrauch.Prognose_Verbrauch(650e6, 1200e6)
erzeugung = Erzeugungsprognosen.Prognose_erzeugung(0.068, 0.045, 0.1, 0.01, 0, 0)

gemerged = pd.merge(
    erzeugung,
    verbrauch,
    on="Datum von",
    how="inner",
)   

gemerged = gemerged.head()

gemerged.to_excel(
    "C:\\Users\\joris\\Documents\\IPJ1\\Daten\\Prognose_Verbrauch_Erzeugung.xlsx",
    index=False, 
)

gesamt2 = EEdf.anteil_erneuerbare_df(erzeugung, verbrauch, "Netzlast [MWh] Originalauflösungen")
print(gesamt2.head())  

# gesamt =Analyse.analyse_erneuerbare_anteil(
#      "C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\Ist_Analyse\\erzeugung.csv",
#      "C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\Ist_Analyse\\verbrauch.csv",
#      "Netzlast inkl. Pumpspeicher [MWh] Originalauflösungen"
# )

# Hist.plot_ee_anteil_histogram_overflow(gesamt2)