import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from Prognose_Erzeugung import Jährlicher_Zuwachs_EE

# ==============================
# 7. Visualisierung: Anteil Erneuerbare Energien über die Jahre
# ==============================
def plot_ee_anteil_histogram(gesamt):
    """
    Erstellt ein Histogramm des Anteils der Erneuerbaren Energien am Stromverbrauch.
    Args:
    gesamt (pd.DataFrame): DataFrame mit der Spalte "Anteil Erneuerbare [MWh]"
    Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
    """

    # erstellen der Bins für das Histogram mit den Abständen von 0 bis 110 in 10 Schritten und sammeln der werte über 100%
    bins = np.linspace(0, 110, 12)  # 0, 10, 20, ..., 100, 110

    plt.style.use('_mpl-gallery')

    # größere Figur und höhere DPI für bessere Lesbarkeit
    fig, ax = plt.subplots(figsize=(12, 6), dpi=140)

    # Defensive Vorbereitung der Daten: konvertieren, Inf/NaN entfernen
    vals = pd.to_numeric(gesamt["Anteil Erneuerbare [%]"], errors="coerce")
    vals = vals.replace([np.inf, -np.inf], np.nan).dropna()

    if len(vals) == 0:
        print("Keine gültigen Werte zum Plotten.")
    else:
        # Histogramm erstellen und Prozentwerte berechnen
        n, bins, patches = ax.hist(vals, bins=bins, color='skyblue', edgecolor='white')
        total = n.sum()
        # Prozentwerte je Bin (in %)
        pct = (n / total) * 100

        # X-Achsen-Labels erstellen (0-10%, 10-20%, etc.)
        labels = [f"{int(bins[i])}-{int(bins[i+1])}%" for i in range(len(bins)-1)]
        plt.xticks(bins[:-1] + 5, labels, rotation=45)  # Labels um 45 Grad drehen für bessere Lesbarkeit

        # Beschriftungen über den Balken
        for count, x_left, x_right, p in zip(n, bins[:-1], bins[1:], pct):
            # x-Position in der Mitte des Balkens
            x = (x_left + x_right) / 2
            # y-Position leicht über dem Balken
            y = count
            ax.text(x, y + max(n) * 0.01, f"{p:.1f}%", ha='center', va='bottom', fontsize=9)

        # Achsentitel und Diagrammtitel
        ax.set_title('Anteil der Erneuerbaren Energien am Stromverbrauch')
        ax.set_xlabel('Anteil Erneuerbare [%]')
        ax.set_ylabel('Anzahl Viertelstunden')

        # Optional: x-Lim auf sinnvollen Bereich setzen (0-600% für prozentuale Anteile)
        ax.set_xlim(0, 110)

        # Y-Achse in Tausender-Einheiten formatieren (z.B. 5,10,15 statt 5000,10000,15000)
        from matplotlib.ticker import MultipleLocator, FuncFormatter
        import math

        max_count = int(max(n)) if len(n) > 0 else 0
        # Ziel: ca. 7 Ticks => Schritt in Tausendern bestimmen
        approx_ticks = 7
        step_thousands = max(1, math.ceil((max_count / 1000) / approx_ticks))
        step = step_thousands * 1000

        ax.yaxis.set_major_locator(MultipleLocator(step))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x/1000)}"))
        ax.set_ylabel('Anzahl (in 1.000)')

        plt.tight_layout() #tight layout for better spacing
        
    plt.show()


def plot_ee_anteil_histogram_overflow(gesamt,jahr:int):
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

    # größere Figur und höhere DPI für bessere Lesbarkeit
    fig, ax = plt.subplots(figsize=(12, 6), dpi=140)

    # Defensive Vorbereitung der Daten: konvertieren, Inf/NaN entfernen
    vals = pd.to_numeric(gesamt["Anteil Erneuerbare [%]"], errors="coerce")
    vals = vals.replace([np.inf, -np.inf], np.nan).dropna()

    if len(vals) == 0:
        print("Keine gültigen Werte zum Plotten.")
        return

    # --- Histogramm counts berechnen: letzte Bin fasst alles >= 100% zusammen ---
    # Bin-Kanten: 0,10,20,...,90,100 und ein abschließendes +inf für ">=100%"
    bin_edges = np.append(np.arange(0, 101, 10), np.inf)

    counts, _ = np.histogram(vals, bins=bin_edges)
    total = counts.sum()
    # Prozentwerte je Bin (in %)
    pct = (counts / total) * 100

    # Balkenpositionen für die Anzeige: Mittelpunkte 0-10 -> 5, 10-20 -> 15, ..., 90-100 -> 95
    # Zusätzlicher Mittelpunkt für das Overflow-Bin (>=100%) bei x=105
    centers = np.append(np.arange(0, 100, 10) + 5, 105)
    # Labels: 0-10%, 10-20%, ..., 90-100%, >=100%
    labels = [f"{i}-{i+10}%" for i in range(0, 100, 10)] + [">=100%"]

    # Balken zeichnen (letzter Balken an Position 105 für ">=100%")
    ax.bar(centers, counts, width=9, color='skyblue', edgecolor='white')

    # X‑Ticks / Labels setzen
    ax.set_xticks(centers)
    ax.set_xticklabels(labels, rotation=45)

    # Beschriftungen über den Balken (inkl. letztem Bin)
    for count, x, p in zip(counts, centers, pct):
        ax.text(x, count + max(counts) * 0.01, f"{p:.1f}%", ha='center', va='bottom', fontsize=9)

    # Achsentitel und Diagrammtitel
    ax.set_title(title)
    ax.set_xlabel('Anteil Erneuerbare [%]')
    ax.set_ylabel('Anzahl Viertelstunden')

    # Optional: x-Lim auf sinnvollen Bereich setzen (Platz für Overflow-Balken schaffen)
    ax.set_xlim(0, 115)

    # Y-Achse in Tausender-Einheiten formatieren
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
    plt.show(block=False)


def plot_histogram_ausbauraten_EE(Zieldaten_2030,Zieldaten_2045):
    """ Funktiom zur Visualisierung der Ausbauraten der Erneuerbaren Energien als Histogramm.
    Args:
        Zieldaten_2030 (dict): Dictionary mit den Zieldaten für 2030.
        Zieldaten_2045 (dict): Dictionary mit den Zieldaten für 2045.
    Unterstützt durch KI (GPT-4.1 Inline Suggestions)
    """
    ausbauraten = Jährlicher_Zuwachs_EE(Zieldaten_2030, Zieldaten_2045)

    jahre = list(range(2026, 2046))

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

    data = {et: [] for et in energietraeger}

    for jahr in jahre:
        for et in energietraeger:
            if jahr <= 2030:
                data[et].append(ausbauraten['zuwachsrate_2030'][et])
            else:
                data[et].append(ausbauraten['zuwachsrate_2045'][et])

    # Plot erstellen
    plt.style.use('_mpl-gallery')
    fig, ax = plt.subplots(figsize=(14, 7), dpi=140)
    bottom = np.zeros(len(jahre))
    for et in energietraeger:
        ax.bar(jahre, data[et], bottom=bottom, color=farben[et], label=et.replace('_', ' ').title())
        bottom += np.array(data[et])

    ax.set_title('Jährliche Ausbauraten der Erneuerbaren Energien (2026-2045)')
    ax.set_xlabel('Jahr')
    ax.set_ylabel('Ausbaurate [GW]')
    ax.legend(title='Energieträger')
    plt.tight_layout()
    plt.show(block =False)

