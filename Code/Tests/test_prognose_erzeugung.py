"""
Unit Tests für Prognose_Erzeugung.py
Testet die Funktionen zur Erzeugungsprognose von Erneuerbaren Energien.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import json
from unittest.mock import patch, mock_open
from Prognose_Erzeugung import Jährlicher_Zuwachs_EE, Prognose_erzeugung


class TestJährlicher_Zuwachs_EE:
    """Tests für die Funktion Jährlicher_Zuwachs_EE"""
    
    @pytest.fixture
    def mock_erzeugerarten(self):
        """Mock-Daten für erzeugerarten.json"""
        return {
            "pv_dach": {"bestand": 50.0},
            "pv_frei": {"bestand": 30.0},
            "wind_onshore": {"bestand": 60.0},
            "wind_offshore": {"bestand": 10.0},
            "biomasse": {"bestand": 8.0},
            "wasser": {"bestand": 5.0},
            "sonstige": {"bestand": 2.0}
        }
    
    @pytest.fixture
    def zielwert_2030(self):
        """Beispiel-Zielwerte für 2030"""
        return {
            "pv_dach": 100.0,
            "pv_frei": 80.0,
            "wind_onshore": 115.0,
            "wind_offshore": 30.0,
            "biomasse": 10.0,
            "wasser": 6.0,
            "sonstige": 3.0
        }
    
    @pytest.fixture
    def zielwert_2045(self):
        """Beispiel-Zielwerte für 2045"""
        return {
            "pv_dach": 150.0,
            "pv_frei": 150.0,
            "wind_onshore": 160.0,
            "wind_offshore": 70.0,
            "biomasse": 12.0,
            "wasser": 7.0,
            "sonstige": 5.0
        }
    
    def test_zuwachs_2030_berechnung(self, zielwert_2030, zielwert_2045, mock_erzeugerarten):
        """Testet die korrekte Berechnung der Zuwachsrate bis 2030"""
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_erzeugerarten))):
            with patch('Prognose_Erzeugung.PROJECT_ROOT', Path('/mock/path')):
                result = Jährlicher_Zuwachs_EE(zielwert_2030, zielwert_2045)
        
        # Prüfe Struktur
        assert "zuwachsrate_2030" in result
        assert "zuwachsrate_2045" in result
        
        # Prüfe PV-Dach: (100 - 50) / 5 = 10 GW/Jahr
        assert result["zuwachsrate_2030"]["pv_dach"] == pytest.approx(10.0, abs=0.01)
        
        # Prüfe Wind Onshore: (115 - 60) / 5 = 11 GW/Jahr
        assert result["zuwachsrate_2030"]["wind_onshore"] == pytest.approx(11.0, abs=0.01)
    
    def test_zuwachs_2045_berechnung(self, zielwert_2030, zielwert_2045, mock_erzeugerarten):
        """Testet die korrekte Berechnung der Zuwachsrate von 2030 bis 2045"""
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_erzeugerarten))):
            with patch('Prognose_Erzeugung.PROJECT_ROOT', Path('/mock/path')):
                result = Jährlicher_Zuwachs_EE(zielwert_2030, zielwert_2045)
        
        # Prüfe PV-Frei: (150 - 80) / 15 = 4.667 GW/Jahr
        assert result["zuwachsrate_2045"]["pv_frei"] == pytest.approx(4.667, abs=0.01)
        
        # Prüfe Wind Offshore: (70 - 30) / 15 = 2.667 GW/Jahr
        assert result["zuwachsrate_2045"]["wind_offshore"] == pytest.approx(2.667, abs=0.01)
    
    def test_alle_energiequellen_vorhanden(self, zielwert_2030, zielwert_2045, mock_erzeugerarten):
        """Testet, ob alle Energiequellen berechnet werden"""
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_erzeugerarten))):
            with patch('Prognose_Erzeugung.PROJECT_ROOT', Path('/mock/path')):
                result = Jährlicher_Zuwachs_EE(zielwert_2030, zielwert_2045)
        
        expected_keys = ["pv_dach", "pv_frei", "wind_onshore", "wind_offshore", 
                        "biomasse", "wasser", "sonstige"]
        
        for key in expected_keys:
            assert key in result["zuwachsrate_2030"]
            assert key in result["zuwachsrate_2045"]


class TestPrognose_erzeugung:
    """Tests für die Hauptfunktion Prognose_erzeugung"""
    
    @pytest.fixture
    def installierte_2030(self):
        """Mock-Daten für installierte Leistung 2030"""
        return {
            "pv_dach": 100.0,
            "pv_frei": 80.0,
            "wind_onshore": 115.0,
            "wind_offshore": 30.0,
            "biomasse": 10.0,
            "wasser": 6.0,
            "sonstige": 3.0
        }
    
    @pytest.fixture
    def installierte_2045(self):
        """Mock-Daten für installierte Leistung 2045"""
        return {
            "pv_dach": 150.0,
            "pv_frei": 150.0,
            "wind_onshore": 160.0,
            "wind_offshore": 70.0,
            "biomasse": 12.0,
            "wasser": 7.0,
            "sonstige": 5.0
        }
    
    @pytest.fixture
    def steigerungsfaktoren(self):
        """Mock-Daten für Steigerungsfaktoren"""
        return {
            "pv_dach": 1.02,
            "pv_frei": 1.02,
            "wind_onshore": 1.015,
            "wind_offshore": 1.015,
            "biomasse": 1.0,
            "wasser": 1.0,
            "sonstige": 1.0
        }
    
    def test_ertragsart_gut(self, installierte_2030, installierte_2045, steigerungsfaktoren):
        """Testet die Funktion mit Ertragsart 'gut' - Integrationstest"""
        # Integrationstest: Nutzt echte Dateien
        result = Prognose_erzeugung(installierte_2030, installierte_2045, 
                                   steigerungsfaktoren, "gut")
        
        # Prüfe, dass ein DataFrame zurückgegeben wird
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'Datum von' in result.columns
    
    def test_ertragsart_mittel(self, installierte_2030, installierte_2045, steigerungsfaktoren):
        """Testet die Funktion mit Ertragsart 'mittel' - Integrationstest"""
        result = Prognose_erzeugung(installierte_2030, installierte_2045, 
                                   steigerungsfaktoren, "mittel")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'Datum von' in result.columns
    
    def test_ertragsart_schlecht(self, installierte_2030, installierte_2045, steigerungsfaktoren):
        """Testet die Funktion mit Ertragsart 'schlecht' - Integrationstest"""
        result = Prognose_erzeugung(installierte_2030, installierte_2045, 
                                   steigerungsfaktoren, "schlecht")
        
        # Prüfe, dass ein DataFrame zurückgegeben wird
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'Datum von' in result.columns
    
    def test_ungueltige_ertragsart(self, installierte_2030, installierte_2045, steigerungsfaktoren):
        """Testet, ob ungültige Ertragsart eine ValueError auslöst"""
        with pytest.raises(ValueError, match="Ungültige Ertragsart"):
            Prognose_erzeugung(installierte_2030, installierte_2045, 
                             steigerungsfaktoren, "ungültig")
    
    def test_ausgabe_struktur(self, installierte_2030, installierte_2045, steigerungsfaktoren):
        """Testet die Struktur der Ausgabe"""
        result = Prognose_erzeugung(installierte_2030, installierte_2045, 
                                   steigerungsfaktoren, "gut")
        
        # Prüfe erforderliche Spalten
        expected_columns = [
            'Datum von',
            'Photovoltaik [MWh] Originalauflösungen',
            'Wind Onshore [MWh] Originalauflösungen',
            'Wind Offshore [MWh] Originalauflösungen',
            'Biomasse [MWh] Originalauflösungen',
            'Wasserkraft [MWh] Originalauflösungen',
            'Sonstige Erneuerbare [MWh] Originalauflösungen',
            'Installierte PV_GW',
            'Installierte Wind_Onshore_GW',
            'Installierte Wind_Offshore_GW',
            'Installierte Biomasse_GW',
            'Installierte Wasser_GW',
            'Installierte Sonstige_GW'
        ]
        
        for col in expected_columns:
            assert col in result.columns, f"Spalte '{col}' fehlt in der Ausgabe"
        
        # Prüfe, dass keine NaN-Werte vorhanden sind
        assert not result.isna().any().any(), "Ausgabe enthält NaN-Werte"
        
        # Prüfe, dass Erzeugungswerte nicht negativ sind
        erzeugung_cols = [col for col in result.columns if '[MWh]' in col]
        for col in erzeugung_cols:
            assert (result[col] >= 0).all(), f"Spalte '{col}' enthält negative Werte"
    
    def test_zeitraum(self, installierte_2030, installierte_2045, steigerungsfaktoren):
        """Testet, ob der korrekte Zeitraum 2026-2045 abgedeckt wird"""
        result = Prognose_erzeugung(installierte_2030, installierte_2045, 
                                   steigerungsfaktoren, "gut")
        
        start_date = result['Datum von'].min()
        end_date = result['Datum von'].max()
        
        assert start_date.year == 2026, f"Startjahr sollte 2026 sein, ist aber {start_date.year}"
        assert end_date.year == 2045, f"Endjahr sollte 2045 sein, ist aber {end_date.year}"
        
        expected_rows = 20 * 365.25 * 96
        assert len(result) == pytest.approx(expected_rows, abs=20), \
            f"DataFrame sollte ca. {expected_rows:.0f} Viertelstundenwerte haben, hat aber {len(result)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
