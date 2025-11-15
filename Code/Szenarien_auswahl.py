"Ünterstützt durch KI (GPT-4.1 Inline Suggestions)"
import json
from config import DATA_DIR

def load_scenarios():
    """Lädt Szenarien aus einer JSON-Datei."""
    pfad = DATA_DIR / "szenarien.json"

    with open(pfad, 'r', encoding='utf-8') as datei:
        scenarios = json.load(datei)

    return scenarios

scenarios = load_scenarios()
for i in range(len(scenarios)):
    print(f"Szenario {i+1}: {scenarios[i]['Name']}")
