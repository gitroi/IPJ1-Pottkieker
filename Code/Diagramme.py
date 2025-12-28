"""
Programmiert von Joris Bürger
"""
from config import DATA_DIR
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
from Prognose_Erzeugung import Jährlicher_Zuwachs_EE
from Prognose_Speicher import ausbaurate_GWh_Jahr

# Zentrale Definition der Technologie-Mappings
TECHNOLOGIE_MAPPING = {
    'pv_dach': 'PV Dach',
    'pv_frei': 'PV Frei',
    'wind_onshore': 'Wind Onshore',
    'wind_offshore': 'Wind Offshore',
    'biomasse': 'Biomasse',
    'wasser': 'Wasser',
    'sonstige': 'Sonstige',
    'batteriespeicher': 'Batteriespeicher',
    'wasserstoff': 'Wasserstoffspeicher',
    'pumpspeicher': 'Pumpspeicher'
}

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

    ax.set_xlim(0, 115)

    from matplotlib.ticker import MultipleLocator, FuncFormatter
    import math

    max_count = int(max(counts)) if len(counts) > 0 else 0
    approx_ticks = 7
    step_thousands = max(1, math.ceil((max_count / 1000) / approx_ticks))
    step = step_thousands * 1000

    ax.yaxis.set_major_locator(MultipleLocator(step))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x/1000)}"))
    ax.set_ylabel('Anzahl Viertelstunden (in 1.000)')

    plt.tight_layout()


def plot_histogram_ausbauraten_EE(Zieldaten_2030,Zieldaten_2045,ax,ax2):
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
    
    pfad = DATA_DIR / "Feste_Parameter" / "erzeugerarten.json"
    with open(pfad, "r") as file:
        erzeugerarten = json.load(file)

    jahre_liste = list(range(2026, 2046))
    ausbaustände = {et: [] for et in erzeugerarten.keys()}
    for jahr in jahre_liste:
        for et in erzeugerarten.keys():
            if jahr <= 2030:
                ausbaustände[et].append(ausbauraten['zuwachsrate_2030'][et]*(jahr-2025)+erzeugerarten[et]["bestand"])
            else:
                ausbaustände[et].append(ausbauraten['zuwachsrate_2045'][et]*(jahr-2030)+Zieldaten_2030[et])

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
    ax.set_ylabel('Ausbaurate [GW/Jahr]')
    ax.legend(title='Energieträger', loc='upper left', fontsize=8)
    ax.tick_params(axis='x', rotation=0)
    
    max_wert = bottom.max() 
    ax.set_ylim(0, max_wert * 1.1)  
    
    from matplotlib.ticker import MaxNLocator
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=False))
    
    # === Zweites Diagramm: Installierte Leistung pro Jahr ===
    x_positions = np.arange(len(jahre_liste))
    bar_width = 0.8 / len(energietraeger) 
    
    for i, et in enumerate(energietraeger):
        offset = (i - len(energietraeger) / 2) * bar_width + bar_width / 2
        ax2.bar(x_positions + offset, ausbaustände[et], width=bar_width, 
                color=farben[et], label=et.replace('_', ' ').title(), edgecolor='white', linewidth=0.5)
    
    ax2.set_title('Installierte Leistung der Erneuerbaren Energien (2026-2045)')
    ax2.set_xlabel('Jahr')
    ax2.set_ylabel('Installierte Leistung [GW]')
    ax2.set_xticks(x_positions)
    ax2.set_xticklabels(jahre_liste, rotation=45, ha='right')
    ax2.legend(title='Energieträger', loc='upper left', fontsize=8)
    ax2.grid(axis='y', alpha=0.3)
    
    
    max_installiert = max([max(ausbaustände[et]) for et in energietraeger])
    ax2.set_ylim(0, max_installiert * 1.1)
    ax2.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=False))

