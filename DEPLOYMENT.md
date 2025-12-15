# 🚀 Deployment Anleitung - Streamlit App

## Für Streamlit Community Cloud (empfohlen)

### 1. Vorbereitung

Alle notwendigen Dateien sind bereits konfiguriert:
- ✅ `requirements.txt` - alle Dependencies
- ✅ `.streamlit/config.toml` - Streamlit-Konfiguration
- ✅ `.gitignore` - ignoriert unnötige Dateien
- ✅ `Code/streamlit_app.py` - angepasst für Deployment

### 2. GitHub Repository erstellen

Falls noch nicht vorhanden:

```bash
# Im Projektverzeichnis
git init
git add .
git commit -m "Initial commit für Deployment"

# Repository auf GitHub erstellen und pushen
git remote add origin https://github.com/DEIN-USERNAME/IPJ1-Pottkieker.git
git branch -M main
git push -u origin main
```

### 3. Bei Streamlit Community Cloud deployen

1. Gehe zu [share.streamlit.io](https://share.streamlit.io)
2. Melde dich mit deinem GitHub-Account an
3. Klicke auf "New app"
4. Wähle:
   - **Repository:** `DEIN-USERNAME/IPJ1-Pottkieker`
   - **Branch:** `main`
   - **Main file path:** `Code/streamlit_app.py`
   - **Python version:** `3.9` oder höher
5. Klicke auf "Deploy!"

### 4. App-URL

Nach erfolgreichem Deployment erhältst du eine URL wie:
`https://DEIN-USERNAME-ipj1-pottkieker-code-streamlit-app-xyz123.streamlit.app`

## Wichtige Hinweise

### Datenstruktur
Stelle sicher, dass alle Daten im Repository vorhanden sind:
- `Daten/Szenarien.json`
- `Daten/Verbrauchsprofile.json`
- `Daten/Feste_Parameter/`
- `Daten/SMARD-Daten/`
- etc.

### Erste Deployment kann 5-10 Minuten dauern

### Bei Problemen

Falls die App nicht startet:
1. Überprüfe die Logs in Streamlit Cloud
2. Teste lokal mit: `streamlit run Code/streamlit_app.py`
3. Überprüfe alle Imports in den Python-Dateien

### App lokal testen

```bash
cd "c:\Users\joris\OneDrive - HAW-HH\Labore\Integrationsprojekt1\IPJ1-Pottkieker"
streamlit run Code/streamlit_app.py
```

## Alternative: Andere Hosting-Optionen

### Heroku
Benötigt zusätzlich:
- `Procfile`
- `setup.sh`

### Docker
Benötigt `Dockerfile`

---

**Team Pottkieker - HAW Hamburg**
