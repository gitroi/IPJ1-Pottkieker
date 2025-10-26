import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==============================
# Pfad zu den CSV-Dateien
# C:\Users\joris\Documents\IPJ1\Daten\Verbrauch.csv
# C:\Users\joris\Documents\IPJ1\Daten\Erzeugung.csv
# ==============================   

pfaderzeugung = "C:\\Users\\joris\\Documents\\IPJ1\\Daten\\Erzeugung.csv"
pfadverbrauch = "C:\\Users\\joris\\Documents\\IPJ1\\Daten\\Verbrauch.csv"

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
    verbrauch[["Datum von", "Netzlast [MWh] Originalauflösungen",
        "Netzlast inkl. Pumpspeicher [MWh] Originalauflösungen"]],
    on="Datum von",
    how="inner",
)

# sichere Division: ersetze 0 durch np.nan vor Division
den = gesamt["Netzlast inkl. Pumpspeicher [MWh] Originalauflösungen"].replace(0, np.nan)
gesamt["Anteil Erneuerbare [MWh]"] = (gesamt["Erneuerbare [MWh]"] / den * 100).round(2)

# ==============================
# 6. Ergebnisse in eine Excel-Datei speichern
# ==============================
# gesamt.to_excel(
#    "C:\\Users\\joris\\Documents\\IPJ1\\Daten\\Analyse_Erneuerbare_Anteil.xlsx",
#   index=False,
# )

# ==============================
# 7. Visualisierung: Anteil Erneuerbare Energien über die Jahre
# ==============================

# erstellen der Bins für das Histogram mit den Abständen von 0 bis 100 in 10 Schritten
bins = np.linspace(0, 100, 11)

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

    # Optional: x-Lim auf sinnvollen Bereich setzen (0-100% für prozentuale Anteile)
    ax.set_xlim(0, 100)

    # Y-Achse in Tausender-Einheiten formatieren (z.B. 5,10,15 statt 5000,10000,15000)
    from matplotlib.ticker import MultipleLocator, FuncFormatter
    import math

    max_count = int(max(n)) if len(n) > 0 else 0
    # Ziel: ca. 6 Ticks => Schritt in Tausendern bestimmen
    approx_ticks = 6
    step_thousands = max(1, math.ceil((max_count / 1000) / approx_ticks))
    step = step_thousands * 1000

    ax.yaxis.set_major_locator(MultipleLocator(step))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x/1000)}"))
    ax.set_ylabel('Anzahl (in 1.000)')

    # verhindert, dass Labels vom Fensterrand oder Menüs überdeckt werden
    plt.tight_layout()
    
plt.show()

# ==============================
# 8. Anzahl der Viertelstunden mit EE-Anteil von 100%
# ==============================

anzahl = (gesamt["Anteil Erneuerbare [MWh]"] >= 100).sum()
print(f"Anzahl der Viertelstunden mit einem EE-Anteil von 100%: {anzahl}")