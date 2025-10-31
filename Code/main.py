import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import Analyse

Analyse.plot_ee_anteil_histogram(Analyse.analyse_erneuerbare_anteil(
    "C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\Erzeugungs_Prognose_2026_2045.csv",
    "C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\verbrauch_prognose_2045.csv",
    "Netzlast [MWh]"
))

