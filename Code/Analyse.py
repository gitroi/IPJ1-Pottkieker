import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def analyse_erneuerbare_anteil(pfaderzeugung, pfadverbrauch, spaltenname_verbrauch):
    """
    Analysiert den Anteil der Erneuerbaren Energien am Stromverbrauch
    basierend auf den CSV-Dateien 'erzeugung.csv' und 'verbrauch.csv'.
    Erstellt Visualisierungen und speichert die Ergebnisse in einer Excel-Datei.
    """
    # ==============================
    # 1. CSV-Dateien einlesen
    # ==============================

    erzeugung = pd.read_csv(pfaderzeugung, sep=";", low_memory=False)
    verbrauch = pd.read_csv(pfadverbrauch, sep=";", low_memory=False)

    # ==============================
    # 2. Datumsangaben konvertieren
    # ==============================

    erzeugung["Datum von"] = pd.to_datetime(erzeugung["Datum von"], format="%d.%m.%Y %H:%M")
    verbrauch["Datum von"] = pd.to_datetime(verbrauch["Datum von"], format="%d.%m.%Y %H:%M")

    # ==============================
    # 3. Anpassen der Datein (Entfernen von Leerzeichen in Spaltennamen etc.) 
    # ==============================

    for col in erzeugung.columns:
        if "MWh" in col:
            erzeugung[col] = (
                erzeugung[col]
                .astype(str)
                .str.replace("-", "0", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .astype(float)
    )

    for col in verbrauch.columns:
        if "MWh" in col:
            verbrauch[col] = (
                verbrauch[col]
                .astype(str)
                .str.replace("-", "0", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .astype(float)
        )

    # ==============================
    # 4. Erneuerbare Energien zusammenfassen
    # ==============================

    erneuerbare_cols = [
    "Biomasse [MWh] Originalauflösungen",
    "Wasserkraft [MWh] Originalauflösungen",
    "Wind Offshore [MWh] Originalauflösungen",
    "Wind Onshore [MWh] Originalauflösungen",
    "Photovoltaik [MWh] Originalauflösungen",
    "Sonstige Erneuerbare [MWh] Originalauflösungen",
    ]

    erzeugung["Erneuerbare [MWh]"] = erzeugung[erneuerbare_cols].sum(axis=1)

    # ==============================
    # 5. verbrauch und erzeugung zusammenführen und anteile berechnen
    # ==============================

    gesamt = pd.merge(
    erzeugung[["Datum von","Biomasse [MWh] Originalauflösungen",
        "Wasserkraft [MWh] Originalauflösungen",
        "Wind Offshore [MWh] Originalauflösungen",
        "Wind Onshore [MWh] Originalauflösungen",
        "Photovoltaik [MWh] Originalauflösungen",
        "Sonstige Erneuerbare [MWh] Originalauflösungen",
        "Erneuerbare [MWh]"]],
    verbrauch[["Datum von",  spaltenname_verbrauch]],
    on="Datum von",
    how="inner",
    )

    # sichere Division: ersetze 0 durch np.nan vor Division
    den = gesamt[ spaltenname_verbrauch].replace(0, np.nan)
    gesamt["Anteil Erneuerbare [MWh]"] = (gesamt["Erneuerbare [MWh]"] / den * 100).round(2)

    # ==============================
    # 6. Ergebnisse in eine Excel-Datei speichern
    # ==============================
    #  gesamt.to_excel(
    #     "C:\\Users\\joris\\Documents\\IPJ1\\Daten\\Analyse_Erneuerbare_Anteil.xlsx",
    #    index=False, 
    #  )

    return gesamt



# ==============================
# 7. Visualisierung: Anteil Erneuerbare Energien über die Jahre
# ==============================
def plot_ee_anteil_histogram(gesamt):
    """
    Erstellt ein Histogramm des Anteils der Erneuerbaren Energien am Stromverbrauch.
    Args:
    gesamt (pd.DataFrame): DataFrame mit der Spalte "Anteil Erneuerbare [MWh]"
    """

    # erstellen der Bins für das Histogram mit den Abständen von 0 bis 110 in 10 Schritten und sammeln der werte über 100%
    bins = np.linspace(0, 110, 12)  # 0, 10, 20, ..., 100, 110

    plt.style.use('_mpl-gallery')

    # größere Figur und höhere DPI für bessere Lesbarkeit
    fig, ax = plt.subplots(figsize=(12, 6), dpi=140)

    # Defensive Vorbereitung der Daten: konvertieren, Inf/NaN entfernen
    vals = pd.to_numeric(gesamt["Anteil Erneuerbare [MWh]"], errors="coerce")
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
        ax.set_title('Anteil der Erneuerbaren Energien am Stromverbrauch der Jahre 2020-2025')
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


def plot_ee_anteil_histogram_overflow(gesamt):
    """
    Erstellt ein Histogramm des Anteils der Erneuerbaren Energien am Stromverbrauch
    und fasst alle Werte >= 100% in einem einzigen Balken zusammen.

    Args:
        gesamt (pd.DataFrame): DataFrame mit der Spalte "Anteil Erneuerbare [MWh]"
    """

    plt.style.use('_mpl-gallery')

    # größere Figur und höhere DPI für bessere Lesbarkeit
    fig, ax = plt.subplots(figsize=(12, 6), dpi=140)

    # Defensive Vorbereitung der Daten: konvertieren, Inf/NaN entfernen
    vals = pd.to_numeric(gesamt["Anteil Erneuerbare [MWh]"], errors="coerce")
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
    ax.set_title('Anteil der Erneuerbaren Energien am Stromverbrauch der Jahre 2020-2025')
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
    plt.show()