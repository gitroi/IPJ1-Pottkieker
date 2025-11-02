import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import Analyse
import Erzeugungsprognosen
import Prognose_Verbrauch

verbrauch = Prognose_Verbrauch.Prognose_Verbrauch(650e6, 1200e6)
erzeugung = Erzeugungsprognosen.Prognose_erzeugung(0.068, 0.045, 0.09, 0, 0, 0)


Analyse.plot_ee_anteil_histogram(Analyse.analyse_erneuerbare_anteil(
    erzeugung,
    verbrauch,
    "Netzlast [MWh] Originalauflösungen"
))