def plot_histogram_energie_nichtEE(jahreswerte: dict, ax):
    """
    Erstellt ein Histogramm der jährlichen Energieerzeugung aus nicht-erneuerbaren Quellen.
    
    Args:
        jahreswerte (dict): Dictionary mit den jährlichen Energieerzeugungswerten.
        ax (matplotlib.axes.Axes): Axes-Objekt für die Darstellung.
    """
    jahre = sorted(list(jahreswerte.keys()))  # Sortiert die Jahre
    werte = [jahreswerte[jahr]["Energie"] / 1e6 for jahr in jahre] 
    
    ax.bar(jahre, werte, width=0.8, color='gray', label='Nicht-EE Energie')
    ax.set_title('Jährliche Energieerzeugung aus nicht-erneuerbaren Quellen')
    ax.set_xlabel('Jahr')
    ax.set_ylabel('Energie [TWh]')
    
    ax.set_xticks(jahre)
    ax.set_xticklabels(jahre, rotation=45, ha='right')
    
    ax.legend()

def kosten(kosten_df: pd.DataFrame, ax1,ax2):
    """
    Erstellt ein Balkendiagramm der Gesamtkosten für jede Technologie.
    
    Args:
        kosten_df (pd.DataFrame): DataFrame mit den Kosteninformationen.
        ax (matplotlib.axes.Axes): Axes-Objekt für die Darstellung.
    """
    
    farben = {
        'PV Dach': '#F9BF02',
        'PV Frei': '#FFFF00',
        'Wind Onshore': '#87CEEB',
        'Wind Offshore': '#4169E1',
        'Biomasse': '#228B22',
        'Wasser': '#00CED1',
        'Sonstige': '#FF8C00',
        'Batteriespeicher': '#9C27B0',
        'Wasserstoffspeicher': '#E91E63',
        'Pumpspeicher': '#1633D8'
    }
    
    technologien = []
    kosten = []
    
    for key, name in TECHNOLOGIE_MAPPING.items():
        spalte = f"Gesamtkosten {key} [€]"
        if spalte in kosten_df.columns:
            gesamt = kosten_df[spalte].sum() / 1e9  
            technologien.append(name)
            kosten.append(gesamt)
    
    colors = [farben[tech] for tech in technologien]
    ax1.bar(technologien, kosten, color=colors, edgecolor='white')
    ax1.set_title('Gesamtkosten nach Technologie (2026-2045)')
    ax1.set_ylabel('Kosten [Mrd. €]')
    ax1.set_xlabel('Technologie')
    
    ax1.set_xticks(range(len(technologien)))
    ax1.set_xticklabels(technologien, rotation=45, ha='right')
    
    for i, (tech, wert) in enumerate(zip(technologien, kosten)):
        if wert > 0.01:  # Nur Werte > 10 Mio. € anzeigen
            ax1.text(i, wert, f"{wert:.1f}", ha='center', va='bottom', fontsize=8)

    anteil_gesamtkosten = []
    gesamt_kosten = sum(kosten)
    for wert in kosten:
        anteil = (wert / gesamt_kosten) * 100 if gesamt_kosten > 0 else 0
        anteil_gesamtkosten.append(anteil)

    ax2.pie(anteil_gesamtkosten, labels=technologien, autopct='%1.1f%%', startangle=140, colors=colors)
    ax2.set_title('Anteil der Gesamtkosten nach Technologie')

