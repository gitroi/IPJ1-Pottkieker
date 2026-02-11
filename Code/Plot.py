"""
Programmiert von Joris Bürger
"""

import pandas as pd
import matplotlib.pyplot as plt
from config import PROJECT_ROOT

# ==============================
# Code zum darstellen der EE erzeugung aus den verschiedenen Quellen pro monat in einem Jahr für die Jahre 2020 bis 2024
# ==============================

def plot_ee_erzeugung_jaehrlich():
    """
    Erstellt ein Liniendiagramm der jährlichen Erneuerbaren Energieerzeugung
    aus verschiedenen Quellen für die Jahre 2020 bis 2024.
    Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
    """
    # Pfad zur CSV-Datei mit Erzeugungsdaten
    erzeugungpfad = PROJECT_ROOT / "Daten" / "Ist_Analyse" / "Erzeugung.csv"
    erzeugungpfad2 = PROJECT_ROOT / "Daten" / "SMARD-Daten" / "erzeugung_2019.csv"
    
    # Lese die CSV-Datei ein
    erzeugung_df = pd.read_csv(erzeugungpfad2, sep=";", dtype=str)
    erzeugung2_df = pd.read_csv(erzeugungpfad, sep=";", dtype=str) 

    for col in erzeugung_df.columns:
        if "MWh" in col:
            erzeugung_df[col] = pd.to_numeric(
                erzeugung_df[col].astype(str)
                .str.replace("-", "0", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False),
                errors='coerce'
            ).fillna(0)

    for col in erzeugung2_df.columns:
        if "MWh" in col:
            erzeugung2_df[col] = pd.to_numeric(
                erzeugung2_df[col].astype(str)
                .str.replace("-", "0", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False),
                errors='coerce'
            ).fillna(0)

    # Konvertiere 'Datum von' in datetime-Format
    erzeugung_df["Datum von"] = pd.to_datetime(erzeugung_df["Datum von"], format="%d.%m.%Y %H:%M")
    erzeugung2_df["Datum von"] = pd.to_datetime(erzeugung2_df["Datum von"], format="%d.%m.%Y %H:%M")
    erzeugung_df = pd.concat([erzeugung2_df, erzeugung_df], ignore_index=True)

    # Filtere Daten für die Jahre 2020 bis 2024
    erzeugung_df = erzeugung_df[(erzeugung_df["Datum von"].dt.year <= 2024)]

    # Setze 'Datum von' als Index
    erzeugung_df.set_index("Datum von", inplace=True)

    # Resample auf jährliche Summe
    jaehrliche_erzeugung = erzeugung_df.resample("YE").sum()

    # Erstelle das Liniendiagramm
    plt.figure(figsize=(14, 6))
    plt.plot(jaehrliche_erzeugung.index, jaehrliche_erzeugung["Photovoltaik [MWh] Originalauflösungen"], label="Photovoltaik", marker='o')
    plt.plot(jaehrliche_erzeugung.index, jaehrliche_erzeugung["Wind Onshore [MWh] Originalauflösungen"], label="Wind Onshore", marker='o')
    plt.plot(jaehrliche_erzeugung.index, jaehrliche_erzeugung["Wind Offshore [MWh] Originalauflösungen"], label="Wind Offshore", marker='o')
    plt.plot(jaehrliche_erzeugung.index, jaehrliche_erzeugung["Biomasse [MWh] Originalauflösungen"], label="Biomasse", marker='o')
    plt.plot(jaehrliche_erzeugung.index, jaehrliche_erzeugung["Wasserkraft [MWh] Originalauflösungen"], label="Wasserkraft", marker='o')
    plt.plot(jaehrliche_erzeugung.index, jaehrliche_erzeugung["Sonstige Erneuerbare [MWh] Originalauflösungen"], label="Sonstige Erneuerbare", marker='o')
    plt.title("Jährliche Erneuerbare Energieerzeugung (2020-2024)")
    plt.xlabel("Jahr")
    plt.ylabel("Energieerzeugung [MWh]")
    plt.legend()
    plt.grid()
    plt.show()

def plot_verbrauch(gesamt:pd.DataFrame):
    """
    Erstellt ein Liniendiagramm des Gesamtenergieverbrauchs.
    Ünterstützt durch KI (GPT-4.1 Inline Suggestions)
    """
    gesamt = gesamt.resample('ME').sum()
    plt.figure(figsize=(14, 6))
    plt.plot(gesamt.index, gesamt["Netzlast [MWh]"], label="Gesamtverbrauch", color='orange', marker='o')
    plt.title("Gesamtenergieverbrauch")
    plt.xlabel("Datum")
    plt.ylabel("Energieverbrauch [MWh]")
    plt.legend()
    plt.grid()
    plt.show()

def plot_verbrauch_woche(gesamt: pd.DataFrame, start_datum=None):
    """
    Erstellt ein Liniendiagramm des Energieverbrauchs in Stundenauflösung für eine Woche.
    
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
        # Wenn der Index timezone-aware ist, muss auch start timezone-aware sein
        if gesamt.index.tz is not None:
            if start.tz is None:
                start = start.tz_localize(gesamt.index.tz)
    
    ende = start + pd.Timedelta(days=7)
    
    woche_df = gesamt[(gesamt.index >= start) & (gesamt.index < ende)]
    
    if woche_df.empty:
        print(f"Keine Daten für den Zeitraum {start} bis {ende} gefunden")
        return
    
    woche_df = woche_df.resample('h').sum()
    
    plt.figure(figsize=(16, 6))
    plt.plot(woche_df.index, woche_df["Netzlast [MWh]"], label="Verbrauch", color='orange', marker='o', markersize=3)
    plt.title(f"Energieverbrauch in Stundenauflösung ({start.strftime('%d.%m.%Y')} - {ende.strftime('%d.%m.%Y')})")
    plt.xlabel("Datum und Uhrzeit")
    plt.ylabel("Energieverbrauch [MWh]")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()