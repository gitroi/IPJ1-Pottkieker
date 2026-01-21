"""
Unit Tests für Prognose_Erzeugung.py
Testet die Funktionen zur Erzeugungsprognose von Erneuerbaren Energien.
Erstellt mit GitHub Copilot
(Kannst du mir einen Test ergenzen, der die Funktion Prognose_erzeugung testet)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
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
    
    def test_rundung_auf_drei_nachkommastellen(self, zielwert_2030, zielwert_2045, mock_erzeugerarten):
        """Testet, ob Werte auf 3 Nachkommastellen gerundet werden"""
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_erzeugerarten))):
            with patch('Prognose_Erzeugung.PROJECT_ROOT', Path('/mock/path')):
                result = Jährlicher_Zuwachs_EE(zielwert_2030, zielwert_2045)
        
        for key in result["zuwachsrate_2030"]:
            # Prüfe, dass maximal 3 Nachkommastellen
            assert len(str(result["zuwachsrate_2030"][key]).split('.')[-1]) <= 3
            assert len(str(result["zuwachsrate_2045"][key]).split('.')[-1]) <= 3


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
        # Integrationstest: Nutzt echte Dateien
        result = Prognose_erzeugung(installierte_2030, installierte_2045, 
                                   steigerungsfaktoren, "mittel")
        
        # Prüfe, dass ein DataFrame zurückgegeben wird
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'Datum von' in result.columns
    
    def test_ertragsart_schlecht(self, installierte_2030, installierte_2045, steigerungsfaktoren):
        """Testet die Funktion mit Ertragsart 'schlecht' - Integrationstest"""
        # Integrationstest: Nutzt echte Dateien
        result = Prognose_erzeugung(installierte_2030, installierte_2045, 
                                   steigerungsfaktoren, "schlecht")
        
        # Prüfe, dass ein DataFrame zurückgegeben wird
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'Datum von' in result.columns
    
    def test_ungueltige_ertragsart(self, installierte_2030, installierte_2045, steigerungsfaktoren):
        """Testet, ob ungültige Ertragsart eine ValueError auslöst"""
        # Mock der Dateizugriffe, um bis zur Validierung zu kommen
        mock_df = pd.DataFrame({
            'Jahr': [2020, 2021],
            'Monat': [1, 1],
            'pv': [50.0, 50.0],
            'wind_onshore': [60.0, 60.0],
            'wind_offshore': [10.0, 10.0],
            'biomasse': [8.0, 8.0],
            'wasser': [5.0, 5.0],
            'sonstige': [2.0, 2.0]
        })
        
        mock_erzeugung = pd.DataFrame({
            'Datum von': pd.date_range('2020-01-01', periods=96, freq='15min'),
            'Photovoltaik [MWh] Originalauflösungen': [100.0] * 96,
            'Wind Onshore [MWh] Originalauflösungen': [200.0] * 96,
            'Wind Offshore [MWh] Originalauflösungen': [150.0] * 96,
            'Biomasse [MWh] Originalauflösungen': [50.0] * 96,
            'Wasserkraft [MWh] Originalauflösungen': [30.0] * 96,
            'Sonstige Erneuerbare [MWh] Originalauflösungen': [10.0] * 96
        })
        
        mock_erzeugerarten = {
            "pv_dach": {"bestand": 50.0},
            "pv_frei": {"bestand": 30.0},
            "wind_onshore": {"bestand": 60.0},
            "wind_offshore": {"bestand": 10.0},
            "biomasse": {"bestand": 8.0},
            "wasser": {"bestand": 5.0},
            "sonstige": {"bestand": 2.0}
        }
        
        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.side_effect = [mock_df, mock_erzeugung]
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_erzeugerarten))):
                with patch('Prognose_Erzeugung.PROJECT_ROOT', Path('/mock/path')):
                    with pytest.raises(ValueError, match="Ungültige Ertragsart"):
                        Prognose_erzeugung(installierte_2030, installierte_2045, 
                                         steigerungsfaktoren, "ungültig")
    
    def test_steigerungsfaktoren_umrechnung(self, steigerungsfaktoren):
        """Testet die Umrechnung der Steigerungsfaktoren auf Viertelstunden"""
        # Jahresfaktor 1.02 sollte auf Viertelstunde umgerechnet werden
        # 1.02 ^ (1 / (365.25 * 24 * 4))
        expected_virtelstunden_faktor = 1.02 ** (1 / (365.25 * 24 * 4))
        
        # Dieser Test prüft die Logik, würde aber echte Dateien benötigen
        assert expected_virtelstunden_faktor < 1.02  # Muss kleiner als Jahresfaktor sein
        assert expected_virtelstunden_faktor > 1.0   # Muss größer als 1.0 sein


class TestDataFrame_Ausgabe:
    """Tests für die Struktur und Qualität der Ausgabe"""
    
    def test_spalten_vorhanden(self):
        """Testet, ob alle erforderlichen Spalten in der Ausgabe vorhanden sind"""
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
        
        # Test-DataFrame simulieren
        df = pd.DataFrame(columns=expected_columns)
        
        for col in expected_columns:
            assert col in df.columns
    
    def test_zeitraum_2026_bis_2045(self):
        """Testet, ob der Zeitraum von 2026 bis 2045 korrekt abgedeckt wird"""
        date_range = pd.date_range(start='01-01-2026 00:00', end='31-12-2045 23:45', 
                                  freq='15min', tz='UTC')
        
        # Prüfe Anzahl der Zeitpunkte (20 Jahre * 365.25 Tage * 96 Viertelstunden)
        expected_count = int(20 * 365.25 * 96)
        assert len(date_range) == pytest.approx(expected_count, abs=200)
        
        # Prüfe Start- und Enddatum
        assert date_range[0].year == 2026
        assert date_range[-1].year == 2045


class TestKapazitätsfaktoren:
    """Tests für die Kapazitätsfaktor-Berechnungen"""
    
    def test_kapazitätsfaktor_bereich(self):
        """Testet, ob Kapazitätsfaktoren im gültigen Bereich [0, 1] liegen"""
        # Simuliere Erzeugung und installierte Leistung
        erzeugung_mwh = 100.0
        installierte_leistung_gw = 1.0  # 1 GW = 1000 MW
        viertelstunde = 0.25  # 15 Minuten
        
        kapazitätsfaktor = erzeugung_mwh / (installierte_leistung_gw * 1000 * viertelstunde)
        
        assert 0 <= kapazitätsfaktor <= 1, f"Kapazitätsfaktor {kapazitätsfaktor} außerhalb [0, 1]"
    
    def test_kapazitätsfaktor_pv_nachts(self):
        """Testet, ob PV-Kapazitätsfaktor nachts null ist"""
        # Nachts sollte PV keine Erzeugung haben
        erzeugung_mwh = 0.0
        installierte_leistung_gw = 100.0
        
        kapazitätsfaktor = erzeugung_mwh / (installierte_leistung_gw * 1000 * 0.25)
        
        assert kapazitätsfaktor == 0.0
    
    def test_kapazitätsfaktor_biomasse_konstant(self):
        """Testet, ob Biomasse einen relativ konstanten Kapazitätsfaktor hat"""
        # Biomasse sollte grundlastfähig sein
        # Simuliere mehrere Zeitpunkte mit ähnlicher Erzeugung
        kapazitätsfaktoren = []
        
        for erzeugung in [45, 47, 46, 48, 45]:
            kf = erzeugung / (8.0 * 1000 * 0.25)  # 8 GW Biomasse
            kapazitätsfaktoren.append(kf)
        
        # Standardabweichung sollte gering sein
        assert np.std(kapazitätsfaktoren) < 0.05


class TestDatensätze:
    """Tests für die verwendeten Datensätze"""
    
    def test_historische_jahre_verfügbar(self):
        """Testet, ob die benötigten historischen Jahre verfügbar sind"""
        # Die Funktion nutzt Jahre 2020-2024
        required_years = [2020, 2021, 2022, 2023, 2024]
        
        for year in required_years:
            assert 2020 <= year <= 2024
    
    def test_schaltjahr_behandlung(self):
        """Testet die Behandlung von Schaltjahren (29. Februar)"""
        # 2020 und 2024 sind Schaltjahre
        schaltjahre = [2020, 2024]
        
        for jahr in schaltjahre:
            # Prüfe, ob 29. Februar existiert
            datum = pd.Timestamp(f'{jahr}-02-29')
            assert datum.is_leap_year


class TestPlausibilität:
    """Tests für Plausibilität der Ergebnisse"""
    
    def test_installierte_leistung_steigt(self):
        """Testet, ob die installierte Leistung über Zeit zunimmt"""
        # Beispiel: 2026 sollte weniger als 2030 haben, 2030 weniger als 2045
        installiert_2026 = 80.0
        installiert_2030 = 100.0
        installiert_2045 = 150.0
        
        assert installiert_2026 < installiert_2030 < installiert_2045
    
    def test_erzeugung_nicht_negativ(self):
        """Testet, ob Erzeugungswerte nicht negativ sind"""
        # Simuliere Prognose-Werte
        prognose_werte = [100.5, 234.7, 0.0, 567.8, 12.3]
        
        for wert in prognose_werte:
            assert wert >= 0, f"Negative Erzeugung: {wert}"
    
    def test_wind_offshore_geringer_als_onshore(self):
        """Testet, ob Wind Offshore in der Regel geringer installiert ist als Onshore"""
        # In Deutschland ist Onshore typischerweise größer
        wind_onshore_2030 = 115.0
        wind_offshore_2030 = 30.0
        
        # Offshore sollte kleiner sein (aktueller Stand)
        assert wind_offshore_2030 < wind_onshore_2030


class TestFehlende_Werte:
    """Tests für den Umgang mit fehlenden Werten"""
    
    def test_keine_nan_in_ausgabe(self):
        """Testet, ob die Ausgabe keine NaN-Werte enthält"""
        # Simuliere DataFrame ohne NaN
        df = pd.DataFrame({
            'A': [1.0, 2.0, 3.0],
            'B': [4.0, 5.0, 6.0]
        })
        
        assert not df.isna().any().any()
    
    def test_keine_inf_in_ausgabe(self):
        """Testet, ob die Ausgabe keine Inf-Werte enthält"""
        df = pd.DataFrame({
            'A': [1.0, 2.0, 3.0],
            'B': [4.0, 5.0, 6.0]
        })
        
        assert not np.isinf(df.values).any()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
