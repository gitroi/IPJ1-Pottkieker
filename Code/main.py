import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import Analyse
import Erzeugungsprognosen
import Prognose_Verbrauch

# verbrauch = Prognose_Verbrauch.Prognose_Verbrauch(650e6, 1200e6)
# erzeugung = Erzeugungsprognosen.Prognose_erzeugung(0.068, 0.045, 0.1, 0.01, 0, 0)

verbrauch = pd.read_csv('C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\Ist_Analyse\\Verbrauch.csv', sep=';', decimal=',')
erzeugung = pd.read_csv('C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\Ist_Analyse\\Erzeugung.csv', sep=';', decimal=',')

gesamt =Analyse.analyse_erneuerbare_anteil(
    "C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\Ist_Analyse\\erzeugung.csv",
    "C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\Ist_Analyse\\verbrauch.csv",
    "Netzlast inkl. Pumpspeicher [MWh] Originalauflösungen"
)

Analyse.plot_ee_anteil_histogram_overflow(gesamt)