#FIXME: Daten aus Dataframe lesen um Rechenleistung zu vermindern
def plot_histogram_ausbauraten_Speicher(szenario, ax, ax2):
    """ 
    Funktion zur Visualisierung der jährlichen Ausbauraten der Speicher
    von 2026 bis 2045 basierend auf den Zieldaten für 2030 und 2045.
    Darstellung in zwei Balken als gestapeltes Balkendiagramm.
    Args:
        szenario: Szenario-Objekt mit den Speicherzieldaten.
        ax: Achsenobjekt für das erste Diagramm.
        ax2: Achsenobjekt für das zweite Diagramm.
    Unterstützt durch KI (GPT-4.1 Inline Suggestions)
    """
    ausbauraten = ausbaurate_GWh_Jahr(szenario)
    
    pfad = DATA_DIR / "Feste_Parameter" / "speicherarten.json"
    with open(pfad, "r") as file:
        speicherarten = json.load(file)

    jahre_liste = list(range(2026, 2046))
    ausbaustände = {et: [] for et in speicherarten.keys()}
    for jahr in jahre_liste:
        for et in speicherarten.keys():
            if jahr <= 2030:
                ausbaustände[et].append(ausbauraten['zuwachsrate_2030'][et]*(jahr-2025)+speicherarten[et]["bestand"])
            else: 
                ausbaustände[et].append(ausbauraten['zuwachsrate_2045'][et]*(jahr-2030)+szenario["Ziele 2030"]["Ausbau Speicher"][et])

    jahre = ["2026–2030", "2031–2045"]

    speicherarten = ['batteriespeicher', 'wasserstoff', 'pumpspeicher']
    farben = {
        'batteriespeicher': "#9C27B0",
        'wasserstoff': "#E91E63",
        'pumpspeicher': "#1633D8"
    }

    data = {et: [
        ausbauraten['zuwachsrate_2030'][et],  
        ausbauraten['zuwachsrate_2045'][et]    
    ] for et in speicherarten}

    bottom = np.zeros(len(jahre))
    for et in speicherarten:
        ax.bar(jahre, data[et], bottom=bottom, color=farben[et], label=et.replace('_', ' ').title())
        bottom += np.array(data[et])

    ax.set_title('Jährliche Ausbauraten der Speicher (2026-2045)')
    ax.set_xlabel('')
    ax.set_ylabel('Ausbaurate [GWh/Jahr]')
    ax.legend(title='Speicherart', loc='upper left', fontsize=8)
    ax.tick_params(axis='x', rotation=0)
    
    max_wert = bottom.max() 
    ax.set_ylim(0, max_wert * 1.1)  
    
    from matplotlib.ticker import MaxNLocator
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=False))
    
    # === Zweites Diagramm: Installierte Kapazität pro Jahr ===
    x_positions = np.arange(len(jahre_liste))
    bar_width = 0.8 / len(speicherarten) 
    
    for i, et in enumerate(speicherarten):
        offset = (i - len(speicherarten) / 2) * bar_width + bar_width / 2
        ax2.bar(x_positions + offset, ausbaustände[et], width=bar_width, 
                color=farben[et], label=et.replace('_', ' ').title(), edgecolor='white', linewidth=0.5)
    
    ax2.set_title('Installierte Kapazität der Speicher (2026-2045)')
    ax2.set_xlabel('Jahr')
    ax2.set_ylabel('Installierte Kapazität [GWh]')
    ax2.set_xticks(x_positions)
    ax2.set_xticklabels(jahre_liste, rotation=45, ha='right')
    ax2.legend(title='Speicherart', loc='upper left', fontsize=8)
    ax2.grid(axis='y', alpha=0.3)
    
    
    max_installiert = max([max(ausbaustände[et]) for et in speicherarten])
    ax2.set_ylim(0, max_installiert * 1.1)
    ax2.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=False))

def plot_Anteil_EE_mit_ohne_Speicher(gesamt_df: pd.DataFrame, ax):
    """
    Erstellt ein Histogramm zum Vergleich des Anteils der Erneuerbaren Energien
    mit und ohne Speicher für jedes Jahr von 2026 bis 2045.
    
    Args:
        gesamt_df (pd.DataFrame): DataFrame mit den Gesamtdaten.
        ax (matplotlib.axes.Axes): Achsenobjekt für das Diagramm.
    """

    jahre = list(range(2026, 2046))
    anteile_mit_speicher = []
    anteile_ohne_speicher = []

    for jahr in jahre:
        df_jahr = gesamt_df[gesamt_df["Datum von"].dt.year == jahr]
        anteil_mit = df_jahr[df_jahr["Anteil Erneuerbare Speicher [%]"]>= 100].count()
        anteil_ohne = df_jahr[df_jahr["Anteil Erneuerbare [%]"]>= 100].count()
        anteil_mit = (anteil_mit["Anteil Erneuerbare Speicher [%]"] / len(df_jahr)) * 100 if len(df_jahr) > 0 else 0
        anteil_ohne = (anteil_ohne["Anteil Erneuerbare [%]"] / len(df_jahr)) * 100 if len(df_jahr) > 0 else 0
        anteile_mit_speicher.append(anteil_mit)
        anteile_ohne_speicher.append(anteil_ohne)

    x = np.arange(len(jahre))
    width = 0.35

    ax.bar(x - width/2, anteile_ohne_speicher, width, label='Ohne Speicher', color='lightgreen', edgecolor='white')
    ax.bar(x + width/2, anteile_mit_speicher, width, label='Mit Speicher', color='green', edgecolor='white')
    ax.set_xticks(x)
    ax.set_xticklabels(jahre, rotation=45, ha='right')
    ax.set_title('Anteil der Erneuerbaren Energien (2026-2045)')
    ax.set_ylabel('Anteil [%]')
    ax.legend()

