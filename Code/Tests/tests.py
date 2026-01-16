"""
Tests für die Softwaremodule.
Erstellt durch Joris Bürger mit Hilfe von inline GitHub Copilot.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
import pandas as pd
from Klassen import Szenario


class TestSzenarioDatenerstellung(unittest.TestCase):
    
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
                "pv_dach": 50.0,
                "pv_frei": 30.0,
                "wind_onshore": 60.0,
                "wind_offshore": 15.0,
                "biomasse": 8.0,
                "wasser": 4.0,
                "sonstige": 0.1
            },
            "Ausbau Speicher": {
                "batteriespeicher": 100.0,
                "wasserstoff": 50.0,
                "pumpspeicher": 30.0
            }
        }
        
        cls.ziele_2045 = {
            "Ausbau EE": {
                "pv_dach": 150.0,
                "pv_frei": 90.0,
                "wind_onshore": 120.0,
                "wind_offshore": 40.0,
                "biomasse": 10.0,
                "wasser": 5.0,
                "sonstige": 0.1
            },
            "Ausbau Speicher": {
                "batteriespeicher": 500.0,
                "wasserstoff": 300.0,
                "pumpspeicher": 100.0
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

    def tearDown(self):
        """Cleanup nach jedem Test"""
        self.szenario = None

if __name__ == '__main__':
    unittest.main()