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
    """
    # Pfad zur CSV-Datei mit Erzeugungsdaten
    erzeugungpfad = PROJECT_ROOT / "Daten" / "Ist_Analyse" / "erzeugung.csv"
    erzeugungpfad2 = PROJECT_ROOT / "Daten" / "erzeugung_2019.csv"
    
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

plot_ee_erzeugung_jaehrlich()