def plot_histogram_gesamtauswertung(gesamt_df: pd.DataFrame,ax1,ax2,ax3,ax4):
    """
    Erstellt verschiedene Histogramme zur Gesamtauswertung eines Szenarios.
    
    Args:
        gesamt_df (pd.DataFrame): DataFrame mit den Gesamtdaten.
        ax1 (matplotlib.axes.Axes): Achsenobjekt für das erste Diagramm.
        ax2 (matplotlib.axes.Axes): Achsenobjekt für das zweite Diagramm.
        ax3 (matplotlib.axes.Axes): Achsenobjekt für das dritte Diagramm.
        ax4 (matplotlib.axes.Axes): Achsenobjekt für das vierte Diagramm.
    """

    #=== Histogramm gesamtkosten je Szenario (Zeile df) als Balkendiagramm ===
    szenarien = gesamt_df["Name"].unique()
    gesamtkosten = gesamt_df["Gesamtkosten_EE_und_Speicher [Miliarden €]"].values

    ax1.bar(range(len(szenarien)), gesamtkosten, color='skyblue', edgecolor='white')
    ax1.set_xticks(range(len(szenarien)))
    ax1.set_xticklabels(szenarien, rotation=45, ha='right')
    ax1.set_title('Gesamtkosten je Szenario')
    ax1.set_ylabel('Gesamtkosten [Mrd. €]')

    #=== Strom aus nicht EE als Balkendiagramm ===
    nicht_ee_strom = gesamt_df["Nicht durch EE gedeckter Strombedarf [TWh]"].values

    ax2.bar(range(len(szenarien)), nicht_ee_strom, color='salmon', edgecolor='white')
    ax2.set_xticks(range(len(szenarien)))
    ax2.set_xticklabels(szenarien, rotation=45, ha='right')
    ax2.set_title('Nicht durch EE gedeckter Stromverbrauch je Szenario')
    ax2.set_ylabel('Nicht-EE Stromverbrauch [TWh]')

    #=== Anteil Viertelstunden mit >=100% EE ohne Speicher als Balkendiagramm ===
    anteil_ee_ohne_speicher = gesamt_df[f"Anteil virtel Stunden mit >=100% EE ohne Speicher 2045 [%]"].values
    anteil_mit_speicher = gesamt_df[f"Anteil virtel Stunden mit >=100% EE mit Speicher 2045 [%]"].values

    x = np.arange(len(szenarien))
    width = 0.35

    ax3.bar(x - width/2, anteil_ee_ohne_speicher, width, label='Ohne Speicher', color='lightgreen', edgecolor='white')
    ax3.bar(x + width/2, anteil_mit_speicher, width, label='Mit Speicher', color='green', edgecolor='white')
    ax3.set_xticks(x)
    ax3.set_xticklabels(szenarien, rotation=45, ha='right')
    ax3.set_title('Anteil Viertelstunden mit >=100% EE je Szenario in 2045')
    ax3.set_ylabel('Anteil [%]')
    ax3.legend()

    #=== Benötigte Leistung Konventionelle 2045 als Balkendiagramm ===
    leistung_konventionelle_2030 = gesamt_df["Benötigte Leistung Konventioenelle 2030 [GW]"].values
    leistung_konventionelle_2045 = gesamt_df["Benötigte Leistung Konventioenelle 2045 [GW]"].values

    ax4.bar(x - width/2, leistung_konventionelle_2030, width, label='2030', color='orange', edgecolor='white')
    ax4.bar(x + width/2, leistung_konventionelle_2045, width, label='2045', color='red', edgecolor='white')
    ax4.set_xticks(x)
    ax4.set_xticklabels(szenarien, rotation=45, ha='right')
    ax4.set_title('Benötigte Leistung Konventionelle je Szenario')
    ax4.set_ylabel('Leistung [GW]')
    ax4.legend()

