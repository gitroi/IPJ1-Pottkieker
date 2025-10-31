import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
def Prognose_Verbrauch(verbrauch_2030_MWh , verbrauch_2045_MWh):
    
    #==== Einlesen der Daten und anpassung ====
    verbrauchpfad = "C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\Ist_Analyse\\verbrauch.csv"

    verbrauch_df = pd.read_csv(verbrauchpfad,
    sep=';', decimal=',', parse_dates=['Datum von'],
    dayfirst=True, low_memory=False
    )

    verbrauch_df["Datum von"] = pd.to_datetime(verbrauch_df["Datum von"], format="%d.%m.%Y %H:%M")

    verbrauch_df = verbrauch_df[["Datum von", "Netzlast [MWh] Originalauflösungen"]]\
    .rename(columns={"Netzlast [MWh] Originalauflösungen": "Netzlast [MWh]"})

    verbrauch_df["Netzlast [MWh]"] = pd.to_numeric(
    verbrauch_df["Netzlast [MWh]"].astype(str)
    .str.replace('.', '',regex=False)
    .str.replace(',', '.',regex=False),
    errors='coerce'
    )

    verbrauch_df["Jahr"]= verbrauch_df["Datum von"].dt.year
    verbrauch_df["Monat"]= verbrauch_df["Datum von"].dt.month
    verbrauch_df["Wochentag"] = verbrauch_df["Datum von"].dt.weekday
    verbrauch_df["Uhrzeit"] = verbrauch_df["Datum von"].dt.hour
    verbrauch_df["Minute"] = verbrauch_df["Datum von"].dt.minute

    #=== Gesamtverbrauch 2025 aus bestehenden Messungen berechnen ===

    gesamtverbrauch_2025_messungen = verbrauch_df[verbrauch_df["Jahr"] == 2025]["Netzlast [MWh]"].sum()

    #=== Anzahl viertelstündliche Messungen 2025 ===

    anzahl_messungen_2025 = verbrauch_df[verbrauch_df["Jahr"] == 2025].shape[0] #shape gibt (Anzahl Zeilen, Anzahl Spalten) zurück 0 für Zeilen 1 für Spalten

    #=== Messungen für 2025 auf ganzes Jahr hochrechen ===

    gesamtverbrauch_2025 = gesamtverbrauch_2025_messungen * (365*24*4)/anzahl_messungen_2025
    gesamtverbrauch_2025 = gesamtverbrauch_2025.round(2)

    #=== Wachstumsrate bis 2030 berechnen ===

    #ziel = start * (1+ r) ** n  => r = (ziel/start)^(1/n) -1

    wachstumsrate_2030 = ((verbrauch_2030_MWh/gesamtverbrauch_2025)**(1/5)) - 1

    #=== Daten gruppieren ===

    profiel = (verbrauch_df.
    groupby(["Monat", "Wochentag", "Uhrzeit", "Minute"],as_index=False)
    ["Netzlast [MWh]"].mean().rename(columns={"Netzlast [MWh]": "Profilmittel [MWh]"})
    )

    date_range = pd.date_range(start='2026-01-01 00:00', end='2030-12-31 23:45', freq='15min')
    df_gesamt = pd.DataFrame({"Datum von": date_range})

    df_gesamt["Jahr"]= df_gesamt["Datum von"].dt.year
    df_gesamt["Monat"]= df_gesamt["Datum von"].dt.month
    df_gesamt["Wochentag"] = df_gesamt["Datum von"].dt.weekday
    df_gesamt["Uhrzeit"] = df_gesamt["Datum von"].dt.hour
    df_gesamt["Minute"] = df_gesamt["Datum von"].dt.minute

    df_gesamt = df_gesamt.merge(profiel, on=["Monat", "Wochentag", "Uhrzeit", "Minute"
        ], how='left'
    )

    #=== Verbrauchsprognose berechnen ===

    df_gesamt["Netzlast_Prognose [MWh]"] = (
        df_gesamt["Profilmittel [MWh]"]
        * (1 + wachstumsrate_2030) ** (df_gesamt["Jahr"] - 2025)  # ** notation für potenzieren
    )

    df_gesamt["Netzlast_Prognose [MWh]"] = df_gesamt["Netzlast_Prognose [MWh]"].round(2)

    #=== Erweitern bis 2045 ===

    date_range_2045 = pd.date_range(start='2031-01-01 00:00', end='2046-12-31 23:45', freq='15min')
    df_2045 = pd.DataFrame({"Datum von": date_range_2045})

    df_2045["Jahr"]= df_2045["Datum von"].dt.year
    df_2045["Monat"]= df_2045["Datum von"].dt.month
    df_2045["Wochentag"] = df_2045["Datum von"].dt.weekday
    df_2045["Uhrzeit"] = df_2045["Datum von"].dt.hour
    df_2045["Minute"] = df_2045["Datum von"].dt.minute

    #===  wachstumsfaktor für 2031 bis 2045 berechnen ===

   
    gesamtverbrauch_2030_berechnet = df_gesamt[df_gesamt["Jahr"] == 2030]["Netzlast_Prognose [MWh]"].sum()

    wachstumsrate_2045 = (verbrauch_2045_MWh/gesamtverbrauch_2030_berechnet) **(1/15) - 1

    basisprofil_2030 = df_gesamt[df_gesamt["Jahr"] == 2030][["Datum von","Jahr","Monat","Wochentag","Uhrzeit","Minute" ,"Netzlast_Prognose [MWh]"]].copy().reset_index(drop=True)

    profiel_2030 = (basisprofil_2030.
                    groupby(["Monat", "Wochentag", "Uhrzeit", "Minute"],as_index=False)
                    ["Netzlast_Prognose [MWh]"].mean().rename(columns={"Netzlast_Prognose [MWh]": "Profilmittel [MWh]"})
    )

    prognose_2045 = df_2045.merge(profiel_2030, on=["Monat", "Wochentag", "Uhrzeit", "Minute"
        ], how='left'
    )

    prognose_2045["Netzlast_Prognose [MWh]"] = (
        prognose_2045["Profilmittel [MWh]"]
        * (1 + wachstumsrate_2045) ** (prognose_2045["Jahr"] - 2030)
    )

    prognose_2045["Netzlast_Prognose [MWh]"] = prognose_2045["Netzlast_Prognose [MWh]"].round(2)

    df_gesamt_2045 = pd.concat([df_gesamt, prognose_2045], ignore_index=True)
    df_gesamt_2045 = df_gesamt_2045.rename(columns={"Netzlast_Prognose [MWh]": "Netzlast [MWh] Originalauflösungen"})
    
    #speichern
    df_prognose_export = df_gesamt_2045[["Datum von", "Netzlast [MWh] Originalauflösungen"]]
    df_prognose_export.to_csv('C:\\Users\\joris\\OneDrive - HAW-HH\\Labore\\Integrationsprojekt1\\IPJ1-Pottkieker\\Daten\\verbrauch_prognose_2045.csv', index=False, sep=';', decimal=',')

    return df_gesamt_2045



