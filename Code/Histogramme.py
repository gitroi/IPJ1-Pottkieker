"""
Programmiert von Joris Bürger
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from Prognose_Erzeugung import Jährlicher_Zuwachs_EE

# ==============================
# 1. Visualisierung: Anteil Erneuerbare Energien über die Jahre
# ==============================

def plot_ee_anteil_histogram_overflow(gesamt,jahr:int,ax):
    """
    Erstellt ein Histogramm des Anteils der Erneuerbaren Energien am Stromverbrauch
    und fasst alle Werte >= 100% in einem einzigen Balken zusammen.

    Args:
        gesamt (pd.DataFrame): DataFrame mit der Spalte "Anteil Erneuerbare [MWh]"
    """

    gesamt["Jahr"] = gesamt["Datum von"].dt.year
    if(jahr):
        title = f'Anteil der Erneuerbaren Energien am Stromverbrauch im Jahr {jahr}'
        gesamt = gesamt[gesamt["Jahr"] == jahr]
    else:
        title = 'Anteil der Erneuerbaren Energien am Stromverbrauch (alle Jahre)'

    plt.style.use('_mpl-gallery')

    vals = pd.to_numeric(gesamt["Anteil Erneuerbare Speicher [%]"], errors="coerce")
    vals = vals.replace([np.inf, -np.inf], np.nan).dropna()

    if len(vals) == 0:
        print("Keine gültigen Werte zum Plotten.")
        return

    bin_edges = np.append(np.arange(0, 101, 10), np.inf)

    counts, _ = np.histogram(vals, bins=bin_edges)
    total = counts.sum()
    pct = (counts / total) * 100

    centers = np.append(np.arange(0, 100, 10) + 5, 105)
    labels = [f"{i}-{i+10}%" for i in range(0, 100, 10)] + [">=100%"]

    ax.bar(centers, counts, width=9, color='skyblue', edgecolor='white')

    ax.set_xticks(centers)
    ax.set_xticklabels(labels, rotation=45)

    for count, x, p in zip(counts, centers, pct):
        ax.text(x, count + max(counts) * 0.01, f"{p:.1f}%", ha='center', va='bottom', fontsize=9)

    ax.set_title(title)
    ax.set_xlabel('Anteil Erneuerbare Speicher [%]')
    ax.set_ylabel('Anzahl Viertelstunden')

    ax.set_xlim(0, 115)

    from matplotlib.ticker import MultipleLocator, FuncFormatter
    import math

    max_count = int(max(counts)) if len(counts) > 0 else 0
    approx_ticks = 7
    step_thousands = max(1, math.ceil((max_count / 1000) / approx_ticks))
    step = step_thousands * 1000

    ax.yaxis.set_major_locator(MultipleLocator(step))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x/1000)}"))
    ax.set_ylabel('Anzahl (in 1.000)')

    plt.tight_layout()


def plot_histogram_ausbauraten_EE(Zieldaten_2030,Zieldaten_2045,ax):
    """ 
    Funktion zur Visualisierung der jährlichen Ausbauraten der Erneuerbaren Energien
    von 2026 bis 2045 basierend auf den Zieldaten für 2030 und 2045.
    Darstellung in zwei Balken als gestapeltes Balkendiagramm.
    Args:
        Zieldaten_2030 (dict): Dictionary mit den Zieldaten für 2030.
        Zieldaten_2045 (dict): Dictionary mit den Zieldaten für 2045.
    Unterstützt durch KI (GPT-4.1 Inline Suggestions)
    """
    ausbauraten = Jährlicher_Zuwachs_EE(Zieldaten_2030, Zieldaten_2045)

    #jahre = list({2030, 2045}) 
    #jahre = list(range(2026, 2046))
    jahre = ["2026–2030", "2031–2045"]

    energietraeger = ['pv_dach','pv_frei', 'wind_onshore', 'wind_offshore', 'biomasse', 'wasser', 'sonstige']
    farben = {
        'pv_dach': "#F9BF02",       # Gold
        'pv_frei': "#EEFF00FF",       # Gold
        'wind_onshore': '#87CEEB',  # Sky Blue
        'wind_offshore': '#4169E1', # Royal Blue
        'biomasse': '#228B22',     # Forest Green
        'wasser': '#00CED1',       # Dark Turquoise
        'sonstige': '#FF8C00'      # Dark Orange
    }

    data = {et: [
        ausbauraten['zuwachsrate_2030'][et],  
        ausbauraten['zuwachsrate_2045'][et]    
    ] for et in energietraeger}

    bottom = np.zeros(len(jahre))
    for et in energietraeger:
        ax.bar(jahre, data[et], bottom=bottom, color=farben[et], label=et.replace('_', ' ').title())
        bottom += np.array(data[et])

    ax.set_title('Jährliche Ausbauraten der Erneuerbaren Energien (2026-2045)')
    ax.set_xlabel('')
    ax.set_ylabel('Ausbaurate [GW]')
    ax.legend(title='Energieträger')
    ax.tick_params(axis='x', rotation=0)