def plot_liniendiagramm_ladestand(gesamt: pd.DataFrame, start_datum,ax: plt.Axes):
    """
    Erstellt ein Liniendiagramm des Ladestands der Speicher über die Zeit.
    
    Args:
        gesamt_df (pd.DataFrame): DataFrame mit den Gesamtdaten.
        ax (matplotlib.axes.Axes): Achsenobjekt für das Diagramm.
    """
    if not isinstance(gesamt.index, pd.DatetimeIndex):
        if 'Datum von' in gesamt.columns:
            gesamt = gesamt.set_index('Datum von')
        else:
            raise ValueError("Der DataFrame-Index muss ein DatetimeIndex sein oder eine 'Datum von' Spalte enthalten")
    
    if start_datum is None:
        start = gesamt.index[0]
    else:
        start = pd.to_datetime(start_datum)
        if gesamt.index.tz is not None:
            if start.tz is None:
                start = start.tz_localize(gesamt.index.tz)
    
    ende = start + pd.Timedelta(days=7)
    
    woche_df = gesamt[(gesamt.index >= start) & (gesamt.index < ende)].copy()
    
    if woche_df.empty:
        raise ValueError("Keine Daten im angegebenen Zeitraum.")
    # woche_df.to_csv("ladestand_debug.csv",sep=";",decimal=",")
    # woche_df = woche_df.resample('h').sum()
    # woche_df.to_csv("ladestand_debug2.csv",sep=";",decimal=",")
    
    woche_df['EE_Status'] = (woche_df["Anteil Erneuerbare [%]"] >= 100).astype(int)
    
    ax.fill_between(woche_df.index, 0, woche_df["Ladestand batteriespeicher [MWh]"]/1e3, label="Batteriespeicher", color='#9C27B0', alpha=0.7)
    ax.fill_between(woche_df.index, 0, woche_df["Ladestand wasserstoff [MWh]"]/1e3, label="Wasserstoffspeicher", color='#E91E63', alpha=0.7)
    ax.fill_between(woche_df.index, 0, woche_df["Ladestand pumpspeicher [MWh]"]/1e3, label="Pumpspeicher", color='#1633D8', alpha=0.7) 
    
    ax.set_title(f"Speichernutzung von {start.date()} bis {ende.date()}")
    ax.set_xlabel('Datum und Uhrzeit')
    ax.set_ylabel('Energie [GWh]')
    ax.legend(loc='upper left')
    ax.grid(True)
    
    ax2 = ax.twinx()
    ax2.plot(woche_df.index, woche_df['EE_Status'], color='orange', linewidth=2, linestyle='-', label='EE-Status', alpha=0.6)
    ax2.set_ylabel('Defizit (0) / Überschuss (1)', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')
    ax2.set_ylim(-0.1, 1.1)
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(['Defizit', 'Überschuss'])
    ax2.legend(loc='upper right')


def verbrauch_jahr(gesamt: pd.DataFrame, jahr: int, ax: plt.Axes):
    """
    Erstellt ein Liniendiagramm des Gesamtenergieverbrauchs für ein bestimmtes Jahr mit Wochenwerten.
    Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
    """
    verbrauch_zeitraum = gesamt.set_index('Datum von')
    verbrauch_zeitraum = verbrauch_zeitraum[verbrauch_zeitraum.index.year == jahr]
    verbrauch_woechentlich = verbrauch_zeitraum.resample('ME').sum()

    ax.plot(verbrauch_woechentlich.index, verbrauch_woechentlich["Netzlast [MWh]"]/1e6, label=f"Verbrauch {jahr}", color='red', marker='o')
    ax.plot(verbrauch_woechentlich.index, verbrauch_woechentlich["Realisierte Erzeugung [MWh]"]/1e6, label="Erzeugung", color='#F9BF02', marker='o')
    ax.plot(verbrauch_woechentlich.index, verbrauch_woechentlich["Energie aus Speicher [MWh]"]/1e6, label="Energie aus Speicher", color='green', marker='o')
    ax.set_title(f"Energieverbrauch im Jahr {jahr} (Wochenwerte)")  
    ax.set_xlabel('Wochen des Jahres')
    ax.set_ylabel('Verbrauch [TWh]')
    ax.legend()

def zweiwochendiagramm_stunden(gesamt: pd.DataFrame, start_datum,ax: plt.Axes):
    """
    Erstellt ein Liniendiagramm der Netzlast, der sumierten erzeugerwerte, sowie der erzeugerwerte
    in Stundenauflösung für eine bestimmte Woche.
    Parameters:
    -----------
    gesamt : pd.DataFrame
        DataFrame mit Verbrauchsdaten, Index muss DatetimeIndex sein oder es muss eine 'Datum von' Spalte vorhanden sein
    start_datum : str oder pd.Timestamp, optional
        Startdatum der Woche (Format: 'YYYY-MM-DD' oder 'YYYY-MM-DD HH:MM:SS')
        Wenn None, wird die erste verfügbare Woche verwendet
    
    Ünterstützt durch KI (GitHub Copilot)
    """
    if not isinstance(gesamt.index, pd.DatetimeIndex):
        if 'Datum von' in gesamt.columns:
            gesamt = gesamt.set_index('Datum von')
        else:
            raise ValueError("Der DataFrame-Index muss ein DatetimeIndex sein oder eine 'Datum von' Spalte enthalten")
    
    if start_datum is None:
        start = gesamt.index[0]
    else:
        start = pd.to_datetime(start_datum)
        if gesamt.index.tz is not None:
            if start.tz is None:
                start = start.tz_localize(gesamt.index.tz)
    
    ende = start + pd.Timedelta(days=14)
    
    woche_df = gesamt[(gesamt.index >= start) & (gesamt.index < ende)]
    
    if woche_df.empty:
        raise ValueError("Keine Daten im angegebenen Zeitraum.")
    
    woche_df = woche_df.resample('h').sum()

    ax.stackplot(woche_df.index, 
                 woche_df["Photovoltaik [MWh] Originalauflösungen"]/1e3,
                 woche_df["Wind Onshore [MWh] Originalauflösungen"]/1e3,
                 woche_df["Wind Offshore [MWh] Originalauflösungen"]/1e3,
                 woche_df["Biomasse [MWh] Originalauflösungen"]/1e3,
                 woche_df["Wasserkraft [MWh] Originalauflösungen"]/1e3,
                 woche_df["Sonstige Erneuerbare [MWh] Originalauflösungen"]/1e3,
                 labels=["PV", "Wind Onshore", "Wind Offshore", "Biomasse", "Wasserkraft", "Sonstige"],
                 colors=['#F9BF02', '#87CEEB', '#4169E1', '#228B22', '#00CED1', '#FF8C00'],
                 alpha=0.8)
    
    ax.plot(woche_df.index, woche_df["Netzlast [MWh]"]/1e3, label="Netzlast", color='red', linewidth=2, linestyle='--')
    
    ax.set_title(f"Energieerzeugung und Verbrauch vom {start.date()} bis {ende.date()}")
    ax.set_xlabel('Datum und Uhrzeit')
    ax.set_ylabel('Energie [GWh]')
    ax.legend()
    ax.grid(True)
