import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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

#feb_Woche = verbrauch_df[(verbrauch_df["Datum von"] >= "2024-10-14") & (verbrauch_df["Datum von"] < "2024-10-21")]

# plt.figure(figsize=(12,5))
# plt.plot(feb_Woche["Datum von"], feb_Woche["Netzlast [MWh]"], lw=0.7)
# plt.title("Beispiel: Stromverbrauch Prognose Oktober 2024")
# plt.xlabel("Datum")
# plt.ylabel("MWh")
# plt.grid(True)
# plt.tight_layout()
# plt.show()

verbrauch_df["Jahr"]= verbrauch_df["Datum von"].dt.year
verbrauch_df["Monat"]= verbrauch_df["Datum von"].dt.month
verbrauch_df["Wochentag"] = verbrauch_df["Datum von"].dt.weekday
verbrauch_df["Uhrzeit"] = verbrauch_df["Datum von"].dt.hour
verbrauch_df["Minute"] = verbrauch_df["Datum von"].dt.minute

#print(verbrauch_df.head(8))

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

wachstumsrate_2030 = 0.069  # 6.9% jährliches Wachstum

df_gesamt["Netzlast_Prognose [MWh]"] = (
    df_gesamt["Profilmittel [MWh]"]
    * (1 + wachstumsrate_2030) ** (df_gesamt["Jahr"] - 2025)  # ** Exponentiation
)

df_gesamt["Netzlast_Prognose [MWh]"] = df_gesamt["Netzlast_Prognose [MWh]"].round(2)

jan_woche = df_gesamt[(df_gesamt["Datum von"] >= "2026-10-14") & (df_gesamt["Datum von"] < "2026-10-21")]

plt.figure(figsize=(12,5))
plt.plot(jan_woche["Datum von"], jan_woche["Netzlast_Prognose [MWh]"], lw=0.7)
plt.title("Beispiel: Stromverbrauch Prognose Oktober 2026")
plt.xlabel("Datum")
plt.ylabel("MWh")
plt.grid(True)
plt.tight_layout()
plt.show()

#=== Jahressummen bilden ===

df_jahressummen = df_gesamt.groupby("Jahr", as_index=False)["Netzlast_Prognose [MWh]"].sum()

#Darstellen in GWh als Balkendiagramm

plt.figure(figsize=(10,5))
plt.bar(df_jahressummen["Jahr"], df_jahressummen["Netzlast_Prognose [MWh]"]/1000000, color='skyblue')
plt.title("Jährliche Stromverbrauchsprognose (2026-2045)") 
plt.xlabel("Jahr")
plt.ylabel("Netzlast Prognose [TWh]")
plt.grid(axis='y')
plt.tight_layout()
plt.show()

#df_Netzlast_Prognose = df_gesamt[["Datum von", "Netzlast_Prognose [MWh]"]]

#df_Netzlast_Prognose.to_csv('Verbrauchsprognose_2026_2030.csv', index=False, sep=';', decimal=',')

#=== Erweitern bis 2045 ===

date_range_2045 = pd.date_range(start='2031-01-01 00:00', end='2046-12-31 23:45', freq='15min')
df_2045 = pd.DataFrame({"Datum von": date_range_2045})

df_2045["Jahr"]= df_2045["Datum von"].dt.year
df_2045["Monat"]= df_2045["Datum von"].dt.month
df_2045["Wochentag"] = df_2045["Datum von"].dt.weekday
df_2045["Uhrzeit"] = df_2045["Datum von"].dt.hour
df_2045["Minute"] = df_2045["Datum von"].dt.minute

df_gesamt_2045 = pd.concat([df_gesamt, df_2045], ignore_index=True)

wachstumsrate_2045 = 0.049  # 4.9% jährliches Wachstum ab 2031

# Berechne Wachstumsfaktoren für jedes Jahr nach 2030
jahre_nach_2030 = df_gesamt_2045["Jahr"] - 2030
wachstumsfaktor = (1 + wachstumsrate_2045) ** jahre_nach_2030

basisprofil_2030 = df_gesamt_2045[df_gesamt_2045["Jahr"] == 2030].copy()

for jahr in range(2031, 2046):
    faktor = (1 + wachstumsrate_2045) ** (jahr - 2030)
    df_gesamt_2045.loc[df_gesamt_2045["Jahr"] == jahr, "Netzlast_Prognose [MWh]"] = (
        basisprofil_2030["Netzlast_Prognose [MWh]"].values * faktor
)


df_gesamt_2045["Netzlast_Prognose [MWh]"] = df_gesamt_2045["Netzlast_Prognose [MWh]"].round(2)

df_prognose_2045 = df_gesamt_2045[["Datum von", "Netzlast_Prognose [MWh]"]]

#=== Darstellung in TWh in Balkendiagramm für Jahressummen===

df_jahressummen_2045 = df_gesamt_2045.groupby("Jahr", as_index=False)["Netzlast_Prognose [MWh]"].sum()
df_jahressummen_2045["Netzlast_Prognose [TWh]"] = df_jahressummen_2045["Netzlast_Prognose [MWh]"] / 1000000

plt.figure(figsize=(10,5))
plt.bar(df_jahressummen_2045["Jahr"], df_jahressummen_2045["Netzlast_Prognose [TWh]"], color='skyblue')
plt.title("Jährliche Stromverbrauchsprognose (2026-2045)") 
plt.xlabel("Jahr")
plt.ylabel("Netzlast Prognose [TWh]")
plt.grid(axis='y')
plt.tight_layout()
plt.show()

prognose = df_gesamt_2045[["Datum von", "Netzlast_Prognose [MWh]"]]
prognose.to_csv('Verbrauchsprognose_2026_2045.csv', index=False, sep=';', decimal=',')

#=== Juni Woche 2045 darstellen ===

# juni_woche = df_gesamt[(df_gesamt["Datum von"] >= "2045-06-10") & (df_gesamt["Datum von"] < "2045-06-17")]

# plt.figure(figsize=(12,5))
# plt.plot(juni_woche["Datum von"], juni_woche["Netzlast_Prognose [MWh]"], lw=0.7)
# plt.title("Beispiel: Stromverbrauch Prognose Juni 2045")
# plt.xlabel("Datum")
# plt.ylabel("MWh")
# plt.grid(True)
# plt.tight_layout()
# plt.show()