#=== Juni 2045 Beispielplot ===

prognose = Prognose_Verbrauch(650e6, 1200e6)
juni_2045 = prognose[(prognose["Datum von"] >= "2045-06-01") & (prognose["Datum von"] < "2045-06-08")]

plt.figure(figsize=(12,5))
plt.plot(juni_2045["Datum von"], juni_2045["Netzlast [MWh] Originalauflösungen"], lw=0.7)
plt.title("Beispiel: Stromverbrauch Prognose Juni 2045")
plt.xlabel("Datum")
plt.ylabel("MWh")
plt.grid(True)
plt.tight_layout()
plt.show()

#=== Darstellung in TWh in Balkendiagramm für Jahressummen===

df_jahressummen_2045 = prognose.groupby("Jahr", as_index=False)["Netzlast [MWh] Originalauflösungen"].sum()
df_jahressummen_2045["Netzlast [MWh] Originalauflösungen"] = df_jahressummen_2045["Netzlast [MWh] Originalauflösungen"] / 1000000

plt.figure(figsize=(10,5))
plt.bar(df_jahressummen_2045["Jahr"], df_jahressummen_2045["Netzlast [MWh] Originalauflösungen"], color='skyblue')
plt.title("Jährliche Stromverbrauchsprognose (2026-2045)") 
plt.xlabel("Jahr")
plt.ylabel("Netzlast Prognose [TWh]")
plt.grid(axis='y')
plt.tight_layout()
plt.show()

jan_woche = prognose[(prognose["Datum von"] >= "2026-10-14") & (prognose["Datum von"] < "2026-10-21")]

plt.figure(figsize=(12,5))
plt.plot(jan_woche["Datum von"], jan_woche["Netzlast [MWh] Originalauflösungen"], lw=0.7)
plt.title("Beispiel: Stromverbrauch Prognose Oktober 2026")
plt.xlabel("Datum")
plt.ylabel("MWh")
plt.grid(True)
plt.tight_layout()
plt.show()