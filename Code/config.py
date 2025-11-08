"""
Zentrale Konfigurationsdatei für das IPJ1-Pottkieker Projekt.
Enthält Pfade und gemeinsame Einstellungen. Erstellt per KI (Claude Sonnet 4.5)
"""

from pathlib import Path

# Projekt-Root-Verzeichnis (eine Ebene über dem Code-Ordner)
PROJECT_ROOT = Path(__file__).parent.parent

# Daten-Verzeichnisse
DATA_DIR = PROJECT_ROOT / "Daten"