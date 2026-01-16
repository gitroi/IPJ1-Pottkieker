"""
Tested die Simulation bei Extremwerten der Eingabedaten.
Erstellt durch Joris Bürger mit hilfe von inline GitHub Copilot.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest 
import pandas as pd
from Klassen import Szenario


class TestExtremwerteSzenario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Erstelle ein vollständiges Test-Szenario einmal für alle Tests"""
        
        cls.veränderungsfaktoren = {
            "Erzeugung": {
                "pv_dach": 1.0,
                "pv_frei": 1.0,
                "wind_onshore": 1.0,
                "wind_offshore": 1.0,
                "biomasse": 1.0,
                "wasser": 1.0,
                "sonstige": 1.0
            },
            "Capex_EE": {
                "pv_dach": 1.0,
                "pv_frei": 1.0,
                "wind_onshore": 1.0,
                "wind_offshore": 1.0,
                "biomasse": 1.0,
                "wasser": 1.0,
                "sonstige": 1.0
            },
            "Opex_EE": {
                "pv_dach": 1.0,
                "pv_frei": 1.0,
                "wind_onshore": 1.0,
                "wind_offshore": 1.0,
                "biomasse": 1.0,
                "wasser": 1.0,
                "sonstige": 1.0
            },
            "Capex_Speicher": {
                "batteriespeicher": 1.0,
                "wasserstoff": 1.0,
                "pumpspeicher": 1.0
            },
            "Opex_Speicher": {
                "batteriespeicher": 1.0,
                "wasserstoff": 1.0,
                "pumpspeicher": 1.0
            }
        }
        
        cls.ziele_2030 = {
            "Ausbau EE": {
                "pv_dach": 0.0,
                "pv_frei": 0.0,
                "wind_onshore": 0.0,
                "wind_offshore": 0.0,
                "biomasse": 0.0,
                "wasser": 0.0,
                "sonstige": 0.0
            },
            "Ausbau Speicher": {
                "batteriespeicher": 0.0,
                "wasserstoff": 0.0,
                "pumpspeicher": 0.0
            }
        }
        
        cls.ziele_2045 = {
            "Ausbau EE": {
                "pv_dach": 0.0,
                "pv_frei": 0.0,
                "wind_onshore": 0.0,
                "wind_offshore": 0.0,
                "biomasse": 0.0,
                "wasser": 0.0,
                "sonstige": 0.0
            },
            "Ausbau Speicher": {
                "batteriespeicher": 0.0,
                "wasserstoff": 0.0,
                "pumpspeicher": 0.0
            }
        }
        
        cls.konven_anteile = {
            "2038": {
                "braun": 0.25,
                "erdgas": 0.4,
                "stein": 0.15,
                "sonstige": 0.1,
                "importe": 0.1
            },
            "2045": {
                "braun": 0.0,
                "erdgas": 0.6,
                "stein": 0.0,
                "sonstige": 0.2,
                "importe": 0.2
            }
        }

        cls.verbrauchsprofile = {
            "Name": "Test-Profil",
            "Verbrauch_2030": 600,
            "Verbrauch_2045": 900,
            "E_Autos_2030": 10000000,
            "E_Autos_2045": 30000000,
            "WP_2030": 5000000,
            "WP_2045": 10000000
        }
        
        cls.szenario_dict = {
            "Name": "Unit Test Szenario",
            "Beschreibung": "Minimales Test-Szenario",
            "Ziele 2030": cls.ziele_2030,
            "Ziele 2045": cls.ziele_2045,
            "Veränderungsfaktoren": cls.veränderungsfaktoren,
            "Konventionelle Anteile": cls.konven_anteile
        }
        
        cls.szenario = Szenario(
            name="Unit Test",
            beschreibung="Test-Szenario für Unit Tests",
            szenario=cls.szenario_dict,
            ziele_2030=cls.ziele_2030,
            ziele_2045=cls.ziele_2045,
            ertragsart="mittel",
            verbrauchsprofile=cls.verbrauchsprofile,
            veränderungsfaktoren=cls.veränderungsfaktoren["Erzeugung"], 
            konven_anteile=cls.konven_anteile,
            lastprofile=False
        )
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup nach allen Tests"""
        cls.szenario = None
    
    def test_szenario_erstellt(self):
        """Prüft ob das Szenario erfolgreich erstellt wurde"""
        self.assertIsNotNone(self.szenario)
        self.assertEqual(self.szenario.name, "Unit Test")
    
    def test_erzeugung_df_erstellt(self):
        """Prüft ob das Erzeugungs-DataFrame erstellt wurde"""
        self.assertIsNotNone(self.szenario.erzeugung_df)
        self.assertIsInstance(self.szenario.erzeugung_df, pd.DataFrame)
        self.assertGreater(len(self.szenario.erzeugung_df), 0)
    
    def test_verbrauch_df_erstellt(self):
        """Prüft ob das Verbrauchs-DataFrame erstellt wurde"""
        self.assertIsNotNone(self.szenario.verbrauch_df)
        self.assertIsInstance(self.szenario.verbrauch_df, pd.DataFrame , self.szenario.erzeugung_df.columns)
        self.assertIn('Datum von', self.szenario.verbrauch_df.columns)
    
    def test_kostenrechnung_durchgeführt(self):
        """Prüft ob die Kostenrechnung durchgeführt wurde"""
        self.assertIsNotNone(self.szenario.kosten_df)
        self.assertIn('Gesamtkosten_EE_und_Speicher [€]', self.szenario.kosten_df.columns)
        self.assertGreater(self.szenario.kosten_df['Gesamtkosten_EE_und_Speicher [€]'].iloc[0], 0)

    def test_nan_werte_in_erzeugung(self):
        """Prüft ob das Erzeugungs-DataFrame keine NaN-Werte enthält"""
        self.assertFalse(self.szenario.erzeugung_df.isnull().values.any(), "NaN-Werte im Erzeugungs-DataFrame gefunden")

    def test_nan_werte_in_verbrauch(self):
        """Prüft ob das Verbrauchs-DataFrame keine NaN-Werte enthält"""
        self.assertFalse(self.szenario.verbrauch_df.isnull().values.any(), "NaN-Werte im Verbrauchs-DataFrame gefunden")

    def test_nan_werte_in_kosten(self):
        """Prüft ob die Kostenrechnung keine NaN-Werte enthält"""
        for key, value in self.szenario.kosten_df.items():
            self.assertIsNotNone(value, f"NaN-Wert in den Kosten für {key} gefunden")

    def test_nan_werte_in_gesamt(self):
        """Prüft ob das Gesamtdaten-DataFrame keine NaN-Werte enthält"""
        self.assertFalse(self.szenario.gesamt_df.isnull().values.any(), "NaN-Werte im Gesamtdaten-DataFrame gefunden")

    def test_erzeugung_ab_2030_null(self):
        """Prüft ob die Erzeugung ab 2030 korrekt auf Null gesetzt wurde"""
        erzeugung_ab_2030 = self.szenario.erzeugung_df[self.szenario.erzeugung_df['Datum von'].dt.year > 2030]
        self.assertTrue((erzeugung_ab_2030.drop(columns=['Datum von']) == 0).all().all(), "Erzeugungswerte ab 2030 sind nicht alle Null")

    def test_energie_aus_speichern_ab_2031_null(self):
        """Prüft ob die Energie aus Speichern ab 2031 null ist"""
        daten_df = self.szenario.auswertungsdaten_generieren()
        daten_df = daten_df[daten_df['Jahr'] > 2030]
        self.assertTrue((daten_df["Energie aus Speichern [TWh]"] == 0).all(), "Energie aus Speichern ab 2031 ist nicht 0")

    def test_erzeugung_erneuerbare_ab_2031_null(self):
        """Prüft ob die Erzeugung Erneuerbare ab 2031 null ist"""
        daten_df = self.szenario.auswertungsdaten_generieren()
        daten_df = daten_df[daten_df['Jahr'] > 2030]
        self.assertTrue((daten_df["Erzeugung Erneuerbare im Jahr [TWh]"] == 0).all(), "Erzeugung Erneuerbare ab 2031 ist nicht 0")

    def test_ee_anteil_ohne_speicher_ab_2031_null(self):
        """Prüft ob der EE Anteil ohne Speicher ab 2031 null ist"""
        daten_df = self.szenario.auswertungsdaten_generieren()
        daten_df = daten_df[daten_df['Jahr'] > 2030]
        self.assertTrue((daten_df["EE Anteil am Stromverbrauch ohne Speicher [%]"] == 0).all(), "EE Anteil ohne Speicher ab 2031 ist nicht 0")

    def test_ee_anteil_mit_speicher_ab_2031_null(self):
        """Prüft ob der EE Anteil mit Speicher ab 2031 null ist"""
        daten_df = self.szenario.auswertungsdaten_generieren()
        daten_df = daten_df[daten_df['Jahr'] > 2030]
        self.assertTrue((daten_df["EE Anteil am Stromverbrauch mit Speicher [%]"] == 0).all(), "EE Anteil mit Speicher ab 2031 ist nicht 0")

    def test_nicht_genutzte_ee_ab_2031_null(self):
        """Prüft ob die nicht genutzte EE Energie ab 2031 null ist"""
        daten_df = self.szenario.auswertungsdaten_generieren()
        daten_df = daten_df[daten_df['Jahr'] > 2030]
        self.assertTrue((daten_df["Nicht genutzte Erneuerbare Energie im Jahr [TWh]"] == 0).all(), "Nicht genutzte EE Energie ab 2031 ist nicht 0")

    def test_gesamtkosten_ee_ab_2031_null(self):
        """Prüft ob die Gesamtkosten EE ab 2031 null sind"""
        daten_df = self.szenario.auswertungsdaten_generieren()
        daten_df = daten_df[daten_df['Jahr'] > 2030]
        self.assertTrue((daten_df["Gesamtkosten_EE [Mrd. €]"] == 0).all(), "Gesamtkosten EE ab 2031 sind nicht 0")

    def tearDown(self):
        """Cleanup nach jedem Test"""
        self.szenario = None

if __name__ == '__main__':
    unittest.main()